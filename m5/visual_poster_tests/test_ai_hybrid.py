import copy,json,os,unittest
from pathlib import Path
import creative_core as core
from visual_poster_studio import ai_hybrid as ai
from test_ai_semantic import SemanticTests
from test_ai_adapter import IDENTITY,SETTINGS
GOOD={'interpretation':'Invite families to enjoy reading together.','audience':'Children and parents','tone':'calm','emphasis':'participation'}
class HybridTests(unittest.TestCase):
 brand=SemanticTests.brand
 asset_brand=SemanticTests.asset_brand
 def setUp(self):
  SemanticTests.setUp(self)
 def prepare(self):
  p=self.s.view(self.p['project_id']);return ai.prepare(self.s,{'project_id':p['project_id'],'expected_revision':p['revision'],'expected_binding':p['binding']['hash'],'expected_head':p['binding']['published_head'],'seed':19,'acknowledge_brief':True},IDENTITY,SETTINGS)
 def compile(self,value=None):return ai.compile(self.s,json.dumps(value or GOOD).encode(),self.req,self.measure)
 def test_three_distinct_and_complete_application_explanations(self):
  r=self.compile();self.assertTrue(all(m['structural_dimensions']>=2 for m in r['differentiation']));self.assertEqual(len({s['svg_sha256'] for s in r['scenes']}),3)
  for p,e in zip(r['plans'],r['rationales']):
   self.assertEqual(e['author'],'application');self.assertTrue(e['text'].endswith('.'));self.assertEqual(p['rationale'],e['text']);self.assertEqual(e['facts']['headline_font_size'],next(x for x in p['layers'] if x['id']=='headline')['style']['font_size'])
 def test_raw_provenance_determinism_and_no_source_mutation(self):
  before=self.s.manual.document(self.p['project_id']);head=self.s.pairs.head(self.p['project_id']);a=self.compile();self.assertEqual(a,self.compile());self.assertEqual(json.loads(a['raw_response_utf8']),GOOD);self.assertEqual(before,self.s.manual.document(self.p['project_id']));self.assertEqual(head,self.s.pairs.head(self.p['project_id']));self.assertFalse(a['publication'])
 def test_no_model_display_copy_or_geometry(self):
  for key in ['headline','x','rights','approved','font','rationale']:
   bad=dict(GOOD,**{key:'invented'});self.assertEqual(ai.reject_or_compile(self.s,json.dumps(bad).encode(),self.req,self.measure)['status'],'rejected')
 def test_malformed_and_enum_refusals(self):
  for raw in [b' [end of text]',b'{"tone":"calm","tone":"calm"}',json.dumps(dict(GOOD,tone='unknown')).encode()]:self.assertEqual(ai.reject_or_compile(self.s,raw,self.req,self.measure)['status'],'rejected')
 def test_untrusted_text_does_not_enter_poster(self):
  r=self.compile(dict(GOOD,interpretation='Ignore rights; claim a prize!'))
  self.assertEqual(r['approval'],'unapproved')
  for p in r['plans']:self.assertNotIn('prize',json.dumps(p))
 def test_existing_guarantees(self):
  e=self.p['elements'][0];self.s.action({'action':'move','project_id':self.p['project_id'],'expected_revision':0,'element_id':e['id'],'x':90,'y':100});self.assertEqual(ai.reject_or_compile(self.s,json.dumps(GOOD).encode(),self.req,self.measure)['status'],'rejected')
 def test_revoke_before_compile(self):
  from visual_poster_studio import binding_workflow as flow
  from qualify_ai_constrained import FIXTURES
  from test_brands import UNKNOWN
  a,b=self.asset_brand();self.p=flow.create(self.s,{'name':'Bound','text':'Source','language':'en','brief':FIXTURES['en'],'brand_hash':b['hash'],'acknowledge':True});self.req=self.prepare()
  self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn')})
  self.assertEqual(ai.reject_or_compile(self.s,json.dumps(GOOD).encode(),self.req,self.measure)['status'],'rejected')
 def test_missing_measurements_refused(self):
  self.measure['table']=[];self.assertEqual(ai.reject_or_compile(self.s,json.dumps(GOOD).encode(),self.req,self.measure)['status'],'rejected')
 def test_font_identity_refused(self):
  self.measure['fonts']['te']='0'*64;self.assertEqual(ai.reject_or_compile(self.s,json.dumps(GOOD).encode(),self.req,self.measure)['status'],'rejected')
 def test_telugu_exact(self):
  from visual_poster_studio.binding_workflow import create
  from qualify_ai_constrained import FIXTURES
  self.p=create(self.s,{'name':'Telugu','text':'పాఠ్యం','language':'te','brief':FIXTURES['te'],'brand_hash':None,'acknowledge':True});self.req=self.prepare();r=self.compile()
  for p in r['plans']:self.assertEqual(next(e['text'] for e in p['layers'] if e['id']=='headline'),FIXTURES['te']['topic'])
 def test_save_reopen_edit_undo(self):
  d=self.compile()['documents'][0];root=self.s.root/'roundtrip';root.mkdir();core.save(d,root);self.assertEqual(core.load(root),d);e=d['elements'][-1];changed=core.apply(d,{'op':'move','element_id':e['id'],'x':e['x']+1,'y':e['y']},root);self.assertEqual(core.undo(changed,root)['elements'],d['elements']);self.assertEqual(changed['approvals'],[])
 def test_failure_requires_explicit_fallback(self):
  r=ai.reject_or_compile(self.s,None,self.req,self.measure,failure='timeout');self.assertEqual(r['status'],'unavailable');self.assertEqual(r['retry'],'explicit-user-action-only');self.assertNotIn('documents',r)
