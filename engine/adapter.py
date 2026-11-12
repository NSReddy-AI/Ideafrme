"""Adapter: the one door the app (FastAPI backend) uses to drive the engine. The engine scripts stay as they are.
Each step runs as its own process (a crash never takes the app down). The adapter reads the steps' JSON events
and gives the app: live progress (0-100), readable errors, versioned outputs (v1, v2 ...), and a QA pass/fail.

Python:
    from adapter import render_reel
    for ev in render_reel("2026-11-03_reel_002_development", platforms=["instagram", "youtube"]):
        print(ev)          # {"event":"progress","pct":37,...} ... last: {"event":"done","ok":true,"outputs":[...]}
CLI (one JSON event per line):
    python engine/adapter.py render <project> [--platform P ...] [--all-platforms] [--baseline tests/baseline_reel_002.json] [--no-version]
    python engine/adapter.py check
    python engine/adapter.py narrate <project>      (M4 B1: narration audio + caption timing + listening check)
    python engine/adapter.py plan <project> [--hook "l1 / l2 / l3 / h1 / h2"]   (M4 B3: transcribe if needed + plan; or add option D)
    python engine/adapter.py approve <project> --choice A|B|C|D [--checked]     (M4 B3)
    python engine/adapter.py build <project>        (M4 B3: build/edit.mp4 + edit_audio.wav from approved material only)
Rules: project.json is never changed except its history log; each platform gets its own export and QA report;
one render per project at a time (build/.render.lock); every job has its own temp folder."""
import os, sys, json, uuid, time, shutil, subprocess, tempfile, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, ENGINE, load, job_dir

WEIGHTS = dict(title=10, frame=5, assemble=70, qa=15)

class Busy(Exception): pass

def _lock(build):
    p = os.path.join(build, ".render.lock")
    if os.path.exists(p):
        try:
            pid = int(open(p).read().split()[0]); os.kill(pid, 0); raise Busy(f"project is already rendering (pid {pid})")
        except (ProcessLookupError, ValueError, IndexError): pass   # stale lock from a crashed run -> take it over
        except PermissionError: raise Busy("project is already rendering")
    with open(p, "w") as f: f.write(f"{os.getpid()} {time.time():.0f}")
    return p

def _next_version(project_dir, brand):
    base = os.path.basename(project_dir); found = [0]
    for f in glob.glob(os.path.join(ROOT, "exports", f"{base}_{brand}_*_v*.mp4")):
        v = f.rsplit("_v", 1)[-1][:-4]
        if v.isdigit(): found.append(int(v))
    return max(found) + 1

def _step(name, args, env, base_pct, span, platform, state):
    """Run one engine step; yield its events re-scaled to the whole job; return (ok, last_error, extra)."""
    p = subprocess.Popen([sys.executable, os.path.join(ENGINE, args[0])] + args[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, env=env, cwd=ROOT)
    err, extra = None, {}
    for line in p.stdout:
        line = line.strip()
        if not line.startswith("{"):
            if line: yield dict(event="log", step=name, platform=platform, message=line)
            continue
        try: ev = json.loads(line)
        except json.JSONDecodeError: yield dict(event="log", step=name, platform=platform, message=line); continue
        ev["step"] = name; ev["platform"] = platform
        if ev.get("event") == "progress":
            ev["step_pct"] = ev["pct"]; ev["pct"] = max(state["pct"], int(base_pct + span * ev["pct"] / 100)); state["pct"] = ev["pct"]
        if ev.get("event") == "error": err = ev
        if ev.get("event") in ("output", "qa"): extra.update(ev)
        yield ev
    stderr = p.stderr.read(); p.wait()
    if p.returncode not in (0, 2) or (p.returncode == 2 and name != "qa"):
        if not err: err = dict(event="error", step=name, platform=platform, code="STEP_CRASHED", message=stderr[-1500:] or f"exit {p.returncode}")
        return False, err, extra
    return True, None, extra

def render_reel(project, platforms=None, all_platforms=False, baseline=None, version=True):
    t0 = time.time(); job_id = uuid.uuid4().hex[:12]
    d = job_dir(project); pj = os.path.join(d, "project.json")
    if not os.path.exists(pj):
        yield dict(event="error", step="adapter", code="PROJECT_NOT_FOUND", message=f"project not found: {project}"); yield dict(event="done", ok=False, job_id=job_id); return
    P = load(pj); brand = load(os.path.join(ROOT, "brands", P["brand"], "brand.json"))
    pfs = list(platforms or (brand.get("default_platforms") if all_platforms else None) or [P["platform"]])
    unknown = [x for x in pfs if not os.path.exists(os.path.join(ROOT, "platforms", x + ".json"))]
    if unknown:
        yield dict(event="error", step="adapter", code="UNKNOWN_PLATFORM", message=f"unknown platform(s): {unknown}"); yield dict(event="done", ok=False, job_id=job_id); return
    build = os.path.join(d, "build")
    plan = os.path.join(build, "plan.json")   # a drafted plan must be approved by the user before anything is rendered
    if os.path.exists(plan):
        from planner import plan_hash
        PL_ = load(plan); why = None
        if not PL_.get("approved"): why = "the plan is not approved yet: python3 engine/planner.py <project> --approve A|B|C|D [--checked]"
        else:
            ch = PL_["creative"]["hooks"]["ABCDEFG".index(PL_["hook_choice"])]; hk = P.get("hook", {})
            same_page = [hk.get(k) for k in ("line1", "line2", "line3")] == [ch.get(k) for k in ("line1", "line2", "line3")] and list(P.get("title", [])) == list(ch.get("headline", []))
            if PL_.get("approved_hash") != plan_hash(PL_) or P.get("plan_hash") != PL_.get("approved_hash") or not same_page:
                why = "the plan or the title page changed after approval - approve it again"
        if why: yield dict(event="error", step="adapter", code="PLAN_NOT_APPROVED", message=why); yield dict(event="done", ok=False, job_id=job_id); return
    if P.get("narration") in ("ai", "recorded"):   # M4 B1: narrated reels need the approved text AND audio made from it
        bad = narration_ready(dict(P, _dir=d))
        if bad: yield dict(event="error", step="adapter", code=bad[0], message=bad[1]); yield dict(event="done", ok=False, job_id=job_id); return
    for f in ("edit.mp4", "edit_audio.wav"):
        if not os.path.exists(os.path.join(build, f)):
            yield dict(event="error", step="adapter", code="EDIT_MISSING", message=f"missing build/{f}: build the edit first"); yield dict(event="done", ok=False, job_id=job_id); return
    try: lock = _lock(build)
    except Busy as e:
        yield dict(event="error", step="adapter", code="BUSY", message=str(e)); yield dict(event="done", ok=False, job_id=job_id); return
    tmp = tempfile.mkdtemp(prefix=f"rs_{job_id}_")
    suffix = f"_v{_next_version(d, P['brand'])}" if version else ""
    outputs, ok, state = [], True, dict(pct=0)
    yield dict(event="start", job_id=job_id, project=project, platforms=pfs, version=suffix.lstrip("_") or None, pct=0)
    try:
        share = 100 / len(pfs)
        for i, pf in enumerate(pfs):
            env = dict(os.environ, RS_EVENTS="1", RS_PLATFORM=pf, RS_TMP=os.path.join(tmp, pf))
            base = i * share; steps = [("title", ["title.py", project])] if i == 0 else []   # the title page is the same on every platform
            steps += [("frame", ["frame.py", project]),
                      ("assemble", ["assemble.py", project, os.path.join(build, "edit.mp4"), os.path.join(build, "edit_audio.wav"), suffix])]
            out = os.path.join(ROOT, "exports", f"{os.path.basename(d)}_{P['brand']}_{pf}{suffix}.mp4")
            qa_args = ["qa.py", out, "--platform", pf, "--layout", os.path.join(build, "layout.json")] + (["--baseline", baseline] if baseline else [])
            steps.append(("qa", qa_args))
            total_w = sum(WEIGHTS[n] for n, _ in steps)
            for name, args in steps:
                span = share * WEIGHTS[name] / total_w
                if name == "qa" and os.path.exists(os.path.join(build, "layout.json")):   # keep this platform's layout next to its export
                    shutil.copy(os.path.join(build, "layout.json"), out.replace(".mp4", "_layout.json")); args[args.index("--layout") + 1] = out.replace(".mp4", "_layout.json")
                good, err, extra = yield from _step(name, args, env, base, span, pf, state)
                base += span
                if good and int(base) > state["pct"]:
                    state["pct"] = min(99, int(base)); yield dict(event="progress", step=name, platform=pf, pct=state["pct"], step_pct=100)
                if not good: ok = False; yield err; break
                if name == "qa":
                    rep = load(extra["report"]) if extra.get("report") else {}
                    shutil.copy(os.path.join(build, "cover_4k.jpg"), out.replace(".mp4", "_cover_4k.jpg"))
                    outputs.append(dict(platform=pf, path=out, cover=out.replace(".mp4", "_cover_4k.jpg"), qa_passed=bool(extra.get("passed")),
                                        qa_report=extra.get("report"), warnings=rep.get("warnings", [])))
                    if "narration" in P: outputs[-1]["ai_label_required"] = P["narration"] == "ai"   # M4 B1: platform AI-content label
            if not ok: break
        if ok:
            sys.path.insert(0, ENGINE); import rs
            j = dict(_dir=d); rs.log(j, f"rendered {suffix.lstrip('_') or 'unversioned'} for {', '.join(pfs)} (job {job_id})")
    finally:
        try: os.remove(lock)
        except OSError: pass
        shutil.rmtree(tmp, ignore_errors=True)
    passed = ok and all(o["qa_passed"] for o in outputs)
    yield dict(event="done", ok=ok, qa_passed=passed, job_id=job_id, seconds=round(time.time() - t0, 1), outputs=outputs, pct=100 if ok else None)

def narration_ready(j):
    """None if a narrated project may render, else (code, message). Approved script unchanged + narration made from it + audio unchanged."""
    import narration_script as NS, hashlib
    ok, code, msg, N = NS.verify(j)
    if not ok: return code, msg
    b = os.path.join(j["_dir"], "build"); tp, wav = os.path.join(b, "narration_timeline.json"), os.path.join(b, "narration.wav")
    if not (os.path.exists(tp) and os.path.exists(wav)): return "NARRATION_MISSING", "no narration audio yet: python3 engine/adapter.py narrate <project>"
    TL = load(tp)
    if TL.get("approved_hash") != N["approved_hash"]: return "NARRATION_AUDIO_STALE", "the narration was made from an older script - narrate again"
    if TL.get("mode") != j.get("narration") or (j.get("narration") == "ai" and (TL.get("voice") != j.get("narrator") or TL.get("style") != j.get("narrator_style")
                                                                                or abs(float(TL.get("speed", 1)) - float(j.get("narration_speed", TL.get("speed", 1)))) > 1e-9
                                                                                or (j.get("narration_speed_method") and float(TL.get("speed", 1)) != 1.0 and TL.get("speed_method") != j.get("narration_speed_method")))):
        return "NARRATION_AUDIO_STALE", "the narration settings changed since the audio was made - narrate again"
    h = hashlib.sha256(open(wav, "rb").read()).hexdigest()
    if h != TL.get("audio_sha256"): return "NARRATION_AUDIO_CHANGED", "build/narration.wav changed after it was made - narrate again"
    if not TL.get("aligned"): return "NARRATION_NOT_ALIGNED", "the recording has no sentence times yet: run narration_align.py"
    return None

def narrate(project):
    """M4 B1: narration audio (AI or recording) + caption timing + listening check, as JSON events like render_reel."""
    t0 = time.time(); job_id = uuid.uuid4().hex[:12]; d = job_dir(project)
    if not os.path.exists(os.path.join(d, "project.json")):
        yield dict(event="error", step="adapter", code="PROJECT_NOT_FOUND", message=f"project not found: {project}"); yield dict(event="done", ok=False, job_id=job_id); return
    P = load(os.path.join(d, "project.json")); mode = P.get("narration", "none")
    yield dict(event="start", job_id=job_id, project=project, action="narrate", narration=mode, pct=0)
    if mode == "none":
        yield dict(event="done", ok=True, job_id=job_id, narration="none", seconds=0.0, pct=100); return
    tmp = tempfile.mkdtemp(prefix=f"rs_{job_id}_"); state = dict(pct=0); ok = True
    try:
        env = dict(os.environ, RS_EVENTS="1", RS_TMP=tmp)
        for name, args, base, span in (("narrate", ["narrate.py", project], 0, 70), ("align", ["narration_align.py", project], 70, 30)):
            good, err, extra = yield from _step(name, args, env, base, span, None, state)
            if not good: ok = False; yield err; break
    finally: shutil.rmtree(tmp, ignore_errors=True)
    b = os.path.join(d, "build"); res = {}
    if ok:
        TL, CK = load(os.path.join(b, "narration_timeline.json")), load(os.path.join(b, "narration_check.json"))
        res = dict(duration=TL["duration"], sentences=len(TL["sentences"]), memory=TL.get("memory"), generated=TL.get("generated"),
                   cer_total=CK["cer_total"], to_check=CK["to_check"], audio=os.path.join(b, "narration.wav"))
    yield dict(event="done", ok=ok, job_id=job_id, narration=mode, seconds=round(time.time() - t0, 1), pct=100 if ok else None, **res)

def _action(project, action, steps, summary=None):
    """M4 B3: run engine steps for one action (plan, approve, build) as JSON events, like render_reel and narrate."""
    t0 = time.time(); job_id = uuid.uuid4().hex[:12]; d = job_dir(project)
    if not os.path.exists(os.path.join(d, "project.json")):
        yield dict(event="error", step="adapter", code="PROJECT_NOT_FOUND", message=f"project not found: {project}"); yield dict(event="done", ok=False, job_id=job_id); return
    yield dict(event="start", job_id=job_id, project=project, action=action, pct=0)
    tmp = tempfile.mkdtemp(prefix=f"rs_{job_id}_"); state = dict(pct=0); ok = True; share = 100 / max(1, len(steps))
    try:
        env = dict(os.environ, RS_EVENTS="1", RS_TMP=tmp)
        for k, (name, args) in enumerate(steps):
            good, err, extra = yield from _step(name, args, env, k * share, share, None, state)
            if not good: ok = False; yield err; break
    finally: shutil.rmtree(tmp, ignore_errors=True)
    extra = {}
    if ok and summary:
        try: extra = summary(d)
        except Exception as e: extra = dict(summary_error=str(e))
    yield dict(event="done", ok=ok, job_id=job_id, action=action, seconds=round(time.time() - t0, 1), pct=100 if ok else None, **extra)

def _plan_summary(d):
    P = load(os.path.join(d, "build", "plan.json")); H = P.get("creative", {}).get("hooks", [])
    return dict(plan=os.path.join(d, "build", "plan.md"), approved=bool(P.get("approved")), hook_choice=P.get("hook_choice"),
                options={"ABCDEFG"[i]: dict(line1=h.get("line1"), line2=h.get("line2"), line3=h.get("line3"), headline=h.get("headline"), source=h.get("source")) for i, h in enumerate(H)},
                cards=[dict(number=b["graphic"]["number"], label=b["graphic"].get("label")) for b in P["facts"]["beats"] if (b.get("graphic") or {}).get("type") == "number"],
                tag=P["facts"].get("tag"), problems=P.get("issues", []), marked=[f if isinstance(f, str) else json.dumps(f, ensure_ascii=False) for f in P.get("flags", [])])

def plan(project, hook=None):
    """Transcribe (if needed) + plan; or add your own option D with hook='l1 / l2 / l3 / h1 / h2'."""
    d = job_dir(project); P = load(os.path.join(d, "project.json")) if os.path.exists(os.path.join(d, "project.json")) else {}
    if hook: steps = [("hook", ["planner.py", project, "--hook", hook])]
    else:
        steps = [] if os.path.exists(os.path.join(d, "build", "transcript.json")) or os.path.exists(os.path.join(d, "build", "words.json")) or not P.get("video") \
            else [("transcribe", ["transcribe.py", "--project", project])]
        steps.append(("plan", ["planner.py", project]))
    yield from _action(project, "plan", steps, _plan_summary)

def approve(project, choice, checked=False):
    yield from _action(project, "approve", [("approve", ["planner.py", project, "--approve", choice] + (["--checked"] if checked else []))], _plan_summary)

def build(project):
    def summ(d):
        L = load(os.path.join(d, "build", "edit_layout.json")); return dict(edit=os.path.join(d, "build", "edit.mp4"), layout=L)
    yield from _action(project, "build", [("build", ["build.py", project])], summ)

def check():
    sys.path.insert(0, ENGINE); import rs
    tools = {t: shutil.which(t) for t in ("ffmpeg", "ffprobe", "node", "npx", "whisper")}
    mods = {}
    for m in ("PIL", "numpy", "scipy", "cv2", "onnxruntime"):
        try: __import__(m); mods[m] = True
        except Exception: mods[m] = False
    try:
        from PIL import features; raqm = bool(features.check("raqm"))
    except Exception: raqm = False
    errs = rs.validate()
    return dict(event="check", tools=tools, python_packages=mods, telugu_layout=raqm, settings=errs,
                ok=all(tools[t] for t in ("ffmpeg", "ffprobe")) and all(mods.values()) and raqm and not [e for e in errs if "handle not set" not in e])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["render", "check", "narrate", "plan", "approve", "build"]); ap.add_argument("project", nargs="?")
    ap.add_argument("--platform", action="append"); ap.add_argument("--all-platforms", action="store_true")
    ap.add_argument("--baseline"); ap.add_argument("--no-version", action="store_true")
    ap.add_argument("--hook"); ap.add_argument("--choice"); ap.add_argument("--checked", action="store_true"); a = ap.parse_args()
    if a.cmd == "check":
        r = check(); print(json.dumps(r, ensure_ascii=False)); sys.exit(0 if r["ok"] else 1)
    if a.cmd in ("narrate", "plan", "approve", "build"):
        gen = dict(narrate=lambda: narrate(a.project), plan=lambda: plan(a.project, a.hook), approve=lambda: approve(a.project, a.choice, a.checked),
                   build=lambda: build(a.project))[a.cmd]; last = {}
        for ev in gen(): print(json.dumps(ev, ensure_ascii=False), flush=True); last = ev
        sys.exit(0 if last.get("ok") else 1)
    last = {}
    for ev in render_reel(a.project, a.platform, a.all_platforms, a.baseline, not a.no_version):
        print(json.dumps(ev, ensure_ascii=False), flush=True); last = ev
    sys.exit(0 if last.get("ok") and last.get("qa_passed") else 1)
