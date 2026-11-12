"""reel_002 motion graphics, rebuilt WITHOUT GSAP (Web Animations API via engine/motion.py) and with local fonts.
Same elements, timings and looks as gen_overlay_sq.py (the GSAP original). Run from this folder:
  python gen_overlay_waapi.py  -> ../build/hf_waapi/index.html (+ fonts/)"""
import json, html, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "engine"))
from plan import *
from motion import Comp, counter_steps, fit_px
words = json.load(open(os.path.join(HERE, "..", "build", "words.json")))
for w in words:
    w.setdefault("num", bool(w.get("hl")))
    if w["w"] in ("నాలుగు",): w["num"] = True
TOT = TOTAL
anchor = [(a, b) for a, b, k, p in SHOTS if k == 'A']
def in_anchor(t): return any(a <= t + 0.01 < b for a, b in anchor)
NOCAP = [(3.95, 6.03), (31.75, 33.31), (40.13, 43.77), (46.53, 47.45), (52.48, TOT)]
def nocap(t): return any(a - 0.01 <= t < b for a, b in NOCAP)
E_ = html.escape
C = Comp(1080, 1080, TOT)
# --- captions (sizes measured now with the real fonts, so no measuring inside the browser)
caps = [w for w in words if not nocap(w['s'])]
for i, w in enumerate(caps):
    s = max(w['s'] - 0.05, 0.4 if i == 0 else 0)
    nxt = caps[i + 1]['s'] - 0.05 if i + 1 < len(caps) else w['e'] + 0.3
    e = min(nxt, w['e'] + 0.35) if nxt - w['e'] > 0.5 else nxt
    for a, b in NOCAP:
        if s < a < e: e = a
    e = max(e, s + 0.2)
    y = 830 if in_anchor(w['s']) else 1010
    cid = f"c{i}"; cls = "cap num" if w['num'] else "cap"
    font = "Anton-Regular.ttf" if all(not ('\u0C00' <= ch <= '\u0C7F') for ch in w['w']) else "NotoSansTelugu-Black.ttf"
    px = fit_px(w['w'], font, 100, 940)
    C.clip(cid, s, e, cls, f'<span style="font-size:{px}px">{E_(w["w"])}</span>', f"top:{y}px")
    C.anim(f"#{cid} span", {"y": 40, "opacity": 0}, {"y": 0, "opacity": 1}, s, 0.15, "power3.out")
    if w['num']:
        C.anim(f"#{cid} span", {}, {}, s + 0.02, 0.12, keyframes=[(0, {"scale": 1}), (0.5, {"scale": 1.15}), (1, {"scale": 1.08})])
# --- hook
C.clip("hook", 0.40, 2.69, "hero", '<span>ఏం చేశాడు?</span>', "top:560px")
C.anim("#hook span", {"scale": 1.3, "filter": "blur(12px)", "opacity": 0}, {"scale": 1, "filter": "blur(0px)", "opacity": 1}, 0.40, 0.25, "expo.out")
# --- text-mask cards
MY = {'m24': 1000, 'm17': 830}
def mask(id, s, e, txt, label, fs):
    svg = (f'<svg width="1080" height="1080" viewBox="0 0 1080 1080"><defs><mask id="{id}m"><rect width="1080" height="1080" fill="#fff"/>'
           f'<text id="{id}t" x="540" y="{MY.get(id, 1000)}" text-anchor="middle" font-family="Anton" font-size="{fs}" fill="#000">{txt}</text></mask></defs>'
           f'<rect width="1080" height="1080" fill="#080B0D" mask="url(#{id}m)"/></svg>')
    C.clip(id, s, e, "full", svg + f'<div class="mlabel">{E_(label)}</div>')
    C.anim(f"#{id}t", {"scale": 1.3}, {"scale": 1}, s, 0.25, "expo.out", origin="50% 70%", box="fill-box")
    C.anim(f"#{id} .mlabel", {"y": 40, "opacity": 0}, {"y": 0, "opacity": 1}, s + 0.15, 0.2, "power3.out")
mask("m24", 3.95, 6.03, "24", "గంటలు సరిపోవు", 760)
C.clip("clock", 3.95, 6.03, "clock", '<svg width="150" height="150" viewBox="0 0 150 150"><circle cx="75" cy="75" r="64" fill="none" stroke="#F5F3EE" stroke-width="9"/><line id="hand" x1="75" y1="75" x2="75" y2="24" stroke="#D6A45B" stroke-width="9" stroke-linecap="round"/></svg>', "top:20px")
C.anim("#hand", {"rotation": 0}, {"rotation": 720}, 3.95, 2.08, "none", origin="75px 75px", box="view-box")
mask("m17", 31.75, 33.31, "17", "మెడికల్ కాలేజీలు", 800)
# --- stat cards (count-up = a few plain numbers shown one after another, no script callbacks)
for i, (s, e, num, label, kind) in enumerate(STATS):
    id = f"st{i}"
    if kind == 'count':
        pre = '₹' if num.startswith('₹') else ''
        raw = num.lstrip('₹'); dec = 1 if '.' in raw else 0; val = float(raw.replace(',', ''))
        steps = counter_steps(val, dec)
        spans = "".join(f'<span class="val" id="{id}v{k}">{t}</span>' for k, (_, t) in enumerate(steps))
        C.clip(id, s, e, "stat", f'<div class="num"><span class="pre">{pre}</span><span class="steps">{spans}</span></div><div class="lab">{E_(label)}</div>')
        for k, (dt, _) in enumerate(steps):
            C.show(f"#{id}v{k}", s + dt, (s + steps[k + 1][0]) if k + 1 < len(steps) else e)
    else:
        inner = (f'<div class="num pin"><svg width="110" height="150" viewBox="0 0 110 150"><path d="M55 145 C55 145 8 82 8 52 A47 47 0 0 1 102 52 C102 82 55 145 55 145Z" fill="#D6A45B"/><circle cx="55" cy="52" r="18" fill="#000"/></svg>'
                 f'<span class="tel">{E_(num)}</span></div><div class="lab">{E_(label)}</div>')
        C.clip(id, s, e, "stat", inner)
        C.anim(f"#{id} .pin svg", {"y": -120, "opacity": 0}, {"y": 0, "opacity": 1}, s, 0.3, "bounce.out")
    C.anim(f"#{id} .num", {"scale": 1.3, "opacity": 0}, {"scale": 1, "opacity": 1}, s, 0.25, "expo.out")
    C.anim(f"#{id} .lab", {"y": 40, "opacity": 0}, {"y": 0, "opacity": 1}, s + 0.12, 0.2, "power3.out")
# --- split 3
panels = [(40.13, '4', 'పోర్టులు', 0), (41.01, '10', 'ఫిషింగ్ హార్బర్లు', 373), (42.19, '6', 'ఫిష్ ల్యాండింగ్ సెంటర్లు', 746)]
inner = ''.join(f'<div class="cover" id="pc{j}" style="top:{y}px"></div><div class="ptxt" id="pt{j}" style="top:{y}px"><div class="pn">{n_}</div><div class="pl">{E_(lab)}</div></div>' for j, (t, n_, lab, y) in enumerate(panels))
C.clip("split", 40.13, 43.77, "full", inner)
for j, (t, n_, lab, y) in enumerate(panels):
    C.anim(f"#pc{j}", {"scaleY": 1}, {"scaleY": 0}, t, 0.2, "expo.out")
    C.anim(f"#pt{j}", {"x": -80, "opacity": 0}, {"x": 0, "opacity": 1}, t, 0.2, "expo.out")
# --- naadu / nedu
C.clip("nn", 46.53, 47.45, "full", '<div class="nn" id="nn1">నాడు</div><div class="nn yel" id="nn2">నేడు</div>')
C.anim("#nn1", {"clipPath": "inset(0 0 0 0)"}, {"clipPath": "inset(0 0 0 100%)"}, 46.97, 0.12, "power2.in")
C.anim("#nn2", {"clipPath": "inset(0 100% 0 0)"}, {"clipPath": "inset(0 0% 0 0)"}, 46.97, 0.12, "power2.out")
C.anim("#nn1", {"y": 40, "opacity": 0}, {"y": 0, "opacity": 1}, 46.53, 0.15, "power3.out")
# --- 130 / 1 lakh cr cards
C.clip("k130", 47.45, 49.15, "big", '<div class="bn">130</div><div class="bl">భారీ ప్రాజెక్టులు</div>')
C.clip("k1l", 49.15, 51.28, "big", '<div class="bn yel">₹1<span class="bs"> లక్ష</span></div><div class="bl">కోట్లకు పైగా పెట్టుబడులు</div>')
for id, s in (("k130", 47.45), ("k1l", 49.15)):
    C.anim(f"#{id} .bn", {"scale": 1.3, "filter": "blur(12px)", "opacity": 0}, {"scale": 1, "filter": "blur(0px)", "opacity": 1}, s, 0.25, "expo.out")
    C.anim(f"#{id} .bl", {"y": 40, "opacity": 0}, {"y": 0, "opacity": 1}, s + 0.15, 0.2, "power3.out")
# --- end card
letters = ''.join(f'<span class="L">{c}</span>' for c in "DEVELOPMENT")
devpx = fit_px("DEVELOPMENT", "SixCaps.ttf", 400, 880)   # 880 leaves room for the 0.02em letter spacing
C.clip("end", 52.48, 54.12, "endc", f'<div class="pre2">ఇలా చెప్పుకుంటూ పోతే చాలానే ఉంది</div><div class="dev" id="dev" style="font-size:{devpx}px">{letters}</div><div class="tel2">డెవలప్‌మెంట్</div>')
C.anim("#end .L", {"y": 80, "opacity": 0}, {"y": 0, "opacity": 1}, 52.48, 0.15, "power3.out", stagger=1 / 30)
C.anim("#end .tel2", {"scale": 1.3, "opacity": 0}, {"scale": 1, "opacity": 1}, 52.9, 0.25, "expo.out")
C.anim("#end .pre2", {"opacity": 0}, {"opacity": 1}, 52.6, 0.2, "none")
# --- flashes
for k, t in enumerate([3.95, 31.75, 47.45, 52.48]):
    C.clip(f"fl{k}", t - 0.1, t + 0.1, "flash", "")
    C.anim(f"#fl{k}", {}, {}, t - 0.1, 0.2, "none", keyframes=[(0, {"opacity": 0}), (0.5, {"opacity": 1}), (1, {"opacity": 0})])

CSS="""
.full,.flash,.endc{top:0;height:1080px;}
.flash{background:#FFFFFF;}
.cap{text-align:center;transform:translateY(-50%);z-index:20;}
.cap span{display:inline-block;font-family:'Anton','Noto Sans Telugu',sans-serif;font-weight:900;line-height:1.25;color:#F5F3EE;text-shadow:0 6px 24px rgba(0,0,0,.55);white-space:nowrap;}
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
C.css(CSS + ".steps{display:inline-grid;}.steps .val{grid-area:1/1;visibility:hidden;}")
out = os.path.join(HERE, "..", "build", "hf_waapi", "index.html")
missing = C.write(out)
print(len(C.els), "elements ->", os.path.normpath(out), "| missing fonts:", missing or "none")
