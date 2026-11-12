"""Build the edit (build/edit.mp4 + build/edit_audio.wav) from APPROVED material only (M4 B1.3 + B3).
Usage: python build.py <project>        then: python adapter.py render <project> --all-platforms
Which build is used:
  narration = ai | recorded   narrated slides: one slide per approved sentence (slide length = its narration), captions = the
                               approved written words timed to the voice, music + mix with the narration.
  narration = none + an approved narration script        text + music slides from the approved script (no voice, no captions).
  a video (project.json "video") + an approved plan       speaker reel (B3): the approved plan's beats in SOURCE ORDER, silences cut,
                               captions = the speaker's own words (transcript, verbatim), number cards = the approved cards, timed to
                               the spoken numbers, music + mix with the speaker's voice.
Nothing is written by a model here: every on-screen word comes from an approved script, an approved plan or the transcript.
Slide pictures (optional): inputs/slide_01.png, slide_02.jpg ... (one per sentence; the user's own pictures only).
Writes build/edit_layout.json (caption band and card area in EDIT pixels) for frame.py / qa.py (safe-area checks, B2).
RS_BUILD_SILENT_MUSIC=1 uses silent music (tests only)."""
import sys, os, json, re, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import te_numbers as TN

PY = sys.executable
def step(name, args, code):
    """Run another engine step as its own process (its events pass straight through to the app)."""
    r = subprocess.run([PY, os.path.join(ENGINE, args[0])] + args[1:], cwd=ROOT, text=True, capture_output=not EVENTS)
    if r.returncode: fail(code, f"{name} failed" + (f": {(r.stderr or r.stdout)[-1200:]}" if not EVENTS else ""))

def edit_size(c): return (1080, 1080) if c["frame"]["type"] == "framed" else (1080, 1920)
def caption_band(c):
    """Where captions sit in the EDIT: the lower band (framed: inside the window's lower part; fullscreen: above the bottom safe line)."""
    W_, H_ = edit_size(c)
    return [90, H_ - 240, W_ - 90, H_ - 40] if H_ == W_ else [90, 1300, W_ - 90, 1500]

def music_and_mix(j, b, dur, voice, cues):
    save(cues, os.path.join(b, "cues.json"))
    if os.environ.get("RS_BUILD_SILENT_MUSIC"):
        for f in ("music.wav", "sfx.wav"):
            run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=mono", os.path.join(b, f)])
    else: step("music", ["music.py", j["_dir"], f"{dur}", os.path.join(b, "cues.json")], "MUSIC_FAILED")
    step("mix", ["mix.py", j["_dir"], voice or "none", f"{dur}"], "MIX_FAILED")

def compose(b, base, overlays, out, dur):
    """base video + [(png_or_mov, x, y, t0, t1 or None)] -> out (30 fps, no audio)."""
    ins, fc, last = ["-i", base], "", "[0:v]"
    for k, (src, x, y, t0, t1) in enumerate(overlays, 1):
        ins += (["-loop", "1", "-t", f"{dur}", "-i", src] if src.endswith(".png") else ["-i", src])
        en = f":enable='between(t,{t0:.3f},{t1:.3f})'" if t0 is not None else ""
        fc += f"{last}[{k}:v]overlay={x}:{y}:format=auto:eof_action=pass{en}[v{k}];"; last = f"[v{k}]"
    fc += f"{last}format=yuv420p,fps=30[vo]"
    run(["ffmpeg", "-loglevel", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[vo]", "-t", f"{dur}", "-c:v", "libx264", "-crf", "14",
         "-preset", "fast", "-an", out], total_s=dur, pct_range=(55, 85))

# ---------------------------------------------------------------------------------------------------------------- slides (narrated / text)
def slide_beats(j, N, pics, full_sub=False):
    """One beat per approved sentence. On-screen words come from the approved WRITTEN text only:
    text = the sentence's first number as written plus its unit word ('31 లక్షల'); sub = the words after it (up to 4; with no voice:
    every other word of the sentence, so the slide carries the whole statement);
    a sentence without a number shows its first words."""
    out = []
    for i, l in enumerate(N["lines"]):
        tw = l["text"].split(); k = next((n for n, w in enumerate(tw) if re.match(r"^[\"'“‘(]*\d", w)), None)
        if k is None: text, sub = " ".join(tw[:3]), " ".join(tw[3:] if full_sub else tw[3:7]) or None
        else:
            e = k + (1 if k + 1 < len(tw) and TN._unit(tw[k + 1]) else 0); text = " ".join(tw[k:e + 1])
            sub = (" ".join(tw[:k] + tw[e + 1:]) if full_sub else " ".join(tw[e + 1:e + 5])) or " ".join(tw[max(0, k - 3):k]) or None
        out.append(dict(img=pics[i] if i < len(pics) else None, text=text.rstrip(".,!?।"), sub=(sub or "").rstrip(".,!?।") or None,
                        badge=None, dur=round(max(2.5, min(5.0, 0.09 * len(l["say"]) + 1.0)), 2)))
    return out

def build_slides(j, c, b):
    import narration_script as NS
    ok, code, msg, N = NS.verify(j)
    if not ok: fail(code, "the slide text comes from the approved narration script: " + msg)
    mode = j.get("narration", "none")
    pics = sorted(f"inputs/{f}" for f in os.listdir(os.path.join(j["_dir"], "inputs")) if re.match(r"slide_\d+\.(png|jpe?g|webp)$", f, re.I)) \
        if os.path.isdir(os.path.join(j["_dir"], "inputs")) else []
    beats = slide_beats(j, N, pics, full_sub=mode not in ("ai", "recorded")); save(beats, os.path.join(b, "beats.json")); progress(5, "slides")
    if mode in ("ai", "recorded"):
        import adapter
        bad = adapter.narration_ready(j)
        if bad: fail(bad[0], bad[1])
        if not os.path.exists(os.path.join(b, "narration_words.json")): fail("NARRATION_NOT_ALIGNED", "captions missing - run: adapter.py narrate <project>")
    step("slides", ["slides.py", j["_dir"]], "SLIDES_FAILED")
    shutil.move(os.path.join(b, "edit.mp4"), os.path.join(b, "slides.mp4")); dur = probe(os.path.join(b, "slides.mp4"))["duration"]
    cues = load(os.path.join(b, "cues.json")); band = caption_band(c); overlays = []
    if mode in ("ai", "recorded"):
        progress(40, "captions")
        step("captions", ["captions.py", j["_dir"], os.path.join(b, "narration_words.json"), os.path.join(b, "captions.mov")], "CAPTIONS_FAILED")
        overlays.append((os.path.join(b, "captions.mov"), band[0] + (band[2] - band[0] - 900) // 2, band[1], None, None))
    compose(b, os.path.join(b, "slides.mp4"), overlays, os.path.join(b, "edit.mp4"), dur)
    progress(88, "music and mix"); music_and_mix(j, b, dur, os.path.join(b, "narration.wav") if mode in ("ai", "recorded") else None, cues)
    return dict(kind=f"slides ({mode})", duration=round(dur, 2), slides=len(beats), captions=mode in ("ai", "recorded"), caption_band=band if overlays else None)

# ---------------------------------------------------------------------------------------------------------------- speaker (B3)
def keep_from_plan(P, words, gap=0.25, pad=0.08):
    """Approved beats in SOURCE order -> kept segments; pauses longer than `gap` inside a beat are cut."""
    segs = []
    for bt in sorted(P["facts"]["beats"], key=lambda x: x["from_word"]):
        ws = words[bt["from_word"]: bt["to_word"] + 1]
        if not ws: continue
        a = ws[0]["s"] - pad
        for w0, w1 in zip(ws, ws[1:]):
            if w1["s"] - w0["e"] > gap: segs.append([a, w0["e"] + pad]); a = w1["s"] - pad
        segs.append([a, ws[-1]["e"] + 0.18])
    segs = [[max(0.0, round(x, 3)), round(y, 3)] for x, y in segs]; out = []
    for s in segs:
        if out and s[0] <= out[-1][1]: out[-1][1] = max(out[-1][1], s[1])
        else: out.append(s)
    return out

def mapper(keep):
    off, M = 0.0, []
    for a, e in keep: M.append((a, e, off)); off += e - a
    def f(t):
        for a, e, o in M:
            if a - 1e-6 <= t <= e + 1e-6: return round(o + (t - a), 3)
        return None
    return f, round(off, 3)

def card_png(c, number, label, path, W_):
    """An approved number card (number as approved + the speaker's own label), brand colours, top of the edit."""
    T = c["title"]; im = Image.new("RGBA", (W_, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sn, sl = 120, 56
    while True:   # the card stays inside the card area (90 px side margins)
        fn = ImageFont.truetype(font_for(number), sn, layout_engine=ImageFont.Layout.RAQM); fl = ImageFont.truetype(font_for(label or "x"), sl, layout_engine=ImageFont.Layout.RAQM)
        wn = d.textlength(number, font=fn); wl = d.textlength(label or "", font=fl); bw = int(max(wn, wl)) + 100
        if bw <= W_ - 180 or sn <= 60: break
        sn, sl = sn - 6, max(30, sl - 3)
    x0 = (W_ - bw) // 2; d.rounded_rectangle((x0, 10, x0 + bw, 290), radius=36, fill=hexrgb(T.get("band1", "#8E0B12")) + (235,))
    d.text((W_ // 2, 112), number, font=fn, fill=hexrgb(T.get("accent", "#FFD400")) + (255,), anchor="mm")
    if label: d.text((W_ // 2, 228), label, font=fl, fill=(255, 255, 255, 255), anchor="mm")
    im.save(path)

def build_speaker(j, c, b):
    from planner import plan_hash
    pj = os.path.join(b, "plan.json")
    if not os.path.exists(pj): fail("PLAN_MISSING", "no plan yet: rs.py plan <project>")
    P = load(pj)
    if not P.get("approved") or P.get("approved_hash") != plan_hash(P) or j.get("plan_hash") != P.get("approved_hash"):
        fail("PLAN_NOT_APPROVED", "the plan is not approved (or changed after approval): rs.py approve <project> A|B|C|D [--checked]")
    T = load(os.path.join(b, "transcript.json")) if os.path.exists(os.path.join(b, "transcript.json")) else None
    if not T: fail("NO_TRANSCRIPT", "build/transcript.json missing - rs.py plan transcribes first")
    words = T["words"]; keep = keep_from_plan(P, words)
    if not (os.path.exists(os.path.join(b, "keep.json")) and load(os.path.join(b, "keep.json")) == keep): save(keep, os.path.join(b, "keep.json"))
    progress(5, "cutting")
    cutp = os.path.join(b, "cut.mov"); kp = os.path.join(b, "keep.json")
    if not (os.path.exists(cutp) and os.path.getmtime(cutp) > os.path.getmtime(kp) - 1 and load(kp) == keep and os.path.exists(os.path.join(b, ".cut_keep.json"))
            and load(os.path.join(b, ".cut_keep.json")) == keep):
        step("cut", ["cut.py", j["_dir"]], "CUT_FAILED"); save(keep, os.path.join(b, ".cut_keep.json"))   # re-cut only when the kept segments changed
    f, dur = mapper(keep)
    W_, H_ = edit_size(c); cut = os.path.join(b, "cut.mov"); pr = probe(cut)
    # picture: centre crop to the edit shape, slow push-in 100 -> 104 %
    ar = W_ / H_; cw, ch = (pr["h"] * ar, pr["h"]) if pr["w"] / pr["h"] > ar else (pr["w"], pr["w"] / ar)
    fx = float(j.get("face_x", 0.5)); x0 = max(0, min(pr["w"] - cw, pr["w"] * fx - cw / 2))
    base = os.path.join(b, "speaker_base.mp4"); nf = max(1, round(dur * FPS))
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", cut, "-vf", f"crop={int(cw)}:{int(ch)}:{int(x0)}:0,scale={int(W_ * 1.25)}:{int(H_ * 1.25)},"
         f"zoompan=z='1+0.04*on/{nf}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W_}x{H_}:fps=30", "-an", "-c:v", "libx264", "-crf", "14", "-preset", "fast", base],
        total_s=dur, pct_range=(15, 40))
    # captions: the speaker's own words, verbatim, on the edit timeline
    ew = []
    for w in words:
        s, e = f(w["s"]), f(w["e"])
        if s is not None and e is not None: ew.append(dict(w=w["w"], s=s, e=max(e, s + 0.05), hl=bool(TN._kind(w["w"]))))
    save(ew, os.path.join(b, "words.json")); progress(45, "captions")
    step("captions", ["captions.py", j["_dir"], os.path.join(b, "words.json"), os.path.join(b, "captions.mov")], "CAPTIONS_FAILED")
    band = caption_band(c); overlays = [(os.path.join(b, "captions.mov"), band[0] + (band[2] - band[0] - 900) // 2, band[1], None, None)]
    cards, cues = [], dict(impact=[0.05], whoosh=[], pop=[])
    beats = sorted(P["facts"]["beats"], key=lambda x: x["from_word"])
    for k, bt in enumerate(beats):
        g = bt.get("graphic") or {}
        if g.get("type") != "number": continue
        t0 = f(words[g["number_word"]]["s"]) if g.get("number_word") is not None else None
        t1 = f(words[bt["to_word"]]["e"])
        if t0 is None or t1 is None: continue
        t1 = max(t1, t0 + 1.6); p = os.path.join(b, f"card_{k + 1}.png"); card_png(c, g["number"], g.get("label"), p, W_)
        overlays.append((p, 0, 40 if H_ == W_ else 300, t0, t1)); cards.append(dict(number=g["number"], label=g.get("label"), s=t0, e=round(t1, 3),
                                                                                       spoken_at=words[g["number_word"]]["s"])); cues["impact"].append(t0)
    for a, _ in keep[1:]: cues["whoosh"].append(f(a))
    compose(b, base, overlays, os.path.join(b, "edit.mp4"), dur)
    voice = os.path.join(b, "voice.wav"); run(["ffmpeg", "-loglevel", "error", "-y", "-i", cut, "-vn", "-ac", "1", "-ar", "48000", voice])
    progress(88, "music and mix"); music_and_mix(j, b, dur, voice, cues)
    return dict(kind="speaker (approved plan)", duration=dur, segments=len(keep), cards=cards, caption_band=band, card_area=[90, 50, W_ - 90, 330] if H_ == W_ else [90, 310, W_ - 90, 590],
                captions_words=len(ew))

def main(project):
    j, c = job(project); b = os.path.join(j["_dir"], "build")
    if j.get("video") and os.path.exists(os.path.join(b, "plan.json")): R = build_speaker(j, c, b)
    elif os.path.exists(os.path.join(b, "narration.json")): R = build_slides(j, c, b)
    else: fail("NOTHING_TO_BUILD", "nothing approved to build: a video + approved plan (rs.py plan/approve) or an approved script (rs.py script/script-approve)")
    W_, H_ = edit_size(c); R.update(edit_size=[W_, H_]); save(R, os.path.join(b, "edit_layout.json"))
    import rs; rs.log(j, f"edit built: {R['kind']}, {R['duration']} s")
    progress(100); emit("output", path=os.path.join(b, "edit.mp4"), audio=os.path.join(b, "edit_audio.wav"), layout=os.path.join(b, "edit_layout.json"))
    print(f"build -> build/edit.mp4 + build/edit_audio.wav | {R['kind']} | {R['duration']} s")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1])
