"""Fresh bounded fixtures; no external media, network, protected stores or broad suites."""
import fcntl,json,os,struct,subprocess,sys,time,unittest,zlib
from pathlib import Path
from threading import Event
from unittest.mock import patch
from studio_png_sandbox.controller import Decoder,Pixels,Refused,ROOT,sha,safe
def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d))
def png(w=2,h=2,pixel=b'\xff\0\0\xff',*,depth=8,color=6,interlace=0,extra=b''):
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,depth,color,0,0,interlace))+extra+chunk(b'IDAT',zlib.compress((b'\0'+pixel*w)*h))+chunk(b'IEND',b'')
class SecurityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.build=Path(os.environ['PNG_BUILD']);cls.evidence=Path(os.environ['PNG_TEST_ROOT']);cls.metrics=[]
 def setUp(self):self.decoder=Decoder(self.build)
 def decode(self,raw):
  v=self.decoder.decode(raw,expected_sha256=sha(raw));self.metrics.append({'seconds':v.seconds,'rss':v.measured_helper_rss,'width':v.width,'height':v.height});return v
 def helper(self,mode,module=None):
  return subprocess.run([str(self.build/'png-helper'),str(module or self.build/'decoder.wasm'),mode],input=b'',capture_output=True,timeout=16,env={'PATH':'/usr/bin:/bin','HOME':str(self.evidence),'TMPDIR':str(self.evidence)})
 def test_exact_rgba_and_alpha(self):
  raw=png(pixel=b'\x14\x28\x3c\x80');v=self.decode(raw);self.assertEqual(v.rgba,b'\x14\x28\x3c\x80'*4)
 def test_deterministic_repeated_decode(self):
  raw=png();a=self.decode(raw);b=self.decode(raw);self.assertEqual(a.rgba,b.rgba);self.assertEqual(a.profile,b.profile)
 def test_supported_rgb8(self):self.assertEqual(self.decode(png(pixel=b'\xff\0\0',color=2)).rgba,b'\xff\0\0\xff'*4)
 def test_maximum_dimensions_and_memory(self):
  v=self.decode(png(2048,2048));self.assertEqual(len(v.rgba),16*1024*1024);self.assertLessEqual(v.measured_helper_rss,128*1024*1024)
 def test_dimension_bomb(self):
  raw=png(1,1);raw=raw[:8]+chunk(b'IHDR',struct.pack('>IIBBBBB',0xffffffff,0xffffffff,8,6,0,0,0))+raw[33:]
  with self.assertRaises(Refused):self.decode(raw)
 def test_excess_decompressed_data(self):
  raw=png(1,1);raw=raw[:33]+chunk(b'IDAT',zlib.compress(b'\0'*1000000))+chunk(b'IEND',b'')
  with self.assertRaises(Refused):self.decode(raw)
 def test_corrupt_crc(self):
  raw=bytearray(png());raw[-1]^=1
  with self.assertRaises(Refused):self.decode(bytes(raw))
 def test_truncation(self):
  with self.assertRaises(Refused):self.decode(png()[:-3])
 def test_trailing_content(self):
  with self.assertRaises(Refused):self.decode(png()+b'<script>bad</script>')
 def test_svg_and_fonts_refused(self):
  for raw in (b'<svg/>',b'OTTO'+b'\0'*100):
   with self.assertRaises(Refused):self.decode(raw)
 def test_animation_metadata_and_external_reference_refused(self):
  for tag,data in [(b'acTL',b'\0'*8),(b'tEXt',b'url\0https://example.invalid'),(b'iCCP',b'\0'*50)]:
   with self.assertRaises(Refused):self.decode(png(extra=chunk(tag,data)))
 def test_unsupported_png_profiles_refused(self):
  for options in ({'depth':16},{'color':3},{'interlace':1}):
   with self.assertRaises(Refused):self.decode(png(**options))
 def test_hash_and_input_bound_before_launch(self):
  with patch('subprocess.Popen',side_effect=AssertionError('No launch')):
   for raw,identity in [(png(),'0'*64),(b'x'*(8*1024*1024+1),'0'*64)]:
    with self.assertRaises(Refused):self.decoder.decode(raw,expected_sha256=identity)
 def test_hard_memory_growth_refusal(self):
  r=self.helper('probe-memory');self.assertEqual(r.returncode,0);self.assertEqual(r.stdout,b'MEMORY_GROW_REFUSED\n')
 def test_fuel_traps(self):
  r=self.helper('probe-fuel');self.assertEqual(r.returncode,2);self.assertIn(b'all fuel consumed',r.stderr)
 def test_stack_traps(self):
  r=self.helper('probe-stack');self.assertEqual(r.returncode,2);self.assertIn(b'stack',r.stderr)
 def test_no_filesystem_network_or_process_imports(self):
  # Minimal well-formed modules requesting one host function, never instantiated.
  for name in ('path_open','sock_open','proc_spawn','thread_spawn'):
   field=name.encode();module=b'env';imp=b'\x01'+bytes([len(module)])+module+bytes([len(field)])+field+b'\x00\x00'
   raw=b'\0asm\x01\0\0\0'+b'\x01\x04\x01\x60\0\0'+b'\x02'+bytes([len(imp)])+imp
   path=self.evidence/(name+'.wasm');path.write_bytes(raw);r=self.helper('decode',path)
   self.assertEqual(r.returncode,2);self.assertIn(b'imports-forbidden',r.stderr)
 def test_pre_cancel_no_launch(self):
  event=Event();event.set()
  with patch('subprocess.Popen',side_effect=AssertionError('No launch')):
   with self.assertRaises(Refused):self.decoder.decode(png(),expected_sha256=sha(png()),cancel=event)
 def test_timeout_confirms_termination_and_next_job(self):
  with self.assertRaises(Refused):self.decoder.decode(png(2048,2048),expected_sha256=sha(png(2048,2048)),timeout=.001)
  pid=self.decoder.last_process
  with self.assertRaises(ProcessLookupError):os.kill(pid,0)
  self.assertFalse(self.decoder.faulted);self.assertEqual(self.decode(png()).width,2)
 def test_duplicate_writer_refused(self):
  path=ROOT/'.runtime/png-sandbox-control/job.lock';path.parent.mkdir(exist_ok=True)
  with path.open('a+') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaises(Refused):self.decode(png())
 def test_unknown_mode_and_module_size_refused(self):
  self.assertEqual(self.helper('not-a-mode').returncode,2)
  path=self.evidence/'oversize.wasm';path.write_bytes(b'\0'*(2*1024*1024+1));r=self.helper('decode',path);self.assertIn(b'module-size',r.stderr)
 def test_path_rejection(self):
  for path in (Path('/tmp/not-authorized'),Path('../bad')):
   with self.assertRaises(Refused):safe(path)
 def test_running_decode_cancellation_confirms_no_process(self):
  started=time.monotonic()
  class Cancel:
   def is_set(self):return time.monotonic()-started>.025
  raw=png(2048,2048);started=time.monotonic()
  with self.assertRaises(Refused):self.decoder.decode(raw,expected_sha256=sha(raw),cancel=Cancel())
  with self.assertRaises(ProcessLookupError):os.kill(self.decoder.last_process,0)
 def test_native_wall_alarm_without_input(self):
  p=subprocess.Popen([str(self.build/'png-helper'),str(self.build/'decoder.wasm'),'decode'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={'PATH':'/usr/bin:/bin','HOME':str(self.evidence),'TMPDIR':str(self.evidence)})
  try:self.assertEqual(p.wait(timeout=16),-14)
  finally:
   if p.poll() is None:p.kill();p.wait(timeout=1)
   for f in (p.stdin,p.stdout,p.stderr):f.close()
 def test_scratch_accounting_conservative_bound(self):
  from studio_png_sandbox.controller import GUEST_MAX,INPUT_MAX,OUTPUT_MAX,SCRATCH_MAX
  worst=GUEST_MAX+10*1024*1024+INPUT_MAX+(OUTPUT_MAX+256)+OUTPUT_MAX+131072
  self.assertLessEqual(worst,SCRATCH_MAX)
 def test_unconfirmed_termination_faults_supervisor(self):
  original=subprocess.Popen;children=[]
  def uncertain(*args,**kwargs):
   p=original(*args,**kwargs);wait=p.wait;children.append((p,wait))
   def fail(*args,**kwargs):raise subprocess.TimeoutExpired('injected wait failure',1)
   p.wait=fail;return p
  raw=png(2048,2048)
  try:
   with patch('subprocess.Popen',side_effect=uncertain):
    with self.assertRaisesRegex(Refused,'termination unconfirmed'):self.decoder.decode(raw,expected_sha256=sha(raw),timeout=.001)
   self.assertTrue(self.decoder.faulted)
   with self.assertRaisesRegex(Refused,'faulted'):self.decoder.decode(png(),expected_sha256=sha(png()))
  finally:
   for p,wait in children:
    p.wait=wait
    if p.poll() is None:p.kill()
    wait(timeout=1)
