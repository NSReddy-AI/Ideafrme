"""Explicit media-workflow@3: accepted core operations + PNGs in one timeline.

Version2 remains frozen-base. No legacy reader or protected schema is extended.
"""
import copy,fcntl,os,threading,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical,core as core_fields
from studio_manual_ui.service import Studio,manual_subset,read,decode,exact,RUNTIME
from visual_poster_studio.project_bindings import validate as binding_validate
from visual_poster_studio.session import exclusive,sync_directory
from .workflow import Workflow,require
from .controller import safe,sha,Refused
KEYS=('document','placements','history')
def snapshot(s):return copy.deepcopy({k:s[k] for k in KEYS})
def comparable(s,floor):
 s=copy.deepcopy(s);s['document']['revision']=0;s['document']['approvals']=[]
 if floor>1:s['document']['history']['version']=max(floor,s['document']['history'].get('version',1))
 return s
class Unified(Workflow):
 def __init__(self,root,library,decoder,*,base=None,binding=None,acknowledge=False,fault=None):
  self.root=safe(Path(root));require(self.root.is_relative_to(RUNTIME) and self.root.name.startswith('png-unified-'),'Owned png-unified-* runtime root required')
  self.library=library;self.decoder=decoder;self.lock=threading.RLock();self.fault=fault;self.blocked=False;self.fd=None;create=base is not None
  if create:require(acknowledge is True,'Explicit media v3 fork acknowledgement required');self.root.mkdir(mode=0o700,parents=True,exist_ok=False)
  try:
   self.fd=os.open(safe(self.root/'png-writer.lock'),os.O_RDWR|os.O_NOFOLLOW|((os.O_CREAT|os.O_EXCL) if create else 0),0o600)
   try:fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise Refused('Another writer owns this unified media project')
   if create:
    manual_subset(base);core.validate(base,self.root);require(binding is not None,'Pinned approved binding required');binding_validate(binding,binding['session_id'],base['id']);self._brand(binding)
    self.identity=str(uuid.uuid4());exclusive(self.root/'png-session.json',canonical({'format':'studio-png-session@2','id':self.identity}),0o444)
    for n in ('generations','pixels','exports','legacy-checkpoints'):(self.root/n).mkdir(mode=0o700)
    source=canonical({'document':base,'binding':binding});require(len(source)<=9*1024*1024,'Source checkpoint limit');exclusive(self.root/'source-checkpoint.json',source,0o444);require(read(self.root/'source-checkpoint.json',9*1024*1024)==source,'Source checkpoint readback failed')
    doc=copy.deepcopy(base);doc['approvals']=[];doc['revision']+=1
    s={'format':'studio-media-workflow@3','version':3,'session_id':self.identity,'generation':1,'parent':None,'document':doc,'source_document_sha256':sha(canonical(base)),'binding':copy.deepcopy(binding),'placements':[],'history':{'version':1,'cursor':0,'transactions':[]},'approvals':[],'history_floor':doc['history'].get('version',1)}
    s['timeline']={'version':1,'cursor':0,'initial':snapshot(s),'transactions':[]};self._publish(s,None)
   else:
    marker=decode(read(self.root/'png-session.json',1024));exact(marker,{'format','id'});require(marker['format']=='studio-png-session@2','Unsupported unified reader version');self.identity=marker['id'];self.current()
  except BaseException:self.close();raise
 def _component(self,s,part):
  v={k:copy.deepcopy(v) for k,v in s.items() if k not in ('timeline','history_floor')};v.update(copy.deepcopy(part));v.update(format='studio-media-workflow@2',version=2)
  # Reuse v2 component validation in memory, never publish/downgrade a v3 file.
  Workflow._validate(self,v)
 def _validate(self,s):
  require(type(s)==dict and set(s)=={'format','version','session_id','generation','parent','document','source_document_sha256','binding','placements','history','approvals','timeline','history_floor'},'Unknown unified envelope fields')
  require(s['format']=='studio-media-workflow@3' and type(s['version'])==int and s['version']==3,'Unsupported unified media version')
  floor=s['history_floor'];require(type(floor)==int and floor in (1,2,3) and s['document']['history'].get('version',1)>=floor,'History compatibility floor violated')
  require(not (self.root/'source-checkpoint.json').stat().st_mode&0o222,'Source checkpoint must remain immutable')
  source=decode(read(self.root/'source-checkpoint.json',9*1024*1024));exact(source,{'document','binding'});manual_subset(source['document']);core.validate(source['document'],self.root)
  require(sha(canonical(source['document']))==s['source_document_sha256'] and source['binding']==s['binding'],'Immutable source/binding changed')
  self._component(s,snapshot(s));t=s['timeline'];exact(t,{'version','cursor','initial','transactions'});require(type(t['version'])==int and t['version']==1 and type(t['cursor'])==int and type(t['transactions'])==list and 0<=t['cursor']<=len(t['transactions'])<=100,'Invalid combined timeline')
  previous=t['initial'];self._component(s,previous);require(previous['placements']==[] and previous['history']=={'version':1,'cursor':0,'transactions':[]},'Invalid initial media state')
  initial=copy.deepcopy(source['document']);initial['revision']+=1;initial['approvals']=[];require(previous['document']==initial,'Initial source checkpoint mismatch')
  for tx in t['transactions']:
   exact(tx,{'kind','before','after','operation'});require(tx['kind'] in ('base','png'),'Unknown combined transaction');a,b=tx['before'],tx['after'];require(set(a)==set(KEYS) and set(b)==set(KEYS),'Incomplete combined snapshot')
   require(comparable(a,floor)==comparable(previous,floor),'Broken combined ancestry');self._component(s,a);self._component(s,b)
   if tx['kind']=='base':
    require(a['placements']==b['placements'] and a['history']==b['history'],'Base edit changed media state')
    expected=core.apply(a['document'],tx['operation'],self.root);require(core_fields(expected)==core_fields(b['document']),'Unauthorized base mutation')
    # UUID is assigned once by the accepted operation, not during replay.
    expected['history']['transactions'][-1]['id']=b['document']['history']['transactions'][-1]['id']
    require(expected==b['document'],'Base history/revision mutation')
   else:
    require(a['document']==b['document'] and tx['operation'] in ('place','geometry','remove'),'PNG edit changed the creative base')
    old,new=a['history'],b['history'];require(new['cursor']==old['cursor']+1 and new['transactions'][:-1]==old['transactions'][:old['cursor']] and len(new['transactions'])==new['cursor'],'Unauthorized PNG history mutation')
    last=new['transactions'][-1];require(last['operation']==tx['operation'] and last['before']==a['placements'] and last['after']==b['placements'],'Invalid PNG delta')
   previous=b
  selected=t['transactions'][t['cursor']-1]['after'] if t['cursor'] else t['initial'];require(comparable(snapshot(s),floor)==comparable(selected,floor),'Combined live state mismatch');return s
 def current(self):
  with self.lock:
   h=self.head();first=None;child=None;name=h['name'];seen=set()
   while name is not None:
    require(name not in seen and len(seen)<200,'Invalid unified ancestry');seen.add(name);s,d=self._load(name)
    if first is None:require(d==h['sha256'],'HEAD hash mismatch');first=s
    if child:
     require(child['generation']==s['generation']+1 and all(child[k]==s[k] for k in ('binding','source_document_sha256')) and child['history_floor']>=s['history_floor'] and child['document']['revision']>=s['document']['revision'],'Unauthorized version/base ancestry')
     a,b=s['timeline'],child['timeline'];travel=a['transactions']==b['transactions'] and abs(a['cursor']-b['cursor'])==1
     edit=b['cursor']==a['cursor']+1 and len(b['transactions'])==b['cursor'] and b['transactions'][:-1]==a['transactions'][:a['cursor']] and comparable(b['transactions'][-1]['before'],child['history_floor'])==comparable(snapshot(s),child['history_floor'])
     require(a['initial']==b['initial'] and (travel or edit),'Unauthorized combined history rewrite')
     if edit and not travel:
      tx=b['transactions'][-1];require(tx['before']==snapshot(s),'Transaction does not start at the exact committed snapshot')
      expected_floor=max(s['history_floor'],tx['after']['document']['history'].get('version',1)) if tx['kind']=='base' else s['history_floor']
      require(child['history_floor']==expected_floor,'Unacknowledged/stale history upgrade')
     else:require(child['history_floor']==s['history_floor'],'History travel cannot change the compatibility floor')
    child=s;name=s['parent']
   require(child['generation']==1 and child['parent'] is None and not child['timeline']['transactions'],'Missing initial unified generation');return copy.deepcopy(first)
 def _record(self,s,before,kind,operation):
  t=s['timeline'];require(len(t['transactions'][:t['cursor']])<100,'Combined history limit');t['transactions']=t['transactions'][:t['cursor']]+[{'kind':kind,'before':before,'after':snapshot(s),'operation':copy.deepcopy(operation)}];t['cursor']+=1
 def _transaction(self,s,target,kind):
  before=snapshot(s);Workflow._transaction(self,s,target,kind);self._record(s,before,'png',kind)
 def action(self,kind,expected,identity=None,g=None):
  if kind not in ('undo','redo'):return super().action(kind,expected,identity,g)
  with self.lock:
   require(not self.blocked and self.token()==expected,'Stale or blocked unified project');s=self.current();t=s['timeline'];position=t['cursor']+(-1 if kind=='undo' else 1);require(0<=position<=len(t['transactions']),'No combined history action')
   revision=s['document']['revision'];chosen=copy.deepcopy(t['transactions'][position-1]['after'] if position else t['initial']);s.update(chosen);s['document']['revision']=revision+1;s['document']['approvals']=[]
   if s['history_floor']>1:s['document']['history']['version']=s['history_floor']
   t['cursor']=position;return self._next(s,expected)
 def edit(self,request,expected):
  with self.lock:
   require(not self.blocked and self.token()==expected,'Stale or blocked unified project');s=self.current();doc=s['document'];require(request.get('project_id')==doc['id'] and type(request.get('expected_revision'))==int and request['expected_revision']==s['generation'],'Stale unified revision');kind=request.get('action')
   if kind=='save':exact(request,{'project_id','expected_revision','action'});return self.view()
   if kind in ('undo','redo'):exact(request,{'project_id','expected_revision','action'});self.action(kind,expected);return self.view()
   before=snapshot(s)
   if kind in ('geometry','reorder'):
    extra={'view_id','targets','acknowledge_upgrade'} if kind=='geometry' else {'view_id','ordered_element_ids','acknowledge_upgrade'};exact(request,{'project_id','expected_revision','action'}|extra);require(type(request['acknowledge_upgrade'])==bool,'Boolean upgrade acknowledgement required')
    operation={'op':kind,'view_id':request['view_id'],'expected_revision':doc['revision'],('targets' if kind=='geometry' else 'ordered_element_ids'):copy.deepcopy(request['targets' if kind=='geometry' else 'ordered_element_ids'])}
    threshold=3 if kind=='geometry' else 2
    if doc['history'].get('version',1)<threshold:
     require(request['acknowledge_upgrade'],'Explicit history upgrade required');raw=canonical(doc)+b'\n';digest=sha(raw);path=self.root/'legacy-checkpoints'/(digest+'.json');self._reserve(len(raw)+4096)
     if not path.exists():exclusive(path,raw,0o444);sync_directory(path.parent)
     require(read(path,8*1024*1024)==raw,'Legacy checkpoint mismatch');operation.update(acknowledge_upgrade=True,legacy_checkpoint_sha256=digest)
    candidate=core.apply(doc,operation,self.root)
   else:
    # In-memory facade reuses accepted validation/action mapping, never persistence.
    class Draft(Studio):
     def _directory(self,identity):return self.root
    draft=object.__new__(Draft);draft.root=self.root;draft.lock=threading.RLock();draft._working={doc['id']:copy.deepcopy(doc)};draft._digests={};draft._saved={}
    if kind=='remove':
     exact(request,{'project_id','expected_revision','action','element_id'});candidate=core.apply(doc,{'op':'remove','element_id':request['element_id']},self.root)
    else:
     from types import SimpleNamespace
     from visual_poster_studio.brand_application import action as brand_action
     r=copy.deepcopy(request);r['expected_revision']=doc['revision'];draft.projects=self.root
     if kind in ('add_text','add_shape'):(self.root/doc['id']).mkdir(exist_ok=True,mode=0o700)
     host=SimpleNamespace(manual=draft,pairs=SimpleNamespace(bindings={doc['id']:s['binding']}),brand_library=self.library,_ready=lambda _:None,_decorate=lambda value:value)
     brand_action(host,r,draft.action);candidate=draft.document(doc['id'])
    tx=candidate['history']['transactions'][-1];op=tx['operation'];operation={'op':op}
    if op=='add':operation['element']=copy.deepcopy(candidate['elements'][-1])
    elif op=='edit_text':operation.update(element_id=request['element_id'],text=request['text'])
    elif op=='move':operation.update(element_id=request['element_id'],x=request['x'],y=request['y'])
    elif op=='restyle':operation.update(element_id=request['element_id'],style={'fill':request['color']} if kind=='color' else {'font_size':request['font_size']})
    elif op=='remove':operation['element_id']=request['element_id']
    else:raise Refused('Unsupported base edit')
   manual_subset(candidate);s['document']=candidate;s['history_floor']=max(s['history_floor'],candidate['history'].get('version',1));self._constraints(s,s['placements']);self._record(s,before,'base',operation)
   with self.library.transaction() as c:self._live_locked(c,s);self._next(s,expected)
   return self.view()
 def view(self):
  s=self.current();doc=s['document'];active={e.get('content_id') for e in doc['elements'] if e['type']=='text'};remaining={lang:sum(c['language']==lang and c['id'] not in active for c in doc['content']) for lang in ('en','te')}
  try:self._brand(s['binding']);eligible=True;detail='Current pinned brand and rights'
  except (OSError,ValueError) as e:eligible=False;detail=str(e)
  from visual_poster_studio.brand_application import policy
  return {'project_id':doc['id'],'name':doc['project']['name'],'revision':s['generation'],'view':doc['views'][0],'elements':doc['elements'],'content':[c for c in doc['content'] if c['id'] in active],'can_undo':s['timeline']['cursor']>0,'can_redo':s['timeline']['cursor']<len(s['timeline']['transactions']),'saved':True,'dirty':False,'remaining_text_slots':remaining,'element_limit':64-len(s['placements']),'approval_count':0,'history_version':s['history_floor'],'media_context':{'id':self.root.name.removeprefix('png-unified-'),'head':self.token(),'version':3,'placements':s['placements']},'binding':{'hash':sha(canonical(s['binding'])),'record':s['binding'],'published_head':self.head(),'eligible':eligible,'status':detail},'brand_application':{'bound_brand':True,'supported':eligible,'export_eligible':eligible,'policy':policy(s['binding']),'violations':{},'note':detail}}
 def scene(self,*,export_svg=False):
  scene=super().scene(export_svg=export_svg);s=self.current();scene.update(project_id=s['document']['id'],revision=s['generation'],svg_sha256=scene['sha256'],source_fingerprint=scene['identity'],profile={'id':'unified-png-draft@1','width':1080,'height':1350,'media_workflow':3});return scene
 def recover_copy(self,name,destination,*,acknowledge=False):
  require(acknowledge is True,'Acknowledge that later edits and previous exports are excluded')
  destination=safe(Path(destination));require(destination.is_relative_to(RUNTIME) and destination.name.startswith('png-unified-') and not destination.exists(),'Fresh unified recovery destination required')
  chain=[];receipts=set();cursor=name
  while cursor is not None:
   require(len(chain)<200 and cursor not in {n for n,_,_ in chain},'Invalid recovery ancestry');s,h=self._load(cursor);chain.append((cursor,s,h))
   for tx in s['timeline']['transactions']:
    for part in (tx['before'],tx['after']):receipts.update(p['receipt'] for p in part['placements'])
   cursor=s['parent']
  require(chain[-1][1]['generation']==1,'Missing recovery origin')
  checkpoints=list((self.root/'legacy-checkpoints').glob('*.json'));source=read(self.root/'source-checkpoint.json',9*1024*1024)
  required=len(source)+sum(len(canonical(s)) for _,s,_ in chain)+sum(len(self._receipt(r)[1])+4096 for r in receipts)+sum(p.stat().st_size for p in checkpoints)+16384
  from .workflow import BUDGET
  require(required<=BUDGET,'Recovery budget exhausted')
  destination.mkdir(mode=0o700)
  for n in ('generations','pixels','exports','legacy-checkpoints'):(destination/n).mkdir(mode=0o700)
  exclusive(destination/'source-checkpoint.json',source,0o444);exclusive(destination/'png-session.json',read(self.root/'png-session.json',1024),0o444);exclusive(destination/'png-writer.lock',b'')
  for n,s,h in chain:
   p=destination/'generations'/n;p.mkdir(mode=0o700);exclusive(p/'workflow.json',canonical(s),0o444);sync_directory(p)
  for rid in receipts:
   r,data=self._receipt(rid);p=destination/'pixels'/rid;p.mkdir(mode=0o700);exclusive(p/'receipt.json',canonical(r),0o444);exclusive(p/'normalized.png',data,0o444);sync_directory(p)
  for p in checkpoints:
   require(p.name==sha(read(p,8*1024*1024))+'.json','Checkpoint hash mismatch');exclusive(destination/'legacy-checkpoints'/p.name,read(p,8*1024*1024),0o444)
  exclusive(destination/'recovery-origin.json',canonical({'format':'studio-unified-recovery@1','source_session_id':self.identity,'selected_generation':name,'sha256':chain[0][2],'later_edits_and_exports_excluded':True}),0o444)
  exclusive(destination/'HEAD.json',canonical({'format':'studio-png-head@1','name':name,'sha256':chain[0][2]}));sync_directory(destination/'generations');sync_directory(destination/'pixels');sync_directory(destination/'legacy-checkpoints');sync_directory(destination)
  restored=Unified(destination,self.library,self.decoder);restored.close();return destination
