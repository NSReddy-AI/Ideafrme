"""Build an edit from images/screenshots + text beats (for link / screenshot / idea reels, no speaker).
Usage: python slides.py <job>          reads build/beats.json:
  [{"img":"inputs/shot1.png", "badge":"1", "text":"NotebookLM", "sub":"Research with your own sources", "dur":3.0}, ...]
  "img" may be null (plain gradient card). Text in the brand's language/font.
With narration (project narration = ai | recorded, M4 B1) each slide's length comes from build/narration_timeline.json.
Writes build/edit.mp4 (1080x1920 for fullscreen brands, 1080x1080 for framed) and build/cues.json (sfx times)."""
import sys, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *
j, c = job(sys.argv[1]); b = os.path.join(j["_dir"], "build"); beats = load(os.path.join(b, "beats.json"))
if j.get("narration") in ("ai", "recorded"):   # M4 B1: each slide lasts as long as its narration sentence (+ its pause)
    _tp = os.path.join(b, "narration_timeline.json")
    if not os.path.exists(_tp): fail("NARRATION_MISSING", "narration is on but build/narration_timeline.json is missing - run voice.py / narrate.py first")
    _tl = load(_tp); _S = _tl["sentences"]
    if len(_S) != len(beats): fail("NARRATION_BEATS_MISMATCH", f"{len(beats)} slides but {len(_S)} narration sentences - one slide per sentence")
    if any(x.get("s") is None for x in _S): fail("NARRATION_NOT_ALIGNED", "the recording has no sentence times yet - run narration_align.py first")
    _edges = [0.0] + [x["s"] for x in _S[1:]] + [_tl["duration"]]
    beats = [dict(bt, dur=(round(_edges[i + 1] * FPS) - round(_edges[i] * FPS)) / FPS) for i, bt in enumerate(beats)]   # whole frames, no drift
framed = c["frame"]["type"] == "framed"; OW, OH = (1080, 1080) if framed else (1080, 1920)
T = c["title"]; C = c["captions"]; font = FONT_TE if c["language"] == "te" else FONT_UI
_T=['']
def F(s): return ImageFont.truetype(font_for(_T[0]), s, layout_engine=ImageFont.Layout.RAQM)
def fit(txt, maxw, s):
    _T[0] = txt
    while s > 30:
        bb = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), txt, font=F(s), anchor="mm")
        if bb[2]-bb[0] <= maxw: break
        s -= 4
    return F(s)
def bg_card():
    t = np.linspace(0, 1, OH)[:, None, None]; g = (np.array(hexrgb(T["grad_top"]))*(1-t)+np.array(hexrgb(T["grad_bottom"]))*t)*np.ones((1, OW, 1))
    yy, xx = np.mgrid[0:OH, 0:OW]; r = np.sqrt(((xx-OW/2)/(OW*0.7))**2+((yy-OH*0.45)/(OH*0.45))**2)
    gw = np.clip(1-r, 0, 1)[..., None]**1.4; g = g*(1-0.6*gw)+np.array(hexrgb(T["glow"]))*0.6*gw
    return Image.fromarray(g.clip(0, 255).astype(np.uint8))
TY = int(OH*(0.74 if not framed else 0.80))   # slide text line
PC, PH = 0.36, (0.62 if not framed else 0.75)   # photo centre / max height (share of the card) - unchanged for every reel without AI narration
if j.get("narration") == "ai":   # M4 B1: keep photos below the AI-voice disclosure band (it is drawn over the top of the edit)
    import frame as _FR
    _r = _FR.disclosure_reserve(c); _top = 0.5 + (_r - 0.5) / 1.06 + 0.005   # the slow push-in (up to 1.06x) moves things outward
    _bot = PC + PH / 2; PC, PH = (_top + _bot) / 2, _bot - _top
if j.get("narration") in ("ai", "recorded"):   # M4 B1.3: narrated reels keep the lower band free for the captions (build.py)
    TY = int(OH * (0.62 if framed else 0.56)); _top = PC - PH / 2; _bot = min(PC + PH / 2, 0.47 if framed else 0.44)
    PC, PH = (_top + _bot) / 2, _bot - _top
def card(bt):
    """Base picture (image fitted with blurred fill) at 1.1x for push-in room."""
    S = (int(OW*1.1), int(OH*1.1)); base = bg_card().resize(S)
    if bt.get("img"):
        im = Image.open(os.path.join(j["_dir"], bt["img"])).convert('RGB')
        fill = im.resize(S).filter(ImageFilter.GaussianBlur(40)); base = Image.blend(base, fill, 0.6)
        sc = min(S[0]*0.92/im.width, S[1]*PH/im.height); im = im.resize((int(im.width*sc), int(im.height*sc)), Image.LANCZOS)
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width-1, im.height-1), radius=28, fill=255)
        sh = Image.new('RGBA', S, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle(((S[0]-im.width)//2+8, int(S[1]*PC-im.height/2)+16, (S[0]+im.width)//2+8, int(S[1]*PC+im.height/2)+16), radius=28, fill=(0, 0, 0, 150))
        base = base.convert('RGBA'); base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
        base.paste(im, ((S[0]-im.width)//2, int(S[1]*PC-im.height/2)), m)
    return base.convert('RGB')
def overlay(bt):
    o = Image.new('RGBA', (OW, OH), (0, 0, 0, 0)); d = ImageDraw.Draw(o); acc = hexrgb(C["highlight"])
    ty = TY
    if bt.get("badge"):
        r = 70; cx, cy = OW//2, ty-150; d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=acc+(255,))
        d.text((cx, cy), str(bt["badge"]), font=ImageFont.truetype(FONT_UI, 80), fill=(10, 10, 10, 255), anchor="mm")
    if bt.get("text"):
        f = fit(bt["text"], OW-120, 110); sh = Image.new('RGBA', (OW, OH), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((OW//2+3, ty+5), bt["text"], font=f, fill=(0, 0, 0, 220), anchor="mm"); o.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
        ImageDraw.Draw(o).text((OW//2, ty), bt["text"], font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(10, 10, 10, 255))
    if bt.get("sub"):
        f = fit(bt["sub"], OW-140, 54); ImageDraw.Draw(o).text((OW//2, ty+110), bt["sub"], font=f, fill=acc+(255,), anchor="mm", stroke_width=2, stroke_fill=(10, 10, 10, 255))
    return o
segs = []; cues = dict(pop=[], whoosh=[], impact=[0.05]); t = 0.0
for i, bt in enumerate(beats):
    d = float(bt.get("dur", 3.0)); nf = round(d*FPS); cp = os.path.join(b, f"_beat{i}.png"); op = os.path.join(b, f"_ov{i}.png")
    card(bt).save(cp); overlay(bt).save(op); seg = os.path.join(b, f"_seg{i}.mp4")
    run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", cp, "-loop", "1", "-i", op, "-filter_complex",
         f"[0:v]zoompan=z='1+0.06*on/{nf}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={OW}x{OH}:fps=30[bg];"
         f"[1:v]format=rgba,fade=t=in:st=0:d=0.18:alpha=1[ov];[bg][ov]overlay=0:0:format=auto,format=yuv420p", "-frames:v", str(nf), "-r", "30", "-c:v", "libx264", "-crf", "14", "-preset", "fast", seg])
    progress((i+1)/len(beats)*95, f"beat {i+1}/{len(beats)}")
    segs.append(seg); (cues["whoosh"] if i else cues["pop"]).append(round(t, 2)); cues["pop"].append(round(t+0.05, 2)); t += d
open(os.path.join(b, "_segs.txt"), "w").write("".join("file '" + s.replace("'", "'\\''") + "'\n" for s in segs))
run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(b, "_segs.txt"), "-c", "copy", os.path.join(b, "edit.mp4")])
cues["riser"] = [max(0, t-2.2)]; cues["build"] = [t*0.6, t-0.5]; save(cues, os.path.join(b, "cues.json"))
print("slides ->", f"{b}/edit.mp4", round(t, 2), "s")
