from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
class Markup(HTMLParser):
    def __init__(self):super().__init__();self.ids={};self.labels=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:raise AssertionError('Duplicate DOM id')
            self.ids[attrs['id']]=(tag,attrs)
        if tag=='label' and 'for' in attrs:self.labels.append(attrs['for'])
class EditingUITests(unittest.TestCase):
    def test_semantic_controls_and_no_duplicate_ids(self):
        doc=Markup();doc.feed((ROOT/'visual_poster_studio/index.html').read_text())
        for identity in doc.labels:self.assertIn(identity,doc.ids)
        self.assertEqual(doc.ids['editor-root'][1]['tabindex'],'-1')
        self.assertEqual(doc.ids['layers'][1]['aria-describedby'],'layer-help')
        self.assertEqual(doc.ids['layer-text'][1]['aria-describedby'],'composition-status text-status')
        self.assertIn('preview-zoom',doc.ids)
    def test_modules_are_fixed_local_routes(self):
        from visual_poster_studio.server import ASSETS
        self.assertEqual(ASSETS['/editing.mjs'][0],'editing.mjs');self.assertIn('/editing_browser.mjs',ASSETS)
        self.assertNotIn('/arbitrary',ASSETS)
    def test_render_profile_remains_fixed(self):
        from visual_poster_studio.scene import PROFILE
        self.assertEqual((PROFILE['width'],PROFILE['height'],PROFILE['background']),(1080,1350,'transparent'))
