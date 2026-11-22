"""Connected product entry points. Protected documents/bindings remain authoritative."""
from studio_manual_ui.service import exact,UIError,text,project_id
from . import binding_workflow
def create(server,value):
 exact(value,{'mode','name','idea','language','brand_hash','purpose','audience','instructions','direction'})
 if value['mode'] not in ('quick','guided','professional'):raise UIError('mode','Unknown experience level')
 idea=text(value['idea'],180);name=text(value['name'] or idea.split('\n')[0][:80],128)
 purpose=text(value['purpose'] or 'Share this message',120);audience=text(value['audience'] or 'General audience',120)
 instructions=text(value['instructions'],1500) if value['instructions'] else ''
 direction=text(value['direction'],120) if value['direction'] else ''
 notes=[]
 if not value['purpose']:notes.append('Purpose is a disclosed application default: Share this message; not a factual claim.')
 if not value['audience']:notes.append('Audience is a disclosed application default: General audience; not researched demographics.')
 if direction:notes.append('User creative direction: '+direction)
 full=instructions+ ('\n\n' if instructions and notes else '')+'\n'.join(notes)
 from .brands import Store,ROOT
 server.studio.brand_library=Store(getattr(server,'brand_root',ROOT))
 doc=binding_workflow.create(server.studio,{'name':name,'text':idea,'language':value['language'],'brief':{'purpose':purpose,'topic':idea,'audience':audience,'format':'poster','instructions':full},'brand_hash':value['brand_hash'],'acknowledge':True})
 return {'project':doc,'resolutions':{'purpose':'user' if value['purpose'] else 'disclosed-default','audience':'user' if value['audience'] else 'disclosed-default','copy':'exact-user-input'},'mode':value['mode']}
def history(server,value):
 exact(value,{'project_id','media_id'});identity=project_id(value['project_id'])
 if value['media_id'] is not None:
  w=server.media.get(value['media_id']);state=w.current()
  if state['document']['id']!=identity:raise UIError('project','Foreign project identity')
  t=state['timeline'];doc=state['document'];rows=[{'index':i+1,'kind':x['kind'],'operation':x['operation'] if type(x['operation'])==str else x['operation']['op'],'active':i<t['cursor']} for i,x in enumerate(t['transactions'])]
  return {'project_id':identity,'media_version':3,'revision':state['generation'],'cursor':t['cursor'],'transactions':rows,'named_versions':[{'id':x['id'],'name':x['name'],'fingerprint':x['fingerprint']} for x in doc['versions']],'recovery':'Use the explicit PNG recovery-copy controls; original generations and exports are retained.'}
 server.studio._ready(identity);doc=server.studio.manual.document(identity);h=doc['history']
 return {'project_id':identity,'revision':doc['revision'],'cursor':h['cursor'],'transactions':[{'id':x['id'],'index':i+1,'kind':'base','operation':x['operation'],'active':i<h['cursor']} for i,x in enumerate(h['transactions'])],'named_versions':[{'id':x['id'],'name':x['name'],'fingerprint':x['fingerprint']} for x in doc['versions']],'recovery':'Home → Recovery. Bound document and brief recover together.'}
def capabilities(server):
 from .hybrid_jobs import Native
 try:png=server.media.listing()['available']
 except (OSError,ValueError):png=False
 return {'m5_status':'IN PROGRESS','ai_artifacts_present':Native().available(),'ai_identity_verified':'on each explicit execution','png_backend_present':png,'reference_analysis':'OFF',
 'features':[{'feature':f,'state':s,'reason':r} for f,s,r in [
 ('Quick / Guided / Professional','implemented','One shared editor and brief contract; mode changes only UI density.'),
 ('Hybrid AI concepts','implemented','Pinned local Qwen3-14B execution; three deterministic compositions from model editorial interpretation. Requires explicit generation and review.'),
 ('PNG drag/resize','implemented','Existing atomic geometry transaction; qualified PNG subset only.'),
 ('PNG stacking order','blocked','media-workflow@3 permits place/geometry/remove, not a reorder transaction. No remove/re-add identity workaround.'),
 ('Reference Style Studio','gated','R2–R6 separately gated; no unqualified decoding/OCR/video analysis enabled.'),
 ('AI image generation','incomplete','No qualified generator/model/weights/rights/runtime adopted. PNG decode qualification is not model-generation qualification.'),
 ('Poster/reel production and adaptation','gated','G5 needs accepted M4 baseline and separately authorized adapter; M4/M6 access prohibited in this sprint.'),
 ('Conversational edit application','blocked','Universal specification §8 requires an atomic multi-operation/provenance contract; current protected contracts do not supply it.'),
 ('Additional fonts/formats/effects','gated','Only current pinned fonts and qualified PNG capability profile enabled.'),
 ('Offline distribution','incomplete','Wrapper rebuild tested; complete runtime/model/tokenizer/build-source/licence and clean-install closure remain open.'),
 ('Native Telugu IME / full accessibility','unverified','Composition safeguards and keyboard paths exist; native-user and full accessibility acceptance still required.')]]}
