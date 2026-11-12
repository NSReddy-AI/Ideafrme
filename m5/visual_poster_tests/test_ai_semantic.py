import copy,json,os,unittest,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical
from visual_poster_studio import ai_semantic as ai,binding_workflow as flow
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.brands import Store
from test_project_bindings import BindingTests
from test_ai_adapter import IDENTITY,SETTINGS
from qualify_ai_constrained import FIXTURES
GOOD={'concepts':[
 {'direction':'Family ritual','rationale':'Turn reading into a quiet shared moment','axis':'vertical','order':'headline-first','focal':'top','hierarchy':'headline','alignment':'start','density':'airy','color':'light'},
 {'direction':'Discover different stories','rationale':'Invite curiosity through a welcoming range of books','axis':'horizontal','order':'support-first','focal':'middle','hierarchy':'balanced','alignment':'middle','density':'moderate','color':'dark'},
 {'direction':'Belong to a reading circle','rationale':'Give shared participation a collective voice','axis':'vertical','order':'support-first','focal':'bottom','hierarchy':'support','alignment':'end','density':'airy','color':'light'}]}
class SemanticTests(unittest.TestCase):
 brand=BindingTests.brand
 asset_brand=BindingTests.asset_brand
 def setUp(self):
  root=Path(os.environ['VISUAL_TEST_ROOT']);self.s=VisualStudio(root/('session-'+uuid.uuid4().hex));self.addCleanup(self.s.close);self.s.brand_library=Store(root/('library-'+uuid.uuid4().hex));self.p=flow.create(self.s,{'name':'Source','text':'Unchanged','language':'en','brief':FIXTURES['en'],'brand_hash':None,'acknowledge':True});self.measure=json.loads(Path(os.environ['SEMANTIC_MEASUREMENTS']).read_text())['results'];self.req=self.prepare()
 def prepare(self):
  p=self.s.view(self.p['project_id']);return ai.prepare(self.s,{'project_id':p['project_id'],'expected_revision':p['revision'],'expected_binding':p['binding']['hash'],'expected_head':p['binding']['published_head'],'seed':19,'acknowledge_brief':True},IDENTITY,SETTINGS)
 def raw(self,v=None):return json.dumps(v or GOOD).encode()
 def compile(self,v=None):return ai.compile(self.s,self.raw(v),self.req,self.measure)
 def bad(self,v):self.assertEqual(ai.reject_or_compile(self.s,self.raw(v),self.req,self.measure)['status'],'rejected')
 def test_three_measured_editable_documents(self):
  r=self.compile();self.assertEqual(len(r['documents']),3);self.assertEqual(len({s['svg_sha256'] for s in r['scenes']}),3);self.assertTrue(all(x['structural_dimensions']>=2 for x in r['differentiation']));self.assertEqual(r['approval'],'unapproved');self.assertEqual(r['documents'][0]['views'][0]['language'],self.p['view']['language'])
 def test_unicode_exact_and_source_unchanged(self):
  old=self.s.manual.document(self.p['project_id']);head=self.s.pairs.head(self.p['project_id']);r=self.compile();self.assertEqual(self.s.manual.document(self.p['project_id']),old);self.assertEqual(self.s.pairs.head(self.p['project_id']),head)
  for p in r['plans']:self.assertEqual(next(e['text'] for e in p['layers'] if e['id']=='headline'),FIXTURES['en']['topic'])
 def test_repeat_deterministic_identity(self):self.assertEqual(self.compile(),self.compile())
 def test_telugu_measurement_not_ascii_estimate(self):
  self.p=flow.create(self.s,{'name':'Telugu source','text':'పాఠ్యం','language':'te','brief':FIXTURES['te'],'brand_hash':None,'acknowledge':True});self.req=self.prepare();r=self.compile();self.assertTrue(all(next(e['text'] for e in p['layers'] if e['id']=='headline')==FIXTURES['te']['topic'] for p in r['plans']))
 def test_no_raw_geometry_fonts_or_effects(self):
  for key in ('x','y','font','shadow','paint_order','approved','cta'):
   v=copy.deepcopy(GOOD);v['concepts'][0][key]='invalid';self.bad(v)
 def test_unknown_semantics_no_downgrade(self):
  for key in ai.CHOICES:
   v=copy.deepcopy(GOOD);v['concepts'][0][key]='unsupported';self.bad(v)
 def test_model_duplicate_not_reassigned(self):
  v=copy.deepcopy(GOOD)
  for c in v['concepts']:c['focal']='top'
  self.bad(v)
 def test_editorial_duplicate_rejected(self):
  v=copy.deepcopy(GOOD)
  for c in v['concepts']:c['direction']='Same direction';c['rationale']='Same rationale'
  self.bad(v)
 def test_missing_measurement_no_approximate_fallback(self):
  self.measure['table']=[];self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_bad_measurement_font_and_metric(self):
  self.measure['fonts']['te']='0'*64;self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_nonfinite_measurement_refused(self):
  self.measure['table'][0]['sizes']['80']['width']=float('inf');self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_unfit_copy_refused_not_wrapped(self):
  for row in self.measure['table']:
   for m in row['sizes'].values():m['width']=3000
  self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_paint_order_safe_and_margins(self):
  for p in self.compile()['plans']:
   self.assertEqual([e['type'] for e in p['layers']],['shape','shape','text','text'])
   for e in p['layers'][2:]:self.assertGreaterEqual(e['x'],56);self.assertGreaterEqual(e['y'],56);self.assertLessEqual(e['x']+e['width'],1024);self.assertLessEqual(e['y']+e['height'],1294)
 def test_editor_operations_and_undo(self):
  d=self.compile()['documents'][0];old=copy.deepcopy(d);e=next(e for e in d['elements'] if e['type']=='text');r=core.apply(d,{'op':'move','element_id':e['id'],'x':e['x']+1,'y':e['y']},self.s.manual.projects/self.p['project_id']);r=core.undo(r,self.s.manual.projects/self.p['project_id']);self.assertEqual(r['elements'],old['elements']);self.assertEqual(r['approvals'],[])
 def test_stale_source_rejected(self):
  e=self.p['elements'][0];self.s.action({'action':'move','project_id':self.p['project_id'],'expected_revision':0,'element_id':e['id'],'x':90,'y':100});self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_revocation_after_preparation_rejected(self):
  from test_brands import UNKNOWN
  a,b=self.asset_brand();self.p=flow.create(self.s,{'name':'Brand source','text':'Source','language':'en','brief':FIXTURES['en'],'brand_hash':b['hash'],'acknowledge':True});self.req=self.prepare();self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn')});self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_version_tamper_and_duplicate_json(self):
  self.assertEqual(ai.reject_or_compile(self.s,b'{"concepts":[],"concepts":[]}',self.req,self.measure)['status'],'rejected');self.req['format']='old';self.assertEqual(ai.reject_or_compile(self.s,self.raw(),self.req,self.measure)['status'],'rejected')
 def test_failure_explicit_fallback(self):
  v=ai.reject_or_compile(self.s,None,self.req,self.measure,failure='Timeout');self.assertEqual(v['status'],'unavailable');self.assertEqual(v['retry'],'explicit-user-action-only')
 def test_standalone_save_reopen_exact(self):
  d=self.compile()['documents'][0];root=self.s.root/'standalone-check';root.mkdir();core.save(d,root);reopened=core.load(root);self.assertEqual(reopened,d);self.assertEqual(core.fingerprint(reopened),core.fingerprint(d))
 def test_history_v3_source_preserved(self):
  p=self.p;e=p['elements'][0];p=self.s.action({'action':'geometry','project_id':p['project_id'],'expected_revision':0,'view_id':p['view']['id'],'targets':[{'element_id':e['id'],'x':80,'y':100,'width':800,'height':240}],'acknowledge_upgrade':True});self.s.action({'action':'save','project_id':p['project_id'],'expected_revision':p['revision']});self.req=self.prepare();old=self.s.manual.document(p['project_id']);r=self.compile();self.assertEqual(self.s.manual.document(p['project_id']),old);self.assertEqual(old['history']['version'],3);self.assertEqual(r['documents'][0]['history'],{'cursor':0,'transactions':[]})
