"""M4 B2 - safe-area contact sheets: every brand x platform, with every layout element outlined and the unsafe zones shaded.
Run from the dev folder:  ~/.venvs/reelstudio/bin/python tools/safe_area_sheets.py
  red shade   = outside the platform safe area that QA uses (platforms/*.json safe_area)
  orange line = stricter published guidance (platforms/*.json safe_area_strict, advisory only)
  green box   = must-stay-visible element inside the safe area      red box = must-stay-visible element OUTSIDE it
  grey box    = may-be-covered element (ribbon, social row, video window)
Writes tests/acceptance/M4_gateB/B2/sheets_<date_time>/ (sheet_<brand>.png, <brand>_<platform>.png, elements.json). No reel is rendered."""
import os, sys, json, subprocess, tempfile, shutil, time
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "engine"))
from common import FONT_TE, FONT_UI, load, save
import build as BLD
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B2", "sheets_" + time.strftime("%Y%m%d_%H%M%S")); os.makedirs(OUT)
TMP = tempfile.mkdtemp(prefix="rs_b2_"); PFS = ("instagram", "youtube", "facebook"); R = {}
for brand in sorted(os.listdir(os.path.join(ROOT, "brands"))):
    if not os.path.exists(os.path.join(ROOT, "brands", brand, "brand.json")): continue
    c = load(os.path.join(ROOT, "brands", brand, "brand.json")); c["_dir"] = os.path.join(ROOT, "brands", brand); tiles = []
    for narr in ("ai",):
        for pf in PFS:
            d = os.path.join(TMP, f"{brand}_{pf}"); os.makedirs(os.path.join(d, "build"))
            save(dict(brand=brand, platform=pf, style=c["default_style"], title_seconds=2.0, title=["నమూనా శీర్షిక", "రెండో లైన్"],
                      hook=dict(line1="", line2="", line3="", tag_top="", tag_bottom=""), narration=narr, narrator="prakash", narrator_style="news", history=[]), os.path.join(d, "project.json"))
            W_, H_ = BLD.edit_size(c); save(dict(edit_size=[W_, H_], caption_band=BLD.caption_band(c), card_area=[90, 50, W_ - 90, 330] if H_ == W_ else [90, 310, W_ - 90, 590]),
                                            os.path.join(d, "build", "edit_layout.json"))
            r = subprocess.run([sys.executable, os.path.join(ROOT, "engine", "frame.py"), d], capture_output=True, text=True)
            if r.returncode: sys.exit(f"frame.py failed for {brand} {pf}: {r.stderr[-500:]}")
            b = os.path.join(d, "build"); LY = load(os.path.join(b, "layout.json")); fr = Image.open(os.path.join(b, "frame.png")).convert("RGBA")
            vid = Image.new("RGB", (W_, H_), (70, 90, 110)); dv = ImageDraw.Draw(vid)
            dv.text((W_ // 2, H_ // 2), "sample edit", font=ImageFont.truetype(FONT_UI, 60), fill=(200, 210, 220), anchor="mm")
            if LY["type"] == "framed":
                w = LY["window"]; comp = fr.copy(); comp.paste(vid.resize((w["size"], w["size"])), (w["x"], w["y"]), Image.open(os.path.join(b, "window_mask.png")).convert("L"))
            else: comp = vid.convert("RGBA"); comp.alpha_composite(fr)
            o = Image.new("RGBA", comp.size, (0, 0, 0, 0)); g = ImageDraw.Draw(o); sa = LY["safe_area"]["area"]; Wc, Hc = comp.size
            for box in ((0, 0, Wc, sa["top"]), (0, sa["bottom"], Wc, Hc), (0, sa["top"], sa["left"], sa["bottom"]), (sa["right"], sa["top"], Wc, sa["bottom"])): g.rectangle(box, fill=(230, 30, 30, 70))
            S = load(os.path.join(ROOT, "platforms", pf + ".json")).get("safe_area_strict")
            if S: g.rectangle((S["left"], S["top"], S["right"], S["bottom"]), outline=(255, 150, 0, 255), width=5)
            f = ImageFont.truetype(FONT_UI, 26)
            for k, v in LY["elements"].items():
                col = (150, 150, 150, 255) if v["cls"] == "may" else ((40, 200, 60, 255) if not v["outside"] else (255, 30, 30, 255))
                g.rectangle(tuple(v["box"]), outline=col, width=4); g.text((v["box"][0] + 6, v["box"][1] + 4), k, font=f, fill=col)
            comp = comp.convert("RGBA"); comp.alpha_composite(o); comp = comp.convert("RGB"); comp.save(os.path.join(OUT, f"{brand}_{pf}.png"))
            R[f"{brand}|{pf}"] = dict(mode=LY["safe_area"]["mode"], must_outside={k: v["outside"] for k, v in LY["elements"].items() if v["cls"] == "must" and v["outside"]},
                                      must_outside_strict={k: v.get("outside_strict") for k, v in LY["elements"].items() if v["cls"] == "must" and v.get("outside_strict")},
                                      may_outside=[k for k, v in LY["elements"].items() if v["cls"] == "may" and v["outside"]])
            tiles.append((pf, comp))
    tw, th, pad = 360, 640, 16; S_ = Image.new("RGB", (pad + 3 * (tw + pad), 70 + th + pad), (245, 245, 245)); d2 = ImageDraw.Draw(S_)
    d2.text((pad, 20), f"{c['name']} - safe areas (red = unsafe, orange = stricter guidance, green/red boxes = must-stay-visible)", font=ImageFont.truetype(FONT_UI, 22), fill=(20, 20, 20))
    for k, (pf, im) in enumerate(tiles):
        S_.paste(im.resize((tw, th)), (pad + k * (tw + pad), 60)); d2.text((pad + k * (tw + pad), 60 + th - 30), pf, font=ImageFont.truetype(FONT_UI, 22), fill=(255, 255, 255))
    S_.save(os.path.join(OUT, f"sheet_{brand}.png"))
save(R, os.path.join(OUT, "elements.json")); shutil.rmtree(TMP, ignore_errors=True)
for k, v in R.items(): print(k, v["mode"], "MUST outside:", v["must_outside"] or "none", "| strict:", list(v["must_outside_strict"]) or "none")
print("sheets ->", os.path.relpath(OUT, ROOT))
