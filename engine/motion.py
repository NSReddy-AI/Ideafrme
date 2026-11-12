"""Motion graphics for HyperFrames without GSAP: the browser's own Web Animations API (no library, no licence) and
fonts copied next to the composition (no internet while rendering).
HyperFrames finds every animation with document.getAnimations() and seeks it to the frame time (adapters/waapi.md).
Rules kept: animations are created synchronously at load, finite, paused, fill 'both'; no timers, no randomness.
The root carries data-no-timeline (no GSAP timeline to wait for; HyperFrames lint requires it for animation-API-only compositions).

    from motion import Comp
    c = Comp(1080, 1080, 54.62)
    c.clip("hook", 0.40, 2.69, "hero", "<span>...</span>", "top:560px")
    c.anim("#hook span", {"scale": 1.3, "opacity": 0, "filter": "blur(12px)"}, {"scale": 1, "opacity": 1, "filter": "blur(0px)"}, 0.40, 0.25, "expo.out")
    c.css(".hero{...}"); c.write("build/hf/index.html")

GSAP-style property names are accepted (x, y, scale, scaleY, rotation, opacity, filter, clipPath) and turned into
independent CSS 'translate' / 'scale' / 'rotate' so two animations on one element never overwrite each other."""
import os, json, shutil, html, math
ENGINE = os.path.dirname(os.path.abspath(__file__))
FONTS = {  # family -> (file in engine/fonts, weight)
    "Noto Sans Telugu": ("NotoSansTelugu-Black.ttf", 900),
    "Anton": ("Anton-Regular.ttf", 400),
    "Six Caps": ("SixCaps.ttf", 400),
}
EASE = {"none": "linear", "linear": "linear",
        "power1.out": "cubic-bezier(0.25,0.46,0.45,0.94)", "power2.out": "cubic-bezier(0.215,0.61,0.355,1)",
        "power3.out": "cubic-bezier(0.165,0.84,0.44,1)", "expo.out": "cubic-bezier(0.19,1,0.22,1)",
        "power2.in": "cubic-bezier(0.55,0.055,0.675,0.19)", "power2.inOut": "cubic-bezier(0.645,0.045,0.355,1)"}

def bounce_out(t):
    n, d = 7.5625, 2.75
    if t < 1 / d: return n * t * t
    if t < 2 / d: t -= 1.5 / d; return n * t * t + 0.75
    if t < 2.5 / d: t -= 2.25 / d; return n * t * t + 0.9375
    t -= 2.625 / d; return n * t * t + 0.984375
SAMPLED = {"bounce.out": bounce_out}

def _num(v, unit=""): return f"{v}{unit}" if isinstance(v, (int, float)) else str(v)
def css_frame(p):
    """GSAP-style props -> one CSS keyframe using independent transform properties."""
    f = {}
    if "x" in p or "y" in p: f["translate"] = f"{_num(p.get('x', 0), 'px')} {_num(p.get('y', 0), 'px')}"
    if "scale" in p: f["scale"] = _num(p["scale"])
    if "scaleY" in p: f["scale"] = f"1 {_num(p['scaleY'])}"
    if "rotation" in p: f["rotate"] = _num(p["rotation"], "deg")
    for k, c in (("opacity", "opacity"), ("filter", "filter"), ("clipPath", "clipPath")):
        if k in p: f[c] = _num(p[k])
    return f

def _lerp(a, b, t):
    out = {}
    for k in b:
        va, vb = a.get(k, b[k]), b[k]
        out[k] = va + (vb - va) * t if isinstance(va, (int, float)) and isinstance(vb, (int, float)) else (vb if t >= 1 else va)
    return out

class Comp:
    def __init__(self, w, h, duration, fps=30, comp_id="reel", lang="te", fonts=("Noto Sans Telugu", "Anton", "Six Caps")):
        self.w, self.h, self.dur, self.fps, self.id, self.lang, self.fonts = w, h, duration, fps, comp_id, lang, fonts
        self.els, self.js, self.styles = [], [], []

    def clip(self, id, s, e, cls, inner, style=""):
        """An element shown only between s and e seconds (hidden by CSS otherwise)."""
        self.els.append(f'<div id="{id}" class="clip {cls}" data-start="{s:.3f}" data-duration="{e - s:.3f}" data-track-index="1" style="{style}">{inner}</div>')
        self.js.append(f'V("#{id}",{s:.3f},{e:.3f});')

    def show(self, sel, s, e):
        """Make any element visible only between s and e (used for step counters)."""
        self.js.append(f'V({json.dumps(sel)},{s:.3f},{e:.3f});')

    def anim(self, sel, frm, to, at, dur, ease="power3.out", stagger=0, origin=None, box=None, keyframes=None):
        """from -> to at `at` seconds for `dur` seconds. keyframes=[(offset, props), ...] overrides from/to."""
        if keyframes: frames = [dict(css_frame(p), offset=round(o, 4)) for o, p in keyframes]; easing = EASE.get(ease, "linear")
        elif ease in SAMPLED:
            fn = SAMPLED[ease]; frames = [dict(css_frame(_lerp(frm, to, fn(i / 16))), offset=round(i / 16, 4)) for i in range(17)]; easing = "linear"
        else: frames = [css_frame(frm), css_frame(to)]; easing = EASE.get(ease, "linear")
        o = dict(d=round(at, 3), dur=round(dur, 3), e=easing)
        if stagger: o["st"] = stagger
        if origin: o["origin"] = origin
        if box: o["box"] = box
        self.js.append(f"A({json.dumps(sel)},{json.dumps(frames)},{json.dumps(o)});")

    def css(self, text): self.styles.append(text)

    def html(self):
        faces = "".join(f"@font-face{{font-family:'{f}';src:url('fonts/{FONTS[f][0]}');font-weight:{FONTS[f][1]};font-display:block;}}" for f in self.fonts)
        base = (f"html,body{{margin:0;padding:0;background:transparent;}}#root{{position:relative;width:{self.w}px;height:{self.h}px;overflow:hidden;background:transparent;}}"
                f".clip{{position:absolute;left:0;width:{self.w}px;visibility:hidden;opacity:0;}}")
        # Visibility spans the WHOLE reel (hidden-visible-hidden keyframes, fill both) so the animation is always "relevant":
        # an animation that has ended without fill drops out of document.getAnimations(), and HyperFrames could then not seek
        # back to it. persist() stops the browser from auto-removing finished animations.
        runtime = (f"const T={self.dur * 1000};\n"
                   "const V=(sel,s,e)=>document.querySelectorAll(sel).forEach(el=>{const a0=s*1000/T,a1=Math.min(1,e*1000/T),H={visibility:'hidden',opacity:0},S={visibility:'visible',opacity:1};"
                   "const a=el.animate([{...H,offset:0},{...H,offset:a0},{...S,offset:a0},{...S,offset:a1},{...H,offset:a1},{...H,offset:1}],"
                   "{duration:T,fill:'both',iterations:1});a.persist();a.pause();a.currentTime=0;});\n"
                   "const A=(sel,kf,o)=>document.querySelectorAll(sel).forEach((el,i)=>{if(o.origin)el.style.transformOrigin=o.origin;if(o.box)el.style.transformBox=o.box;"
                   "const a=el.animate(kf,{delay:(o.d+(o.st||0)*i)*1000,duration:o.dur*1000,easing:o.e,fill:'both',iterations:1});a.persist();a.pause();a.currentTime=0;});")
        return (f'<!doctype html>\n<html lang="{self.lang}"><head><meta charset="utf-8">\n<style>{faces}{base}{"".join(self.styles)}</style></head><body>\n'
                f'<div id="root" data-composition-id="{self.id}" data-no-timeline data-start="0" data-duration="{self.dur}" data-fps="{self.fps}" data-width="{self.w}" data-height="{self.h}">\n'
                + "\n".join(self.els) + f"\n</div>\n<script>\n{runtime}\n" + "\n".join(self.js) + "\n</script></body></html>\n")

    def write(self, path):
        """Write the composition and copy its fonts into fonts/ beside it (nothing loads from the internet)."""
        d = os.path.dirname(os.path.abspath(path)); os.makedirs(os.path.join(d, "fonts"), exist_ok=True); missing = []
        for f in self.fonts:
            src = os.path.join(ENGINE, "fonts", FONTS[f][0])
            if os.path.exists(src): shutil.copy(src, os.path.join(d, "fonts", FONTS[f][0]))
            else: missing.append(FONTS[f][0])
        open(path, "w", encoding="utf-8").write(self.html())
        return missing

def counter_steps(value, dec=0, steps=18, dur=0.6, ease=lambda t: 1 - (1 - t) ** 3):
    """A count-up as a list of (time offset, text): no script callbacks, every frame is a plain element."""
    out = []
    for k in range(steps + 1):
        t = k / steps; v = value * ease(t)
        txt = f"{v:,.{dec}f}" if dec else f"{round(v):,}"
        if not out or out[-1][1] != txt: out.append((round(t * dur, 3), txt))
    return out

def fit_px(text, font_file, start_px, max_w):
    """Largest font size (<= start_px) at which text fits max_w, measured with the real font (no runtime measuring)."""
    from PIL import ImageFont
    p = os.path.join(ENGINE, "fonts", font_file); size = start_px
    if not os.path.exists(p): return start_px
    while size > 20:
        f = ImageFont.truetype(p, size, layout_engine=ImageFont.Layout.RAQM)
        if f.getlength(text) <= max_w: return size
        size -= 2
    return size
