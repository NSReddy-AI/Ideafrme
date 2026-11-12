import copy
import os
from pathlib import Path
import types
import unittest
import creative_core as core
from creative_core.document import canonical
from test_reorder import ReorderTests

class CompatibilityTests(ReorderTests):
    def test_legacy_bytes_unchanged(self):
        doc=self.s.manual.document(self.p['project_id']);before=canonical(doc);core.validate(doc,self.root/'projects'/self.p['project_id']);self.assertEqual(before,canonical(doc));self.assertNotIn('version',doc['history'])
    def test_unknown_history_versions(self):
        doc=self.s.manual.document(self.p['project_id'])
        for value in [0,1,4,True,'2',None]:
            bad=copy.deepcopy(doc);bad['history']['version']=value
            with self.assertRaises(core.CreativeError):core.validate(bad,self.root/'projects'/self.p['project_id'])
    def test_real_old_reader_refuses_v2(self):
        module=types.ModuleType('creative_core._old_validation');module.__package__='creative_core'
        source=Path(os.environ['VISUAL_OLD_VALIDATOR']).read_text();exec(compile(source,'retained-pre-extension-validation.py','exec'),module.__dict__)
        old=self.s.manual.document(self.p['project_id']);module.validate(old,self.root/'projects'/self.p['project_id'])
        self.reorder();new=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(core.CreativeError):module.validate(new,self.root/'projects'/self.p['project_id'])
        self.act('undo')
        with self.assertRaises(core.CreativeError):module.validate(self.s.manual.document(self.p['project_id']),self.root/'projects'/self.p['project_id'])
    def test_reorder_not_allowed_in_v1_history(self):
        self.reorder();doc=self.s.manual.document(self.p['project_id']);doc['history'].pop('version')
        with self.assertRaises(core.CreativeError):core.validate(doc,self.root/'projects'/self.p['project_id'])
