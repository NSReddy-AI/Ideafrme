"""Gate B1.2 final technical checks (approved 10 Nov 2026). NO reel is rendered.
Run on the Mac from the dev folder:   ~/.venvs/reelstudio/bin/python tools/gate_b1_2_restart_test.py      (about 5 minutes)
  1 loudness     the 12 levelled blind clips (blind_leveled/) re-measured: -14 +/- 0.5 LUFS, true peak <= -1 dB, no clipped samples
  2 restart      the same 9-sentence script spoken again in NEW test projects with a fresh voice process every 5 sentences
                 (batches of 5 + 4) for Prakash/News and Lalitha/Documentary; peak memory per batch recorded
  3 continuity   compared with the single-process B1.2 takes: every sentence file, the narration audio, the text (approval
                 fingerprint) and every sentence time identical; joins between sentences are silent (no clicks); a re-run comes
                 from the cache ("model not loaded"); 1.15x and 1.20x from the cache equal the B1.2 takes
  4 isolation    original Reel Studio, reel_002, the three environments, the model cache and the B1.1/B1.2 evidence unchanged;
                 offline tests (tests/test_narration.py) pass
Evidence: tests/acceptance/M4_gateB/B1/B1.2_final_<date_time>/"""
import os, sys, json, time, hashlib, subprocess, shutil, re, wave, glob
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ENG = os.path.join(ROOT, "engine"); sys.path.insert(0, ENG)
HOME = os.path.expanduser("~"); PY = sys.executable; os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
B1 = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1"); OUT = os.path.join(B1, "B1.2_final_" + time.strftime("%Y%m%d_%H%M%S")); os.makedirs(OUT)
B12 = sorted(glob.glob(os.path.join(B1, "B1.2_speed_*")))[0]
LOG, R = [], dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), checks=[], b12_evidence=os.path.relpath(B12, ROOT))
def log(m): line = f"[{time.strftime('%H:%M:%S')}] {m}"; print(line, flush=True); LOG.append(line)
def check(name, ok, detail=""): R["checks"].append(dict(name=name, passed=bool(ok), detail=detail)); log(("PASS " if ok else "FAIL ") + name + (f" - {json.dumps(detail, ensure_ascii=False)[:220]}" if detail != "" else ""))
def load(p): return json.load(open(p, encoding="utf-8"))
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def sh(cmd, env=None, timeout=7200): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, **(env or {})), timeout=timeout)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
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
         "reelstudio_env": os.path.join(HOME, ".venvs", "reelstudio"), "rs_asr_env": os.path.join(HOME, ".venvs", "rs_asr"), "rs_tts_env": os.path.join(HOME, ".venvs", "rs_tts"),
         "voice_model_cache": os.path.join(HOME, ".cache", "rs_tts_hf"), "B1.1_evidence": os.path.join(B1, "run_20261110_164955"), "B1.2_evidence": B12,
         "B1.2_projects": os.path.join(ROOT, "projects", "zz_gateB_b12_prakash_news")}
def read_wav(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16), w.getframerate()

log("B1.2 final technical checks (no reel is rendered)"); FP0 = {k: fingerprint(p) for k, p in WATCH.items()}
a22 = sorted(glob.glob(os.path.join(ROOT, "tests", "acceptance", "M4_gateA2_2", "20*", "results.json")))
if a22:
    ref = load(a22[-1])["steps"]["1 pre-checks"]["fingerprints"]
    for k in ("original_Reel_Studio", "reelstudio_env", "rs_asr_env"): check(f"isolation since Gate A2.2: {k} unchanged", ref.get(k) == FP0.get(k))
ref = load(os.path.join(B1, "fingerprints_before.json"))
for k in ("original_Reel_Studio", "reel_002_project"): check(f"isolation since B1 start: {k} unchanged", ref.get(k) == FP0.get(k))

# 1 loudness ---------------------------------------------------------------------------------------------------------------------
log("STEP 1 loudness of the 12 levelled clips"); LOUD = {}
for f in sorted(glob.glob(os.path.join(B12, "blind_leveled", "X*.wav"))):
    e = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); TP = float(re.findall(r"Peak:\s+(-?[\d.]+)", e)[-1]); x, _ = read_wav(f)
    LOUD[os.path.basename(f)] = dict(lufs=I, true_peak_db=TP, clipped=int(np.sum(np.abs(x.astype(np.int32)) >= 32767)))
save(LOUD, os.path.join(OUT, "loudness_blind_leveled.json"))
check("loudness: 12 levelled clips at -14 +/- 0.5 LUFS", len(LOUD) == 12 and all(abs(v["lufs"] + 14) <= 0.5 for v in LOUD.values()), {k: v["lufs"] for k, v in LOUD.items()})
check("loudness: true peak <= -1 dB on all 12", all(v["true_peak_db"] <= -1.0 for v in LOUD.values()), {k: v["true_peak_db"] for k, v in LOUD.items()})
check("loudness: no clipped samples on all 12", all(v["clipped"] == 0 for v in LOUD.values()))

# 2+3 restart + continuity ---------------------------------------------------------------------------------------------------------
C = load(os.path.join(ENG, "tts.json")); check("settings: fresh voice process every 5 sentences; default speed 1.0; atempo", C["memory"].get("restart_every") == 5 and C["speed"]["default"] == 1.0 and C["speed"]["method"] == "atempo")
RES = {}
for voice, style in (("prakash", "news"), ("lalitha", "documentary")):
    src = os.path.join(ROOT, "projects", f"zz_gateB_b12_{voice}_{style}"); d = os.path.join(ROOT, "projects", f"zz_gateB_b12r_{voice}_{style}"); b = os.path.join(d, "build")
    log(f"STEP 2 restart test {voice}/{style}: 9 sentences, fresh voice process every 5 (two model loads, about 2 minutes)")
    if os.path.exists(d): check(f"{voice}/{style}: new test project", False, "already exists - nothing changed"); continue
    os.makedirs(b); os.makedirs(os.path.join(d, "inputs"))
    P = load(os.path.join(src, "project.json")); P.update(brief=f"Gate B1.2 restart test ({voice}/{style}) - not for publishing", history=[]); P.pop("narration_hash", None)
    save(P, os.path.join(d, "project.json")); shutil.copy(os.path.join(src, "inputs", "script.txt"), os.path.join(d, "inputs", "script.txt"))
    sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.0", "--method", "atempo"])
    sh([PY, "engine/rs.py", "script", d, os.path.join(d, "inputs", "script.txt")]); r2 = sh([PY, "engine/rs.py", "script-approve", d, "--checked"])
    Na, Nb = load(os.path.join(src, "build", "narration.json")), load(os.path.join(b, "narration.json"))
    check(f"{voice}/{style}: same approved text (fingerprint) as the B1.2 takes", r2.returncode == 0 and Na["approved_hash"] == Nb["approved_hash"], Nb.get("approved_hash", "")[:12])
    t = time.time(); r = sh([PY, "engine/narrate.py", d], env=dict(RS_EVENTS="1")); secs = round(time.time() - t, 1)
    errs = [json.loads(l).get("code") for l in r.stdout.splitlines() if l.startswith("{") and '"error"' in l]
    if r.returncode: check(f"{voice}/{style}: narration with restarts", False, errs or r.stderr[-300:]); continue
    T1 = load(os.path.join(b, "narration_timeline.json")); G = T1["generated"]; ref = load(os.path.join(B12, "answer_key", f"{voice}_{style}_1.00x_timeline.json"))
    batches = G.get("batches", []); RES[f"{voice}/{style}"] = dict(seconds=secs, batches=batches, peak_rss_gb=T1["memory"]["peak_rss_gb"], single_process_peak_gb=ref["memory"]["peak_rss_gb"])
    check(f"{voice}/{style}: two batches (5 + 4 sentences), two model loads", [x["sentences"] for x in batches] == [5, 4], batches)
    check(f"{voice}/{style}: peak memory per batch under 8 GB", all(x["peak_rss_gb"] <= 8.0 for x in batches), dict(batches=[x["peak_rss_gb"] for x in batches], single_process=ref["memory"]["peak_rss_gb"]))
    ca = {f: sha(os.path.join(src, "build", "narration_cache", f)) for f in os.listdir(os.path.join(src, "build", "narration_cache")) if f.endswith(".wav") and not f.endswith(".part.wav")}
    cb = {f: sha(os.path.join(b, "narration_cache", f)) for f in os.listdir(os.path.join(b, "narration_cache")) if f.endswith(".wav") and not f.endswith(".part.wav")}
    same_files = set(cb) <= set(ca) and len(cb) == 9 and all(ca[f] == cb[f] for f in cb)
    check(f"{voice}/{style}: every sentence identical to the single-process take (sentence files)", same_files, f"{sum(ca.get(f) == h for f, h in cb.items())}/9 identical")
    check(f"{voice}/{style}: sentence text and times identical to the B1.2 take", [(x["say"], x["s"], x["e"]) for x in T1["sentences"]] == [(x["say"], x["s"], x["e"]) for x in ref["sentences"]])
    check(f"{voice}/{style}: narration audio identical to the B1.2 take", T1["audio_sha256"] == ref["audio_sha256"], dict(now=T1["audio_sha256"][:12], b12=ref["audio_sha256"][:12]))
    x, sr = read_wav(os.path.join(b, "narration.wav")); joins = []
    for a_, c_ in zip(T1["sentences"], T1["sentences"][1:]):   # corrected (B1.2): exact sample positions, not millisecond-rounded times
        lo, hi = (a_["e_sample"], c_["s_sample"]) if "e_sample" in a_ else (int(a_["e"] * sr) + 1, int(c_["s"] * sr) - 1)
        seg = x[lo:hi].astype(np.int32); joins.append(int(np.max(np.abs(seg))) if len(seg) else 0)
    check(f"{voice}/{style}: audio continuity - every join between sentences is silent (no click)", all(j == 0 for j in joins), joins)
    r = sh([PY, "engine/narrate.py", d]); T2 = load(os.path.join(b, "narration_timeline.json"))
    check(f"{voice}/{style}: cache - re-run speaks nothing, same audio, 'model not loaded'", r.returncode == 0 and T2["generated"]["spoken"] == 0 and T2["audio_sha256"] == T1["audio_sha256"]
          and T2["memory"]["model_loaded"] is False, T2["memory"].get("note"))
    for sp in (1.15, 1.2):
        sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", str(sp), "--method", "atempo"]); r = sh([PY, "engine/narrate.py", d])
        Ts = load(os.path.join(b, "narration_timeline.json")); raw = os.path.join(B12, "work", f"{voice}_{style}_{sp:.2f}x_raw.wav")
        check(f"{voice}/{style} {sp}x: from the cache, identical to the B1.2 take", r.returncode == 0 and Ts["generated"]["spoken"] == 0 and os.path.exists(raw) and sha(raw) == Ts["audio_sha256"])
    sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.0", "--method", "atempo"]); sh([PY, "engine/narrate.py", d])
    check(f"{voice}/{style}: project left at the default speed 1.0", load(os.path.join(d, "project.json")).get("narration_speed") == 1.0)
    for f in ("narration_timeline.json", "narration.json"): shutil.copy(os.path.join(b, f), os.path.join(OUT, f"{voice}_{style}_{f}"))
R["restart"] = RES

# 4 offline tests + isolation ------------------------------------------------------------------------------------------------------
log("STEP 4 offline tests and isolation"); r = sh([PY, "tests/test_narration.py", "--out", OUT], timeout=1800); open(os.path.join(OUT, "test_narration.txt"), "w").write(r.stdout + r.stderr)
tn = load(os.path.join(OUT, "test_narration.json")) if os.path.exists(os.path.join(OUT, "test_narration.json")) else {}
check("offline tests: tests/test_narration.py (incl. restart batches)", r.returncode == 0, f"{tn.get('passed')}/{tn.get('total')}")
FP1 = {k: fingerprint(p) for k, p in WATCH.items()}
for k in WATCH: check(f"isolation: {k} unchanged during this run", FP0[k] == FP1[k], (FP1[k] or {}).get("files"))
check("lock: no heavy-model lock left behind", not os.path.exists(os.path.join(ROOT, ".heavy_model.lock")) or not open(os.path.join(ROOT, ".heavy_model.lock")).read().strip())
n = sum(c["passed"] for c in R["checks"]); R.update(finished=time.strftime("%Y-%m-%d %H:%M:%S"), result="PASS" if n == len(R["checks"]) else "FAIL")
save(R, os.path.join(OUT, "results.json")); open(os.path.join(OUT, "log.txt"), "w").write("\n".join(LOG) + "\n")
open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8").write("\n".join([f"# B1.2 final technical checks", "", f"{R['started']} -> {R['finished']} | **{R['result']}** ({n}/{len(R['checks'])})", "",
    "| Check | Result | Detail |", "| --- | --- | --- |"] + [f"| {c['name']} | {'PASS' if c['passed'] else 'FAIL'} | {json.dumps(c['detail'], ensure_ascii=False)[:160]} |" for c in R["checks"]]) + "\n")
log(f"FINAL: {R['result']} ({n}/{len(R['checks'])}) - evidence {os.path.relpath(OUT, ROOT)}/summary.md"); sys.exit(0 if R["result"] == "PASS" else 2)
