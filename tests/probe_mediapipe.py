"""Read-only check of the MediaPipe install (changes nothing). Run with Reel Studio's Python:
  ~/.venvs/reelstudio/bin/python tests/probe_mediapipe.py"""
import os, sys, glob, json, subprocess, tempfile, importlib.metadata as md
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = {"python": sys.version.split()[0]}
for p in ("numpy", "opencv-python", "opencv-contrib-python", "mediapipe", "pillow", "onnxruntime", "scipy"):
    try: R[p] = md.version(p)
    except md.PackageNotFoundError: R[p] = None
import cv2, numpy as np
R["cv2_version"] = cv2.__version__; R["cv2_file"] = cv2.__file__
R["cv2_contrib"] = hasattr(cv2, "xfeatures2d") or hasattr(cv2, "ximgproc")
import mediapipe as mp
R["mp_dir"] = os.path.dirname(mp.__file__)
R["mp_has_solutions"] = hasattr(mp, "solutions")
R["mp_has_tasks"] = hasattr(mp, "tasks")
R["mp_top_level"] = sorted(n for n in dir(mp) if not n.startswith("_"))[:40]
R["tflite_in_package"] = sorted(os.path.relpath(f, R["mp_dir"]) for f in glob.glob(os.path.join(R["mp_dir"], "**", "*face*.tflite"), recursive=True))[:20]
# one real frame from reel_002's edit (the speaker at 5 s)
edit = os.path.join(ROOT, "projects", "2026-11-03_reel_002_development", "build", "edit.mp4")
png = os.path.join(tempfile.mkdtemp(), "f.png")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "5", "-i", edit, "-frames:v", "1", png])
img = cv2.cvtColor(cv2.imread(png), cv2.COLOR_BGR2RGB); R["frame"] = list(img.shape)
if R["mp_has_solutions"]:
    try:
        with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5) as fd:
            res = fd.process(img)
        R["solutions_faces"] = [dict(score=round(d.score[0], 3), box=[round(v, 3) for v in (d.location_data.relative_bounding_box.xmin, d.location_data.relative_bounding_box.ymin,
                                d.location_data.relative_bounding_box.width, d.location_data.relative_bounding_box.height)]) for d in (res.detections or [])]
    except Exception as e: R["solutions_error"] = f"{type(e).__name__}: {e}"
try:
    from mediapipe.tasks.python import vision
    R["tasks_vision_FaceDetector"] = hasattr(vision, "FaceDetector")
except Exception as e: R["tasks_error"] = f"{type(e).__name__}: {e}"
print(json.dumps(R, indent=1))
