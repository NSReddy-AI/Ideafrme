"""Application-owned binding/brief orchestration; no media, model or creative schema changes."""
import copy,html,json
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError,exact,project_id
from .brands import Store,ROOT as BRAND_ROOT
from .project_bindings import sha,brief,check

def library(studio):return getattr(studio,'brand_library',None) or Store(BRAND_ROOT)
def pin(studio,value):
 if value is None:return None
 check(type(value)==str,'Select an immutable approved brand hash.')
 store=library(studio)
 with store.transaction() as c:
  b=store.get(c,value);check(b['type']=='brand' and b['state']=='approved','Approved brand version required.');item=store.describe(c,value);check(item['approval_current'],'Pinned brand approval is stale or rights blocked.')
  for identity in b['payload']['asset_ids']:check(store.eligibility(c,identity,'commercial_design','poster')['eligible'],'Commercial poster scope is not cleared for a referenced asset.')
  for (h,) in c.execute('SELECT hash FROM records').fetchall():
   newer=store.get(c,h)
   if newer['type']=='brand' and newer['brand_id']==b['brand_id'] and newer['state']=='approved' and newer['revision']>b['revision']:
    check(newer['payload']['mandatory_rules']==b['payload']['mandatory_rules'],'A later approved brand changes mandatory rules; explicit version review required.')
  return {'brand_id':b['brand_id'],'revision':b['revision'],'hash':value,'record':b}

def eligible_versions(studio):
 store=library(studio)
 if not store.root.exists():return {'versions':[]}
 with store.transaction() as c:
  values=[(h,store.get(c,h)) for (h,) in c.execute('SELECT hash FROM records').fetchall()]
 result=[]
 for h,b in values:
  if b['type']!='brand' or b['state']!='approved':continue
  try:pin(studio,h);enabled=True;reason='Current reviewed metadata; registered assets are not applied.'
  except (OSError,ValueError) as exc:enabled=False;reason=str(exc)
  result.append({'hash':h,'brand_id':b['brand_id'],'revision':b['revision'],'name':b['payload']['name'],'eligible':enabled,'reason':reason,'mandatory_rules':b['payload']['mandatory_rules'],'preferences':b['payload']['preferences'],'inspiration':b['payload']['inspiration']})
 return {'versions':result}

def binding_state(studio,identity):
 b=studio.pairs.bindings.get(identity)
 if b is None:return None
 valid=True;reason='Draft only; hard-rule declarations require human review. No registered assets applied.'
 try:
  if b['brand'] is not None:check(pin(studio,b['brand']['hash'])==b['brand'],'Pinned brand bytes changed.')
 except (ValueError,OSError) as exc:valid=False;reason=str(exc)
 return {'hash':sha(canonical(b)),'record':copy.deepcopy(b),'published_head':studio.pairs.heads[identity],'eligible':valid,'status':reason}

def mark_saved(studio,identity,doc):studio.pairs.install(studio.manual,identity,doc)
def save(studio,request):
 identity=project_id(request['project_id']);exact(request,{'project_id','expected_revision','action'});doc=studio.manual._expected(identity,request['expected_revision'])
 studio.pairs.commit(identity,doc,studio.pairs.bindings[identity],studio.pairs.heads[identity]);mark_saved(studio,identity,doc);return studio._decorate(studio.manual.view(identity))

def create(studio,request):
 exact(request,{'name','text','language','brief','brand_hash','acknowledge'});check(request['acknowledge'] is True,'Acknowledge the bound-project compatibility boundary.');fields=brief(request['brief']);brand=pin(studio,request['brand_hash'])
 value=studio.create({k:request[k] for k in ('name','text','language')});identity=value['project_id'];doc=studio.manual.document(identity);b=studio.pairs.new(identity,brand,fields)
 try:studio.pairs.commit(identity,doc,b,None)
 except Exception:
  studio.manual._working.pop(identity,None);raise
 mark_saved(studio,identity,doc);return studio._decorate(studio.manual.view(identity))

def proposal(studio,request):
 exact(request,{'project_id','expected_revision','expected_binding','expected_head','brand_hash','brief'});identity=project_id(request['project_id']);studio._ready(identity);check(identity in studio.pairs.bindings,'Legacy project remains unbound; create a new bound project explicitly.')
 doc=studio.manual._expected(identity,request['expected_revision']);old=studio.pairs.bindings[identity]
 check(request['expected_binding']==sha(canonical(old)) and request['expected_head']==studio.pairs.heads[identity] and studio.pairs.head(identity)==request['expected_head'],'Stale binding or published head.')
 target=pin(studio,request['brand_hash']);fields=brief(request['brief']);check(target!=old['brand'] or fields!=old['brief'],'Binding change has no effect.')
 before=old['brand']['record']['payload'] if old['brand'] else {'name':'No brand','mandatory_rules':[],'preferences':[],'inspiration':[]}
 after=target['record']['payload'] if target else {'name':'No brand','mandatory_rules':[],'preferences':[],'inspiration':[]}
 impact={'project_id':identity,'document_revision':doc['revision'],'creative_fingerprint':core.fingerprint(doc),'previous_binding':request['expected_binding'],'previous_head':request['expected_head'],'brand_from':before['name'],'brand_to':after['name'],'brand_hash_to':target['hash'] if target else None,'hard_rules_before':before['mandatory_rules'],'hard_rules_after':after['mandatory_rules'],'preferences_before':before['preferences'],'preferences_after':after['preferences'],'inspiration_before':before['inspiration'],'inspiration_after':after['inspiration'],'brief_before':old['brief'],'brief_after':fields,'current_approvals_cleared':len(doc['approvals']),'assets_applied':False,'warning':'Save current document and context together. Creative Undo does not undo this binding revision. Draft-only; no automatic hard-rule compliance.'}
 return impact,sha(canonical(impact)),target,fields

def change(studio,request):
 exact(request,{'proposal','impact_hash','acknowledge'});check(request['acknowledge'] is True,'Explicit context-change confirmation required.')
 impact,h,target,fields=proposal(studio,request['proposal']);check(h==request['impact_hash'],'Impact changed; review again.')
 identity=impact['project_id'];doc=studio.manual.document(identity);doc['revision']+=1;doc['approvals']=[];old=studio.pairs.bindings[identity];b={**copy.deepcopy(old),'revision':old['revision']+1,'parent':sha(canonical(old)),'brand':target,'brief':fields}
 studio.pairs.commit(identity,doc,b,studio.pairs.heads[identity]);mark_saved(studio,identity,doc);studio.exports.cancel();return studio._decorate(studio.manual.view(identity))

def bound_scene(studio,identity,scene):
 b=studio.pairs.bindings.get(identity)
 if b is None:return scene
 if b['brand'] is not None:check(pin(studio,b['brand']['hash'])==b['brand'],'Pinned brand mismatch.')
 ident={'format':'studio-bound-render@1','binding_hash':sha(canonical(b)),'brand_hash':b['brand']['hash'] if b['brand'] else None,'brief_hash':sha(canonical(b['brief']))}
 ident['workflow_fingerprint']='sha256:'+sha(canonical({'creative_fingerprint':scene['source_fingerprint'],'context':ident,'profile':scene['profile']}))
 result=copy.deepcopy(scene);result['binding_identity']=ident;result['workflow_fingerprint']=ident['workflow_fingerprint'];result['svg']=scene['svg'].replace('</svg>','<metadata id="studio-binding-identity">'+html.escape(canonical(ident).decode())+'</metadata></svg>');check(len(result['svg'].encode())<=4*1024*1024,'Bound SVG exceeds export limit.');result['svg_sha256']=sha(result['svg'].encode());return result
