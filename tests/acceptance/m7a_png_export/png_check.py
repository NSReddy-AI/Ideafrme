import hashlib, json, sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W = Path("/Users/Nadish/projects/AI Video Editor./IDEAFRAME_M6_dev")
D = Path(__file__).resolve().parent   # copies of the exported draft (originally in the throwaway check session)
TE = str(W / "engine/fonts/NotoSansTelugu-Black.ttf"); EN = str(W / "m5/examples/posters/assets/fonts/Inter-Bold.otf")
man = json.loads((D / "manifest.json").read_text())
png = D / "poster.draft.png"; svg = D / "poster.draft.svg"
out = {"manifest": {k: man[k] for k in ("revision", "svg_sha256", "png_sha256", "browser_reported_qa")},
       "png_sha_ok": hashlib.sha256(png.read_bytes()).hexdigest() == man["png_sha256"],
       "svg_sha_ok": hashlib.sha256(svg.read_bytes()).hexdigest() == man["svg_sha256"] == "593bf05888c60fb16216abb2f6381281cd0ca94096b3805898a054eabecb930a"}
im = Image.open(png); out["png_mode_size"] = [im.mode, im.size]
A = np.array(im.convert("RGBA"))[:, :, 3]
out["edge_ink_px"] = int((A[0] > 0).sum() + (A[-1] > 0).sum() + (A[:, 0] > 0).sum() + (A[:, -1] > 0).sum())
# measured boxes from the browser (getBBox), same revision
L = [("title", "శ్రీకాకుళం క్షేత్రం", 72, (80, 103.4, 464.6, 105)), ("l2", "అక్కచెల్లెమ్మలకు స్త్రీ", 60, (64, 303.2, 492.5, 87)),
     ("l3", "ఇన్‌స్టాగ్రామ్ కార్‌ దుఃఖం", 60, (80, 503.2, 611.3, 87)), ("l4", "౦౧౨౩౪౫౬౭౮౯", 60, (80, 709.2, 450.8, 81)),
     ("l5", "“24 గంటలు సరిపోవు” Hello é", 56, (80, 902.6, 756.7, 81.5)), ("l6", "కృష్ణ బ్రహ్మ జ్ఞానం", 64, (300, 1123.3, 469.4, 93))]
ink_all = A > 0
claimed = np.zeros_like(ink_all)
layers = []
for name, text, fs, (mx, my, mw, mh) in L:
    y0, y1 = int(my) - 20, int(my + mh) + 20
    band = ink_all[max(0, y0):y1]; ys, xs = np.nonzero(band)
    ink = [int(xs.min()), int(ys.min()) + max(0, y0), int(xs.max()) + 1, int(ys.max()) + 1 + max(0, y0)]
    inside = ink[0] >= mx - 2 and ink[1] >= my - 2 and ink[2] <= mx + mw + 2 and ink[3] <= my + mh + 2
    claimed[max(0, y0):y1] |= band
    layers.append(dict(layer=name, measured=[mx, my, mw, mh], png_ink=ink, ink_inside_measured_box_2px=inside, left_offset_px=round(ink[0] - mx, 1)))
out["layers"] = layers
out["stray_ink_px_outside_layer_bands"] = int((ink_all & ~claimed).sum())
# shaping, word by word, against the engine (Pillow + RAQM, same font file, same size)
def mask_engine(word, fs):
    f = ImageFont.truetype(TE, fs, layout_engine=ImageFont.Layout.RAQM)
    g = Image.new("L", (fs * (len(word) + 4), fs * 3), 0); ImageDraw.Draw(g).text((fs, fs), word, font=f, fill=255)
    a = np.array(g) > 127; ys, xs = np.nonzero(a); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
def covered(m, o):
    if not m.sum(): return 1.0
    pad = np.pad(o, 1); hit = np.zeros_like(m)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1): hit |= pad[1 + dy:1 + dy + m.shape[0], 1 + dx:1 + dx + m.shape[1]]
    return float((m & hit).sum() / m.sum())
shaping = []
for name, text, fs, (mx, my, mw, mh) in L:
    if name == "l5": continue                      # mixed Latin/Telugu: checked visually
    band = (A[int(my) - 20:int(my + mh) + 20] > 127)
    fe = ImageFont.truetype(TE, fs, layout_engine=ImageFont.Layout.RAQM); fsp = ImageFont.truetype(EN, fs)
    x = mx; words = text.split(" ")
    for w in words:
        e = mask_engine(w, fs); adv = fe.getlength(w)
        x0 = int(x) - 8; win = band[:, max(0, x0):int(x + adv) + 8]
        best = None
        for dy in range(0, win.shape[0] - e.shape[0] + 1):            # find the word's ink by best placement
            for dx in range(0, max(1, win.shape[1] - e.shape[1] + 1)):
                p = win[dy:dy + e.shape[0], dx:dx + e.shape[1]]
                if p.shape != e.shape: continue
                s = min(covered(e, p), covered(p, e))
                if best is None or s > best[0]: best = (s, dx, dy)
        shaping.append(dict(layer=name, word=w, match=round(best[0], 4) if best else None))
        x += adv + fsp.getlength(" ")
out["shaping"] = shaping
out["shaping_min"] = min(s["match"] for s in shaping)
print(json.dumps(out, ensure_ascii=False, indent=1))
