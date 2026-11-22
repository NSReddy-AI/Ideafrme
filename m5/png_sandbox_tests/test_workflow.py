import base64,copy,errno,json,os,struct,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from creative_core.document import canonical
from studio_manual_ui.service import Studio,UIError
from studio_media_workflow import Store as OldMedia
from visual_poster_studio.brands import Store as Library
from visual_poster_studio.binding_workflow import pin
from studio_png_sandbox.controller import Decoder,Refused,sha
from studio_png_sandbox.workflow import Workflow,normalized_png
from png_sandbox_tests.test_security import png
RIGHTS={'status':'granted','authority':'Synthetic fixture owner','evidence':'First-party generated red pixels','scopes':['internal_preview','commercial_design','redistribute'],'destinations':['library_metadata','poster'],'expires':'2099-01-01T00:00:00Z'}
class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['PNG_TEST_ROOT']);self.decoder=Decoder(Path(os.environ['PNG_BUILD']));self.library=Library(self.root/('library-'+uuid.uuid4().hex));self.stores=[]
 def tearDown(self):
  for s in self.stores:s.close()
 def make(self,text='Read together / కలిసి చదువుదాం',kind='logo',rules=None):
  raw=png();a=self.library.command({'action':'register_asset','name':'first-party.png','kind':kind,'provenance':{'owner':'Fixture','source':'Generated test bytes','license':'First-party test grant'},'data_base64':base64.b64encode(raw).decode(),'rights':copy.deepcopy(RIGHTS)})
  payload={'name':'PNG fixture brand','colors':['#111111','#FFFFFF','#FF0000'],'typography':{'english':'Inter Bold','telugu':'Noto Sans Telugu Black'},'mandatory_rules':rules or [],'preferences':[],'inspiration':[],'notes':'Synthetic pixels only','asset_ids':[a['asset_id']]}
  b=self.library.command({'action':'save','brand_id':None,'expected_head':None,'payload':payload});b=self.library.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'reviewer':'Fixture owner','acknowledge':True})
  manual=Studio(self.root/('manual-'+uuid.uuid4().hex));v=manual.create({'name':'PNG fixture','text':text,'language':'te'});doc=manual.document(v['project_id']);manual.close()
  binding={'format':'studio-project-binding@1','version':1,'binding_id':str(uuid.uuid4()),'session_id':str(uuid.uuid4()),'project_id':doc['id'],'revision':1,'parent':None,'brand':pin(SimpleNamespace(brand_library=self.library),b['hash']),'brief':{'purpose':'Read together','topic':text,'audience':'Families','format':'poster','instructions':'First-party PNG only'},'origin':None}
  s=Workflow(self.root/('png-workflow-'+uuid.uuid4().hex),self.library,self.decoder,base=doc,binding=binding,acknowledge=True);self.stores.append(s);return s,a
 def add(self,s,a):return s.place(a['asset_id'],{'x':100,'y':500,'width':120,'height':120},s.token())
 def revoke(self,a):self.library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':{'status':'denied','authority':'Fixture owner','evidence':'Withdrawn','scopes':[],'destinations':[],'expires':None}})
 def test_explicit_version_and_old_readers_refuse(self):
  s,a=self.make();self.assertEqual(s.current()['format'],'studio-media-workflow@2')
  with self.assertRaises((ValueError,OSError)):OldMedia(s.root,library=self.library)
  with self.assertRaises((ValueError,OSError)):Studio(s.root,resume=True)
 def test_png_placement_preserves_document_and_binding(self):
  s,a=self.make();before=s.current();self.add(s,a);after=s.current();self.assertEqual(before['document'],after['document']);self.assertEqual(before['binding'],after['binding']);self.assertEqual(after['document']['assets'],[]);self.assertEqual(after['placements'][0]['kind'],'logo')
 def test_geometry_single_step_undo_redo(self):
  s,a=self.make();identity=self.add(s,a);old=s.current()['placements'];s.action('geometry',s.token(),identity,{'x':300,'y':600,'width':180,'height':180});changed=s.current()['placements'];s.action('undo',s.token());self.assertEqual(s.current()['placements'],old);s.action('redo',s.token());self.assertEqual(s.current()['placements'],changed);self.assertEqual(s.current()['approvals'],[])
 def test_no_approval_resurrection_and_redo_branch(self):
  s,a=self.make();identity=self.add(s,a);s.action('geometry',s.token(),identity,{'x':300,'y':600,'width':180,'height':180});s.action('undo',s.token());s.action('remove',s.token(),identity)
  with self.assertRaises(Refused):s.action('redo',s.token())
  self.assertEqual(s.current()['approvals'],[]);self.assertEqual(s.current()['document']['approvals'],[])
 def test_save_close_reopen_exact_scene_and_history(self):
  s,a=self.make();self.add(s,a);before=s.current();scene=s.scene();path=s.root;s.close();restored=Workflow(path,self.library,self.decoder);self.stores.append(restored);self.assertEqual(restored.current(),before);self.assertEqual(restored.scene(),scene)
 def test_english_telugu_and_combining_text_preserved(self):
  text='Together / కలిసి చదువుదాం / e\u0301';s,a=self.make(text);self.add(s,a);self.assertEqual(s.current()['document']['content'][0]['text'],text);self.assertIn('కలిసి',s.scene()['svg']);self.assertIn('e\u0301',s.scene()['svg'])
 def test_stale_and_aspect_invalid_transactions_preserve_head(self):
  s,a=self.make();old=s.token();identity=self.add(s,a)
  with self.assertRaises(Refused):s.action('remove',old,identity)
  head=s.token()
  with self.assertRaises(Refused):s.action('geometry',head,identity,{'x':10,'y':10,'width':100,'height':90})
  self.assertEqual(s.token(),head)
 def test_palette_hard_rule_and_logo_text_protection(self):
  s,a=self.make(rules=['Only approved palette and supported fonts.']);self.add(s,a)
  with self.assertRaises(Refused):s.place(a['asset_id'],{'x':80,'y':100,'width':100,'height':100},s.token())
 def test_no_assets_rule_refuses(self):
  s,a=self.make(rules=['No external assets.']);head=s.token()
  with self.assertRaises(Refused):self.add(s,a)
  self.assertEqual(s.token(),head)
 def test_revoked_rights_before_decode_no_worker(self):
  s,a=self.make();self.revoke(a)
  with patch.object(self.decoder,'decode',side_effect=AssertionError('No worker')):
   with self.assertRaises((ValueError,OSError)):self.add(s,a)
 def test_revocation_during_decode_refuses_publication(self):
  s,a=self.make();original=self.decoder.decode
  def withdrawn(*args,**kwargs):
   result=original(*args,**kwargs);self.revoke(a);return result
  old=s.token()
  with patch.object(self.decoder,'decode',side_effect=withdrawn):
   with self.assertRaises((ValueError,OSError)):self.add(s,a)
  self.assertEqual(s.token(),old)
 def test_revocation_blocks_render_but_allows_removal(self):
  s,a=self.make();identity=self.add(s,a);self.revoke(a)
  with self.assertRaises((ValueError,OSError)):s.scene()
  s.action('remove',s.token(),identity);self.assertEqual(s.current()['placements'],[])
 def test_failed_publication_preserves_previous_and_recovery_copy(self):
  s,a=self.make();before=s.current();head=s.token()
  def fault(stage):
   if stage=='before-head':raise OSError(errno.ENOSPC,'Injected only')
  s.fault=fault
  with self.assertRaises(OSError):self.add(s,a)
  self.assertEqual(s.token(),head);self.assertEqual(s.current(),before);candidate=max(s.candidates(),key=lambda x:x.get('generation',0));destination=self.root/('png-workflow-'+uuid.uuid4().hex);s.recover_copy(candidate['name'],destination,acknowledge=True);r=Workflow(destination,self.library,self.decoder);self.stores.append(r);self.assertEqual(len(r.current()['placements']),1);self.assertEqual(s.token(),head)
 def test_post_head_interruption_reopens_whole_state(self):
  s,a=self.make()
  def fault(stage):
   if stage=='after-head':raise OSError('Interrupted response')
  s.fault=fault
  with self.assertRaises(OSError):self.add(s,a)
  path=s.root;s.close();r=Workflow(path,self.library,self.decoder);self.stores.append(r);self.assertEqual(len(r.current()['placements']),1)
 def test_budget_refusal_and_duplicate_writer(self):
  s,a=self.make()
  with self.assertRaises(Refused):Workflow(s.root,self.library,self.decoder)
  head=s.token()
  with patch('studio_png_sandbox.workflow.BUDGET',1):
   with self.assertRaises(Refused):self.add(s,a)
  self.assertEqual(s.token(),head)
 def test_tampered_derived_bytes_rejected(self):
  s,a=self.make();self.add(s,a);rid=s.current()['placements'][0]['receipt'];p=s.root/'pixels'/rid/'normalized.png';p.chmod(0o600);p.write_bytes(b'not PNG')
  with self.assertRaises(Refused):s.scene()
 def test_normalized_png_roundtrip_pixels(self):
  raw=png(pixel=b'\x12\x23\x34\x80');pixels=self.decoder.decode(raw,expected_sha256=sha(raw));normalized=normalized_png(pixels);again=self.decoder.decode(normalized,expected_sha256=sha(normalized));self.assertEqual(pixels.rgba,again.rgba)
 def test_export_stale_and_receipt_preservation(self):
  s,a=self.make();identity=self.add(s,a);scene=s.scene();head=s.token();raster=png(1080,1350);name=s.export(head,raster,scene['sha256']);before={p.name:sha(p.read_bytes()) for p in (s.root/'exports'/name).iterdir()};s.action('remove',s.token(),identity)
  with self.assertRaises(Refused):s.export(head,raster,scene['sha256'])
  self.assertEqual(before,{p.name:sha(p.read_bytes()) for p in (s.root/'exports'/name).iterdir()})
