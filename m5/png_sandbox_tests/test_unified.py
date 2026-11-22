import copy,json,os,uuid,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from creative_core.document import canonical
from studio_png_sandbox.unified import Unified
from studio_png_sandbox.workflow import Workflow
from studio_png_sandbox.controller import Refused,sha
from png_sandbox_tests.test_workflow import WorkflowTests
class UnifiedTests(unittest.TestCase):
 def setUp(self):
  self.fixture=WorkflowTests();self.fixture.setUp();self.old,self.asset=self.fixture.make();source=self.old.current();self.original=canonical(source)
  self.u=Unified(self.fixture.root/('png-unified-'+uuid.uuid4().hex),self.fixture.library,self.fixture.decoder,base=source['document'],binding=source['binding'],acknowledge=True)
 def tearDown(self):self.u.close();self.fixture.tearDown()
 def edit(self,action,**extra):
  v=self.u.view();return self.u.edit({'project_id':v['project_id'],'expected_revision':v['revision'],'action':action,**extra},self.u.token())
 def place(self):return self.u.place(self.asset['asset_id'],{'x':100,'y':500,'width':120,'height':120},self.u.token())
 def test_old_reader_rejection_and_source_preservation(self):
  self.assertEqual(self.u.current()['version'],3);self.assertEqual(canonical(self.old.current()),self.original)
  with self.assertRaises(Refused):Workflow(self.u.root,self.fixture.library,self.fixture.decoder)
  self.assertEqual(self.u.current()['document']['assets'],[])
 def test_english_telugu_text_and_brand_colors(self):
  identity=self.u.view()['elements'][0]['id'];text='Read / కలిసి చదువుదాం / e\u0301';self.edit('edit_text',element_id=identity,text=text);self.place();self.edit('color',element_id=identity,color='#111111');self.assertEqual(self.u.view()['content'][0]['text'],text);self.assertIn('కలిసి',self.u.scene()['svg']);self.assertIn('<image',self.u.scene()['svg'])
 def test_interleaved_single_timeline(self):
  identity=self.u.view()['elements'][0]['id'];start=self.u.view()['content'][0]['text'];self.edit('edit_text',element_id=identity,text='Hello');png=self.place();self.u.action('geometry',self.u.token(),png,{'x':300,'y':700,'width':180,'height':180});self.edit('undo');self.assertEqual(self.u.current()['placements'][0]['geometry']['x'],100);self.edit('undo');self.assertEqual(self.u.current()['placements'],[]);self.edit('undo');self.assertEqual(self.u.view()['content'][0]['text'],start);self.edit('redo');self.edit('redo');self.edit('redo');self.assertEqual(self.u.current()['placements'][0]['geometry']['x'],300)
 def test_geometry_upgrade_checkpoint_sticky_and_undo(self):
  v=self.u.view();e=v['elements'][0];targets=[{'element_id':e['id'],'x':80,'y':100,'width':800,'height':240}]
  with self.assertRaises(Refused):self.edit('geometry',view_id=v['view']['id'],targets=targets,acknowledge_upgrade=False)
  self.edit('geometry',view_id=v['view']['id'],targets=targets,acknowledge_upgrade=True);self.assertEqual(self.u.view()['history_version'],3);self.edit('undo');self.assertEqual(self.u.view()['history_version'],3);self.assertEqual(self.u.view()['elements'][0]['width'],e['width']);self.edit('redo');self.assertEqual(self.u.view()['elements'][0]['width'],800);self.assertEqual(len(list((self.u.root/'legacy-checkpoints').glob('*.json'))),1)
 def test_new_branch_after_undo_and_no_approvals(self):
  identity=self.u.view()['elements'][0]['id'];self.edit('edit_text',element_id=identity,text='One');self.place();self.edit('undo');self.edit('font_size',element_id=identity,font_size=56)
  with self.assertRaises(Refused):self.edit('redo')
  self.assertEqual(self.u.current()['approvals'],[]);self.assertEqual(self.u.current()['document']['approvals'],[])
 def test_add_geometry_reuses_approved_palette(self):
  v=self.edit('add_shape',shape='rectangle');self.assertEqual(v['elements'][-1]['style']['fill'],'#111111');identity=v['elements'][-1]['id'];self.edit('move',element_id=identity,x=300,y=700);self.edit('remove',element_id=identity);self.edit('undo');self.assertEqual(self.u.view()['elements'][-1]['id'],identity)
 def test_stale_invalid_color_and_overlap_preserve_state(self):
  v=self.u.view();identity=v['elements'][0]['id'];head=self.u.token();self.place()
  with self.assertRaises(Refused):self.u.edit({'project_id':v['project_id'],'expected_revision':v['revision'],'action':'font_size','element_id':identity,'font_size':52},head)
  before=self.u.token()
  with self.assertRaises(ValueError):self.edit('color',element_id=identity,color='#ABCDEF')
  with self.assertRaises(ValueError):self.edit('move',element_id=identity,x=100,y=500)
  self.assertEqual(self.u.token(),before)
 def test_reopen_document_timeline_and_svg_exact(self):
  identity=self.u.view()['elements'][0]['id'];self.edit('edit_text',element_id=identity,text='Telugu / తెలుగు');self.place();state=self.u.current();svg=self.u.scene()['svg'];root=self.u.root;self.u.close();self.u=Unified(root,self.fixture.library,self.fixture.decoder);self.assertEqual(self.u.current(),state);self.assertEqual(self.u.scene()['svg'],svg)
 def test_interrupted_edit_is_atomic(self):
  before=self.u.current();head=self.u.token();identity=self.u.view()['elements'][0]['id']
  def fault(stage):
   if stage=='before-head':raise OSError('Simulated interrupted save')
  self.u.fault=fault
  with self.assertRaises(OSError):self.edit('edit_text',element_id=identity,text='Not partially published')
  self.assertEqual(self.u.token(),head);self.assertEqual(self.u.current(),before)
 def test_revocation_blocks_new_edits_and_exports(self):
  self.place();self.fixture.revoke(self.asset);identity=self.u.view()['elements'][0]['id'];head=self.u.token()
  with self.assertRaises(ValueError):self.edit('edit_text',element_id=identity,text='Blocked')
  with self.assertRaises(ValueError):self.u.scene()
  self.assertEqual(self.u.token(),head)
 def test_recovery_copy_preserves_combined_history_and_checkpoints(self):
  identity=self.u.view()['elements'][0]['id'];self.place();self.edit('edit_text',element_id=identity,text='Recovery / తెలుగు');v=self.u.view();targets=[{'element_id':identity,'x':80,'y':100,'width':800,'height':240}];self.edit('geometry',view_id=v['view']['id'],targets=targets,acknowledge_upgrade=True)
  selected=self.u.current();name=self.u.head()['name'];original=self.u.token();destination=self.fixture.root/('png-unified-'+uuid.uuid4().hex);self.u.recover_copy(name,destination,acknowledge=True);r=Unified(destination,self.fixture.library,self.fixture.decoder)
  try:self.assertEqual(r.current(),selected);self.assertEqual(r.scene()['svg'],self.u.scene()['svg']);self.assertEqual(self.u.token(),original)
  finally:r.close()
 def test_png_delta_cannot_forge_history_upgrade(self):
  self.place();h=self.u.head();p=self.u.root/'generations'/h['name']/'workflow.json';s=self.u.current();s['history_floor']=3;s['document']['history']['version']=3;raw=canonical(s)
  # Controlled corruption of this test's own new record, never existing evidence.
  p.chmod(0o600);p.write_bytes(raw);p.chmod(0o444);h['sha256']=sha(raw);(self.u.root/'HEAD.json').write_bytes(canonical(h))
  with self.assertRaisesRegex(Refused,'history upgrade'):self.u.current()
