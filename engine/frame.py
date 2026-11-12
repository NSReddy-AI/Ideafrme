"""T2 main-frame layers for a job (static PNG + window mask + layout.json).
Usage: python frame.py <job>
brand.json -> frame.type:
  "framed"     : background, logos, headline, rounded video window, social row, ribbon (Jagan For Andhra)
  "fullscreen" : the edit fills 1080x1920; only a small handle tag on top (Tech / Editing brands)
Safe areas (platform safe_area): brand.json frame.safe_area = "enforce" (move handle/logo inside) or "warn" (report only).
Default: enforce for fullscreen brands, warn for framed brands (their approved template keeps its positions).
layout.json -> "safe_area": {platform, mode, issues:[{element, side, px}]}
M4 B1 - AI narration disclosure: only when project.json narration = "ai", the line from engine/tts.json "disclosure.te" is drawn
on a dark pill and checked against the platform safe area like every other element. Framed brands: the pill sits inside the video
window and a matching hole is cut in window_mask.png, so the frame layer (which lies UNDER the video) shows through.
Position: brand.json frame.disclosure.position (framed: window_top | window_bottom, fullscreen: top | bottom; default window_top / top);
RS_DISCLOSURE_POSITION overrides it for preview stills. layout.json then also has "narration" and "ai_disclosure".
Projects without a narration setting get exactly the same frame, mask and layout as before."""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import *
SS = 4
def headline(lines, top, max_size, box_h=220, maxw=980, shadow="#0459A8"):
    size = max_size
    while True:
        f = ImageFont.truetype(font_for(' '.join(lines)), size, layout_engine=ImageFont.Layout.RAQM)
        d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        wmax = max(d.textbbox((0, 0), l, font=f, anchor="ls")[2]-d.textbbox((0, 0), l, font=f, anchor="ls")[0] for l in lines)
        lh = round(size*1.32)
        if wmax <= maxw and lh*len(lines) <= box_h: break
        size -= 1
    if size < 56: print(f"WARNING: headline only fits at {size}px (<56). Shorten it.")
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t); y0 = top+(box_h-lh*len(lines))//2
    for i, l in enumerate(lines): d.text((W//2, y0+lh*i+lh//2), l, font=f, fill=(255, 255, 255, 255), anchor="mm")
    sh = Image.new('RGBA', (W, H), hexrgb(shadow)+(0,)); sh.putalpha(t.split()[3].point(lambda v: int(v*0.85)))
    sh = sh.transform((W, H), Image.AFFINE, (1, 0, -4, 0, 1, -6)).filter(ImageFilter.GaussianBlur(7))
    o = Image.new('RGBA', (W, H), (0, 0, 0, 0)); o.alpha_composite(sh); o.alpha_composite(t); return o, size
def circle(img, d):
    img = img.convert('RGBA').resize((d*4, d*4), Image.LANCZOS); m = Image.new('L', (d*4, d*4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d*4-1, d*4-1), fill=255); img.putalpha(m); return img.resize((d, d), Image.LANCZOS)
def social_box(c, cy):
    F = ImageFont.truetype(FONT_UI, 36); icon, gap = 40, 18
    names = [n for n in ("facebook", "youtube", "instagram") if asset(c, f"icon_{n}")]
    tw = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(c["handle"], font=F); wd = len(names)*(icon+gap)+tw
    return (int(W/2-wd/2), cy-icon//2, int(W/2+wd/2), cy+icon//2)
def social(c, cy):
    F = ImageFont.truetype(FONT_UI, 36); h = c["handle"]; icon, gap = 40, 18
    names = [n for n in ("facebook", "youtube", "instagram") if asset(c, f"icon_{n}")]
    tw = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(h, font=F)
    x = W/2-(len(names)*(icon+gap)+tw)/2; L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for n in names:
        L.alpha_composite(Image.open(asset(c, f"icon_{n}")).convert('RGBA').resize((icon, icon), Image.LANCZOS), (round(x), cy-icon//2)); x += icon+gap
    ImageDraw.Draw(L).text((x, cy), h, font=F, fill=(255, 255, 255, 255), anchor="lm"); return L
def _runs(txt):
    """Split mixed text into (text, is_telugu) runs: the Telugu font has no Latin letters (e.g. 'AI'), so each run gets its own font."""
    out = []
    for ch in txt:
        te = '\u0c00' <= ch <= '\u0c7f' or ch in '\u200c\u200d'
        kind = te if (te or ch.isalpha()) else (out[-1][1] if out else True)   # spaces / punctuation stay with the run they are in
        if out and out[-1][1] == kind: out[-1][0] += ch
        else: out.append([ch, kind])
    return [(t, k) for t, k in out]

def _mixed(size):
    fte = ImageFont.truetype(FONT_TE, size, layout_engine=ImageFont.Layout.RAQM); fui = ImageFont.truetype(FONT_UI, round(size * 0.92), layout_engine=ImageFont.Layout.RAQM)
    return fte, fui

def _mixed_width(txt, size):
    fte, fui = _mixed(size); return sum((fte if k else fui).getlength(t) for t, k in _runs(txt))


def _split2(txt, size):
    """Two lines of about equal width, broken at a space."""
    words = txt.split(" "); best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:]); d = abs(_mixed_width(a, size) - _mixed_width(b, size))
        if best is None or d < best[0]: best = (d, [a, b])
    return best[1] if best else [txt]

def disclosure(c, fr, pos, win, sy=None, logo_bottom=None, safe=None):
    """-> (layer RGBA WxH, box (l,t,r,b), text-only alpha mask L WxH, font px, text, lines). White text on a dark pill.
    Approved 10 Nov: position A (top) for every brand, the complete line split over 2 lines at about 34 px.
    Telugu runs use the Telugu font, Latin runs ('AI') the UI font, on one baseline per line."""
    D = fr.get("disclosure") or {}
    txt = load(os.path.join(ENGINE, "tts.json"))["disclosure"]["te"]; pad_x, pad_y, maxw = 30, 12, 900
    size, nlines = D.get("size", 34), D.get("lines", 2)
    while True:
        lines = _split2(txt, size) if nlines == 2 else [txt]
        if max(_mixed_width(l, size) for l in lines) <= maxw - 2 * pad_x or size <= 24: break
        size -= 1
    fte, fui = _mixed(size); asc, desc = fte.getmetrics(); lh = round((asc + desc) * 1.08)
    tw = max(_mixed_width(l, size) for l in lines); bw, bh = int(tw) + 2 * pad_x, lh * len(lines) + 2 * pad_y
    if fr["type"] == "framed":
        cx = win["x"] + win["size"] // 2
        top = win["y"] + 22 if pos == "window_top" else win["y"] + win["size"] - 22 - bh
    else:
        SL, ST, SR, SB = safe; cx = W // 2
        top = max(ST + 14, (logo_bottom or 0) + 14) if pos == "top" else (sy - 20 - 14 - bh if sy else SB - 14 - bh)
    box = (cx - bw // 2, top, cx - bw // 2 + bw, top + bh)
    layer = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle(tuple(v * SS for v in box), radius=min(28, bh // 2) * SS, fill=(12, 12, 12, 220))
    layer = layer.resize((W, H), Image.LANCZOS)
    tl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(tl)
    for i, line in enumerate(lines):
        x = cx - _mixed_width(line, size) / 2; base = box[1] + pad_y + i * lh + asc
        for t, k in _runs(line):
            f = fte if k else fui; dt.text((x, base), t, font=f, fill=(255, 255, 255, 255), anchor="ls"); x += f.getlength(t)
    layer.alpha_composite(tl)
    return layer, box, tl.split()[3], size, txt, lines

def disclosure_reserve(c):
    """Share of the EDIT's height (from the top) that the AI disclosure covers for this brand, worst case over all platforms,
    plus a 12 px margin. slides.py keeps photos and slide text below it, so the disclosure never covers them."""
    import glob
    fr = c["frame"]; pos = (fr.get("disclosure") or {}).get("position") or ("window_top" if fr["type"] == "framed" else "top"); worst = 0.0
    for pf in sorted(glob.glob(os.path.join(ROOT, "platforms", "*.json"))):
        sa = load(pf).get("safe_area") or {}; safe = (sa.get("left", 0), sa.get("top", 0), sa.get("right", W), sa.get("bottom", H))
        if fr["type"] == "framed":
            box = disclosure(c, fr, pos, fr["window"])[1]; win = fr["window"]; worst = max(worst, (box[3] - win["y"] + 12) / win["size"])
        else:
            ly = max(40, safe[1]); box = disclosure(c, fr, pos, None, sy=None, logo_bottom=(ly + 110) if asset(c, "logo_left") else None, safe=safe)[1]
            worst = max(worst, (box[3] + 12) / H) if pos == "top" else worst
    return round(worst, 4)

MUST = ("headline", "logo_left", "logo_right", "ai_disclosure", "captions", "cards")   # M4 B2 element classes (plan step 2)
def elements(j, c, fr, boxes, b):
    """Frame elements + the edit's caption band and card area (build/edit_layout.json, EDIT pixels -> screen pixels)."""
    E = {k: dict(box=[int(v) for v in bx], cls="must" if k in MUST else "may") for k, bx in boxes.items()}
    if fr["type"] == "framed" and asset(c, "ribbon"):
        r = Image.open(asset(c, "ribbon")); E["ribbon"] = dict(box=[0, 1644, r.width, 1644 + r.height], cls="may")
    ep = os.path.join(b, "edit_layout.json")
    if os.path.exists(ep):
        EL = load(ep); win = fr.get("window") if fr["type"] == "framed" else None; k = (win["size"] / EL["edit_size"][0]) if win else 1.0
        def to_screen(bx): return [int(win["x"] + bx[0] * k), int(win["y"] + bx[1] * k), int(win["x"] + bx[2] * k), int(win["y"] + bx[3] * k)] if win else [int(v) for v in bx]
        if EL.get("caption_band"): E["captions"] = dict(box=to_screen(EL["caption_band"]), cls="must")
        if EL.get("card_area"): E["cards"] = dict(box=to_screen(EL["card_area"]), cls="must")
    S = j["_platform"].get("safe_area_strict")
    for v in E.values():
        v["outside"] = [i for i in safe_check(j, {"x": v["box"]})]
        if S: v["outside_strict"] = [dict(side=sd, px=int(o)) for sd, o in (("top", S["top"] - v["box"][1]), ("bottom", v["box"][3] - S["bottom"]),
                                                                               ("left", S["left"] - v["box"][0]), ("right", v["box"][2] - S["right"])) if o > 0]
    return E

def build(j, c):
    fr = c["frame"]; b = os.path.join(j["_dir"], "build"); L = {}
    mode = fr.get("safe_area", "warn" if fr["type"] == "framed" else "enforce"); SL, ST, SR, SB = safe_area(j)
    if fr["type"] == "framed":
        win = fr["window"]; x0, y0, s = win["x"], win["y"], win["size"]; st = fr.get("border_px", 8)
        bg = Image.open(asset(c, "bg")).convert('RGB')
        sc = max(W/bg.width, H/bg.height); bg = bg.resize((round(bg.width*sc), round(bg.height*sc)), Image.LANCZOS)
        im = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width-W)//2+W, (bg.height-H)//2+H)).convert('RGBA')
        for key, cx in (("logo_left", 207), ("logo_right", 878)):
            if asset(c, key): im.alpha_composite(circle(Image.open(asset(c, key)), 185 if key == "logo_left" else 180), (cx-92, 239-92))
        hl, size = headline(j["title"], fr["headline_top"], fr.get("headline_max", 72)); im.alpha_composite(hl)
        bd = Image.new('RGBA', (W*SS, H*SS), (0, 0, 0, 0)); dd = ImageDraw.Draw(bd)
        dd.rounded_rectangle(((x0-st)*SS, (y0-st)*SS, (x0+s+st)*SS-1, (y0+s+st)*SS-1), radius=28*SS, fill=hexrgb(fr["border_color"])+(255,))
        dd.rounded_rectangle((x0*SS, y0*SS, (x0+s)*SS-1, (y0+s)*SS-1), radius=24*SS, fill=(0, 0, 0, 0))
        im.alpha_composite(bd.resize((W, H), Image.LANCZOS))
        im.alpha_composite(social(c, fr["social_y"]))
        if asset(c, "ribbon"): im.alpha_composite(Image.open(asset(c, "ribbon")).convert('RGBA'), (0, 1644))
        L = dict(type="framed", window=dict(x=x0, y=y0, size=s), headline_px=size)
        boxes = {"headline": hl.getbbox() or (W//2, fr["headline_top"], W//2, fr["headline_top"]), "social_row": social_box(c, fr["social_y"]),
                 "video_window": (x0, y0, x0+s, y0+s)}
        if asset(c, "logo_left"): boxes["logo_left"] = (207-92, 239-92, 207+93, 239+93)
        if asset(c, "logo_right"): boxes["logo_right"] = (878-92, 239-92, 878+88, 239+88)
    else:
        win = dict(x=0, y=0, size=0); im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sy = fr.get("social_y", 1760); lx, ly = 40, 40
        if mode == "enforce":
            sy = max(ST+20, min(sy, SB-20)); lx, ly = max(lx, SL), max(ly, ST)
        im.alpha_composite(social(c, sy))
        if asset(c, "logo_left"): im.alpha_composite(circle(Image.open(asset(c, "logo_left")), 110), (lx, ly))
        L = dict(type="fullscreen")
        boxes = {"social_row": social_box(c, sy)}
        if asset(c, "logo_left"): boxes["logo_left"] = (lx, ly, lx+110, ly+110)
    disc = None
    if j.get("narration") == "ai":   # M4 B1
        pos = os.environ.get("RS_DISCLOSURE_POSITION") or (fr.get("disclosure") or {}).get("position") or ("window_top" if fr["type"] == "framed" else "top")
        okpos = ("window_top", "window_bottom") if fr["type"] == "framed" else ("top", "bottom")
        if pos not in okpos: fail("DISCLOSURE_POSITION_INVALID", f"disclosure position must be one of {okpos} for a {fr['type']} brand (is '{pos}')")
        layer, dbox, dmask, dpx, dtxt, dlines = disclosure(c, fr, pos, win, sy=None if fr["type"] == "framed" else sy,
                                                   logo_bottom=(ly + 110) if fr["type"] != "framed" and asset(c, "logo_left") else None, safe=(SL, ST, SR, SB))
        im.alpha_composite(layer); boxes["ai_disclosure"] = dbox
        dmask.save(os.path.join(b, "ai_disclosure_mask.png"))
        def _over(a, z): return max(0, min(a[2], z[2]) - max(a[0], z[0])) * max(0, min(a[3], z[3]) - max(a[1], z[1])) > 0
        protected = [k for k, v in boxes.items() if k not in ("ai_disclosure", "video_window") and _over(dbox, v)]
        if protected: fail("DISCLOSURE_OVERLAP", f"the AI disclosure would cover {protected} - choose another position")
        disc = dict(text=dtxt, lines=dlines, position=pos, box=list(dbox), font_px=dpx, mask=os.path.join(b, "ai_disclosure_mask.png"),
                    covers_none_of=[k for k in boxes if k not in ("ai_disclosure", "video_window")], edit_reserve_top=disclosure_reserve(c))
    m = Image.new('L', (W*SS if fr["type"] == "framed" else 1, 1), 0)
    if fr["type"] == "framed":
        m = Image.new('L', (s*SS, s*SS), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, s*SS-1, s*SS-1), radius=24*SS, fill=255)
        if disc:   # hole in the video window where the disclosure pill is, so the frame layer under the video shows it
            l, t, r, bt = (v for v in disc["box"]); bh = bt - t
            ImageDraw.Draw(m).rounded_rectangle(((l-x0)*SS, (t-y0)*SS, (r-x0)*SS-1, (bt-y0)*SS-1), radius=bh//2*SS, fill=0)
        m.resize((s, s), Image.LANCZOS).save(os.path.join(b, "window_mask.png"))
    issues = safe_check(j, boxes)
    L["safe_area"] = dict(platform=j["platform"], mode=mode, area=dict(zip(("left", "top", "right", "bottom"), (SL, ST, SR, SB))), issues=issues)
    L["elements"] = elements(j, c, fr, boxes, b)   # M4 B2: every element, classed must-stay-visible / may-be-covered, in screen pixels
    for i in issues: emit("warning", code="SAFE_AREA", message=f"{i['element']} is {i['px']}px outside the {j['platform']} safe area ({i['side']})")
    if "narration" in j:   # M4 B1: narration projects only (older layouts stay byte-identical)
        L["narration"] = j["narration"]; L["title_seconds"] = float(j.get("title_seconds", 2.0))
        if disc: L["ai_disclosure"] = disc
    im.save(os.path.join(b, "frame.png")); save(L, os.path.join(b, "layout.json"))
    print("frame ->", {k: v for k, v in L.items() if k != "safe_area"}, f"| safe area ({mode}): {len(issues)} issue(s)")
if __name__ == "__main__":
    build(*job(sys.argv[1]))
