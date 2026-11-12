"""Checks a finished reel and gives a PASS / FAIL result the app can read.
Usage: python qa.py <reel.mp4> [--platform instagram] [--layout build/layout.json] [--baseline tests/baseline_reel_002.json] [--json out.json]
Writes <reel>_qa.json (pass/fail + every check) and <reel>_qa.jpg (contact sheet). Exit code: 0 = pass, 2 = fail.
Rules: platform size and 30 fps, H.264 + AAC, loudness = platform target ±0.5 LUFS, true peak <= -1.0 dB, no black frames,
safe-area issues (from frame.py's layout.json; failures only when the brand enforces safe areas), optional locked baseline.
M4 B2: layouts with "elements" (frame.py) -> must_stay_visible (enforced brands) or warnings (warn-mode template) + advisory strict-zone warnings.
M4 B1, only for narration projects (layout.json has "narration"): ai_disclosure (AI narration -> the Telugu disclosure is readable
on sampled frames and inside the safe area; recorded / none -> no disclosure) and clipping (no full-scale audio samples)."""
import sys, os, re, subprocess, json, argparse
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, load, emit, tmpdir

ap = argparse.ArgumentParser(); ap.add_argument("reel"); ap.add_argument("extra", nargs="*")
ap.add_argument("--platform"); ap.add_argument("--layout"); ap.add_argument("--baseline"); ap.add_argument("--json")
A = ap.parse_args(); F = A.reel
def sh(cmd): return subprocess.run(cmd, capture_output=True, text=True)
if not os.path.exists(F):
    emit("error", step="qa", code="FILE_NOT_FOUND", message=f"reel not found: {F}"); sys.exit(f"reel not found: {F}")
pf_name = A.platform or next((p for p in ("instagram", "youtube", "facebook") if f"_{p}" in os.path.basename(F)), "instagram")
PF = load(os.path.join(ROOT, "platforms", pf_name + ".json"))
p = json.loads(sh(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
                   "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_packets", "-of", "json", F]).stdout)
v = next(s for s in p["streams"] if s["codec_type"] == "video"); au = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
D = float(p["format"]["duration"]); size = int(p["format"]["size"]); frames = int(v.get("nb_read_packets", 0))
bl = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", sh(["ffmpeg", "-hide_banner", "-nostats", "-i", F, "-vf", "blackdetect=d=0.04:pix_th=0.08", "-an", "-f", "null", "-"]).stderr)
ld = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", F, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"]).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)[-1]); TP = float(re.findall(r"Peak:\s+(-?[\d.]+)", ld)[-1])
target = PF.get("loudness_lufs", -14)
checks, warnings = [], []
def check(name, ok, value, rule): checks.append(dict(name=name, pass_=bool(ok), value=value, rule=rule))
check("size", (v["width"], v["height"]) == (PF["width"], PF["height"]), f"{v['width']}x{v['height']}", f"{PF['width']}x{PF['height']}")
check("fps", v["r_frame_rate"] == f"{PF['fps']}/1", v["r_frame_rate"], f"{PF['fps']}/1")
check("codecs", v["codec_name"] == "h264" and au is not None and au["codec_name"] == "aac", f"{v['codec_name']} + {au['codec_name'] if au else 'no audio'}", "h264 + aac")
check("loudness", abs(I-target) <= 0.5, I, f"{target} ±0.5 LUFS")
check("true_peak", TP <= -1.0, TP, "<= -1.0 dB")
check("black_frames", not bl, [list(map(float, x)) for x in bl], "none")
mx = PF.get("max_seconds")
if mx and D > mx: warnings.append(f"length {D:.1f}s is over the {PF['name']} limit {mx}s (limits not verified)")
if A.layout and os.path.exists(A.layout):
    sa = load(A.layout).get("safe_area", {}); iss = sa.get("issues", [])
    msgs = [f"{i['element']} {i['px']}px outside safe area ({i['side']})" for i in iss]
    if sa.get("mode") == "enforce": check("safe_area", not iss, msgs, f"inside {sa.get('platform')} safe area")
    else: warnings += [f"safe area (template, not enforced): {m}" for m in msgs]
LY = load(A.layout) if A.layout and os.path.exists(A.layout) else {}
if LY.get("elements"):   # M4 B2: every MUST-stay-visible element (headline, logos, disclosure, captions, cards) against the platform safe area
    bad = {k: v["outside"] for k, v in LY["elements"].items() if v["cls"] == "must" and v["outside"]}
    msg = [f"{k}: " + ", ".join(f"{o['side']} {o['px']}px" for o in v) for k, v in bad.items()]
    if LY.get("safe_area", {}).get("mode") == "enforce": check("must_stay_visible", not bad, msg or "all inside", f"must-stay-visible elements inside {PF['name']} safe area")
    else: warnings += [f"must-stay-visible outside the safe area (approved template, warn mode): {m}" for m in msg]
    strict = [f"{k}: " + ", ".join(f"{o['side']} {o['px']}px" for o in v["outside_strict"]) for k, v in LY["elements"].items() if v["cls"] == "must" and v.get("outside_strict")]
    warnings += [f"advisory (stricter published guidance): {m}" for m in strict]
if "narration" in LY:   # M4 B1 - narration projects only; reels without a narration setting get exactly the checks they had before
    import numpy as np
    disc = LY.get("ai_disclosure")
    if LY["narration"] == "ai":
        why = []
        if not disc: why.append("missing from the layout")
        else:
            if any(i["element"] == "ai_disclosure" for i in LY.get("safe_area", {}).get("issues", [])): why.append("outside the safe area")
            mk = np.array(Image.open(disc["mask"]).convert("L")) > 200 if os.path.exists(disc.get("mask", "")) else None
            if mk is None or not mk.any(): why.append("text mask missing")
            else:
                l, t, r, b = disc["box"]; pill = np.zeros_like(mk); pill[t + 6:b - 6, l + 20:r - 20] = True; pill &= ~mk
                TS = float(LY.get("title_seconds", 2.0)); T2 = tmpdir()
                for k, tt in enumerate((TS + 0.4, TS + max(0.8, (D - TS) * 0.25), TS + max(1.2, (D - TS) * 0.5))):
                    if tt >= D: continue
                    fp = os.path.join(T2, f"disc_{k}.png"); sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{tt:.2f}", "-i", F, "-frames:v", "1", fp])
                    if not os.path.exists(fp): why.append(f"no frame at {tt:.1f}s"); continue
                    g = np.array(Image.open(fp).convert("L")).astype(float)
                    if g.shape != mk.shape: why.append("frame size differs from layout"); break
                    txt_l, pill_l = g[mk].mean(), g[pill].mean()
                    if not (txt_l > 170 and pill_l < 100): why.append(f"not readable at {tt:.1f}s (text {txt_l:.0f}, background {pill_l:.0f})")
        check("ai_disclosure", not why, "on screen, inside safe area" if not why else why, "AI narration: Telugu disclosure readable on screen, inside the safe area")
        warnings.append("upload checklist: switch on the platform's AI-content label (AI narration)")
    else:
        check("ai_disclosure", not disc, "absent" if not disc else "present", f"no AI-voice disclosure for narration '{LY['narration']}'")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", F, "-vn", "-f", "s16le", "-acodec", "pcm_s16le", "-"], capture_output=True).stdout
    pcm = np.frombuffer(raw, np.int16) if raw else np.zeros(0, np.int16)
    clipped = int(np.sum(np.abs(pcm.astype(np.int32)) >= 32767))
    check("clipping", clipped == 0, clipped, "no clipped audio samples")
if A.baseline:
    B = load(A.baseline)
    check("baseline_frames", frames == B["frames"], frames, f"exactly {B['frames']}")
    check("baseline_file_size", B["size_min"] <= size <= B["size_max"], size, f"{B['size_min']}-{B['size_max']} bytes")
# contact sheet (frames go to this job's own temp folder)
T = tmpdir(); n = 16; Wc, Hc = 180, 320; S = Image.new('RGB', (Wc*8, Hc*2))
for i in range(n):
    t = D*(i+0.5)/n; f = os.path.join(T, f"qa_{i}.png")
    sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", F, "-frames:v", "1", "-vf", f"scale={Wc}:{Hc}", f])
    im = Image.open(f); d = ImageDraw.Draw(im); d.rectangle((0, 0, 44, 13), fill=0); d.text((2, 1), f"{t:.1f}", fill=(255, 255, 0)); S.paste(im, ((i % 8)*Wc, (i//8)*Hc))
sheet = os.path.splitext(F)[0]+"_qa.jpg"; S.save(sheet, quality=85)
ok = all(c["pass_"] for c in checks)
R = dict(reel=F, platform=pf_name, passed=ok, duration=round(D, 3), frames=frames, file_size=size, loudness_lufs=I, true_peak_db=TP,
         checks=[{**{k: c[k] for k in ("name", "value", "rule")}, "passed": c["pass_"]} for c in checks], warnings=warnings, contact_sheet=sheet)
out = A.json or os.path.splitext(F)[0]+"_qa.json"
with open(out, "w", encoding="utf-8") as f: json.dump(R, f, ensure_ascii=False, indent=2)
# human summary (same first lines as before)
print("specs:", [(s["codec_name"], s.get("width"), s.get("height"), s.get("r_frame_rate")) for s in p["streams"]], "dur", p["format"]["duration"])
print("black frames:", bl or "none")
print("loudness:", [str(I)], "LUFS, peak", [str(TP)], "dBFS")
print("contact sheet ->", sheet)
for c in R["checks"]: print(f"  {'PASS' if c['passed'] else 'FAIL'}  {c['name']}: {c['value']}  (rule {c['rule']})")
for w in warnings: print("  WARN ", w)
print("QA", "PASSED" if ok else "FAILED", "->", out)
emit("qa", step="qa", passed=ok, report=out)
sys.exit(0 if ok else 2)
