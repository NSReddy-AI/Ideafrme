"""Explicit media-workflow@2 fork: frozen creative@1 base + editable PNG overlays.

No media records are inserted into the accepted manual document/history. The
distinct envelope is authoritative; older readers must refuse it. Drafts only.
"""
import base64,copy,fcntl,html,json,math,os,re,struct,threading,uuid,zlib,time
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import manual_subset,read,decode,exact,RUNTIME
from visual_poster_studio.session import exclusive,sync_directory
from visual_poster_studio.binding_workflow import pin
from visual_poster_studio.project_bindings import validate as validate_binding
from visual_poster_studio.brand_application import validate as validate_brand,overlaps
from visual_poster_studio.scene import build_scene
from visual_poster_studio.fonts import Fonts
from .controller import Decoder,Pixels,Refused,sha,safe
FORMAT='studio-media-workflow@2'
BUDGET=128*1024*1024
def require(ok,detail):
 if not ok:raise Refused(detail)
def packet(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
def normalized_png(pixels):
 """Fixed unfiltered RGBA container over qualified bytes; zlib supplies DEFLATE.
 No source-image parsing, profiles, metadata, external references or codec options.
 """
 require(isinstance(pixels,Pixels),'Only supervised pixels accepted')
 rows=b''.join(b'\0'+pixels.rgba[y*pixels.width*4:(y+1)*pixels.width*4] for y in range(pixels.height))
 out=b'\x89PNG\r\n\x1a\n'+packet(b'IHDR',struct.pack('>IIBBBBB',pixels.width,pixels.height,8,6,0,0,0))+packet(b'IDAT',zlib.compress(rows,6))+packet(b'IEND',b'')
 require(len(out)<=8*1024*1024,'Normalized PNG exceeds 8 MiB; no truncation');return out
def geometry(v):
 require(type(v)==dict and set(v)=={'x','y','width','height'},'Complete geometry required')
 require(all(type(n)==int for n in v.values()),'Integer geometry required')
 require(v['x']>=0 and v['y']>=0 and v['width']>0 and v['height']>0 and v['x']+v['width']<=1080 and v['y']+v['height']<=1350,'Geometry outside canvas')
 return v
class Workflow:
 def __init__(self,root,library,decoder,*,base=None,binding=None,acknowledge=False,fault=None):
  self.root=safe(Path(root));require(self.root.is_relative_to(RUNTIME) and self.root.name.startswith('png-workflow-'),'Owned png-workflow-* runtime root required')
  self.library=library;self.decoder=decoder;self.lock=threading.RLock();self.fault=fault;self.blocked=False;self.fd=None
  create=base is not None
  if create:require(acknowledge is True,'Explicit version-2 fork acknowledgement required');self.root.mkdir(mode=0o700,parents=True,exist_ok=False)
  try:
   self.fd=os.open(safe(self.root/'png-writer.lock'),os.O_RDWR|os.O_NOFOLLOW|((os.O_CREAT|os.O_EXCL) if create else 0),0o600)
   try:fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise Refused('Another PNG workflow writer is active')
   if create:
    manual_subset(base);core.validate(base,self.root);require(binding is not None,'Pinned brand binding required')
    validate_binding(binding,binding['session_id'],base['id']);self._brand(binding)
    self.identity=str(uuid.uuid4());exclusive(self.root/'png-session.json',canonical({'format':'studio-png-session@1','id':self.identity}),0o444)
    for name in ('generations','pixels','exports'):(self.root/name).mkdir(mode=0o700)
    source=copy.deepcopy(base);source['approvals']=[];source['revision']+=1
    state={'format':FORMAT,'version':2,'session_id':self.identity,'generation':1,'parent':None,'document':source,'source_document_sha256':sha(canonical(base)),'binding':copy.deepcopy(binding),'placements':[],'history':{'version':1,'cursor':0,'transactions':[]},'approvals':[]}
    self._publish(state,None)
   else:
    m=decode(read(self.root/'png-session.json',1024));exact(m,{'format','id'});require(m['format']=='studio-png-session@1','Unsupported owner');self.identity=m['id'];self.current()
  except BaseException:self.close();raise
 def close(self):
  if self.fd is not None:os.close(self.fd);self.fd=None
 def _brand(self,binding):
  require(binding['brand'] is not None,'Approved brand required');require(pin(SimpleNamespace(brand_library=self.library),binding['brand']['hash'])==binding['brand'],'Pinned brand no longer current')
 def _live_locked(self,c,s):
  # Reuse the existing pin evaluator on the ALREADY HELD SQLite/OS transaction;
  # no nested writer lock and no gap between final rights check and publication.
  library=self.library
  class Reader:
   def transaction(self):return nullcontext(c)
   def __getattr__(self,n):return getattr(library,n)
  require(pin(SimpleNamespace(brand_library=Reader()),s['binding']['brand']['hash'])==s['binding']['brand'],'Pinned brand no longer current')
  for p in s['placements']:
   r,_=self._receipt(p['receipt']);asset=library.asset(c,p['asset_id']);require(asset['sha256']==r['asset_sha256'],'Asset changed')
   for scope,destination in [('internal_preview','library_metadata'),('commercial_design','poster')]:
    grant=library.eligibility(c,p['asset_id'],scope,destination);require(grant['eligible'] and grant['rights_hash']==r['rights_hash'],'Live rights changed')
 def _asset(self,binding,identity,*,export_svg=False):
  self._brand(binding);matches=[x for x in binding['brand']['record']['bindings'] if x['asset_id']==identity];require(len(matches)==1,'Asset is not approved in pinned brand')
  match=matches[0]
  with self.library.transaction() as c:
   asset=self.library.asset(c,identity);require(asset['kind'] in ('logo','image') and asset['sha256']==match['sha256'],'Approved PNG asset identity mismatch')
   scopes=[('internal_preview','library_metadata'),('commercial_design','poster')]+([('redistribute','poster')] if export_svg else [])
   for scope,destination in scopes:
    grant=self.library.eligibility(c,identity,scope,destination);require(grant['eligible'] and grant['rights_hash']==match['rights_hash'],'Rights missing, expired, changed or revoked')
   length=c.execute('SELECT length(data) FROM blobs WHERE hash=?',(asset['sha256'],)).fetchone();require(length and length[0]==asset['bytes'] and 0<length[0]<=8*1024*1024,'Asset byte limit')
   raw=c.execute('SELECT data FROM blobs WHERE hash=?',(asset['sha256'],)).fetchone()[0];require(type(raw)==bytes and sha(raw)==asset['sha256'],'Asset bytes changed')
   return asset,raw,match['rights_hash']
 def _usage(self):
  count=0;total=0
  for p in self.root.rglob('*'):
   safe(p);count+=1
   require(count<=2048,'Session entry limit')
   if p.is_file():total+=p.stat().st_size
  return total
 def _reserve(self,n):require(self._usage()+n<=BUDGET,'128 MiB retained session budget exhausted; evidence retained')
 def head(self):
  h=decode(read(self.root/'HEAD.json',1024));exact(h,{'format','name','sha256'});require(h['format']=='studio-png-head@1' and re.fullmatch(r'[0-9]{8}-[0-9a-f]{32}',h['name']) and re.fullmatch('[0-9a-f]{64}',h['sha256']),'Invalid HEAD; explicit recovery required');return h
 def token(self):return sha(canonical(self.head()))
 def _receipt(self,identity):
  require(type(identity)==str and re.fullmatch('[0-9a-f]{64}',identity),'Invalid pixel identity');p=safe(self.root/'pixels'/identity);raw=read(p/'receipt.json',4096);r=decode(raw)
  exact(r,{'format','asset_id','asset_sha256','rights_hash','profile','width','height','png_sha256','rgba_sha256'})
  require(r['format']=='studio-qualified-png@1' and sha(raw)==identity and r['profile']==self.decoder.profile,'Unqualified or stale pixel profile')
  data=read(p/'normalized.png',8*1024*1024);require(sha(data)==r['png_sha256'],'Qualified PNG hash changed');return r,data
 def _validate(self,s):
  exact(s,{'format','version','session_id','generation','parent','document','source_document_sha256','binding','placements','history','approvals'})
  require(s['format']==FORMAT and type(s['version'])==int and s['version']==2 and s['session_id']==self.identity,'Unsupported media workflow')
  require(type(s['generation'])==int and 1<=s['generation']<=200 and s['approvals']==[],'Invalid generation or attempted approval resurrection')
  manual_subset(s['document']);core.validate(s['document'],self.root);require(s['document']['approvals']==[],'Draft base approvals must be invalidated')
  validate_binding(s['binding'],s['binding']['session_id'],s['document']['id'])
  require(type(s['source_document_sha256'])==str and re.fullmatch('[0-9a-f]{64}',s['source_document_sha256']),'Source identity required')
  def placements(items):
   require(type(items)==list and len(items)+len(s['document']['elements'])<=64,'Layer limit');seen=set()
   for p in items:
    exact(p,{'id','receipt','asset_id','kind','geometry'});require(type(p['id'])==str and re.fullmatch('[0-9a-f-]{36}',p['id']) and p['id'] not in seen,'Duplicate placement');seen.add(p['id']);geometry(p['geometry']);r,_=self._receipt(p['receipt']);require(r['asset_id']==p['asset_id'] and p['kind'] in ('logo','image'),'Placement receipt mismatch')
    g=p['geometry'];require(abs(g['width']*r['height']-g['height']*r['width'])<=max(r['width'],r['height']),'Aspect ratio must be preserved')
  placements(s['placements']);h=s['history'];exact(h,{'version','cursor','transactions'});require(h['version']==1 and type(h['cursor'])==int and type(h['transactions'])==list and 0<=h['cursor']<=len(h['transactions'])<=100,'Invalid media history')
  previous=[]
  for t in h['transactions']:
   exact(t,{'before','after','operation'});require(t['operation'] in ('place','geometry','remove') and t['before']==previous and t['before']!=t['after'],'Invalid media transaction chain');placements(t['before']);placements(t['after']);previous=t['after']
   a,b=t['before'],t['after']
   if t['operation']=='place':require(len(b)==len(a)+1 and b[:-1]==a and b[-1]['id'] not in {x['id'] for x in a},'Invalid place transaction')
   elif t['operation']=='remove':require(len(b)==len(a)-1 and any(a[:i]+a[i+1:]==b for i in range(len(a))),'Invalid remove transaction')
   else:
    require(len(a)==len(b) and [x['id'] for x in a]==[x['id'] for x in b],'Geometry cannot change identities/order')
    changed=[(x,y) for x,y in zip(a,b) if x!=y];require(len(changed)==1 and {k:v for k,v in changed[0][0].items() if k!='geometry'}=={k:v for k,v in changed[0][1].items() if k!='geometry'},'Unauthorized geometry mutation')
  expected=h['transactions'][h['cursor']-1]['after'] if h['cursor'] else []
  require(s['placements']==expected,'History and live placements disagree');return s
 def _load(self,name):
  require(type(name)==str and re.fullmatch(r'[0-9]{8}-[0-9a-f]{32}',name),'Generation path refused');p=safe(self.root/'generations'/name/'workflow.json');raw=read(p,8*1024*1024);require(not p.stat().st_mode&0o222,'Immutable generation required');s=decode(raw);self._validate(s);require(raw==canonical(s) and s['generation']==int(name[:8]),'Noncanonical generation');return s,sha(raw)
 def current(self):
  with self.lock:
   h=self.head();first=None;child=None;name=h['name'];seen=set()
   while name is not None:
    require(name not in seen and len(seen)<200,'Invalid ancestry');seen.add(name);s,d=self._load(name)
    if first is None:require(d==h['sha256'],'HEAD mismatch');first=s
    if child:
     require(child['generation']==s['generation']+1 and all(child[k]==s[k] for k in ('document','binding','source_document_sha256')),'Frozen base or ancestry changed')
     a,b=s['history'],child['history'];travel=a['transactions']==b['transactions'] and abs(a['cursor']-b['cursor'])==1
     edit=b['cursor']==a['cursor']+1 and len(b['transactions'])==b['cursor'] and b['transactions'][:-1]==a['transactions'][:a['cursor']] and b['transactions'][-1]['before']==s['placements']
     require(travel or edit,'Unauthorized history rewrite')
    child=s;name=s['parent']
   require(child['generation']==1,'Missing initial generation');return copy.deepcopy(first)
 def candidates(self):
  result=[]
  for p in sorted((self.root/'generations').iterdir()):
   safe(p)
   try:s,h=self._load(p.name);result.append({'name':p.name,'sha256':h,'generation':s['generation'],'valid':True})
   except (OSError,ValueError,KeyError,TypeError):result.append({'name':p.name,'valid':False})
  return result
 def recover_copy(self,name,destination,*,acknowledge=False):
  """Explicit restore to new physical root; preserve immutable selected ancestry.
  No repair of original HEAD, rewriting records, shared files or previous exports.
  """
  require(acknowledge is True,'Acknowledge later edits and exports are excluded')
  destination=safe(Path(destination));require(destination.is_relative_to(RUNTIME) and destination.name.startswith('png-workflow-'),'Owned fresh recovery destination required');require(not destination.exists(),'Recovery destination exists')
  chain=[];receipts=set();cursor=name
  while cursor is not None:
   require(len(chain)<200 and cursor not in {x[0] for x in chain},'Invalid recovery ancestry');s,h=self._load(cursor);chain.append((cursor,s,h))
   for t in s['history']['transactions']:
    receipts.update(p['receipt'] for p in t['after']+t['before'])
   cursor=s['parent']
  require(chain[-1][1]['generation']==1,'Incomplete recovery chain')
  planned=sum(len(canonical(item[1])) for item in chain)+sum(len(self._receipt(r)[1])+len(canonical(self._receipt(r)[0])) for r in receipts)+8192
  require(planned<=BUDGET,'Recovery copy exceeds session budget')
  destination.mkdir(mode=0o700)
  for directory in ('generations','pixels','exports'):(destination/directory).mkdir(mode=0o700)
  exclusive(destination/'png-session.json',read(self.root/'png-session.json',1024),0o444);exclusive(destination/'png-writer.lock',b'')
  for n,s,h in chain:
   p=destination/'generations'/n;p.mkdir(mode=0o700);exclusive(p/'workflow.json',canonical(s),0o444);sync_directory(p)
  for rid in receipts:
   r,data=self._receipt(rid);p=destination/'pixels'/rid;p.mkdir(mode=0o700);exclusive(p/'receipt.json',canonical(r),0o444);exclusive(p/'normalized.png',data,0o444);sync_directory(p)
  exclusive(destination/'recovery-origin.json',canonical({'format':'studio-png-recovery@1','source_session_id':self.identity,'selected_generation':name,'selected_sha256':chain[0][2],'later_edits_and_exports_excluded':True}),0o444)
  exclusive(destination/'HEAD.json',canonical({'format':'studio-png-head@1','name':name,'sha256':chain[0][2]}));sync_directory(destination/'generations');sync_directory(destination/'pixels');sync_directory(destination)
  restored=Workflow(destination,self.library,self.decoder);restored.close();return destination
 def _publish(self,s,expected):
  require(not self.blocked,'Uncertain publication; explicit reopen/recovery required')
  self._validate(s);require((expected is None and not (self.root/'HEAD.json').exists()) or self.token()==expected,'Stale media head')
  raw=canonical(s);require(len(raw)<=8*1024*1024,'Metadata budget');self._reserve(len(raw)+4096);name=f"{s['generation']:08d}-"+uuid.uuid4().hex;p=self.root/'generations'/name
  try:
   p.mkdir(mode=0o700);exclusive(p/'workflow.json',raw,0o444);sync_directory(p);sync_directory(p.parent);self._load(name)
   if self.fault:self.fault('before-head')
   require((expected is None and not (self.root/'HEAD.json').exists()) or self.token()==expected,'Stale publication')
   pending=self.root/('HEAD-'+uuid.uuid4().hex+'.pending');exclusive(pending,canonical({'format':'studio-png-head@1','name':name,'sha256':sha(raw)}));os.replace(pending,self.root/'HEAD.json')
   if self.fault:self.fault('after-head')
   sync_directory(self.root)
  except BaseException:self.blocked=True;raise
  return self.token()
 def _next(self,s,expected):
  require(self.token()==expected,'Stale media head');s['parent']=self.head()['name'];s['generation']+=1;return self._publish(s,expected)
 def place(self,identity,g,expected,*,cancel=None):
  with self.lock:
   require(not self.blocked and self.token()==expected,'Stale or blocked workflow');s=self.current();g=geometry(g);asset,raw,grant=self._asset(s['binding'],identity)
   pixels=self.decoder.decode(raw,expected_sha256=asset['sha256'],cancel=cancel)
   require(abs(g['width']*pixels.height-g['height']*pixels.width)<=max(pixels.width,pixels.height),'Aspect-ratio protection')
   p=validate_brand(s['document'],s['binding']);effects={r['effect'] for r in p['recognized_rules']};require('no-assets' not in effects,'Brand forbids external assets')
   if 'palette-fonts' in effects:
    palette={bytes.fromhex(c[1:]) for c in p['colors']}
    require(all(pixels.rgba[i+3]==0 or (pixels.rgba[i+3]==255 and pixels.rgba[i:i+3] in palette) for i in range(0,len(pixels.rgba),4)),'Image pixels conflict with strict palette rule')
   self._asset(s['binding'],identity);require(cancel is None or not cancel.is_set(),'Cancelled before publication');normalized=normalized_png(pixels)
   receipt={'format':'studio-qualified-png@1','asset_id':identity,'asset_sha256':asset['sha256'],'rights_hash':grant,'profile':pixels.profile,'width':pixels.width,'height':pixels.height,'png_sha256':sha(normalized),'rgba_sha256':sha(pixels.rgba)};rraw=canonical(receipt);rid=sha(rraw);directory=self.root/'pixels'/rid
   if not directory.exists():
    self._reserve(len(normalized)+len(rraw)+4096);directory.mkdir(mode=0o700);exclusive(directory/'normalized.png',normalized,0o444);exclusive(directory/'receipt.json',rraw,0o444);sync_directory(directory);sync_directory(directory.parent)
   placement={'id':str(uuid.uuid4()),'receipt':rid,'asset_id':identity,'kind':asset['kind'],'geometry':g}
   target=s['placements']+[placement];self._constraints(s,target);self._transaction(s,target,'place')
   with self.library.transaction() as c:self._live_locked(c,s);self._next(s,expected)
   return placement['id']
 def _constraints(self,s,items):
  p=validate_brand(s['document'],s['binding']);margin=p['minimum_margin'] or 0
  for i in items:
   g=i['geometry'];require(g['x']>=margin and g['y']>=margin and g['x']+g['width']<=1080-margin and g['y']+g['height']<=1350-margin,'Brand margin violation')
   require(not any(e['type']=='text' and overlaps(g,e) for e in s['document']['elements']),'Media must not obscure existing text')
 def _transaction(self,s,target,kind):
  h=s['history'];h['transactions']=h['transactions'][:h['cursor']]+[{'before':copy.deepcopy(s['placements']),'after':copy.deepcopy(target),'operation':kind}];h['cursor']+=1;s['placements']=target
 def action(self,kind,expected,identity=None,g=None):
  with self.lock:
   require(not self.blocked and self.token()==expected,'Stale or blocked workflow');s=self.current()
   if kind in ('undo','redo'):
    h=s['history'];position=h['cursor']+(-1 if kind=='undo' else 1);require(0<=position<=len(h['transactions']),'No history action available');h['cursor']=position;s['placements']=copy.deepcopy(h['transactions'][position-1]['after']) if position else []
   else:
    require(kind in ('geometry','remove'),'Unsupported operation');target=copy.deepcopy(s['placements']);matches=[p for p in target if p['id']==identity];require(len(matches)==1,'Unknown layer')
    if kind=='geometry':matches[0]['geometry']=geometry(g)
    else:target.remove(matches[0])
    require(target!=s['placements'],'No-op rejected');self._constraints(s,target);self._transaction(s,target,kind)
   if kind=='geometry':
    with self.library.transaction() as c:self._live_locked(c,s);return self._next(s,expected)
   return self._next(s,expected)
 def scene(self,*,export_svg=False):
  s=self.current();self._brand(s['binding']);self._constraints(s,s['placements']);scene=build_scene(s['document'],Fonts());media=[]
  for p in s['placements']:
   asset,_,grant=self._asset(s['binding'],p['asset_id'],export_svg=export_svg);r,raw=self._receipt(p['receipt']);require(r['asset_sha256']==asset['sha256'] and r['rights_hash']==grant,'Stale receipt rights');g=p['geometry'];uri='data:image/png;base64,'+base64.b64encode(raw).decode()
   media.append(f'<image id="png-{p["id"]}" x="{g["x"]}" y="{g["y"]}" width="{g["width"]}" height="{g["height"]}" preserveAspectRatio="xMidYMid meet" href="{uri}"/>')
  identity=sha(canonical({'state':s,'profile':self.decoder.profile,'fonts':scene['fonts']}));svg=scene['svg'].replace('</svg>',''.join(media)+'<metadata>'+identity+'</metadata></svg>');require(len(svg.encode())<=4*1024*1024,'SVG limit')
  return {'format':'studio-png-scene@1','svg':svg,'sha256':sha(svg.encode()),'identity':identity,'head':self.token(),'draft':True,'boxes':scene['boxes'],'fonts':scene['fonts']}
 def export(self,head,png,svg_sha256,*,cancel=None,expires=None):
  with self.lock:
   require(not self.blocked and self.token()==head,'Stale export');scene=self.scene(export_svg=True);require(scene['sha256']==svg_sha256,'Scene changed');require(len(list((self.root/'exports').iterdir()))<20,'20 export sets retained; no automatic deletion')
   pixels=self.decoder.decode(png,expected_sha256=sha(png),cancel=cancel);require((pixels.width,pixels.height)==(1080,1350),'Export dimensions');require(cancel is None or not cancel.is_set(),'Cancelled export')
   # Caller supplies same-scene browser raster; comparison with browser evidence is
   # required separately. This validates transport/codec, not visual correctness.
   self.scene(export_svg=True);require(self.token()==head,'Stale publication');svg=scene['svg'].encode();self._reserve(len(svg)+len(png)+4096);destination=self.root/'exports'/uuid.uuid4().hex
   with self.library.transaction() as c:
    current=self.current();self._live_locked(c,current)
    for p in current['placements']:
     grant=self.library.eligibility(c,p['asset_id'],'redistribute','poster');require(grant['eligible'],'SVG embedding redistribution permission missing')
    require(expires is None or time.monotonic()<=expires,'Export handshake expired before publication')
    destination.mkdir(mode=0o700);exclusive(destination/'draft.svg',svg,0o444);exclusive(destination/'draft.png',png,0o444);exclusive(destination/'manifest.json',canonical({'format':'studio-png-export@1','head':head,'scene_sha256':svg_sha256,'svg_sha256':sha(svg),'png_sha256':sha(png),'rgba_sha256':sha(pixels.rgba),'draft':True}),0o444);sync_directory(destination);sync_directory(destination.parent)
   return destination.name
