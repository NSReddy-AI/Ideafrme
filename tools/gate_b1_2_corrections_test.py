"""Gate B1.2 corrections - tests for final B1.2 acceptance (approved 10 Nov 2026). NO reel is rendered.
Run on the Mac from the dev folder:   ~/.venvs/reelstudio/bin/python tools/gate_b1_2_corrections_test.py      (about 5 minutes)
  1 continuity   corrected check with EXACT sample positions, re-run on the two B1.2 restart-test projects (from the cache);
                 their audio must stay identical to the approved B1.2 takes
  2 fade test    10 ms fade at sentence edges (test setting only - the default stays off) for all 4 voices/styles at 1.0x, made from the
                 approved B1.2 sentences (no model load): positions, pauses and alignment identical; every sample outside the 10 ms edges
                 identical (no speech cut, no pronunciation change); edges inside the quiet trim margin; loudness after the same levelling
                 within 0.05 LU of before. Before/after listening pairs written for Prakash/News and Lalitha/Documentary.
  3 memory       one real narration of the 9-sentence script with restart OFF (default): peak memory per sentence and overall
  4 length rule  which approved test sentences the new 5.5 s / 70-character warning marks, per voice and style (nothing is changed)
  5 regression   tests/test_narration.py, tests/test_milestone2.py, planner suite, adapter check identical to pre-B1;
                 reel_002 baseline: project, locked baseline file and its approved exports unchanged (no render - not authorised);
                 original app, environments, model cache and all earlier evidence unchanged
Evidence: tests/acceptance/M4_gateB/B1/B1.2_corrections_<date_time>/ (summary.md, results.json, before_after/*.wav)"""
import os, sys, json, time, hashlib, subprocess, shutil, re, wave, glob
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ENG = os.path.join(ROOT, "engine"); sys.path.insert(0, ENG)
HOME = os.path.expanduser("~"); PY = sys.executable; os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
B1 = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1"); OUT = os.path.join(B1, "B1.2_corrections_" + time.strftime("%Y%m%d_%H%M%S"))
os.makedirs(os.path.join(OUT, "before_after")); os.makedirs(os.path.join(OUT, "work"))
B12 = sorted(glob.glob(os.path.join(B1, "B1.2_speed_*")))[0]
LOG, R = [], dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), checks=[])
def log(m): line = f"[{time.strftime('%H:%M:%S')}] {m}"; print(line, flush=True); LOG.append(line)
def check(name, ok, detail=""): R["checks"].append(dict(name=name, passed=bool(ok), detail=detail)); log(("PASS " if ok else "FAIL ") + name + (f" - {json.dumps(detail, ensure_ascii=False)[:220]}" if detail != "" else ""))
def load(p): return json.load(open(p, encoding="utf-8"))
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def sh(cmd, env=None, timeout=7200): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, **(env or {})), timeout=timeout)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def read_i16(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.int32), w.getframerate()
def fingerprint(path):
    if not os.path.exists(path): return None
    if os.path.isfile(path): return dict(files=1, sha256=sha(path))
    h, n = hashlib.sha256(), 0
    for dp, dn, fn in os.walk(path):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            try: st = os.lstat(p)
            except OSError: continue
            h.update(f"{os.path.relpath(p, path)}|{st.st_size}|{int(st.st_mtime)}\n".encode()); n += 1
    return dict(files=n, sha256=h.hexdigest())
def level(src, dst):
    """The B1.2 levelling (gain to -14 LUFS + peak limiter), so before and after are compared the same way."""
    def m(p):
        e = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+)", e)[-1])
    I0, _ = m(src); sh(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", f"volume={-14.0 - I0}dB,alimiter=limit=0.84:level=false:attack=5:release=50,aresample=48000",
                        "-ac", "1", "-c:a", "pcm_s16le", dst]); I, TP = m(dst); return dict(raw_lufs=I0, lufs=I, true_peak_db=TP)
EXP = sorted(glob.glob(os.path.join(ROOT, "exports", "2026-11-03_reel_002_development_jagan_for_andhra_*_v23*")))
WATCH = {"original_Reel_Studio": os.path.join(os.path.dirname(ROOT), "Reel Studio"), "reel_002_project": os.path.join(ROOT, "projects", "2026-11-03_reel_002_development"),
         "reel_002_locked_baseline_file": os.path.join(ROOT, "tests", "baseline_reel_002.json"), "checkpoint_sh": os.path.join(ROOT, "checkpoint.sh"),
         "reelstudio_env": os.path.join(HOME, ".venvs", "reelstudio"), "rs_asr_env": os.path.join(HOME, ".venvs", "rs_asr"), "rs_tts_env": os.path.join(HOME, ".venvs", "rs_tts"),
         "voice_model_cache": os.path.join(HOME, ".cache", "rs_tts_hf"), "B1.1_evidence": os.path.join(B1, "run_20261110_164955"), "B1.2_evidence": B12,
         "B1.2_final_evidence": sorted(glob.glob(os.path.join(B1, "B1.2_final_*")))[0]}
for p in EXP: WATCH["reel_002_export_" + os.path.basename(p)[-40:]] = p

log("B1.2 corrections tests (no reel is rendered)"); FP0 = {k: fingerprint(p) for k, p in WATCH.items()}
ref = load(os.path.join(B1, "fingerprints_before.json"))
for k in ("original_Reel_Studio", "reel_002_project"): check(f"isolation since B1 start: {k} unchanged", ref.get(k) == FP0.get(k))
for line in open(os.path.join(B1, "before_B12_corrections.txt"), encoding="utf-8"):
    if line.startswith("#") or not line.strip(): continue
    h, f = line.split()[:2]; check(f"backup: {f}.preB12 matches its recorded checksum", sha(os.path.join(ROOT, f + ".preB12")) == h)
C = load(os.path.join(ENG, "tts.json"))
check("settings: restart off by default, edge fade off by default (approved audio), default speed 1.0, atempo, 8 GB stop",
      C["memory"]["restart_every"] == 0 and C.get("edge_fade_ms", 0) == 0 and C["speed"]["default"] == 1.0 and C["speed"]["method"] == "atempo" and C["memory"]["limit_gb"] == 8.0)

# 1 continuity (exact samples) ------------------------------------------------------------------------------------------------------
log("STEP 1 continuity check with exact sample positions (re-made from the cache)")
for voice, style in (("prakash", "news"), ("lalitha", "documentary")):
    d = os.path.join(ROOT, "projects", f"zz_gateB_b12r_{voice}_{style}"); b = os.path.join(d, "build")
    r = sh([PY, "engine/narrate.py", d]); TL = load(os.path.join(b, "narration_timeline.json")); ref12 = load(os.path.join(B12, "answer_key", f"{voice}_{style}_1.00x_timeline.json"))
    x, sr = read_i16(os.path.join(b, "narration.wav")); S = TL["sentences"]
    joins = [int(np.abs(x[a["e_sample"]: c["s_sample"]]).max()) for a, c in zip(S, S[1:])]
    check(f"{voice}/{style}: audio still identical to the approved B1.2 take", r.returncode == 0 and TL["generated"]["spoken"] == 0 and TL["audio_sha256"] == ref12["audio_sha256"])
    check(f"{voice}/{style}: continuity (exact samples) - every pause between sentences is digital silence", all(j == 0 for j in joins), joins)
    check(f"{voice}/{style}: sentence positions are whole samples and end exactly where the pause begins", all(c["s_sample"] - a["e_sample"] == int(round(TL["pause_s"] * sr)) for a, c in zip(S, S[1:])))
    R.setdefault("continuity", {})[f"{voice}/{style}"] = dict(join_max=joins, edge_tail_db=[round(20 * np.log10(max(1, int(np.abs(x[a["e_sample"] - int(0.01 * sr): a["e_sample"]]).max())) / 32768), 1) for a in S])

# 2 fade test ------------------------------------------------------------------------------------------------------------------------
log("STEP 2 10 ms fade test (from the approved sentences; no model load)")
cf = os.path.join(OUT, "work", "tts_fade10.json"); Cf = dict(C, edge_fade_ms=10); save(Cf, cf); FADE = {}
for voice, style in (("prakash", "news"), ("prakash", "documentary"), ("lalitha", "news"), ("lalitha", "documentary")):
    src = os.path.join(ROOT, "projects", f"zz_gateB_b12_{voice}_{style}"); d = os.path.join(ROOT, "projects", f"zz_gateB_b12f_{voice}_{style}"); b = os.path.join(d, "build")
    if os.path.exists(d): check(f"fade {voice}/{style}: new test project", False, "already exists - nothing changed"); continue
    os.makedirs(os.path.join(d, "inputs")); shutil.copytree(os.path.join(src, "build", "narration_cache"), os.path.join(b, "narration_cache"))
    P = load(os.path.join(src, "project.json")); P.update(brief=f"Gate B1.2 fade test ({voice}/{style}) - not for publishing", history=[]); P.pop("narration_hash", None); save(P, os.path.join(d, "project.json"))
    shutil.copy(os.path.join(src, "inputs", "script.txt"), os.path.join(d, "inputs", "script.txt"))
    sh([PY, "engine/rs.py", "script", d, os.path.join(d, "inputs", "script.txt")]); sh([PY, "engine/rs.py", "script-approve", d, "--checked"])
    r = sh([PY, "engine/narrate.py", d], env=dict(RS_TTS_CONFIG=cf)); TF = load(os.path.join(b, "narration_timeline.json"))
    before = os.path.join(B12, "work", f"{voice}_{style}_1.00x_raw.wav"); after = os.path.join(b, "narration.wav")
    xb, sr = read_i16(before); xa, _ = read_i16(after); S = TF["sentences"]; n10 = int(round(0.010 * sr)); thr = int(32768 * 10 ** (C["trim_db"] / 20))
    inner = all(np.array_equal(xa[a["s_sample"] + n10: a["e_sample"] - n10], xb[a["s_sample"] + n10: a["e_sample"] - n10]) for a in S)
    pauses = all(np.array_equal(xa[a["e_sample"]: c["s_sample"]], xb[a["e_sample"]: c["s_sample"]]) for a, c in zip(S, S[1:]))
    edge_max = max(max(int(np.abs(xb[a["s_sample"]: a["s_sample"] + n10]).max()), int(np.abs(xb[a["e_sample"] - n10: a["e_sample"]]).max())) for a in S)
    lb, la = level(before, os.path.join(OUT, "work", f"before_{voice}_{style}.wav")), level(after, os.path.join(OUT, "work", f"after_{voice}_{style}.wav"))
    check(f"fade {voice}/{style}: made from the approved sentences (no model load), same length", r.returncode == 0 and TF["generated"]["spoken"] == 0 and len(xa) == len(xb))
    check(f"fade {voice}/{style}: every sample outside the 10 ms edges identical (no speech cut, pronunciation unchanged)", inner)
    check(f"fade {voice}/{style}: pauses and sentence positions identical (alignment unchanged)", pauses)
    check(f"fade {voice}/{style}: faded edges were inside the quiet margin (max {edge_max} <= speech threshold {thr})", edge_max <= thr, edge_max)
    check(f"fade {voice}/{style}: loudness after levelling within 0.05 LU of before", abs(la["raw_lufs"] - lb["raw_lufs"]) <= 0.05 and abs(la["lufs"] + 14) <= 0.5 and la["true_peak_db"] <= -1.0,
          dict(before=lb, after=la))
    FADE[f"{voice}/{style}"] = dict(before=lb, after=la, edge_max_before=edge_max, threshold=thr,
                                    edges_after=[(int(xa[a["s_sample"]]), int(xa[a["e_sample"] - 1])) for a in S], edges_before=[(int(xb[a["s_sample"]]), int(xb[a["e_sample"] - 1])) for a in S])
    if (voice, style) in (("prakash", "news"), ("lalitha", "documentary")):
        shutil.copy(os.path.join(OUT, "work", f"before_{voice}_{style}.wav"), os.path.join(OUT, "before_after", f"{voice}_{style}_A_before_approved.wav"))
        shutil.copy(os.path.join(OUT, "work", f"after_{voice}_{style}.wav"), os.path.join(OUT, "before_after", f"{voice}_{style}_B_after_fade10ms.wav"))
R["fade"] = FADE

# 3 memory (restart off) -------------------------------------------------------------------------------------------------------------
log("STEP 3 memory: one real narration, restart off (voice model loads once; about 1-2 minutes)")
d = os.path.join(ROOT, "projects", "zz_gateB_b12m_lalitha_documentary"); b = os.path.join(d, "build")
if os.path.exists(d): check("memory: new test project", False, "already exists - nothing changed")
else:
    src = os.path.join(ROOT, "projects", "zz_gateB_b12_lalitha_documentary"); os.makedirs(b); os.makedirs(os.path.join(d, "inputs"))
    P = load(os.path.join(src, "project.json")); P.update(brief="Gate B1.2 memory test (restart off) - not for publishing", history=[]); P.pop("narration_hash", None); save(P, os.path.join(d, "project.json"))
    shutil.copy(os.path.join(src, "inputs", "script.txt"), os.path.join(d, "inputs", "script.txt"))
    r1 = sh([PY, "engine/rs.py", "script", d, os.path.join(d, "inputs", "script.txt")]); open(os.path.join(OUT, "length_warnings_lalitha_documentary.txt"), "w", encoding="utf-8").write(r1.stdout)
    r2 = sh([PY, "engine/rs.py", "script-approve", d]); check("length rule: approval refused until the flagged long sentences are reviewed (--checked)", r2.returncode != 0 and "long sentence" in (r2.stderr + r2.stdout))
    sh([PY, "engine/rs.py", "script-approve", d, "--checked"])
    t = time.time(); r = sh([PY, "engine/narrate.py", d], env=dict(RS_EVENTS="1")); secs = round(time.time() - t, 1)
    if r.returncode: check("memory: narration with restart off", False, r.stdout[-300:] + r.stderr[-300:])
    else:
        TM = load(os.path.join(b, "narration_timeline.json")); G = TM["generated"]; ref12 = load(os.path.join(B12, "answer_key", "lalitha_documentary_1.00x_timeline.json"))
        per = [(round(s.get("rss_peak_bytes", 0) / 1e9, 2), s["audio_s"]) for s in G["per_sentence"]]
        R["memory"] = dict(peak_rss_gb=TM["memory"]["peak_rss_gb"], load_s=G["load_s"], seconds=secs, batches=G.get("batches"), per_sentence_peak_gb_and_audio_s=per,
                           long_sentence_warnings=[s["i"] + 1 for s in TM["sentences"] if s.get("long")])
        check("memory: one model load (restart off), peak under the 8 GB stop", len(G.get("batches", [])) == 1 and TM["memory"]["peak_rss_gb"] <= 8.0, R["memory"]["peak_rss_gb"])
        check("memory run: audio identical to the approved B1.2 take (restart off gives the same result)", TM["audio_sha256"] == ref12["audio_sha256"])

# 4 length rule on the approved test sentences ----------------------------------------------------------------------------------------
import narration_script as NS
N0 = load(os.path.join(ROOT, "projects", "zz_gateB_b12_prakash_news", "build", "narration.json")); LEN = {}
for voice in ("prakash", "lalitha"):
    for style in ("news", "documentary"):
        LEN[f"{voice}/{style}"] = [dict(line=i + 1, est_speech_s=NS.length_check(dict(narrator=voice, narrator_style=style), l["say"])[0],
                                        chars=NS.length_check(dict(narrator=voice, narrator_style=style), l["say"])[1],
                                        flagged=NS.length_check(dict(narrator=voice, narrator_style=style), l["say"])[2]) for i, l in enumerate(N0["lines"])]
R["length_rule"] = LEN; check("length rule: approved B1.2 texts unchanged (nothing split or rewritten)", NS.fingerprint(N0["lines"]) == N0["approved_hash"])

# 5 regression -------------------------------------------------------------------------------------------------------------------------
log("STEP 5 regression tests (offline)")
r = sh([PY, "tests/test_narration.py", "--out", OUT], timeout=1800); open(os.path.join(OUT, "test_narration.txt"), "w").write(r.stdout + r.stderr)
tn = load(os.path.join(OUT, "test_narration.json")) if os.path.exists(os.path.join(OUT, "test_narration.json")) else {}
check("offline tests: tests/test_narration.py", r.returncode == 0, f"{tn.get('passed')}/{tn.get('total')}")
r = sh([PY, "tests/test_milestone2.py"], timeout=900); check("offline tests: tests/test_milestone2.py", r.returncode == 0 and "ALL PASSED" in r.stdout, r.stdout.strip().splitlines()[-1:])
r = sh([PY, "tests/test_plan_checks.py"], timeout=900); check("offline tests: planner suite", r.returncode == 0, (r.stdout.strip().splitlines() or [""])[-1])
ra, rb = sh([PY, "engine/adapter.py.preB1", "check"]), sh([PY, "engine/adapter.py", "check"]); check("legacy: adapter check identical to pre-B1", ra.stdout == rb.stdout and ra.returncode == rb.returncode)
FP1 = {k: fingerprint(p) for k, p in WATCH.items()}
for k in WATCH: check(f"preserved: {k} unchanged", FP0[k] == FP1[k] and FP1[k] is not None, (FP1[k] or {}).get("sha256", "missing")[:12])
check("lock: no heavy-model lock left behind", not os.path.exists(os.path.join(ROOT, ".heavy_model.lock")) or not open(os.path.join(ROOT, ".heavy_model.lock")).read().strip())

n = sum(c["passed"] for c in R["checks"]); R.update(finished=time.strftime("%Y-%m-%d %H:%M:%S"), result="PASS" if n == len(R["checks"]) else "FAIL")
save(R, os.path.join(OUT, "results.json")); open(os.path.join(OUT, "log.txt"), "w").write("\n".join(LOG) + "\n")
open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8").write("\n".join([f"# B1.2 corrections", "", f"{R['started']} -> {R['finished']} | **{R['result']}** ({n}/{len(R['checks'])})", "",
    "No reel was rendered. The fade is a TEST setting here; the default stays off (approved audio) until you accept it.", "",
    "| Check | Result | Detail |", "| --- | --- | --- |"] + [f"| {c['name']} | {'PASS' if c['passed'] else 'FAIL'} | {json.dumps(c['detail'], ensure_ascii=False)[:160]} |" for c in R["checks"]]) + "\n")
log(f"FINAL: {R['result']} ({n}/{len(R['checks'])}) - evidence {os.path.relpath(OUT, ROOT)}/summary.md ; listening pairs in before_after/"); sys.exit(0 if R["result"] == "PASS" else 2)
