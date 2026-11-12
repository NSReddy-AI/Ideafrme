"""Reproducible text/vector proposals. No model execution, media or protected formats."""
import copy,re,uuid
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError,exact,project_id,manual_subset,safe,read,decode
from . import binding_workflow as workflow
from .project_bindings import sha
from .scene import build_scene,PROFILE
from .session import exclusive,sync_directory

VERSION='local-composition@1'
LIMIT=128*1024

def require(value,message):
 if not value:raise UIError('director',message,409)

def source(studio,request):
 exact(request,{'project_id','expected_revision','expected_binding','expected_head','seed','acknowledge_brief'})
 identity=project_id(request['project_id']);studio._ready(identity)
 require(type(request['seed']) is int and 0<=request['seed']<=2147483647,'Seed must be an integer from 0 to 2147483647.')
 require(request['acknowledge_brief'] is True,'Review and acknowledge the saved brief first.')
 doc=studio.manual._expected(identity,request['expected_revision']);state=workflow.binding_state(studio,identity)
 require(state is not None,'Create an explicitly bound brief project first; legacy projects remain unchanged.')
 require(state['eligible'],'Pinned brand eligibility is blocked: '+state['status'])
 require(state['hash']==request['expected_binding'] and state['published_head']==request['expected_head'] and studio.pairs.head(identity)==request['expected_head'],'Stale project binding; reload and review.')
 stored=studio.pairs.chain(identity,request['expected_head']['commit'])
 require(stored['manifest_sha256']==request['expected_head']['manifest_sha256'],'Published manifest identity mismatch.')
 require(canonical(stored['document'])==canonical(doc),'Save document changes before creating concepts.')
 require(studio.fonts is not None,'Pinned rendering fonts unavailable.')
 fields=state['record']['brief']
 require(fields['topic'].strip() and fields['purpose'].strip() and fields['audience'].strip(),'Enter purpose, topic and audience in the saved brief.')
 for k,n in [('topic',180),('purpose',120),('audience',120)]:
  require(len(fields[k])<=n,'Shorten '+k+' explicitly for this bounded concept planner; text is never truncated.')
  require(len(fields[k].split('\n'))<=8,'At most eight explicit lines per displayed brief field.')
  for line in fields[k].split("\n"):list(studio.fonts.runs(line)) # pinned coverage, no normalization
 return copy.deepcopy(doc),copy.deepcopy(state['record'])

def wrap(text,columns):
 # Insert breaks only before complete space-delimited runs. Never split combining/ZWJ words.
 result=[];width=0
 for token in re.findall(r'\n|[^ \n]+| +',text):
  if token=='\n':result.append(token);width=0;continue
  if width and width+len(token)>columns and not token.isspace():result.append('\n');width=0
  result.append(token);width+=len(token)
 return ''.join(result)

def fitted(text,width,height,preferred):
 longest=max((len(w) for w in re.split(r'[ \n]+',text)),default=1)
 for size in range(preferred,15,-1):
  columns=max(1,int(width/(size*1.2)))
  if longest>columns:continue
  value=wrap(text,columns);lines=value.split('\n')
  if max(map(len,lines))*size*1.2<=width and len(lines)*size*1.65<=height:
   return value,size
 raise UIError('director-copy','Copy cannot safely fit this composition. Edit the saved brief explicitly; no truncation or font substitution.')

def luminance(value):
 rgb=[int(value[i:i+2],16)/255 for i in (1,3,5)];rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb];return sum(a*b for a,b in zip(rgb,[.2126,.7152,.0722]))

def palette(binding):
 colors=binding['brand']['record']['payload']['colors'] if binding['brand'] else []
 # Brand palette only when supplied. One approved color uses transparent negative space.
 if colors:
  ordered=sorted(set(colors),key=lambda c:(luminance(c),c));return ordered[0],ordered[-1],len(ordered)>1
 return '#14213D','#F4B942',True

def document(identity,plan,binding):
 doc=core.new_document(identity);doc['project']['name']=plan['name'];doc['elements']=[];doc['content']=[]
 for lang in ('en','te'):
  for i in range(16):doc['content'].append({'id':f'text-{lang}-{i}','text':'New text' if lang=='en' else 'కొత్త పాఠ్యం','language':lang,'kind':'editorial'})
 used={'en':0,'te':0}
 for item in plan['layers']:
  e={k:copy.deepcopy(item[k]) for k in ('id','type','x','y','width','height','style')};e['view_id']='portrait'
  if e['type']=='text':
   lang='te' if any('\u0c00'<=c<='\u0c7f' for c in item['text']) else 'en';slot=next(c for c in doc['content'] if c['id']==f'text-{lang}-{used[lang]}');used[lang]+=1;slot['text']=item['text'];e['content_id']=slot['id']
  doc['elements'].append(e)
 doc['approvals']=[];doc['versions']=[];manual_subset(doc);return doc

def directions(binding,seed):
 fields=binding['brief'];dark,accent,two=palette(binding);margin=64+(seed%5)*8;plans=[]
 # These are composition algorithms; sizes adapt to exact copy, not industry-specific templates.
 specs=[('editorial','Editorial hierarchy','An asymmetric reading path: topic leads, purpose supports, audience closes.',[(margin,150,1080-2*margin,510,92),(margin,760,720,240,40),(margin,1130,920- margin,120,24)]),
 ('split','Split-field dialogue','Two fields balance the headline against a separate purpose panel; unequal hierarchy creates tension.',[(margin,160,440,780,66),(590,270,400,530,40),(590,1080,400,160,24)]),
 ('orbit','Geometric focus','A geometric focal point anchors a compact headline; a broad lower information band changes the reading rhythm.',[(margin,610,1080-2*margin,340,72),(margin,1020,620,220,32),(720,1050,280,180,22)])]
 for index,(key,name,reason,boxes) in enumerate(specs):
  layers=[]
  def shape(name,x,y,w,h,fill,kind='rectangle'):layers.append({'id':name,'type':'shape','x':x,'y':y,'width':w,'height':h,'style':{'fill':fill,'shape':kind}})
  colors=binding['brand']['record']['payload']['colors'] if binding['brand'] else []
  if not colors:shape('background',0,0,1080,1350,'#F6F4EF')
  elif two:shape('background',0,0,1080,1350,accent)
  if key=='editorial':shape('accent-rule',margin,margin,240+seed%4*32,12,accent)
  elif key=='split':shape('panel',552,100,480,930,accent);shape('spine',margin,80,10,1160,dark)
  else:shape('focal-orbit',400+(seed%4)*24,90,450,450,dark if binding['brand'] else accent,'ellipse');shape('lower-rule',margin,970,1080-2*margin,8,dark)
  for role,box in zip(('topic','purpose','audience'),boxes):
   x,y,w,h,size=box;text,size=fitted(fields[role],w,h,size);fill=dark
   if key=='split' and role=='purpose' and two:
    # Pick the palette color with the strongest available contrast against panel, no new color.
    fill=dark
   if key=='split' and role=='purpose' and not two:
    # Single-color brand: omit filled panel, never invent a prohibited contrast color.
    layers=[e for e in layers if e['id']!='panel']
   layers.append({'id':role,'type':'text','x':x,'y':y,'width':w,'height':h,'style':{'fill':fill,'font_size':size},'text':text})
  plans.append({'id':key,'name':name,'rationale':reason,'composition':key,'typography_hierarchy':{e['id']:e['style']['font_size'] for e in layers if e['type']=='text'},'emphasis':['topic','purpose panel','geometric anchor'][index],'layers':layers})
 return plans

def generate(studio,request):
 with studio.manual.lock:
  doc,binding=source(studio,request);brand=binding['brand'];payload=brand['record']['payload'] if brand else {}
  inputs={'planner':VERSION,'source_project':doc['id'],'source_document_sha256':sha(canonical(doc)),'binding_hash':sha(canonical(binding)),'source_head':request['expected_head'],'seed':request['seed'],'brief':binding['brief'],'brand_hash':brand['hash'] if brand else None,'profile':PROFILE,'fonts':{k:f['hash'] for k,f in studio.fonts.faces.items()}}
  bundle={'format':'studio-concept-proposals@1','inputs':inputs,'mode':'deterministic; local model unavailable','rules':payload.get('mandatory_rules',[]),'preferences':payload.get('preferences',[]),'inspiration':payload.get('inspiration',[]),'typography_preferences':payload.get('typography',{}),'instructions':binding['brief']['instructions'],'warnings':['Proposals only: review every rule and instruction; no automatic compliance or originality certification.','Only pinned Inter Bold and Noto Sans Telugu Black are used; typography preferences are advisory.','No registered assets applied. No invented claims, translation or model inference.'],'concepts':directions(binding,request['seed'])}
  
  if brand and len(set(payload['colors']))<2:bundle['warnings'].append('Limited brand palette: transparent negative space; inspect legibility on the intended background.')
  if brand and len(set(payload['colors']))>1:
   low,high,_=palette(binding)
   if (luminance(high)+.05)/(luminance(low)+.05)<4.5:bundle['warnings'].append('Approved palette has low text contrast; manual palette/brand review needed before use.')
  bundle['digest']=sha(canonical(bundle));require(len(canonical(bundle))<=LIMIT,'Concept bundle exceeds 128 KiB.')
  for plan in bundle['concepts']:
   identity=str(uuid.uuid5(uuid.UUID(studio.pairs.session_id),bundle['digest']+':'+plan['id']));candidate=document(identity,plan,binding);core.validate(candidate,studio.manual.projects/doc["id"]);build_scene(candidate,studio.fonts)
  return bundle

def retain(studio,bundle):
 """Immutable provenance only, never project truth. Orphans remain evidence after failure."""
 root=safe(studio.root/'concept-proposals');raw=canonical(bundle)+b'\n';require(len(raw)<=LIMIT,'Proposal receipt exceeds limit.')
 if not root.exists():root.mkdir();sync_directory(studio.root)
 target=safe(root/(bundle['digest']+'.json'));files=list(root.iterdir());require(len(files)<=20,'Proposal receipt count exhausted.')
 total=0
 for p in files:
  safe(p);require(p.is_file() and p.suffix=='.json' and p.stat().st_size<=LIMIT,'Invalid proposal receipt directory.');total+=p.stat().st_size
 if target.exists():require(read(target,LIMIT)==raw and target.stat().st_mode&0o222==0,'Proposal receipt mismatch.');return
 require(len(files)<20 and total+len(raw)<=4*1024*1024,'Proposal receipt storage exhausted; existing evidence retained.')
 exclusive(target,raw,0o444);require(read(target,LIMIT)==raw,'Proposal receipt readback failed.')

def select(studio,request):
 exact(request,{'source','bundle_digest','concept_id','acknowledge_rules'})
 with studio.manual.lock:
  require(request['acknowledge_rules'] is True,'Review the plan, all mandatory rules and instructions before opening an unapproved draft.')
  bundle=generate(studio,request['source']);require(request['bundle_digest']==bundle['digest'],'Stale or altered concept bundle; regenerate and review.')
  plans=[p for p in bundle['concepts'] if p['id']==request['concept_id']];require(len(plans)==1,'Unknown concept.')
  identity=str(uuid.uuid5(uuid.UUID(studio.pairs.session_id),bundle['digest']+':'+plans[0]['id']));directory=safe(studio.manual.projects/identity)
  require(not directory.exists() and not studio.pairs.owns(identity),'This concept already exists. Open it from Projects, or choose a new seed; no project overwritten.')
  require(len(list(studio.manual.projects.iterdir()))<100,'Session project limit reached.')
  binding=copy.deepcopy(studio.pairs.bindings[request['source']['project_id']]);doc=document(identity,plans[0],binding);core.validate(doc,studio.manual.projects/request["source"]["project_id"]);build_scene(doc,studio.fonts)
  b=studio.pairs.new(identity,binding['brand'],binding['brief'])
  retain(studio,bundle)
  directory.mkdir();studio.pairs.commit(identity,doc,b,None);workflow.mark_saved(studio,identity,doc)
  return {'project':studio.view(identity),'bundle_digest':bundle['digest'],'concept_id':plans[0]['id'],'approved':False}
