"""T1 title page at 4K (2160x3840) + 1080x1920 copy.
Usage: python title.py <job>
Needs job.json: hook{line1,line2,line3,tag_top,tag_bottom}, title_person (cut-out PNG with alpha), title_bg (image)
Optional job.json: title_face_x (0-1, face position in the person PNG, default 0.5), title_scale.
Colours come from brand.json -> title."""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from common import *
K = 2; WW, HH = W*K, H*K
_TXT=['']
def F(sz): return ImageFont.truetype(font_for(_TXT[0]), int(sz), layout_engine=ImageFont.Layout.RAQM)
def cover(img, w, h):
    s = max(w/img.width, h/img.height); img = img.resize((round(img.width*s), round(img.height*s)), Image.LANCZOS)
    l, t = (img.width-w)//2, (img.height-h)//2; return img.crop((l, t, l+w, t+h))
def fit(txt, maxw, start):
    _TXT[0] = txt; s = start
    while s > 40:
        b = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), txt, font=F(s), anchor="mm")
        if b[2]-b[0] <= maxw: return F(s)
        s -= 2
    return F(s)
def brush(w, h, color, seed):
    r = np.random.default_rng(seed); ww, hh = w*2, h*2
    m = Image.new('L', (ww, hh), 0); d = ImageDraw.Draw(m)
    top = [(x, int(hh*0.10+r.normal(0, hh*0.035))) for x in range(0, ww+1, ww//60)]
    bot = [(x, int(hh*0.90+r.normal(0, hh*0.035))) for x in range(ww, -1, -ww//60)]
    d.polygon(top+bot, fill=255)
    for _ in range(26):
        y = int(r.integers(int(hh*0.08), int(hh*0.92))); x0 = int(r.integers(0, ww//10)); ln = int(r.integers(ww//8, ww//3))
        d.line([(x0, y), (x0+ln, y)], fill=0, width=int(r.integers(2, 7)))
        x1 = ww-int(r.integers(0, ww//10)); d.line([(x1-ln, y), (x1, y)], fill=0, width=int(r.integers(2, 7)))
    m = m.filter(ImageFilter.GaussianBlur(1.2)).resize((w, h), Image.LANCZOS)
    base = np.clip(np.zeros((h, w, 3), np.float32)+np.array(color, np.float32)+r.normal(0, 10, (h, w))[..., None], 0, 255)
    im = Image.fromarray(base.astype(np.uint8)).convert('RGBA'); im.putalpha(m); return im
def text(img, s, cx, cy, font, fill, stroke=0, sf=None, shadow=None):
    if shadow:
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((cx+4*K, cy+6*K), s, font=font, fill=shadow, anchor="mm", stroke_width=stroke, stroke_fill=shadow)
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6*K)))
    ImageDraw.Draw(img).text((cx, cy), s, font=font, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=sf)
def build(j, c):
    T = c["title"]; hk = j["hook"]; d = j["_dir"]; out = Image.new('RGBA', (WW, HH), (0, 0, 0, 255))
    # background: gradient + glow, textured by the topic photo
    top, bot, glow = hexrgb(T["grad_top"]), hexrgb(T["grad_bottom"]), hexrgb(T["glow"])
    t = np.linspace(0, 1, HH)[:, None, None]
    g = (np.array(top)*(1-t)+np.array(bot)*t)*np.ones((1, WW, 1))
    yy, xx = np.mgrid[0:HH, 0:WW]; r = np.sqrt(((xx-WW/2)/(WW*0.55))**2+((yy-HH*0.27)/(HH*0.30))**2)
    gw = np.clip(1-r, 0, 1)[..., None]**1.6; g = g*(1-0.75*gw)+np.array(glow)*0.75*gw
    bgp = os.path.join(d, j["title_bg"]) if j.get("title_bg") else None
    if bgp and os.path.exists(bgp):
        tex = cover(Image.open(bgp).convert('L'), WW, HH).filter(ImageFilter.GaussianBlur(6*K))
        g = g*(0.88+0.24*(np.array(tex, np.float32)[..., None]/255))
    out.alpha_composite(Image.fromarray(g.clip(0, 255).astype(np.uint8)).convert('RGBA'))
    # bottom fade
    fade = hexrgb(T["fade"]); ga = np.zeros((HH, WW), np.uint8); ys = np.arange(1000*K, HH)
    ga[1000*K:] = (np.clip((ys-1000*K)/(600*K), 0, 1)**0.9*255)[:, None]
    fl = Image.new('RGBA', (WW, HH), fade+(255,)); fl.putalpha(Image.fromarray(ga)); out.alpha_composite(fl)
    # person, centred on the face, oval-feathered
    pp = os.path.join(d, j["title_person"]) if j.get("title_person") else None
    if pp and os.path.exists(pp):
        p = Image.open(pp).convert('RGBA'); fx = j.get("title_face_x", 0.5)
        sc = j.get("title_scale") or (1900*K/2)/p.height
        p = p.resize((round(p.width*sc), round(p.height*sc)), Image.LANCZOS)
        pa = np.array(p.split()[3]).astype(np.float32); py, px_ = np.mgrid[0:p.height, 0:p.width]
        rr = np.sqrt(((px_-fx*p.width)/(0.45*p.width))**2+((py-0.30*p.height)/(0.95*p.height))**2)
        p.putalpha(Image.fromarray((pa*np.clip((1-rr)/0.22, 0, 1)).astype(np.uint8)))
        layer = Image.new('RGBA', (WW, HH), (0, 0, 0, 0)); x = round(WW/2-fx*p.width)
        crop = p.crop((max(0, -x), 0, min(p.width, WW-x), p.height)); layer.alpha_composite(crop, (max(0, x), 170*K))
        la = np.array(layer.split()[3]).astype(np.float32)*np.clip((940*K-np.arange(HH))/(150*K), 0, 1)[:, None]
        layer.putalpha(Image.fromarray(la.astype(np.uint8))); out.alpha_composite(layer)
    # hanging sign
    if hk.get("tag_top"):
        sw, sh_ = 300*K, 215*K; sign = Image.new('RGBA', (sw+40*K, sh_+40*K), (0, 0, 0, 0)); dd = ImageDraw.Draw(sign)
        dd.rounded_rectangle((20*K, 20*K, 20*K+sw, 20*K+sh_), radius=18*K, fill=hexrgb(T["sign"])+(255,), outline=(0x8A, 0x6A, 0x3A, 255), width=5*K)
        for cx in (60*K, sw-20*K): dd.ellipse((cx-7*K, 40*K, cx+7*K, 54*K), fill=(30, 20, 10, 255))
        text(sign, hk["tag_top"], 20*K+sw//2, 20*K+sh_*0.36, fit(hk["tag_top"], sw-40*K, 52*K), (255, 255, 255, 255))
        text(sign, hk.get("tag_bottom", ""), 20*K+sw//2, 20*K+sh_*0.72, fit(hk.get("tag_bottom", " "), sw-40*K, 58*K), hexrgb(T["accent"])+(255,))
        sign = sign.rotate(-2.5, resample=Image.BICUBIC, expand=True)
        SX, SY = 735*K, 60*K; pin = (SX+sw//2+20*K, 18*K); dd = ImageDraw.Draw(out)
        dd.line([pin, (SX+60*K, SY+30*K)], fill=(40, 30, 20, 255), width=4*K); dd.line([pin, (SX+sw-20*K, SY+36*K)], fill=(40, 30, 20, 255), width=4*K)
        out.alpha_composite(sign, (SX-20*K, SY-20*K))
        ImageDraw.Draw(out).ellipse((pin[0]-11*K, pin[1]-11*K, pin[0]+11*K, pin[1]+11*K), fill=(190, 160, 90, 255), outline=(60, 40, 20, 255), width=3*K)
    # bands + lines
    out.alpha_composite(brush(1060*K, 245*K, hexrgb(T["band1"]), 11), (10*K, 985*K))
    text(out, hk["line1"], WW//2, 1105*K, fit(hk["line1"], 960*K, 150*K), hexrgb(T["accent"])+(255,), 4*K, (60, 0, 0, 255), (0, 0, 0, 160))
    out.alpha_composite(brush(1040*K, 265*K, hexrgb(T["band2"]), 12), (20*K, 1235*K))
    text(out, hk["line2"], WW//2, 1365*K, fit(hk["line2"], 930*K, 140*K), hexrgb(T["band2_text"])+(255,))
    raw3 = hk["line3"]; mark = raw3[-1] if raw3[-1] in "?!" else ""; l3 = raw3.rstrip("?!")
    f3 = fit(l3, 880*K, 190*K); dd = ImageDraw.Draw(out)
    b = dd.textbbox((0, 0), l3, font=f3, anchor="ls"); tw = b[2]-b[0]
    fq = ImageFont.truetype(FONT_MARK, int(f3.size*1.45))
    qw = (lambda b: b[2]-b[0])(dd.textbbox((0, 0), mark, font=fq, anchor="ls")) if mark else 0
    x0 = WW/2-(tw+qw+10*K)/2; base = 1660*K
    sh = Image.new('RGBA', (WW, HH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x0+6*K, base+8*K), l3, font=f3, fill=(0, 0, 0, 200), anchor="ls", stroke_width=10*K, stroke_fill=(0, 0, 0, 200))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5*K))); dd = ImageDraw.Draw(out)
    dd.text((x0, base), l3, font=f3, fill=hexrgb(T["accent"])+(255,), anchor="ls", stroke_width=9*K, stroke_fill=(0x1A, 0x0A, 0x05, 255))
    if mark: dd.text((x0+tw+10*K, base+10*K), mark, font=fq, fill=(0xE5, 0x1B, 0x1B, 255), anchor="ls", stroke_width=8*K, stroke_fill=(0x1A, 0x0A, 0x05, 255))
    b = os.path.join(d, "build"); out = out.convert('RGB')
    out.save(os.path.join(b, "title_4k.png")); out.save(os.path.join(b, "cover_4k.jpg"), quality=95)
    out.resize((W, H), Image.LANCZOS).save(os.path.join(b, "title_1080.png"))
    print("title ->", os.path.join(b, "title_4k.png"))
if __name__ == "__main__":
    build(*job(sys.argv[1]))
