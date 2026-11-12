import copy
from test_reorder import ReorderTests
from studio_manual_ui.service import UIError
import creative_core as core

class WorkflowTests(ReorderTests):
    def test_remove_one_transaction(self):
        before=self.s.manual.document(self.p['project_id']);identity=self.p['elements'][1]['id'];self.act('remove',element_id=identity);after=self.s.manual.document(self.p['project_id'])
        self.assertEqual(after['revision'],before['revision']+1);self.assertEqual(after['history']['transactions'][-1]['operation'],'remove');self.assertEqual(len(after['elements']),len(before['elements'])-1);self.assertEqual(after['content'],before['content'])
    def test_remove_undo_redo_exact(self):
        before=copy.deepcopy(self.p['elements']);self.act('remove',element_id=before[0]['id']);self.act('undo');self.assertEqual(self.p['elements'],before);self.act('redo');self.assertEqual(len(self.p['elements']),len(before)-1)
    def test_remove_stale_rejected(self):
        before=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(UIError):self.s.action({'project_id':self.p['project_id'],'expected_revision':0,'action':'remove','element_id':self.p['elements'][0]['id']})
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_remove_unknown_rejected(self):
        before=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(UIError):self.act('remove',element_id='unknown')
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_remove_does_not_overwrite_saved(self):
        self.act('save');path=self.root/'projects'/self.p['project_id']/'creative.json';raw=path.read_bytes();self.act('remove',element_id=self.p['elements'][0]['id']);self.assertEqual(path.read_bytes(),raw)
    def test_remove_approval_invalidation(self):
        identity=self.p['project_id'];self.s.manual._working[identity]=core.approve(self.s.manual.document(identity),'Synthetic reviewer',self.root/'projects'/identity);self.p=self.s.view(identity)
        self.act('remove',element_id=self.p['elements'][0]['id']);self.act('undo');self.assertEqual(self.p['approval_count'],0)
    def test_remove_last_layer_and_restore(self):
        before=copy.deepcopy(self.p['elements'])
        for identity in [e['id'] for e in before]:self.act('remove',element_id=identity)
        self.assertEqual(self.p['elements'],[]);scene=self.s.scene(self.p['project_id'],self.p['revision']);self.assertEqual(scene['boxes'],[])
        for i in before:self.act('undo')
        self.assertEqual(self.p['elements'],before)
    def test_remove_v2_preserves_history_version(self):
        self.reorder();self.act('remove',element_id=self.p['elements'][0]['id']);self.act('undo');self.assertEqual(self.p['history_version'],2)
