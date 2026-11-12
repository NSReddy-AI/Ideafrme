"""Voice cleaning in the mix: DeepFilterNet vs the old basic filter, on 41 s of 'What jagan said' (with music + effects).
Run: ~/.venvs/reelstudio/bin/python tests/test_mix.py
Checks loudness -14 +-0.5 LUFS and true peak <= -1.0 dB AFTER AAC encoding (as in a real reel), and writes two 15 s
samples to listen to: tests/out/mix_basic_15s.wav and tests/out/mix_deepfilter_15s.wav."""
import os, sys, json, re, shutil, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "tests", "out"); os.makedirs(OUT, exist_ok=True)
E = os.path.join(ROOT, "engine"); PY = sys.executable; say = lambda *a: print(*a, flush=True)
REF = json.load(open(os.path.join(ROOT, "tests", "asr_reference_what_jagan_said.json")))
src = os.path.normpath(os.path.join(ROOT, REF["source"])); S = REF["segments_in_order"]
TEST = "zz_mix_test"; d = os.path.join(ROOT, "projects", TEST); b = os.path.join(d, "build"); os.makedirs(b, exist_ok=True)
pj = json.load(open(os.path.join(ROOT, "projects", "2026-11-03_reel_002_development", "project.json"))); pj.update(status="test", history=[])
voice = os.path.join(b, "voice.wav")
parts = "".join(f"[0:a]atrim={a}:{c},asetpts=PTS-STARTPTS[a{i}];" for i, (a, c) in enumerate(S))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", parts + "".join(f"[a{i}]" for i in range(len(S))) + f"concat=n={len(S)}:v=0:a=1[o]",
                "-map", "[o]", "-ac", "2", "-ar", "48000", voice], check=True)
D = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice], capture_output=True, text=True).stdout)
json.dump(pj, open(os.path.join(d, "project.json"), "w"), ensure_ascii=False, indent=1)
subprocess.run([PY, os.path.join(E, "music.py"), TEST, str(D)], check=True, capture_output=True)
def meas(f):
    l = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", l)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+)", l)[-1])
R = {}
for mode in ("basic", "deepfilter"):
    pj["voice_clean"] = mode; json.dump(pj, open(os.path.join(d, "project.json"), "w"), ensure_ascii=False, indent=1)
    out = os.path.join(OUT, f"mix_{mode}.wav")
    r = subprocess.run([PY, os.path.join(E, "mix.py"), TEST, voice, str(D), out], capture_output=True, text=True)
    used = (re.findall(r"voice cleaning: (\w+)", r.stdout) or ["?"])[-1]
    if r.returncode: say(f"{mode}: FAILED", r.stderr[-400:]); R[mode] = dict(error=r.stderr[-400:]); continue
    aac = out.replace(".wav", ".m4a"); subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", aac], check=True)
    (i1, p1), (i2, p2) = meas(out), meas(aac)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, "-t", "15", os.path.join(OUT, f"mix_{mode}_15s.wav")], check=True)
    R[mode] = dict(used=used, lufs=i1, true_peak=p1, lufs_after_aac=i2, true_peak_after_aac=p2, passed=abs(i2 + 14) <= 0.5 and p2 <= -1.0)
    say(f"{mode:10} used={used:10} LUFS {i1} / after AAC {i2} | true peak {p1} / after AAC {p2} dB -> {'PASS' if R[mode]['passed'] else 'FAIL'}")
json.dump(R, open(os.path.join(OUT, "mix_report.json"), "w"), indent=1)
shutil.rmtree(d, ignore_errors=True)
ok = all(v.get("passed") for v in R.values()) and R.get("deepfilter", {}).get("used") == "deepfilter"
say("\nMIX TEST", "PASSED" if ok else "NEEDS REVIEW", "| listen: tests/out/mix_basic_15s.wav vs tests/out/mix_deepfilter_15s.wav")
