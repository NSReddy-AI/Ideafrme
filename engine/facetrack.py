"""Optional face tracking (OFF by default): reframe a wide video to 1:1 or 9:16 keeping the speaker centred.
MediaPipe only (Apache-2.0): Face Detector, with the Pose Landmarker as a fallback when the face is too small.
Usage:
  python facetrack.py <in.mp4> <out.mp4> [--aspect 1:1|9:16] [--size 1080] [--project P [--force]]
                      [--ss S] [--t T] [--every N] [--audio] [--track track.json] [--backend mediapipe|matte]
  --project P : obey project.json "face_tracking" (false by default -> stops with FACE_TRACKING_OFF unless --force)
  --backend matte : development-only test detector (never used by the app)
Writes <out> (30 fps) and a track file (per-frame crop window, detections, scene cuts, coverage stats).
How it moves: detects every N frames, finds scene cuts on every frame, holds still inside a dead-zone,
eases toward the speaker with a speed limit, and jumps instantly at a cut (no slow pan across a cut)."""
import os, sys, re, json, time, argparse, subprocess
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ENGINE, probe, progress, fail, emit, job, load

FACE_MODEL = os.path.join(ENGINE, "models", "blaze_face_short_range.tflite")
POSE_MODEL = os.path.join(ENGINE, "models", "pose_landmarker_lite.task")
LMK_MODEL = os.path.join(ENGINE, "models", "face_landmarker.task")   # optional: mouth movement -> who is speaking

class MPDetector:
    """MediaPipe Tasks: Face Detector (faces), Face Landmarker (mouth movement, optional model), Pose Landmarker
    (hand-at-mouth = holding a microphone; head position when no face is found)."""
    def __init__(self, fps):
        try:
            import mediapipe as mp
            from mediapipe.tasks.python import BaseOptions, vision
        except Exception as e: fail("MEDIAPIPE_MISSING", f"MediaPipe is not installed in this Python: {e}")
        for m in (FACE_MODEL, POSE_MODEL):
            if not os.path.exists(m): fail("MODEL_MISSING", f"missing model file {m} (see SETUP: face tracking models)")
        self.mp, self.fps = mp, fps
        VM = vision.RunningMode.VIDEO
        self.face = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=FACE_MODEL), running_mode=VM, min_detection_confidence=0.5))
        self.pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=POSE_MODEL), running_mode=VM, num_poses=4, min_pose_detection_confidence=0.5))
        self.lmk = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=LMK_MODEL), running_mode=VM, num_faces=5, min_face_detection_confidence=0.5,
            output_face_blendshapes=True)) if os.path.exists(LMK_MODEL) else None
    def __call__(self, rgb, idx):
        """Every face (detector = best coverage), with mouth movement (landmarker) and a 'hand at the mouth' cue (pose wrist
        near the nose: holding a microphone) attached when found. Pose heads stand in when no face is found."""
        h, w = rgb.shape[:2]; ts = int(idx * 1000 / self.fps)
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        out = []
        for d in self.face.detect_for_video(img, ts).detections:
            b = d.bounding_box; s = d.categories[0].score if d.categories else 0.5
            out.append(dict(cx=(b.origin_x + b.width / 2) / w, cy=(b.origin_y + b.height / 2) / h, size=b.width / w, score=round(float(s), 3), src="face"))
        if self.lmk:
            r = self.lmk.detect_for_video(img, ts)
            for k, lms in enumerate(r.face_landmarks):
                xs = [p.x for p in lms]; ys = [p.y for p in lms]; cx, cy, sz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs)
                bs = r.face_blendshapes[k] if r.face_blendshapes and k < len(r.face_blendshapes) else []
                jaw = next((float(c.score) for c in bs if c.category_name == "jawOpen"), None)
                near = [o for o in out if abs(o["cx"] - cx) < max(0.04, o["size"] * 0.6) and abs(o["cy"] - cy) < 0.15]
                if near: near[0]["jaw"] = jaw
                else: out.append(dict(cx=cx, cy=cy, size=sz, score=0.6, src="face", jaw=jaw))
        poses = self.pose.detect_for_video(img, ts).pose_landmarks
        for lm in poses:
            nose, le, re, ls, rs, lw, rw = lm[0], lm[7], lm[8], lm[11], lm[12], lm[15], lm[16]
            if getattr(nose, "visibility", 1) < 0.3: continue
            head = max(abs(le.x - re.x) * 1.6, abs(ls.x - rs.x) * 0.45, 0.02)
            mic = any(getattr(wr, "visibility", 1) > 0.3 and abs(wr.x - nose.x) < head * 1.2 and abs(wr.y - nose.y) * h / w < head * 1.6 for wr in (lw, rw))
            near = [o for o in out if abs(o["cx"] - nose.x) < max(0.05, o["size"] * 0.8)]
            if near: near[0]["mic"] = near[0].get("mic", False) or mic
            elif not any(o["src"] == "face" for o in out) or mic:
                out.append(dict(cx=nose.x, cy=nose.y, size=head, score=round(float(getattr(nose, "visibility", 0.5)), 3), src="pose", mic=mic))
        for o in out:
            o["edge"] = o["cx"] - o["size"] / 2 < 0.01 or o["cx"] + o["size"] / 2 > 0.99
            for k in ("cx", "cy", "size"): o[k] = round(float(o[k]), 4)
        return out

class MatteDetector:
    """Development-only stand-in (the RVM person matte already in the engine) so the movement logic can be tested
    where MediaPipe is not installed. Head = centre of the top part of the person silhouette."""
    def __init__(self, fps):
        import onnxruntime as ort
        self.s = ort.InferenceSession(os.path.join(ENGINE, "models", "rvm.onnx"))
    def __call__(self, rgb, idx):
        h, w = rgb.shape[:2]; z = [np.zeros([1, 1, 1, 1], np.float32)] * 4
        x = cv2.resize(rgb, (w // 2, h // 2)).astype(np.float32).transpose(2, 0, 1)[None] / 255
        a = self.s.run(None, {"src": x, "r1i": z[0], "r2i": z[1], "r3i": z[2], "r4i": z[3], "downsample_ratio": np.array([0.5], np.float32)})[1][0, 0]
        m = a > 0.5; rows = np.where(m.any(1))[0]
        if m.mean() < 0.01 or not len(rows): return []
        top = rows[0]; band = m[top:top + max(4, (rows[-1] - top) // 5)]
        cols = np.where(band.any(0))[0]; cx = (cols[0] + cols[-1]) / 2 / m.shape[1]
        return [dict(cx=float(cx), cy=float(top / m.shape[0] + 0.08), size=float((cols[-1] - cols[0]) / m.shape[1]), score=0.5, src="matte")]

def frames(src, w, h, ss=None, t=None):
    cmd = ["ffmpeg", "-loglevel", "error"] + (["-ss", str(ss)] if ss else []) + ["-i", src] + (["-t", str(t)] if t else []) + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE); n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.wait()

def display_size(src, w, h):
    """Phones store portrait video as landscape + a rotation flag; ffmpeg turns it upright when decoding."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", src], capture_output=True, text=True).stdout
    m = re.search(r"(?:TAG:rotate|rotation)=(-?\d+)", out)
    return (h, w) if m and abs(int(m.group(1))) % 180 == 90 else (w, h)

def choose_speaker(raw, cuts, n, info=None, axis="x"):
    """Per shot: link detections into person tracks by position, score every person, follow the best one.
    Score = present x (centre of shot 0.35 + size 0.25 + mouth movement 0.2 + hand at mouth 0.2) x (half if cut by the
    frame edge). Broadcast cameras keep the speaker near the middle; the cues break ties.
    -> {frame: speaker position along the tracking axis (cx for a wide source, cy for a tall one) or None}"""
    shots = [0] + sorted(c for c in cuts if 0 < c < n) + [n]; dets = {}
    for a, b in zip(shots, shots[1:]):
        idx = sorted(i for i in raw if a <= i < b); tracks = []
        for i in idx:
            for d in sorted(raw[i], key=lambda d: -d["size"]):
                best = min(tracks, key=lambda t: abs(t["cx"][-1] - d["cx"]), default=None)
                if best is not None and abs(best["cx"][-1] - d["cx"]) < 0.08 and best["f"][-1] != i: t = best
                else: t = dict(f=[], cx=[], cy=[], size=[], jaw=[], mic=[], edge=[]); tracks.append(t)
                t["f"].append(i); t["cx"].append(d["cx"]); t["cy"].append(d.get("cy", 0.5)); t["size"].append(d["size"]); t["jaw"].append(d.get("jaw"))
                t["mic"].append(bool(d.get("mic"))); t["edge"].append(bool(d.get("edge")))
        for i in idx: dets[i] = None
        if not tracks: continue
        def talk(t):
            j = [x for x in t["jaw"] if x is not None]
            return float(np.std(j)) + float(np.mean(np.abs(np.diff(j)))) if len(j) >= 3 else 0.0
        big = max(np.mean(t["size"]) for t in tracks); tk = max(talk(t) for t in tracks) or 1.0
        def score(t):
            pres = len(t["f"]) / max(1, len(idx)); centre = 1 - min(1, abs(float(np.median(t["cx"])) - 0.5) / 0.5)
            s = pres * (0.35 * centre + 0.25 * np.mean(t["size"]) / big + 0.2 * talk(t) / tk + 0.2 * np.mean(t["mic"]))
            return float(s * (1 - 0.5 * np.mean(t["edge"])))
        ranked = sorted(tracks, key=score, reverse=True); sp = ranked[0]
        for f, v in zip(sp["f"], sp["cx" if axis == "x" else "cy"]): dets[f] = v
        if info is not None:
            margin = (score(sp) - score(ranked[1])) / max(1e-6, score(sp)) if len(ranked) > 1 else 1.0
            info.append(dict(shot=[a, b], people=len(tracks), speaker_cx=round(float(np.median(sp["cx"])), 3), score=round(score(sp), 3),
                             margin=round(margin, 3), mouth=round(talk(sp), 3), hand_at_mouth=round(float(np.mean(sp["mic"])), 2), unsure=margin < 0.15))
    return dets

def plan(dets, cuts, N, crop_w, W, every, fps, dead=0.06, ease=0.12, vmax=0.9):
    """Crop start (pixels along the tracking axis) for every frame. dets: {frame: target position (0-1) or None}."""
    # target per frame: hold the last detection inside a shot, back-fill the shot start with its first detection
    tgt = np.full(N, np.nan); cut_set = set(cuts); last = np.nan
    for i in range(N):
        if i in cut_set: last = np.nan
        if i in dets and dets[i] is not None: last = dets[i]
        tgt[i] = last
    shots = [0] + sorted(c for c in cuts if 0 < c < N) + [N]
    for a, b in zip(shots, shots[1:]):
        seg = tgt[a:b]; ok = ~np.isnan(seg)
        if ok.any(): first = seg[ok][0]; seg[:np.argmax(ok)] = first
        else: seg[:] = 0.5                                          # no one found in this shot -> centre crop
        tgt[a:b] = seg
    half = crop_w / 2 / W; cam = np.zeros(N); step = vmax * crop_w / W / fps   # max pan per frame (fraction of width)
    for a, b in zip(shots, shots[1:]):
        c = min(max(tgt[a], half), 1 - half)                         # a cut starts already on the speaker
        for i in range(a, b):
            want = min(max(tgt[i], half), 1 - half); d = want - c
            if abs(d) > dead * crop_w / W: c += float(np.clip(d * ease, -step, step))
            cam[i] = c
    return np.clip(np.round(cam * W - crop_w / 2), 0, W - crop_w).astype(int), tgt

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--aspect", default="1:1"); ap.add_argument("--size", type=int, default=1080)
    ap.add_argument("--project"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--ss", type=float); ap.add_argument("--t", type=float); ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--audio", action="store_true"); ap.add_argument("--track"); ap.add_argument("--backend", default=os.environ.get("RS_FACE_BACKEND", "mediapipe"))
    A = ap.parse_args(); t0 = time.time()
    if A.project:
        j, _ = job(A.project)
        if not j.get("face_tracking", False) and not A.force: fail("FACE_TRACKING_OFF", "face tracking is off for this project (project.json face_tracking: false)")
    P = probe(A.src); W, H = display_size(A.src, P["w"], P["h"])
    rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", A.src],
                          capture_output=True, text=True).stdout
    m = re.search(r"(\d+)/(\d+)", rate)          # some ffprobe builds print extra lines; take the first "num/den"
    fps = int(m.group(1)) / int(m.group(2)) if m and int(m.group(2)) else 30.0
    dur = A.t or (P["duration"] - (A.ss or 0)); NT = max(1, int(dur * fps))
    aw, ah = map(int, A.aspect.split(":")); crop_w = min(W, int(round(H * aw / ah))); crop_h = min(H, int(round(crop_w * ah / aw)))
    crop_w -= crop_w % 2; crop_h -= crop_h % 2; y0, x0 = (H - crop_h) // 2, (W - crop_w) // 2
    axis = "x" if (W - crop_w) >= (H - crop_h) else "y"          # wide source: follow left/right; tall (phone) source: up/down
    L, C = (W, crop_w) if axis == "x" else (H, crop_h)
    aim = 0.5 if axis == "x" else 0.42                              # tall source: face a little above the middle (headroom)
    ow, oh = A.size, int(round(A.size * ah / aw)); ow -= ow % 2; oh -= oh % 2
    det = (MatteDetector if A.backend == "matte" else MPDetector)(fps)
    # pass 1: detections every N frames, scene cuts on every frame
    dets, raw, cuts, prev, n = {}, {}, [], None, 0; last_cx = None
    for i, f in enumerate(frames(A.src, W, H, A.ss, A.t)):
        small = cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2HSV), (64, 36), interpolation=cv2.INTER_AREA)
        hist = cv2.calcHist([small], [0, 1], None, [16, 8], [0, 180, 0, 256]); cv2.normalize(hist, hist)
        gray = cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32)
        if prev is not None and (cv2.compareHist(prev[0], hist, cv2.HISTCMP_CORREL) < 0.5 or float(np.abs(gray - prev[1]).mean()) > 18):
            cuts.append(i); last_cx = None          # scene cut: brightness/colour jump between two frames
        prev = (hist, gray)
        if i % A.every == 0 or (cuts and cuts[-1] == i): raw[i] = det(f, i)
        n = i + 1
        if i % 30 == 0: progress(i / NT * 45, "finding the speaker")
    if n == 0: fail("NO_FRAMES", f"could not read frames from {A.src}")
    shots_info = []; dets = choose_speaker(raw, cuts, n, shots_info, axis)
    shift = (0.5 - aim) * C / L                                     # place the face at `aim` inside the crop
    xs, tgt = plan({k: (None if v is None else v + shift) for k, v in dets.items()}, cuts, n, C, L, A.every, fps)
    t1 = time.time()
    # pass 2: crop + scale + encode at 30 fps
    enc = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}", "-r", f"{fps}", "-i", "-"]
    if A.audio: enc += (["-ss", str(A.ss)] if A.ss else []) + ["-i", A.src] + (["-t", str(A.t)] if A.t else []) + ["-map", "0:v", "-map", "1:a?", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    enc += ["-vf", "fps=30", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", A.out]
    e = subprocess.Popen(enc, stdin=subprocess.PIPE)
    for i, f in enumerate(frames(A.src, W, H, A.ss, A.t)):
        if i >= n: break
        crop = f[y0:y0 + crop_h, xs[i]:xs[i] + crop_w] if axis == "x" else f[xs[i]:xs[i] + crop_h, x0:x0 + crop_w]
        e.stdin.write(cv2.resize(crop, (ow, oh), interpolation=cv2.INTER_LANCZOS4 if ow > crop_w else cv2.INTER_AREA).tobytes())
        if i % 30 == 0: progress(45 + i / n * 54, "reframing")
    e.stdin.close(); e.wait()
    if e.returncode: fail("ENCODE_FAILED", "facetrack: ffmpeg could not write the output")
    # accuracy from the detections: where the speaker lands in the output (0.5 = centre), tracked vs a plain centre crop
    pos_t, pos_c, srcs = [], [], {}
    for i, c in raw.items():
        if dets.get(i) is None: continue
        fx = dets[i] * L; pos_t.append((fx - xs[i]) / C); pos_c.append((fx - (L - C) / 2) / C)
        s = next((d["src"] for d in c if abs(d["cx" if axis == "x" else "cy"] - dets[i]) < 1e-9), "?"); srcs[s] = srcs.get(s, 0) + 1
    def acc(p):
        p = np.array(p); return dict(mean_offset=round(float(np.mean(np.abs(p - aim))), 3) if len(p) else None,
                                     within_15pct=round(float(np.mean(np.abs(p - aim) <= 0.15)), 3) if len(p) else None,
                                     out_of_frame=int(np.sum((p < 0) | (p > 1))))
    stats = dict(src=A.src, out=A.out, backend=A.backend, aspect=A.aspect, source_size=[W, H], axis=axis, aim=aim, fps_in=fps, frames=n, crop=[crop_w, crop_h],
                 sampled=len(raw), found=sum(v is not None for v in dets.values()), coverage=round(sum(v is not None for v in dets.values()) / max(1, len(raw)), 3),
                 by=srcs, cuts=cuts, shots=shots_info, unsure_shots=sum(x["unsure"] for x in shots_info), tracked=acc(pos_t), centre_crop=acc(pos_c),
                 time_detect_s=round(t1 - t0, 1), time_render_s=round(time.time() - t1, 1))
    track = A.track or os.path.splitext(A.out)[0] + "_track.json"
    with open(track, "w") as f: json.dump(dict(stats=stats, raw={str(k): v for k, v in raw.items()}, axis=axis, crop_pos=xs.tolist(),
                                     crop_x=xs.tolist() if axis == "x" else [x0] * n, crop_y=[y0] * n if axis == "x" else xs.tolist(), target=[None if np.isnan(v) else round(float(v), 4) for v in tgt]), f)
    progress(100); emit("output", path=A.out, track=track)
    print("facetrack ->", A.out, json.dumps({k: stats[k] for k in ("frames", "coverage", "by", "tracked", "centre_crop", "time_detect_s", "time_render_s")}))

if __name__ == "__main__":
    main()
