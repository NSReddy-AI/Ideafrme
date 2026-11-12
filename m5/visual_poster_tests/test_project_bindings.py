import copy,errno,json,os,unittest,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import Studio,UIError
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.brands import Store
from visual_poster_studio import binding_workflow as flow
from visual_poster_studio.project_bindings import sha
from test_brands import P,GRANT,UNKNOWN
BRIEF={'purpose':'Inform','topic':'తెలుగు é topic','audience':'Local audience','format':'poster','instructions':'No invented claims.'}
QA={'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':True}
class BindingTests(unittest.TestCase):
 def setUp(self):
  parent=Path(os.environ['VISUAL_TEST_ROOT']);self.root=parent/('session-'+uuid.uuid4().hex);self.s=VisualStudio(self.root);self.addCleanup(self.s.close);self.s.brand_library=Store(parent/('brand-'+uuid.uuid4().hex));self.legacy=self.s.create({'name':'Legacy','text':'తెలుగు','language':'te'});self.s.action({'project_id':self.legacy['project_id'],'expected_revision':0,'action':'save'})
 def brand(self,p=None):
  store=self.s.brand_library;b=store.command({'action':'save','brand_id':None,'expected_head':None,'payload':copy.deepcopy(P if p is None else p)});return store.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'reviewer':'Fixture owner','acknowledge':True})
 def create(self,h=None):return flow.create(self.s,{'name':'Bound project','text':'తెలుగు / Brief','language':'te','brief':copy.deepcopy(BRIEF),'brand_hash':h,'acknowledge':True})
 def proposal(self,p,h=None,fields=None):return {'project_id':p['project_id'],'expected_revision':p['revision'],'expected_binding':p['binding']['hash'],'expected_head':p['binding']['published_head'],'brand_hash':h,'brief':copy.deepcopy(fields or dict(BRIEF,topic='Changed topic'))}
 def change(self,p,h=None,fields=None):
  proposal=self.proposal(p,h,fields);impact,digest,_,_=flow.proposal(self.s,proposal);return flow.change(self.s,{'proposal':proposal,'impact_hash':digest,'acknowledge':True})
 def test_bound_create_atomic_saved_and_legacy_unchanged(self):
  path=self.root/'projects'/self.legacy['project_id']/'creative.json';before=path.read_bytes();p=self.create();self.assertTrue(p['saved']);self.assertFalse(p['dirty']);self.assertEqual(p['binding']['record']['brief'],BRIEF);self.assertFalse((self.root/'projects'/p['project_id']/'creative.json').exists());self.assertEqual(path.read_bytes(),before)
 def test_brand_pin_and_snapshot(self):
  b=self.brand();p=self.create(b['hash']);self.assertEqual(p['binding']['record']['brand']['record'],b['record']);self.assertEqual(p['binding']['record']['brand']['hash'],b['hash'])
 def test_older_manual_reader_cannot_open_bound_project(self):
  p=self.create();self.s.close();older=Studio(self.root,resume=True)
  try:
   self.assertNotIn(p['project_id'],[x['project_id'] for x in older.list_projects()])
   with self.assertRaises((UIError,OSError)):older.view(p['project_id'])
  finally:older.close()
 def test_save_stop_resume_exact_pair(self):
  p=self.create();self.s.action({'project_id':p['project_id'],'expected_revision':p['revision'],'action':'move','element_id':p['elements'][0]['id'],'x':100,'y':120});p=self.s.view(p['project_id']);self.s.action({'project_id':p['project_id'],'expected_revision':p['revision'],'action':'save'});doc=self.s.manual.document(p['project_id']);binding=copy.deepcopy(self.s.pairs.bindings[p['project_id']]);self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close);self.assertEqual(self.s.manual.document(p['project_id']),doc);self.assertEqual(self.s.pairs.bindings[p['project_id']],binding)
 def test_binding_revision_confirmation_and_stale_cas(self):
  p=self.create();proposal=self.proposal(p);_,h,_,_=flow.proposal(self.s,proposal)
  with self.assertRaises(UIError):flow.change(self.s,{'proposal':proposal,'impact_hash':h,'acknowledge':False})
  changed=flow.change(self.s,{'proposal':proposal,'impact_hash':h,'acknowledge':True});self.assertEqual(changed['revision'],1);self.assertEqual(changed['binding']['record']['revision'],2)
  with self.assertRaises(UIError):flow.change(self.s,{'proposal':proposal,'impact_hash':h,'acknowledge':True})
 def test_current_approval_invalidated_historical_preserved(self):
  p=self.create();identity=p['project_id'];directory=self.root/'projects'/identity;doc=core.snapshot(core.approve(self.s.manual.document(identity),'Fixture reviewer',directory),'Historical approval',directory);self.s.manual._working[identity]=doc;p=self.s.view(identity);versions=copy.deepcopy(doc['versions']);changed=self.change(p);self.assertEqual(self.s.manual.document(identity)['approvals'],[]);self.assertEqual(self.s.manual.document(identity)['versions'],versions)
 def test_interruption_before_publication_preserves_old_pair(self):
  p=self.create();before=self.s.pairs.head(p['project_id']);before_doc=self.s.manual.document(p['project_id'])
  def fault(phase):
   if phase=='before-publication':raise OSError(errno.ENOSPC,'Synthetic full')
  self.s.pairs.fault=fault
  with self.assertRaises(UIError):self.change(p)
  self.assertEqual(self.s.pairs.head(p['project_id']),before);self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close);self.assertEqual(self.s.manual.document(p['project_id']),before_doc)
 def test_after_publication_restart_reads_whole_new_pair(self):
  p=self.create()
  def fault(phase):
   if phase=='after-publication':raise OSError('Synthetic termination point')
  self.s.pairs.fault=fault
  with self.assertRaises(UIError):self.change(p)
  self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close);value=self.s.view(p['project_id']);self.assertEqual(value['revision'],1);self.assertEqual(value['binding']['record']['revision'],2);self.assertEqual(value['binding']['record']['brief']['topic'],'Changed topic')
 def test_export_identity_tracks_brief_without_changing_core(self):
  p=self.create();scene=self.s.scene(p['project_id'],0);p=self.change(p);second=self.s.scene(p['project_id'],p['revision']);self.assertEqual(scene['source_fingerprint'],second['source_fingerprint']);self.assertNotEqual(scene['workflow_fingerprint'],second['workflow_fingerprint']);self.assertNotEqual(scene['svg_sha256'],second['svg_sha256']);self.assertIn('studio-binding-identity',second['svg'])
 def test_bound_manifest_identity_and_stale_export(self):
  p=self.create();identity=p['project_id'];started=self.s.begin({'project_id':identity,'expected_revision':0});result=self.s.finish({'token':started['token'],'revision':0,'png':None,'qa':QA});self.assertIn('binding_identity',result['manifest']);self.assertFalse(self.s.exports.audit()['blocked']);started=self.s.begin({'project_id':identity,'expected_revision':0});self.change(p)
  with self.assertRaises(UIError):self.s.finish({'token':started['token'],'revision':0,'png':None,'qa':QA})
 def test_legacy_export_identity_unchanged(self):
  p=self.legacy;scene=self.s.scene(p['project_id'],0);self.assertNotIn('binding_identity',scene);start=self.s.begin({'project_id':p['project_id'],'expected_revision':0});result=self.s.finish({'token':start['token'],'revision':0,'png':None,'qa':QA});self.assertNotIn('binding_identity',result['manifest'])
 def test_raw_checkpoint_recovery_refused_bound(self):
  from visual_poster_studio.checkpoint_restore import restore
  p=self.create()
  with self.assertRaises(UIError):restore(self.root,p['project_id'],'0'*64,self.root.parent/('bad-'+uuid.uuid4().hex),True)
 def test_explicit_paired_recovery_copy(self):
  from visual_poster_studio.binding_recover import recover
  p=self.create();head=self.s.pairs.head(p['project_id']);old=self.s.manual.document(p['project_id']);binding=copy.deepcopy(p['binding']['record']);self.s.close();destination=self.root.parent/('recovered-'+uuid.uuid4().hex);recover(self.root,p['project_id'],head['commit'],destination,True);restored=VisualStudio(destination,resume=True)
  try:
   value=restored.view(p['project_id']);self.assertEqual(value['binding']['record']['brief'],binding['brief']);self.assertEqual(value['binding']['record']['origin']['binding_hash'],sha(canonical(binding)));self.assertEqual(restored.manual.document(p['project_id'])['history'],old['history'])
  finally:restored.close()
 def test_corrupted_binding_blocks_project_only(self):
  p=self.create();head=self.s.pairs.head(p['project_id']);path=self.s.pairs.directory(p['project_id'])/'commits'/head['commit']/'binding.json';path.chmod(0o600);path.write_text('{}');self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close)
  with self.assertRaises(UIError):self.s.view(p['project_id'])
  self.assertEqual(self.s.view(self.legacy['project_id'])['name'],'Legacy')
 def test_legacy_cannot_be_silently_bound(self):
  p=self.legacy;request={'project_id':p['project_id'],'expected_revision':0,'expected_binding':None,'expected_head':None,'brand_hash':None,'brief':BRIEF}
  with self.assertRaises(UIError):flow.proposal(self.s,request)
 def asset_brand(self,poster=True):
  import base64
  grant=dict(GRANT,scopes=['internal_preview','commercial_design'] if poster else ['internal_preview'],destinations=['library_metadata','poster'] if poster else ['library_metadata'])
  asset=self.s.brand_library.command({'action':'register_asset','name':'Opaque test.bin','kind':'logo','provenance':{'owner':'Fixture','source':'Test bytes','license':'Fixture only'},'data_base64':base64.b64encode(b'OPAQUE BINDING FIXTURE').decode(),'rights':grant});return asset,self.brand(dict(P,asset_ids=[asset['asset_id']]))
 def test_poster_rights_scope_required(self):
  a,b=self.asset_brand(False)
  with self.assertRaises(UIError):self.create(b['hash'])
 def test_revocation_blocks_scene_and_finish_but_work_can_save(self):
  a,b=self.asset_brand();p=self.create(b['hash']);start=self.s.begin({'project_id':p['project_id'],'expected_revision':0});self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn')})
  with self.assertRaises(UIError):self.s.scene(p['project_id'],0)
  with self.assertRaises(UIError):self.s.finish({'token':start['token'],'revision':0,'png':None,'qa':QA})
  self.s.action({'project_id':p['project_id'],'expected_revision':0,'action':'save'});self.assertFalse(self.s.view(p['project_id'])['binding']['eligible'])
  changed=self.change(self.s.view(p['project_id']),None);self.assertIsNone(changed['binding']['record']['brand']);self.s.scene(p['project_id'],changed['revision'])
 def test_later_hard_rule_change_blocks_old_pin(self):
  b=self.brand();p=self.create(b['hash']);store=self.s.brand_library;draft=store.command({'action':'save','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'payload':dict(P,mandatory_rules=['New mandatory restriction'])});approved=store.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':draft['hash'],'reviewer':'Owner','acknowledge':True})
  with self.assertRaises(UIError):self.s.scene(p['project_id'],0)
  p=self.change(self.s.view(p['project_id']),approved['hash'],BRIEF);self.s.scene(p['project_id'],p['revision'])
 def test_later_benign_preferences_preserve_pinned_version(self):
  b=self.brand();p=self.create(b['hash']);store=self.s.brand_library;draft=store.command({'action':'save','brand_id':b['record']['brand_id'],'expected_head':b['hash'],'payload':dict(P,preferences=['New optional mood'])});store.command({'action':'approve','brand_id':b['record']['brand_id'],'expected_head':draft['hash'],'reviewer':'Owner','acknowledge':True});self.s.scene(p['project_id'],0);self.assertEqual(self.s.view(p['project_id'])['binding']['record']['brand']['hash'],b['hash'])
 def test_geometry_checkpoint_is_paired_and_v3_sticky(self):
  p=self.create();e=p['elements'][0];p=self.s.action({'action':'geometry','project_id':p['project_id'],'expected_revision':0,'view_id':p['view']['id'],'targets':[{'element_id':e['id'],'x':e['x'],'y':e['y'],'width':800,'height':240}],'acknowledge_upgrade':True});self.assertEqual(p['history_version'],3);self.assertGreaterEqual(len(self.s.pairs.candidates(p['project_id'])),2);self.s.action({'action':'save','project_id':p['project_id'],'expected_revision':p['revision']});p=self.s.action({'action':'undo','project_id':p['project_id'],'expected_revision':p['revision']});self.assertEqual(p['history_version'],3);self.assertEqual(p['binding']['record']['revision'],1)
 def test_quota_refusal_preserves_head(self):
  from unittest.mock import patch
  p=self.create();head=self.s.pairs.head(p['project_id'])
  with patch('visual_poster_studio.recovery.BUDGET',1):
   with self.assertRaises(UIError):self.change(p)
  self.assertEqual(self.s.pairs.head(p['project_id']),head)
 def test_named_history_cannot_be_deleted_by_new_pair(self):
  p=self.create();identity=p['project_id'];doc=core.snapshot(self.s.manual.document(identity),'Keep',self.root/'projects'/identity);self.s.manual._working[identity]=doc;self.s.action({'action':'save','project_id':identity,'expected_revision':doc['revision']});bad=copy.deepcopy(doc);bad['versions']=[];bad['revision']+=1
  with self.assertRaises(UIError):self.s.pairs.commit(identity,bad,self.s.pairs.bindings[identity],self.s.pairs.heads[identity])
 def test_bound_export_context_tamper_rejected(self):
  p=self.create();start=self.s.begin({'project_id':p['project_id'],'expected_revision':0});out=self.s.finish({'token':start['token'],'revision':0,'png':None,'qa':QA});path=Path(out['directory'])/'manifest.json';m=json.loads(path.read_text());m['binding_identity']['brief_hash']='0'*64;path.write_text(json.dumps(m));self.assertTrue(self.s.exports.audit()['blocked'])
 def test_recovery_retains_prior_binding_versions(self):
  from visual_poster_studio.binding_recover import recover
  p=self.create();original=p['binding']['record'];p=self.change(p);head=self.s.pairs.head(p['project_id']);self.s.close();destination=self.root.parent/('origin-history-'+uuid.uuid4().hex);recover(self.root,p['project_id'],head['commit'],destination,True);archive=destination/'bound-projects'/p['project_id']/'origin-history';records=[json.loads((folder/'binding.json').read_text()) for folder in archive.iterdir()];self.assertIn(original,records);self.assertEqual(len(records),2)
