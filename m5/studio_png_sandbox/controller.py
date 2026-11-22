"""One-job supervisor for the pinned no-import PNG module. No network or auto retry."""
from dataclasses import dataclass
import fcntl,hashlib,json,os,resource,selectors,signal,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT_MAX=8*1024*1024
OUTPUT_MAX=16*1024*1024
SCRATCH_MAX=128*1024*1024
GUEST_MAX=64*1024*1024
OVERHEAD_MAX=128*1024*1024
class Refused(ValueError):pass
def sha(raw):return hashlib.sha256(raw).hexdigest()
def file_sha(path):
 # Pin the exact same bytes without a whole-runtime allocation in the Studio host.
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(65536),b''):h.update(block)
 return h.hexdigest()
def safe(path):
 p=Path(path)
 if not p.is_absolute():raise Refused('Absolute isolated path required')
 for x in (p,*p.parents):
  if x.is_symlink():raise Refused('Symlink refused')
 if not p.resolve().is_relative_to(ROOT/'.runtime'):raise Refused('Path outside isolated runtime')
 return p
@dataclass(frozen=True)
class Pixels:
 width:int
 height:int
 rgba:bytes
 source_sha256:str
 profile:str
 measured_helper_rss:int
 seconds:float
class Decoder:
 """Trusted-local-actor API; construct with an explicit recorded build directory.

 Host overhead is measured and refused, NOT kernel-enforced. Runtime escape is
 outside the Wasm threat model. One helper, no untrusted descendants or threads.
 """
 def __init__(self,build):
  self.build=safe(Path(build));self.faulted=False;self.last_process=None
  self.manifest=json.loads((self.build/'build.json').read_text())
  if self.manifest.get('format')!='studio-png-build@1':raise Refused('Unknown build')
  if self.manifest.get('runtime')!='wasmtime-50.0.1':raise Refused('Unknown runtime')
  for name in ('png-helper','decoder.wasm'):
   p=safe(self.build/name)
   if p.stat().st_size>4*1024*1024 or file_sha(p)!=self.manifest['files'][name]:raise Refused('Build hash mismatch')
  # Dynamic runtime is pinned too; no inherited loader/environment overrides.
  runtime=safe(Path(self.manifest['runtime_library']))
  if file_sha(runtime)!=self.manifest['runtime_library_sha256']:raise Refused('Runtime hash mismatch')
  self.profile='studio-png-rgba@1:'+self.manifest['files']['decoder.wasm']+':'+self.manifest['files']['png-helper']
 def decode(self,raw,*,expected_sha256,cancel=None,timeout=15):
  if self.faulted:raise Refused('Supervisor faulted; explicit new instance required')
  if type(raw)!=bytes or not 0<len(raw)<=INPUT_MAX or sha(raw)!=expected_sha256:raise Refused('Input length/hash mismatch')
  if not 0<timeout<=15:raise Refused('Deadline must be at most 15 seconds')
  if cancel is not None and cancel.is_set():raise Refused('Cancelled before start')
  lockroot=ROOT/'.runtime/png-sandbox-control'
  safe(lockroot);lockroot.mkdir(exist_ok=True,mode=0o700)
  lockpath=safe(lockroot/'job.lock');fd=os.open(lockpath,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
  try:
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise Refused('Another PNG job is active')
   return self._run(raw,expected_sha256,cancel,timeout)
  finally:os.close(fd)
 def _run(self,raw,identity,cancel,timeout):
  started=time.monotonic();stdout=bytearray();stderr=bytearray();sent=0;p=None
  selector=selectors.DefaultSelector()
  try:
   p=subprocess.Popen([str(self.build/'png-helper'),str(self.build/'decoder.wasm'),'decode'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True,cwd=self.build,env={'PATH':'/usr/bin:/bin','HOME':str(self.build),'TMPDIR':str(self.build)})
   self.last_process=p.pid
   for f,events in [(p.stdin,selectors.EVENT_WRITE),(p.stdout,selectors.EVENT_READ),(p.stderr,selectors.EVENT_READ)]:os.set_blocking(f.fileno(),False);selector.register(f,events)
   while selector.get_map():
    if (cancel is not None and cancel.is_set()) or time.monotonic()-started>=timeout:raise Refused('Cancelled or timed out')
    for key,events in selector.select(min(.01,max(.001,timeout-(time.monotonic()-started)))):
     f=key.fileobj
     if f is p.stdin:
      try:n=os.write(f.fileno(),memoryview(raw)[sent:sent+65536]);sent+=n
      except BrokenPipeError:sent=len(raw)
      if sent==len(raw):selector.unregister(f);f.close()
     else:
      chunk=os.read(f.fileno(),65536)
      if not chunk:selector.unregister(f);f.close();continue
      target=stdout if f is p.stdout else stderr;limit=OUTPUT_MAX+256 if f is p.stdout else 4096
      if len(target)+len(chunk)>limit:raise Refused('Helper output budget exceeded')
      target.extend(chunk)
   code=p.wait(timeout=max(.001,timeout-(time.monotonic()-started)))
   if code:raise Refused('Helper refused: '+stderr.decode('utf-8',errors='replace')[-1024:])
   newline=stdout.find(b'\n')
   if not 0<newline<256:raise Refused('Invalid result header')
   header=stdout[:newline]
   values=header.decode('ascii').split()
   if len(values)!=6 or values[0]!='PNG_RGBA_V1':raise Refused('Invalid result header')
   w,h,memory,rss,threads=map(int,values[1:])
   data_size=len(stdout)-newline-1
   if not 0<w<=2048 or not 0<h<=2048 or data_size!=w*h*4 or memory>GUEST_MAX or rss>OVERHEAD_MAX or threads!=1:raise Refused('Invalid result limits')
   # Conservative bound on application-owned input/output copies; no scratch
   # filesystem exists for the guest. Runtime allocations are measured separately.
   if GUEST_MAX+10*1024*1024+len(raw)+len(stdout)+data_size+131072>SCRATCH_MAX:raise Refused('Application buffer budget')
   if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>OVERHEAD_MAX:raise Refused('Controller measured RSS ceiling')
   if cancel is not None and cancel.is_set():raise Refused('Cancelled before result publication')
   return Pixels(w,h,bytes(memoryview(stdout)[newline+1:]),identity,self.profile,rss,time.monotonic()-started)
  except (Exception,BaseException):
   if p is not None and p.poll() is None:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    try:p.wait(timeout=1)
    except subprocess.TimeoutExpired:self.faulted=True;raise Refused('FAULT: helper termination unconfirmed')
   raise
  finally:
   selector.close()
   if p is not None:
    for f in (p.stdin,p.stdout,p.stderr):
     if f is not None and not f.closed:f.close()
