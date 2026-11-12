"""Two candidate upgrades, tested side by side with what Reel Studio does today. Run with Reel Studio's Python:
  ~/.venvs/reelstudio/bin/python tests/test_scenes_denoise.py
A) Scene cuts: PySceneDetect 0.7.3 (BSD-3, AdaptiveDetector and ContentDetector) vs the detector inside engine/facetrack.py,
   on 3 clips whose cuts were checked by eye (news: 4 cuts, studio: 8 cuts, selfie: none). A cut counts if found within 2 frames.
B) Speech cleaning: DeepFilterNet (deep-filter binary, MIT/Apache-2.0) vs no cleaning, judged by the Telugu speech-to-text
   (character errors against the approved captions), plus 15 s before/after samples to listen to.
Nothing in the engine changes; tools live in ~/.venvs/rs_asr and ~/.cache/rs_tools."""
import os, sys, json, time, subprocess, re, unicodedata
import numpy as np, cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "tests", "out"); os.makedirs(OUT, exist_ok=True)
TOP = os.path.dirname(ROOT); ASR_PY = os.path.expanduser("~/.venvs/rs_asr/bin/python"); DF = os.path.expanduser("~/.cache/rs_tools/deep-filter")
say = lambda *a: print(*a, flush=True); R = {"scenes": {}, "denoise": {}}
CLIPS = {"news": (os.path.join(TOP, "raw footage", "What jagan said.mov"), [294, 380, 601, 662]),
         "studio": (os.path.join(ROOT, "tests", "clips", "studio_presenter.mp4"), [351, 427, 466, 530, 581, 592, 654, 745]),
         "selfie": (os.path.join(ROOT, "tests", "clips", "Selfie.MOV"), [])}
T = 30.0
def ours(path):
    """The cut detector inside engine/facetrack.py (colour histogram + brightness jump), first 30 s."""
    t0 = time.time(); fps = cv2.VideoCapture(path).get(cv2.CAP_PROP_FPS) or 30
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", path, "-t", str(T), "-vf", "scale=64:36", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    prev, cuts, i = None, [], 0
    while True:
        b = p.stdout.read(64 * 36 * 3)
        if len(b) < 64 * 36 * 3: break
        f = np.frombuffer(b, np.uint8).reshape(36, 64, 3)
        hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV); h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]); cv2.normalize(h, h)
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32)
        if prev is not None and (cv2.compareHist(prev[0], h, cv2.HISTCMP_CORREL) < 0.5 or float(np.abs(g - prev[1]).mean()) > 18): cuts.append(i)
        prev, i = (h, g), i + 1
    p.wait(); return cuts, round(time.time() - t0, 1)
PSD = r'''
import sys, json, time
from scenedetect import detect, AdaptiveDetector, ContentDetector
out = {}
for name, det in (("adaptive", AdaptiveDetector()), ("content", ContentDetector())):
    t = time.time(); sc = detect(sys.argv[1], det, end_time=float(sys.argv[2]))
    out[name] = dict(cuts=[s[0].get_frames() for s in sc[1:]], seconds=round(time.time() - t, 1))
print(json.dumps(out))
'''
def score(found, truth, tol=2):
    hit = [t for t in truth if any(abs(t - f) <= tol for f in found)]; extra = [f for f in found if not any(abs(t - f) <= tol for t in truth)]
    return dict(found=found, missed=[t for t in truth if t not in hit], extra=extra, recall=round(len(hit) / len(truth), 2) if truth else None)
say("== A. scene cuts (first 30 s of each clip)")
for name, (path, truth) in CLIPS.items():
    if not os.path.exists(path): say(f"   {name}: clip missing"); continue
    c, s = ours(path); R["scenes"].setdefault(name, {})["reel_studio_today"] = dict(score(c, truth), seconds=s)
    r = subprocess.run([ASR_PY, "-c", PSD, path, str(T)], capture_output=True, text=True)
    if r.returncode: say(f"   {name}: PySceneDetect failed: {r.stderr[-300:]}"); continue
    for k, v in json.loads(r.stdout.strip().splitlines()[-1]).items(): R["scenes"][name][f"pyscenedetect_{k}"] = dict(score(v["cuts"], truth), seconds=v["seconds"])
    for k, v in R["scenes"][name].items(): say(f"   {name:7} {k:24} recall {v['recall']}  missed {v['missed']}  extra {v['extra']}  ({v['seconds']} s)")
say("== B. speech cleaning (Telugu, 41 s reference)")
REF = json.load(open(os.path.join(ROOT, "tests", "asr_reference_what_jagan_said.json")))
raw48 = os.path.join(OUT, "dn_raw48k.wav")
S = REF["segments_in_order"]; parts = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(S))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", CLIPS["news"][0], "-filter_complex", parts + "".join(f"[a{i}]" for i in range(len(S))) + f"concat=n={len(S)}:v=0:a=1[o]",
                "-map", "[o]", "-ac", "1", "-ar", "48000", raw48], check=True)
dfdir = os.path.join(OUT, "dn_df"); os.makedirs(dfdir, exist_ok=True); t0 = time.time()
r = subprocess.run([DF, "--compensate-delay", "-o", dfdir, raw48], capture_output=True, text=True); R["denoise"]["deepfilter_seconds"] = round(time.time() - t0, 1)
dfw = os.path.join(dfdir, os.path.basename(raw48))
if r.returncode or not os.path.exists(dfw): say("   deep-filter failed:", (r.stderr or r.stdout)[-400:]); R["denoise"]["error"] = (r.stderr or r.stdout)[-400:]
else:
    say(f"   deep-filter: {R['denoise']['deepfilter_seconds']} s for 41 s of audio")
    for nm, src in (("before", raw48), ("after", dfw)):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-t", "15", os.path.join(OUT, f"denoise_{nm}_15s.wav")], check=True)
    def cer(wav48):
        w16 = wav48.replace(".wav", "_16k.wav"); subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav48, "-ar", "16000", "-ac", "1", w16], check=True)
        out = os.path.join(OUT, os.path.basename(w16).replace(".wav", "_t.json"))
        r = subprocess.run([sys.executable, os.path.join(ROOT, "engine", "transcribe.py"), "--audio", w16, "--lang", "te", "--out", out], capture_output=True, text=True)
        if r.returncode: return None, r.stderr[-300:]
        n = lambda t: re.sub(r"[\s\"'“”‘’.,!?;:()\[\]{}…\-–—|।‌‍]", "", unicodedata.normalize("NFC", t))
        a, b = n(REF["text"]), n(" ".join(x["w"] for x in json.load(open(out))["words"]))
        prev = list(range(len(b) + 1))
        for i, x in enumerate(a, 1):
            cur = [i]
            for j, y in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
            prev = cur
        return round(prev[-1] / len(a), 3), None
    for nm, src in (("no_cleaning", raw48), ("deepfilternet", dfw)):
        say(f"   transcribing ({nm}) ... about 6 minutes"); c, err = cer(src); R["denoise"][nm + "_cer"] = c if c is not None else err; say(f"   {nm}: character errors {c}")
json.dump(R, open(os.path.join(OUT, "scenes_denoise_report.json"), "w"), indent=1, ensure_ascii=False)
say("\nreport -> tests/out/scenes_denoise_report.json | listen: tests/out/denoise_before_15s.wav vs denoise_after_15s.wav")
