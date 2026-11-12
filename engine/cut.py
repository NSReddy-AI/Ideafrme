"""Cut a source video to the kept segments (in order), 30 fps, PCM audio.
Usage: python cut.py <job>     reads build/keep.json = [[start,end],...] (seconds in the source)
Source = job.json "video". Segments may be re-ordered (e.g. hook first)."""
import sys, os
from common import *
j, c = job(sys.argv[1]); b = os.path.join(j["_dir"], "build")
keep = load(os.path.join(b, "keep.json")); src = os.path.join(j["_dir"], j["video"])
parts = "".join(f"[0:v]trim={a}:{e},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={e-a-0.012:.3f}:d=0.012[a{i}];" for i, (a, e) in enumerate(keep))
cat = "".join(f"[v{i}][a{i}]" for i in range(len(keep)))
if not os.path.exists(src): fail("FILE_NOT_FOUND", f"source video not found: {src}")
run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", f"{parts}{cat}concat=n={len(keep)}:v=1:a=1[v][a];[v]fps=30[vo]",
     "-map", "[vo]", "-map", "[a]", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "pcm_s16le", f"{b}/cut.mov"], total_s=sum(e-a for a, e in keep))
print("cut ->", f"{b}/cut.mov", round(sum(e-a for a, e in keep), 2), "s")
