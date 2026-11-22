"""Explicit, single-flight local-text planning. No HTTP, media backend or source-project mutation."""
import copy,hashlib,json,os,signal,subprocess,sys,threading,time,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError,exact,safe,read
from . import ai_hybrid as hybrid,director,binding_workflow as workflow
from .ai_adapter import require
from .session import exclusive,sync_directory

BINARY=Path('/opt/homebrew/Cellar/llama.cpp/0.9.0/bin/llama-completion')
BINARY_HASH='74cf11468e49effb467313dad495e299423950d5b0c11abf83363efb60ffb850'
MODEL=Path('/Users/Nadish/.ollama/models/blobs/sha256-a8cc1361f3145dc01f6d77c6c82c9116b9ffe3c97b34716fe20418455876c40e')
MODEL_HASH=MODEL.name.removeprefix('sha256-')
IDENTITY={'runtime':'llama.cpp','runtime_version':'0.9.0','runtime_commit':'cd959bae99ff4bed22bef2604f45241c09bbb8c8','runtime_sha256':BINARY_HASH,'model':'Qwen3-14B Q4_K_M','weights_sha256':MODEL_HASH,'tokenizer_container_sha256':MODEL_HASH}
SETTINGS={'seed':19,'temperature':0,'context_tokens':2048,'max_output_tokens':384}
LIMIT=64*1024*1024
ACTIVE={'verifying-artifacts','inferencing','compiling','queued','cancelling'}
# No Python preexec_fn in a multithreaded host. Helper sets limits before same-PID exec.
LIMITED_EXEC='import os,resource,sys; resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576)); resource.setrlimit(resource.RLIMIT_CORE,(0,0)); os.execve(sys.argv[1],sys.argv[1:],os.environ)'
class Cancelled(Exception):pass

class Native:
 identity=IDENTITY
 def available(self):
  return BINARY.is_file() and MODEL.is_file()
 def execute(self,path,request,cancel,stage):
  started=time.monotonic()
  for name,p,digest in [('runtime',BINARY,BINARY_HASH),('model',MODEL,MODEL_HASH)]:
   h=hashlib.sha256()
   with safe(p).open('rb') as stream:
    for block in iter(lambda:stream.read(8*1024*1024),b''):
     if cancel.is_set():raise Cancelled()
     if time.monotonic()-started>240:raise UIError('ai-timeout','Artifact verification timed out; no automatic retry.',409)
     h.update(block)
   require(h.hexdigest()==digest,'Pinned '+name+' changed; local AI is unavailable. Use explicit deterministic planning.')
  prompt='<|im_start|>system\n'+request['messages'][0]['content']+'<|im_end|>\n<|im_start|>user\n'+request['messages'][1]['content']+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
  exclusive(path/'schema.json',canonical(request['schema']));exclusive(path/'prompt.txt',prompt.encode())
  for n in ('tmp','cache'):(path/n).mkdir(mode=0o700)
  command=[str(BINARY),'--offline','-m',str(MODEL),'--device','none','--n-gpu-layers','0','--threads','1','--threads-batch','1','--ctx-size','2048','--batch-size','64','--ubatch-size','64','--predict','384','--seed','19','--temp','0','--single-turn','--no-conversation','--no-display-prompt','--simple-io','--color','off','--no-warmup','--json-schema-file',str(path/'schema.json'),'--file',str(path/'prompt.txt'),'--perf']
  exclusive(path/'command.json',canonical(command))
  env={k:v for k,v in os.environ.items() if not k.startswith(('LLAMA_','HF_','OLLAMA_'))};env.update(TMPDIR=str(path/'tmp'),XDG_CACHE_HOME=str(path/'cache'),LLAMA_CACHE=str(path/'cache'),OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
  launch=[sys.executable,'-I','-B','-c',LIMITED_EXEC,*command]
  exclusive(path/'launch.json',canonical(launch))
  if cancel.is_set():raise Cancelled()
  with (path/'stdout.txt').open('xb') as out,(path/'stderr.txt').open('xb') as err:
   proc=subprocess.Popen(launch,cwd=path,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
   timed=False;aborted=False
   stage('inferencing')
   try:
    while proc.poll() is None:
     aborted=cancel.is_set();timed=time.monotonic()-started>240
     if aborted or timed:break
     cancel.wait(.1)
   finally:
    # Always terminate any remaining process group, even on normal leader exit.
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:proc.wait(timeout=1)
    except subprocess.TimeoutExpired:pass
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:raise UIError('ai-termination-unconfirmed','Termination could not be confirmed; restart manually after inspecting diagnostics.',409)
    try:os.killpg(proc.pid,0)
    except ProcessLookupError:confirmed=True
    else:confirmed=False
    exclusive(path/'termination.json',canonical({'pid':proc.pid,'returncode':proc.returncode,'group_absent':confirmed,'cancelled':aborted,'timeout':timed,'seconds':time.monotonic()-started}))
    if not confirmed:raise UIError('ai-termination-unconfirmed','Process group still present; further generation blocked.',409)
   if aborted or cancel.is_set():raise Cancelled()
   if timed:raise UIError('ai-timeout','Planning exceeded 240 seconds; process stopped. Shorten the brief or explicitly choose deterministic planning.',409)
   if proc.returncode:raise UIError('ai-runtime','Local model failed (exit '+str(proc.returncode)+'); inspect job diagnostics or explicitly choose deterministic planning.',409)
  return read(path/'stdout.txt',32768)

class Jobs:
 def __init__(self,studio,executor=None):
  self.studio=studio;self.executor=executor or Native();self.lock=threading.RLock();self.job=None;self.closed=False;self.fault=False;self.thread=None
 @property
 def active(self):return self.job is not None and self.job['state'] in ACTIVE
 def _public(self):
  if self.job is None:return None
  j=self.job;v={k:copy.deepcopy(j[k]) for k in ('id','state','detail','error','diagnostics')};v['elapsed_seconds']=round((j.get('finished') or time.monotonic())-j['started'],1)
  if j['state']=='ready':
   result=j['result'];v['result']={k:copy.deepcopy(result[k]) for k in ('editorial_intent','rationales','plans','scenes','differentiation','brief','pinned_brand','request_hash','response_sha256')}
  return v
 def status(self):
  with self.lock:return {'available':not self.closed and not self.fault and self.executor.available(),'slow_mode':'Typical tested time 94–128 seconds; may take up to 240 seconds. CPU only.','automatic_retry':False,'job':self._public()}
 def start(self,request):
  exact(request,{'source','measurements'})
  with self.lock:
   require(not self.closed and not self.fault,'Planner closed or termination fault; restart manually after inspection.')
   require(not self.active,'One local planning job is already active.')
   require(self.executor.available(),'Pinned local runtime/model missing; choose deterministic planning explicitly. No automatic download.')
   with self.studio.manual.lock:
    prepared=hybrid.prepare(self.studio,request['source'],self.executor.identity,SETTINGS);hybrid.geometry.Measurements(request['measurements'])
   require(len(canonical(request['measurements']))<=32768,'Measurement input exceeds 32 KiB.')
   root=safe(self.studio.root/'hybrid-jobs')
   if not root.exists():root.mkdir(mode=0o700);sync_directory(self.studio.root)
   count=0;size=0
   for f in root.rglob('*'):
    safe(f);count+=1
    if f.is_file():size+=f.stat().st_size
   require(count<=1024 and len(list(root.iterdir()))<10 and size+20*1024*1024<=LIMIT,'Planning evidence quota reached; nothing deleted. Start a fresh session explicitly.')
   identity=uuid.uuid4().hex;path=root/identity;path.mkdir(mode=0o700);exclusive(path/'request.json',canonical(prepared));exclusive(path/'measurements.json',canonical(request['measurements']))
   j={'id':identity,'state':'queued','detail':'Verifying pinned local artifacts.','error':None,'started':time.monotonic(),'diagnostics':str(path),'request':prepared,'measurements':copy.deepcopy(request['measurements']),'cancel':threading.Event(),'path':path};self.job=j
   self.thread=threading.Thread(target=self._work,args=(j,),name='studio-hybrid-planner',daemon=True);self.thread.start();return self._public()
 def _stage(self,j,state):
  with self.lock:
   if not j['cancel'].is_set():j.update(state=state,detail={'inferencing':'Local AI interpreting editorial intent; no percent estimate.','compiling':'Validating rights and composing three measured designs.','verifying-artifacts':'Verifying pinned runtime and model hashes.'}[state])
 def _work(self,j):
  try:
   self._stage(j,'verifying-artifacts');raw=self.executor.execute(j['path'],j['request'],j['cancel'],lambda state:self._stage(j,state))
   if j['cancel'].is_set():raise Cancelled()
   self._stage(j,'compiling');result=hybrid.compile(self.studio,raw,j['request'],j['measurements'])
   data=canonical(result);require(len(data)<=16*1024*1024,'Compiled evidence exceeds 16 MiB; output refused.')
   exclusive(j['path']/'compilation.json',data,0o444)
   with self.lock:
    if j['cancel'].is_set():raise Cancelled()
    j.update(state='ready',detail='Three unapproved concepts ready; review all rules and browser previews.',result=result,raw=raw)
  except Cancelled:
   with self.lock:j.update(state='cancelled',detail='Generation cancelled; source project unchanged.',error=None)
  except Exception as exc:
   code=getattr(exc,'code','ai-failed');detail=getattr(exc,'detail','Planning failed; no automatic retry. Inspect local diagnostics or choose deterministic planning explicitly.')
   with self.lock:
    j.update(state='fault' if code=='ai-termination-unconfirmed' else 'timeout' if code=='ai-timeout' else 'failed',detail=detail,error=code)
    if code=='ai-termination-unconfirmed':self.fault=True
  finally:
   with self.lock:
    j['finished']=time.monotonic()
    try:exclusive(j['path']/'status.json',canonical({k:j[k] for k in ('id','state','detail','error','diagnostics')}),0o444)
    except (OSError,ValueError):j.update(state='fault',error='ai-evidence',detail='Planning evidence could not be finalized; result unavailable.');self.fault=True
 def cancel(self,request):
  exact(request,{'job_id'})
  with self.lock:
   require(self.job is not None and request['job_id']==self.job['id'],'Unknown planning job.')
   if self.active:self.job['cancel'].set();self.job.update(state='cancelling',detail='Stopping local inference and verifying termination.')
   elif self.job['state']=='ready':self.job.pop('result',None);self.job.update(state='cancelled',detail='Proposal discarded; source unchanged.')
   return self._public()
 def select(self,request):
  exact(request,{'job_id','concept_id','acknowledge_rules'})
  with self.lock:
   j=self.job;require(j is not None and j['id']==request['job_id'] and j['state']=='ready','No current ready proposal.');require(request['acknowledge_rules'] is True,'Review intent, all rules and previews before selecting an unapproved draft.')
   with self.studio.manual.lock:
    result=hybrid.compile(self.studio,j['raw'],j['request'],j['measurements']);require(canonical(result)==canonical(j['result']),'Compiled proposal changed; regenerate explicitly.')
    matches=[(i,p) for i,p in enumerate(result['plans']) if p['id']==request['concept_id']];require(len(matches)==1,'Unknown concept.')
    i,plan=matches[0];doc=result['documents'][i];identity=doc['id'];directory=safe(self.studio.manual.projects/identity)
    require(not directory.exists() and not self.studio.pairs.owns(identity),'Concept already exists; open it from Projects, no overwrite.')
    require(len(list(self.studio.manual.projects.iterdir()))<100,'Session project limit reached.')
    # Immutable job compilation is provenance; project truth remains existing paired storage.
    directory.mkdir(mode=0o700);binding=self.studio.pairs.new(identity,result['pinned_brand'],result['brief']);self.studio.pairs.commit(identity,doc,binding,None);workflow.mark_saved(self.studio,identity,doc)
    return {'project':self.studio.view(identity),'job_id':j['id'],'concept_id':plan['id'],'approved':False}
 def close(self):
  with self.lock:
   self.closed=True
   if self.active:self.job['cancel'].set()
  if self.thread:self.thread.join(5)
  if self.thread and self.thread.is_alive():raise UIError('ai-termination-unconfirmed','Planner thread did not stop; session ownership retained for diagnosis.',409)
