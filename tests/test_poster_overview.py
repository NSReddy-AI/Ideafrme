"""M7-C: poster dates, concept/brief roles and export-to-poster records (app/poster_overview.py and /api/creative/overview).
Real server on a spare port with its own throwaway folders; no engine job. Run:  ~/.venvs/reelstudio/bin/python -B tests/test_poster_overview.py"""
import base64, io, json, shutil, sys, tempfile, unittest, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app")); sys.path.insert(0, str(ROOT / "tests"))
import poster_overview as po
from test_m6_creative import Server, BRIEF


class UnitTest(unittest.TestCase):
    def setUp(self): self.dir = Path(tempfile.mkdtemp(prefix="m6-overview-"))
    def tearDown(self): shutil.rmtree(self.dir, ignore_errors=True)

    def test_roles_need_a_receipt(self):
        sid = str(uuid.uuid4()); src = str(uuid.uuid4()); other = str(uuid.uuid4()); plain = str(uuid.uuid4()); digest = "d" * 64
        made = str(uuid.uuid5(uuid.UUID(sid), digest + ":editorial"))
        (self.dir / "concept-proposals").mkdir()
        (self.dir / "concept-proposals" / f"{digest}.json").write_text(json.dumps({"digest": digest, "inputs": {"source_project": src}, "concepts": [{"id": "editorial"}, {"id": "split"}]}), encoding="utf-8")
        (self.dir / "concept-proposals" / "broken.json").write_text("{ nope", encoding="utf-8")
        r = po.roles(self.dir, sid, {src, made, other, plain}, {src, made, other})
        self.assertEqual((r[made], r[src], r[other], r[plain]), (("concept", src), ("brief-source", None), ("brief", None), ("plain", None)))
        self.assertEqual(po.roles(self.dir, str(uuid.uuid4()), {src, made}, {src, made})[made], ("brief", None), "another session's receipt proves nothing")
        self.assertEqual(po.roles(self.dir / "nowhere", sid, {src}, set())[src], ("plain", None))

    def test_modified_and_index(self):
        self.assertIsNone(po.modified(self.dir, "x")); (self.dir / "bound-projects" / "x" / "c").mkdir(parents=True); (self.dir / "bound-projects" / "x" / "c" / "f.json").write_text("{}")
        self.assertRegex(po.modified(self.dir, "x"), r"^\d{4}-\d\d-\d\d \d\d:\d\d$")
        ix = po.ExportIndex(self.dir / "links"); self.assertEqual(ix.all(), {})
        ix.add("/some/where/draft-abc", "p1", "Reading day", 3); ix.add("/some/where/draft-def", "p2", "తెలుగు", 0)
        self.assertEqual({k: (v["project_id"], v["name"], v["revision"]) for k, v in ix.all().items()}, {"draft-abc": ("p1", "Reading day", 3), "draft-def": ("p2", "తెలుగు", 0)})
        ix.file.write_text("{ damaged", encoding="utf-8"); self.assertEqual(ix.all(), {}, "a damaged index is read as empty, never as wrong names")


class RouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.S = Server(); cls.S.start()
    @classmethod
    def tearDownClass(cls): cls.S.stop(); cls.S.clean()
    def ok(self, st, body): self.assertLess(st, 300, body); return body

    def test_overview(self):
        plain = self.ok(*self.S.call("POST", "/api/creative/projects", {"name": "Plain", "text": "Hello", "language": "en"}))["project"]
        src = self.ok(*self.S.call("POST", "/api/creative/workflow/create", {"name": "Brief one", "text": "చదువుల పండుగ", "language": "te", "brief": BRIEF, "brand_hash": None, "acknowledge": True}))["project"]
        lone = self.ok(*self.S.call("POST", "/api/creative/workflow/create", {"name": "Brief two", "text": "Reading day", "language": "en", "brief": BRIEF, "brand_hash": None, "acknowledge": True}))["project"]
        b = (self.ok(*self.S.call("GET", f"/api/creative/projects/{src['project_id']}"))["project"])["binding"]
        req = {"project_id": src["project_id"], "expected_revision": src["revision"], "expected_binding": b["hash"], "expected_head": b["published_head"], "seed": 7, "acknowledge_brief": True}
        bundle = self.ok(*self.S.call("POST", "/api/creative/director/generate", req))
        made = self.ok(*self.S.call("POST", "/api/creative/director/select", {"source": req, "bundle_digest": bundle["digest"], "concept_id": bundle["concepts"][0]["id"], "acknowledge_rules": True}))["project"]
        o = self.ok(*self.S.call("GET", "/api/creative/overview")); rows = {p["project_id"]: p for p in o["posters"]}
        self.assertEqual((rows[made["project_id"]]["role"], rows[made["project_id"]]["source"], rows[made["project_id"]]["source_name"]), ("concept", src["project_id"], "Brief one"))
        self.assertEqual((rows[src["project_id"]]["role"], rows[lone["project_id"]]["role"], rows[plain["project_id"]]["role"]), ("brief-source", "brief", "plain"))
        self.assertTrue(all(rows[x["project_id"]]["modified"] for x in (src, lone, made)), {k: v["modified"] for k, v in rows.items()}); self.assertEqual(o["exports"], [])
        self.assertIsNone(rows[plain["project_id"]]["modified"], "a poster that was never saved has no date; none is invented")
        # an export is recorded against its poster by M6; M5's own record is unchanged
        start = self.ok(*self.S.call("POST", "/api/creative/export/begin", {"project_id": made["project_id"], "expected_revision": made["revision"]}))
        done = self.ok(*self.S.call("POST", "/api/creative/export/finish", {"token": start["token"], "revision": made["revision"], "png": None, "qa": {"fonts_loaded": True, "overflow": [], "parity": False, "embedded_fonts": False}}))
        self.assertNotIn("project_id", done["manifest"])
        e = self.ok(*self.S.call("GET", "/api/creative/overview"))["exports"]
        self.assertEqual(len(e), 1); self.assertEqual((e[0]["poster"]["project_id"], e[0]["poster"]["name"], e[0]["poster"]["revision"], e[0]["state"]), (made["project_id"], made["name"], made["revision"], "draft"))
        self.assertEqual(self.S.call("POST", "/api/creative/overview", {})[0] >= 400, True, "the overview is read-only")


if __name__ == "__main__":
    unittest.main(verbosity=1)
