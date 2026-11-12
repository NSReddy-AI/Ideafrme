"""Word-by-word caption overlay (transparent .mov) from build/words.json.
words.json = [{"w":"word","s":start,"e":end,"hl":true/false}, ...]  (times on the EDIT timeline)
Usage: python captions.py <job> [words.json] [out.mov]
Style from brand.json -> captions {size, color, highlight, box_w, font: "te"|"ui"}."""
import sys, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *
j, c = job(sys.argv[1]); b = os.path.join(j["_dir"], "build"); C = c["captions"]
words = load(sys.argv[2] if len(sys.argv) > 2 else os.path.join(b, "words.json"))
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(b, "captions.mov")
BW, BH = C.get("box_w", 900), 200; font = FONT_TE if C.get("font", "te") == "te" else FONT_UI
def render(w, hl):
    size = C.get("size", 104)
    while True:
        f = ImageFont.truetype(font_for(w), size, layout_engine=ImageFont.Layout.RAQM)
        bb = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), w, font=f, anchor="mm")
        if bb[2]-bb[0] <= BW-40 or size < 40: break
        size -= 4
    t = Image.new('RGBA', (BW, BH), (0, 0, 0, 0)); sh = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((BW//2+3, BH//2+5), w, font=f, fill=(0, 0, 0, 200), anchor="mm"); t.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(t).text((BW//2, BH//2), w, font=f, fill=hexrgb(C["highlight"] if hl else C["color"])+(255,), anchor="mm", stroke_width=2, stroke_fill=(15, 15, 15, 255))
    return t
imgs = [render(x["w"], x.get("hl")) for x in words]; spans = []
for i, x in enumerate(words):
    s = max(0, x["s"]-0.05); nxt = words[i+1]["s"]-0.05 if i+1 < len(words) else x["e"]+0.3
    e = min(nxt, x["e"]+0.35) if nxt-x["e"] > 0.5 else nxt; spans.append((s, max(e, s+0.2)))
dur = float(j.get("edit_duration") or (spans[-1][1]+0.5)); N = round(dur*FPS)
p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{BW}x{BH}', '-r', '30', '-i', '-', '-c:v', 'qtrle', out], stdin=subprocess.PIPE)
blank = bytes(BW*BH*4); cache = {}
for n in range(N):
    t = n/FPS; fr = blank
    for i, (s, e) in enumerate(spans):
        if s <= t < e:
            k = round(1-(1-min(1, (t-s)/0.15))**3, 2)
            if (i, k) not in cache:
                im = imgs[i].copy(); im.putalpha(im.split()[3].point(lambda v: int(v*k)))
                cv = Image.new('RGBA', (BW, BH), (0, 0, 0, 0)); cv.alpha_composite(im, (0, int(30*(1-k)))); cache[(i, k)] = cv.tobytes()
            fr = cache[(i, k)]; break
    p.stdin.write(fr)
    if n % 30 == 0: progress(n/N*99)
p.stdin.close(); p.wait()
if p.returncode: fail("ENCODE_FAILED", "captions: ffmpeg could not write the overlay")
progress(100); print("captions ->", out, N, "frames")
