"""Immutable document/context pairs with one publication pointer; legacy primaries untouched."""
import copy,hashlib,json,os,re,uuid
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError,safe,read,decode,encoded,exact,project_id,manual_subset,MAX_DOCUMENT
from .session import marker,exclusive,sync_directory
from .brands import validate_record

def check(ok,message):
 if not ok:raise UIError('binding-contract',message,409)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def brief(value):
 exact(value,{'purpose','topic','audience','format','instructions'});check(value['format']=='poster','Only the existing poster format is supported.')
 for k in ('purpose','topic','audience','instructions'):
  s=value[k];check(type(s)==str and len(s)<=2000 and '\x00' not in s,'Invalid brief text.')
  try:s.encode('utf-8')
  except UnicodeError:raise UIError('binding-contract','Invalid Unicode brief.')
 return value

def validate(value,session_id,identity):
 exact(value,{'format','version','binding_id','session_id','project_id','revision','parent','brand','brief','origin'})
 check(value['format']=='studio-project-binding@1' and type(value['version'])==int and value['version']==1,'Unsupported binding format.')
 project_id(value['binding_id']);check(value['session_id']==session_id and value['project_id']==identity,'Binding owner/project mismatch.')
 check(type(value['revision'])==int and value['revision']>0,'Invalid binding revision.');check(value['parent'] is None or type(value['parent'])==str and re.fullmatch('[0-9a-f]{64}',value['parent']),'Invalid binding parent.');brief(value['brief'])
 if value['brand'] is not None:
  b=value['brand'];exact(b,{'brand_id','revision','hash','record'});validate_record(b['record']);check(b['record']['type']=='brand' and b['record']['state']=='approved' and b['brand_id']==b['record']['brand_id'] and b['revision']==b['record']['revision'] and b['hash']==sha(canonical(b['record'])),'Invalid pinned approved brand.')
 if value['origin'] is not None:
  o=value['origin'];exact(o,{'session_id','project_id','commit','binding_hash'});project_id(o['session_id']);project_id(o['project_id']);check(valid_commit(o['commit']) and type(o['binding_hash'])==str and re.fullmatch('[0-9a-f]{64}',o['binding_hash']),'Invalid recovery origin.')
 check(len(canonical(value))<=65536,'Binding exceeds 64 KiB.');return value

def valid_commit(value):return type(value)==str and re.fullmatch('[0-9]{8}-[0-9a-f]{32}',value)

class Pairs:
 def __init__(self,session,journal):
  self.session=session;self.root=safe(session/'bound-projects');self.session_id=marker(session)['manual_id'];self.journal=journal;self.heads={};self.bindings={};self.errors={};self.fault=None
 def usage(self):
  if not self.root.exists():return 0
  total=count=0
  for p in self.root.rglob('*'):
   safe(p);count+=1;check(count<=8192,'Bound recovery entry limit exceeded.')
   if p.is_file():total+=p.stat().st_size
  return total
 def directory(self,identity):return safe(self.root/project_id(identity))
 def owns(self,identity):return self.directory(identity).exists()
 def head(self,identity):
  path=self.directory(identity)/'HEAD.json'
  if not path.exists():return None
  raw=read(path,4096);v=decode(raw);exact(v,{'format','commit','manifest_sha256'});check(v['format']=='studio-bound-head@1' and valid_commit(v['commit']) and type(v['manifest_sha256'])==str and re.fullmatch('[0-9a-f]{64}',v['manifest_sha256']),'Invalid bound HEAD.');return v
 def pair(self,identity,commit):
  check(valid_commit(commit),'Invalid pair identity.');path=self.directory(identity)/'commits'/commit
  mraw=read(path/'manifest.json',4096);m=decode(mraw);exact(m,{'format','project_id','session_id','sequence','parent','creative_sha256','binding_sha256','origin_binding_sha256'})
  check(m['format']=='studio-bound-commit@1' and m['project_id']==identity and m['session_id']==self.session_id and type(m['sequence'])==int and m['sequence']==int(commit[:8]) and (m['parent'] is None or valid_commit(m['parent'])),'Invalid paired manifest.')
  docraw=read(path/'creative.json',MAX_DOCUMENT);braw=read(path/'binding.json',65536);check(sha(docraw)==m['creative_sha256'] and sha(braw)==m['binding_sha256'],'Pair integrity mismatch.')
  for name in ['creative.json','binding.json','manifest.json']:
   check((path/name).stat().st_mode&0o222==0,'Pair files must be immutable.')
  doc=decode(docraw);manual_subset(doc);core.validate(doc,self.session/'projects'/identity);check(doc['id']==identity,'Document identity mismatch.');b=validate(decode(braw),self.session_id,identity)
  origin=None
  if m['origin_binding_sha256'] is not None:
   origin=read(path/'origin-binding.json',65536);check((path/'origin-binding.json').stat().st_mode&0o222==0,'Recovery provenance must be immutable.');check(sha(origin)==m['origin_binding_sha256'] and b['origin'] is not None and b['origin']['binding_hash']==sha(origin),'Recovery provenance mismatch.')
  if origin is not None:validate(decode(origin),b['origin']['session_id'],b['origin']['project_id'])
  check(set(p.name for p in path.iterdir())=={'creative.json','binding.json','manifest.json'}|({'origin-binding.json'} if origin else set()),'Unexpected pair files.')
  return {'document':doc,'binding':b,'manifest':m,'manifest_sha256':sha(mraw),'origin':origin,'commit':commit}
 def chain(self,identity,commit):
  first=None;newer=None;seen=set()
  while commit is not None:
   check(commit not in seen and len(seen)<200,'Invalid or excessive paired ancestry.');seen.add(commit);v=self.pair(identity,commit)
   if first is None:first=v
   if newer:
    self.compatible(v['document'],newer['document'])
    check(newer['manifest']['sequence']==v['manifest']['sequence']+1 and newer['document']['revision']>=v['document']['revision'],'Broken pair order/revision.')
    a,b=v['binding'],newer['binding']
    if canonical(a)!=canonical(b):check(b['binding_id']==a['binding_id'] and b['revision']==a['revision']+1 and b['parent']==sha(canonical(a)) and newer['document']['revision']>v['document']['revision'] and newer['document']['approvals']==[],'Invalid binding revision or approval invalidation.')
   newer=v;commit=v['manifest']['parent']
  check(newer['manifest']['sequence']==1 and newer['binding']['revision']==1 and newer['binding']['parent'] is None,'Missing initial pair.');return first
 def load(self,identity):
  check(not (self.session/'projects'/identity/'creative.json').exists(),'Bound project has an unexpected legacy primary mirror.')
  h=self.head(identity);check(h is not None,'Bound publication missing; explicit recovery required.');v=self.chain(identity,h['commit']);check(h['manifest_sha256']==v['manifest_sha256'],'HEAD manifest mismatch.');self.heads[identity]=h;self.bindings[identity]=v['binding'];return v['document']
 def scan(self,manual):
  if not self.root.exists():return
  for p in self.root.iterdir():
   safe(p);identity=project_id(p.name)
   try:self.install(manual,identity,self.load(identity))
   except (OSError,ValueError,KeyError,TypeError,AttributeError,core.CreativeError) as e:self.errors[identity]={'state':'bound-recovery-required','detail':'Paired document/binding validation failed; originals preserved.'}
 def compatible(self,before,after):
  check(canonical(before)==canonical(after) or after['revision']>before['revision'],'Changed document needs a newer revision.')
  check(after['history'].get('version',1)>=before['history'].get('version',1),'History envelope cannot downgrade.')
  versions={v['id']:v for v in after['versions']};check(all(versions.get(v['id'])==v for v in before['versions']),'Historical named snapshots/approvals are append-only.')
 def install(self,manual,identity,doc):
  manual._working[identity]=copy.deepcopy(doc);manual._saved[identity]=sha(encoded(doc));manual._digests[identity]=sha(canonical(doc)+b'\n')
 def new(self,identity,pin,fields,origin=None):
  return validate({'format':'studio-project-binding@1','version':1,'binding_id':str(uuid.uuid4()),'session_id':self.session_id,'project_id':identity,'revision':1,'parent':None,'brand':pin,'brief':brief(fields),'origin':origin},self.session_id,identity)
 def commit(self,identity,doc,binding,expected_head,publish=True,origin_raw=None):
  project_id(identity);validate(binding,self.session_id,identity);manual_subset(doc);core.validate(doc,self.session/'projects'/identity);check(doc['id']==identity,'Foreign document.')
  actual=self.head(identity) if self.owns(identity) else None;check(actual==expected_head,'Stale paired publication; reopen before saving.')
  previous=self.chain(identity,actual['commit']) if actual else None
  if previous and canonical(previous['document'])==canonical(doc) and canonical(previous['binding'])==canonical(binding) and publish:return actual
  if previous:
   self.compatible(previous['document'],doc)
   check(doc['revision']>=previous['document']['revision'],'Document revision cannot decrease.')
   if canonical(previous['binding'])!=canonical(binding):check(binding['binding_id']==previous['binding']['binding_id'] and binding['revision']==previous['binding']['revision']+1 and binding['parent']==sha(canonical(previous['binding'])) and doc['revision']>previous['document']['revision'] and doc['approvals']==[],'Invalid binding change.')
   else:check(canonical(previous['document'])==canonical(doc) or doc['revision']>previous['document']['revision'],'Changed document needs a newer revision.')
  else:check(binding['revision']==1 and binding['parent'] is None,'Initial binding revision required.')
  if previous and origin_raw is None:origin_raw=previous['origin']
  d=self.directory(identity);commits=d/'commits';existing=list(commits.iterdir()) if commits.exists() else [];check(len(existing)<200,'Paired save/recovery candidate limit reached.')
  draw=canonical(doc)+b'\n';braw=canonical(binding);self.journal.reserve(len(draw)+len(braw)+len(origin_raw or b'')+16384)
  if not self.root.exists():self.root.mkdir(mode=0o700);sync_directory(self.session)
  if not d.exists():d.mkdir(mode=0o700);sync_directory(self.root)
  if not commits.exists():commits.mkdir(mode=0o700);sync_directory(d)
  sequence=previous['manifest']['sequence']+1 if previous else 1;name=f'{sequence:08d}-'+uuid.uuid4().hex;path=commits/name;path.mkdir(mode=0o700);sync_directory(commits)
  m={'format':'studio-bound-commit@1','project_id':identity,'session_id':self.session_id,'sequence':sequence,'parent':actual['commit'] if actual else None,'creative_sha256':sha(draw),'binding_sha256':sha(braw),'origin_binding_sha256':sha(origin_raw) if origin_raw else None}
  try:
   exclusive(path/'creative.json',draw,0o444)
   if self.fault:self.fault('after-document')
   exclusive(path/'binding.json',braw,0o444)
   if origin_raw is not None:exclusive(path/'origin-binding.json',origin_raw,0o444)
   mraw=canonical(m);exclusive(path/'manifest.json',mraw,0o444);self.chain(identity,name)
   if self.fault:self.fault('before-publication')
   h={'format':'studio-bound-head@1','commit':name,'manifest_sha256':sha(mraw)}
   if publish:
    check(self.head(identity)==expected_head,'Concurrent publication changed.');temporary=d/('HEAD-'+uuid.uuid4().hex+'.pending');exclusive(temporary,canonical(h));os.replace(temporary,d/'HEAD.json')
    if self.fault:self.fault('after-publication')
    sync_directory(d);check(self.head(identity)==h,'Publication readback failed.');self.heads[identity]=h;self.bindings[identity]=copy.deepcopy(binding)
   return h
  except (OSError,ValueError,KeyError,TypeError,AttributeError,core.CreativeError) as e:
   self.errors[identity]={'state':'bound-publication-uncertain','detail':'No automatic repair; select a verified complete pair for recovery.'};raise UIError('bound-recovery-required','Paired save interrupted. Original generations preserved.',409) from e
 def candidates(self,identity):
  project_id(identity);path=self.directory(identity)/'commits';result=[]
  if not path.exists():return result
  entries=list(path.iterdir());check(len(entries)<=200,'Candidate limit exceeded.')
  for p in sorted(entries):
   try:v=self.chain(identity,p.name);result.append({'commit':p.name,'valid':True,'document_revision':v['document']['revision'],'binding_revision':v['binding']['revision']})
   except (OSError,ValueError,KeyError,TypeError,AttributeError,core.CreativeError):result.append({'commit':p.name,'valid':False})
  return result
