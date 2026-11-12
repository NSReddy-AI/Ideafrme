import copy
from test_service import ServiceCase
from studio_manual_ui.service import UIError

class CanvasTransactionTests(ServiceCase):
    def test_drag_target_one_move_one_undo(self):
        old=copy.deepcopy(self.p['elements']);revision=self.p['revision'];self.action('move',element_id=old[0]['id'],x=120,y=140)
        doc=self.s.manual.document(self.p['project_id']);self.assertEqual(doc['revision'],revision+1);self.assertEqual(len(doc['history']['transactions']),1);self.assertEqual(doc['history']['transactions'][0]['operation'],'move')
        self.action('undo');self.assertEqual(self.p['elements'],old);self.action('redo');self.assertEqual(self.p['elements'][0]['x'],120)
    def test_stale_drag_no_partial_write(self):
        self.action('move',element_id=self.p['elements'][0]['id'],x=120,y=140);before=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(UIError):self.s.action({'project_id':self.p['project_id'],'expected_revision':0,'action':'move','element_id':self.p['elements'][0]['id'],'x':150,'y':160})
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_save_reopen_svg_identity(self):
        self.action('move',element_id=self.p['elements'][0]['id'],x=32,y=100);self.action('save');scene=self.s.scene(self.p['project_id'],self.p['revision']);self.p=self.s.reopen(self.p['project_id'],self.p['revision']);self.assertEqual(scene,self.s.scene(self.p['project_id'],self.p['revision']))
    def test_unsupported_resize_and_batch_refused(self):
        before=self.s.manual.document(self.p['project_id'])
        for kind in ['resize','transform','move_many']:
            with self.assertRaises(UIError):self.s.action({'project_id':self.p['project_id'],'expected_revision':self.p['revision'],'action':kind})
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
