"""M6 step 3 acceptance: M5 poster / brand / Director routes on the M6 FastAPI server, plus M4 routes unchanged.
Starts a real server (M4 Python, spare port) with its OWN throwaway session and Brand Library folders under
m5/.runtime/studio-ui/ (IDEAFRAME_M6_SESSION / IDEAFRAME_M6_BRANDS), and deletes them afterwards.
No engine job, render or model runs. Run from the M6 folder:
    ~/.venvs/reelstudio/bin/python -B tests/test_m6_creative.py"""
import json, os, shutil, socket, subprocess, sys, time, unittest, uuid
import urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "m5" / ".runtime" / "studio-ui"
PAYLOAD = {"name": "తెలుగు Brand", "colors": ["#112233", "#FFFFFF"], "typography": {"english": "Inter Bold", "telugu": "Noto Sans Telugu"},
           "mandatory_rules": ["Preserve logo geometry"], "preferences": ["Calm spacing"], "inspiration": ["Editorial"], "notes": "", "asset_ids": []}
BRIEF = {"purpose": "Inform", "topic": "తెలుగు topic", "audience": "Local audience", "format": "poster", "instructions": "No invented claims."}


def free_port():
    with socket.socket() as s: s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


class Server:
    def __init__(self):
        tag = uuid.uuid4().hex[:8]
        self.session, self.brands = f"m6-test-{tag}", f"m6-test-brands-{tag}"
        self.port = free_port(); self.proc = None

    def start(self):
        env = dict(os.environ, RS_PORT=str(self.port), PYTHONDONTWRITEBYTECODE="1",
                   IDEAFRAME_M6_SESSION=self.session, IDEAFRAME_M6_BRANDS=self.brands)
        self.proc = subprocess.Popen([sys.executable, "-B", str(ROOT / "app" / "server.py")], cwd=ROOT, env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        for _ in range(100):
            try: urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/catalog", timeout=1); return
            except OSError: time.sleep(0.2)
        self.stop(); raise RuntimeError("server did not start")

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(10)
            except subprocess.TimeoutExpired: self.proc.kill(); self.proc.wait()
        self.stderr = ""
        if self.proc and self.proc.stderr: self.stderr = self.proc.stderr.read(); self.proc.stderr.close()

    def clean(self):
        for name in (self.session, self.brands):
            p = RUNTIME / name
            if p.exists() and p.resolve().is_relative_to(RUNTIME.resolve()): shutil.rmtree(p)

    def call(self, method, path, body=None, headers=None, raw=None):
        data = raw if raw is not None else (json.dumps(body, ensure_ascii=False).encode() if body is not None else None)
        h = {"Content-Type": "application/json"} if data is not None else {}
        h.update(headers or {})
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"null")


class CreativeRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.S = Server(); cls.S.start()

    @classmethod
    def tearDownClass(cls):
        cls.S.stop(); cls.S.clean()

    def ok(self, status, value, expect=200):
        self.assertEqual(status, expect, value); return value

    # -- M4 is unchanged
    def test_m4_routes_still_work(self):
        cat = self.ok(*self.S.call("GET", "/api/catalog"))
        self.assertEqual(sorted(b["id"] for b in cat["brands"]), ["editing_freelance", "jagan_for_andhra", "tech_ai_tools"])
        rows = self.ok(*self.S.call("GET", "/api/projects"))
        self.assertIn("2026-11-03_reel_002_development", [r["name"] for r in rows])

    # -- poster project lifecycle through VisualStudio
    def test_poster_project_edit_scene_save(self):
        p = self.ok(*self.S.call("POST", "/api/creative/projects", {"name": "M6 poster", "text": "తెలుగు పోస్టర్", "language": "te"}), 201)["project"]
        pid, rev = p["project_id"], p["revision"]
        p = self.ok(*self.S.call("POST", "/api/creative/action", {"project_id": pid, "expected_revision": rev, "action": "add_shape", "shape": "rectangle"}))["project"]
        self.assertEqual(p["revision"], rev + 1)
        stale = self.S.call("POST", "/api/creative/action", {"project_id": pid, "expected_revision": rev, "action": "add_shape", "shape": "ellipse"})
        self.assertEqual(stale[0], 409, stale)                           # stale revision refused, not overwritten
        p = self.ok(*self.S.call("POST", "/api/creative/action", {"project_id": pid, "expected_revision": p["revision"], "action": "undo"}))["project"]
        p = self.ok(*self.S.call("POST", "/api/creative/action", {"project_id": pid, "expected_revision": p["revision"], "action": "save"}))["project"]
        scene = self.ok(*self.S.call("POST", "/api/creative/scene", {"project_id": pid, "expected_revision": p["revision"]}))
        self.assertTrue(scene["svg"].startswith("<svg") and 'width="1080" height="1350"' in scene["svg"])
        for word in ("తెలుగు", "పోస్టర్"):                                # Telugu kept byte for byte (M5 splits runs per script)
            self.assertIn(word, scene["svg"])
        listed = self.ok(*self.S.call("GET", "/api/creative/projects"))["projects"]
        self.assertIn(pid, [x["project_id"] for x in listed])
        self.assertIsNotNone(self.ok(*self.S.call("GET", "/api/creative/fonts"))["fonts"])
        self.assertIn("analysis", self.ok(*self.S.call("GET", "/api/creative/session")))

    # -- Brand Library, bound project and deterministic Director
    def test_brand_binding_and_director(self):
        saved = self.ok(*self.S.call("POST", "/api/brands/action", {"action": "save", "brand_id": None, "expected_head": None, "payload": PAYLOAD}))
        approved = self.ok(*self.S.call("POST", "/api/brands/action", {"action": "approve", "brand_id": saved["record"]["brand_id"],
                                                                     "expected_head": saved["hash"], "reviewer": "M6 test", "acknowledge": True}))
        self.assertEqual(approved["record"]["state"], "approved")
        self.assertEqual(len(self.ok(*self.S.call("GET", "/api/brands"))["brands"]), 1)
        wrong = self.S.call("POST", "/api/brands/asset", {"action": "save", "brand_id": None, "expected_head": None, "payload": PAYLOAD})
        self.assertEqual(wrong[0], 400, wrong)                           # asset route accepts only register_asset
        p = self.ok(*self.S.call("POST", "/api/creative/workflow/create", {"name": "Bound", "text": "తెలుగు / Brief", "language": "te",
                                                                          "brief": BRIEF, "brand_hash": approved["hash"], "acknowledge": True}))["project"]
        req = {"project_id": p["project_id"], "expected_revision": p["revision"], "expected_binding": p["binding"]["hash"],
               "expected_head": p["binding"]["published_head"], "seed": 7, "acknowledge_brief": True}
        bundle = self.ok(*self.S.call("POST", "/api/creative/director/generate", req))
        self.assertEqual(len(bundle["concepts"]), 3)
        self.assertIn("deterministic", bundle["mode"])                   # no model inference behind this route
        again = self.ok(*self.S.call("POST", "/api/creative/director/generate", req))
        self.assertEqual(bundle["digest"], again["digest"])              # reproducible

    # -- request rules carried over from M5's own server
    def test_request_rules(self):
        good = {"name": "x", "text": "y", "language": "en"}
        self.assertEqual(self.S.call("POST", "/api/creative/projects", good, {"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.S.call("POST", "/api/creative/projects", good, {"Host": "evil.example"})[0], 403)
        self.assertEqual(self.S.call("POST", "/api/creative/projects", good, {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.S.call("POST", "/api/creative/projects", raw=b'{"name":"a","name":"b","text":"y","language":"en"}')[0], 400)
        self.assertEqual(self.S.call("POST", "/api/creative/projects", raw=b"x" * (64 * 1024 + 1))[0], 413)
        self.assertEqual(self.S.call("POST", "/api/creative/projects", {"name": "x", "text": "y", "language": "en", "extra": 1})[0], 400)
        self.assertEqual(self.S.call("GET", "/api/creative/projects/not-a-uuid")[0], 400)
        self.assertEqual(self.S.call("POST", "/api/creative/projects", good, {"Origin": f"http://localhost:{self.S.port}"})[0], 201)


class Resume(unittest.TestCase):
    def test_restart_resumes_same_session(self):
        S = Server()
        try:
            S.start()
            pid = S.call("POST", "/api/creative/projects", {"name": "Keep", "text": "Kept", "language": "en"})[1]["project"]["project_id"]
            p = S.call("GET", f"/api/creative/projects/{pid}")[1]["project"]
            S.call("POST", "/api/creative/action", {"project_id": pid, "expected_revision": p["revision"], "action": "save"})
            S.stop(); S.start()                                          # owner lock released on shutdown, session resumed
            listed = S.call("GET", "/api/creative/projects")
            self.assertEqual(listed[0], 200, listed)
            self.assertIn(pid, [x["project_id"] for x in listed[1]["projects"]])
        finally:
            S.stop(); S.clean()


if __name__ == "__main__":
    unittest.main(verbosity=2)
