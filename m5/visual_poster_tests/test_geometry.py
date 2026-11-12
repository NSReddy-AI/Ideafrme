import copy,hashlib,os,types,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError
from test_reorder import ReorderTests

class GeometryTests(ReorderTests):
    def targets(self):return [dict(element_id=e['id'],x=e['x']+10,y=e['y']+20,width=e['width'],height=e['height']) for e in self.p['elements']]
    def geometry(self,targets=None,ack=True):return self.act('geometry',view_id=self.p['view']['id'],targets=self.targets() if targets is None else targets,acknowledge_upgrade=ack)
    def test_atomic_geometry_history(self):
        before=self.s.manual.document(self.p['project_id']);self.geometry();after=self.s.manual.document(self.p['project_id'])
        self.assertEqual(after['format'],before['format']);self.assertEqual(after['schema_version'],1);self.assertEqual(after['history']['version'],3)
        self.assertEqual(after['revision'],before['revision']+1);self.assertEqual(len(after['history']['transactions']),len(before['history']['transactions'])+1)
        self.act('undo');self.assertEqual(self.p['elements'],before['elements']);self.assertEqual(self.p['history_version'],3);self.act('redo');self.assertEqual(self.p['elements'],after['elements'])
    def test_invalid_targets_atomic(self):
        targets=self.targets();badcases=[[],targets+[targets[0]],[dict(targets[0],element_id='unknown')],[dict(targets[0],width=0)],[dict(targets[0],height=float('nan'))],[dict(targets[0],x=True)],[dict(targets[0],unexpected=1)],targets+[dict(targets[0],element_id=targets[1]['element_id'])]]
        for bad in badcases:
            before=self.s.manual.document(self.p['project_id'])
            with self.assertRaises((UIError,core.CreativeError)):self.geometry(bad)
            self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_noop_ack_and_stale(self):
        before=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(UIError):self.geometry(ack=False)
        targets=[dict(element_id=e['id'],**{k:e[k] for k in ('x','y','width','height')}) for e in self.p['elements']]
        with self.assertRaises(UIError):self.geometry(targets)
        with self.assertRaises(UIError):self.s.action({'project_id':self.p['project_id'],'expected_revision':0,'action':'geometry','view_id':'portrait','targets':self.targets(),'acknowledge_upgrade':True})
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_checkpoint_restore_explicit(self):
        from visual_poster_studio.checkpoint_restore import restore
        before=self.s.manual.document(self.p['project_id']);self.geometry();self.act('save');identity=self.p['project_id'];source=self.root
        checkpoint=next((source/'projects'/identity/'legacy-checkpoints').glob('*.json'));self.assertEqual(checkpoint.read_bytes(),canonical(before)+b'\n');self.assertFalse(checkpoint.stat().st_mode&0o222)
        self.s.close();destination=source.parent/('restored-'+uuid.uuid4().hex)
        with self.assertRaises(UIError):restore(source,identity,checkpoint.stem,destination)
        restore(source,identity,checkpoint.stem,destination,True)
        from visual_poster_studio.service import VisualStudio
        reopened=VisualStudio(destination,resume=True)
        try:self.assertEqual(reopened.manual.document(identity),before)
        finally:reopened.close()
        self.assertEqual(checkpoint.read_bytes(),canonical(before)+b'\n')
    def test_older_reader_v3_refusal(self):
        module=types.ModuleType('creative_core._pre_v3');module.__package__='creative_core'
        path=Path(__file__).resolve().parents[1]/'.runtime/studio-ui/visual-geometry-baseline-01/before/creative_core/validation.py'
        exec(compile(path.read_text(),str(path),'exec'),module.__dict__)
        module.validate(self.s.manual.document(self.p['project_id']),self.root/'projects'/self.p['project_id']);self.geometry()
        for undo in [False,True]:
            if undo:self.act('undo')
            with self.assertRaises(core.CreativeError):module.validate(self.s.manual.document(self.p['project_id']),self.root/'projects'/self.p['project_id'])
    def test_save_reopen_deterministic_scene(self):
        self.geometry();self.act('save');scene=self.s.scene(self.p['project_id'],self.p['revision']);self.p=self.s.reopen(self.p['project_id'],self.p['revision']);self.assertEqual(scene,self.s.scene(self.p['project_id'],self.p['revision']))
    def test_geometry_tamper_rejected(self):
        self.geometry();doc=self.s.manual.document(self.p['project_id'])
        for key,value in [('style',{'fill':'#000000'}),('id','different')]:
            bad=copy.deepcopy(doc);bad['elements'][0][key]=value;bad['history']['transactions'][-1]['after']['elements'][0][key]=value
            with self.assertRaises(core.CreativeError):core.validate(bad,self.root/'projects'/self.p['project_id'])
    def test_v2_upgrade_and_reorder_sticky_v3(self):
        self.reorder();self.geometry();self.reorder(ack=False);self.assertEqual(self.p['history_version'],3);self.act('undo');self.assertEqual(self.p['history_version'],3)
    def test_approval_invalidation(self):
        identity=self.p['project_id'];directory=self.root/'projects'/identity
        doc=core.snapshot(core.approve(self.s.manual.document(identity),'reviewer',directory),'Historical',directory);self.s.manual._working[identity]=doc;self.p=self.s.view(identity);versions=copy.deepcopy(doc['versions'])
        self.geometry();self.act('undo');self.act('redo');current=self.s.manual.document(identity);self.assertEqual(current['approvals'],[]);self.assertEqual(current['versions'],versions)
    def test_foreign_view_refused(self):
        doc=self.s.manual.document(self.p['project_id']);doc['views'].append(dict(doc['views'][0],id='other'));self.s.manual._working[self.p['project_id']]=doc
        with self.assertRaises(UIError):self.act('geometry',view_id='other',targets=self.targets(),acknowledge_upgrade=True)
    def test_checkpoint_required_and_verified(self):
        identity=self.p['project_id'];directory=self.root/'projects'/identity;doc=self.s.manual.document(identity)
        op={'op':'geometry','expected_revision':doc['revision'],'view_id':'portrait','targets':self.targets(),'acknowledge_upgrade':True,'legacy_checkpoint_sha256':'0'*64}
        with self.assertRaises(core.CreativeError):core.apply(doc,op,directory)
        digest=self.s.journal.checkpoint(identity,doc);op['legacy_checkpoint_sha256']=digest;path=directory/'legacy-checkpoints'/(digest+'.json');path.chmod(0o644)
        with self.assertRaises(core.CreativeError):core.apply(doc,op,directory)
        self.assertEqual(doc,self.s.manual.document(identity))
    def test_geometry_not_accepted_under_v2(self):
        self.geometry();doc=self.s.manual.document(self.p['project_id']);doc['history']['version']=2
        with self.assertRaises(core.CreativeError):core.validate(doc,self.root/'projects'/self.p['project_id'])
    def test_session_restart_v3_and_resize(self):
        targets=self.targets();targets[0].update(width=800,height=240);self.geometry(targets);self.act('save');identity=self.p['project_id'];before=self.s.manual.document(identity);scene=self.s.scene(identity,self.p['revision']);self.s.close()
        from visual_poster_studio.service import VisualStudio
        self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close)
        self.assertEqual(before,self.s.manual.document(identity));self.assertEqual(scene,self.s.scene(identity,self.p['revision']))
