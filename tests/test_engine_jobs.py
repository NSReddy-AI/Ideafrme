"""Isolated engine job root (app/engine_jobs.py), without rendering. The full reel_002 render is recorded in
tests/acceptance/m6_step7_reel002_parity. Run: ~/.venvs/reelstudio/bin/python -B tests/test_engine_jobs.py"""
import hashlib, json, shutil, sys, unittest
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import engine_jobs as J                                     # noqa: E402

P = "2026-11-03_reel_002_development"


class JobRoot(unittest.TestCase):
    def test_job_root_is_a_faithful_isolated_copy(self):
        before = J._tree(ROOT / "projects" / P, skip=("__pycache__",))
        root, brand = J.make_root(P)
        try:
            self.assertTrue(root.resolve().is_relative_to((ROOT / "jobs").resolve()))
            for f in (ROOT / "engine").iterdir():                                  # engine code copied byte for byte
                if f.is_file() and f.suffix in (".py", ".json"): self.assertEqual((root / "engine" / f.name).read_bytes(), f.read_bytes(), f.name)
            for d in ("fonts", "models"): self.assertTrue((root / "engine" / d).is_symlink())
            self.assertFalse((root / "engine" / "fonts").resolve() == (root / "engine" / "fonts"))
            self.assertEqual(J._tree(root / "brands" / "jagan_for_andhra"), J._tree(ROOT / "brands" / "jagan_for_andhra"))
            self.assertEqual(J._tree(root / "projects" / P, skip=("__pycache__",)), before)
            self.assertFalse((root / "projects" / P).is_symlink())                  # a copy: the original can never be written
            self.assertEqual(list((root / "exports").iterdir()), [])
            self.assertEqual(brand["kind"], "folder")
        finally:
            shutil.rmtree(root)
        self.assertEqual(J._tree(ROOT / "projects" / P, skip=("__pycache__",)), before)

    def test_unknown_project_is_refused(self):
        with self.assertRaises(ValueError): J.make_root("no_such_project")


if __name__ == "__main__":
    unittest.main(verbosity=2)
