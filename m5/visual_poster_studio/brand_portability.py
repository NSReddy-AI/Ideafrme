"""Bounded logical ZIP_STORED backup; no extraction, SQL import or media decoding."""
import base64,hashlib,io,json,os,re,stat,struct,uuid,zipfile
from pathlib import Path
from .brands import Store,APP,canonical,validate_record,check,now
from .session import exclusive,sync_directory
from studio_manual_ui.service import UIError,safe,read,exact
MAX_PACKAGE=72*1024*1024
FORMAT='studio-brand-backup@1'
HEX=re.compile('[0-9a-f]{64}')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def empty():return {k:{} for k in ('records','blobs','heads','assets','rights_heads')}
def snapshot(store,c):
 s=empty()
 for h,raw in c.execute('SELECT hash,payload FROM records'):
  check(type(raw)==bytes and len(raw)<=65536 and digest(raw)==h,'Stored record hash/size mismatch.');s['records'][h]=raw
 for h,data in c.execute('SELECT hash,data FROM blobs'):
  check(type(data)==bytes and len(data)<=8*1024*1024 and digest(data)==h,'Stored asset hash mismatch.');s['blobs'][h]=data
 for table in ('heads','assets','rights_heads'):s[table]=dict(c.execute('SELECT id,hash FROM '+table))
 validate_state(s,{})
 return s

def validate_state(s,omissions):
 check(len(s['records'])<=1000 and len(s['assets'])<=100 and len(s['blobs'])<=100,'Library entry bound exceeded.')
 check(sum(len(b) for b in s['blobs'].values())<=32*1024*1024,'Asset byte bound exceeded.')
 records={}
 for h,raw in s['records'].items():
  check(type(h)==str and HEX.fullmatch(h) and len(raw)<=65536 and digest(raw)==h,'Record identity mismatch.')
  try:v=json.loads(raw)
  except (ValueError,UnicodeError):raise UIError('backup','Malformed record JSON.')
  validate_record(v);check(canonical(v)==raw,'Noncanonical record.');records[h]=v
 assets={};brands={};rights={}
 for h,v in records.items():
  if v['type']=='asset':
   check(v['id'] not in assets,'Competing asset identity.');assets[v['id']]=h
  elif v['type']=='brand':brands.setdefault(v['brand_id'],[]).append(h)
  else:rights.setdefault(v['asset_id'],[]).append(h)
 check(assets==s['assets'],'Asset pointer coverage mismatch.')
 needed={records[h]['sha256'] for h in assets.values()}
 check(set(s['blobs']).isdisjoint(omissions) and set(s['blobs'])|set(omissions)==needed,'Blob closure mismatch.')
 for i,h in assets.items():
  a=records[h]
  if a['sha256'] in s['blobs']:check(len(s['blobs'][a['sha256']])==a['bytes'] and digest(s['blobs'][a['sha256']])==a['sha256'],'Asset bytes mismatch.')
 check(set(brands)==set(s['heads']) and set(rights)==set(s['rights_heads']),'Head coverage mismatch.')
 def chain(group,head,parent_key,kind,identity_key,identity):
  check(head in group,'Head not in its history.');seen=set();h=head
  while h is not None:
   check(h in group and h not in seen,'Incomplete/cyclic ancestry.');seen.add(h);v=records[h];check(v['type']==kind and v[identity_key]==identity,'Foreign ancestry.')
   parent=v[parent_key]
   if parent is not None:check(parent in records and records[parent]['type']==kind and records[parent][identity_key]==identity,'Missing/foreign parent.')
   if kind=='brand':
    check(v['revision']==(records[parent]['revision']+1 if parent in records else 1),'Invalid brand revision arithmetic.')
    if v['state']=='approved':
     check(parent in records and records[parent]['state']=='draft' and records[parent]['payload']==v['payload'],'Approval changed its draft payload.')
     for binding,i in zip(v['bindings'],v['payload']['asset_ids']):
      check(binding['asset_id']==i and i in assets and binding['sha256']==records[assets[i]]['sha256'],'Approval asset binding mismatch.')
      r=records.get(binding['rights_hash']);check(r is not None and r['type']=='rights' and r['asset_id']==i and r['status']=='granted' and 'internal_preview' in r['scopes'] and 'library_metadata' in r['destinations'] and r['expires']>v['approved_at'],'Approval rights binding invalid.')
   h=parent
  check(seen==set(group),'Competing or unreachable revisions.')
 for bid,group in brands.items():
  for h in group:check(all(i in assets for i in records[h]['payload']['asset_ids']),'Brand asset dependency missing.')
  chain(group,s['heads'][bid],'parent','brand','brand_id',bid)
 for aid,group in rights.items():
  check(aid in assets,'Rights reference unknown asset.');chain(group,s['rights_heads'][aid],'previous','rights','asset_id',aid)
 return records

def fingerprint(s):
 return digest(canonical({**{k:s[k] for k in ('heads','assets','rights_heads')},'records':sorted(s['records']),'blobs':{h:len(b) for h,b in s['blobs'].items()}}))

def build_package(store):
 with store.transaction() as c:s=snapshot(store,c)
 records=validate_state(s,{})
 eligible=set(s['blobs'])
 for aid,h in s['assets'].items():
  rh=s['rights_heads'].get(aid);r=records.get(rh)
  if not (r and r['status']=='granted' and r['expires']>now() and 'redistribute' in r['scopes'] and 'library_metadata' in r['destinations']):eligible.discard(records[h]['sha256'])
 omitted={h:'not-cleared-for-portable-copy' for h in s['blobs'] if h not in eligible}
 files={};entries={}
 for table,suffix in [('records','.json'),('blobs','.bin')]:
  entries[table]={}
  for h,raw in s[table].items():
   if table=='blobs' and h in omitted:continue
   path=table+'/'+h+suffix;files[path]=raw;entries[table][h]={'path':path,'bytes':len(raw),'sha256':h}
 manifest={'format':FORMAT,'version':1,'store_schema':{'application_id':APP,'user_version':1},**entries,'omitted_blobs':omitted,**{k:s[k] for k in ('heads','assets','rights_heads')}}
 files['manifest.json']=canonical(manifest);check(len(files['manifest.json'])<=1024*1024,'Manifest limit exceeded.')
 check(sum(len(v) for v in files.values())+len(files)*256<=MAX_PACKAGE,'Backup exceeds package bound.')
 stream=io.BytesIO()
 with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED,allowZip64=False) as z:
  for path,raw in sorted(files.items()):
   item=zipfile.ZipInfo(path,(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_STORED;item.external_attr=0o100644<<16;z.writestr(item,raw)
 raw=stream.getvalue();parse(raw);return raw

def _parse(raw):
 check(type(raw)==bytes and 22<=len(raw)<=MAX_PACKAGE,'Package size refused.')
 # Own v1 writer has no ZIP comment, ZIP64, prefix or multi-disk records.
 tail=raw[-22:];check(tail[:4]==b'PK\x05\x06','Unsupported ZIP trailer.')
 _,disk,central_disk,count_disk,count,size,offset,comment=struct.unpack('<4s4H2IH',tail)
 check(disk==central_disk==comment==0 and count==count_disk and 1<=count<=1101 and size<=256*1024 and offset+size==len(raw)-22,'ZIP directory bounds refused.')
 try:
  with zipfile.ZipFile(io.BytesIO(raw),'r',allowZip64=False) as z:
   infos=z.infolist();check(len(infos)==count and len({i.filename for i in infos})==count,'Duplicate ZIP entries.')
   files={};ranges=[];total=0
   for item in infos:
    name=item.filename;check(name=='manifest.json' or re.fullmatch(r'(records/[0-9a-f]{64}\.json|blobs/[0-9a-f]{64}\.bin)',name),'Unsafe or unknown archive path.')
    mode=item.external_attr>>16;check(stat.S_IFMT(mode) in (0,stat.S_IFREG) and not item.is_dir() and item.compress_type==zipfile.ZIP_STORED and item.flag_bits==0 and not item.extra and not item.comment,'Unsupported ZIP entry.')
    limit=1024*1024 if name=='manifest.json' else 65536 if name.startswith('records/') else 8*1024*1024
    check(0<item.file_size<=limit and item.compress_size==item.file_size,'Entry size/compression refused.');total+=item.file_size;check(total<=MAX_PACKAGE,'Aggregate byte limit.')
    start=item.header_offset;check(0<=start and start+30<=offset and raw[start:start+4]==b'PK\x03\x04','Invalid local header.')
    check(struct.unpack_from('<HH',raw,start+6)==(0,0),'Unsupported local flags/method.');n,e=struct.unpack_from('<HH',raw,start+26);end=start+30+n+e+item.file_size;check(e==0 and raw[start+30:start+30+n]==name.encode('ascii') and end<=offset,'Local header bounds/name mismatch.');ranges.append((start,end));files[name]=z.read(item)
   cursor=0
   for start,end in sorted(ranges):check(start==cursor,'Overlapping/gapped archive entries.');cursor=end
   check(cursor==offset,'Unexpected archive data.')
 except (zipfile.BadZipFile,NotImplementedError,RuntimeError,ValueError,EOFError) as e:
  if isinstance(e,UIError):raise
  raise UIError('backup','Invalid ZIP package.') from e
 check('manifest.json' in files,'Manifest missing.')
 try:m=json.loads(files['manifest.json'])
 except (ValueError,UnicodeError):raise UIError('backup','Malformed manifest.')
 exact(m,{'format','version','store_schema','records','blobs','omitted_blobs','heads','assets','rights_heads'})
 check(canonical(m)==files['manifest.json'] and m['format']==FORMAT and type(m['version'])==int and m['version']==1 and m['store_schema']=={'application_id':APP,'user_version':1},'Unsupported/noncanonical backup version.')
 exact(m['store_schema'],{'application_id','user_version'});check(all(type(v)==int for v in m['store_schema'].values()),'Invalid store version types.')
 s=empty();expected={'manifest.json'}
 for table,suffix in [('records','.json'),('blobs','.bin')]:
  check(type(m[table])==dict and len(m[table])<=(1000 if table=='records' else 100),'Entry count refused.')
  for h,entry in m[table].items():
   check(type(h)==str and HEX.fullmatch(h),'Invalid entry hash.');exact(entry,{'path','bytes','sha256'});path=table+'/'+h+suffix
   check(entry['path']==path and entry['sha256']==h and type(entry['bytes'])==int and path in files and len(files[path])==entry['bytes'] and digest(files[path])==h,'Entry integrity mismatch.');s[table][h]=files[path];expected.add(path)
 check(set(files)==expected,'Unlisted/incomplete package.')
 for k in ('heads','assets','rights_heads'):check(type(m[k])==dict and len(m[k])<=1000,'Invalid pointer table.');s[k]=m[k]
 omissions=m['omitted_blobs'];check(type(omissions)==dict and len(omissions)<=100 and all(type(h)==str and HEX.fullmatch(h) and reason=='not-cleared-for-portable-copy' for h,reason in omissions.items()),'Invalid omission declaration.')
 records=validate_state(s,omissions);return {'state':s,'records':records,'omissions':omissions,'package_sha256':digest(raw),'manifest_sha256':digest(files['manifest.json'])}

def parse(raw):
 try:return _parse(raw)
 except UIError:raise
 except (ValueError,KeyError,TypeError,OverflowError,RecursionError,struct.error) as exc:raise UIError('backup','Malformed backup structure.') from exc

def ancestor(a,b,records,parent):
 seen=set()
 while b is not None:
  if a==b:return True
  if b in seen or b not in records:return False
  seen.add(b);b=records[b].get(parent)
 return False

def plan(parsed,local):
 incoming=parsed['state'];records={h:json.loads(v) for h,v in {**local['records'],**incoming['records']}.items()};conflicts=[];heads=dict(local['heads']);rhs=dict(local['rights_heads']);quarantines={}
 for i,h in incoming['assets'].items():
  if i in local['assets'] and local['assets'][i]!=h:conflicts.append('Conflicting asset identity '+i)
 for table,parent in [('heads','parent'),('rights_heads','previous')]:
  output=heads if table=='heads' else rhs
  for i,h in incoming[table].items():
   old=local[table].get(i)
   if old==h:continue
   if old and ancestor(h,old,records,parent):continue
   if old and not ancestor(old,h,records,parent):conflicts.append('Divergent '+table+' history '+i);continue
   if table=='rights_heads' and records[h]['status']=='granted':quarantines[i]=h
   else:output[i]=h
 missing=sorted(set(parsed['omissions'])-set(local['blobs']))
 union_records=set(local['records'])|set(incoming['records']);union_assets={**local['assets'],**incoming['assets']};union_blobs={**local['blobs'],**incoming['blobs']}
 if len(union_records)+len(quarantines)>1000 or len(union_assets)>100 or sum(len(b) for b in union_blobs.values())>32*1024*1024:conflicts.append('Destination capacity exceeded, including quarantine records.')
 result={'package_sha256':parsed['package_sha256'],'manifest_sha256':parsed['manifest_sha256'],'destination_fingerprint':fingerprint(local),'brands':len(incoming['heads']),'versions':sum(v['type']=='brand' for v in parsed['records'].values()),'assets':len(incoming['assets']),'rights_decisions':sum(v['type']=='rights' for v in parsed['records'].values()),'new_records':len(set(incoming['records'])-set(local['records'])),'new_blobs':len(set(incoming['blobs'])-set(local['blobs'])),'is_noop':not quarantines and not (set(incoming['records'])-set(local['records'])) and not (set(incoming['blobs'])-set(local['blobs'])) and heads==local['heads'] and rhs==local['rights_heads'],'duplicate_records':len(set(local['records'])&set(incoming['records'])),'duplicate_blobs':len(set(local['blobs'])&set(incoming['blobs'])),'conflicts':conflicts,'missing_dependencies':missing,'omitted_assets':parsed['omissions'],'rights_quarantined':sorted(quarantines),'can_restore':not conflicts and not missing,'creative_use_enabled':False,'brand_summaries':[{'id':i,'name':records[h]['payload']['name'],'state':records[h]['state'],'incoming_head':h,'destination_head':heads[i]} for i,h in incoming['heads'].items()]}
 return result,heads,rhs,quarantines

def preview(store,raw):
 parsed=parse(raw)
 if store.root.exists():
  with store.transaction() as c:local=snapshot(store,c)
 else:local=empty()
 return plan(parsed,local)[0]

def restore(store,raw,expected_destination,expected_package,acknowledge,fault=None):
 check(acknowledge is True,'Explicit restore acknowledgement required.');parsed=parse(raw);check(parsed['package_sha256']==expected_package,'Package changed since preview.')
 # Validate missing dependencies/conflicts before initializing an absent library.
 first=preview(store,raw);check(first['destination_fingerprint']==expected_destination,'Destination changed since preview.');check(first['can_restore'],'Restore blocked by conflicts/missing dependencies.')
 with store.transaction(create=True) as c:
  local=snapshot(store,c);result,heads,rhs,quarantines=plan(parsed,local);check(fingerprint(local)==expected_destination and result['can_restore'],'Stale or blocked restore preview.')
  incoming=parsed['state']
  for h,data in incoming['records'].items():c.execute('INSERT OR IGNORE INTO records VALUES(?,?)',(h,data))
  for h,data in incoming['blobs'].items():c.execute('INSERT OR IGNORE INTO blobs VALUES(?,?)',(h,data))
  if fault:fault('after-insert')
  for i,h in incoming['assets'].items():c.execute('INSERT OR IGNORE INTO assets VALUES(?,?)',(i,h))
  for i,parent in quarantines.items():
   v={'type':'rights','id':str(uuid.uuid4()),'asset_id':i,'previous':parent,'status':'unknown','authority':'Restore quarantine','evidence':'Package '+parsed['package_sha256']+' is not current clearance proof. New local review required.','scopes':[],'destinations':[],'expires':None};rhs[i]=store.put(c,v)
  for table,values in [('heads',heads),('rights_heads',rhs)]:
   for i,h in values.items():c.execute('INSERT INTO '+table+' VALUES(?,?) ON CONFLICT(id) DO UPDATE SET hash=excluded.hash',(i,h))
  snapshot(store,c)
  if fault:fault('before-commit')
 return {**result,'restored':True,'approval_or_permission_granted':False}

def save_backup(store):
 raw=build_package(store);h=digest(raw);root=safe(store.root.parent/(store.root.name+'-backups'))
 if not root.exists():root.mkdir(mode=0o700);sync_directory(root.parent)
 entries=list(root.iterdir());check(all(safe(p).is_file() and re.fullmatch(r'[0-9a-f]{64}\.zip',p.name) for p in entries),'Unexpected backup-directory entry; explicit review required.');check(len(entries)<=20,'Backup count limit exceeded.')
 target=safe(root/(h+'.zip'))
 if target.exists():check(read(target,MAX_PACKAGE)==raw,'Existing backup hash mismatch.')
 else:
  check(len(entries)<20 and sum(safe(p).stat().st_size for p in entries if p.is_file())+len(raw)<=256*1024*1024,'Backup retention quota exhausted; nothing deleted.');exclusive(target,raw)
 check(read(target,MAX_PACKAGE)==raw,'Backup readback failed.');sync_directory(root);parsed=parse(raw)
 return {'path':str(target),'package_sha256':h,'manifest_sha256':parsed['manifest_sha256'],'bytes':len(raw),'omitted_assets':parsed['omissions'],'physical_power_loss_verified':False}

def upload(value):
 check(type(value)==str and len(value)<=((MAX_PACKAGE+2)//3)*4,'Bounded base64 package required.')
 try:raw=base64.b64decode(value,validate=True)
 except (ValueError,TypeError):raise UIError('backup','Invalid package encoding.')
 check(len(raw)<=MAX_PACKAGE,'Package too large.');return raw
