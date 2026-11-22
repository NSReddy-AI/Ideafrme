"""Fixed-ID main Studio bridge. No paths or format-upgrade shortcuts from HTTP."""
import base64,copy,json,re,secrets,time,uuid
from pathlib import Path
from studio_manual_ui.service import UIError,exact,read,decode,project_id
from studio_png_sandbox.controller import Decoder,Refused,ROOT,sha,safe
from studio_png_sandbox.unified import Unified
from .brands import Store as Library,ROOT as BRAND_ROOT
from .brand_application import validate as validate_brand
BUILD=ROOT/'.runtime/png-first-001/build-08'
class Media:
 def __init__(self,server):self.server=server;self.studio=server.studio;self.opened={};self.pending=None
 def close(self):
  for s in self.opened.values():s.close()
  self.opened.clear();self.pending=None
 def library(self):return Library(getattr(self.server,'brand_root',BRAND_ROOT))
 def decoder(self):return Decoder(BUILD)
 def get(self,identity):
  require_id(identity)
  if identity not in self.opened:self.opened[identity]=Unified(self.studio.root/('png-unified-'+identity),self.library(),self.decoder())
  return self.opened[identity]
 def listing(self):
  try:self.decoder();available=True;reason='Qualified restricted PNG profile available'
  except (OSError,ValueError,KeyError) as e:available=False;reason=str(e)
  projects=[];paths=list(self.studio.root.glob('png-unified-*'))
  if len(paths)>100:raise Refused('Unified project catalogue limit')
  for p in paths:
   safe(p);identity=p.name.removeprefix('png-unified-')
   try:s=self.get(identity);v=s.view();projects.append({'id':identity,'name':v['name'],'revision':v['revision'],'eligible':v['binding']['eligible']})
   except (OSError,ValueError,KeyError):projects.append({'id':identity,'name':'Recovery required','error':True})
  return {'available':available,'reason':reason,'projects':projects,'analysis':'OFF','version':3}
 def fork(self,v):
  exact(v,{'project_id','expected_revision','acknowledge'});identity=project_id(v['project_id']);self.studio._ready(identity)
  if v['acknowledge'] is not True:raise Refused('Explicit media v3 fork acknowledgement required')
  if len(list(self.studio.root.glob('png-unified-*')))>=100:raise Refused('Unified project limit')
  with self.studio.manual.lock:
   doc=self.studio.manual._expected(identity,v['expected_revision']);binding=self.studio.pairs.bindings.get(identity)
   if binding is None or binding['brand'] is None:raise Refused('Select/save an approved brand binding in the source project before creating a media workspace')
   validate_brand(doc,binding);key=uuid.uuid4().hex;s=Unified(self.studio.root/('png-unified-'+key),self.library(),self.decoder(),base=doc,binding=binding,acknowledge=True);self.opened[key]=s
  return {'project':s.view()}
 def check(self,v,fields):
  exact(v,{'id','head'}|fields);s=self.get(v['id'])
  if s.token()!=v['head']:raise Refused('Stale unified workspace; reopen current saved state')
  return s
 def open(self,v):exact(v,{'id'});return {'project':self.get(v['id']).view()}
 def action(self,v):s=self.check(v,{'request'});result=s.edit(v['request'],v['head']);self.pending=None;return {'project':result}
 def scene(self,v):
  s=self.check(v,{'request'});r=v['request'];exact(r,{'project_id','expected_revision'});view=s.view()
  if r['project_id']!=view['project_id'] or r['expected_revision']!=view['revision']:raise Refused('Stale scene revision')
  return s.scene()
 def overlay(self,v):
  s=self.check(v,{'action','asset_id','layer_id','geometry'})
  if v['action']=='place':s.place(v['asset_id'],v['geometry'],v['head'])
  elif v['action'] in ('geometry','remove'):s.action(v['action'],v['head'],v['layer_id'],v['geometry'])
  else:raise Refused('Unsupported overlay action')
  self.pending=None;return {'project':s.view()}
 def begin(self,v):
  s=self.check(v,{'request'});now=time.monotonic();legacy=self.studio.exports.pending
  if (self.pending and now-self.pending['started']<=15) or (legacy and now-legacy['started']<=15):raise Refused('One export in flight')
  self.scene(v);scene=s.scene(export_svg=True);token=secrets.token_hex(24);self.pending={'id':v['id'],'head':v['head'],'started':now,'scene':scene,'token':token};return {'token':token,'expires_seconds':15,'scene':scene}
 def finish(self,v):
  s=self.check(v,{'request'});r=v['request'];exact(r,{'token','revision','png','qa'});p=self.pending;self.pending=None
  if not p or p['id']!=v['id'] or p['head']!=v['head'] or r['token']!=p['token'] or time.monotonic()-p['started']>15 or r['revision']!=p['scene']['revision']:raise Refused('Stale/expired export handshake')
  qa=r['qa'];exact(qa,{'fonts_loaded','overflow','parity','embedded_fonts'})
  if qa['fonts_loaded'] is not True or qa['overflow']!=[]:raise Refused('Font/overflow QA failed')
  if r['png'] is None:
   # SVG-only export still records a manifest after current rights check; no
   # native alternate rasterizer or inferred PNG is substituted.
   scene=s.scene(export_svg=True);s._reserve(len(scene['svg'].encode())+4096)
   if len(list((s.root/'exports').iterdir()))>=20:raise Refused('Export count limit')
   from visual_poster_studio.session import exclusive,sync_directory
   from creative_core.document import canonical
   name=uuid.uuid4().hex;dest=s.root/'exports'/name
   with s.library.transaction() as c:
    state=s.current();s._live_locked(c,state)
    for item in state['placements']:
     if not s.library.eligibility(c,item['asset_id'],'redistribute','poster')['eligible']:raise Refused('SVG redistribution rights missing')
    if time.monotonic()-p['started']>15:raise Refused('Handshake expired')
    dest.mkdir(mode=0o700);exclusive(dest/'draft.svg',scene['svg'].encode(),0o444);exclusive(dest/'manifest.json',canonical({'format':'studio-png-export@1','head':v['head'],'scene_sha256':scene['sha256'],'svg_sha256':scene['sha256'],'png_sha256':None,'draft':True}),0o444);sync_directory(dest);sync_directory(dest.parent)
  else:
   if qa['parity'] is not True or qa['embedded_fonts'] is not True or type(r['png'])!=str or len(r['png'])>((8*1024*1024+2)//3)*4:raise Refused('PNG qualification/limit failed')
   name=s.export(v['head'],base64.b64decode(r['png'],validate=True),p['scene']['sha256'],expires=p['started']+15)
  manifest=decode(read(s.root/'exports'/name/'manifest.json',65536));return {'directory':str(s.root/'exports'/name),'manifest':manifest}
 def navigation(self,v):
  s=self.check(v,set());result=self.studio.navigation();result['media_context']={'id':v['id'],'root':str(s.root),'version':3};entries=[]
  for p in (s.root/'exports').iterdir():
   safe(p)
   if not re.fullmatch('[0-9a-f]{32}',p.name):raise Refused('Invalid retained export entry')
   mpath=p/'manifest.json';m=decode(read(mpath,65536)) if mpath.exists() else None
   entries.append({'id':p.name,'state':'draft' if m else 'partial','revision':None,'directory':str(p),'svg_sha256':m['svg_sha256'] if m else None,'png_sha256':m['png_sha256'] if m else None})
  result['exports']=entries;return result
 def assets(self,v):
  s=self.check(v,set());state=s.current();s._brand(state['binding']);choices=[]
  with s.library.transaction() as c:
   for identity in state['binding']['brand']['record']['payload']['asset_ids']:
    asset=s.library.asset(c,identity)
    if asset['kind'] in ('image','logo'):choices.append({'id':identity,'name':asset['name'],'kind':asset['kind']})
  return {'assets':choices,'placements':state['placements'],'exports':[{'id':p.name,'complete':(p/'manifest.json').exists(),'png':(p/'draft.png').exists()} for p in (s.root/'exports').iterdir()]}
 def recovery(self,v):
  s=self.check(v,set());return {'candidates':s.candidates()}
 def recover(self,v):
  s=self.check(v,{'candidate','acknowledge'});key=uuid.uuid4().hex;destination=self.studio.root/('png-unified-'+key);s.recover_copy(v['candidate'],destination,acknowledge=v['acknowledge']);return {'project':self.get(key).view()}

def require_id(value):
 if type(value)!=str or not re.fullmatch('[0-9a-f]{32}',value):raise Refused('Fixed workspace ID required; paths refused')
