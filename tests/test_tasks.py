"""M7-B B4C-1: durable local tasks (app/tasks.py). No engine job, render or model runs: the engine queue is a plain dict here.
Run from the M6 folder:  ~/.venvs/reelstudio/bin/python -B tests/test_tasks.py"""
import json, os, shutil, socket, subprocess, sys, tempfile, threading, time, unittest, urllib.request, urllib.error, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import tasks
from tasks import TaskStore, TaskError


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="m6-tasks-")); self.started = []; self.cancelled = []; self.facts = []
        self.store = self.new()
    def tearDown(self): shutil.rmtree(self.dir, ignore_errors=True)
    def new(self):
        def start(name, action): jid = uuid.uuid4().hex[:10]; self.started.append((name, action, jid)); return jid
        return TaskStore(self.dir, start_job=start, cancel_job=self.cancelled.append, reel_facts=lambda name: list(self.facts))
    def status(self, t, sid): return next(s for s in t["steps"] if s["id"] == sid)["status"]

    def test_create_and_real_progress(self):
        t = self.store.create("poster", key="k1", poster="p1", meta={"prompt": "చదువుల పండుగ పోస్టర్", "output": "poster"})
        self.assertEqual((t["status"], t["meta"]["prompt"], len(t["steps"])), ("pending", "చదువుల పండుగ పోస్టర్", 8))
        self.assertEqual(self.store.create("poster", key="k1")["id"], t["id"], "same key gives the same task, not a second one")
        tid = t["id"]
        for sid in ("interpret", "brief"): self.store.step(tid, sid, "running"); t = self.store.step(tid, sid, "done")
        t = self.store.step(tid, "concepts", "running"); self.assertEqual(t["status"], "running")
        t = self.store.step(tid, "concepts", "done", detail="3 concepts")
        self.assertEqual((t["status"], self.status(t, "choose")), ("waiting", "waiting"), "the choice now really waits for the person")
        t = self.store.step(tid, "choose", "done"); t = self.store.step(tid, "poster", "done", poster="p2")
        self.assertEqual(t["project"]["posters"], ["p1", "p2"]); self.assertEqual(self.status(t, "review"), "waiting")
        self.assertEqual(json.loads((self.dir / f"{tid}.json").read_text(encoding="utf-8"))["rev"], t["rev"], "what is on disk is what was returned")
        self.assertEqual([p.name for p in self.dir.iterdir() if p.name.startswith(".")], [], "no temporary files left behind")

    def test_failure_is_never_a_finish(self):
        tid = self.store.create("poster")["id"]
        with self.assertRaises(TaskError): self.store.step(tid, "brief", "failed")                 # a failure needs its error
        t = self.store.step(tid, "brief", "failed", error="Enter purpose, topic and audience.")
        self.assertEqual((t["status"], self.status(t, "brief")), ("failed", "failed"))
        with self.assertRaises(TaskError) as c: self.store.step(tid, "concepts", "done")
        self.assertEqual(c.exception.status, 409, "nothing after a failed step can be marked done")
        t = self.store.retry(tid); self.assertEqual((t["status"], self.status(t, "brief")), ("pending", "pending"))
        t = self.store.step(tid, "brief", "running"); t = self.store.step(tid, "brief", "done")
        self.assertEqual(next(s for s in t["steps"] if s["id"] == "brief")["attempts"], 1)

    def test_invalid_requests(self):
        tid = self.store.create("reel", reel="2026-11-12_x")["id"]
        for call in (lambda: self.store.create("movie"), lambda: self.store.get("../../etc"), lambda: self.store.get("0" * 12),
                     lambda: self.store.step(tid, "nope", "done"), lambda: self.store.step(tid, "plan", "finished"),
                     lambda: self.store.step(tid, "render", "done"), lambda: self.store.step(tid, "approve", "done"),
                     lambda: self.store.create("poster", meta={"prompt": "x" * 5000}), lambda: self.store.retry(tid)):
            with self.assertRaises(TaskError): call()
        self.assertEqual(self.store.get(tid)["status"], "pending", "refused requests change nothing")

    def test_engine_jobs_are_mirrored_not_invented(self):
        jobs = {}; reel = "2026-11-12_demo"
        jobs["j1"] = dict(id="j1", project=reel, action="build", status="queued", pct=0, events=[], created=time.time())
        self.store.mirror(jobs); t = self.store.list(reel=reel)[0]
        self.assertEqual((t["kind"], t["status"], self.status(t, "build"), self.status(t, "plan"), self.status(t, "narrate")), ("reel", "running", "running", "skipped", "skipped"))
        jobs["j1"].update(status="running", pct=42); self.store.mirror(jobs)
        self.assertEqual(next(s for s in self.store.get(t["id"])["steps"] if s["id"] == "build")["pct"], 42, "progress is the engine's own number")
        jobs["j1"].update(status="failed", events=[dict(event="error", code="STEP_CRASHED", message="ffmpeg stopped")]); self.store.mirror(jobs)
        t = self.store.get(t["id"]); b = next(s for s in t["steps"] if s["id"] == "build")
        self.assertEqual((t["status"], b["status"], b["error"], b["pct"]), ("failed", "failed", "ffmpeg stopped", None))
        t = self.store.retry(t["id"]); self.assertEqual((self.started[-1][:2], t["status"]), ((reel, "build"), "retrying"))
        jid = self.started[-1][2]; jobs[jid] = dict(id=jid, project=reel, action="build", status="done", pct=100, events=[], created=time.time(), seconds=7.8)
        self.store.mirror(jobs); t = self.store.get(t["id"]); self.assertEqual((self.status(t, "build"), self.status(t, "render"), t["status"]), ("done", "pending", "pending"))
        self.facts[:] = ["project: a / b / c", "script prepared (check the ❓ lines)"]; self.assertEqual(self.status(self.store.get(t["id"]), "approve"), "waiting")
        self.facts[:] = ["project: a / b / c", "script approved"]; self.assertEqual(self.status(self.store.get(t["id"]), "approve"), "done")
        jobs["j9"] = dict(id="j9", project=reel, action="render", status="done", pct=100, events=[], created=time.time(), seconds=17.9)
        self.store.mirror(jobs); self.assertEqual(self.store.get(t["id"])["status"], "completed"); self.assertEqual(len(self.store.list(reel=reel)), 1, "one task for the reel, not one per job")

    def test_approval_job_is_not_retried(self):
        jobs = {"a1": dict(id="a1", project="r", action="approve", status="failed", pct=0, events=[dict(event="error", message="choose A, B, C or D")], created=time.time())}
        self.store.mirror(jobs); t = self.store.list(reel="r")[0]; self.assertEqual(self.status(t, "approve"), "failed")
        with self.assertRaises(TaskError) as c: self.store.retry(t["id"])
        self.assertEqual((c.exception.code, self.started), ("not-retryable", []), "an approval is never repeated automatically")

    def test_cancel(self):
        jobs = {"j1": dict(id="j1", project="r", action="render", status="running", pct=10, events=[], created=time.time())}
        self.store.mirror(jobs); t = self.store.list(reel="r")[0]
        t = self.store.cancel(t["id"]); self.assertEqual((t["status"], self.cancelled, self.status(t, "render")), ("cancelled", ["j1"], "cancelled"))
        self.assertEqual(self.store.cancel(t["id"])["status"], "cancelled", "cancelling twice is harmless")
        with self.assertRaises(TaskError): self.store.retry(t["id"])
        tid = self.store.create("poster")["id"]; self.store.cancel(tid)
        with self.assertRaises(TaskError): self.store.step(tid, "brief", "done")

    def test_restart_recovery(self):
        a = self.store.create("poster")["id"]; self.store.step(a, "interpret", "done"); self.store.step(a, "brief", "done"); self.store.step(a, "concepts", "running")
        b = self.store.create("poster")["id"]
        for sid in ("interpret", "brief", "concepts"): self.store.step(b, sid, "done")
        jobs = {"j1": dict(id="j1", project="r", action="render", status="running", pct=60, events=[], created=time.time())}; self.store.mirror(jobs); c = self.store.list(reel="r")[0]["id"]
        (self.dir / "ffffffffffff.json").write_text("{ not json", encoding="utf-8"); (self.dir / "eeeeeeeeeeee.json").write_text(json.dumps({"format": "other"}), encoding="utf-8")
        again = self.new()
        ta, tb, tc = again.get(a), again.get(b), again.get(c)
        self.assertEqual((ta["status"], self.status(ta, "concepts")), ("failed", "failed"), "a step that was running is not assumed finished")
        self.assertIn("restarted", next(s for s in ta["steps"] if s["id"] == "concepts")["error"])
        self.assertEqual((tb["status"], self.status(tb, "choose")), ("waiting", "waiting"), "waiting for the person survives a restart")
        self.assertEqual((tc["status"], self.status(tc, "render"), tc["jobs"]), ("failed", "failed", {}))
        self.assertEqual(sorted(i["file"] for i in again.invalid), ["eeeeeeeeeeee.json", "ffffffffffff.json"]); self.assertTrue((self.dir / "ffffffffffff.json").exists(), "a damaged file is reported, not deleted")
        self.assertEqual(again.retry(a)["status"], "pending"); again.retry(c); self.assertEqual(self.started[-1][:2], ("r", "render"))

    def test_concurrent_access(self):
        tid = self.store.create("poster")["id"]; errors = []
        def work(i):
            try:
                for n in range(25): self.store.step(tid, "interpret", "running", detail=f"w{i}-{n}"); self.store.create("poster", key=f"same-key")
            except Exception as e: errors.append(e)
        th = [threading.Thread(target=work, args=(i,)) for i in range(8)]; [t.start() for t in th]; [t.join() for t in th]
        self.assertEqual(errors, []); disk = tasks.validate(json.loads((self.dir / f"{tid}.json").read_text(encoding="utf-8")))
        self.assertEqual(disk["rev"], self.store.get(tid)["rev"]); self.assertEqual(len([t for t in self.store.list() if t.get("key") == "same-key"]), 1)


class RouteTest(unittest.TestCase):
    """The same rules through the real server (spare port, its own throwaway folders)."""
    @classmethod
    def setUpClass(cls):
        tag = uuid.uuid4().hex[:8]; cls.names = dict(IDEAFRAME_M6_SESSION=f"m6-test-{tag}", IDEAFRAME_M6_BRANDS=f"m6-test-brands-{tag}", IDEAFRAME_M6_LINKS=f"m6-test-links-{tag}", IDEAFRAME_M6_TASKS=f"tasks-test-{tag}")
        with socket.socket() as s: s.bind(("127.0.0.1", 0)); cls.port = s.getsockname()[1]
        cls.start()
    @classmethod
    def start(cls):
        cls.proc = subprocess.Popen([sys.executable, "-B", str(ROOT / "app" / "server.py")], cwd=ROOT, env=dict(os.environ, RS_PORT=str(cls.port), PYTHONDONTWRITEBYTECODE="1", **cls.names), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try: urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/api/tasks", timeout=1); return
            except OSError: time.sleep(0.2)
        raise RuntimeError("server did not start")
    @classmethod
    def stop(cls):
        cls.proc.terminate()
        try: cls.proc.wait(10)
        except subprocess.TimeoutExpired: cls.proc.kill(); cls.proc.wait()
    @classmethod
    def tearDownClass(cls):
        cls.stop(); rt = ROOT / "m5" / ".runtime" / "studio-ui"
        for k in ("IDEAFRAME_M6_SESSION", "IDEAFRAME_M6_BRANDS", "IDEAFRAME_M6_LINKS"): shutil.rmtree(rt / cls.names[k], ignore_errors=True)
        shutil.rmtree(ROOT / "jobs" / cls.names["IDEAFRAME_M6_TASKS"], ignore_errors=True)
    def call(self, method, path, body=None):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=json.dumps(body).encode() if body is not None else None, method=method, headers={"Content-Type": "application/json"} if body is not None else {})
        try:
            with urllib.request.urlopen(req, timeout=20) as r: return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")

    def test_routes_and_restart(self):
        st, t = self.call("POST", "/api/tasks", {"kind": "both", "key": "walk-1", "meta": {"prompt": "Poster and reel for Reading Day", "output": "both"}})
        self.assertEqual((st, t["kind"], len(t["steps"])), (200, "both", 14)); tid = t["id"]
        self.assertEqual(self.call("POST", "/api/tasks", {"kind": "both", "key": "walk-1"})[1]["id"], tid)
        self.assertEqual(self.call("POST", f"/api/tasks/{tid}/step", {"step": "interpret", "status": "done"})[0], 200)
        self.assertEqual(self.call("POST", f"/api/tasks/{tid}/step", {"step": "brief", "status": "running"})[1]["status"], "running")
        for bad, want in ((("POST", "/api/tasks", {"kind": "x"}), 400), (("POST", "/api/tasks", {"kind": "poster", "extra": 1}), 400), (("GET", "/api/tasks/nope"), 400), (("GET", "/api/tasks/" + "0" * 12), 404),
                          (("POST", f"/api/tasks/{tid}/step", {"step": "render", "status": "done"}), 409), (("POST", f"/api/tasks/{tid}/step", {"step": "brief", "status": "failed"}), 400), (("POST", f"/api/tasks/{tid}/retry"), 409)):
            self.assertEqual(self.call(*bad)[0], want, bad)
        self.assertEqual(self.call("GET", "/api/catalog")[0], 200, "existing routes still answer")
        self.stop(); self.start()                                   # restart: the running step is reported as interrupted, the prompt is kept
        st, t = self.call("GET", f"/api/tasks/{tid}"); brief = next(s for s in t["steps"] if s["id"] == "brief")
        self.assertEqual((st, t["status"], brief["status"], t["meta"]["prompt"]), (200, "failed", "failed", "Poster and reel for Reading Day")); self.assertIn("restarted", brief["error"])
        self.assertEqual(self.call("POST", f"/api/tasks/{tid}/retry")[1]["status"], "pending")
        self.assertEqual(self.call("POST", f"/api/tasks/{tid}/cancel")[1]["status"], "cancelled")
        self.assertEqual(self.call("GET", "/api/tasks?active=true")[1]["tasks"], [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
