"""M4 product demonstration (B1.3 + B2 + B3): makes real sample reels end to end in Reel Studio_dev. Nothing is published.
Run on the Mac from the dev folder:   ~/.venvs/reelstudio/bin/python tools/demo_product.py [--skip-speaker]      (about 30-45 minutes)
Reels (each exported for Instagram, YouTube and Facebook, with QA):
  demo_news_prakash        AI narration, Prakash, News          - 9 approved lines (reel_002's approved captions, numbers as words)
  demo_documentary_lalitha AI narration, Lalitha, Documentary   - same approved lines
  demo_text_music          no narration: text + music slides from the same approved lines
  demo_recorded            your own recording - only if you put it at projects/demo_recorded/inputs/my_narration.wav (else skipped)
  demo_speaker_said        speaker reel through the planner (B3): "What jagan said" (work/said/source.mov, copied in) -> Telugu
                           speech-to-text -> local Qwen3 planner -> hook A approved FOR THE DEMO -> build -> render. Needs Ollama running.
Approvals made by this runner are DEMO approvals (marked in each project's history); the reels are for your review, not publishing.
Title pages reuse reel_002's approved hook, headline, photo and background. Safe-area sheets for every brand x platform (B2).
Summary: tests/acceptance/M4_product_demo/<date_time>/summary.md (+ results.json, log.txt). Exports in exports/."""
import os, sys, json, time, subprocess, shutil, hashlib, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ENG = os.path.join(ROOT, "engine"); sys.path.insert(0, ENG)
PY = sys.executable; os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; HOME = os.path.expanduser("~")
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_product_demo", time.strftime("%Y%m%d_%H%M%S")); os.makedirs(OUT)
LOG, R = [], dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), reels={}, issues=[])
def log(m): line = f"[{time.strftime('%H:%M:%S')}] {m}"; print(line, flush=True); LOG.append(line)
def load(p): return json.load(open(p, encoding="utf-8"))
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
def sh(cmd, timeout=7200): return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout)
def adapter(*args):
    r = sh([PY, "engine/adapter.py"] + list(args)); ev = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")]
    done = ev[-1] if ev else {}; errs = [e for e in ev if e.get("event") == "error"]
    return bool(done.get("ok")), done, errs, r
def fingerprint(path):
    if not os.path.exists(path): return None
    if os.path.isfile(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()
    h = hashlib.sha256()
    for dp, dn, fn in os.walk(path):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f); st = os.lstat(p); h.update(f"{os.path.relpath(p, path)}|{st.st_size}|{int(st.st_mtime)}\n".encode())
    return h.hexdigest()
WATCH = {"original_Reel_Studio": os.path.join(os.path.dirname(ROOT), "Reel Studio"), "reel_002_project": os.path.join(ROOT, "projects", "2026-11-03_reel_002_development"),
         "reel_002_baseline_file": os.path.join(ROOT, "tests", "baseline_reel_002.json"), "rs_tts_env": os.path.join(HOME, ".venvs", "rs_tts"),
         "rs_asr_env": os.path.join(HOME, ".venvs", "rs_asr"), "reelstudio_env": os.path.join(HOME, ".venvs", "reelstudio")}
FP0 = {k: fingerprint(p) for k, p in WATCH.items()}
R002 = load(os.path.join(ROOT, "projects", "2026-11-03_reel_002_development", "project.json"))
SCRIPT = open(os.path.join(ROOT, "projects", "zz_gateB_b12_prakash_news", "inputs", "script.txt"), encoding="utf-8").read()

def new_project(slug, style, **extra):
    d = os.path.join(ROOT, "projects", slug)
    if os.path.exists(os.path.join(d, "project.json")): log(f"{slug}: project exists - re-using it"); return d
    os.makedirs(os.path.join(d, "build"), exist_ok=True); os.makedirs(os.path.join(d, "inputs"), exist_ok=True)
    P = dict(brand="jagan_for_andhra", platform="instagram", style=style, provider=None, brief="M4 product demo - not for publishing", video=None, title_seconds=2.0,
             hook=R002["hook"], title=R002["title"], title_person="../2026-11-03_reel_002_development/" + R002["title_person"],
             title_bg="../2026-11-03_reel_002_development/" + R002["title_bg"], face_tracking=False, approved=True, status="demo",
             history=[f"{time.strftime('%Y-%m-%d %H:%M')} created by tools/demo_product.py (title page = reel_002's approved hook/headline)"])
    P.update(extra); save(P, os.path.join(d, "project.json")); open(os.path.join(d, "inputs", "notes.txt"), "a").close(); open(os.path.join(d, "inputs", "urls.txt"), "a").close()
    return d

def approve_script(d):
    open(os.path.join(d, "inputs", "script.txt"), "w", encoding="utf-8").write(SCRIPT)
    r1 = sh([PY, "engine/rs.py", "script", d, os.path.join(d, "inputs", "script.txt")]); r2 = sh([PY, "engine/rs.py", "script-approve", d, "--checked"])
    open(os.path.join(d, "build", "script_review.txt"), "w", encoding="utf-8").write(r1.stdout); return r2.returncode == 0

def render(slug, d, info):
    ok, done, errs, r = adapter("build", d)
    if not ok: info.update(build="FAILED", errors=[e.get("code") + ": " + e.get("message", "")[:300] for e in errs] or [r.stderr[-400:]]); log(f"{slug}: build FAILED {info['errors']}"); return
    info["build"] = dict(seconds=done.get("seconds"), layout=done.get("layout")); log(f"{slug}: edit built ({done.get('layout', {}).get('duration')} s)")
    ok, done, errs, r = adapter("render", d, "--all-platforms")
    info["render"] = dict(ok=ok, qa_passed=done.get("qa_passed"), seconds=done.get("seconds"), errors=[e.get("code") + ": " + e.get("message", "")[:300] for e in errs],
                          outputs=[dict(platform=o["platform"], file=os.path.relpath(o["path"], ROOT), qa_passed=o["qa_passed"], warnings=o.get("warnings", []),
                                        ai_label_required=o.get("ai_label_required")) for o in done.get("outputs", [])])
    for o in done.get("outputs", []):
        q = load(o["qa_report"]) if o.get("qa_report") and os.path.exists(o["qa_report"]) else {}
        o2 = next(x for x in info["render"]["outputs"] if x["platform"] == o["platform"]); o2["failed_checks"] = [c["name"] for c in q.get("checks", []) if not c["passed"]]
        o2.update(loudness=q.get("loudness_lufs"), true_peak=q.get("true_peak_db"), seconds=q.get("duration"), contact_sheet=os.path.relpath(q.get("contact_sheet", ""), ROOT) if q else None)
    log(f"{slug}: render {'ok' if ok else 'FAILED'} | QA {'PASS' if done.get('qa_passed') else 'not all passed'} | " + ", ".join(f"{o['platform']} {'PASS' if o['qa_passed'] else 'FAIL ' + str(o.get('failed_checks'))}" for o in info["render"]["outputs"]))

# 1-2 AI narration reels ---------------------------------------------------------------------------------------------------------
for slug, voice, style, pstyle in (("demo_news_prakash", "prakash", "news", "news_speech"), ("demo_documentary_lalitha", "lalitha", "documentary", "documentary")):
    log(f"{slug}: AI narration {voice}/{style}"); info = R["reels"].setdefault(slug, {}); d = new_project(slug, pstyle)
    sh([PY, "engine/rs.py", "narration", d, "ai", "--voice", voice, "--style", style]); info["script_approved_for_demo"] = approve_script(d)
    ok, done, errs, r = adapter("narrate", d)
    info["narration"] = dict(ok=ok, seconds=done.get("seconds"), duration=done.get("duration"), memory=done.get("memory"), cer=done.get("cer_total"),
                             to_check=[x.get("line") for x in (done.get("to_check") or [])], errors=[e.get("code") for e in errs])
    log(f"{slug}: narration {'ok' if ok else 'FAILED ' + str(info['narration']['errors'])} | {done.get('duration')} s | memory {done.get('memory', {}).get('peak_rss_gb') if done.get('memory') else '-'} GB | error {done.get('cer_total')}")
    if ok: render(slug, d, info)

# 3 no narration -------------------------------------------------------------------------------------------------------------------
slug = "demo_text_music"; log(f"{slug}: no narration (text + music)"); info = R["reels"].setdefault(slug, {}); d = new_project(slug, "documentary")
sh([PY, "engine/rs.py", "narration", d, "none"]); info["script_approved_for_demo"] = approve_script(d); render(slug, d, info)

# 4 recorded (only with a real recording) --------------------------------------------------------------------------------------------
rec = os.path.join(ROOT, "projects", "demo_recorded", "inputs", "my_narration.wav")
if os.path.exists(rec):
    slug = "demo_recorded"; log(f"{slug}: your recorded narration"); info = R["reels"].setdefault(slug, {}); d = new_project(slug, "documentary")
    sh([PY, "engine/rs.py", "narration", d, "recorded", "--style", "documentary", "--file", "inputs/my_narration.wav"]); info["script_approved_for_demo"] = approve_script(d)
    ok, done, errs, r = adapter("narrate", d); info["narration"] = dict(ok=ok, cer=done.get("cer_total"), to_check=done.get("to_check"), errors=[e.get("code") for e in errs])
    if ok: render(slug, d, info)
else:
    R["reels"]["demo_recorded"] = dict(skipped="no recording yet - record the 9 lines of projects/demo_text_music/inputs/script.txt and save as projects/demo_recorded/inputs/my_narration.wav")
    log("demo_recorded: skipped (no recording yet)")

# 5 speaker reel through the planner (B3) ----------------------------------------------------------------------------------------------
if "--skip-speaker" not in sys.argv:
    slug = "demo_speaker_said"; info = R["reels"].setdefault(slug, {}); src = os.path.join(os.path.dirname(ROOT), "work", "said", "source.mov")
    if not os.path.exists(src): info["skipped"] = "source video not found: work/said/source.mov"
    else:
        d = new_project(slug, "news_speech", video="inputs/source.mov", hook=dict(line1="", line2="", line3="", tag_top="", tag_bottom=""), title=["", ""], approved=False)
        if not os.path.exists(os.path.join(d, "inputs", "source.mov")): shutil.copy2(src, os.path.join(d, "inputs", "source.mov"))
        log(f"{slug}: transcribe + plan (Telugu speech-to-text about 10 minutes, then the local planner)")
        ok, done, errs, r = adapter("plan", d); info["plan"] = dict(ok=ok, seconds=done.get("seconds"), options=done.get("options"), cards=done.get("cards"), tag=done.get("tag"),
                                                                 problems=done.get("problems"), marked=done.get("marked"), errors=[e.get("code") + ": " + e.get("message", "")[:200] for e in errs])
        log(f"{slug}: plan {'ok' if ok else 'FAILED ' + str(info['plan']['errors'])}")
        if ok and not done.get("problems"):
            ok2, done2, errs2, _ = adapter("approve", d, "--choice", "A", "--checked"); info["approve"] = dict(ok=ok2, choice="A (DEMO approval by the runner)", errors=[e.get("code") for e in errs2])
            if ok2: render(slug, d, info)
        elif ok: info["approve"] = dict(ok=False, note="the plan has problems - left for your review (build/plan.md)")
else: R["reels"]["demo_speaker_said"] = dict(skipped="--skip-speaker")

# 6 safe-area sheets (B2) -----------------------------------------------------------------------------------------------------------------
log("B2 safe-area sheets"); r = sh([PY, "tools/safe_area_sheets.py"]); R["safe_area_sheets"] = r.stdout.strip().splitlines()[-12:]; open(os.path.join(OUT, "safe_area.txt"), "w").write(r.stdout + r.stderr)

import rs as RS
for k in list(R["reels"]):
    if os.path.exists(os.path.join(ROOT, "projects", k, "project.json")):
        dn, nx = RS.next_step(os.path.join(ROOT, "projects", k)); R["reels"][k]["workflow"] = dict(done=dn, next=nx)
FP1 = {k: fingerprint(p) for k, p in WATCH.items()}; R["preserved"] = {k: FP0[k] == FP1[k] for k in WATCH}
R["finished"] = time.strftime("%Y-%m-%d %H:%M:%S"); save(R, os.path.join(OUT, "results.json")); open(os.path.join(OUT, "log.txt"), "w").write("\n".join(LOG) + "\n")
L = ["# M4 product demo", "", f"{R['started']} -> {R['finished']}. Nothing published. Approvals by the runner are DEMO approvals.", "", "| Reel | Result | Exports (QA) |", "| --- | --- | --- |"]
for k, v in R["reels"].items():
    outs = ", ".join(f"{o['platform']} {'PASS' if o['qa_passed'] else 'FAIL ' + ','.join(o.get('failed_checks') or [])}" for o in (v.get("render") or {}).get("outputs", []))
    L.append(f"| {k} | {v.get('skipped') or ('rendered' if (v.get('render') or {}).get('ok') else 'see results.json')} | {outs or '-'} |")
L += ["", "## Workflow status per project (rs.py next)", ""] + [f"- **{k}**: " + " → ".join(v.get("workflow", {}).get("done", [])) + f" → next: {v.get('workflow', {}).get('next', '-')}" for k, v in R["reels"].items()]
L += ["", "Preserved: " + ", ".join(f"{k} {'unchanged' if v else 'CHANGED'}" for k, v in R["preserved"].items())]
open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
log(f"DONE - summary {os.path.relpath(OUT, ROOT)}/summary.md")
