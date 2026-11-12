"""Versioned semantic directions and general measured-box packing. No model/UI/project writes."""
import copy,math,uuid
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import exact,decode
from . import ai_constrained as boundary,director
from .ai_adapter import require,text,completion_json,outcome
from .fonts import SPECS
from .scene import build_scene,PROFILE
from .project_bindings import sha

CHOICES={'axis':['vertical','horizontal'],'order':['headline-first','support-first'],'focal':['top','middle','bottom'],'hierarchy':['headline','balanced','support'],'alignment':['start','middle','end'],'density':['airy','moderate','compact'],'color':['light','dark']}
SCHEMA={'type':'object','properties':{'concepts':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'object','properties':{'direction':{'type':'string','minLength':1,'maxLength':40},'rationale':{'type':'string','minLength':1,'maxLength':80},**{k:{'type':'string','enum':v} for k,v in CHOICES.items()}},'required':['direction','rationale',*CHOICES],'additionalProperties':False}}},'required':['concepts'],'additionalProperties':False}

def prepare(studio,source,identity,settings):
 base=boundary.prepare(studio,source,identity,settings)
 data={k:copy.deepcopy(base['data'][k]) for k in ('brief','mandatory_rules','preferences')}
 system='Create three original poster directions from this brief. Interpret its language and audience. Do not generate geometry, copy, fonts or claims. Use each focal area and each hierarchy once across the three, and different editorial directions. No tools. English direction/rationale, short. /no_think'
 contract='Fields: direction,rationale,axis(vertical/horizontal),order(headline-first/support-first),focal(top/middle/bottom),hierarchy(headline/balanced/support),alignment(start/middle/end),density(airy/moderate/compact),color(light/dark). Alignment positions boxes; text stays left-aligned. Compiler handles measured fit, margins, contrast and shape/text paint order. Exact topic=required headline; exact purpose=support; CTA absent(no approved CTA copy). Fonts are pinned Inter Bold/Noto Sans Telugu Black; colors chosen only from approved palette. Respect brand rules; suggestions stay unapproved.'
 req={k:copy.deepcopy(base[k]) for k in ('model_identity','settings','source','source_document_hash','binding_hash','capability_digest','data')};req.update(format='studio-ai-semantic-request@1',schema=copy.deepcopy(SCHEMA),messages=[{'role':'system','content':system},{'role':'user','content':canonical(data).decode()+'\n'+contract}]);req['request_hash']=sha(canonical(req));return req

class Measurements:
 """Exact text/size results from existing browser fontRuns/fitTextBox/SVG getBBox."""
 def __init__(self,record):
  exact(record,{'kind','fonts','table'});require(record['kind']=='semantic-font-measurements@1','Unknown measurement format.');require(record['fonts']=={k:v[1] for k,v in SPECS.items()},'Measurement font identity changed.');require(type(record['table']) is list and len(record['table'])<=32,'Bounded measurement table required.');self.record=copy.deepcopy(record);self.hash=sha(canonical(record));self.table={}
  for row in record['table']:
   exact(row,{'text','sizes'});text(row['text'],2000);require(row['text'] not in self.table and type(row['sizes']) is dict and len(row['sizes'])<=65,'Invalid measurement rows.');self.table[row['text']]=row['sizes']
 def get(self,copytext,size):
  require(copytext in self.table and str(size) in self.table[copytext],'Exact browser measurement unavailable; no approximate fallback.');value=self.table[copytext][str(size)];exact(value,{'width','height','left','top'})
  require(all(type(v) in (int,float) and math.isfinite(v) for v in value.values()),'Invalid font metrics.');require(0<value['width']<=4096 and 0<value['height']<=4096 and value['left']>=-1 and value['top']>=-1,'Measured glyph overflow/size unsupported.');return math.ceil(value['width']),math.ceil(value['height'])

def palette(binding,mode):
 colors=binding['brand']['record']['payload']['colors'] if binding['brand'] else ['#14213D','#F6F4EF','#D7A441'];ordered=sorted(set(colors),key=lambda c:(director.luminance(c),c));require(len(ordered)>=2,'At least two authorized contrasting palette colors required.');dark,light=ordered[0],ordered[-1];require((director.luminance(light)+.05)/(director.luminance(dark)+.05)>=4.5,'No authorized contrasting palette pair.');return (light,dark) if mode=='light' else (dark,light)

def pack(concept,fields,binding,measure):
 """Generic two-role packer; content-dependent metrics, no catalog or preassigned directions."""
 margin,gap={'airy':(104,80),'moderate':(80,56),'compact':(56,32)}[concept['density']];inner_w,inner_h=1080-2*margin,1350-2*margin
 sizes=None
 for base in range(40,15,-1):
  hs,ss={'headline':(2*base,base),'balanced':(base,base),'support':(base,2*base)}[concept['hierarchy']];hw,hh=measure.get(fields['topic'],hs);sw,sh=measure.get(fields['purpose'],ss)
  gw,gh=(max(hw,sw),hh+gap+sh) if concept['axis']=='vertical' else (hw+gap+sw,max(hh,sh))
  if gw<=inner_w and gh<=inner_h:sizes=(hs,ss,hw,hh,sw,sh,gw,gh);break
 require(sizes is not None,'Measured text cannot fit requested semantic hierarchy; no intent downgrade.')
 hs,ss,hw,hh,sw,sh,gw,gh=sizes;fraction={'start':0,'middle':.5,'end':1}[concept['alignment']];focus={'top':0,'middle':.5,'bottom':1}[concept['focal']]
 x=margin+round((inner_w-gw)*(fraction if concept['axis']=='vertical' else .5));y=margin+round((inner_h-gh)*focus);ordered=['headline','support'] if concept['order']=='headline-first' else ['support','headline'];dims={'headline':(hw,hh,hs,fields['topic']),'support':(sw,sh,ss,fields['purpose'])};boxes={};offset=0
 for role in ordered:
  w,h,size,copytext=dims[role]
  xx=x+round((gw-w)*fraction) if concept['axis']=='vertical' else x+offset;yy=y+offset if concept['axis']=='vertical' else y+round((gh-h)*fraction)
  boxes[role]={'id':role,'type':'text','x':xx,'y':yy,'width':w,'height':h,'style':{'font_size':size},'text':copytext};offset+=(h if concept['axis']=='vertical' else w)+gap
 bg,fg=palette(binding,concept['color']);background={'id':'background','type':'shape','x':0,'y':0,'width':1080,'height':1350,'style':{'shape':'rectangle','fill':bg}}
 first=boxes[ordered[0]]
 if concept['axis']=='vertical':rule={'x':x,'y':first['y']+first['height']+gap//2-4,'width':gw,'height':8}
 else:rule={'x':first['x']+first['width']+gap//2-4,'y':y,'width':8,'height':gh}
 focal={'id':'focal','type':'shape',**rule,'style':{'shape':'rectangle','fill':fg}}
 for e in boxes.values():e['style']['fill']=fg;require(e['x']>=margin and e['y']>=margin and e['x']+e['width']<=1080-margin and e['y']+e['height']<=1350-margin,'Packing exceeded safe margins.')
 # All shapes precede exact user-copy text. Geometry follows requested roles; never repaired afterward.
 return {'id':'','name':concept['direction'],'angle':concept['direction'],'rationale':concept['rationale'],'layers':[background,focal,*[boxes[r] for r in ordered]],'semantic':copy.deepcopy(concept),'measurement_sha256':measure.hash}

def compile(studio,raw,request,measurements):
 exact(request,{'format','model_identity','settings','source','source_document_hash','binding_hash','capability_digest','data','schema','messages','request_hash'});require(request['format']=='studio-ai-semantic-request@1','Unknown semantic request version.')
 with studio.manual.lock:
  require(canonical(prepare(studio,request['source'],request['model_identity'],request['settings']))==canonical(request),'Source, rights, request or capabilities changed.')
  doc,binding=director.source(studio,request['source']);value=decode(completion_json(raw));exact(value,{'concepts'});require(type(value['concepts']) is list and len(value['concepts'])==3,'Exactly three semantic proposals required.');measure=Measurements(measurements);plans=[];documents=[];scenes=[]
  for i,c in enumerate(value['concepts']):
   exact(c,{'direction','rationale',*CHOICES});text(c['direction'],40);text(c['rationale'],80)
   for key,choices in CHOICES.items():require(type(c[key]) is str and c[key] in choices,'Unsupported semantic intent: '+key)
   p=pack(c,binding['brief'],binding,measure);p['id']=str(i);identity=str(uuid.uuid5(uuid.UUID(doc['id']),request['request_hash']+measure.hash+str(i)));candidate=director.document(identity,p,binding);candidate['views'][0]['language']=doc['views'][0]['language'];core.validate(candidate,studio.manual.projects/doc['id']);scene=build_scene(candidate,studio.fonts);plans.append(p);documents.append(candidate);scenes.append(scene)
  require({p['semantic']['focal'] for p in plans}==set(CHOICES['focal']) and {p['semantic']['hierarchy'] for p in plans}==set(CHOICES['hierarchy']),'Model repeated required focal/hierarchy intents; no compiler reassignment.')
  metrics=boundary.differentiation(plans);require(all(m['structural_dimensions']>=2 and m['editorial_similarity']<.75 and m['rationale_similarity']<.75 for m in metrics),'Semantic proposals compile to duplicates or insufficient structural/editorial differences.')
  return {'format':'studio-ai-semantic-compilation@1','request_hash':request['request_hash'],'response_sha256':sha(completion_json(raw)),'measurement_sha256':measure.hash,'pinned_brand':copy.deepcopy(binding['brand']),'brief':copy.deepcopy(binding['brief']),'plans':plans,'documents':documents,'scenes':scenes,'differentiation':metrics,'approval':'unapproved','publication':False,'browser_bounds_required':True,'review':['semantic brand rules','English/Telugu intent','originality and claims','visual quality']}

def reject_or_compile(studio,raw,request,measurements,*,failure=None):
 if failure:return outcome(None,None,failure=failure)
 try:return {'status':'compiled','result':compile(studio,raw,request,measurements)}
 except (ValueError,KeyError,TypeError,RecursionError) as e:return {'status':'rejected','reason':str(e),'retry':'none automatic','fallback':'existing deterministic workflow, explicit separate action only'}
