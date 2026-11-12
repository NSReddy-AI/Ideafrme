"""The token audit catches each kind of hard-coded style and ignores ids, links and token utilities.
Run: python3 -B tests/test_token_audit.py"""
import sys, unittest
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import m6_token_audit as T


class Audit(unittest.TestCase):
    def rules(self, line): return {n for n, _ in T.scan_line(line)}

    def test_catches_hard_coded_styles(self):
        self.assertEqual(self.rules('style={{ color: "#1F3C9E" }}'), {"literal colour"})
        self.assertEqual(self.rules("background: rgba(0,0,0,.5)"), {"literal colour function"})
        self.assertEqual(self.rules('className="bg-zinc-100 text-white"'), {"palette colour class"})
        self.assertEqual(self.rules('className="rounded-md p-2"'), {"fixed radius"})
        self.assertEqual(self.rules('className="rounded p-2"'), {"fixed radius"})
        self.assertEqual(self.rules('className="transition duration-150 ease-in-out"'), {"fixed motion"})

    def test_accepts_tokens_links_and_exemptions(self):
        for ok in ('className="bg-act text-on-act rounded-btn rounded-full rounded-chip"', '<a href="#/posters">',
                   "location.hash = '#/p/' + name", "duration-[var(--motion-fast)] ease-[var(--ease-out)]",
                   "svg.querySelector('#' + b.id)", 'x = "#FFF" // token-audit: allow brand data sample'):
            self.assertEqual(T.scan_line(ok), [], ok)

    def test_current_sources_are_clean(self):
        self.assertEqual(T.main(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
