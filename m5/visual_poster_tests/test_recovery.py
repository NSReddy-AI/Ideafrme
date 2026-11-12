import errno
import os
from pathlib import Path
from unittest.mock import patch
from test_resume import ResumeTests
from studio_manual_ui.service import UIError
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.recovery import sha

class RecoveryTests(ResumeTests):
    def test_budget_refusal_preserves_primary(self):
        self.act('save');primary=self.root/'projects'/self.p['project_id']/'creative.json';before=primary.read_bytes();self.act('move',element_id=self.p['elements'][0]['id'],x=99,y=100)
        with patch('visual_poster_studio.recovery.BUDGET',1):
            with self.assertRaises(UIError):self.act('save')
        self.assertEqual(primary.read_bytes(),before)
    def test_enospc_before_primary(self):
        self.act('save');primary=self.root/'projects'/self.p['project_id']/'creative.json';before=primary.read_bytes();self.act('move',element_id=self.p['elements'][0]['id'],x=99,y=100)
        with patch('creative_core.persistence._atomic',side_effect=OSError(errno.ENOSPC,'injected ENOSPC')):
            with self.assertRaises(UIError):self.act('save')
        self.assertEqual(primary.read_bytes(),before);self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close)
        self.assertEqual(self.s.project_errors[self.p['project_id']]['state'],'interrupted-save')
        with self.assertRaises(UIError):self.s.view(self.p['project_id'])
    def test_sync_failure_after_primary(self):
        self.act('save');identity=self.p['project_id'];self.act('move',element_id=self.p['elements'][0]['id'],x=144,y=100)
        from visual_poster_studio.recovery import sync_directory
        def fail(path):
            if Path(path)==self.root/'projects'/identity:raise UIError('durability-blocked','injected synchronization failure')
            return sync_directory(path)
        with patch('visual_poster_studio.recovery.sync_directory',side_effect=fail):
            with self.assertRaises(UIError):self.act('save')
        state=self.s.journal.inspect(identity);self.assertEqual(state['state'],'interrupted-save');self.assertEqual(state['primary'],'candidate')
        self.assertEqual(sha(self.s.journal.candidate(identity,'after')),sha((self.root/'projects'/identity/'creative.json').read_bytes()))
    def test_startup_sync_failure_is_blocked(self):
        import uuid
        root=self.root.parent/('sync-'+uuid.uuid4().hex)
        with patch('visual_poster_studio.session.os.fsync',side_effect=OSError(errno.ENOTSUP,'injected unsupported sync')):
            with self.assertRaises((UIError,OSError)):VisualStudio(root)
    def test_primary_tamper_is_not_repaired(self):
        self.act('save');primary=self.root/'projects'/self.p['project_id']/'creative.json';primary.write_bytes(b'{broken');self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close)
        self.assertIn(self.p['project_id'],self.s.project_errors);self.assertEqual(primary.read_bytes(),b'{broken')

    def test_resume_unsupported_sync_refused(self):
        self.act('save');self.s.close()
        with patch('visual_poster_studio.service.sync_directory',side_effect=UIError('durability-blocked','injected unsupported directory sync')):
            with self.assertRaises(UIError):VisualStudio(self.root,resume=True)
    def test_completion_sync_failure_live_block(self):
        self.act('save');identity=self.p['project_id'];self.act('move',element_id=self.p['elements'][0]['id'],x=144,y=100)
        from visual_poster_studio.session import sync_directory
        def fail(path):
            if (Path(path)/'complete.json').exists():raise UIError('durability-blocked','injected completion sync failure')
            return sync_directory(path)
        with patch('visual_poster_studio.session.sync_directory',side_effect=fail):
            with self.assertRaises(UIError):self.act('save')
        self.assertIn(identity,self.s.project_errors)
        with self.assertRaises(UIError):self.s.view(identity)
