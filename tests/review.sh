#!/bin/bash
# Final review of Reel Studio_dev against the Milestone 2 acceptance criteria. Read-only for the original and the backup.
cd "$(dirname "$0")/.."; DEV="$PWD"; PY="$HOME/.venvs/reelstudio/bin/python"; TOP="$(dirname "$DEV")"
line() { echo; echo "== $1"; }
line "1. Original Reel Studio and backup untouched"
( cd "$TOP/Reel Studio" && shasum -a 256 -c "$TOP/Reel Studio_backup_2026-11-09/CHECKSUMS.sha256" --quiet && echo "original: unchanged (matches backup checksums)" ) || echo "original: CHANGED"
( cd "$TOP/Reel Studio_backup_2026-11-09" && shasum -a 256 -c CHECKSUMS.sha256 --quiet && echo "backup: intact" ) || echo "backup: CHANGED"
line "2. Engine checkpoint (environment, self-test, locked baseline, all platforms, project.json)"
bash checkpoint.sh 2>/dev/null | grep -v "^== " 
line "3. Face tracking, all labelled clips"
bash tests/run_facetrack_suite.sh 2>/dev/null
line "4. Face tracking is off by default"
"$PY" - <<'P'
import sys, os, json, shutil; sys.path.insert(0, "engine"); import rs
d = rs.new("jagan_for_andhra", "instagram", "news_speech", "_review_default"); v = json.load(open(os.path.join(d, "project.json"))).get("face_tracking")
print("new project face_tracking =", v, "->", "OK (off)" if v is False else "PROBLEM"); shutil.rmtree(d, ignore_errors=True)
P
line "5. 4K upscaler (ported) on a small test image"
"$PY" - <<'P'
import subprocess, sys, time, os
from PIL import Image
src = "projects/2026-11-03_reel_002_development/inputs/bg_aerial.png"; a, b = "tests/out/_up_in.png", "tests/out/_up_out.png"
Image.open(src).convert("RGB").crop((0, 0, 48, 48)).save(a); t = time.time()
r = subprocess.run([sys.executable, "engine/esrgan_np.py", a, b, "48"], capture_output=True, text=True)
ok = r.returncode == 0 and os.path.exists(b) and Image.open(b).size == (192, 192)
print("upscale 48x48 -> 192x192:", "OK" if ok else "FAILED " + r.stderr[-300:], f"({time.time() - t:.1f} s)")
P
line "6. HyperFrames available (no download)"
( npx --no-install hyperframes --version 2>/dev/null && echo "hyperframes: OK" ) || echo "hyperframes: not found without downloading"
line "7. Leftover temporary files"
find . -name "*.tmp" -o -name "*.new" | sed 's#^#  #'; echo "  (end of list)"
line "8. Size of test material in the dev copy (not part of a release)"
du -sh exports projects/zz_* tests/out tests/clips 2>/dev/null | sed 's#^#  #'
echo; echo "REVIEW DONE"
