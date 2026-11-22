"""Derived Brand A policy only; existing pins/records remain authoritative. No asset I/O."""
import copy,re,uuid
import creative_core as core
from studio_manual_ui.service import UIError,manual_subset,exact

ALIASES={
 'Only approved palette and supported fonts.':'palette-fonts',
 'Only the approved palette and supported fonts.':'palette-fonts',
 'Use only approved colors.':'palette-fonts',
 'No additional display copy or invented claims.':'exact-brief-copy',
 'No external assets.':'no-assets',
 'No registered assets applied.':'no-assets',
 'Preserve logo geometry':'no-asset-mutation',
 'Preserve logo geometry.':'no-asset-mutation',
 'No text overlap.':'no-text-overlap',
 'Allow layout variation.':'layout-flexibility',
}
FONT_NAMES={'english':{'':'Inter Bold','Inter':'Inter Bold','Inter Bold':'Inter Bold'},'telugu':{'':'Noto Sans Telugu Black','Noto Sans Telugu':'Noto Sans Telugu Black','Noto Sans Telugu Black':'Noto Sans Telugu Black'}}

def policy(binding):
 if binding is None or binding['brand'] is None:return None
 pin=binding['brand'];p=pin['record']['payload'];blocked=[];fonts={}
 for script,mapping in FONT_NAMES.items():
  value=p['typography'][script]
  if value not in mapping:blocked.append('Unsupported '+script+' typography '+repr(value)+': external fonts/other weights require separate qualification. No substitution.')
  else:fonts[script]={'declared':value,'applied':mapping[value],'resolution':'fixed pinned script font; family-only preference uses its sole supported weight' if value not in ('Inter Bold','Noto Sans Telugu Black') else 'exact pinned face'}
 if not p['colors']:blocked.append('Approved brand has no usable palette. Revise/reapprove the profile explicitly.')
 out={'evaluator':'brand-application-a@1','brand_hash':pin['hash'],'colors':list(p['colors']),'typography':fonts,'minimum_margin':None,'minimum_font':1,'maximum_font':512,'minimum_contrast':None,'exact_brief_copy':False,'no_text_overlap':False,'recognized_rules':[],'blocked':blocked,'preferences':copy.deepcopy(p['preferences']),'inspiration':copy.deepcopy(p['inspiration']),'flexibility':'Layout, hierarchy, geometry, approved colors and supported sizes remain editable within hard rules. Preferences/inspiration never override hard restrictions.'}
 for rule in p['mandatory_rules']:
  if rule in ALIASES:
   effect=ALIASES[rule];out['recognized_rules'].append({'declaration':rule,'effect':effect})
   if effect=='exact-brief-copy':out['exact_brief_copy']=True
   if effect=='no-text-overlap':out['no_text_overlap']=True
   continue
  match=re.fullmatch(r'Minimum safe margin: ([0-9]{1,3}) px\.',rule)
  if match and int(match[1])<=256:
   n=int(match[1]);out['minimum_margin']=max(out['minimum_margin'] or 0,n);out['recognized_rules'].append({'declaration':rule,'effect':'minimum-margin'});continue
  match=re.fullmatch(r'(Minimum|Maximum) font size: ([0-9]{1,3}) px\.',rule)
  if match and 1<=int(match[2])<=512:
   key='minimum_font' if match[1]=='Minimum' else 'maximum_font';out[key]=(max if match[1]=='Minimum' else min)(out[key],int(match[2]));out['recognized_rules'].append({'declaration':rule,'effect':key});continue
  match=re.fullmatch(r'Minimum text contrast: ([0-9]{1,2}(?:\.[0-9])?):1\.',rule)
  if match and 1<=float(match[1])<=21:
   out['minimum_contrast']=max(out['minimum_contrast'] or 1,float(match[1]));out['recognized_rules'].append({'declaration':rule,'effect':'minimum-contrast'});continue
  out['blocked'].append('Unrecognized hard rule '+repr(rule)+'. No automatic interpretation; revise/reapprove it into a supported declaration or wait for the required capability.')
 if out['minimum_font']>out['maximum_font']:out['blocked'].append('Contradictory minimum/maximum font sizes.')
 return out

def supported(p):
 if p and p['blocked']:raise UIError('brand-requirements',' '.join(p['blocked']),409)
def overlaps(a,b):return not(a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y'])
def covers(a,b):return a['x']<=b['x'] and a['y']<=b['y'] and a['x']+a['width']>=b['x']+b['width'] and a['y']+a['height']>=b['y']+b['height']
def issues(doc,binding,p):
 if p is None:return {}
 manual_subset(doc);colors={c.lower() for c in p['colors']};result={};texts={c['id']:c['text'] for c in doc['content']};allowed={binding['brief'][k] for k in ('topic','purpose','audience')};elements=doc['elements'];text_layers=[e for e in elements if e['type']=='text']
 for i,e in enumerate(elements):
  key=e['id']
  if e['style']['fill'].lower() not in colors:result[key+':color']=1
  background=e['type']=='shape' and e['style']['shape']=='rectangle' and (e['x'],e['y'],e['width'],e['height'])==(0,0,1080,1350)
  if p['minimum_margin'] is not None and not background:
   m=p['minimum_margin'];deficit=max(0,m-e['x'],m-e['y'],e['x']+e['width']-(1080-m),e['y']+e['height']-(1350-m))
   if deficit:result[key+':safe-margin']=deficit
  if e['type']!='text':continue
  size=e['style']['font_size'];violation=max(0,p['minimum_font']-size,size-p['maximum_font'])
  if violation:result[key+':font-size']=violation
  if p['exact_brief_copy'] and texts[e['content_id']] not in allowed:result[key+':exact-brief-copy']=1
  if p['no_text_overlap']:
   for other in text_layers:
    if other['id']!=key and overlaps(e,other):result[key+':text-overlap:'+other['id']]=1
  if p['minimum_contrast'] is not None:
   from .director import luminance
   background_layer=None;uncertain=False
   for other in reversed(elements[:i]):
    if other['type']=='shape' and overlaps(e,other):
     if other['style']['shape']=='rectangle' and covers(other,e):background_layer=other
     else:uncertain=True
     break
   if any(other['type']=='shape' and overlaps(e,other) for other in elements[i+1:]):uncertain=True
   if uncertain or background_layer is None:result[key+':contrast-unverifiable']=1
   else:
    a,b=sorted([luminance(e['style']['fill']),luminance(background_layer['style']['fill'])]);ratio=(b+.05)/(a+.05)
    if ratio+1e-9<p['minimum_contrast']:result[key+':contrast']=p['minimum_contrast']-ratio
 return result

def validate(doc,binding):
 p=policy(binding);supported(p);v=issues(doc,binding,p)
 if v:raise UIError('brand-violation','Brand restrictions not satisfied: '+', '.join(sorted(v))+'. No export or automatic repair; edit within the approved profile.',409)
 return p

def live(studio,identity):
 binding=studio.pairs.bindings.get(identity)
 if binding and binding['brand']:
  from .binding_workflow import pin
  if pin(studio,binding['brand']['hash'])!=binding['brand']:raise UIError('brand-requirements','Pinned brand changed.',409)
 return binding

def status(studio,identity):
 try:
  binding=live(studio,identity);p=policy(binding)
  if p is None:return {'bound_brand':False,'supported':True,'export_eligible':True,'policy':None,'violations':{},'note':'Unbranded workflow unchanged.'}
  v=issues(studio.manual.document(identity),binding,p)
  return {'bound_brand':True,'supported':not p['blocked'],'export_eligible':not p['blocked'] and not v,'policy':p,'violations':v,'note':'No external assets loaded. Save and Undo remain available; exports require all hard restrictions.'}
 except (ValueError,OSError) as exc:return {'bound_brand':True,'supported':False,'export_eligible':False,'policy':None,'violations':{},'note':str(exc)}

def action(studio,request,perform):
 """Guard one existing user transaction; save/history travel never silently repairs records."""
 identity=request.get('project_id');kind=request.get('action')
 with studio.manual.lock:
  binding=studio.pairs.bindings.get(identity) if type(identity)==str else None
  if not binding or not binding['brand'] or kind in ('save','undo','redo'):return perform(request)
  binding=live(studio,identity);p=policy(binding);supported(p);before=studio.manual.document(identity);prior=issues(before,binding,p)
  if kind=='color' and (type(request.get('color'))!=str or request['color'].lower() not in {c.lower() for c in p['colors']}):raise UIError('brand-color','Choose a color from the pinned approved palette.',409)
  if kind=='edit_text' and p['exact_brief_copy'] and (type(request.get('text'))!=str or request['text'] not in {binding['brief'][k] for k in ('topic','purpose','audience')}):raise UIError('brand-copy','This hard rule allows exact brief text only; change the brief explicitly instead of inventing display copy.',409)
  try:
   if kind in ('add_shape','add_text'):
    extras={'shape'} if kind=='add_shape' else {'language'};exact(request,{'project_id','expected_revision','action'}|extras);studio._ready(identity);studio.manual._expected(identity,request['expected_revision'])
    if len(before['elements'])>=64:raise UIError('limit','Layer limit reached.')
    e={'id':'layer-'+str(uuid.uuid4()),'view_id':before['views'][0]['id'],'x':80,'y':100,'width':300,'height':200,'type':'shape','style':{'fill':p['colors'][0]}}
    if kind=='add_shape':
     if request['shape'] not in ('rectangle','ellipse'):raise UIError('shape','Unsupported geometry.')
     e['style']['shape']=request['shape']
    else:
     language=request['language'];used={e.get('content_id') for e in before['elements']};slot=next((c for c in before['content'] if c['language']==language and c['id'] not in used),None)
     if language not in ('en','te') or slot is None:raise UIError('language','Choose a supported unused text slot.')
     e.update(type='text',width=800,height=160,content_id=slot['id'],style={'fill':p['colors'][0],'font_size':64})
    candidate=core.apply(before,{'op':'add','element':e},studio.manual.projects/identity);manual_subset(candidate);studio.manual._working[identity]=candidate;value=studio._decorate(studio.manual.view(identity))
   else:value=perform(request)
   after=issues(studio.manual.document(identity),binding,p)
   if any(key not in prior or severity>prior[key]+1e-9 for key,severity in after.items()):raise UIError('brand-violation','Edit introduces or worsens a brand violation: '+', '.join(sorted(after))+'. Original working revision retained.',409)
   return value
  except Exception:
   studio.manual._working[identity]=before
   raise
