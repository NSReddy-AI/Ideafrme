"""M7-B B4C-1: durable local tasks.

A task is a small record of real work: which steps a poster, a reel, or a poster-then-reel ("both") goes through, what
state each step is really in, and what went wrong. It does not do the work. Poster steps are reported by the screen at
the moment the existing M5 call succeeds or fails; reel steps mirror the existing engine job queue (app/server.py JOBS),
which stays exactly as it is.

Storage: one JSON file per task under jobs/tasks/ (jobs/ is local data, not in Git). Writes are atomic (temp file, fsync,
rename). All access goes through one lock. Nothing here touches a poster, a reel project or the Brand Library.

After a restart, a step that was "running" cannot still be running (engine jobs live in the server's memory), so it is
marked failed with a plain reason and may be retried where that is safe. Nothing is ever marked done by a restart.
"""
import json, os, re, threading, time, uuid
from pathlib import Path

FORMAT = "ideaframe-task@1"
WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE / "jobs" / os.environ.get("IDEAFRAME_M6_TASKS", "tasks")       # tests name another folder under jobs/

TASK_STATES = ("pending", "running", "waiting", "completed", "failed", "cancelled", "retrying")
STEP_STATES = ("pending", "running", "waiting", "done", "failed", "cancelled", "skipped")
TERMINAL = ("completed", "cancelled")

# user = the person must act; retry: "client" = the screen may do the step again, "job" = the engine job may be queued again
def _s(id, label, user=False, retry=None): return dict(id=id, label=label, user=user, retry=retry)
POSTER = [_s("interpret", "Understand the request"), _s("brief", "Save the brief", retry="client"),
          _s("concepts", "Make three concepts", retry="client"), _s("choose", "Choose a concept", user=True),
          _s("poster", "Create the editable poster", retry="client"), _s("review", "Review and edit the poster", user=True),
          _s("qa", "Poster QA", retry="client"), _s("export", "Export the poster", user=True, retry="client")]
REEL = [_s("plan", "Plan the reel", retry="job"), _s("approve", "Approve the plan or script", user=True),
        _s("narrate", "Narration", retry="job"), _s("build", "Build the edit", retry="job"), _s("render", "Render and check", retry="job")]
KINDS = {"poster": POSTER, "reel": REEL, "both": POSTER + [_s("handoff", "Make a reel from the poster", user=True)] + REEL}
JOB_STEP = {"plan": "plan", "hook": "plan", "approve": "approve", "narrate": "narrate", "build": "build", "render": "render"}
REEL_IDS = tuple(d["id"] for d in REEL)
RETRY_ACTIONS = ("plan", "narrate", "build", "render")        # never re-run an approval or a hand-written hook automatically

_ID = re.compile(r"^[0-9a-f]{12}$")
_now = lambda: time.strftime("%Y-%m-%d %H:%M:%S")


class TaskError(Exception):
    def __init__(self, status, code, detail): super().__init__(detail); self.status, self.code, self.detail = status, code, detail


def _text(v, limit, what):
    if v is None: return None
    if not isinstance(v, str) or len(v) > limit or "\x00" in v: raise TaskError(400, "invalid", f"{what} must be text of at most {limit} characters")
    return v


def validate(t):
    """A stored task must be exactly this shape, or it is not used."""
    ok = (isinstance(t, dict) and t.get("format") == FORMAT and isinstance(t.get("id"), str) and _ID.match(t["id"]) and t.get("kind") in KINDS
          and t.get("status") in TASK_STATES and isinstance(t.get("steps"), list) and isinstance(t.get("events"), list) and isinstance(t.get("rev"), int)
          and [s.get("id") for s in t["steps"] if isinstance(s, dict)] == [d["id"] for d in KINDS[t["kind"]]]
          and all(s.get("status") in STEP_STATES for s in t["steps"]) and isinstance(t.get("project"), dict) and isinstance(t.get("jobs"), dict))
    if not ok: raise ValueError("not a valid task record")
    return t


def derive(t):
    """The task's state follows from its steps; it is never set by hand."""
    st = [s["status"] for s in t["steps"]]
    if "running" in st: return "retrying" if any(s["status"] == "running" and s.get("attempts", 0) > 1 for s in t["steps"]) else "running"
    if "failed" in st: return "failed"
    if t.get("cancelled"): return "cancelled"
    if "waiting" in st: return "waiting"
    if all(x in ("done", "skipped") for x in st): return "completed"
    return "pending"


class TaskStore:
    def __init__(self, root=None, start_job=None, cancel_job=None, reel_facts=None):
        self.root = Path(root or ROOT); self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock(); self.tasks = {}; self.invalid = []
        self.start_job, self.cancel_job, self.reel_facts = start_job, cancel_job, reel_facts
        self.started = time.time(); self._seen = {}; self._bound = {}
        self._load(); self.recover()

    # ---------------------------------------------------------------- storage
    def _path(self, tid): return self.root / f"{tid}.json"

    def _load(self):
        for p in sorted(self.root.glob("*.json")):
            try:
                t = validate(json.loads(p.read_text(encoding="utf-8")))
                if t["id"] != p.stem: raise ValueError("id does not match its file")
                self.tasks[t["id"]] = t
            except Exception as e:      # a damaged file is left where it is and reported; it is never repaired or deleted here
                self.invalid.append(dict(file=p.name, reason=str(e)))

    def _save(self, t):
        t["rev"] += 1; t["updated"] = _now(); t["status"] = derive(t); validate(t)
        tmp = self.root / f".{t['id']}.{uuid.uuid4().hex[:8]}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False, indent=1); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, self._path(t["id"]))
        return t

    def _event(self, t, step, status, detail=None):
        t["events"].append(dict(at=_now(), step=step, status=status, detail=detail)); del t["events"][:-200]

    def recover(self):
        """After a restart nothing can still be running. Say so; never guess that it finished."""
        with self.lock:
            for t in self.tasks.values():
                hit = False
                for s in t["steps"]:
                    if s["status"] == "running":
                        s.update(status="failed", error="The app was closed or restarted while this step was running. Nothing was marked as finished.", finished=_now(), pct=None); hit = True
                        self._event(t, s["id"], "failed", "interrupted by a restart")
                if hit: t["jobs"] = {}; self._save(t)

    # ---------------------------------------------------------------- reading
    def get(self, tid):
        if not isinstance(tid, str) or not _ID.match(tid): raise TaskError(400, "invalid", "that is not a task id")
        with self.lock:
            t = self.tasks.get(tid)
            if not t: raise TaskError(404, "not-found", "no such task")
            self._sync_reel(t); return json.loads(json.dumps(t))

    def list(self, poster=None, reel=None, active=False, limit=50):
        with self.lock:
            out = []
            for t in sorted(self.tasks.values(), key=lambda x: x["created"], reverse=True):
                if poster and poster not in (t["project"].get("posters") or []): continue
                if reel and t["project"].get("reel") != reel: continue
                if active and t["status"] in TERMINAL: continue
                self._sync_reel(t); out.append(json.loads(json.dumps(t)))
                if len(out) >= limit: break
            return out

    # ---------------------------------------------------------------- writing
    def create(self, kind, key=None, poster=None, reel=None, meta=None):
        if kind not in KINDS: raise TaskError(400, "invalid", "kind must be poster, reel or both")
        key = _text(key, 200, "key"); poster = _text(poster, 100, "poster"); reel = _text(reel, 200, "reel")
        meta = meta or {}
        if not isinstance(meta, dict): raise TaskError(400, "invalid", "meta must be an object")
        clean = dict(prompt=_text(meta.get("prompt"), 4000, "prompt"), output=_text(meta.get("output"), 20, "output"), title=_text(meta.get("title"), 200, "title"))
        with self.lock:
            if key:     # the same request sent twice gives the same task, never a second one
                for t in self.tasks.values():
                    if t.get("key") == key and t["status"] not in TERMINAL: return json.loads(json.dumps(t))
            tid = uuid.uuid4().hex[:12]
            t = dict(format=FORMAT, id=tid, kind=kind, key=key, status="pending", rev=0, created=_now(), updated=_now(), cancelled=False,
                     project=dict(posters=[poster] if poster else [], reel=reel), meta={k: v for k, v in clean.items() if v},
                     steps=[dict(id=d["id"], label=d["label"], user=d["user"], retry=d["retry"], status="pending", detail=None, error=None, pct=None,
                                 attempts=0, started=None, finished=None) for d in KINDS[kind]], events=[], jobs={})
            self._event(t, None, "created", kind); self.tasks[tid] = t
            return json.loads(json.dumps(self._save(t)))

    def _step(self, t, sid):
        for s in t["steps"]:
            if s["id"] == sid: return s
        raise TaskError(400, "invalid", f"this kind of task has no step called {sid!r}")

    def step(self, tid, sid, status, detail=None, error=None, pct=None, poster=None, reel=None, _internal=False):
        """Record that a step really changed state. Refuses anything that could turn into a false finish."""
        if status not in STEP_STATES: raise TaskError(400, "invalid", "unknown step state")
        detail = _text(detail, 500, "detail"); error = _text(error, 1000, "error"); poster = _text(poster, 100, "poster"); reel = _text(reel, 200, "reel")
        if pct is not None and not (isinstance(pct, (int, float)) and 0 <= pct <= 100): raise TaskError(400, "invalid", "progress must be between 0 and 100")
        with self.lock:
            if not isinstance(tid, str) or tid not in self.tasks: raise TaskError(404, "not-found", "no such task")
            t = self.tasks[tid]; s = self._step(t, sid)
            if t.get("cancelled") and not _internal: raise TaskError(409, "cancelled", "this task was cancelled; start a new one")
            if not _internal and sid in REEL_IDS: raise TaskError(409, "conflict", "reel steps follow the reel engine and the reel's own approval; they cannot be set from the screen")
            if s["status"] == "skipped" and status != "skipped": raise TaskError(409, "conflict", "a skipped step cannot be changed")
            if status == "failed" and not error: raise TaskError(400, "invalid", "a failed step needs its error")
            if status == "done":       # nothing after an unfinished step may be marked done by the screen
                before = t["steps"][:t["steps"].index(s)]
                if not _internal and any(b["status"] in ("failed", "running") for b in before): raise TaskError(409, "conflict", "an earlier step is still running or has failed")
            if status == "running":
                if s["status"] != "running": s["attempts"] = s.get("attempts", 0) + 1; s["started"] = _now(); s["finished"] = None
                s["error"] = None
            if status in ("done", "failed", "cancelled", "skipped"): s["finished"] = _now()
            changed = s["status"] != status or (detail is not None and detail != s.get("detail")) or (pct is not None and pct != s.get("pct"))
            if s["status"] != status: self._event(t, sid, status, error or detail)
            s["status"] = status
            if detail is not None: s["detail"] = detail
            s["error"] = error if status == "failed" else None
            s["pct"] = pct if status == "running" else None
            if poster and poster not in t["project"]["posters"]: t["project"]["posters"].append(poster); changed = True
            if reel and t["project"].get("reel") != reel: t["project"]["reel"] = reel; changed = True
            if status == "done":       # the next step that needs the person is now really waiting for them
                for nxt in t["steps"][t["steps"].index(s) + 1:]:
                    if nxt["status"] in ("done", "skipped"): continue
                    if nxt["status"] == "pending" and nxt["user"]: nxt["status"] = "waiting"; self._event(t, nxt["id"], "waiting"); changed = True
                    break
            if changed: self._save(t)
            return json.loads(json.dumps(t))

    def cancel(self, tid):
        with self.lock:
            if not isinstance(tid, str) or tid not in self.tasks: raise TaskError(404, "not-found", "no such task")
            t = self.tasks[tid]
            if t["status"] in TERMINAL: return json.loads(json.dumps(t))
            for jid in list(t["jobs"]):        # a running engine job is stopped through the engine's own cancel
                if self.cancel_job:
                    try: self.cancel_job(jid)
                    except Exception: pass
            for s in t["steps"]:
                if s["status"] in ("running", "waiting"): s.update(status="cancelled", finished=_now(), pct=None); self._event(t, s["id"], "cancelled")
            t["cancelled"] = True; self._event(t, None, "cancelled")
            return json.loads(json.dumps(self._save(t)))

    def retry(self, tid):
        """Try the failed step again, only where that cannot repeat an approval or duplicate a project."""
        with self.lock:
            if not isinstance(tid, str) or tid not in self.tasks: raise TaskError(404, "not-found", "no such task")
            t = self.tasks[tid]
            if t.get("cancelled"): raise TaskError(409, "cancelled", "this task was cancelled; start a new one")
            failed = [s for s in t["steps"] if s["status"] == "failed"]
            if not failed: raise TaskError(409, "conflict", "nothing in this task has failed")
            s = failed[0]
            if s["retry"] == "client":      # the screen does the step again; here it only becomes possible
                s.update(status="waiting" if s["user"] else "pending", error=None, finished=None); self._event(t, s["id"], "retry", "ready to try again")
                return json.loads(json.dumps(self._save(t)))
            if s["retry"] == "job":
                action = s.get("action") or s["id"]; reel = t["project"].get("reel")
                if action not in RETRY_ACTIONS or not reel or not self.start_job: raise TaskError(409, "not-retryable", "this step cannot be retried automatically; open the reel and run it there")
                try: jid = self.start_job(reel, action)
                except Exception as e: raise TaskError(409, "not-retryable", f"the reel engine refused: {e}")
                t["jobs"][jid] = s["id"]; s.update(status="running", error=None, attempts=s.get("attempts", 0) + 1, started=_now(), finished=None, detail="queued again"); self._event(t, s["id"], "retry", f"job {jid}")
                return json.loads(json.dumps(self._save(t)))
            raise TaskError(409, "not-retryable", "this step needs you: open the project and do it again there")

    # ---------------------------------------------------------------- reel engine jobs (read-only mirror of server.JOBS)
    def _reel_task(self, reel):
        """The open task that owns this reel: a 'both' task bound to it, else its own 'reel' task."""
        live = [t for t in self.tasks.values() if t["project"].get("reel") == reel and t["status"] not in TERMINAL and not t.get("cancelled")]
        live.sort(key=lambda t: t["created"], reverse=True)
        return live[0] if live else None

    def mirror(self, jobs):
        """Copy the real state of each engine job onto its step. Called by the watcher thread; safe to call at any time."""
        with self.lock:
            for jid, J in list(jobs.items()):
                step_id = JOB_STEP.get(J.get("action"))
                if not step_id or J.get("created", 0) < self.started - 1: continue
                js = J.get("status")
                if self._seen.get(jid) == (js, J.get("pct")): continue        # nothing new about this job (finished jobs stay in the queue's list)
                t = self.tasks.get(self._bound.get(jid)) or next((x for x in self.tasks.values() if jid in x["jobs"]), None)
                if not t:
                    t = self._reel_task(J["project"])
                    if not t:
                        made = self.create("reel", reel=J["project"]); t = self.tasks[made["id"]]
                    t["jobs"][jid] = step_id
                self._bound[jid] = t["id"]
                s = self._step(t, step_id)
                self._seen[jid] = (js, J.get("pct")); s["action"] = J.get("action")
                if js in ("queued", "running"):
                    if step_id in ("build", "render"):        # a build or render that runs proves the earlier optional steps were not needed
                        for o in t["steps"][:t["steps"].index(s)]:
                            if o["id"] in ("plan", "narrate") and o["status"] == "pending": o.update(status="skipped", detail="not used for this reel", finished=_now())
                    self.step(t["id"], step_id, "running", detail="waiting for the engine" if js == "queued" else None, pct=J.get("pct") if js == "running" else None, _internal=True)
                elif js == "done": self.step(t["id"], step_id, "done", detail=f"{J.get('seconds')} s" if J.get("seconds") is not None else None, _internal=True)
                elif js == "cancelled": self.step(t["id"], step_id, "cancelled", _internal=True)
                elif js == "failed":
                    errs = [e for e in J.get("events", []) if e.get("event") == "error"]
                    self.step(t["id"], step_id, "failed", error=(errs[-1].get("message") if errs else None) or "the engine step failed", _internal=True)
                if js in ("done", "failed", "cancelled"): t["jobs"].pop(jid, None)
                self._sync_reel(t)

    def _sync_reel(self, t):
        """Approval is a fact of the reel project (plan or script approved), read from the engine's own step list."""
        reel = t["project"].get("reel")
        if not reel or not self.reel_facts or t["status"] in TERMINAL or t.get("cancelled"): return
        try: done = self.reel_facts(reel)
        except Exception: return
        s = self._step(t, "approve"); text = " | ".join(done)
        approved = "plan approved" in text or "script approved" in text
        drafted = "plan drafted" in text or "script prepared" in text
        want = "done" if approved else "waiting" if drafted else s["status"]
        if want != s["status"] and s["status"] not in ("failed", "cancelled", "skipped", "running"):
            self.step(t["id"], "approve", want, detail="approved in the reel" if approved else "the plan or script is ready for you to read", _internal=True)

    def watch(self, jobs, every=0.5):
        def loop():
            while True:
                try: self.mirror(jobs)
                except Exception: pass
                time.sleep(every)
        threading.Thread(target=loop, daemon=True).start()


# -------------------------------------------------------------------- routes (added to the M6 server by install())
def install(app, jobs, start_job, cancel_job, reel_facts):
    from fastapi import APIRouter, Request
    from fastapi.responses import JSONResponse
    store = TaskStore(start_job=start_job, cancel_job=cancel_job, reel_facts=reel_facts); store.watch(jobs)
    r = APIRouter()

    def guard(fn):
        try: return fn()
        except TaskError as e: return JSONResponse({"error": e.code, "detail": e.detail}, status_code=e.status)

    async def body(request):
        try: v = await request.json()
        except Exception: raise TaskError(400, "invalid", "send a JSON object")
        if not isinstance(v, dict): raise TaskError(400, "invalid", "send a JSON object")
        return v

    @r.get("/api/tasks")
    def tasks(poster: str | None = None, reel: str | None = None, active: bool = False):
        return guard(lambda: {"tasks": store.list(poster=poster, reel=reel, active=active), "invalid": store.invalid})

    @r.get("/api/tasks/{tid}")
    def task(tid: str): return guard(lambda: store.get(tid))

    @r.post("/api/tasks")
    async def create(request: Request):
        try: v = await body(request)
        except TaskError as e: return JSONResponse({"error": e.code, "detail": e.detail}, status_code=e.status)
        extra = set(v) - {"kind", "key", "poster", "reel", "meta"}
        if extra: return JSONResponse({"error": "invalid", "detail": f"unknown field {sorted(extra)[0]}"}, status_code=400)
        return guard(lambda: store.create(v.get("kind"), key=v.get("key"), poster=v.get("poster"), reel=v.get("reel"), meta=v.get("meta")))

    @r.post("/api/tasks/{tid}/step")
    async def step(tid: str, request: Request):
        try: v = await body(request)
        except TaskError as e: return JSONResponse({"error": e.code, "detail": e.detail}, status_code=e.status)
        extra = set(v) - {"step", "status", "detail", "error", "poster", "reel"}
        if extra: return JSONResponse({"error": "invalid", "detail": f"unknown field {sorted(extra)[0]}"}, status_code=400)
        return guard(lambda: store.step(tid, v.get("step"), v.get("status"), detail=v.get("detail"), error=v.get("error"), poster=v.get("poster"), reel=v.get("reel")))

    @r.post("/api/tasks/{tid}/cancel")
    def cancel(tid: str): return guard(lambda: store.cancel(tid))

    @r.post("/api/tasks/{tid}/retry")
    def retry(tid: str): return guard(lambda: store.retry(tid))

    app.include_router(r)
    return store
