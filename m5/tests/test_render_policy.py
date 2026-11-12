"""Phase 2 pure tests: no renderer processes, installs or external writes."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from creative_core import CreativeError, approve, fingerprint, load, new_document
from poster_render import build_scene, render_identity
from poster_render.approval import check_export

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'examples/posters'


class RenderPolicyTests(unittest.TestCase):
    def setUp(self):
        self.doc=load(PROJECT)
        self.policy=json.loads((PROJECT/'render-policies.json').read_text())['editorial']

    def reject(self,doc=None,policy=None):
        with self.assertRaises(CreativeError):
            build_scene(doc or self.doc,PROJECT,'editorial',policy or self.policy)

    def test_layer_mapping_and_source_preserved(self):
        original=deepcopy(self.doc)
        scene=build_scene(self.doc,PROJECT,'editorial',self.policy)
        self.assertEqual(self.doc,original)
        for el in self.doc['elements']:
            if el['view_id']=='editorial':self.assertIn('id="layer-'+el['id']+'"',scene['svg'])
        self.assertEqual(scene['width'],1080)

    def test_unapproved_draft_and_final_gate(self):
        draft=check_export(self.doc,self.policy,'engine',draft=True)
        self.assertTrue(draft['draft']);self.assertFalse(draft['approved'])
        with self.assertRaises(CreativeError):check_export(self.doc,self.policy,'engine',draft=False)
        doc=approve(self.doc,'synthetic-test-only',PROJECT)
        with self.assertRaises(CreativeError):check_export(doc,self.policy,'engine',draft=False)
        receipt={'identity':render_identity(doc,self.policy,'engine'),'reviewer':'synthetic-test-only'}
        self.assertTrue(check_export(doc,self.policy,'engine',receipt,draft=False)['approved'])
        with self.assertRaises(CreativeError):check_export(doc,self.policy,'changed-engine',receipt,draft=False)

    def test_render_identity_covers_policy(self):
        one=render_identity(self.doc,self.policy,'engine')
        self.policy['safe_margin']=60
        self.assertNotEqual(one,render_identity(self.doc,self.policy,'engine'))

    def test_fractional_and_excessive_views(self):
        for width,height in [(1080.5,1350),(32768,32768),(0,1350)]:
            doc=deepcopy(self.doc);doc['views'][0].update(width=width,height=height)
            self.reject(doc)

    def test_external_paint_rejected(self):
        for paint in ['url(https://example.com/a)','red; background:url(file:///etc/passwd)','<script/>']:
            doc=deepcopy(self.doc);doc['elements'][0]['style']['fill']=paint;self.reject(doc)

    def test_missing_font_rejected(self):
        del self.doc['elements'][0]['style']['font_asset_id'];self.reject()

    def test_outside_safe_area_rejected(self):
        self.doc['elements'][0]['x']=0;self.reject()

    def test_rotated_bounds_refused(self):
        self.doc['elements'][0]['style']['rotation']=45;self.reject()

    def test_brand_required_layer(self):
        self.policy['required_elements']=['absent'];self.reject()

    def test_brand_palette(self):
        self.doc['elements'][0]['style']['fill']='#ff0000';self.reject()

    def test_markup_escaped_not_executed(self):
        self.doc['content'][0]['text']='<script>alert(1)</script> & text'
        svg=build_scene(self.doc,PROJECT,'editorial',self.policy)['svg']
        self.assertNotIn('<script>',svg);self.assertIn('&lt;script&gt;',svg)

    def test_unsupported_video(self):
        el=self.doc['elements'][0]
        el.update(type='video',asset_id='te');el.pop('content_id')
        self.reject()

    def test_unsafe_svg_assets(self):
        payloads=[b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
          b'<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com"/></svg>',
          b'<!DOCTYPE svg [<!ENTITY a SYSTEM "file:///etc/passwd">]><svg/>',
          b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>']
        with tempfile.TemporaryDirectory(dir=ROOT/'.runtime') as folder:
            root=Path(folder)
            for data in payloads:
                (root/'asset.svg').write_bytes(data)
                doc=new_document();doc['assets']=[{'id':'evil','kind':'vector','path':'asset.svg',
                    'sha256':hashlib.sha256(data).hexdigest()}]
                policy=deepcopy(self.policy);policy['fonts']={};policy['required_elements']=[]
                # Add fonts by read-only references would escape the fixture; isolate the asset parser.
                from poster_render.scene import _asset
                with self.assertRaises(CreativeError):_asset(doc['assets'][0],root)

    def test_asset_hash_and_path_escape(self):
        for key,value in [('path','../outside.ttf'),('sha256','0'*64)]:
            doc=deepcopy(self.doc);doc['assets'][0][key]=value;self.reject(doc)

    def test_unsupported_glyph_refused(self):
        self.doc['content'][0]['text']='Unapproved emoji \U0001f600';self.reject()

    def test_telugu_requires_telugu_font(self):
        self.doc['content'][0]['text']='తెలుగు';self.reject()

    def test_other_views_and_explicit_newlines(self):
        policies=json.loads((PROJECT/'render-policies.json').read_text())
        for view in ('telugu','cinematic'):
            result=build_scene(self.doc,PROJECT,view,policies[view])
            self.assertIn('<tspan',result['svg'])
            self.assertEqual(fingerprint(self.doc),result['document_fingerprint'])

    def test_invalid_vector_reference_no_external_read(self):
        from poster_render.scene import _safe_svg
        with self.assertRaises(CreativeError):_safe_svg(b'<svg xmlns="http://www.w3.org/2000/svg"><path fill="url(file:///etc/passwd)" d="M0 0L10 10"/></svg>')


if __name__=='__main__':unittest.main()
