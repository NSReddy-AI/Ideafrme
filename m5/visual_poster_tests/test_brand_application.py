import copy,json,os,unittest
from pathlib import Path
import creative_core as core
from visual_poster_studio import brand_application as brand,ai_hybrid as ai,binding_workflow as flow,director
from visual_poster_studio.service import VisualStudio
from test_ai_hybrid import HybridTests,GOOD
from test_ai_adapter import IDENTITY,SETTINGS
from test_brands import P,UNKNOWN
from qualify_ai_constrained import FIXTURES

PAYLOAD={**P,'typography':{'english':'Inter Bold','telugu':'Noto Sans Telugu Black'},'colors':['#14213D','#F6F4EF','#D7A441'],'mandatory_rules':['Only approved palette and supported fonts.','No additional display copy or invented claims.','Minimum safe margin: 56 px.','Minimum text contrast: 4.5:1.','No text overlap.']}
class ApplicationTests(unittest.TestCase):
 brand=HybridTests.brand
 asset_brand=HybridTests.asset_brand
 def prepare(self):return HybridTests.prepare(self)
 def setUp(self):HybridTests.setUp(self)
 def branded(self,payload=None,lang='en'):
  b=self.brand(copy.deepcopy(PAYLOAD if payload is None else payload));self.p=flow.create(self.s,{'name':'Brand A '+lang,'text':FIXTURES[lang]['topic'],'language':lang,'brief':copy.deepcopy(FIXTURES[lang]),'brand_hash':b['hash'],'acknowledge':True});self.req=self.prepare();return b
 def compile(self):return ai.compile(self.s,json.dumps(GOOD).encode(),self.req,self.measure)
 def install(self,index=0):
  result=self.compile();d=result['documents'][index];identity=d['id'];(self.s.manual.projects/identity).mkdir();b=self.s.pairs.new(identity,result['pinned_brand'],result['brief']);self.s.pairs.commit(identity,d,b,None);flow.mark_saved(self.s,identity,d);self.p=self.s.view(identity);return result
 def action(self,kind,**extra):
  p=self.s.view(self.p['project_id']);return self.s.action({'action':kind,'project_id':p['project_id'],'expected_revision':p['revision'],**extra})
 def test_unbranded_editing_unchanged(self):
  p=self.p;self.action('color',element_id=p['elements'][0]['id'],color='#abcdef');self.assertFalse(self.s.view(p['project_id'])['brand_application']['bound_brand'])
 def test_both_languages_three_distinct_brand_concepts(self):
  for lang in ('en','te'):
   self.branded(lang=lang);r=self.compile();self.assertTrue(all(m['structural_dimensions']>=2 for m in r['differentiation']))
   for d in r['documents']:
    p=brand.validate(d,self.s.pairs.bindings[self.p['project_id']]);self.assertEqual(p['typography']['telugu']['applied'],'Noto Sans Telugu Black');self.assertEqual({e['style']['fill'] for e in d['elements']} - set(PAYLOAD['colors']),set());self.assertEqual(next(c['text'] for c in d['content'] if c['id']==next(e['content_id'] for e in d['elements'] if e['id']=='headline')),FIXTURES[lang]['topic'])
 def test_existing_family_metadata_resolves_only_pinned_face(self):
  self.branded(dict(PAYLOAD,typography={'english':'Inter','telugu':'Noto Sans Telugu'}));r=self.compile();p=brand.validate(r['documents'][0],self.s.pairs.bindings[self.p['project_id']]);self.assertEqual(p['typography']['english']['applied'],'Inter Bold')
 def test_unsupported_fonts_and_unknown_rule_fail_before_generation(self):
  for payload in [dict(PAYLOAD,typography={'english':'Inter Regular','telugu':'Noto Sans Telugu Black'}),dict(PAYLOAD,mandatory_rules=['Make it luxurious and always use our logo.'])]:
   b=self.brand(payload);self.p=flow.create(self.s,{'name':'Blocked','text':'Reading day','language':'en','brief':FIXTURES['en'],'brand_hash':b['hash'],'acknowledge':True})
   with self.assertRaises(UIError):self.prepare()
   self.assertFalse(self.s.view(self.p['project_id'])['brand_application']['supported']);self.action('save')
 def test_approved_color_one_undo_and_approval_clear(self):
  self.branded();self.install();identity=self.p['project_id'];before=self.s.manual.document(identity);approved=core.snapshot(core.approve(before,'Fixture',self.s.manual.projects/identity),'Approved history',self.s.manual.projects/identity);self.s.manual._working[identity]=approved;e=next(e for e in before['elements'] if e['id']=='focal');old=e['style']['fill'];value=self.action('color',element_id=e['id'],color='#D7A441');after=self.s.manual.document(identity);self.assertEqual(after['revision'],approved['revision']+1);self.assertEqual(after['history']['cursor'],before['history']['cursor']+1);self.assertEqual(after['approvals'],[]);self.assertEqual(after['versions'],approved['versions']);self.action('undo');self.assertEqual(next(e for e in self.s.manual.document(identity)['elements'] if e['id']=='focal')['style']['fill'],old);self.assertEqual(self.s.manual.document(identity)['approvals'],[]);self.action('redo');self.assertEqual(next(e for e in self.s.manual.document(identity)['elements'] if e['id']=='focal')['style']['fill'],'#D7A441')
 def test_unapproved_color_and_copy_reject_without_revision(self):
  self.branded();self.install();before=self.s.manual.document(self.p['project_id']);e=next(e for e in before['elements'] if e['id']=='headline')
  for kind,extra in [('color',{'color':'#ff00ff'}),('edit_text',{'text':'Unapproved prize claim'}),('edit_text',{'text':[]})]:
   with self.assertRaises(UIError):self.action(kind,element_id=e['id'],**extra)
   self.assertEqual(self.s.manual.document(self.p['project_id']),before)
 def test_margin_overlap_font_constraints_rollback(self):
  self.branded();self.install();identity=self.p['project_id'];before=core.snapshot(core.approve(self.s.manual.document(identity),'Fixture reviewer',self.s.manual.projects/identity),'Protected history',self.s.manual.projects/identity);self.s.manual._working[identity]=before
  for kind,extra in [('move',{'x':0,'y':0})]:
   with self.assertRaises(UIError):self.action(kind,element_id='headline',**extra)
   self.assertEqual(self.s.manual.document(self.p['project_id']),before)
  other=next(e for e in before['elements'] if e['id']=='support')
  with self.assertRaises(UIError):self.action('move',element_id='headline',x=other['x'],y=other['y'])
  self.assertEqual(self.s.manual.document(self.p['project_id']),before)
 def test_explicit_font_bounds_and_unsatisfied_generation(self):
  self.branded(dict(PAYLOAD,mandatory_rules=PAYLOAD['mandatory_rules']+['Minimum font size: 24 px.','Maximum font size: 80 px.']));self.install();before=self.s.manual.document(self.p['project_id'])
  with self.assertRaises(UIError):self.action('font_size',element_id='headline',font_size=23)
  self.assertEqual(self.s.manual.document(self.p['project_id']),before)
  self.branded(dict(PAYLOAD,mandatory_rules=PAYLOAD['mandatory_rules']+['Minimum font size: 100 px.']))
  with self.assertRaises(UIError):self.compile()
 def test_contradictory_and_ambiguous_requirements(self):
  b={'brand':{'hash':'x','record':{'payload':dict(PAYLOAD,mandatory_rules=['Minimum font size: 80 px.','Maximum font size: 20 px.'])}}}
  self.assertTrue(brand.policy(b)['blocked'])
  b['brand']['record']['payload']['mandatory_rules']=['minimum safe margin: 56 px.'];self.assertTrue(brand.policy(b)['blocked'])
 def test_exports_revalidate_restored_invalid_state(self):
  self.branded();self.install();identity=self.p['project_id'];good=self.s.manual.document(identity);bad=core.apply(good,{'op':'restyle','element_id':'background','style':{'fill':'#ff00ff'}},self.s.manual.projects/identity);self.s.manual._working[identity]=bad
  with self.assertRaises(UIError):self.s.scene(identity,bad['revision'])
  self.action('save');self.s.manual._working[identity]=good
 def test_save_reopen_resume_preserves_binding_history_and_svg(self):
  self.branded();self.install();identity=self.p['project_id'];self.action('color',element_id='focal',color='#D7A441');self.action('save');d=self.s.manual.document(identity);scene=self.s.scene(identity,d['revision']);root=self.s.root;library=self.s.brand_library;self.s.close();self.s=VisualStudio(root,resume=True);self.addCleanup(self.s.close);self.s.brand_library=library;self.assertEqual(self.s.manual.document(identity),d);self.assertEqual(self.s.scene(identity,d['revision']),scene)
 def test_live_rights_revocation_blocks_application(self):
  a,b=self.asset_brand();self.p=flow.create(self.s,{'name':'Rights','text':'Reading day','language':'en','brief':FIXTURES['en'],'brand_hash':b['hash'],'acknowledge':True});self.req=self.prepare();self.install();self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn')});before=self.s.manual.document(self.p['project_id'])
  with self.assertRaises(UIError):self.action('color',element_id='headline',color='#FFFFFF')
  self.assertEqual(self.s.manual.document(self.p['project_id']),before);self.action('save')
 def test_deterministic_fallback_known_supported_profile(self):
  self.branded(dict(PAYLOAD,mandatory_rules=['Only approved palette and supported fonts.']))
  r=director.generate(self.s,self.req['source']);self.assertEqual(len(r['concepts']),3)
 def test_preserve_logo_geometry_does_not_load_or_require_logo(self):
  self.branded(dict(PAYLOAD,mandatory_rules=['Preserve logo geometry']));r=self.compile();self.assertTrue(all(d['assets']==[] for d in r['documents']))
 def test_new_layers_use_approved_default_and_undo(self):
  self.branded(dict(PAYLOAD,mandatory_rules=[]));before=self.s.manual.document(self.p['project_id']);p=self.action('add_shape',shape='ellipse');created=p['elements'][-1];self.assertEqual(created['style']['fill'],PAYLOAD['colors'][0]);self.assertEqual(p['revision'],before['revision']+1);self.action('undo');self.assertEqual(self.s.manual.document(self.p['project_id'])['elements'],before['elements'])
 def test_undo_can_restore_legacy_violation_but_export_blocks(self):
  self.branded(dict(PAYLOAD,mandatory_rules=[]));e=self.p['elements'][0];self.action('color',element_id=e['id'],color=PAYLOAD['colors'][0]);self.assertTrue(self.s.view(self.p['project_id'])['brand_application']['export_eligible']);self.action('undo');p=self.s.view(self.p['project_id']);self.assertFalse(p['brand_application']['export_eligible']);self.action('save')
from studio_manual_ui.service import UIError
