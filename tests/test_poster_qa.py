"""Unit tests for app/poster_qa.py (pure; no server, no files). Run: ~/.venvs/reelstudio/bin/python -B tests/test_poster_qa.py"""
import sys, unittest
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import poster_qa as Q


def doc(*elements, texts=None):
    texts = texts or {"t": "Hello", "u": "World"}
    return {"views": [{"id": "v", "width": 1080, "height": 1350, "language": "en"}],
            "content": [{"id": k, "text": v, "language": "en", "kind": "editorial"} for k, v in texts.items()],
            "elements": [dict(e, view_id="v") for e in elements]}

def text(i="a", x=100, y=100, w=400, h=100, size=72, fill="#FFFFFF", cid="t"):
    return {"id": i, "type": "text", "content_id": cid, "x": x, "y": y, "width": w, "height": h, "style": {"font_size": size, "fill": fill}}

def shape(i="bg", x=0, y=0, w=1080, h=1350, fill="#000000"):
    return {"id": i, "type": "shape", "x": x, "y": y, "width": w, "height": h, "style": {"fill": fill, "shape": "rectangle"}}

def get(r, name, eid=None): return [c for c in r["checks"] if c["name"] == name and (eid is None or c["element_id"] == eid)]

COVER = {"en": {ord(c) for c in "HeloWrd "}, "te": {ord(c) for c in "తెలుగు"}}


class PosterQA(unittest.TestCase):
    def test_contrast_ratio_matches_wcag(self):
        self.assertAlmostEqual(Q.contrast("#FFFFFF", "#000000"), 21.0, places=2)
        self.assertAlmostEqual(Q.contrast("#777777", "#FFFFFF"), 4.48, places=2)

    def test_good_poster_passes(self):
        r = Q.check(doc(shape(), text()), COVER)
        self.assertTrue(r["passed"], r); self.assertEqual(r["warnings"], 0, r)

    def test_low_contrast_fails_and_large_text_threshold(self):
        r = Q.check(doc(shape(fill="#FFFFFF"), text(fill="#999999", size=40)), COVER)   # 2.85:1, small text
        self.assertFalse(r["passed"]); self.assertFalse(get(r, "contrast")[0]["passed"])
        r = Q.check(doc(shape(fill="#FFFFFF"), text(fill="#949494", size=52)), COVER)   # ~3.03:1, large text
        self.assertTrue(get(r, "contrast")[0]["passed"], r)
        r = Q.check(doc(shape(fill="#FFFFFF"), text(fill="#949494", size=51)), COVER)   # same colour, not large
        self.assertFalse(get(r, "contrast")[0]["passed"], r)

    def test_transparent_or_mixed_backdrop_is_a_warning_not_a_guess(self):
        r = Q.check(doc(text()), COVER)
        c = get(r, "contrast")[0]; self.assertEqual(c["level"], "warning"); self.assertTrue(r["passed"])
        r = Q.check(doc(shape(w=200, h=200), text()), COVER)                            # text spills off the shape
        self.assertEqual(get(r, "contrast")[0]["level"], "warning")

    def test_shape_above_text_is_not_its_background(self):
        r = Q.check(doc(text(), shape(fill="#FFFFFF")), COVER)                           # shape painted on top
        self.assertEqual(get(r, "contrast")[0]["level"], "warning")

    def test_canvas_and_safe_area(self):
        r = Q.check(doc(shape(), text(x=900, w=300)), COVER)
        self.assertFalse(get(r, "canvas", "a")[0]["passed"]); self.assertFalse(r["passed"])
        r = Q.check(doc(shape(), text(x=20)), COVER)
        self.assertFalse(get(r, "safe_area")[0]["passed"]); self.assertTrue(r["passed"])

    def test_missing_glyphs_and_empty_text(self):
        r = Q.check(doc(shape(), text(), texts={"t": "Hello é"}), COVER)
        g = get(r, "glyphs")[0]; self.assertFalse(g["passed"]); self.assertIn("U+00E9", g["detail"])
        r = Q.check(doc(shape(), text(), texts={"t": "తెలుగు Hello"}), COVER)
        self.assertTrue(get(r, "glyphs")[0]["passed"], r)
        r = Q.check(doc(shape(), text(), texts={"t": "  "}), COVER)
        self.assertFalse(get(r, "empty")[0]["passed"])
        r = Q.check(doc(shape(), text()), None)                                          # fonts unavailable: check skipped
        self.assertEqual(get(r, "glyphs"), [])

    def test_overlapping_text_layers(self):
        r = Q.check(doc(shape(), text("a"), text("b", y=150, cid="u")), COVER)
        self.assertEqual(len(get(r, "overlap")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
