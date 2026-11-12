"""Prepare synthetic posters and approved, hash-pinned copies of TWO font files only."""
from pathlib import Path
import hashlib
import json
import sys
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from creative_core import new_document, validate

assert ROOT == Path('/Users/Nadish/projects/AI Video Editor./Codex/AI Studio')
assert ROOT.resolve() == ROOT and not any(p.is_symlink() for p in (ROOT, *ROOT.parents))
project = ROOT / 'examples/posters'
fonts = project / 'assets/fonts'
fonts.mkdir(parents=True, exist_ok=True)
source = Path('/Users/Nadish/projects/AI Video Editor./Reel Studio/engine/fonts')
font_specs = [
    ('te', 'NotoSansTelugu-Black.ttf', '42a3167fc2d8ca089b03dcbfcdfe673ecaa176545944ea9c50377144947ae383',
     'Noto Sans Telugu','Copyright 2022 The Noto Project Authors (https://github.com/notofonts/telugu)'),
    ('en', 'Inter-Bold.otf', '00fd6f4691ee8884a33b46bf45851b341927c37c30064f558e1befb242971c49',
     'Inter','Copyright 2016 The Inter Project Authors')]
doc = new_document('phase2-synthetic-posters')
doc.update(elements=[],content=[],views=[],assets=[])
policy = {'background':'#f1efe6','safe_margin':64,'required_elements':['editorial-brand'],
          'palette':['none','#f1efe6','#163d36','#c5dca3','#ed7049','#ffffff','#111b30','#91adef','#d4ddef'],
          'fonts':{}}
# OFL text is a standard license; retain the full body and each font's own copyright.
ofl_source = (source/'licences/Anton-OFL.txt').read_text()
ofl_body = ofl_source[ofl_source.index('SIL OPEN FONT LICENSE Version 1.1'):]
manifest=[]
for script,name,digest,family,copyright in font_specs:
    data=(source/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==digest
    destination=fonts/name
    if destination.exists(): assert destination.read_bytes()==data
    else: destination.write_bytes(data)
    (fonts/(name+'.LICENSE.txt')).write_text(copyright+'\n\n'+ofl_body,encoding='utf-8')
    doc['assets'].append({'id':script,'path':'assets/fonts/'+name,'kind':'font','sha256':digest})
    policy['fonts'][script]={'family':family,'script':script,'weight':900 if script=='te' else 700}
    manifest.append({'source':str(source/name),'destination':str(destination.relative_to(ROOT)),
                     'sha256':digest,'license':'OFL-1.1','family':family})

def shape(id,view,x,y,w,h,color,ellipse=False,stroke=None):
    style={'shape':'ellipse' if ellipse else 'rectangle','fill':color}
    if stroke:style.update(stroke=stroke,stroke_width=3)
    doc['elements'].append({'id':id,'type':'shape','view_id':view,'x':x,'y':y,'width':w,'height':h,'style':style})

def text(id,view,value,x,y,w,h,size,color,script='en'):
    doc['content'].append({'id':id,'text':value,'language':script,'kind':'editorial'})
    doc['elements'].append({'id':id,'type':'text','view_id':view,'content_id':id,
       'x':x,'y':y,'width':w,'height':h,'style':{'font_asset_id':script,'font_size':size,'fill':color}})

doc['views']=[{'id':'editorial','width':1080,'height':1350,'language':'en'},
              {'id':'telugu','width':1080,'height':1920,'language':'te'},
              {'id':'cinematic','width':2160,'height':3840,'language':'en'},
              {'id':'calibration','width':1080,'height':1350,'language':'te'}]
# Editorial: oversized type, structural grid, abstract rising discs.
text('editorial-brand','editorial','REEL STUDIO  /  FIELD NOTES',80,72,920,50,25,'#163d36')
shape('ed-rule','editorial',80,146,920,3,'#163d36')
text('ed-heading','editorial','Ideas deserve\na clear voice.',80,192,920,290,90,'#163d36')
text('ed-deck','editorial','A study in type, space and intention.',84,503,910,70,30,'#163d36')
shape('ed-panel','editorial',80,640,920,480,'#c5dca3')
for i,(x,y,s,c) in enumerate([(180,850,180,'#163d36'),(365,760,230,'#ed7049'),(615,680,290,'#163d36')]):
    shape(f'ed-disc-{i}','editorial',x,y,s,s,c,True)
text('ed-caption','editorial','01   /   ORIGINAL IDEAS. HUMAN DIRECTION.',80,1180,920,60,25,'#163d36')
text('ed-footer','editorial','SYNTHETIC POSTER STUDY     •     M5 / PHASE 2',80,1245,920,32,19,'#163d36')
# Telugu: intentionally short editorial text, no factual claims or borrowed brands.
text('telugu-brand','telugu','REEL STUDIO  /  CREATIVE STUDIES',80,82,920,60,26,'#f1efe6')
shape('te-rule','telugu',80,165,920,3,'#c5dca3')
text('te-kicker','telugu','తెలుగు / ENGLISH',80,230,920,110,40,'#c5dca3','te')
text('te-heading','telugu','కొత్త ఆలోచన\nకొత్త దిశ',80,375,920,420,108,'#f1efe6','te')
shape('te-disc-outer','telugu',190,925,700,700,'#c5dca3',True)
shape('te-disc-inner','telugu',300,1035,480,480,'#163d36',True)
shape('te-disc-accent','telugu',515,1080,240,240,'#ed7049',True)
text('te-caption','telugu','మన ఆలోచన. మన సృష్టి.',80,1660,920,110,45,'#f1efe6','te')
text('te-footer','telugu','02   /   LOCAL TYPE. ORIGINAL COMPOSITION.',80,1790,920,50,24,'#c5dca3')
# 4K still: geometric orbital sculpture; no 4K video claim.
text('cine-brand','cinematic','REEL STUDIO     /     MOTION IN STILLNESS',160,150,1840,100,48,'#d4ddef')
shape('cine-rule','cinematic',160,315,1840,4,'#91adef')
text('cine-heading','cinematic','MAKE\nSPACE.',160,480,1840,900,280,'#f1efe6')
text('cine-deck','cinematic','Leave room for the unexpected.',165,1420,1800,120,60,'#91adef')
for i,(x,y,w,h) in enumerate([(350,1800,1450,1350),(520,1910,1100,1130),(700,2080,730,790)]):
    shape(f'cine-orbit-{i}','cinematic',x,y,w,h,'none',True,'#91adef')
shape('cine-core','cinematic',870,2300,410,410,'#ed7049',True)
text('cine-caption','cinematic','03  /  A CINEMATIC POSTER EXPERIMENT',160,3290,1840,120,48,'#f1efe6')
text('cine-footer','cinematic','2160 × 3840 STILL IMAGE',160,3500,1840,100,40,'#91adef')
# Multiplication sign deliberately replaced with ASCII for the strict v1 glyph subset.
doc['content'][-1]['text']='2160 x 3840 STILL IMAGE'
# Synthetic test fixtures only; tiny PNG encoding here is not a product codec.
def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
pixels=b''.join(b'\0'+b''.join(bytes((237,112,73,255 if (x+y)%2 else 0)) for x in range(8)) for y in range(8))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',8,8,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')
svg=b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" fill="#163d36"/><path d="M25 65 L50 20 L75 65 Z" fill="#c5dca3"/></svg>'
for id,filename,kind,data in [('alpha','alpha.png','image',png),('symbol','symbol.svg','logo',svg)]:
    (project/'assets'/filename).write_bytes(data)
    doc['assets'].append({'id':id,'path':'assets/'+filename,'kind':kind,'sha256':hashlib.sha256(data).hexdigest()})
text('cal-brand','calibration','TYPE / ASSET CALIBRATION',80,80,920,80,36,'#163d36')
text('cal-te','calibration','అభివృద్ధి • సృష్టి • ప్రకృతి\nక్షేత్రం • విజ్ఞానం • శ్రద్ధ\nత్ర • జ్ఞ • క్ష • శ్రీ\nతెలుగు సంఖ్యలు ౦౧౨౩౪౫౬౭౮౯\nTelugu + English 0123456789\n(తెలుగు) — “ఆలోచన”',80,220,920,520,44,'#163d36','te')
text('cal-en','calibration','AV WA To fi fl\nEnglish typography: 0123456789\nQuotes: “ideas” / (space) / &',80,780,920,240,38,'#163d36')
for id,aid,kind,x in [('cal-logo','symbol','logo',80),('cal-alpha','alpha','image',350)]:
    doc['elements'].append({'id':id,'type':kind,'view_id':'calibration','asset_id':aid,
       'x':x,'y':1090,'width':140,'height':140,'style':{}})
validate(doc,project)
(project/'creative.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
policies={}
for view,bg,required in [('editorial','#f1efe6','editorial-brand'),('telugu','#163d36','telugu-brand'),('cinematic','#111b30','cine-brand'),('calibration','#f1efe6','cal-brand')]:
    p=dict(policy,background=bg,required_elements=[required])
    policies[view]=p
(project/'render-policies.json').write_text(json.dumps(policies,indent=2)+'\n')
(ROOT/'docs/FONT_SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Created synthetic editable document, policies and two verified font copies.')
