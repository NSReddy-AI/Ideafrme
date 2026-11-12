"""M6 step 5: M4 brands -> Brand Library -> engine folder, byte for byte. Uses a THROWAWAY Library under
m5/.runtime/studio-ui/ (deleted afterwards); M6's real Library and brands/ are only read.
Run: ~/.venvs/reelstudio/bin/python -B tests/test_brand_bridge.py"""
import hashlib, json, shutil, sys, tempfile, unittest, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "app"), str(ROOT / "m5")]
import brand_bridge as B                                                   # noqa: E402
from studio_manual_ui.service import RUNTIME, UIError                      # noqa: E402
from visual_poster_studio.brands import Store                             # noqa: E402

BRANDS = sorted(p.parent for p in (ROOT / "brands").glob("*/brand.json"))
LATER = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")


def tree(d): return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(d).rglob("*")) if p.is_file()}


def grant(store, asset_id, scopes=("internal_preview", "commercial_design"), destinations=("library_metadata", "reel")):
    """TEST ONLY: a synthetic rights decision. Real rights are the owner's to record."""
    lib = store.list(); a = next(x for x in lib["assets"] if x["record"]["id"] == asset_id)
    store.command(dict(action="rights", asset_id=asset_id, expected_rights=a["rights_hash"],
                       rights=dict(status="granted", authority="test fixture", evidence="synthetic test grant", scopes=list(scopes), destinations=list(destinations), expires=LATER)))


class BrandBridge(unittest.TestCase):
    def setUp(self):
        self.root = RUNTIME / f"m6-test-brands-{uuid.uuid4().hex[:8]}"; self.store = Store(self.root)
        self.out = Path(tempfile.mkdtemp(prefix="m6-brand-export-"))
        self.before = {d.name: tree(d) for d in BRANDS}

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True); shutil.rmtree(self.out, ignore_errors=True)
        self.assertEqual({d.name: tree(d) for d in BRANDS}, self.before, "brands/ must never change")

    def approve(self, r):
        return self.store.command(dict(action="approve", brand_id=r["brand_id"], expected_head=r["head"], reviewer="Test reviewer", acknowledge=True))

    def test_three_brands_import_as_drafts_with_unknown_rights(self):
        self.assertEqual([d.name for d in BRANDS], ["editing_freelance", "jagan_for_andhra", "tech_ai_tools"])
        res = [B.import_brand(self.store, d, "Test owner") for d in BRANDS]
        lib = self.store.list()
        self.assertEqual(len(lib["brands"]), 3)
        self.assertTrue(all(b["record"]["state"] == "draft" for b in lib["brands"]))
        self.assertTrue(all(a["rights"]["status"] == "unknown" for a in lib["assets"]))
        self.assertEqual(sum(r["assets"] for r in res), len(lib["assets"]))
        jagan = next(b for b in lib["brands"] if b["record"]["payload"]["name"] == "Jagan For Andhra")["record"]["payload"]
        self.assertIn("Every Telugu line approved by the user before render.", jagan["mandatory_rules"])
        self.assertEqual(B.imported(self.store).keys(), {d.name for d in BRANDS})
        with self.assertRaisesRegex(ValueError, "already in the Brand Library"): B.import_brand(self.store, BRANDS[0], "Test owner")
        with self.assertRaisesRegex(UIError, "clearance blocks approval"): self.approve(res[0])    # rights unknown -> no approval

    def test_round_trip_rebuilds_every_brand_folder_byte_for_byte(self):
        for d in BRANDS:
            r = B.import_brand(self.store, d, "Test owner")
            for i in next(b for b in self.store.list()["brands"] if b["record"]["brand_id"] == r["brand_id"])["record"]["payload"]["asset_ids"]:
                grant(self.store, i)
            self.approve(r)
            m = B.export_engine_brand(self.store, r["brand_id"], self.out / d.name)
            got = tree(self.out / d.name); got.pop("EXPORT_MANIFEST.json")
            src = {p: h for p, h in tree(d).items() if p in got}
            self.assertEqual(got, src, d.name)                                # identical bytes
            self.assertEqual(set(got), {f["path"] for f in B.plan(d)["files"]})
            self.assertEqual(json.loads((self.out / d.name / "brand.json").read_text()), json.loads((d / "brand.json").read_text()))
            self.assertEqual(m["m4_brand_id"], d.name); self.assertEqual(m["reviewer"], "Test reviewer")

    def test_export_refusals(self):
        d = BRANDS[0]; r = B.import_brand(self.store, d, "Test owner")
        with self.assertRaisesRegex(ValueError, "only an approved"): B.export_engine_brand(self.store, r["brand_id"], self.out / "draft")
        ids = next(b for b in self.store.list()["brands"] if b["record"]["brand_id"] == r["brand_id"])["record"]["payload"]["asset_ids"]
        for i in ids: grant(self.store, i, destinations=("library_metadata", "poster"))       # cleared for posters, not reels
        self.approve(r)
        with self.assertRaisesRegex(ValueError, "not cleared for commercial reel use"): B.export_engine_brand(self.store, r["brand_id"], self.out / "poster-only")
        for i in ids: grant(self.store, i)                                                      # now reels too, but after approval
        with self.assertRaisesRegex(ValueError, "rights changed since approval"): B.export_engine_brand(self.store, r["brand_id"], self.out / "stale")
        (self.out / "exists").mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"): B.export_engine_brand(self.store, r["brand_id"], self.out / "exists")
        self.assertFalse((self.out / "draft").exists() or (self.out / "poster-only").exists() or (self.out / "stale").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
