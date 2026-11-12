"""approved-content@1 derivation (app/approved_content.py). Fixtures are copies of two real approved M4 projects
(tests/fixtures/approved_content); tampering happens on temporary copies. Run: ~/.venvs/reelstudio/bin/python -B tests/test_approved_content.py"""
import json, shutil, sys, tempfile, unittest
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import approved_content as A                                    # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "approved_content"; ENGINE = str(ROOT / "engine")


class Derive(unittest.TestCase):
    def setUp(self): self.tmp = Path(tempfile.mkdtemp(prefix="m6-approved-"))
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)

    def copy(self, name, as_=None):
        d = self.tmp / (as_ or name); shutil.copytree(FIX / name, d); return d

    def edit(self, path, fn):
        v = json.loads(path.read_text(encoding="utf-8")); fn(v); path.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")

    def test_speaker_plan(self):
        d = A.derive(FIX / "speaker", ENGINE)
        self.assertEqual(d["format"], "ideaframe-approved-content@1"); self.assertEqual([a["type"] for a in d["approvals"]], ["plan"])
        by = {i["id"]: i for i in d["items"]}
        self.assertEqual(by["hook.line2"]["kind"], "quote"); self.assertTrue(by["hook.line2"]["verbatim"])     # “ ” = the speaker's words
        self.assertEqual(by["hook.line1"]["kind"], "hook"); self.assertEqual(by["hook.line1"]["language"], "te")
        self.assertIn("headline.2", by); self.assertIn("tag", by); self.assertIn("post.intro", by)
        self.assertEqual(sum(i["kind"] == "number" for i in d["items"]), 5)
        self.assertEqual(len({i["id"] for i in d["items"]}), len(d["items"]))                                # unique ids
        self.assertEqual(A.derive(FIX / "speaker", ENGINE)["fingerprint"], d["fingerprint"])                    # deterministic

    def test_narrated_script(self):
        d = A.derive(FIX / "narrated", ENGINE)
        self.assertEqual([a["type"] for a in d["approvals"]], ["narration"])
        self.assertTrue(all(i["kind"] == "script" for i in d["items"])); self.assertGreater(len(d["items"]), 3)

    def test_any_change_after_approval_is_refused(self):
        d = self.copy("speaker"); self.edit(d / "build/plan.json", lambda p: p["facts"]["beats"][0]["graphic"].update(label="changed"))
        with self.assertRaises(A.ApprovalError) as e: A.derive(d, ENGINE)
        self.assertEqual(e.exception.code, "PLAN_STALE")
        d = self.copy("speaker", "s2"); self.edit(d / "project.json", lambda j: j.__setitem__("title", ["other", "title"]))
        with self.assertRaises(A.ApprovalError) as e: A.derive(d, ENGINE)
        self.assertEqual(e.exception.code, "PLAN_STALE")
        d = self.copy("narrated"); self.edit(d / "build/narration.json", lambda n: n["lines"][0].update(text=n["lines"][0]["text"] + "!"))
        with self.assertRaises(A.ApprovalError) as e: A.derive(d, ENGINE)
        self.assertEqual(e.exception.code, "SCRIPT_STALE")

    def test_unapproved_gives_nothing(self):
        d = self.copy("speaker"); self.edit(d / "build/plan.json", lambda p: p.update(approved=False))
        with self.assertRaises(A.ApprovalError) as e: A.derive(d, ENGINE)
        self.assertEqual(e.exception.code, "PLAN_NOT_APPROVED")

    def test_hand_approved_baseline_is_labelled(self):
        d = A.derive(ROOT / "projects" / "2026-11-03_reel_002_development", ENGINE)
        self.assertEqual(d["approvals"][0]["type"], "project"); self.assertIsNone(d["approvals"][0]["hash"])

    def test_item_status(self):
        d = A.derive(FIX / "speaker", ENGINE); it = d["items"][0]
        self.assertEqual(A.item_status(d, it["id"], it["sha256"], it["text"]), (True, "exactly as approved"))
        self.assertFalse(A.item_status(d, it["id"], it["sha256"], it["text"] + " ")[0])
        self.assertFalse(A.item_status(d, it["id"], "0" * 64, it["text"])[0])
        self.assertFalse(A.item_status(A.ApprovalError("PLAN_STALE", "x"), it["id"], it["sha256"], it["text"])[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
