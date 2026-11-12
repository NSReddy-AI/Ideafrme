"""Reel Studio app backend (M4): FastAPI over the existing engine. Local only, offline, nothing is ever published.
Run:  ~/.venvs/reelstudio/bin/python app/server.py            -> http://127.0.0.1:8765  (serves app/web/dist)
Dev:  same + `npm run dev` in app/web (Vite proxies /api and /files here).
Every engine action runs as its own process through engine/rs.py or engine/adapter.py (the same commands as the CLI), so the
engine's approvals, fingerprints, memory stops and locks apply unchanged. Jobs run ONE AT A TIME (one heavy model at a time)."""
import os, sys, json, re, glob, time, uuid, queue, threading, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); ENGINE = os.path.join(ROOT, "engine")
sys.path.insert(0, ENGINE)
_hook = sys.excepthook
import rs, adapter                      # engine modules (read-only use: next_step, plan summary, narration checks)
from common import load, job_dir
sys.excepthook = _hook
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PY = sys.executable
PROJECTS, EXPORTS = os.path.join(ROOT, "projects"), os.path.join(ROOT, "exports")
app = FastAPI(title="Reel Studio")

# ---------------------------------------------------------------- helpers
# Locked baseline (checkpoint.sh / tests/baseline_reel_002.json): the app shows it but never changes it.
PROTECTED = {"2026-11-03_reel_002_development"}

def _name_ok(name, write=False):
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", name or "") or name.startswith("."): raise HTTPException(400, "bad project name")
    d = os.path.join(PROJECTS, name)
    if not os.path.exists(os.path.join(d, "project.json")): raise HTTPException(404, f"project not found: {name}")
    if write and name in PROTECTED: raise HTTPException(403, "this is the locked reel_002 baseline - it is read-only in the app")
    return d

def _run(args, timeout=600):
    r = subprocess.run([PY] + args, capture_output=True, text=True, cwd=ROOT, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

def _fail(rc, out, err):
    msg = (err.strip() or out.strip()).splitlines()
    raise HTTPException(400, msg[-1] if msg else f"failed (exit {rc})")

def _rel(p): return os.path.relpath(p, ROOT) if p else None

def _history(d, msg):
    rs.log(dict(_dir=d), msg)

def _save_project(d, P):
    json.dump(P, open(os.path.join(d, "project.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

SPEAKER_STATE = ("transcript.json", "words.json", "plan.json", "plan.md", "keep.json", ".cut_keep.json", "cut.mov", "edit.mp4",
                 "edit_audio.wav", "edit_layout.json", "layout.json", "speaker_base.mp4", "captions.mov")

def _supersede(d, why):
    """A new source video makes the old transcript, plan and edit invalid: move them to build/_superseded_<time>/ (kept, not deleted)."""
    b = os.path.join(d, "build"); moved = [f for f in SPEAKER_STATE if os.path.exists(os.path.join(b, f))]
    if not moved: return
    dst = os.path.join(b, time.strftime("_superseded_%Y%m%d_%H%M%S")); os.makedirs(dst, exist_ok=True)
    for f in moved: os.replace(os.path.join(b, f), os.path.join(dst, f))
    P = load(os.path.join(d, "project.json")); [P.pop(k, None) for k in ("plan_hash", "hook_choice")]; P["approved"] = False; _save_project(d, P)
    _history(d, f"app: {why} - old transcript/plan/edit moved to build/{os.path.basename(dst)}")

def _exports(d):
    """Exports of a project grouped by version: each platform's video, cover, QA summary, contact sheet, post copy."""
    base = os.path.basename(d); groups = {}
    for f in glob.glob(os.path.join(EXPORTS, f"{base}_*.mp4")):     # versioned (_vN) and older unversioned exports (shown as v0 "original")
        m = re.match(re.escape(base) + r"_(.+)_([a-z]+)(?:_v(\d+))?\.mp4$", os.path.basename(f))
        if not m: continue
        brand, pf, v = m.group(1), m.group(2), int(m.group(3) or 0); q = f[:-4] + "_qa.json"; Q = load(q) if os.path.exists(q) else {}
        item = dict(platform=pf, brand=brand, file=_rel(f), size_mb=round(os.path.getsize(f) / 1e6, 1),
                    cover=_rel(f[:-4] + "_cover_4k.jpg") if os.path.exists(f[:-4] + "_cover_4k.jpg") else None,
                    post=_rel(f[:-4] + "_post.md") if os.path.exists(f[:-4] + "_post.md") else None,
                    qa=dict(passed=Q.get("passed"), duration=Q.get("duration"), loudness=Q.get("loudness_lufs"), true_peak=Q.get("true_peak_db"),
                            checks=[dict(name=c["name"], passed=c["passed"], detail=str(c.get("detail", ""))[:200]) for c in Q.get("checks", [])],
                            warnings=Q.get("warnings", []), contact_sheet=_rel(Q.get("contact_sheet")) if Q.get("contact_sheet") else None) if Q else None,
                    created=time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(f))))
        groups.setdefault(v, []).append(item)
    return [dict(version=v, outputs=sorted(groups[v], key=lambda x: x["platform"])) for v in sorted(groups, reverse=True)]

def _project_view(name):
    d = _name_ok(name); P = load(os.path.join(d, "project.json")); b = os.path.join(d, "build"); ex = lambda f: os.path.exists(os.path.join(b, f))
    done, nxt = rs.next_step(name)
    lang = load(os.path.join(ROOT, "brands", P["brand"], "brand.json")).get("language")
    v = dict(name=name, locked=name in PROTECTED, archived=bool(P.get("archived")), language=lang, project=P, mode="speaker" if P.get("video") else "slides", done=done, next=nxt,
             inputs=sorted(f for f in os.listdir(os.path.join(d, "inputs")) if not f.startswith(".")),
             notes=open(os.path.join(d, "inputs", "notes.txt"), encoding="utf-8").read() if os.path.exists(os.path.join(d, "inputs", "notes.txt")) else "",
             transcript=ex("transcript.json") or ex("words.json"), edit=_rel(os.path.join(b, "edit.mp4")) if ex("edit.mp4") else None,
             edit_layout=load(os.path.join(b, "edit_layout.json")) if ex("edit_layout.json") else None, exports=_exports(d))
    if ex("transcript.json"):
        v["words"] = [dict(i=i, w=w["w"], s=w["s"], e=w["e"], review=bool(w.get("review")), w_asr=w.get("w_asr")) for i, w in enumerate(load(os.path.join(b, "transcript.json"))["words"])]
    if ex("plan.json"):
        try: v["plan"] = adapter._plan_summary(d); v["plan"]["markdown"] = open(os.path.join(b, "plan.md"), encoding="utf-8").read() if ex("plan.md") else ""
        except Exception as e: v["plan"] = dict(error=str(e))
    if ex("narration.json"):
        import narration_script as NS
        N = load(os.path.join(b, "narration.json")); v["script"] = dict(review=NS.show(N), approved=bool(N.get("approved")), approved_hash=N.get("approved_hash"),
                                                                          lines=[dict(text=l["text"], say=l["say"], numbers=l.get("numbers", []), length=l.get("length")) for l in N["lines"]])
    if P.get("narration") in ("ai", "recorded"):
        bad = adapter.narration_ready(dict(P, _dir=d)); v["narration_ready"] = None if bad else True; v["narration_problem"] = bad and dict(code=bad[0], message=bad[1])
        if ex("narration_check.json"): v["narration_check"] = load(os.path.join(b, "narration_check.json"))
        if ex("narration_timeline.json"):
            T = load(os.path.join(b, "narration_timeline.json")); v["narration_audio"] = dict(file=_rel(os.path.join(b, "narration.wav")), duration=T.get("duration"), memory=T.get("memory"), voice=T.get("voice"), style=T.get("style"), speed=T.get("speed"))
    return v

# ---------------------------------------------------------------- jobs (one at a time)
JOBS, Q = {}, queue.Queue()
ACTIONS = {"plan", "hook", "approve", "narrate", "build", "render"}

def _job_cmd(name, a):
    act = a["action"]
    if act == "plan": return ["engine/adapter.py", "plan", name]
    if act == "hook": return ["engine/adapter.py", "plan", name, "--hook", a["hook"]]
    if act == "approve": return ["engine/adapter.py", "approve", name, "--choice", a["choice"]] + (["--checked"] if a.get("checked") else [])
    if act == "narrate": return ["engine/adapter.py", "narrate", name]
    if act == "build": return ["engine/adapter.py", "build", name]
    if act == "render":
        pfs = a.get("platforms") or []
        return ["engine/adapter.py", "render", name] + (sum([["--platform", p] for p in pfs], []) if pfs else ["--all-platforms"])

def _worker():
    while True:
        jid = Q.get(); J = JOBS[jid]; J.update(status="running", started=time.time())
        try:
            # /usr/bin/time -l reports the peak memory of the job's process tree (macOS)
            if J.get("cancel"): raise RuntimeError("cancelled before it started")
            p = subprocess.Popen(["/usr/bin/time", "-l", PY] + J["cmd"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT,
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), start_new_session=True)   # own process group: cancel stops all of it
            J["pid"] = p.pid
            for line in p.stdout:
                line = line.strip()
                if not line: continue
                try: ev = json.loads(line) if line.startswith("{") else dict(event="log", message=line)
                except json.JSONDecodeError: ev = dict(event="log", message=line)
                J["events"].append(ev)
                if ev.get("pct") is not None: J["pct"] = ev["pct"]
                if ev.get("event") == "done": J["result"] = ev
            err = p.stderr.read(); p.wait()
            m = re.search(r"(\d+)\s+maximum resident set size", err); J["peak_rss_gb"] = round(int(m.group(1)) / 1e9, 2) if m else None
            res = J.get("result") or {}
            J["ok"] = bool(res.get("ok")); J["status"] = "done" if J["ok"] else ("cancelled" if J.get("cancel") else "failed")
            if not res: J["events"].append(dict(event="error", code="STEP_CRASHED", message=err.strip().splitlines()[-1] if err.strip() else f"exit {p.returncode}"))
            if J["ok"] and J["action"] == "render":
                for o in res.get("outputs", []):     # post copy beside every export (never posted anywhere)
                    subprocess.run([PY, "engine/post.py", J["project"], o["path"]], cwd=ROOT, capture_output=True, text=True, timeout=60)
        except Exception as e:
            J.update(status="cancelled" if J.get("cancel") else "failed", ok=False); J["events"].append(dict(event="error", code="CANCELLED" if J.get("cancel") else "APP_ERROR", message=str(e)))
        finally:
            J["finished"] = time.time(); J["seconds"] = round(J["finished"] - J["started"], 1)
            try: _history(job_dir(J["project"]), f"app job {J['action']} {J['status']} ({J['seconds']} s, peak {J.get('peak_rss_gb')} GB, job {jid})")
            except Exception: pass

threading.Thread(target=_worker, daemon=True).start()

def _job_public(J, since=0):
    return {k: v for k, v in J.items() if k not in ("events", "cmd", "pid")} | dict(events=J["events"][since:], n_events=len(J["events"]))

# ---------------------------------------------------------------- API
class NewProject(BaseModel): brand: str; platform: str; style: str; slug: str
class Patch(BaseModel): video: str | None = None; brief: str | None = None; notes: str | None = None; face_x: float | None = None; archived: bool | None = None
class Narration(BaseModel): mode: str; voice: str | None = None; style: str | None = None; speed: float | None = None; file: str | None = None
class Script(BaseModel): text: str
class Approve(BaseModel): checked: bool = False
class Job(BaseModel): action: str; choice: str | None = None; checked: bool = False; hook: str | None = None; platforms: list[str] | None = None

@app.get("/api/catalog")
def catalog():
    import providers
    C = load(os.path.join(ENGINE, "tts.json"))
    brands = [dict(id=b, **{k: load(os.path.join(ROOT, "brands", b, "brand.json")).get(k) for k in ("name", "handle", "language", "default_style", "default_platforms")})
              for b in rs.brands()]
    try: prov = providers.status()
    except Exception as e: prov = dict(error=str(e))
    return dict(brands=brands, platforms=[dict(id=p, name=load(os.path.join(ROOT, "platforms", p + ".json"))["name"]) for p in rs.names("platforms")],
                styles=[dict(id=s, name=load(os.path.join(ROOT, "styles", s + ".json"))["name"]) for s in rs.names("styles")],
                voices=C["voices"], narration_styles=sorted(C["styles"]), speeds=C["speed"].get("test_values", [1.0]), providers=prov)

@app.get("/api/projects")
def projects(all: bool = False):
    out = []
    for pj in sorted(glob.glob(os.path.join(PROJECTS, "*", "project.json")), key=os.path.getmtime, reverse=True):
        name = os.path.basename(os.path.dirname(pj))
        if not all and name.startswith("zz_"): continue      # test projects stay hidden unless asked for
        P = load(pj)
        if not all and P.get("archived"): continue
        try: done, nxt = rs.next_step(name)
        except Exception as e: done, nxt = [], f"error: {e}"
        out.append(dict(name=name, brand=P.get("brand"), platform=P.get("platform"), style=P.get("style"), status=P.get("status"), narration=P.get("narration"), archived=bool(P.get("archived")),
                        mode="speaker" if P.get("video") else "slides", steps_done=len(done), next=nxt, modified=time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(pj))),
                        exports=len(glob.glob(os.path.join(EXPORTS, f"{name}_*_v*.mp4")))))
    return out

@app.post("/api/projects")
def create(n: NewProject):
    slug = re.sub(r"[^a-z0-9_]+", "_", n.slug.lower()).strip("_")
    if not slug: raise HTTPException(400, "give the project a short name")
    rc, out, err = _run(["engine/rs.py", "new", n.brand, n.platform, n.style, slug])
    if rc: _fail(rc, out, err)
    return _project_view(os.path.basename(out.strip().splitlines()[-1]))

@app.get("/api/projects/{name}")
def project(name: str): return _project_view(name)

@app.patch("/api/projects/{name}")
def patch(name: str, p: Patch):
    d = _name_ok(name, write=True); P = load(os.path.join(d, "project.json"))
    if p.video is not None:
        if p.video and not os.path.exists(os.path.join(d, p.video)): raise HTTPException(400, f"video not found: {p.video}")
        if P.get("video") != (p.video or None):      # a different source: new transcript, plan and approval
            _supersede(d, f"source video changed to {p.video or 'none'}"); P = load(os.path.join(d, "project.json"))
        P["video"] = p.video or None
    if p.brief is not None: P["brief"] = p.brief
    if p.face_x is not None:                       # speaker reels: where the face is across the source (0 = left, 1 = right) for the crop
        if not 0 <= p.face_x <= 1: raise HTTPException(400, "face position must be 0..1")
        P["face_x"] = round(p.face_x, 3)
    if p.archived is not None: P["archived"] = bool(p.archived)   # hidden from the list; nothing is deleted
    _save_project(d, P)
    if p.notes is not None: open(os.path.join(d, "inputs", "notes.txt"), "w", encoding="utf-8").write(p.notes)
    _history(d, "app: " + ", ".join(k for k, v in p.model_dump().items() if v is not None) + " updated")
    return _project_view(name)

@app.post("/api/projects/{name}/upload")
async def upload(name: str, filename: str, request: Request, kind: str = "file"):
    """Raw body upload (no extra form library): a source video, a slide picture, or the user's own narration recording."""
    d = _name_ok(name, write=True); fn = re.sub(r"[^A-Za-z0-9_.\-]+", "_", os.path.basename(filename)).lstrip(".")
    if not fn: raise HTTPException(400, "bad file name")
    if kind == "slide":
        n = len(glob.glob(os.path.join(d, "inputs", "slide_*.png"))) + 1; fn = f"slide_{n:02d}.png"
    dst = os.path.join(d, "inputs", fn); tmp = dst + ".part"
    with open(tmp, "wb") as f:
        async for chunk in request.stream(): f.write(chunk)
    if kind == "slide" and not filename.lower().endswith(".png"):   # slides.py reads slide_NN.png: convert other pictures
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, dst], capture_output=True, text=True); os.remove(tmp)
        if r.returncode: raise HTTPException(400, "could not read that picture")
    else: os.replace(tmp, dst)
    if kind == "video":
        _supersede(d, f"new source video inputs/{fn}")
        P = load(os.path.join(d, "project.json")); P["video"] = f"inputs/{fn}"; P["approved"] = False; _save_project(d, P)
    if kind in ("title_person", "title_bg"):     # title page pictures (the person cut-out should be a PNG with transparency)
        P = load(os.path.join(d, "project.json")); P[kind] = f"inputs/{fn}"; _save_project(d, P)
    _history(d, f"app: uploaded inputs/{fn} ({kind})")
    return _project_view(name)

class CaptionFix(BaseModel): fixes: dict[int, str]

@app.put("/api/projects/{name}/captions")
def caption_fixes(name: str, c: CaptionFix):
    """Speaker reels: spelling fixes to the speech-to-text words (captions stay the speaker's own words). The original word is kept
    as w_asr. A fix after the plan was approved withdraws that approval - the user approves again before anything is rebuilt."""
    d = _name_ok(name, write=True); tp = os.path.join(d, "build", "transcript.json")
    if not os.path.exists(tp): raise HTTPException(400, "no transcript yet - run the plan first")
    T = load(tp); W = T["words"]; changed = []
    for i, txt in c.fixes.items():
        txt = (txt or "").strip()
        if not (0 <= i < len(W)) or not txt: raise HTTPException(400, f"bad fix for word {i}")
        if txt != W[i]["w"]:
            W[i].setdefault("w_asr", W[i]["w"]); changed.append(f"{W[i]['w']} -> {txt}"); W[i]["w"] = txt; W[i].pop("review", None)
    if not changed: return _project_view(name)
    T["corrected"] = True; json.dump(T, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pj = os.path.join(d, "build", "plan.json")
    if os.path.exists(pj):
        PL = load(pj)
        if PL.get("approved"):
            PL["approved"] = False; json.dump(PL, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            _history(d, "app: plan approval withdrawn - captions corrected after approval")
    _history(d, f"app: caption spelling fixes ({len(changed)}): " + "; ".join(changed)[:500])
    return _project_view(name)

class TitlePage(BaseModel): line1: str; line2: str; line3: str; tag_top: str = ""; tag_bottom: str = ""; headline: list[str] = ["", ""]

@app.put("/api/projects/{name}/title")
def title_page(name: str, t: TitlePage):
    """Slides reels: the user's own title page words (hook lines, sign, 2-line headline), saved exactly as written.
    Speaker reels get theirs from the approved plan (own wording = option D), so they are refused here."""
    d = _name_ok(name, write=True); P = load(os.path.join(d, "project.json"))
    if P.get("video") or os.path.exists(os.path.join(d, "build", "plan.json")):
        raise HTTPException(409, "speaker reel: the title page comes from the approved plan - add your own wording as hook option D")
    if not all(x.strip() for x in (t.line1, t.line2, t.line3)): raise HTTPException(400, "all three hook lines are needed")
    P["hook"] = dict(line1=t.line1.strip(), line2=t.line2.strip(), line3=t.line3.strip(), tag_top=t.tag_top.strip(), tag_bottom=t.tag_bottom.strip())
    P["title"] = [x.strip() for x in (list(t.headline) + ["", ""])[:2]]; _save_project(d, P)
    _history(d, "app: title page words set by the user")
    return _project_view(name)

@app.post("/api/projects/{name}/narration")
def narration(name: str, n: Narration):
    d = _name_ok(name, write=True); args = ["engine/rs.py", "narration", name, n.mode]
    lang = load(os.path.join(ROOT, "brands", load(os.path.join(d, "project.json"))["brand"], "brand.json")).get("language")
    if n.mode == "ai" and lang != "te":   # the approved offline voices (Prakash, Lalitha) are Telugu narrators
        raise HTTPException(400, "AI narration is approved for Telugu brands only - use your own recording or text + music")
    if n.voice: args += ["--voice", n.voice]
    if n.style: args += ["--style", n.style]
    if n.speed is not None: args += ["--speed", str(n.speed)]
    if n.file: args += ["--file", n.file]
    rc, out, err = _run(args)
    if rc: _fail(rc, out, err)
    return _project_view(name)

@app.post("/api/projects/{name}/script")
def script(name: str, s: Script):
    """Saves the text exactly as written (one sentence per line) and prepares it for review. Never rewritten."""
    d = _name_ok(name, write=True); lines = [l.strip() for l in s.text.splitlines() if l.strip()]
    if not lines: raise HTTPException(400, "write at least one sentence")
    f = os.path.join(d, "inputs", "script.txt"); open(f, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    rc, out, err = _run(["engine/rs.py", "script", name, f])
    if rc: _fail(rc, out, err)
    return _project_view(name)

@app.post("/api/projects/{name}/script/approve")
def script_approve(name: str, a: Approve):
    _name_ok(name, write=True); rc, out, err = _run(["engine/rs.py", "script-approve", name] + (["--checked"] if a.checked else []))
    if rc or "APPROVED" not in out: _fail(rc or 1, out, err)
    return _project_view(name)

@app.post("/api/projects/{name}/jobs")
def start_job(name: str, j: Job):
    _name_ok(name, write=True)
    if j.action not in ACTIONS: raise HTTPException(400, f"unknown action {j.action}")
    if j.action == "approve" and (j.choice or "") not in list("ABCD"): raise HTTPException(400, "choose A, B, C or D")
    if j.action == "hook" and not (j.hook or "").strip(): raise HTTPException(400, "write the hook as l1 / l2 / l3 / h1 / h2")
    busy = [x for x in JOBS.values() if x["project"] == name and x["status"] in ("queued", "running")]
    if busy: raise HTTPException(409, f"this project already has a {busy[0]['action']} job {busy[0]['status']}")
    jid = uuid.uuid4().hex[:10]
    JOBS[jid] = dict(id=jid, project=name, action=j.action, status="queued", pct=0, events=[], cmd=_job_cmd(name, j.model_dump()), created=time.time())
    Q.put(jid); return _job_public(JOBS[jid])

@app.get("/api/jobs")
def jobs(project: str | None = None):
    return [_job_public(J, len(J["events"])) for J in sorted(JOBS.values(), key=lambda x: -x["created"]) if not project or J["project"] == project][:30]

@app.get("/api/jobs/{jid}")
def job(jid: str, since: int = 0):
    if jid not in JOBS: raise HTTPException(404, "no such job")
    return _job_public(JOBS[jid], since)

@app.post("/api/jobs/{jid}/cancel")
def cancel(jid: str):
    """Stop a queued or running job. Finished sentences/pieces stay cached by the engine; locks of a killed step are taken over next time."""
    import signal
    J = JOBS.get(jid)
    if not J: raise HTTPException(404, "no such job")
    if J["status"] not in ("queued", "running"): return _job_public(J, len(J["events"]))
    J["cancel"] = True
    if J.get("pid"):
        try: os.killpg(J["pid"], signal.SIGTERM)
        except ProcessLookupError: pass
    _history(job_dir(J["project"]), f"app: job {J['action']} cancelled by the user")
    return _job_public(J, len(J["events"]))

@app.get("/api/projects/{name}/source_frame")
def source_frame(name: str, t: float = 3.0):
    """One still from the source video (for choosing the speaker crop). Written to build/source_frame.jpg."""
    d = _name_ok(name); P = load(os.path.join(d, "project.json"))
    if not P.get("video"): raise HTTPException(400, "no source video")
    out = os.path.join(d, "build", "source_frame.jpg")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(max(0, t)), "-i", os.path.join(d, P["video"]), "-frames:v", "1", "-vf", "scale=640:-2", out], capture_output=True, text=True)
    if r.returncode or not os.path.exists(out): raise HTTPException(400, "could not read a frame from the video")
    return FileResponse(out, headers={"Cache-Control": "no-store"})

@app.delete("/api/projects/{name}/inputs/{fn}")
def remove_input(name: str, fn: str):
    """Take a file out of the project: moved to inputs/.removed/ (kept). Slide pictures are renumbered so they stay in order."""
    d = _name_ok(name, write=True); src = os.path.join(d, "inputs", os.path.basename(fn))
    if fn in ("notes.txt", "urls.txt", "script.txt") or not os.path.isfile(src): raise HTTPException(400, f"cannot remove {fn}")
    P = load(os.path.join(d, "project.json"))
    if f"inputs/{fn}" in (P.get("video"), P.get("narration_file")): raise HTTPException(409, f"{fn} is in use (source video or narration recording) - choose another first")
    rm = os.path.join(d, "inputs", ".removed"); os.makedirs(rm, exist_ok=True); os.replace(src, os.path.join(rm, time.strftime("%Y%m%d_%H%M%S_") + fn))
    if re.match(r"slide_\d+\.png$", fn):
        for k, f in enumerate(sorted(x for x in os.listdir(os.path.join(d, "inputs")) if re.match(r"slide_\d+\.png$", x)), 1):
            if f != f"slide_{k:02d}.png": os.replace(os.path.join(d, "inputs", f), os.path.join(d, "inputs", f"slide_{k:02d}.png"))
    for k in ("title_person", "title_bg"):
        if P.get(k) == f"inputs/{fn}": P.pop(k); _save_project(d, P)
    _history(d, f"app: removed inputs/{fn} (kept in inputs/.removed)")
    return _project_view(name)

@app.get("/api/check")
def check():
    import providers
    r = adapter.check()
    try: r["providers"] = providers.status()
    except Exception as e: r["providers"] = dict(error=str(e))
    r["memory_gb"] = round(int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout or 0) / 1e9, 1)
    r["asr_env"] = os.path.exists(os.path.expanduser("~/.venvs/rs_asr/bin/python")); r["tts_env"] = os.path.exists(os.path.expanduser("~/.venvs/rs_tts/bin/python"))
    return r

@app.get("/files/{path:path}")
def files(path: str):
    """Only files inside projects/ and exports/ (videos, pictures, reports) are served."""
    full = os.path.realpath(os.path.join(ROOT, path))
    if not any(full.startswith(os.path.realpath(x) + os.sep) for x in (PROJECTS, EXPORTS)) or not os.path.isfile(full): raise HTTPException(404, "not found")
    return FileResponse(full)

# M6 step 3: M5 poster editing, Brand Library and deterministic Creative Director (app/creative.py, code in ../m5).
# Included before the page fallback below so its routes win.
sys.path.insert(0, HERE)
import creative
app.include_router(creative.router)

DIST = os.path.join(HERE, "web", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")
    @app.get("/{rest:path}")
    def spa(rest: str): return FileResponse(os.path.join(DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("RS_PORT", 8765)))
