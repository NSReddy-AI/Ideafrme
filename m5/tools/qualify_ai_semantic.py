"""Exactly one semantic fixed-model CPU qualification; measured compiler, no UI integration. No UI, acquisition or media execution."""
import argparse,hashlib,json,os,resource,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_visual_resume_tests import hashes
from studio_manual_ui.service import safe
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.brands import Store
from visual_poster_studio.binding_workflow import create
from visual_poster_studio.ai_capabilities import manifest
from visual_poster_studio.ai_semantic import prepare,reject_or_compile
FIXTURES={
 'en':{'purpose':'Read together','topic':'Reading day','audience':'Children and parents','format':'poster','instructions':'Invite families to read together. Quiet, welcoming, not competitive. No prices, prizes or invented facts.'},
 'te':{'purpose':'కలిసి చదవండి','topic':'పుస్తకాల పండుగ','audience':'పిల్లలు, తల్లిదండ్రులు','format':'poster','instructions':'కుటుంబాలు కలిసి చదవడాన్ని ప్రోత్సహించాలి. ప్రశాంతమైన రూపకల్పన కావాలి. బహుమతులు లేదా ధరల గురించి చెప్పవద్దు.'}}
# Authored BEFORE execution; separate from the prompt and never sent as English translation of Telugu.
RUBRIC={'intent':['family or parent/child participation','shared reading or books','calm and welcoming rather than competitive'],'forbidden':['pricing','prizes','unsupported factual claims'],'meaning':'English rationale must evidence intent; exact text slots do NOT establish comprehension','technical':'all three plans must pass with no repair','differentiation':'each pair >=2 measured structural dimensions, editorial/rationale Jaccard<0.75; additional human qualitative review','latency':'diagnostic slow mode <=240s/request, one compute thread, no automatic retries; not a production resource contract','Telugu':'one narrow family-reading brief; native speaker acceptance remains required for broader scope'}

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while c:=f.read(8*1024*1024):h.update(c)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case',choices=FIXTURES,required=True);ap.add_argument('--run-id',required=True);ap.add_argument('--measurements',required=True);a=ap.parse_args()
 if not a.run_id.startswith('visual-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.run_id):raise SystemExit('Fresh visual- run ID required.')
 measurement_path=safe(Path(a.measurements).absolute());assert measurement_path.is_relative_to(ROOT/'.runtime');measurements=json.loads(measurement_path.read_text())['results']
 root=safe(ROOT/'.runtime/studio-ui'/a.run_id);root.mkdir(exist_ok=False);(root/'tmp').mkdir();(root/'cache').mkdir();before=hashes();(root/'rubric.json').write_text(json.dumps(RUBRIC,indent=2));(root/'capabilities.json').write_text(json.dumps(manifest(),indent=2))
 inv=json.loads((ROOT/'.runtime/studio-ui/visual-director-2a-01/inventory.json').read_text());runtime=inv['runtimes']['llama.cpp'];binary=safe(Path(runtime['qualification_binary']['path']));weight=inv['models']['qwen3:8b']['artifacts'][1];model=safe(Path(weight['path']));assert digest(binary)==runtime['qualification_binary']['sha256'];assert digest(model)==weight['actual_sha256']
 identity={'runtime':'llama.cpp','runtime_version':runtime['version'],'runtime_commit':runtime['commit'],'runtime_sha256':runtime['qualification_binary']['sha256'],'model':'Qwen3-8B Q4_K_M','weights_sha256':weight['actual_sha256'],'tokenizer_container_sha256':weight['actual_sha256']}
 s=VisualStudio(root/'session');s.brand_library=Store(root/'library')
 try:
  payload={'name':'Qualification metadata','colors':['#14213D','#F6F4EF','#D7A441'],'typography':{'english':'Inter Bold','telugu':'Noto Sans Telugu Black'},'mandatory_rules':['No additional display copy or invented claims.','Only the approved palette and supported fonts.'],'preferences':['Quiet, welcoming spacing'],'inspiration':[],'notes':'First-party synthetic metadata; no media assets.','asset_ids':[]}
  b=s.brand_library.command({'action':'save','brand_id':None,'expected_head':None,'payload':payload});b=s.brand_library.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'reviewer':'Fixture metadata owner','acknowledge':True})
  p=create(s,{'name':'AI qualification source','text':'Unchanged source','language':a.case,'brief':FIXTURES[a.case],'brand_hash':b['hash'],'acknowledge':True});source={'project_id':p['project_id'],'expected_revision':0,'expected_binding':p['binding']['hash'],'expected_head':p['binding']['published_head'],'seed':19,'acknowledge_brief':True};request=prepare(s,source,identity,{'seed':19,'temperature':0,'context_tokens':2048,'max_output_tokens':768});(root/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2));(root/'schema.json').write_text(json.dumps(request['schema']))
  prompt='<|im_start|>system\n'+request['messages'][0]['content']+'<|im_end|>\n<|im_start|>user\n'+request['messages'][1]['content']+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n';(root/'prompt.txt').write_text(prompt)
  cmd=[str(binary),'--offline','-m',str(model),'--device','none','--n-gpu-layers','0','--threads','1','--threads-batch','1','--ctx-size','2048','--batch-size','64','--ubatch-size','64','--predict','768','--seed','19','--temp','0','--single-turn','--no-conversation','--no-display-prompt','--simple-io','--color','off','--no-warmup','--json-schema-file',str(root/'schema.json'),'--file',str(root/'prompt.txt'),'--perf']
  env={k:v for k,v in os.environ.items() if not k.startswith(('LLAMA_','HF_','OLLAMA_'))};env.update(TMPDIR=str(root/'tmp'),XDG_CACHE_HOME=str(root/'cache'),LLAMA_CACHE=str(root/'cache'),OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
  def bounds():resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  start=time.monotonic();timed=False
  with (root/'stdout.txt').open('xb') as out,(root/'stderr.txt').open('xb') as err:
   child=subprocess.Popen(cmd,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True,preexec_fn=bounds)
   try:child.wait(timeout=240)
   except subprocess.TimeoutExpired:
    timed=True;os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=2)
  usage=resource.getrusage(resource.RUSAGE_CHILDREN);wall=time.monotonic()-start;raw=(root/'stdout.txt').read_bytes();result=reject_or_compile(s,raw,request,measurements,failure='timeout' if timed else 'runtime failure' if child.returncode else None)
  after=hashes();report={'case':a.case,'command':cmd,'exit_code':child.returncode,'timeout':timed,'wall_seconds':wall,'child_maxrss_bytes':usage.ru_maxrss,'termination_confirmed_direct_child':child.poll() is not None,'result':result,'source_drift':[n for n in set(before)|set(after) if before.get(n)!=after.get(n)],'source_hashes':after,'hard_aggregate_containment_qualified':False,'UI_integration':False,'Gate_A_changed':False};serialized=json.dumps(report,ensure_ascii=False,indent=2);assert len(serialized.encode())<=16*1024*1024;(root/'results.json').write_text(serialized);
  if result['status']=='compiled':
   for i,document in enumerate(result['result']['documents']):(root/('concept-'+str(i)+'.creative.json')).write_text(json.dumps(document,ensure_ascii=False,indent=2))
  print(json.dumps({k:v for k,v in report.items() if k not in ('command','result','source_hashes')},ensure_ascii=False));print(json.dumps({'status':result['status'],'reason':result.get('reason')},ensure_ascii=False))
 finally:s.close()
if __name__=='__main__':main()
