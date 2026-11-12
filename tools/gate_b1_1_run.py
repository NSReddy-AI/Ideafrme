"""Gate B1.1 evidence run (build + offline tests + isolated narration tests). NO reel is rendered.
Run on the Mac from the dev folder:
  ~/.venvs/reelstudio/bin/python tools/gate_b1_1_run.py
Steps (each result recorded; the run continues past a failed check so the full picture is in the evidence):
  1 backups        every changed file's pre-B1 copy still matches its recorded checksum; current checksums recorded
  2 fingerprints   original Reel Studio folder, reel_002 project, the reelstudio / rs_asr / rs_tts environments, the voice-model cache
  3 compile        every engine file compiles
  4 offline tests  tests/test_narration.py (fake voice; legacy = identical to pre-B1), tests/test_milestone2.py, planner suite
  5 AI narration   2 test projects (Prakash News, Lalitha Documentary), 3 sentences each, REAL voice model, offline, memory watched,
                   then speech-to-text check; a re-run proves the cache; a 1.15x technical check (pitch / pauses) - no listening test
  6 recorded       the recorded path with a STAND-IN file (the AI test narration); your own recording is tested in B1.3
  7 none           narration none -> text + music, no disclosure
  8 stills         disclosure position previews (tools/gate_b1_disclosure_stills.py)
  9 isolation      fingerprints from step 2 unchanged; environments and model cache unchanged
Test scripts in step 5 are approved by this runner for testing only - they are not approved for publishing.
Evidence: tests/acceptance/M4_gateB/B1/run_<date_time>/ (summary.md, results.json, narration wav + json per project)."""
import os, sys, json, time, hashlib, subprocess, shutil, glob, wave
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ENG = os.path.join(ROOT, "engine"); sys.path.insert(0, ENG)
HOME = os.path.expanduser("~"); PY = sys.executable
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1", "run_" + time.strftime("%Y%m%d_%H%M%S")); os.makedirs(OUT)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"   # no new .pyc files inside any environment
R = dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), checks=[], steps={}); LOG = []
def log(m): line = f"[{time.strftime('%H:%M:%S')}] {m}"; print(line, flush=True); LOG.append(line)
def check(name, ok, detail=""): R["checks"].append(dict(name=name, passed=bool(ok), detail=detail)); log(("PASS " if ok else "FAIL ") + name + (f" - {json.dumps(detail, ensure_ascii=False)[:220]}" if detail != "" else ""))
def load(p): return json.load(open(p, encoding="utf-8"))
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def sh(cmd, env=None, timeout=3600): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, **(env or {})), timeout=timeout)
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
         "rs_tts_env": os.path.join(HOME, ".venvs", "rs_tts"), "voice_model_cache": os.path.join(HOME, ".cache", "rs_tts_hf")}
CHANGED = ["engine/voice.py", "engine/te_numbers.py", "engine/slides.py", "engine/mix.py", "engine/frame.py", "engine/qa.py", "engine/adapter.py", "engine/rs.py", "engine/common.py", "CLAUDE.md"]
NEW = ["engine/tts.json", "engine/tts_worker.py", "engine/narrate.py", "engine/narration_script.py", "engine/narration_align.py", "tests/test_narration.py",
       "tools/gate_b1_disclosure_stills.py", "tools/gate_b1_1_run.py"]

# 1 backups ---------------------------------------------------------------------------------------------------------------------
log("STEP 1 backups"); rows = []
for line in open(os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1", "before.txt"), encoding="utf-8"):
    if line.startswith("#") or not line.strip(): continue
    h, f = line.split()[:2]; bk = os.path.join(ROOT, f + ".preB1")
    hb = hashlib.sha256(open(bk, "rb").read()).hexdigest() if os.path.exists(bk) else None
    hn = hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
    rows.append(dict(file=f, before_sha256=h, backup_sha256=hb, backup_ok=hb == h, now_sha256=hn, changed=hn != h))
save(rows, os.path.join(OUT, "backups.json"))
check("backups: every pre-B1 backup matches its recorded checksum", all(r["backup_ok"] for r in rows), [r["file"] for r in rows if not r["backup_ok"]])
check("backups: exactly the planned files changed", sorted(r["file"] for r in rows if r["changed"]) == sorted(CHANGED), [r["file"] for r in rows if r["changed"]])
R["steps"]["files"] = dict(changed=CHANGED, new=NEW, new_present={f: os.path.exists(os.path.join(ROOT, f)) for f in NEW},
                           new_sha256={f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() for f in NEW if os.path.exists(os.path.join(ROOT, f))})

# 2 fingerprints ----------------------------------------------------------------------------------------------------------------
log("STEP 2 fingerprints"); FP0 = {k: fingerprint(p) for k, p in WATCH.items()}; R["steps"]["fingerprints_before"] = FP0
a22 = sorted(glob.glob(os.path.join(ROOT, "tests", "acceptance", "M4_gateA2_2", "20*", "results.json")))
if a22:
    ref = load(a22[-1])["steps"]["1 pre-checks"]["fingerprints"]
    for k in ("original_Reel_Studio", "reelstudio_env", "rs_asr_env"):
        check(f"isolation since Gate A2.2: {k} unchanged", ref.get(k) == FP0.get(k), dict(a22=ref.get(k, {}).get("sha256", "")[:12], now=(FP0.get(k) or {}).get("sha256", "")[:12]))
b1 = os.path.join(ROOT, "tests", "acceptance", "M4_gateB", "B1", "fingerprints_before.json")
if os.path.exists(b1):
    ref = load(b1)
    for k in ("original_Reel_Studio", "reel_002_project"): check(f"isolation since B1 start: {k} unchanged", ref.get(k) == FP0.get(k), ref.get(k))

# 3 compile ---------------------------------------------------------------------------------------------------------------------
r = sh([PY, "-m", "py_compile"] + glob.glob(os.path.join(ENG, "*.py")) + [os.path.join(ROOT, "tests", "test_narration.py")])
check("compile: every engine file", r.returncode == 0, r.stderr[-300:])

# 4 offline tests ---------------------------------------------------------------------------------------------------------------
log("STEP 4 offline tests (about 1-2 minutes)")
r = sh([PY, "tests/test_narration.py", "--out", OUT], timeout=1200); open(os.path.join(OUT, "test_narration.txt"), "w").write(r.stdout + r.stderr)
tn = load(os.path.join(OUT, "test_narration.json")) if os.path.exists(os.path.join(OUT, "test_narration.json")) else {}
check("offline tests: tests/test_narration.py", r.returncode == 0, f"{tn.get('passed')}/{tn.get('total')} passed")
r = sh([PY, "tests/test_milestone2.py"], timeout=900); open(os.path.join(OUT, "test_milestone2.txt"), "w").write(r.stdout + r.stderr)
check("offline tests: tests/test_milestone2.py (settings, title + frame for every brand)", r.returncode == 0 and "ALL PASSED" in r.stdout, r.stdout.strip().splitlines()[-1:] )
r = sh([PY, "tests/test_plan_checks.py"], timeout=900); open(os.path.join(OUT, "test_plan_checks.txt"), "w").write(r.stdout + r.stderr)
check("offline tests: planner suite (tests/test_plan_checks.py)", r.returncode == 0, (r.stdout.strip().splitlines() or [""])[-1])

# 5 AI narration with the real voice model ---------------------------------------------------------------------------------------
SCRIPT = ["అక్కచెల్లెమ్మలకు 31 లక్షల ఇళ్ల పట్టాలు ఇచ్చారు.", "సొంతింటి కల నెరవేర్చేలా 17,000 జగనన్న కాలనీలు.", "పేదవాడి ఆరోగ్యానికి 10,000 విలేజ్ క్లినిక్‌లు."]
import rs
def test_project(slug, **narr):
    d = os.path.join(ROOT, "projects", f"zz_gateB_{slug}")
    if not os.path.exists(d):
        os.makedirs(os.path.join(d, "build")); os.makedirs(os.path.join(d, "inputs"))
        save(dict(brand="jagan_for_andhra", platform="instagram", style="documentary", provider=None, brief=f"Gate B1 test project ({slug}) - not for publishing",
                  video=None, title_seconds=2.0, hook=dict(line1="", line2="", line3="", tag_top="", tag_bottom=""), title=["పరీక్ష", "Gate B1"],
                  title_person=None, title_bg=None, face_tracking=False, approved=False, status="test", history=[]), os.path.join(d, "project.json"))
    return d
def events(r): return [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
def run_narrate(d):
    t = time.time(); r = sh([PY, "engine/adapter.py", "narrate", d], timeout=3600); ev = events(r)
    return r.returncode, ev, round(time.time() - t, 1), r.stderr
AI = {}
for slug, voice, style in (("ai_news", "prakash", "news"), ("ai_documentary", "lalitha", "documentary")):
    log(f"STEP 5 AI narration: {voice} / {style} (real voice model, offline)"); d = test_project(slug)
    sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.0"])
    open(os.path.join(d, "inputs", "script.txt"), "w", encoding="utf-8").write("\n".join(SCRIPT) + "\n")
    r1 = sh([PY, "engine/rs.py", "script", d, os.path.join(d, "inputs", "script.txt")]); r2 = sh([PY, "engine/rs.py", "script-approve", d])
    open(os.path.join(OUT, f"{slug}_script.txt"), "w", encoding="utf-8").write(r1.stdout + "\n" + r2.stdout + r2.stderr)
    check(f"{slug}: test script prepared and approved (numbers spoken as words)", r2.returncode == 0, r2.stderr[-200:])
    rc, ev, secs, err = run_narrate(d); done = ev[-1] if ev else {}
    errs = [e for e in ev if e.get("event") == "error"]; b = os.path.join(d, "build")
    check(f"{slug}: narration made by the real voice model, offline", rc == 0 and done.get("ok"), errs[:1] or err[-300:])
    if rc == 0:
        TL, CK = load(os.path.join(b, "narration_timeline.json")), load(os.path.join(b, "narration_check.json"))
        mem = TL["memory"]["peak_rss_gb"] if TL["generated"]["spoken"] else "model not loaded"; AI[slug] = dict(seconds=secs, duration=TL["duration"], memory_gb=mem, warned=TL["memory"]["warned"],
                                                           load_s=TL["generated"]["load_s"], per_sentence=[(x["audio_s"], x["synth_s"]) for x in TL["generated"]["per_sentence"]],
                                                           cer_total=CK["cer_total"], to_check=CK["to_check"], sync=CK["first_caption_vs_sentence_start_s"], offline=TL["offline"], ollama=TL["ollama"])
        if TL["memory"].get("model_loaded", TL["generated"]["spoken"] > 0):
            check(f"{slug}: peak memory under 8 GB", mem <= 8.0, f"{mem} GB")
        else:
            log(f"INFO {slug}: memory - model not loaded (every sentence came from the cache); no memory measurement in this run")
        check(f"{slug}: offline (no network attempt; voice process blocks outside connections)", "TTS_NETWORK_BLOCKED" not in json.dumps(ev), TL["offline"])
        check(f"{slug}: round-trip character error <= 20%", CK["cer_total"] <= 0.20, CK["cer_total"])
        check(f"{slug}: every caption starts within 0.1 s of its sentence", CK["max_sync_offset_s"] <= 0.1, CK["first_caption_vs_sentence_start_s"])
        for f in ("narration.wav", "narration_timeline.json", "narration_check.json", "narration_words.json", "narration.json"): shutil.copy(os.path.join(b, f), os.path.join(OUT, f"{slug}_{f}"))
        rc2, ev2, secs2, _ = run_narrate(d); TL2 = load(os.path.join(b, "narration_timeline.json"))
        check(f"{slug}: re-run uses the cache (nothing spoken again, same audio)", rc2 == 0 and TL2["generated"]["spoken"] == 0 and TL2["audio_sha256"] == TL["audio_sha256"], dict(seconds=secs2))
        AI[slug]["rerun_seconds"] = secs2
        if slug == "ai_news":   # technical speed check on the real voice (no listening comparison: that is B1.2)
            import narrate as NR; have = {m: NR.filter_available(m) for m in ("rubberband", "atempo")}; AI[slug]["ffmpeg_filters"] = have
            log(f"FFmpeg speed filters on this Mac: {have}")
            for m in [x for x in ("rubberband", "atempo") if have[x]]:
                sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.15", "--method", m]); rc3, ev3, secs3, _ = run_narrate(d)
                T3 = load(os.path.join(b, "narration_timeline.json")); S0, S3 = TL["sentences"], T3["sentences"]
                ratio = [round(a["speech_s"] / c["speech_s"], 3) for a, c in zip(S0, S3)]; gaps = [round(c["s"] - a["e"], 3) for a, c in zip(S3, S3[1:])]
                check(f"speed 1.15x {m} (real voice, technical): speech 1.15x shorter, pauses unchanged, nothing re-spoken",
                      rc3 == 0 and all(abs(x - 1.15) <= 0.04 for x in ratio) and all(abs(g - 0.35) <= 0.002 for g in gaps) and T3["generated"]["spoken"] == 0,
                      dict(ratio=ratio, pauses=gaps, errors=[e.get("code") for e in ev3 if e.get("event") == "error"]))
                AI[slug][f"speed_1_15_{m}"] = dict(ratio=ratio, pauses=gaps); shutil.copy(os.path.join(b, "narration.wav"), os.path.join(OUT, f"{slug}_speed1.15_{m}_TECHNICAL.wav"))
            if not have["rubberband"]:
                sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.15", "--method", "rubberband"]); rc4, ev4, _, _ = run_narrate(d)
                check("speed with rubberband on this Mac: refused clearly (SPEED_METHOD_UNAVAILABLE), nothing changed",
                      rc4 != 0 and "SPEED_METHOD_UNAVAILABLE" in [e.get("code") for e in ev4 if e.get("event") == "error"], [e.get("code") for e in ev4 if e.get("event") == "error"])
            sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style, "--speed", "1.0"]); run_narrate(d)   # back to the default
R["steps"]["ai_narration"] = AI

# 6 recorded (stand-in) ----------------------------------------------------------------------------------------------------------
log("STEP 6 recorded narration path (stand-in file)"); d = test_project("recorded"); src = os.path.join(ROOT, "projects", "zz_gateB_ai_news", "build", "narration.wav")
if os.path.exists(src):
    shutil.copy(src, os.path.join(d, "inputs", "standin_recording.wav"))
    sh([PY, "engine/rs.py", "narration", d, "recorded", "--style", "news", "--file", "inputs/standin_recording.wav"])
    open(os.path.join(d, "inputs", "script.txt"), "w", encoding="utf-8").write("\n".join(SCRIPT) + "\n")
    sh([PY, "engine/rs.py", "script", d, os.path.join(d, "inputs", "script.txt")]); sh([PY, "engine/rs.py", "script-approve", d])
    rc, ev, secs, err = run_narrate(d); b = os.path.join(d, "build")
    ok = rc == 0 and ev and ev[-1].get("ok")
    TR = load(os.path.join(b, "narration_timeline.json")) if ok else {}; CK = load(os.path.join(b, "narration_check.json")) if ok else {}
    check("recorded (stand-in): sentence times found by speech-to-text, captions timed", ok and TR.get("aligned") and all(s.get("s") is not None for s in TR.get("sentences", [])),
          dict(cer=CK.get("cer_total"), errors=[e.get("code") for e in ev if e.get("event") == "error"]))
    R["steps"]["recorded_standin"] = dict(seconds=secs, cer_total=CK.get("cer_total"), sentences=[(s.get("s"), s.get("e")) for s in TR.get("sentences", [])])
else: check("recorded (stand-in): needs the AI news narration from step 5", False)

# 7 none + disclosure on/off in the frame ----------------------------------------------------------------------------------------
log("STEP 7 narration none / disclosure on-off"); d = test_project("none"); sh([PY, "engine/rs.py", "narration", d, "none"])
r = sh([PY, "engine/voice.py", d]); check("none: voice.py -> text + music, no voice, no error", r.returncode == 0 and "text + music" in r.stdout, r.stdout[-120:])
for slug in ("ai_news", "recorded", "none"):
    dd = os.path.join(ROOT, "projects", f"zz_gateB_{slug}"); r = sh([PY, "engine/frame.py", dd]); LY = load(os.path.join(dd, "build", "layout.json"))
    want = slug.startswith("ai"); has = "ai_disclosure" in LY
    check(f"frame ({slug}): disclosure {'present and inside the safe area' if want else 'absent'}",
          r.returncode == 0 and has == want and not [i for i in LY["safe_area"]["issues"] if i["element"] == "ai_disclosure"], LY.get("ai_disclosure", {}).get("box"))
    shutil.copy(os.path.join(dd, "build", "layout.json"), os.path.join(OUT, f"{slug}_layout.json"))

# 8 stills ----------------------------------------------------------------------------------------------------------------------
log("STEP 8 disclosure stills"); r = sh([PY, "tools/gate_b1_disclosure_stills.py"], timeout=900)
check("stills: disclosure previews, all inside the safe area", r.returncode == 0 and "all inside safe area: True" in r.stdout, r.stdout.strip()[-160:])

# 9 isolation -------------------------------------------------------------------------------------------------------------------
log("STEP 9 isolation"); FP1 = {k: fingerprint(p) for k, p in WATCH.items()}; R["steps"]["fingerprints_after"] = FP1
for k in WATCH: check(f"isolation: {k} unchanged during this run", FP0[k] == FP1[k], (FP1[k] or {}).get("files"))
check("lock: no heavy-model lock left behind", not os.path.exists(os.path.join(ROOT, ".heavy_model.lock")) or not open(os.path.join(ROOT, ".heavy_model.lock")).read().strip())

# summary -----------------------------------------------------------------------------------------------------------------------
R["finished"] = time.strftime("%Y-%m-%d %H:%M:%S"); n = sum(c["passed"] for c in R["checks"]); R["result"] = "PASS" if n == len(R["checks"]) else "FAIL"
save(R, os.path.join(OUT, "results.json")); open(os.path.join(OUT, "log.txt"), "w").write("\n".join(LOG) + "\n")
L = [f"# Gate B1.1 evidence run", "", f"{R['started']} -> {R['finished']} | **{R['result']}** ({n}/{len(R['checks'])} checks)", "", "No reel was rendered. Test scripts were approved by this runner for testing only.", "",
     "| Check | Result | Detail |", "| --- | --- | --- |"] + [f"| {c['name']} | {'PASS' if c['passed'] else 'FAIL'} | {json.dumps(c['detail'], ensure_ascii=False)[:160]} |" for c in R["checks"]]
open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
log(f"FINAL: {R['result']} ({n}/{len(R['checks'])}) - evidence {os.path.relpath(OUT, ROOT)}/summary.md"); sys.exit(0 if R["result"] == "PASS" else 2)
