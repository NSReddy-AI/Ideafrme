import copy
import hashlib
import xml.etree.ElementTree as ET
from test_service import ServiceCase
from studio_manual_ui.service import UIError
from visual_poster_studio.scene import build_scene

class SceneTests(ServiceCase):
    # Reuse the same isolated fixture setup, without inheriting service test methods below.
    def test_deterministic_source_immutable(self):
        d=self.s.manual.document(self.p['project_id']);before=copy.deepcopy(d)
        a=build_scene(d,self.s.fonts);b=build_scene(d,self.s.fonts)
        self.assertEqual(a,b);self.assertEqual(d,before);self.assertEqual(hashlib.sha256(a['svg'].encode()).hexdigest(),a['svg_sha256'])
    def test_geometry_order(self):
        self.action('add_shape',shape='rectangle');self.action('add_shape',shape='ellipse')
        a=self.s.scene(self.p['project_id'],self.p['revision']);root=ET.fromstring(a['svg']);ns={'s':'http://www.w3.org/2000/svg'}
        self.assertEqual([b['element_id'] for b in a['boxes']],[e['id'] for e in self.p['elements']]);self.assertEqual(root.find('.//s:rect',ns).get('width'),'300');self.assertEqual(root.find('.//s:ellipse',ns).get('rx'),'150.0')
    def test_unicode_escaping(self):
        value='<script>& " é é తెలుగు';self.action('edit_text',element_id=self.p['elements'][0]['id'],text=value)
        a=self.s.scene(self.p['project_id'],self.p['revision']);root=ET.fromstring(a['svg']);texts=root.findall('.//{http://www.w3.org/2000/svg}text')
        self.assertEqual(''.join(texts[0].itertext()),value);self.assertNotIn('<script>',a['svg'])
    def test_missing_glyph(self):
        self.action('edit_text',element_id=self.p['elements'][0]['id'],text='🦄')
        with self.assertRaises(UIError):self.s.scene(self.p['project_id'],self.p['revision'])
    def test_unsupported_view(self):
        d=self.s.manual.document(self.p['project_id']);d['views'][0]['width']=4096
        with self.assertRaises(UIError):build_scene(d,self.s.fonts)
    def test_unsupported_style(self):
        d=self.s.manual.document(self.p['project_id']);d['elements'][0]['style']['rotation']=30
        with self.assertRaises(UIError):build_scene(d,self.s.fonts)
    def test_controls_refused(self):
        self.action('edit_text',element_id=self.p['elements'][0]['id'],text='a\tb')
        with self.assertRaises(UIError):self.s.scene(self.p['project_id'],self.p['revision'])

    def test_embedded_font_notices(self):
        scene=self.s.scene(self.p['project_id'],self.p['revision'])
        root=ET.fromstring(scene['svg']);metadata=root.find('{http://www.w3.org/2000/svg}metadata').text
        self.assertIn('Copyright 2016 The Inter Project Authors',metadata)
        self.assertIn('Copyright 2022 The Noto Project Authors',metadata)
        self.assertEqual(metadata.count('SIL OPEN FONT LICENSE Version 1.1'),2)
