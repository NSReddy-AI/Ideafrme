import copy
import os
from pathlib import Path
import unittest
import uuid
import creative_core as core
from creative_core.document import canonical
from visual_poster_studio.service import VisualStudio
from studio_manual_ui.service import UIError

class ReorderTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['VISUAL_TEST_ROOT'])/('reorder-'+uuid.uuid4().hex);self.s=VisualStudio(self.root);self.addCleanup(self.s.close)
        self.p=self.s.create({'name':'Reorder','text':'తెలుగు é','language':'te'})
        self.act('add_shape',shape='rectangle');self.act('add_shape',shape='ellipse')
    def act(self,kind,**extra):
        self.p=self.s.action({'project_id':self.p['project_id'],'expected_revision':self.p['revision'],'action':kind,**extra});return self.p
    def reorder(self,ids=None,ack=True):return self.act('reorder',view_id=self.p['view']['id'],ordered_element_ids=ids if ids is not None else [e['id'] for e in self.p['elements']][::-1],acknowledge_upgrade=ack)
    def test_one_atomic_transaction(self):
        before=self.s.manual.document(self.p['project_id']);self.reorder();after=self.s.manual.document(self.p['project_id'])
        self.assertEqual(after['revision'],before['revision']+1);self.assertEqual(len(after['history']['transactions']),len(before['history']['transactions'])+1)
        self.assertEqual(after['history']['version'],2);self.assertEqual(after['content'],before['content'])
        self.assertEqual({e['id']:e for e in after['elements']},{e['id']:e for e in before['elements']})
    def test_checkpoint_exact_immutable(self):
        before=self.s.manual.document(self.p['project_id']);self.reorder();paths=list((self.root/'projects'/self.p['project_id']/'legacy-checkpoints').glob('*.json'))
        self.assertEqual(len(paths),1);self.assertEqual(paths[0].read_bytes(),canonical(before)+b'\n');self.assertEqual(paths[0].stat().st_mode&0o222,0)
    def test_ack_required_atomic(self):
        before=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(UIError):self.reorder(ack=False)
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_invalid_permutations(self):
        ids=[e['id'] for e in self.p['elements']]
        for bad in [ids,ids[:-1],ids+[ids[0]],['unknown']+ids[1:],None,True,[True]+ids[1:]]:
            before=self.s.manual.document(self.p['project_id'])
            with self.assertRaises((UIError,core.CreativeError)):
                self.act('reorder',view_id=self.p['view']['id'],ordered_element_ids=bad,acknowledge_upgrade=True)
            self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_stale_revision(self):
        with self.assertRaises(UIError):self.s.action({'project_id':self.p['project_id'],'expected_revision':0,'action':'reorder','view_id':'portrait','ordered_element_ids':[e['id'] for e in self.p['elements']][::-1],'acknowledge_upgrade':True})
    def test_sticky_undo_redo_and_branch(self):
        ids=[e['id'] for e in self.p['elements']];self.reorder();self.act('undo');self.assertEqual([e['id'] for e in self.p['elements']],ids)
        self.assertEqual(self.p['history_version'],2);self.act('redo');self.assertEqual([e['id'] for e in self.p['elements']],ids[::-1])
        self.act('undo');self.act('move',element_id=ids[0],x=120,y=100);self.assertFalse(self.p['can_redo']);self.assertEqual(self.p['history_version'],2)
    def test_approvals_and_snapshots(self):
        identity=self.p['project_id'];directory=self.root/'projects'/identity
        doc=core.snapshot(core.approve(self.s.manual.document(identity),'Synthetic reviewer',directory),'Historical',directory)
        self.s.manual._working[identity]=doc;self.p=self.s.view(identity);saved=copy.deepcopy(doc['versions'])
        self.reorder();self.assertEqual(self.p['approval_count'],0);self.act('undo');self.assertEqual(self.p['approval_count'],0);self.act('redo')
        self.assertEqual(self.s.manual.document(identity)['versions'],saved)
    def test_persisted_nonorder_tampering(self):
        self.reorder();doc=self.s.manual.document(self.p['project_id'])
        for key,value in [('x',123),('width',456)]:
            bad=copy.deepcopy(doc);bad['history']['transactions'][-1]['after']['elements'][0][key]=value;bad['elements'][0][key]=value
            with self.assertRaises(core.CreativeError):core.validate(bad,self.root/'projects'/self.p['project_id'])
    def test_public_api_requires_checkpoint(self):
        doc=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(core.CreativeError):core.apply(doc,{'op':'reorder','view_id':'portrait','ordered_element_ids':[e['id'] for e in doc['elements']][::-1],'expected_revision':doc['revision'],'acknowledge_upgrade':True,'legacy_checkpoint_sha256':'0'*64},self.root/'projects'/self.p['project_id'])
    def test_multiview_and_foreign_ids(self):
        identity=self.p['project_id'];directory=self.root/'projects'/identity;doc=self.s.manual.document(identity)
        # Synthetic core fixture with no inherited history; preserve interleaved view slots.
        doc['history']={'cursor':0,'transactions':[]};doc['views'].append({'id':'other','width':1080,'height':1350,'language':'en'})
        foreign=copy.deepcopy(doc['elements'][1]);foreign.update(id='foreign',view_id='other');doc['elements'].insert(1,foreign)
        self.s.manual._working[identity]=doc;digest=self.s.journal.checkpoint(identity,doc)
        op={'op':'reorder','view_id':'portrait','ordered_element_ids':[e['id'] for e in doc['elements'] if e['view_id']=='portrait'][::-1],'expected_revision':doc['revision'],'acknowledge_upgrade':True,'legacy_checkpoint_sha256':digest}
        result=core.apply(doc,op,directory);self.assertEqual(result['elements'][1],foreign)
        op['ordered_element_ids'][0]='foreign'
        with self.assertRaises(core.CreativeError):core.apply(doc,op,directory)
    def test_export_source_order(self):
        before=self.s.scene(self.p['project_id'],self.p['revision']);self.reorder();after=self.s.scene(self.p['project_id'],self.p['revision'])
        self.assertEqual([x['element_id'] for x in after['boxes']],[x['element_id'] for x in before['boxes']][::-1]);self.assertNotEqual(before['svg_sha256'],after['svg_sha256'])

    def test_history_limit_preserves_state(self):
        from unittest.mock import patch
        before=self.s.manual.document(self.p['project_id'])
        with patch('creative_core.operations.MAX_HISTORY',len(before['history']['transactions'])):
            with self.assertRaises(UIError):self.reorder()
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_wrong_checkpoint_bytes(self):
        doc=self.s.manual.document(self.p['project_id']);identity=self.p['project_id'];digest=self.s.journal.checkpoint(identity,doc)
        path=self.root/'projects'/identity/'legacy-checkpoints'/(digest+'.json');path.chmod(0o600);path.write_bytes(b'changed');path.chmod(0o444)
        with self.assertRaises(core.CreativeError):core.apply(doc,{'op':'reorder','view_id':'portrait','ordered_element_ids':[e['id'] for e in doc['elements']][::-1],'expected_revision':doc['revision'],'acknowledge_upgrade':True,'legacy_checkpoint_sha256':digest},self.root/'projects'/identity)
