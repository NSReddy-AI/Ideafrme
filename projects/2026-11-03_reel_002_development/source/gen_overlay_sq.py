import json, html
from plan import *
words=json.load(open('words_out.json'))
for w in words:
    if w['w'] in ('నాలుగు',): w['num']=True
TOT=TOTAL
anchor=[(a,b) for a,b,k,p in SHOTS if k=='A']
def in_anchor(t): return any(a<=t+0.01<b for a,b in anchor)
NOCAP=[(3.95,6.03),(31.75,33.31),(40.13,43.77),(46.53,47.45),(52.48,TOT)]
def nocap(t): return any(a-0.01<=t<b for a,b in NOCAP)
els=[]; tl=[]
def clip(id,s,e,cls,inner,style=''):
    els.append(f'<div id="{id}" class="clip {cls}" data-start="{s:.3f}" data-duration="{e-s:.3f}" data-track-index="1" style="{style}">{inner}</div>')
    tl.append(f'tl.set("#{id}",{{autoAlpha:1}},{s:.3f}); tl.set("#{id}",{{autoAlpha:0}},{e:.3f});')
E_ = html.escape
# --- captions
caps=[w for w in words if not nocap(w['s'])]
for i,w in enumerate(caps):
    s=max(w['s']-0.05,0.4 if i==0 else 0)
    nxt=caps[i+1]['s']-0.05 if i+1<len(caps) else w['e']+0.3
    e=min(nxt, w['e']+0.35) if nxt-w['e']>0.5 else nxt
    for a,b in NOCAP:
        if s<a<e: e=a
    e=max(e,s+0.2)
    y=830 if in_anchor(w['s']) else 1010
    cid=f"c{i}"
    cls="cap num" if w['num'] else "cap"
    clip(cid,s,e,cls,f'<span>{E_(w["w"])}</span>',f"top:{y}px")
    tl.append(f'tl.fromTo("#{cid} span",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.15,ease:"power3.out"}},{s:.3f});')
    if w['num']:
        tl.append(f'tl.fromTo("#{cid} span",{{scale:1}},{{keyframes:[{{scale:1.15,duration:0.06}},{{scale:1.08,duration:0.06}}]}},{s+0.02:.3f});')
# --- hook
clip("hook",0.40,2.69,"hero",'<span>ఏం చేశాడు?</span>',"top:560px")
tl.append('tl.fromTo("#hook span",{scale:1.3,filter:"blur(12px)",opacity:0},{scale:1,filter:"blur(0px)",opacity:1,duration:0.25,ease:"expo.out"},0.40);')
# --- text-mask cards
MY={'m24':1000,'m17':830}
def mask(id,s,e,txt,label,fs):
    svg=(f'<svg width="1080" height="1080" viewBox="0 0 1080 1080"><defs><mask id="{id}m"><rect width="1080" height="1080" fill="#fff"/>'
         f'<text id="{id}t" x="540" y="{MY.get(id,1000)}" text-anchor="middle" font-family="Anton" font-size="{fs}" fill="#000">{txt}</text></mask></defs>'
         f'<rect width="1080" height="1080" fill="#080B0D" mask="url(#{id}m)"/></svg>')
    clip(id,s,e,"full",svg+f'<div class="mlabel">{E_(label)}</div>')
    tl.append(f'tl.fromTo("#{id}t",{{scale:1.3,transformOrigin:"50% 70%"}},{{scale:1,duration:0.25,ease:"expo.out"}},{s:.3f});')
    tl.append(f'tl.fromTo("#{id} .mlabel",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.2,ease:"power3.out"}},{s+0.15:.3f});')
mask("m24",3.95,6.03,"24","గంటలు సరిపోవు",760)
clip("clock",3.95,6.03,"clock",'<svg width="150" height="150" viewBox="0 0 150 150"><circle cx="75" cy="75" r="64" fill="none" stroke="#F5F3EE" stroke-width="9"/><line id="hand" x1="75" y1="75" x2="75" y2="24" stroke="#D6A45B" stroke-width="9" stroke-linecap="round"/></svg>',"top:20px")
tl.append('tl.fromTo("#hand",{rotation:0,svgOrigin:"75 75"},{rotation:720,svgOrigin:"75 75",duration:2.08,ease:"none"},3.95);')
mask("m17",31.75,33.31,"17","మెడికల్ కాలేజీలు",800)
# --- stat cards
def fmt_js(n): return n
for i,(s,e,num,label,kind) in enumerate(STATS):
    id=f"st{i}"
    if kind=='count':
        pre='₹' if num.startswith('₹') else ''
        raw=num.lstrip('₹'); dec=1 if '.' in raw else 0; val=float(raw.replace(',',''))
        inner=f'<div class="num"><span class="pre">{pre}</span><span class="val" id="{id}v">{num.lstrip("₹")}</span></div><div class="lab">{E_(label)}</div>'
        clip(id,s,e,"stat",inner)
        tl.append(f'(function(){{const o={{v:0}};const el=document.getElementById("{id}v");tl.fromTo(o,{{v:0}},{{v:{val},duration:0.6,ease:"power2.out",onUpdate:()=>{{el.textContent=fmt(o.v,{dec});}}}},{s:.3f});}})();')
    else:
        inner=(f'<div class="num pin"><svg width="110" height="150" viewBox="0 0 110 150"><path d="M55 145 C55 145 8 82 8 52 A47 47 0 0 1 102 52 C102 82 55 145 55 145Z" fill="#D6A45B"/><circle cx="55" cy="52" r="18" fill="#000"/></svg>'
               f'<span class="tel">{E_(num)}</span></div><div class="lab">{E_(label)}</div>')
        clip(id,s,e,"stat",inner)
        tl.append(f'tl.fromTo("#{id} .pin svg",{{y:-120,opacity:0}},{{y:0,opacity:1,duration:0.3,ease:"bounce.out"}},{s:.3f});')
    tl.append(f'tl.fromTo("#{id} .num",{{scale:1.3,opacity:0}},{{scale:1,opacity:1,duration:0.25,ease:"expo.out"}},{s:.3f});')
    tl.append(f'tl.fromTo("#{id} .lab",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.2,ease:"power3.out"}},{s+0.12:.3f});')
# --- split 3
panels=[(40.13,'4','పోర్టులు',0),(41.01,'10','ఫిషింగ్ హార్బర్లు',373),(42.19,'6','ఫిష్ ల్యాండింగ్ సెంటర్లు',746)]
inner=''
for j,(t,n_,lab,y) in enumerate(panels):
    inner+=f'<div class="cover" id="pc{j}" style="top:{y}px"></div><div class="ptxt" id="pt{j}" style="top:{y}px"><div class="pn">{n_}</div><div class="pl">{E_(lab)}</div></div>'
clip("split",40.13,43.77,"full",inner)
for j,(t,n_,lab,y) in enumerate(panels):
    tl.append(f'tl.fromTo("#pc{j}",{{scaleY:1}},{{scaleY:0,duration:0.2,ease:"expo.out"}},{t:.3f});')
    tl.append(f'tl.fromTo("#pt{j}",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.2,ease:"expo.out"}},{t:.3f});')
# --- naadu / nedu
clip("nn",46.53,47.45,"full",'<div class="nn" id="nn1">నాడు</div><div class="nn yel" id="nn2">నేడు</div>')
tl.append('tl.fromTo("#nn1",{clipPath:"inset(0 0 0 0)"},{clipPath:"inset(0 0 0 100%)",duration:0.12,ease:"power2.in"},46.97);')
tl.append('tl.fromTo("#nn2",{clipPath:"inset(0 100% 0 0)"},{clipPath:"inset(0 0% 0 0)",duration:0.12,ease:"power2.out"},46.97);')
tl.append('tl.fromTo("#nn1",{y:40,opacity:0},{y:0,opacity:1,duration:0.15,ease:"power3.out"},46.53);')
# --- 130 / 1 lakh cr cards
clip("k130",47.45,49.15,"big",'<div class="bn">130</div><div class="bl">భారీ ప్రాజెక్టులు</div>')
clip("k1l",49.15,51.28,"big",'<div class="bn yel">₹1<span class="bs"> లక్ష</span></div><div class="bl">కోట్లకు పైగా పెట్టుబడులు</div>')
for id,s in (("k130",47.45),("k1l",49.15)):
    tl.append(f'tl.fromTo("#{id} .bn",{{scale:1.3,filter:"blur(12px)",opacity:0}},{{scale:1,filter:"blur(0px)",opacity:1,duration:0.25,ease:"expo.out"}},{s});')
    tl.append(f'tl.fromTo("#{id} .bl",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.2,ease:"power3.out"}},{s+0.15:.3f});')
# --- end card
letters=''.join(f'<span class="L">{c}</span>' for c in "DEVELOPMENT")
clip("end",52.48,54.12,"endc",f'<div class="pre2">ఇలా చెప్పుకుంటూ పోతే చాలానే ఉంది</div><div class="dev" id="dev">{letters}</div><div class="tel2">డెవలప్‌మెంట్</div>')
tl.append('tl.fromTo("#end .L",{y:80,opacity:0},{y:0,opacity:1,duration:0.15,ease:"power3.out",stagger:1/30},52.48);')
tl.append('tl.fromTo("#end .tel2",{scale:1.3,opacity:0},{scale:1,opacity:1,duration:0.25,ease:"expo.out"},52.9);')
tl.append('tl.fromTo("#end .pre2",{opacity:0},{opacity:1,duration:0.2},52.6);')
# --- flashes
for k,t in enumerate([3.95,31.75,47.45,52.48]):
    clip(f"fl{k}",t-0.1,t+0.1,"flash","")
    tl.append(f'tl.fromTo("#fl{k}",{{opacity:0}},{{keyframes:[{{opacity:1,duration:0.1}},{{opacity:0,duration:0.1}}],ease:"none"}},{t-0.1:.3f});')

CSS="""
html,body{margin:0;padding:0;background:transparent;}
#root{position:relative;width:1080px;height:1080px;overflow:hidden;background:transparent;}
.clip{position:absolute;left:0;width:1080px;visibility:hidden;opacity:0;}
.full,.flash,.endc{top:0;height:1080px;}
.flash{background:#FFFFFF;}
.cap{text-align:center;transform:translateY(-50%);z-index:20;}
.cap span{display:inline-block;font-family:'Anton','Noto Sans Telugu',sans-serif;font-weight:900;font-size:100px;line-height:1.25;color:#F5F3EE;text-shadow:0 6px 24px rgba(0,0,0,.55);white-space:nowrap;}
.cap.num span{color:#D6A45B;}
.hero{text-align:center;}
.hero span{display:inline-block;font-family:'Noto Sans Telugu';font-weight:900;font-size:140px;color:#F5F3EE;text-shadow:0 6px 24px rgba(0,0,0,.55);}
.mlabel{position:absolute;top:170px;width:1080px;text-align:center;font-family:'Noto Sans Telugu';font-weight:900;font-size:84px;color:#F5F3EE;}
#m17 .mlabel{top:880px;color:#D6A45B;}
#m24 .mlabel{top:175px;}
.clock{text-align:center;}
.stat{top:735px;text-align:center;}
.stat .num{font-family:'Anton','Noto Sans Telugu';font-size:150px;line-height:1.05;color:#D6A45B;text-shadow:0 6px 24px rgba(0,0,0,.55);}
.stat .pre{font-size:110px;margin-right:8px;}
.stat .pin{display:flex;align-items:center;justify-content:center;gap:24px;}
.stat .tel{font-family:'Noto Sans Telugu';font-weight:900;font-size:110px;}
.stat .lab{font-family:'Noto Sans Telugu';font-weight:900;font-size:46px;color:#F5F3EE;margin:0 60px;line-height:1.3;}
.cover{position:absolute;left:0;width:1080px;height:333px;background:#101820;transform-origin:50% 0%;}
.ptxt{position:absolute;left:60px;height:333px;display:flex;align-items:center;gap:30px;}
.pn{font-family:'Anton';font-size:230px;color:#D6A45B;text-shadow:0 6px 24px rgba(0,0,0,.6);}
.pl{font-family:'Noto Sans Telugu';font-weight:900;font-size:58px;color:#F5F3EE;width:600px;line-height:1.25;text-shadow:0 6px 24px rgba(0,0,0,.8);}
.nn{position:absolute;top:760px;width:1080px;text-align:center;font-family:'Noto Sans Telugu';font-weight:900;font-size:150px;color:#F5F3EE;text-shadow:0 6px 24px rgba(0,0,0,.6);}
.yel{color:#D6A45B !important;}
.big{top:0;height:1080px;background:rgba(16,24,32,.62);}
.bn{position:absolute;top:200px;width:1080px;text-align:center;font-family:'Anton','Noto Sans Telugu';font-size:400px;line-height:1;color:#F5F3EE;}
.bs{font-family:'Noto Sans Telugu';font-weight:900;font-size:150px;}
.bl{position:absolute;top:690px;width:1080px;text-align:center;font-family:'Noto Sans Telugu';font-weight:900;font-size:76px;color:#F5F3EE;}
.endc{background:#101820;}
.pre2{position:absolute;top:170px;width:1080px;text-align:center;font-family:'Noto Sans Telugu';font-weight:900;font-size:58px;color:#F5F3EE;}
.dev{position:absolute;top:260px;width:1080px;text-align:center;font-family:'Six Caps';font-size:400px;line-height:1;color:#E8D2A6;letter-spacing:0.02em;white-space:nowrap;}
.L{display:inline-block;}
.tel2{position:absolute;top:800px;width:1080px;text-align:center;font-family:'Noto Sans Telugu';font-weight:900;font-size:120px;color:#D6A45B;}
"""
doc=f"""<!doctype html>
<html lang="te"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Six+Caps&family=Noto+Sans+Telugu:wght@900&display=block" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="reel" data-start="0" data-duration="{TOT}" data-fps="30" data-width="1080" data-height="1080">
{chr(10).join(els)}
</div>
<script>
function fmt(v,d){{ if(d) return v.toFixed(d); return Math.round(v).toLocaleString('en-US'); }}
function fit(){{
  document.querySelectorAll('.cap span').forEach(s=>{{ const w=s.getBoundingClientRect().width; if(w>940) s.style.fontSize=(130*940/w).toFixed(1)+'px'; }});
  const d=document.getElementById('dev'); const w=d.scrollWidth; if(w>960) d.style.fontSize=(400*960/w).toFixed(1)+'px';
}}
Promise.all([
  document.fonts.load('900 130px "Noto Sans Telugu"','అసలు జగన్'),
  document.fonts.load('400 130px "Anton"','0123456789'),
  document.fonts.load('400 560px "Six Caps"','DEVELOPMENT')
]).then(()=>document.fonts.ready).then(()=>{{
  document.querySelectorAll('.clip').forEach(e=>{{e.style.visibility='visible';e.style.opacity='1';}}); fit();
  document.querySelectorAll('.clip').forEach(e=>{{e.style.visibility='';e.style.opacity='';}});
  const tl=gsap.timeline({{paused:true}});
  tl.set({{}},{{}},{TOT});
  {chr(10).join(tl)}
  window.__timelines=window.__timelines||{{}};
  window.__timelines.reel=tl;
}});
</script></body></html>"""
open('hf/index_sq.html','w').write(doc)
print(len(els),"elements")
