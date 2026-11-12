"""Separate metadata-only library. Opaque asset bytes never enter a renderer/decoder."""
import base64
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl,hashlib,json,os,re,sqlite3,uuid
from pathlib import Path
from studio_manual_ui.service import WORKSPACE,UIError,safe,read,exact
ROOT=WORKSPACE/'.runtime/studio-ui/brand-library'
SCOPES={'internal_preview','commercial_design','redistribute','template_use','font_embed'}
DESTINATIONS={'poster','reel','library_metadata'}
APP=0x42524131

def check(ok,message):
 if not ok:raise UIError('brand-contract',message)
def string(value,maximum=256,empty=False):
 check(type(value)==str and (empty or bool(value)) and len(value)<=maximum and '\x00' not in value,'Invalid text field.')
 try:value.encode('utf-8')
 except UnicodeError:raise UIError('brand-contract','Invalid Unicode.')
 return value
def identity(value):
 check(type(value)==str,'UUID required.')
 try:check(str(uuid.UUID(value))==value,'Canonical UUID required.')
 except (ValueError,AttributeError):raise UIError('brand-contract','UUID required.')
 return value
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def now():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def timestamp(v):
 check(type(v)==str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',v),'Exact UTC timestamp required.')
 try:datetime.strptime(v,'%Y-%m-%dT%H:%M:%SZ')
 except ValueError:raise UIError('brand-contract','Invalid expiry date.')
 return v

def payload(v):
 exact(v,{'name','colors','typography','mandatory_rules','preferences','inspiration','notes','asset_ids'});string(v['name']);string(v['notes'],2000,True)
 exact(v['typography'],{'english','telugu'})
 for x in v['typography'].values():string(x,256,True)
 check(type(v['colors'])==list and len(v['colors'])<=16,'Maximum 16 colors.')
 check(all(type(c)==str and re.fullmatch('#[0-9A-Fa-f]{6}',c) for c in v['colors']) and len(set(c.lower() for c in v['colors']))==len(v['colors']),'Unique hex colors required.')
 for name in ('mandatory_rules','preferences','inspiration'):
  check(type(v[name])==list and len(v[name])<=32,'Maximum 32 declarations.')
  for item in v[name]:string(item)
 check(type(v['asset_ids'])==list and len(v['asset_ids'])<=64,'Maximum 64 asset references.')
 for i in v['asset_ids']:identity(i)
 check(len(set(v['asset_ids']))==len(v['asset_ids']),'Duplicate asset reference.')
 return v

def rights(v):
 exact(v,{'status','authority','evidence','scopes','destinations','expires'});string(v['authority'],256,True);string(v['evidence'],2000,True)
 check(v['status'] in ('unknown','granted','denied'),'Unknown rights status.')
 for key,allowed in [('scopes',SCOPES),('destinations',DESTINATIONS)]:
  check(type(v[key])==list and all(type(i)==str and i in allowed for i in v[key]) and len(set(v[key]))==len(v[key]),'Invalid scope or destination.')
 if v['status']=='granted':
  check(bool(v['authority']) and bool(v['evidence']) and bool(v['scopes']) and bool(v['destinations']),'Grant requires authority, evidence, scopes and destinations.');timestamp(v['expires'])
 else:check(not v['scopes'] and not v['destinations'] and v['expires'] is None,'Non-grants cannot carry permissions.')
 return v

def validate_record(v):
 if v.get('type')=='asset':
  exact(v,{'type','id','name','kind','sha256','bytes','provenance'});identity(v['id']);string(v['name'],128)
  check('/' not in v['name'] and '\\' not in v['name'],'Asset label must not be a path.')
  check(v['kind'] in ('logo','image','font','template'),'Unknown asset kind.');check(type(v['bytes'])==int and 0<v['bytes']<=8*1024*1024,'Asset size limit.')
  check(type(v['sha256'])==str and re.fullmatch('[0-9a-f]{64}',v['sha256']),'Invalid asset hash.');exact(v['provenance'],{'owner','source','license'})
  for value in v['provenance'].values():string(value,256,True)
 elif v.get('type')=='rights':
  exact(v,{'type','id','asset_id','previous','status','authority','evidence','scopes','destinations','expires'});identity(v['id']);identity(v['asset_id']);rights({k:v[k] for k in ('status','authority','evidence','scopes','destinations','expires')})
  check(v['previous'] is None or type(v['previous'])==str and re.fullmatch('[0-9a-f]{64}',v['previous']),'Invalid rights ancestry.')
 elif v.get('type')=='brand':
  exact(v,{'type','brand_id','revision','parent','state','reviewer','approved_at','payload','bindings'});identity(v['brand_id']);check(type(v['revision'])==int and v['revision']>0,'Invalid revision.');payload(v['payload'])
  check(v['parent'] is None or type(v['parent'])==str and re.fullmatch('[0-9a-f]{64}',v['parent']),'Invalid parent.')
  check(v['state'] in ('draft','approved'),'Invalid version state.');string(v['reviewer'],256,True);check(type(v['bindings'])==list,'Invalid bindings.')
  if v['state']=='draft':check(v['reviewer']=='' and v['approved_at'] is None and not v['bindings'],'Draft cannot claim approval.')
  else:
   string(v['reviewer']);timestamp(v['approved_at']);check(len(v['bindings'])==len(v['payload']['asset_ids']),'Missing approval bindings.')
   for binding in v['bindings']:
    exact(binding,{'asset_id','sha256','rights_hash'});identity(binding['asset_id'])
    for key in ('sha256','rights_hash'):check(type(binding[key])==str and re.fullmatch('[0-9a-f]{64}',binding[key]),'Invalid binding hash.')
 else:raise UIError('brand-contract','Unknown record type.')
 return v

class Store:
 def __init__(self,root=ROOT):
  self.root=safe(Path(root));check(self.root.is_relative_to(WORKSPACE/'.runtime/studio-ui') and self.root!=WORKSPACE/'.runtime/studio-ui','Library must be inside the isolated runtime tree.')
 @contextmanager
 def transaction(self,create=False):
  exists=self.root.exists()
  if not exists:
   check(create,'Library not initialized.');self.root.mkdir(mode=0o700,parents=True,exist_ok=False)
  db=safe(self.root/'library.sqlite3');lock=safe(self.root/'library.lock')
  if exists:check(db.exists(),'Incomplete library; no automatic initialization/repair.')
  for name in ('library.sqlite3-journal','library.sqlite3-wal','library.sqlite3-shm'):safe(self.root/name)
  if db.exists():check(db.stat().st_size<=64*1024*1024,'Library size limit exceeded.')
  fd=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);con=None
  try:
   try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except OSError:raise UIError('brand-busy','Library has another active operation.',409)
   if not exists:
    created=os.open(db,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(created)
   con=sqlite3.connect(db,timeout=0);con.execute('PRAGMA temp_store=MEMORY');con.execute('PRAGMA cache_size=-2048');con.execute('PRAGMA synchronous=FULL');con.execute('PRAGMA foreign_keys=ON')
   if not exists:
    con.execute('PRAGMA page_size=4096');con.execute('PRAGMA journal_mode=DELETE');con.execute('PRAGMA max_page_count=16384');con.execute('PRAGMA application_id='+str(APP));con.execute('PRAGMA user_version=1')
    con.executescript('CREATE TABLE records(hash TEXT PRIMARY KEY, payload BLOB NOT NULL); CREATE TABLE blobs(hash TEXT PRIMARY KEY,data BLOB NOT NULL); CREATE TABLE heads(id TEXT PRIMARY KEY,hash TEXT NOT NULL REFERENCES records(hash)); CREATE TABLE assets(id TEXT PRIMARY KEY,hash TEXT NOT NULL REFERENCES records(hash)); CREATE TABLE rights_heads(id TEXT PRIMARY KEY,hash TEXT NOT NULL REFERENCES records(hash));')
    for table in ('records','blobs'):
     for op in ('UPDATE','DELETE'):con.execute(f"CREATE TRIGGER {table}_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'immutable record'); END")
    con.commit()
   check(con.execute('PRAGMA application_id').fetchone()[0]==APP and con.execute('PRAGMA user_version').fetchone()[0]==1,'Unknown library version; no migration.')
   check(con.execute('PRAGMA page_size').fetchone()[0]==4096,'Unsupported page size.')
   check(con.execute('PRAGMA journal_mode').fetchone()[0]=='delete','Unsupported journal mode.')
   check(con.execute('PRAGMA quick_check').fetchone()[0]=='ok','Library integrity check failed.')
   check(db.stat().st_size<=64*1024*1024,'Library size limit exceeded.')
   con.execute('PRAGMA max_page_count=16384');con.execute('BEGIN IMMEDIATE');yield con;con.commit()
  except sqlite3.Error as e:
   if con:con.rollback()
   raise UIError('brand-storage','Library transaction failed; no automatic repair/retry.',409) from e
  finally:
   if con:con.close()
   os.close(fd)
 def put(self,c,v):
  validate_record(v);raw=canonical(v);check(len(raw)<=65536,'Record exceeds 64 KiB.');check(c.execute('SELECT count(*) FROM records').fetchone()[0]<1000,'Library record limit reached.')
  h=hashlib.sha256(raw).hexdigest();c.execute('INSERT INTO records VALUES(?,?)',(h,raw));return h
 def get(self,c,h):
  row=c.execute('SELECT payload FROM records WHERE hash=?',(h,)).fetchone();check(row is not None,'Record not found.');raw=row[0];check(type(raw)==bytes and len(raw)<=65536,'Invalid stored record size/type.');check(hashlib.sha256(raw).hexdigest()==h,'Record hash mismatch.')
  try:v=json.loads(raw)
  except (ValueError,UnicodeError):raise UIError('brand-contract','Invalid stored JSON.')
  validate_record(v);check(canonical(v)==raw,'Noncanonical stored record.');return v
 def asset(self,c,i):
  identity(i);row=c.execute('SELECT hash FROM assets WHERE id=?',(i,)).fetchone();check(row is not None,'Asset not found.');v=self.get(c,row[0]);check(v['type']=='asset' and v['id']==i,'Asset identity mismatch.');return v
 def eligibility(self,c,i,scope,destination):
  check(scope in SCOPES and destination in DESTINATIONS,'Unsupported requested scope/destination.');self.asset(c,i);row=c.execute('SELECT hash FROM rights_heads WHERE id=?',(i,)).fetchone()
  if not row:return {'eligible':False,'reason':'missing-clearance','rights_hash':None}
  v=self.get(c,row[0]);check(v['type']=='rights' and v['asset_id']==i,'Rights identity mismatch.')
  ok=v['status']=='granted' and v['expires']>now() and scope in v['scopes'] and destination in v['destinations']
  return {'eligible':ok,'reason':'current-scoped-grant' if ok else 'unknown-denied-expired-or-out-of-scope','rights_hash':row[0]}
 def describe(self,c,h):
  v=self.get(c,h);out={'hash':h,'record':v}
  if v['type']=='brand':
   states=[self.eligibility(c,i,'internal_preview','library_metadata') for i in v['payload']['asset_ids']];matches=v['state']!='approved' or all(b['asset_id']==i and b['sha256']==self.asset(c,i)['sha256'] and b['rights_hash']==s['rights_hash'] for b,i,s in zip(v['bindings'],v['payload']['asset_ids'],states));out.update(current_review_eligible=all(s['eligible'] for s in states) and matches,approval_current=v['state']=='approved' and all(s['eligible'] for s in states) and matches,creative_use_enabled=False,asset_rights=states)
  return out
 def list(self):
  if not self.root.exists():return {'brands':[],'assets':[],'initialized':False,'creative_use_enabled':False}
  with self.transaction() as c:
   brands=[self.describe(c,h) for (h,) in c.execute('SELECT hash FROM heads ORDER BY id').fetchall()];assets=[]
   for (i,h) in c.execute('SELECT id,hash FROM assets ORDER BY id').fetchall():
    asset=self.asset(c,i);row=c.execute('SELECT data FROM blobs WHERE hash=?',(asset['sha256'],)).fetchone();check(row is not None and len(row[0])==asset['bytes'] and hashlib.sha256(row[0]).hexdigest()==asset['sha256'],'Asset bytes changed.')
    r=c.execute('SELECT hash FROM rights_heads WHERE id=?',(i,)).fetchone();assets.append({'hash':h,'record':asset,'rights':self.get(c,r[0]) if r else None,'rights_hash':r[0] if r else None,'eligibility':self.eligibility(c,i,'internal_preview','library_metadata'),'decoding_enabled':False})
   return {'brands':brands,'assets':assets,'initialized':True,'creative_use_enabled':False}
 def command(self,request):
  check(type(request)==dict,'Object required.');kind=request.get('action')
  with self.transaction(create=True) as c:
   if kind=='register_asset':
    exact(request,{'action','name','kind','provenance','data_base64','rights'});check(type(request['data_base64'])==str and len(request['data_base64'])<=12*1024*1024,'Bounded encoded bytes required.')
    try:data=base64.b64decode(request['data_base64'],validate=True)
    except (ValueError,TypeError):raise UIError('asset','Invalid base64.')
    check(0<len(data)<=8*1024*1024,'Asset must be 1 byte–8 MiB.');check(c.execute('SELECT count(*) FROM assets').fetchone()[0]<100,'Maximum 100 assets.');digest=hashlib.sha256(data).hexdigest()
    check(c.execute('SELECT coalesce(sum(length(data)),0) FROM blobs').fetchone()[0]+(0 if c.execute('SELECT 1 FROM blobs WHERE hash=?',(digest,)).fetchone() else len(data))<=32*1024*1024,'Opaque asset budget exhausted.')
    v={'type':'asset','id':str(uuid.uuid4()),'name':request['name'],'kind':request['kind'],'sha256':digest,'bytes':len(data),'provenance':request['provenance']};h=self.put(c,v)
    c.execute('INSERT OR IGNORE INTO blobs VALUES(?,?)',(digest,data));c.execute('INSERT INTO assets VALUES(?,?)',(v['id'],h));r={'type':'rights','id':str(uuid.uuid4()),'asset_id':v['id'],'previous':None,**rights(request['rights'])};rh=self.put(c,r);c.execute('INSERT INTO rights_heads VALUES(?,?)',(v['id'],rh));return {'asset_id':v['id'],'hash':h,'rights_hash':rh}
   if kind=='rights':
    exact(request,{'action','asset_id','expected_rights','rights'});self.asset(c,request['asset_id']);row=c.execute('SELECT hash FROM rights_heads WHERE id=?',(request['asset_id'],)).fetchone();check(row is not None and row[0]==request['expected_rights'],'Stale rights decision.')
    v={'type':'rights','id':str(uuid.uuid4()),'asset_id':request['asset_id'],'previous':row[0],**rights(request['rights'])};h=self.put(c,v);c.execute('UPDATE rights_heads SET hash=? WHERE id=?',(h,request['asset_id']));return {'rights_hash':h}
   if kind=='save':
    exact(request,{'action','brand_id','expected_head','payload'});payload(request['payload']);bid=request['brand_id'];parent=request['expected_head'];previous=None
    if bid is None:check(parent is None,'New brand cannot have a parent.');bid=str(uuid.uuid4())
    else:
     identity(bid);row=c.execute('SELECT hash FROM heads WHERE id=?',(bid,)).fetchone();check(row is not None and row[0]==parent,'Stale brand head.');previous=self.get(c,parent)
    for i in request['payload']['asset_ids']:self.asset(c,i)
    v={'type':'brand','brand_id':bid,'revision':previous['revision']+1 if previous else 1,'parent':parent,'state':'draft','reviewer':'','approved_at':None,'payload':request['payload'],'bindings':[]};h=self.put(c,v);c.execute('INSERT INTO heads VALUES(?,?) ON CONFLICT(id) DO UPDATE SET hash=excluded.hash',(bid,h));return self.describe(c,h)
   if kind=='approve':
    exact(request,{'action','brand_id','expected_head','reviewer','acknowledge'});identity(request['brand_id']);string(request['reviewer']);check(request['acknowledge'] is True,'Explicit manual-review acknowledgement required.')
    row=c.execute('SELECT hash FROM heads WHERE id=?',(request['brand_id'],)).fetchone();check(row is not None and row[0]==request['expected_head'],'Stale brand head.');old=self.get(c,row[0]);check(old['state']=='draft','Create a new draft revision first.');bindings=[]
    for i in old['payload']['asset_ids']:
     e=self.eligibility(c,i,'internal_preview','library_metadata');check(e['eligible'],'Asset clearance blocks approval.');a=self.asset(c,i);bindings.append({'asset_id':i,'sha256':a['sha256'],'rights_hash':e['rights_hash']})
    v={**old,'revision':old['revision']+1,'parent':row[0],'state':'approved','reviewer':request['reviewer'],'approved_at':now(),'bindings':bindings};h=self.put(c,v);c.execute('UPDATE heads SET hash=? WHERE id=?',(h,request['brand_id']));return self.describe(c,h)
   if kind=='history':
    exact(request,{'action','brand_id'});identity(request['brand_id']);row=c.execute('SELECT hash FROM heads WHERE id=?',(request['brand_id'],)).fetchone();check(row is not None,'Brand not found.');items=[];h=row[0]
    while h:
     check(len(items)<1000,'Invalid ancestry.');v=self.describe(c,h);check(v['record']['type']=='brand' and v['record']['brand_id']==request['brand_id'],'Invalid brand ancestry.');items.append(v);h=v['record']['parent']
    return {'versions':items}
   raise UIError('brand-contract','Unknown library action.')
