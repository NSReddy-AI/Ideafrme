import unittest
from unittest.mock import patch
from studio_manual_ui.service import UIError
from visual_poster_studio.fonts import Fonts,SPECS

class FontTests(unittest.TestCase):
    def test_pins_and_coverage(self):
        f=Fonts();self.assertEqual(set(f.faces),{'en','te'})
        for lang,face in f.faces.items():self.assertEqual(face['hash'],SPECS[lang][1])
        self.assertIn(ord('శ'),f.faces['te']['coverage']);self.assertIn(ord('́'),f.faces['en']['coverage'])
    def test_changed_font(self):
        with patch('visual_poster_studio.fonts.read',return_value=b'bad'):
            with self.assertRaises(UIError):Fonts()
    def test_missing_font(self):
        with patch('visual_poster_studio.fonts.read',side_effect=FileNotFoundError):
            with self.assertRaises(UIError):Fonts()
    def test_mixed_cluster_runs(self):
        runs=Fonts().runs('శ్రీ\u200d é');self.assertEqual(''.join(r[1] for r in runs),'శ్రీ\u200d é');self.assertEqual(runs[0][0],'te')
    def test_unsupported_glyph(self):
        with self.assertRaises(UIError):Fonts().runs('🦄')
