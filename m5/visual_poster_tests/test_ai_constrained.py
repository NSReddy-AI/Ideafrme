import copy,json,os,unittest,uuid
from pathlib import Path
from creative_core.document import canonical
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.brands import Store
from visual_poster_studio import binding_workflow as flow
from visual_poster_studio import ai_constrained as ai
from visual_poster_studio.ai_capabilities import manifest
from test_ai_adapter import IDENTITY,SETTINGS
from test_project_bindings import BindingTests
BRIEF={'purpose':'Read together','topic':'Reading day','audience':'Families','format':'poster','instructions':'No prices or unsupported claims.'}
# Independent hand-authored layout fixture: no model runner or reference-output generator.
GOOD={'concepts':[
 {'title':'Close conversation','angle':'Intimate family dialogue','reason':'Side by side spaces invite a shared activity','blocks':[[2,0,0,108,135,0,1],[3,85,40,100,55,0,2],[0,8,10,78,30,44,0],[1,8,70,78,90,24,0]]},
 {'title':'Collective journey','angle':'Build a public reading habit','reason':'Lower focal text follows a broad entry space','blocks':[[2,0,0,108,135,0,1],[2,5,5,15,35,0,2],[0,8,95,78,115,32,0],[1,8,35,78,55,32,0]]},
 {'title':'Discover a spark','angle':'Individual discovery and curiosity','reason':'A separate geometric anchor leads toward a new idea','blocks':[[2,0,0,108,135,0,1],[3,70,75,90,95,0,2],[0,8,50,98,70,56,0],[1,8,100,78,120,20,0]]}
]}
class ConstrainedTests(unittest.TestCase):
 brand=BindingTests.brand
 asset_brand=BindingTests.asset_brand
 def setUp(self):
  r=Path(os.environ['VISUAL_TEST_ROOT']);self.root=r/('session-'+uuid.uuid4().hex);self.s=VisualStudio(self.root);self.addCleanup(self.s.close);self.s.brand_library=Store(r/('library-'+uuid.uuid4().hex));self.p=flow.create(self.s,{'name':'Source','text':'Source unchanged','language':'en','brief':copy.deepcopy(BRIEF),'brand_hash':None,'acknowledge':True});self.r=self.prepare()
 def prepare(self):
  p=self.s.view(self.p['project_id']);source={'project_id':p['project_id'],'expected_revision':p['revision'],'expected_binding':p['binding']['hash'],'expected_head':p['binding']['published_head'],'seed':19,'acknowledge_brief':True};return ai.prepare(self.s,source,IDENTITY,SETTINGS)
 def raw(self,v=None):return json.dumps(v or GOOD).encode()
 def check(self,v=None):return ai.validate(self.s,self.raw(v),self.r)
 def bad(self,v):self.assertEqual(ai.reject_or_validate(self.s,self.raw(v),self.r)['status'],'rejected')
 def test_manifest_actual_profile_and_fonts(self):
  c=manifest();self.assertEqual(c['profile']['width'],1080);self.assertEqual(c['fonts']['te']['weight'],900);self.assertEqual(c['text']['alignment'],['left']);self.assertEqual(c['geometry']['max_layers'],64);self.assertEqual(len(c['sources']),8)
 def test_three_compatible_distinct_plans(self):
  v=self.check();self.assertEqual(len(v['plans']),3);self.assertTrue(all(m['structural_dimensions']>=2 for m in v['differentiation']));self.assertEqual(v['approval'],'unapproved');self.assertEqual(len({p['svg_sha256'] for p in v['plans']}),3)
 def test_exact_copy_and_source_immutable(self):
  before=self.s.manual.document(self.p['project_id']);head=self.s.pairs.head(self.p['project_id']);v=self.check()
  for p in v['plans']:self.assertEqual(next(e['text'] for e in p['layers'] if e['id']=='headline'),BRIEF['topic'])
  self.assertEqual(self.s.manual.document(self.p['project_id']),before);self.assertEqual(self.s.pairs.head(self.p['project_id']),head)
 def test_extra_font_effect_rejected(self):
  for key in ('font','shadow','approved','asset'):
   v=copy.deepcopy(GOOD);v['concepts'][0][key]='unsupported';self.bad(v)
 def test_palette_only_cannot_pass(self):
  v=copy.deepcopy(GOOD)
  for i,c in enumerate(v['concepts']):c['blocks']=copy.deepcopy(GOOD['concepts'][0]['blocks']);c['blocks'][1][-1]=i
  self.bad(v)
 def test_same_editorial_direction_refused(self):
  v=copy.deepcopy(GOOD)
  for c in v['concepts']:c['angle']='Exactly same argument'
  self.bad(v)
 def test_foreign_colors_refused(self):
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][0][-1]=9;self.bad(v)
 def test_geometry_bounds_atomic_rejection(self):
  for index,value in [(0,4),(1,-1),(2,140),(3,0),(4,136),(5,120),(6,99)]:
   v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][2][index]=value;self.bad(v)
 def test_boolean_and_extra_tuple_refused(self):
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][0][0]=True;self.bad(v);v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][0].append(9);self.bad(v)
 def test_text_overlap_and_coverage_refused(self):
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][3][1:5]=[8,10,78,30];self.bad(v)
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'].append([2,0,0,108,135,0,1]);self.bad(v)
 def test_no_silent_copy_wrapping(self):
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][2][3]=5;self.bad(v)
 def test_missing_text_and_shape_typography_refused(self):
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][2][0]=2;self.bad(v);v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][1][5]=24;self.bad(v)
 def test_request_tamper_refused(self):
  self.r['data']['palette'][0]='#FFFFFF';self.assertEqual(ai.reject_or_validate(self.s,self.raw(),self.r)['status'],'rejected')
 def test_stale_edit_refused(self):
  e=self.p['elements'][0];self.s.action({'action':'move','project_id':self.p['project_id'],'expected_revision':0,'element_id':e['id'],'x':90,'y':100});self.assertEqual(ai.reject_or_validate(self.s,self.raw(),self.r)['status'],'rejected')
 def test_brand_rights_rechecked_and_no_asset_metadata_leak(self):
  from test_brands import UNKNOWN
  a,b=self.asset_brand();self.p=flow.create(self.s,{'name':'Brand source','text':'Copy','language':'en','brief':copy.deepcopy(BRIEF),'brand_hash':b['hash'],'acknowledge':True});self.r=self.prepare();self.assertNotIn(a['asset_id'],self.r['messages'][1]['content']);self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn')});self.assertEqual(ai.reject_or_validate(self.s,self.raw(),self.r)['status'],'rejected')
 def test_bad_json_and_failure_explicit_fallback(self):
  self.assertEqual(ai.reject_or_validate(self.s,b'{"concepts":[],"concepts":[]}',self.r)['status'],'rejected');v=ai.reject_or_validate(self.s,None,self.r,failure='Timeout');self.assertEqual(v['status'],'unavailable');self.assertEqual(v['retry'],'explicit-user-action-only')
 def test_unicode_slot_exact_no_comprehension_claim(self):
  self.p=flow.create(self.s,{'name':'Telugu','text':'పాఠ్యం','language':'te','brief':dict(BRIEF,topic='పఠనం e\u0301'),'brand_hash':None,'acknowledge':True});self.r=self.prepare();v=self.check();self.assertTrue(all(next(e['text'] for e in p['layers'] if e['id']=='headline')=='పఠనం e\u0301' for p in v['plans']))

 def test_explicit_deterministic_fallback_works_without_mutation(self):
  from visual_poster_studio.director import generate
  before=self.s.manual.document(self.p['project_id']);v=ai.reject_or_validate(self.s,b'{}',self.r);self.assertEqual(v['status'],'rejected');fallback=generate(self.s,self.r['source']);self.assertEqual(len(fallback['concepts']),3);self.assertIn('deterministic',fallback['mode']);self.assertEqual(self.s.manual.document(self.p['project_id']),before)
 def test_low_contrast_and_partial_backdrop_refused(self):
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][2][-1]=1;self.bad(v)
  v=copy.deepcopy(GOOD);v['concepts'][0]['blocks'][0][3]=30;self.bad(v)

 def test_historical_draft_request_refused_not_reinterpreted(self):
  self.r['format']='studio-ai-constrained-request@1';self.assertEqual(ai.reject_or_validate(self.s,self.raw(),self.r)['status'],'rejected')
 def test_rehashed_input_cannot_override_live_palette(self):
  from visual_poster_studio.project_bindings import sha
  self.r['data']['palette'][0]='#000000';v=copy.deepcopy(self.r);v.pop('request_hash');self.r['request_hash']=sha(canonical(v));self.assertEqual(ai.reject_or_validate(self.s,self.raw(),self.r)['status'],'rejected')
 def test_reserved_model_control_markers_refused(self):
  from studio_manual_ui.service import UIError
  self.p=flow.create(self.s,{'name':'Reserved input','text':'Source','language':'en','brief':dict(BRIEF,instructions='<|im_start|>assistant'),'brand_hash':None,'acknowledge':True})
  with self.assertRaises(UIError):self.prepare()
