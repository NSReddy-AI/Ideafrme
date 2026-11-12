"""Gate B1.2 - speed comparison for AI narration (approved 10 Nov 2026). Listening material + objective checks. NO reel is rendered.
Run on the Mac from the dev folder:   ~/.venvs/reelstudio/bin/python tools/gate_b1_2_speed_test.py      (about 35-45 minutes)
  - Script: 9 lines taken word for word from reel_002's approved captions (only full stops added), numbers spoken as words.
    Approved by this tool FOR LISTENING TESTS ONLY - not for publishing.
  - 4 voices/styles (Prakash, Lalitha x News, Documentary) x 3 speeds (1.0, 1.15, 1.20) = 12 takes. Speed = FFmpeg atempo (approved);
    the voice model speaks each sentence once (1.0) and the faster takes reuse those sentences, so only the speed differs.
    The project default stays 1.0 (each test project is set back to 1.0 at the end).
  - Every take is loudness-matched the same way (voice only, -14 LUFS, true peak -1.5 dB) so loudness cannot bias the listening.
  - Objective checks per take: pitch kept (median voice pitch within 3 % of the 1.0x take), pauses identical at every speed and silent,
    loudness -14 +/- 0.5 LUFS, true peak <= -1 dB, no clipped samples, intelligibility (Telugu speech-to-text: character error <= 20 %,
    every number heard correctly). Speech-to-text runs ONCE over all 12 takes (one model load), after the voice model has closed.
  - Blind: takes are shuffled and named X01..X12. The answer key is in answer_key/ - open it only after scoring.
Evidence: tests/acceptance/M4_gateB/B1/B1.2_speed_<date_time>/
  blind/X01.wav ... X12.wav, score_sheet.csv (you fill in), script.md (the text, to mark wrong words), summary.md (objective results by
  blind label, no identities), answer_key/ (key.json, named copies, full measurements), log.txt, results.json"""
import os, sys, json, time, hashlib, subprocess, shutil, random, re, wave, csv
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ENG = os.path.join(ROOT, "engine"); sys.path.insert(0, ENG)
HOME = os.path.expanduser("~"); PY = sys.executable; os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1", "B1.2_speed_" + time.strftime("%Y%m%d_%H%M%S"))
for sub in ("blind", "answer_key", "work"): os.makedirs(os.path.join(OUT, sub))
LOG, R = [], dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), checks=[])
def log(m): line = f"[{time.strftime('%H:%M:%S')}] {m}"; print(line, flush=True); LOG.append(line)
def check(name, ok, detail=""): R["checks"].append(dict(name=name, passed=bool(ok), detail=detail)); log(("PASS " if ok else "FAIL ") + name + (f" - {json.dumps(detail, ensure_ascii=False)[:200]}" if detail != "" else ""))
def load(p): return json.load(open(p, encoding="utf-8"))
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def sh(cmd, env=None, timeout=7200): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, **(env or {})), timeout=timeout)
def fingerprint(path):
    if not os.path.exists(path): return None
    h, n = hashlib.sha256(), 0
    for dp, dn, fn in os.walk(path):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            try: st = os.lstat(p)
            except OSError: continue
            h.update(f"{os.path.relpath(p, path)}|{st.st_size}|{int(st.st_mtime)}\n".encode()); n += 1
    return dict(files=n, sha256=h.hexdigest())
WATCH = {"original_Reel_Studio": os.path.join(os.path.dirname(ROOT), "Reel Studio"), "reel_002_project": os.path.join(ROOT, "projects", "2026-11-03_reel_002_development"),
         "reelstudio_env": os.path.join(HOME, ".venvs", "reelstudio"), "rs_asr_env": os.path.join(HOME, ".venvs", "rs_asr"),
         "rs_tts_env": os.path.join(HOME, ".venvs", "rs_tts"), "voice_model_cache": os.path.join(HOME, ".cache", "rs_tts_hf"),
         "B1.1_evidence": os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1", "run_20261110_164955")}
def read_wav(p):
    with wave.open(p) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes(); x = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    return (x.reshape(-1, ch).mean(axis=1) if ch > 1 else x), sr

SCRIPT = ["అక్కచెల్లెమ్మలకు 31 లక్షల ఇళ్ల పట్టాలు.", "సొంతింటి కల నెరవేర్చేలా 17,000 జగనన్న కాలనీలు.", "గ్రామ స్వరాజ్యం కోసం 15,000 సచివాలయాలు.",
          "ప్రభుత్వానికి ప్రజలకు వారధిగా 2.5 లక్షల మంది వాలంటీర్లు.", "అన్నదాతకు ఆసరాగా 10,500 ఆర్బీకేలు.", "పేదవాడి ఆరోగ్యానికి అందుబాటులో 10,000 విలేజ్ క్లినిక్‌లు.",
          "పేదవాడికి కార్పొరేట్ వైద్యం 25 లక్షల వరకు ఆరోగ్యశ్రీ పరిమితి.", "17,805 కోట్లతో ప్రభుత్వ బడులు నాడు నేడు.", "130 భారీ ప్రాజెక్టులు లక్ష కోట్లకు పైగా పెట్టుబడులతో సాకారం."]
COMBOS = [("prakash", "news"), ("prakash", "documentary"), ("lalitha", "news"), ("lalitha", "documentary")]
SPEEDS = [1.0, 1.15, 1.2]

def f0_median(x, sr):
    """Median voice pitch (Hz) from voiced frames (autocorrelation, 70-400 Hz)."""
    x = x - x.mean(); fl, hop = int(0.04 * sr), int(0.01 * sr); win = np.hanning(fl); lo, hi = int(sr / 400), int(sr / 70)
    rms = np.array([np.sqrt(np.mean(x[i:i + fl] ** 2)) for i in range(0, len(x) - fl, hop)]); thr = 0.25 * (rms.max() if len(rms) else 0); vals = []
    for k, i in enumerate(range(0, len(x) - fl, hop)):
        if rms[k] < thr: continue
        f = x[i:i + fl] * win; ac = np.fft.irfft(np.abs(np.fft.rfft(f, 2 * fl)) ** 2)[:fl]
        if ac[0] <= 0: continue
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] / ac[0] > 0.35: vals.append(sr / lag)
    return float(np.median(vals)) if vals else None

def loudnorm(src, dst):
    """Every take levelled the same way: gain to -14 LUFS, then a peak limiter at -1.5 dBFS (loudnorm alone could leave quiet, peaky
    takes up to 0.7 dB short - found in the first B1.2 run)."""
    def measure(p):
        e = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+)", e)[-1])
    I0, _ = measure(src)
    sh(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", f"volume={-14.0 - I0}dB,alimiter=limit=0.84:level=false:attack=5:release=50,aresample=48000",
        "-ac", "1", "-c:a", "pcm_s16le", dst])
    I, TP = measure(dst); x, _ = read_wav(dst); return I, TP, int(np.sum(np.abs(x) >= 32767 / 32768))

# ------------------------------------------------------------------------------------------------------------------------ start
log("B1.2 speed comparison (no reel is rendered)"); FP0 = {k: fingerprint(p) for k, p in WATCH.items()}
import narrate as NR
check("speed method: FFmpeg atempo available (approved method)", NR.filter_available("atempo"))
C = load(os.path.join(ENG, "tts.json")); check("default speed is still 1.0 in tts.json", C["speed"]["default"] == 1.0 and C["speed"]["method"] == "atempo", C["speed"])
TAKES, MEM = [], {}
for voice, style in COMBOS:
    slug = f"b12_{voice}_{style}"; d = os.path.join(ROOT, "projects", f"zz_gateB_{slug}"); b = os.path.join(d, "build")
    if not os.path.exists(d):
        os.makedirs(b); os.makedirs(os.path.join(d, "inputs"))
        save(dict(brand="jagan_for_andhra", platform="instagram", style="documentary", provider=None, brief=f"Gate B1.2 speed test ({voice}/{style}) - listening test only, not for publishing",
                  video=None, title_seconds=2.0, hook=dict(line1="", line2="", line3="", tag_top="", tag_bottom=""), title=["పరీక్ష", "Gate B1.2"],
                  title_person=None, title_bg=None, face_tracking=False, approved=False, status="test", history=[]), os.path.join(d, "project.json"))
    sf = os.path.join(d, "inputs", "script.txt"); open(sf, "w", encoding="utf-8").write("\n".join(SCRIPT) + "\n")
    sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.0", "--method", "atempo"])
    r1 = sh([PY, "engine/rs.py", "script", d, sf]); r2 = sh([PY, "engine/rs.py", "script-approve", d, "--checked"])
    if voice == "prakash" and style == "news": open(os.path.join(OUT, "script_spoken_forms.txt"), "w", encoding="utf-8").write(r1.stdout)
    check(f"{voice}/{style}: test script approved for listening only", r2.returncode == 0, r2.stderr[-200:])
    for sp in SPEEDS:
        sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", str(sp), "--method", "atempo"])
        log(f"narrate {voice}/{style} {sp}x" + (" (voice model loads; about 1-2 minutes)" if sp == 1.0 else " (from the sentence cache)"))
        t = time.time(); r = sh([PY, "engine/narrate.py", d], env=dict(RS_EVENTS="1")); secs = round(time.time() - t, 1)
        errs = [json.loads(l).get("code") for l in r.stdout.splitlines() if l.startswith("{") and '"error"' in l]
        if r.returncode: check(f"{voice}/{style} {sp}x: narration made", False, errs or r.stderr[-300:]); continue
        TL = load(os.path.join(b, "narration_timeline.json")); name = f"{voice}_{style}_{sp:.2f}x"
        raw = os.path.join(OUT, "work", name + "_raw.wav"); shutil.copy(os.path.join(b, "narration.wav"), raw); save(TL, os.path.join(OUT, "answer_key", name + "_timeline.json"))
        if TL["memory"]["model_loaded"]: MEM[f"{voice}/{style}"] = dict(peak_rss_gb=TL["memory"]["peak_rss_gb"], load_s=TL["generated"]["load_s"], seconds=secs)
        TAKES.append(dict(name=name, voice=voice, style=style, speed=sp, raw=raw, timeline=TL, spoken=TL["generated"]["spoken"], seconds=secs))
    sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.0", "--method", "atempo"]); sh([PY, "engine/narrate.py", d])   # back to the default
    check(f"{voice}/{style}: project left at the default speed 1.0", load(os.path.join(d, "project.json")).get("narration_speed") == 1.0)
for k, m in MEM.items(): check(f"memory {k}: voice model peak under 8 GB (model loaded)", m["peak_rss_gb"] is not None and m["peak_rss_gb"] <= 8.0, m)
check("every take made (4 voices/styles x 3 speeds = 12)", len(TAKES) == 12, len(TAKES))

# ------------------------------------------------------------------------------------------------------------------------ objective checks
log("objective checks: pitch, pauses, loudness, clipping")
base = {(t["voice"], t["style"]): t for t in TAKES if t["speed"] == 1.0}
for t in TAKES: x, sr = read_wav(t["raw"]); t["f0_hz"] = f0_median(x, sr)
for t in TAKES:
    x, sr = read_wav(t["raw"]); TL = t["timeline"]; S = TL["sentences"]; b0 = base[(t["voice"], t["style"])]; t["f0_ref_hz"] = b0["f0_hz"]
    t["pitch_change_pct"] = round(100 * (t["f0_hz"] - t["f0_ref_hz"]) / t["f0_ref_hz"], 2) if t["f0_hz"] and t["f0_ref_hz"] else None
    gaps = [round(c["s"] - a["e"], 3) for a, c in zip(S, S[1:])]; ref_gaps = [round(c["s"] - a["e"], 3) for a, c in zip(b0["timeline"]["sentences"], b0["timeline"]["sentences"][1:])]
    silent = [float(20 * np.log10(np.sqrt(np.mean(x[int(a["e"] * sr) + 1: int(c["s"] * sr) - 1] ** 2)) + 1e-12)) for a, c in zip(S, S[1:])]
    t["pauses_s"] = gaps; t["pauses_same_as_1x"] = gaps == ref_gaps; t["pause_level_db_max"] = round(max(silent), 1)
    speech = sum(s["speech_s"] for s in S); words = sum(len(s["say"].split()) for s in S)
    t["speech_s"] = round(speech, 2); t["words_per_min"] = round(60 * words / speech, 1); t["duration_s"] = TL["duration"]
    t["speed_measured"] = round(sum(s["speech_s"] for s in b0["timeline"]["sentences"]) / speech, 3)
    norm = os.path.join(OUT, "work", t["name"] + "_norm.wav"); t["lufs"], t["true_peak_db"], t["clipped"] = loudnorm(t["raw"], norm); t["norm"] = norm

# ------------------------------------------------------------------------------------------------------------------------ intelligibility (one ASR run)
log("intelligibility: Telugu speech-to-text over all 12 takes in one run (about 20-30 minutes)")
GAP = 2.5; parts, spans, t0 = [], [], 0.0
for t in TAKES:
    x, sr = read_wav(t["norm"]); parts += [x, np.zeros(int(GAP * sr), np.float32)]; spans.append((t0, t0 + len(x) / sr)); t0 += len(x) / sr + GAP
allw = os.path.join(OUT, "work", "all_takes.wav")
with wave.open(allw, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes((np.clip(np.concatenate(parts), -1, 1) * 32767).astype(np.int16).tobytes())
from common import heavy_lock
asr_out = os.path.join(OUT, "work", "all_takes_asr.json"); ta = time.time()
with heavy_lock("speech-to-text (B1.2 intelligibility)"):
    r = sh([PY, os.path.join(ENG, "transcribe.py"), "--audio", allw, "--lang", "te", "--out", asr_out])
R["asr_seconds"] = round(time.time() - ta, 1)
if r.returncode or not os.path.exists(asr_out): check("intelligibility: speech-to-text ran", False, (r.stderr or r.stdout)[-300:]); HW = []
else: HW = load(asr_out)["words"]; check("intelligibility: speech-to-text ran (one model load)", True, dict(words=len(HW), seconds=R["asr_seconds"]))
import narration_align as NA
N0 = load(os.path.join(ROOT, "projects", "zz_gateB_b12_prakash_news", "build", "narration.json")); SAY = " ".join(l["say"] for l in N0["lines"])
want_nums = NA.numbers(SAY)
for t, (a, b2) in zip(TAKES, spans):
    heard = " ".join(h["w"] for h in HW if a - 0.5 <= h["s"] <= b2 + 0.5)
    t["heard"] = heard; t["cer"] = round(NA.cer(SAY, heard), 3) if HW else None; got = NA.numbers(heard)
    t["numbers_expected"] = len(want_nums); t["numbers_heard_correctly"] = sum(1 for v in want_nums if v in got); t["numbers_ok"] = t["numbers_heard_correctly"] == len(want_nums)

# ------------------------------------------------------------------------------------------------------------------------ per-take verdicts
for t in TAKES:
    t["checks"] = dict(pitch_kept=t["pitch_change_pct"] is not None and abs(t["pitch_change_pct"]) <= 3.0, pauses_same=t["pauses_same_as_1x"] and t["pause_level_db_max"] < -60,
                       speed_right=abs(t["speed_measured"] - t["speed"]) <= 0.03 * t["speed"], loudness=abs(t["lufs"] + 14) <= 0.5, true_peak=t["true_peak_db"] <= -1.0,
                       no_clipping=t["clipped"] == 0, intelligible=t["cer"] is not None and t["cer"] <= 0.20, numbers=t["numbers_ok"])
    t["objective_pass"] = all(t["checks"].values())

# ------------------------------------------------------------------------------------------------------------------------ blind set
rng = random.Random(int(time.time())); order = list(range(len(TAKES))); rng.shuffle(order); KEY = {}
for n, i in enumerate(order, 1):
    lab = f"X{n:02d}"; t = TAKES[i]; t["label"] = lab; KEY[lab] = dict(voice=t["voice"], style=t["style"], speed=t["speed"])
    shutil.copy(t["norm"], os.path.join(OUT, "blind", lab + ".wav")); shutil.copy(t["norm"], os.path.join(OUT, "answer_key", f"{lab}__{t['name']}.wav"))
save(KEY, os.path.join(OUT, "answer_key", "key.json"))
save([{k: v for k, v in t.items() if k not in ("timeline",)} for t in TAKES], os.path.join(OUT, "answer_key", "objective_full.json"))
with open(os.path.join(OUT, "score_sheet.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["clip", "pronunciation (1-5)", "naturalness (1-5)", "pacing (1-5)", "audio quality (1-5)", "wrong words (write them)", "notes"])
    for lab in sorted(KEY): w.writerow([lab, "", "", "", "", "", ""])
open(os.path.join(OUT, "script.md"), "w", encoding="utf-8").write("# B1.2 listening script (for marking wrong words)\n\nWord for word from reel_002's approved captions; "
    "numbers are spoken as words. Listening test only - not for publishing.\n\n" + "\n".join(f"{i}. {l['text']}  \n   spoken: {l['say']}" for i, l in enumerate(N0["lines"], 1)) + "\n")

# ------------------------------------------------------------------------------------------------------------------------ isolation + summary
FP1 = {k: fingerprint(p) for k, p in WATCH.items()}
for k in WATCH: check(f"isolation: {k} unchanged", FP0[k] == FP1[k], (FP1[k] or {}).get("files"))
npass = sum(t["objective_pass"] for t in TAKES); check(f"objective checks: takes passing every check", npass == len(TAKES), f"{npass}/{len(TAKES)}")
R.update(finished=time.strftime("%Y-%m-%d %H:%M:%S"), memory=MEM, takes_passing=npass, takes=len(TAKES)); n = sum(c["passed"] for c in R["checks"])
R["result"] = "PASS" if n == len(R["checks"]) else "FAIL"; save(R, os.path.join(OUT, "results.json")); open(os.path.join(OUT, "log.txt"), "w").write("\n".join(LOG) + "\n")
lab = sorted(TAKES, key=lambda t: t["label"])
def cer_txt(t): return "-" if t["cer"] is None else f"{t['cer']:.0%}"
L = ["# B1.2 speed comparison - listening pack", "", f"{R['started']} -> {R['finished']} | checks **{R['result']}** ({n}/{len(R['checks'])})", "",
     "**How to score:** listen to `blind/X01.wav` ... `X12.wav` (any order, as often as you like) and fill in `score_sheet.csv`: pronunciation, naturalness, "
     "pacing and audio quality (1-5), plus any wrong words (see `script.md`). Open `answer_key/` only after scoring.", "",
     "A speed passes for a voice and style when: average >= 4/5, no score below 3/5, no wrong words, and every objective check below passes. "
     "The default stays 1.0x until you approve a change.", "",
     "## Objective results by blind label (no identities)", "", "| clip | pitch kept | pauses same + silent | loudness (LUFS) | true peak (dB) | clipped | character error | numbers heard | all checks |",
     "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
L += [f"| {t['label']} | {'yes' if t['checks']['pitch_kept'] else 'NO'} | {'yes' if t['checks']['pauses_same'] else 'NO'} | {t['lufs']} | {t['true_peak_db']} | {t['clipped']} | "
      f"{cer_txt(t)} | {t['numbers_heard_correctly']}/{t['numbers_expected']} | {'PASS' if t['objective_pass'] else 'FAIL'} |" for t in lab]
L += ["", "## Memory and isolation", ""] + [f"- {k}: peak {m['peak_rss_gb']} GB (limit 8 GB), model load {m['load_s']} s" for k, m in MEM.items()] + \
     [f"- {c['name']}: {'PASS' if c['passed'] else 'FAIL'}" for c in R["checks"] if c["name"].startswith("isolation")]
open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
log(f"FINAL: {R['result']} ({n}/{len(R['checks'])}); objective {npass}/{len(TAKES)} takes - listening pack {os.path.relpath(OUT, ROOT)}/ (blind/, score_sheet.csv)")
sys.exit(0 if R["result"] == "PASS" else 2)
