import copy
from pathlib import Path
from test_service import ServiceCase
import creative_core as core

class TextCompletionTests(ServiceCase):
    def test_explicit_wrap_round_trip(self):
        text='తెలుగు శ్రీ క్ష\nEnglish é  text';identity=self.p['elements'][0]['id'];self.action('edit_text',element_id=identity,text=text);self.action('save');scene=self.s.scene(self.p['project_id'],self.p['revision']);self.p=self.s.reopen(self.p['project_id'],self.p['revision']);self.assertEqual(scene,self.s.scene(self.p['project_id'],self.p['revision']));self.assertEqual(next(c['text'] for c in self.p['content'] if c['id']==self.p['elements'][0]['content_id']),text)
    def test_text_undo_redo_exact(self):
        identity=self.p['elements'][0]['id'];old=copy.deepcopy(self.p['content']);self.action('edit_text',element_id=identity,text='శ్రీ\né');new=copy.deepcopy(self.p['content']);self.action('undo');self.assertEqual(self.p['content'],old);self.action('redo');self.assertEqual(self.p['content'],new)
    def test_layout_does_not_change_contract(self):
        doc=self.s.manual.document(self.p['project_id']);self.assertNotIn('version',doc['history']);bad=copy.deepcopy(doc);bad['elements'][0]['style']['line_height']=2
        with self.assertRaises(core.CreativeError):core.validate(bad,self.s.manual.projects/self.p['project_id'])
    def test_fixed_renderer_profile_preserved(self):
        scene=self.s.scene(self.p['project_id'],self.p['revision']);self.assertEqual(scene['profile']['line_height'],1.65);self.assertEqual(scene['profile']['id'],'visual-poster-draft@1')
    def test_accessible_text_controls(self):
        html=(Path(__file__).resolve().parents[1]/'visual_poster_studio/index.html').read_text()
        for name in ['text-layout-title','wrap-text','cancel-text-draft','fit-text','text-layout-help']:self.assertIn('id="'+name+'"',html)
        self.assertIn('aria-describedby="composition-status text-status text-layout-help"',html)
