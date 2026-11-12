"""Motion graphics without GSAP: rebuilds reel_002's graphics with engine/motion.py (Web Animations API, local fonts),
renders them with HyperFrames, and compares them with the original GSAP render (build/overlay.webm).
Run (after tests/setup_motion.sh has fetched the two fonts):  ~/.venvs/reelstudio/bin/python tests/test_motion.py
Writes tests/out/motion_report.json and tests/out/motion_compare.jpg (GSAP left, new right, 16 moments)."""
import os, sys, json, re, time, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "tests", "out"); os.makedirs(OUT, exist_ok=True)
P = os.path.join(ROOT, "projects", "2026-11-03_reel_002_development"); HF = os.path.join(P, "build", "hf_waapi")
OLD, NEW = os.path.join(P, "build", "overlay.webm"), os.path.join(P, "build", "overlay_waapi.webm")
R = {}; say = lambda *a: print(*a, flush=True)
def run(cmd, cwd=None): t = time.time(); r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"); return r, round(time.time() - t, 1)

say("== 1. fonts in engine/fonts")
need = ["NotoSansTelugu-Black.ttf", "Anton-Regular.ttf", "SixCaps.ttf"]
R["fonts"] = {f: os.path.exists(os.path.join(ROOT, "engine", "fonts", f)) for f in need}; say("  ", R["fonts"])
say("== 2. build the composition (no GSAP)")
r, _ = run([sys.executable, os.path.join(P, "source", "gen_overlay_waapi.py")]); say("  ", (r.stdout or r.stderr).strip()[-300:])
html = open(os.path.join(HF, "index.html"), encoding="utf-8").read()
R["internet_references"] = sorted(set(re.findall(r"https?://[^\s\"')]+", html))); R["gsap_used"] = "gsap" in html.lower()
say("   internet references:", R["internet_references"] or "none", "| GSAP:", R["gsap_used"])
say("== 3. HyperFrames lint")
r, _ = run(["npx", "--no-install", "hyperframes", "lint"], cwd=HF); R["lint"] = dict(code=r.returncode, out=(r.stdout + r.stderr).strip()[-1200:]); say("  ", R["lint"]["out"][-600:] or "ok")
say("== 4. HyperFrames render (transparent webm)")
r, secs = run(["npx", "--no-install", "hyperframes", "render", "--format", "webm", "--output", NEW], cwd=HF)
R["render"] = dict(code=r.returncode, seconds=secs, tail=(r.stdout + r.stderr).strip()[-600:]); say(f"   exit {r.returncode}, {secs} s")
if r.returncode or not os.path.exists(NEW):
    say(R["render"]["tail"]); json.dump(R, open(os.path.join(OUT, "motion_report.json"), "w"), ensure_ascii=False, indent=1); sys.exit(1)
def info(f):
    j = json.loads(run(["ffprobe", "-v", "error", "-count_packets", "-show_entries", "format=duration:stream=width,height,codec_name,nb_read_packets,r_frame_rate:stream_tags=alpha_mode", "-of", "json", f])[0].stdout)
    s = j["streams"][0]; return dict(duration=round(float(j["format"]["duration"]), 3), size=f"{s['width']}x{s['height']}", fps=s["r_frame_rate"], frames=int(s.get("nb_read_packets", 0)), codec=s["codec_name"], alpha=s.get("tags", {}).get("alpha_mode"))
R["old"], R["new"] = info(OLD), info(NEW); say("   GSAP:", R["old"]); say("   new :", R["new"])
say("== 5. compare 16 moments")
ts = [1.0, 4.5, 7.6, 10.6, 14.6, 18.0, 22.3, 27.5, 34.5, 41.5, 42.6, 46.9, 48.0, 50.0, 53.3, 53.9]
S = Image.new("RGB", (8 * 270, 4 * 270), (40, 40, 40)); diffs = []
for k, t in enumerate(ts):
    fr = []
    for j, src in enumerate((OLD, NEW)):
        f = os.path.join(OUT, f"_m{j}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx-vp9", "-ss", str(t), "-i", src, "-frames:v", "1", "-pix_fmt", "rgba", f])
        im = Image.open(f).convert("RGBA"); fr.append(np.array(im).astype(float))
        bg = Image.new("RGBA", (270, 270), (70, 110, 90, 255)); bg.alpha_composite(im.resize((270, 270)))
        ImageDraw.Draw(bg).text((4, 4), f"{'GSAP' if j == 0 else 'NEW'} {t}s", fill=(255, 255, 0)); S.paste(bg.convert("RGB"), (((2 * k + j) % 8) * 270, ((2 * k + j) // 8) * 270))
    diffs.append(round(float(np.abs(fr[0][..., 3] - fr[1][..., 3]).mean()), 2))
S.save(os.path.join(OUT, "motion_compare.jpg"), quality=85); R["alpha_diff_by_time"] = dict(zip(map(str, ts), diffs))
say("   coverage difference (0 = same):", R["alpha_diff_by_time"])
ok = all(R["fonts"].values()) and not R["internet_references"] and not R["gsap_used"] and R["render"]["code"] == 0 and abs(R["old"]["duration"] - R["new"]["duration"]) < 0.1
json.dump(R, open(os.path.join(OUT, "motion_report.json"), "w"), ensure_ascii=False, indent=1)
say("\nMOTION TEST", "PASSED (now check the picture)" if ok else "NEEDS REVIEW", "-> tests/out/motion_report.json, tests/out/motion_compare.jpg")
