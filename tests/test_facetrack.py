"""Face tracking acceptance test (dev copy only). Run with Reel Studio's Python, from the Reel Studio_dev folder:
  ~/.venvs/reelstudio/bin/python tests/test_facetrack.py                                   (news clip + its labels)
  ~/.venvs/reelstudio/bin/python tests/test_facetrack.py --truth tests/facetrack_truth_studio_presenter.json
  ~/.venvs/reelstudio/bin/python tests/test_facetrack.py --clip "path/to/phone video.mov" [--ss 0 --t 30]   (no labels yet)
A truth file (labelled by eye) names its clip and where the real speaker is in each shot.
OFF: tracking refuses to run on a project with face_tracking false, and reel_002 still matches the locked baseline.
ON : a test project (zz_facetrack_test) is built from 30 s of a wide speaker video: MediaPipe reframes it to 1:1,
     Telugu captions are laid on, music + mix, then the normal adapter render + QA. Accuracy is measured twice:
     from the tracker's own detections, and independently by re-detecting faces on the finished 1:1 frames.
Writes tests/out/facetrack_report.json and tests/out/facetrack_viz.jpg. Changes nothing outside Reel Studio_dev."""
import os, sys, json, time, shutil, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); E = os.path.join(ROOT, "engine"); PY = sys.executable
sys.path.insert(0, E)
OUT = os.path.join(ROOT, "tests", "out"); os.makedirs(OUT, exist_ok=True)
import argparse
ap = argparse.ArgumentParser(); ap.add_argument("--truth"); ap.add_argument("--clip"); ap.add_argument("--ss", type=float, default=0); ap.add_argument("--t", type=float, default=30)
A = ap.parse_args()
if not A.truth and not A.clip: A.truth = os.path.join(ROOT, "tests", "facetrack_truth_what_jagan_said.json")
TRUTH = json.load(open(A.truth)) if A.truth else None
SRC = A.clip or os.path.normpath(os.path.join(ROOT, TRUTH["source"]))
SS, T = (TRUTH["clip"]["ss"], TRUTH["clip"]["t"]) if TRUTH else (A.ss, A.t)
NAME = "".join(ch if ch.isalnum() else "_" for ch in os.path.splitext(os.path.basename(SRC))[0]).strip("_").lower()[:40]
BASE = "2026-11-03_reel_002_development"; TEST = f"zz_facetrack_{NAME}"
if not os.path.exists(SRC): sys.exit(f"clip not found: {SRC}")
R = dict(source=SRC, kind=TRUTH.get("kind") if TRUTH else "unlabelled", off={}, on={}); t_all = time.time()
REPORT, VIZ = os.path.join(OUT, f"facetrack_report_{NAME}.json"), os.path.join(OUT, f"facetrack_viz_{NAME}.jpg")
def sh(args, **kw):
    t = time.time(); r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT, **kw); return r, round(time.time() - t, 1)
def say(*a): print(*a, flush=True)

say("== OFF 1: tracking must refuse a project with face_tracking off")
r, _ = sh([PY, os.path.join(E, "facetrack.py"), SRC, os.path.join(OUT, "should_not_exist.mp4"), "--project", BASE], env=dict(os.environ, RS_EVENTS="1"))
refused = r.returncode != 0 and "FACE_TRACKING_OFF" in r.stdout and not os.path.exists(os.path.join(OUT, "should_not_exist.mp4"))
R["off"]["refuses_when_off"] = refused; say("   refused:", refused)

say("== OFF 2: reel_002 vs locked baseline (tracking not used)")
r, secs = sh([PY, os.path.join(E, "adapter.py"), "render", BASE, "--platform", "instagram", "--baseline", os.path.join(ROOT, "tests", "baseline_reel_002.json")])
done = json.loads(r.stdout.strip().splitlines()[-1]); rep = json.load(open(done["outputs"][0]["qa_report"])) if done.get("outputs") else {}
R["off"]["baseline"] = dict(ok=done.get("ok"), qa_passed=done.get("qa_passed"), render_s=secs, frames=rep.get("frames"), size=rep.get("file_size"),
                           lufs=rep.get("loudness_lufs"), peak=rep.get("true_peak_db"), failed=[c["name"] for c in rep.get("checks", []) if not c["passed"]])
say("  ", R["off"]["baseline"])

say("== ON 1: test project with face_tracking true")
d = os.path.join(ROOT, "projects", TEST); b = os.path.join(d, "build"); os.makedirs(b, exist_ok=True); os.makedirs(os.path.join(d, "inputs"), exist_ok=True)
pj = json.load(open(os.path.join(ROOT, "projects", BASE, "project.json")))
pj.update(face_tracking=True, edit_duration=T, status="test", brief="face tracking test (not a real reel)", history=[], video=None,
          title_person=os.path.join("..", BASE, pj["title_person"]), title_bg=os.path.join("..", BASE, pj["title_bg"]))
json.dump(pj, open(os.path.join(d, "project.json"), "w"), ensure_ascii=False, indent=2)

say("== ON 2: MediaPipe reframe to 1:1 (", T, "s )")
tracked = os.path.join(b, "tracked.mp4")
r, secs = sh([PY, os.path.join(E, "facetrack.py"), SRC, tracked, "--aspect", "1:1", "--project", TEST, "--ss", str(SS), "--t", str(T)])
if r.returncode: say(r.stdout[-1500:], r.stderr[-1500:]); R["on"]["error"] = (r.stderr or r.stdout)[-1500:]; json.dump(R, open(REPORT, "w"), indent=1); sys.exit(1)
trk = json.load(open(os.path.splitext(tracked)[0] + "_track.json")); st = trk["stats"]
R["on"]["tracking"] = dict(unsure_shots=st.get("unsure_shots"), shots=st.get("shots"), speaker_by_mouth=os.path.exists(os.path.join(E, "models", "face_landmarker.task")), total_s=secs, detect_s=st["time_detect_s"], render_s=st["time_render_s"], frames=st["frames"], coverage=st["coverage"], by=st["by"],
                          cuts=len(st["cuts"]), tracked=st["tracked"], centre_crop=st["centre_crop"])
say("  ", R["on"]["tracking"])

say("== ON 3: independent check - find the speaker again on the finished 1:1 frames")
import facetrack
det = (facetrack.MatteDetector if os.environ.get("RS_FACE_BACKEND") == "matte" else facetrack.MPDetector)(30.0)
fps_in = st["fps_in"]; cuts_out = sorted({int(round(c * 30 / fps_in)) for c in st["cuts"]}); raw2, n2 = {}, 0
for i, f in enumerate(facetrack.frames(tracked, 1080, 1080)):
    if i % 5 == 0 or i in cuts_out: raw2[i] = det(f, i)
    n2 = i + 1
AX, AIM = st.get("axis", "x"), st.get("aim", 0.5)
sp = facetrack.choose_speaker(raw2, cuts_out, n2, None, AX); offs = np.array([abs(v - AIM) for v in sp.values() if v is not None])
# ground truth (labelled by eye): where the REAL speaker lands in the output, and frames following someone else
if TRUTH:
    k_ = 0 if AX == "x" else 1
    xs_ = trk.get("crop_pos", trk["crop_x"]); cw_ = st["crop"][k_]; W_ = st["source_size"][k_]; tgt_ = trk["target"]; pos, wrong, labelled = [], 0, 0
    shift_ = (0.5 - AIM) * cw_ / W_                       # the plan's target includes the headroom shift
    for sh_ in TRUTH["shots"]:
        a_, b_ = sh_["frames"]; pts = sorted((int(k), v) for k, v in (sh_.get("points") or {}).items())
        if sh_.get("speaker_cx") is not None: pts = [(a_, sh_["speaker_cx"]), (b_ - 1, sh_["speaker_cx"])]
        if not pts: continue
        tol = sh_.get("tolerance", 0.05)
        for i in range(a_, min(b_, len(xs_))):
            gx = float(np.interp(i, [p[0] for p in pts], [p[1] for p in pts]))
            pos.append((gx * W_ - xs_[i]) / cw_); labelled += 1
            if tgt_[i] is not None and abs(tgt_[i] - shift_ - gx) > tol + 0.08: wrong += 1      # following a different person
    pos = np.array(pos)
    R["on"]["ground_truth"] = dict(axis=AX, frames=int(len(pos)), mean_offset=round(float(np.mean(np.abs(pos - AIM))), 3), within_15pct=round(float(np.mean(np.abs(pos - AIM) <= 0.15)), 3),
                                   out_of_frame=int(np.sum((pos < 0.05) | (pos > 0.95))), wrong_person_frames=int(wrong))
    say("   ground truth:", R["on"]["ground_truth"])
R["on"]["independent"] = dict(checked=int(len(raw2)), speaker_found=int(len(offs)), mean_offset=round(float(offs.mean()), 3) if len(offs) else None,
                              within_15pct=round(float(np.mean(offs <= 0.15)), 3) if len(offs) else None)
say("  ", R["on"]["independent"])

say("== ON 4: Telugu captions + music + mix")
words = [w for w in json.load(open(os.path.join(ROOT, "projects", BASE, "build", "words.json"))) if w["s"] < T - 1]
json.dump(words, open(os.path.join(b, "words.json"), "w"), ensure_ascii=False)
steps = [[PY, os.path.join(E, "captions.py"), TEST],
         ["ffmpeg", "-loglevel", "error", "-y", "-i", tracked, "-i", os.path.join(b, "captions.mov"), "-filter_complex", "[0:v][1:v]overlay=90:820:format=auto,format=yuv420p",
          "-t", str(T), "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-an", os.path.join(b, "edit.mp4")],
         ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(SS), "-i", SRC, "-t", str(T), "-map", "0:a:0", "-ac", "2", "-ar", "48000", os.path.join(b, "voice.wav")],
         [PY, os.path.join(E, "music.py"), TEST, str(T)],
         [PY, os.path.join(E, "mix.py"), TEST, os.path.join(b, "voice.wav"), str(T)]]
for s in steps:
    r, secs = sh(s)
    if r.returncode: say("   FAILED:", s[1] if s[0] != "ffmpeg" else "ffmpeg", r.stderr[-800:]); R["on"]["error"] = r.stderr[-800:]; break
else: say("   ok")

say("== ON 5: normal render + QA (Instagram)")
r, secs = sh([PY, os.path.join(E, "adapter.py"), "render", TEST, "--platform", "instagram"])
done = json.loads(r.stdout.strip().splitlines()[-1]); rep = json.load(open(done["outputs"][0]["qa_report"])) if done.get("outputs") else {}
R["on"]["render"] = dict(ok=done.get("ok"), qa_passed=done.get("qa_passed"), render_s=secs, frames=rep.get("frames"), lufs=rep.get("loudness_lufs"),
                         peak=rep.get("true_peak_db"), failed=[c["name"] for c in rep.get("checks", []) if not c["passed"]],
                         reel=done["outputs"][0]["path"] if done.get("outputs") else None, contact_sheet=rep.get("contact_sheet"))
say("  ", {k: v for k, v in R["on"]["render"].items() if k not in ("reel", "contact_sheet")})

# picture: source with the crop window (red) above the finished 1:1 frame, 6 moments
W0, H0 = st["source_size"]; cw, chh = st["crop"]; xs, ys = trk["crop_x"], trk.get("crop_y", [0] * len(trk["crop_x"])); fps = st["fps_in"]
sc = min(320 / W0, 180 / H0); tw_, th_ = int(W0 * sc), int(H0 * sc)
V = Image.new("RGB", (6 * 320, 180 + 320 + 8), (20, 20, 20)); tmp = os.path.join(OUT, "_v.png")
for k, i in enumerate(np.linspace(0, len(xs) - 1 - int(fps), 6).astype(int)):   # stop 1 s before the end of the edit
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{SS + i / fps:.3f}", "-i", SRC, "-frames:v", "1", "-vf", f"scale={tw_}:{th_}", tmp])
    a = Image.open(tmp).convert("RGB"); ImageDraw.Draw(a).rectangle((xs[i] * sc, ys[i] * sc, (xs[i] + cw) * sc - 1, (ys[i] + chh) * sc - 1), outline=(255, 40, 40), width=3)
    V.paste(a, (k * 320 + (320 - tw_) // 2, (180 - th_) // 2))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{i / fps:.3f}", "-i", os.path.join(b, "edit.mp4"), "-frames:v", "1", "-vf", "scale=320:320", tmp])
    V.paste(Image.open(tmp).convert("RGB"), (k * 320, 188))
V.save(VIZ, quality=88)
# one frame per shot with a 10% grid, for labelling a new clip by eye
shots_ = [0] + st["cuts"] + [len(xs)]; mids = [(a_ + b_) // 2 for a_, b_ in zip(shots_, shots_[1:]) if b_ - a_ > 5]
if len(mids) < 4: mids = sorted(set(int(x) for x in np.linspace(15, len(xs) - 15, 6)))      # few cuts: label several moments
mids = mids[:12]; gs = min(480 / W0, 480 / H0); gw, gh = int(W0 * gs), int(H0 * gs); cols = 4 if gh > gw else 2
G = Image.new("RGB", (cols * gw, ((len(mids) + cols - 1) // cols) * gh), (20, 20, 20))
for k, i in enumerate(mids):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{SS + i / fps:.3f}", "-i", SRC, "-frames:v", "1", "-vf", f"scale={gw}:{gh}", tmp])
    g = Image.open(tmp).convert("RGB"); dg = ImageDraw.Draw(g)
    for x in range(1, 10):
        dg.line((x * gw / 10, 0, x * gw / 10, gh), fill=(255, 230, 0), width=1); dg.line((0, x * gh / 10, gw, x * gh / 10), fill=(0, 230, 255), width=1)
    dg.rectangle((0, gh - 20, 140, gh), fill=(0, 0, 0)); dg.text((4, gh - 16), f"frame {i}", fill=(255, 255, 0)); G.paste(g, ((k % cols) * gw, (k // cols) * gh))
G.save(os.path.join(OUT, f"facetrack_shots_{NAME}.jpg"), quality=85); os.remove(tmp)
R["total_s"] = round(time.time() - t_all, 1)
json.dump(R, open(REPORT, "w"), ensure_ascii=False, indent=1)
tr = R["on"].get("tracking", {}).get("tracked", {}); ind = R["on"].get("independent", {})
gt = R["on"].get("ground_truth")
R["on"]["accuracy_ok"] = bool(tr.get("within_15pct") is not None and tr["within_15pct"] >= 0.85 and tr.get("out_of_frame") == 0
                              and (gt is None or (gt["within_15pct"] >= 0.85 and gt["out_of_frame"] == 0 and gt["wrong_person_frames"] <= 0.05 * gt["frames"])))
if gt is None: say("NOTE: no labels for this clip yet - accuracy is the tracker's own measure only; labels needed before it counts")
json.dump(R, open(REPORT, "w"), ensure_ascii=False, indent=1)
say("accuracy rule (real speaker within ±15% of centre in >=85% of frames, never out of frame):", "PASS" if R["on"]["accuracy_ok"] else "FAIL")
ok = refused and R["off"]["baseline"]["qa_passed"] and R["on"].get("render", {}).get("qa_passed") and R["on"]["accuracy_ok"] and gt is not None
say(f"\nreport -> {os.path.relpath(REPORT, ROOT)} | picture -> {os.path.relpath(VIZ, ROOT)}")
say("FACE TRACKING TEST", f"({NAME})", "PASSED" if ok else "NEEDS REVIEW")
