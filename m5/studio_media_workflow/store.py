"""Own namespace, immutable metadata generations, CAS publication and explicit recovery copy."""
import copy,hashlib,os,threading,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import RUNTIME,safe,read,decode,exact,project_id,UIError
from visual_poster_studio.session import exclusive,sync_directory
from visual_poster_studio.project_bindings import brief
from visual_poster_studio.binding_workflow import pin
from .contracts import FORMAT,MAX_ENVELOPE,CANDIDATES,require,validate,commit_name,digest
from . import containment
BUDGET=128*1024*1024
MARKER='media-workflow-session.json'
def sha(v):return hashlib.sha256(v).hexdigest()

class Store:
 def __init__(self,root,*,create=False,library=None,name='Quarantined media project',fields=None,brand_hash=None,recovery=None):
  import fcntl
  self.root=safe(Path(root));require(self.root.is_relative_to(RUNTIME) and self.root!=RUNTIME and self.root.name.startswith('media-workflow-'),'Use a fresh media-workflow-* directory under isolated .runtime/studio-ui.')
  self.library=library;self._fd=None;self.lock=threading.RLock();self.blocked=False;self.fault=None
  if create:self.root.mkdir(mode=0o700,parents=True,exist_ok=False)
  try:
   lockpath=safe(self.root/'media-workflow.lock')
   self._fd=os.open(lockpath,os.O_RDWR|os.O_NOFOLLOW|((os.O_CREAT|os.O_EXCL) if create else 0),0o600)
   try:fcntl.flock(self._fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except OSError as exc:raise UIError('media-busy','Another writer owns this media workflow.',409) from exc
   if create:
    self.session_id=str(uuid.uuid4());exclusive(self.root/MARKER,canonical({'format':'studio-media-session@1','version':1,'session_id':self.session_id}),0o444)
    (self.root/'commits').mkdir(mode=0o700);sync_directory(self.root)
    require(type(name)==str and 0<len(name)<=128,'Bounded project name required.');fields=brief(fields)
    project=str(uuid.uuid4());doc=core.new_document(project);doc['project']['name']=name;doc['content'][0]['text']=fields['topic'] or 'Pending media';doc['approvals']=[]
    selected=self._pin(brand_hash)
    binding={'format':'studio-project-binding@1','version':1,'binding_id':str(uuid.uuid4()),'session_id':self.session_id,'project_id':project,'revision':1,'parent':None,'brand':selected,'brief':copy.deepcopy(fields),'origin':None}
    initial={'format':FORMAT,'version':1,'session_id':self.session_id,'generation':1,'parent':None,'document':doc,'binding':binding,'admissions':[],'state':'quarantined','recovered_from':None}
    if recovery is not None:
     selected,origin=recovery;doc=copy.deepcopy(selected['document']);doc['revision']+=1;doc['approvals']=[];binding=copy.deepcopy(selected['binding']);binding.update(binding_id=str(uuid.uuid4()),session_id=self.session_id,revision=1,parent=None,origin={'session_id':selected['session_id'],'project_id':doc['id'],'commit':origin['commit'],'binding_hash':sha(canonical(selected['binding']))})
     initial.update(document=doc,binding=binding,admissions=copy.deepcopy(selected['admissions']),recovered_from=copy.deepcopy(origin))
     source_raw=canonical(selected);require(sha(source_raw)==origin['envelope_sha256'],'Recovery source mismatch.');exclusive(self.root/'recovery-source.json',source_raw,0o444)
    self._commit(initial,None)
   else:
    marker=decode(read(self.root/MARKER,4096));exact(marker,{'format','version','session_id'});require(marker['format']=='studio-media-session@1' and type(marker['version'])==int and marker['version']==1,'Unknown media ownership marker.');self.session_id=project_id(marker['session_id']);require(safe(self.root/'commits').is_dir(),'Incomplete media session; no automatic repair.');self.current()
  except Exception:self.close();raise
 def close(self):
  if self._fd is not None:os.close(self._fd);self._fd=None
 def _pin(self,identity):
  if identity is None:return None
  require(self.library is not None,'An explicitly selected library is required.')
  from types import SimpleNamespace
  return pin(SimpleNamespace(brand_library=self.library),identity)
 def _head(self):
  path=self.root/'HEAD.json'
  if not path.exists():return None
  raw=read(path,4096);h=decode(raw);exact(h,{'format','commit','sha256'});require(h['format']=='studio-media-head@1' and commit_name(h['commit']) and digest(h['sha256']),'Invalid media HEAD; explicit recovery copy only.');require(raw==canonical(h),'Noncanonical media HEAD.');return h
 def head_token(self):
  h=self._head();return sha(canonical(h)) if h is not None else None
 def _generation(self,name):
  require(commit_name(name),'Invalid generation name.');path=safe(self.root/'commits'/name/'workflow.json');raw=read(path,MAX_ENVELOPE);require(path.stat().st_mode&0o222==0,'Media generations must be immutable.');v=validate(decode(raw),self.root,self.session_id);require(raw==canonical(v),'Noncanonical envelope.');require(v['generation']==int(name[:8]),'Generation/name mismatch.')
  if v['recovered_from'] is not None:
   origin=v['recovered_from'];source=safe(self.root/'recovery-source.json');source_raw=read(source,MAX_ENVELOPE);require(source.stat().st_mode&0o222==0 and sha(source_raw)==origin['envelope_sha256'],'Recovery source integrity failure.');validate(decode(source_raw),self.root,origin['session_id'])
  return v,sha(raw)
 def _chain(self,name):
  first=None;newer=None;seen=set()
  while name is not None:
   require(name not in seen and len(seen)<200,'Excessive/cyclic media ancestry.');seen.add(name);v,h=self._generation(name)
   if first is None:first=(v,h)
   if newer:
    require(newer['generation']==v['generation']+1,'Broken media sequence.')
    require(canonical(newer['document'])==canonical(v['document']) and canonical(newer['binding'])==canonical(v['binding']),'Foundation cannot rewrite document/binding between admissions.')
    require(newer['admissions'][:-1]==v['admissions'] and len(newer['admissions'])==len(v['admissions'])+1,'Admissions must append exactly one immutable record.')
    require(newer['recovered_from']==v['recovered_from'],'Recovery provenance changed.')
   newer=v;name=v['parent']
  require(newer['generation']==1,'Missing initial media generation.');return first
 def current(self):
  with self.lock:
   h=self._head();require(h is not None,'Missing HEAD; no automatic recovery/publication.');v,d=self._chain(h['commit']);require(d==h['sha256'],'Media HEAD content hash mismatch.');return copy.deepcopy(v)
 def _reserve(self,size):
  total=count=0
  for p in self.root.rglob('*'):
   safe(p);count+=1
   if p.is_file():total+=p.stat().st_size
  require(count<=1024 and total+size<=BUDGET,'128 MiB metadata/recovery budget exhausted; evidence retained.')
  require(len(list((self.root/'commits').iterdir()))<200,'Media generation/candidate quota exhausted.')
 def _commit(self,value,expected):
  require(not self.blocked,'Publication uncertain; close and validate/recover explicitly.')
  require(self.head_token()==expected,'Stale media HEAD.');validate(value,self.root,self.session_id)
  old=self.current() if expected is not None else None
  require((old is None and value['generation']==1 and value['parent'] is None) or (old is not None and value['generation']==old['generation']+1 and value['parent']==self._head()['commit']),'Invalid proposed media sequence.')
  raw=canonical(value);self._reserve(len(raw)+8192);name=f"{value['generation']:08d}-"+uuid.uuid4().hex;directory=self.root/'commits'/name;
  try:
   directory.mkdir(mode=0o700);sync_directory(directory.parent)
   exclusive(directory/'workflow.json',raw,0o444);self._chain(name)
   if self.fault:self.fault('before-publication')
   require(self.head_token()==expected,'Media HEAD changed during commit.');head={'format':'studio-media-head@1','commit':name,'sha256':sha(raw)};pending=self.root/('HEAD-'+uuid.uuid4().hex+'.pending');exclusive(pending,canonical(head));os.replace(pending,self.root/'HEAD.json')
   if self.fault:self.fault('after-publication')
   sync_directory(self.root);require(self._head()==head,'Publication readback mismatch.');return self.head_token()
  except Exception:
   self.blocked=True
   raise UIError('media-recovery-required','Commit interrupted/uncertain; complete generations retained, no automatic repair.',409)
 def _admission(self,value,identity,declared_format):
  project_id(identity);require(type(declared_format)==str and declared_format in CANDIDATES,'Unsupported candidate format; no decoder enabled.');binding=value['binding'];require(binding['brand'] is not None,'A pinned approved brand is required for asset admission.');require(self._pin(binding['brand']['hash'])==binding['brand'],'Pinned brand no longer eligible.');require(identity in binding['brand']['record']['payload']['asset_ids'],'Asset is not in the pinned approved brand.')
  with self.library.transaction() as c:
   asset=self.library.asset(c,identity);require(asset['kind'] in CANDIDATES[declared_format],'Declared format/kind mismatch.')
   scopes=['internal_preview','commercial_design']+(['font_embed'] if asset['kind']=='font' else [])
   grants=[self.library.eligibility(c,identity,s,'library_metadata' if s=='internal_preview' else 'poster') for s in scopes];require(all(g['eligible'] for g in grants),'Current scoped asset permissions are insufficient.')
   length=c.execute('SELECT length(data) FROM blobs WHERE hash=?',(asset['sha256'],)).fetchone();require(length is not None and length[0]==asset['bytes'] and 0<length[0]<=8*1024*1024,'Asset blob length/integrity failure.')
   raw=c.execute('SELECT data FROM blobs WHERE hash=?',(asset['sha256'],)).fetchone()[0];require(type(raw)==bytes and len(raw)==asset['bytes'] and sha(raw)==asset['sha256'],'Asset bytes fail hash verification.')
   return {'asset_id':identity,'asset_record_hash':sha(canonical(asset)),'asset':copy.deepcopy(asset),'rights_hash':grants[0]['rights_hash'],'declared_format':declared_format,'state':'quarantined-unparsed'}
 def admit(self,identity,declared_format,expected_head):
  with self.lock:
   require(self.head_token()==expected_head,'Stale media HEAD.');v=self.current();require(not any(a['asset_id']==identity for a in v['admissions']),'Asset already admitted.');a=self._admission(v,identity,declared_format);v['generation']+=1;v['parent']=self._head()['commit'];v['admissions'].append(a);return self._commit(v,expected_head)
 def request_processing(self,identity):
  with self.lock:
   require(not self.blocked,'Publication uncertainty blocks processing requests.');v=self.current();a=next((a for a in v['admissions'] if a['asset_id']==identity),None);require(a is not None,'Asset not admitted.');require(self._admission(v,identity,a['declared_format'])==a,'Asset/rights identity changed since admission.');containment.require_qualified()
 def candidates(self):
  values=[];paths=list((self.root/'commits').iterdir());require(len(paths)<=200,'Candidate quota exceeded.')
  for p in sorted(paths):
   safe(p)
   try:v,h=self._chain(p.name);values.append({'commit':p.name,'valid':True,'generation':v['generation'],'sha256':h})
   except (ValueError,OSError,KeyError,TypeError):values.append({'commit':p.name,'valid':False})
  return values
 def recover_copy(self,commit,destination,*,acknowledge=False):
  require(acknowledge is True,'Acknowledge selected candidate excludes later changes.')
  with self.lock:
   v,h=self._chain(commit);origin={'session_id':self.session_id,'commit':commit,'envelope_sha256':h}
   # Historical metadata may be recovered while rights are blocked; every use rechecks live rights.
   target=Store(destination,create=True,library=self.library,name=v['document']['project']['name'],fields=v['binding']['brief'],recovery=(v,origin))
   target.close();return Path(destination)
