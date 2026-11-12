"""Gate B1.1 - still-image previews of the AI-narration disclosure position (for the user's choice). NOT a reel render.
Run from the dev folder:  ~/.venvs/reelstudio/bin/python tools/gate_b1_disclosure_stills.py
For every brand x platform x candidate position, frame.py draws the real frame layer in a temporary project; the still is then
composited the way assemble.py combines the frame and the video (framed: video inside the window mask; fullscreen: frame on top),
with a neutral sample slide and a sample caption where captions sit. Each still is shown clean and with the platform's unsafe zones
shaded red. Writes tests/acceptance/M4_gateB/B1/disclosure/ (<brand>_<platform>_<position>.png, sheet_<brand>.png, positions.json).
Nothing in projects/ or brands/ is changed."""
import os, sys, json, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "engine"))
from common import FONT_TE, FONT_UI, load, save
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1", "disclosure_A_2lines"); os.makedirs(OUT, exist_ok=True)   # B1.1 previews stay in disclosure/
TMP = tempfile.mkdtemp(prefix="rs_b1stills_")
BRANDS = {"jagan_for_andhra": ("window_top",), "tech_ai_tools": ("top",), "editing_freelance": ("top",)}   # option A approved 10 Nov
PLATFORMS = ("instagram", "youtube", "facebook")
LABEL = {"window_top": "A - top of the video window", "top": "A - top of the screen"}
PHOTO = (214, 120, 40)   # sample photo colour, used to prove the disclosure never covers a photo

def sample_video(c, d, brand):
    """The REAL edit frame: slides.py builds a 1.6 s slide (sample photo + slide text) with narration = ai, exactly as a narrated reel
    would; the frame is taken near the end of the push-in (largest zoom)."""
    b = os.path.join(d, "build"); ph = Image.new("RGB", (1200, 900), PHOTO); g = ImageDraw.Draw(ph)
    g.rectangle((20, 20, 1179, 879), outline=(250, 235, 210), width=10); g.text((600, 450), "sample photo", font=ImageFont.truetype(FONT_UI, 70), fill=(255, 245, 230), anchor="mm")
    ph.save(os.path.join(d, "inputs", "sample_photo.png"))
    save([dict(img="inputs/sample_photo.png", text="నమూనా స్లయిడ్", dur=1.6)], os.path.join(b, "beats.json"))
    save(dict(sentences=[dict(i=0, s=0.25, e=1.2)], duration=1.6, note="preview only - not a narration"), os.path.join(b, "narration_timeline.json"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "engine", "slides.py"), d], capture_output=True, text=True)
    if r.returncode: sys.exit(f"slides.py failed for {brand}: {r.stderr[-600:]}")
    fp = os.path.join(b, "preview_frame.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.5", "-i", os.path.join(b, "edit.mp4"), "-frames:v", "1", fp], check=True)
    return Image.open(fp).convert("RGB")   # slide text sits in the lower part of the slide, where captions also go

def photo_under(im, box_edit):
    """Sample-photo pixels inside the disclosure area (edit coordinates) - must be 0."""
    import numpy as np
    a = np.array(im).astype(int); l, t, r, b = [max(0, v) for v in box_edit]; z = a[t:b, l:r]
    return int(((abs(z[..., 0] - PHOTO[0]) < 25) & (abs(z[..., 1] - PHOTO[1]) < 25) & (abs(z[..., 2] - PHOTO[2]) < 25)).sum())

def shade(im, sa):
    o = im.convert("RGBA"); m = Image.new("RGBA", o.size, (0, 0, 0, 0)); d = ImageDraw.Draw(m); W, H = o.size; red = (230, 30, 30, 90)
    for box in ((0, 0, W, sa["top"]), (0, sa["bottom"], W, H), (0, sa["top"], sa["left"], sa["bottom"]), (sa["right"], sa["top"], W, sa["bottom"])): d.rectangle(box, fill=red)
    d.rectangle((sa["left"], sa["top"], sa["right"], sa["bottom"]), outline=(255, 60, 60, 255), width=3); o.alpha_composite(m); return o.convert("RGB")

res = {}
for brand, positions in BRANDS.items():
    c = load(os.path.join(ROOT, "brands", brand, "brand.json")); c["_dir"] = os.path.join(ROOT, "brands", brand); tiles = []
    for pos in positions:
        for pf in PLATFORMS:
            d = os.path.join(TMP, f"{brand}_{pf}_{pos}"); os.makedirs(os.path.join(d, "build")); os.makedirs(os.path.join(d, "inputs"))
            save(dict(brand=brand, platform=pf, style=c["default_style"], title_seconds=2.0, title=["నమూనా శీర్షిక", "రెండో లైన్"],
                      hook=dict(line1="", line2="", line3="", tag_top="", tag_bottom=""), narration="ai", narrator="prakash", narrator_style="news", history=[]),
                 os.path.join(d, "project.json"))
            r = subprocess.run([sys.executable, os.path.join(ROOT, "engine", "frame.py"), d], capture_output=True, text=True, env=dict(os.environ, RS_DISCLOSURE_POSITION=pos))
            if r.returncode: sys.exit(f"frame.py failed for {brand} {pf} {pos}: {r.stderr[-600:]}")
            b = os.path.join(d, "build"); LY = load(os.path.join(b, "layout.json")); fr = Image.open(os.path.join(b, "frame.png")).convert("RGBA")
            vid = sample_video(c, d, brand); dz = LY["ai_disclosure"]; l, t, rr, bb = dz["box"]
            if LY["type"] == "framed":
                w = LY["window"]; k = vid.size[0] / w["size"]; under = photo_under(vid, [int((l - w["x"]) * k), int((t - w["y"]) * k), int((rr - w["x"]) * k), int((bb - w["y"]) * k)])
                comp = fr.copy(); comp.paste(vid.resize((w["size"], w["size"])), (w["x"], w["y"]), Image.open(os.path.join(b, "window_mask.png")).convert("L"))
            else:
                under = photo_under(vid, [l, t, rr, bb]); comp = vid.convert("RGBA"); comp.alpha_composite(fr)
            comp = comp.convert("RGB"); sa = LY["safe_area"]["area"]
            issues = [i for i in LY["safe_area"]["issues"] if i["element"] == "ai_disclosure"]
            clean = os.path.join(OUT, f"{brand}_{pf}_{pos}.png"); comp.save(clean); shade(comp, sa).save(clean.replace(".png", "_safe_zones.png"))
            res[f"{brand}|{pf}|{pos}"] = dict(box=dz["box"], font_px=dz["font_px"], lines=dz["lines"], inside_safe_area=not issues, issues=issues,
                                              covers_none_of=dz["covers_none_of"], photo_pixels_under_disclosure=under, still=os.path.relpath(clean, ROOT))
            tiles.append((pos, pf, comp, shade(comp, sa), not issues and under == 0))
    # contact sheet: one row per position; each platform clean + shaded
    tw, th, pad, head = 300, 533, 16, 70; cols = len(PLATFORMS) * 2
    S = Image.new("RGB", (pad + cols * (tw + pad), head + len(positions) * (th + 60 + pad)), (245, 245, 245)); d = ImageDraw.Draw(S)
    d.text((pad, 18), f"{c['name']} - AI narration disclosure, option A (top), 2 lines   (red = platform unsafe zone)", font=ImageFont.truetype(FONT_UI, 26), fill=(20, 20, 20))
    for k, (pos, pf, im, sh, ok) in enumerate(tiles):
        row, col = divmod(k, len(PLATFORMS)); y = head + row * (th + 60 + pad)
        for m, img in enumerate((im, sh)):
            x = pad + (col * 2 + m) * (tw + pad); S.paste(img.resize((tw, th), Image.LANCZOS), (x, y + 44))
            d.text((x, y + 12), f"A · {pf}{' · safe zones' if m else ''}" + ("" if ok else "  CHECK FAILED"), font=ImageFont.truetype(FONT_UI, 18), fill=(20, 20, 20) if ok else (200, 0, 0))
    S.save(os.path.join(OUT, f"sheet_{brand}.png"))
save(dict(note="AI-narration disclosure, option A (top) for every brand, complete approved line on 2 lines (approved 10 Nov; stills for visual approval). "
               "Each still uses the real slides.py edit (sample photo + slide text, near full push-in) and the real frame layer.",
          labels=LABEL, results=res), os.path.join(OUT, "positions.json"))
shutil.rmtree(TMP, ignore_errors=True)
ok = all(v["inside_safe_area"] and v["photo_pixels_under_disclosure"] == 0 for v in res.values())
print(f"{len(res)} stills -> {os.path.relpath(OUT, ROOT)}/ (sheet_<brand>.png); all inside safe area: {all(v['inside_safe_area'] for v in res.values())}; "
      f"no photo under the disclosure: {all(v['photo_pixels_under_disclosure'] == 0 for v in res.values())}")
sys.exit(0 if ok else 1)
