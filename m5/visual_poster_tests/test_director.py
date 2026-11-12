import copy,errno,json,os,unittest,uuid
from pathlib import Path
import creative_core as core
from creative_core.document import canonical
from studio_manual_ui.service import UIError
from visual_poster_studio import director as d
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.brands import Store
from visual_poster_studio import binding_workflow as flow
from test_project_bindings import BindingTests,BRIEF,QA

class DirectorTests(unittest.TestCase):
 brand=BindingTests.brand
 asset_brand=BindingTests.asset_brand
 def setUp(self):
  root=Path(os.environ['VISUAL_TEST_ROOT']);self.root=root/('session-'+uuid.uuid4().hex);self.s=VisualStudio(self.root);self.addCleanup(self.s.close);self.s.brand_library=Store(root/('library-'+uuid.uuid4().hex));self.p=flow.create(self.s,{'name':'Reviewed source','text':'Original source','language':'en','brief':dict(BRIEF,purpose='Inform readers',audience='Local community',topic='తెలుగు é local ideas'),'brand_hash':None,'acknowledge':True})
 def request(self):
  p=self.s.view(self.p['project_id']);return {'project_id':p['project_id'],'expected_revision':p['revision'],'expected_binding':p['binding']['hash'],'expected_head':p['binding']['published_head'],'seed':7,'acknowledge_brief':True}
 def select(self,r=None,c='editorial',**extra):
  r=r or self.request();b=d.generate(self.s,r);return d.select(self.s,dict(source=r,bundle_digest=b['digest'],concept_id=c,acknowledge_rules=True,**extra))
 def test_three_compositions_not_palette_swaps(self):
  b=d.generate(self.s,self.request());self.assertEqual(len(b['concepts']),3);self.assertEqual(len({canonical([(e['type'],e['x'],e['y'],e['width'],e['height']) for e in c['layers']]) for c in b['concepts']}),3);self.assertEqual(len({canonical(c['typography_hierarchy']) for c in b['concepts']}),3)
 def test_exact_reproducible_plans_and_seed(self):
  r=self.request();a=d.generate(self.s,r);self.assertEqual(a,d.generate(self.s,r));self.assertNotEqual(a['digest'],d.generate(self.s,dict(r,seed=8))['digest']);self.assertEqual(a['inputs']['brief'],self.p['binding']['record']['brief'])
 def test_source_unchanged_no_generated_approvals(self):
  old=self.s.manual.document(self.p['project_id']);head=copy.deepcopy(self.s.pairs.head(self.p['project_id']));value=self.select()['project'];self.assertEqual(self.s.manual.document(self.p['project_id']),old);self.assertEqual(self.s.pairs.head(self.p['project_id']),head);doc=self.s.manual.document(value['project_id']);self.assertEqual(doc['format'],core.FORMAT);self.assertEqual(doc['schema_version'],1);self.assertEqual(doc['approvals'],[]);self.assertEqual(doc['history'],{'cursor':0,'transactions':[]});self.assertNotEqual(doc['id'],old['id'])
 def test_all_selected_concepts_editable_and_saveable(self):
  for c in ('editorial','split','orbit'):
   p=self.select(c=c)['project'];e=next(e for e in p['elements'] if e['type']=='text');p=self.s.action({'action':'move','project_id':p['project_id'],'expected_revision':0,'element_id':e['id'],'x':e['x']+1,'y':e['y']});p=self.s.action({'action':'undo','project_id':p['project_id'],'expected_revision':p['revision']});self.assertEqual(next(x for x in p['elements'] if x['id']==e['id'])['x'],e['x']);self.s.action({'action':'save','project_id':p['project_id'],'expected_revision':p['revision']})
 def test_reopen_exact_document_binding_svg(self):
  p=self.select()['project'];identity=p['project_id'];doc=self.s.manual.document(identity);b=copy.deepcopy(p['binding']);scene=self.s.scene(identity,0);self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close);self.assertEqual(self.s.manual.document(identity),doc);self.assertEqual(self.s.view(identity)['binding'],b);self.assertEqual(self.s.scene(identity,0),scene)
 def test_export_identity_is_deterministic(self):
  p=self.select()['project'];first=self.s.scene(p['project_id'],0);self.assertEqual(first,self.s.scene(p['project_id'],0));start=self.s.begin({'project_id':p['project_id'],'expected_revision':0});result=self.s.finish({'token':start['token'],'revision':0,'png':None,'qa':QA});self.assertEqual(result['manifest']['binding_identity'],first['binding_identity']);self.assertFalse(self.s.exports.audit()['blocked'])
 def test_exact_copy_combining_marks_no_split_words(self):
  b=d.generate(self.s,self.request());topic=b['inputs']['brief']['topic'];self.assertIn('e\u0301',topic)
  for c in b['concepts']:
   rendered=next(x['text'] for x in c['layers'] if x['id']=='topic');self.assertEqual(rendered.replace('\n',''),topic.replace('\n',''));self.assertIn('e\u0301',rendered)
 def test_no_truncation_long_topic_refused(self):
  request=self.request();fields=dict(BRIEF,topic='a'*181);proposal={'project_id':self.p['project_id'],'expected_revision':0,'expected_binding':request['expected_binding'],'expected_head':request['expected_head'],'brand_hash':None,'brief':fields};_,h,_,_=flow.proposal(self.s,proposal);flow.change(self.s,{'proposal':proposal,'impact_hash':h,'acknowledge':True})
  with self.assertRaises(UIError):d.generate(self.s,self.request())
 def test_stale_binding_and_digest_refused(self):
  r=self.request();b=d.generate(self.s,r)
  with self.assertRaises(UIError):d.select(self.s,{'source':r,'bundle_digest':'0'*64,'concept_id':'editorial','acknowledge_rules':True})
  with self.assertRaises(UIError):d.generate(self.s,dict(r,expected_binding='0'*64))
 def test_reject_duplicate_selection_no_overwrite(self):
  p=self.select()['project'];old=self.s.manual.document(p['project_id'])
  with self.assertRaises(UIError):self.select()
  self.assertEqual(self.s.manual.document(p['project_id']),old)
 def test_ack_and_unknown_concept_required(self):
  r=self.request();b=d.generate(self.s,r)
  for ack,c in [(False,'editorial'),(True,'foreign')]:
   with self.assertRaises(UIError):d.select(self.s,{'source':r,'bundle_digest':b['digest'],'concept_id':c,'acknowledge_rules':ack})
  with self.assertRaises(UIError):d.generate(self.s,dict(r,acknowledge_brief=False))
 def test_saved_source_required(self):
  p=self.p;e=p['elements'][0];self.s.action({'action':'move','project_id':p['project_id'],'expected_revision':0,'element_id':e['id'],'x':120,'y':110})
  with self.assertRaises(UIError):d.generate(self.s,self.request())
 def test_seed_strict_and_request_paths_rejected(self):
  for value in [-1,2147483648,True,'../x',None]:
   with self.assertRaises(UIError):d.generate(self.s,dict(self.request(),seed=value))
  with self.assertRaises(UIError):d.generate(self.s,dict(self.request(),project_id='../project'))
 def test_missing_font_fails_closed(self):
  self.s.fonts=None
  with self.assertRaises(UIError):d.generate(self.s,self.request())
 def test_brand_snapshot_and_rules_review_no_assets_applied(self):
  b=self.brand();self.p=flow.create(self.s,{'name':'Brand source','text':'Brand source','language':'en','brief':dict(BRIEF,purpose='Inform',audience='Readers'),'brand_hash':b['hash'],'acknowledge':True});bundle=d.generate(self.s,self.request());self.assertEqual(bundle['rules'],b['record']['payload']['mandatory_rules']);p=self.select()['project'];self.assertEqual(p['binding']['record']['brand']['hash'],b['hash']);self.assertEqual(self.s.manual.document(p['project_id'])['assets'],[])
 def test_revocation_between_plan_and_select_blocks(self):
  from test_brands import UNKNOWN
  a,b=self.asset_brand();self.p=flow.create(self.s,{'name':'Rights source','text':'Source','language':'en','brief':dict(BRIEF,purpose='Inform',audience='Readers'),'brand_hash':b['hash'],'acknowledge':True});r=self.request();bundle=d.generate(self.s,r);self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='Withdrawn')})
  with self.assertRaises(UIError):d.select(self.s,{'source':r,'bundle_digest':bundle['digest'],'concept_id':'editorial','acknowledge_rules':True})
 def test_failed_publication_preserves_source(self):
  old=self.s.manual.document(self.p['project_id']);head=self.s.pairs.head(self.p['project_id'])
  def fault(phase):
   if phase=='before-publication':raise OSError(errno.ENOSPC,'Synthetic only')
  self.s.pairs.fault=fault
  with self.assertRaises(UIError):self.select()
  self.assertEqual(self.s.manual.document(self.p['project_id']),old);self.assertEqual(self.s.pairs.head(self.p['project_id']),head)
 def test_receipt_immutable_and_retained_on_failure(self):
  r=self.request();b=d.generate(self.s,r);self.select();path=self.root/'concept-proposals'/(b['digest']+'.json');self.assertEqual(json.loads(path.read_text()),b);self.assertEqual(path.stat().st_mode&0o222,0)
 def test_multiline_exact_copy_and_single_palette(self):
  self.assertEqual(d.wrap('తెలుగు e\u0301\nexact copy',8).replace('\n',''),'తెలుగు e\u0301exact copy')
  binding=copy.deepcopy(self.p['binding']['record']);binding['brief']['topic']='First line\nSecond line';self.assertEqual(len(d.directions(binding,0)),3)
 def test_receipt_limit_preserves_source(self):
  root=self.root/'concept-proposals';root.mkdir()
  for i in range(20):(root/(str(i)+'.json')).write_text('{}')
  before=self.s.pairs.head(self.p['project_id'])
  with self.assertRaises(UIError):self.select()
  self.assertEqual(self.s.pairs.head(self.p['project_id']),before)
 def test_v3_source_preserved_new_project_not_migrated(self):
  p=self.p;e=p['elements'][0];p=self.s.action({'action':'geometry','project_id':p['project_id'],'expected_revision':0,'view_id':p['view']['id'],'targets':[{'element_id':e['id'],'x':100,'y':100,'width':800,'height':240}],'acknowledge_upgrade':True});self.s.action({'action':'save','project_id':p['project_id'],'expected_revision':p['revision']});old=self.s.manual.document(p['project_id']);self.select();self.assertEqual(self.s.manual.document(p['project_id']),old);self.assertEqual(old['history']['version'],3)
 def test_new_project_post_publication_failure_reopens_complete(self):
  before=self.s.manual.document(self.p['project_id'])
  def fault(phase):
   if phase=='after-publication':raise OSError('Synthetic interrupted response')
  self.s.pairs.fault=fault
  with self.assertRaises(UIError):self.select()
  self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close);self.assertEqual(self.s.manual.document(self.p['project_id']),before);projects=self.s.list_projects();self.assertEqual(len(projects),2);new=next(p for p in projects if p['project_id']!=self.p['project_id']);self.assertEqual(self.s.view(new['project_id'])['binding']['record']['brief'],self.p['binding']['record']['brief'])
 def test_http_auth_and_open(self):
  import threading,urllib.request,urllib.error
  from visual_poster_studio.server import Server
  server=Server(self.s,0);server.brand_root=self.s.brand_library.root;t=threading.Thread(target=server.serve_forever,daemon=True);t.start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown);base='http://127.0.0.1:'+str(server.server_port)
  def post(path,body,headers):
   request=urllib.request.Request(base+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**headers});return urllib.request.urlopen(request,timeout=5)
  with self.assertRaises(urllib.error.HTTPError) as e:post('/api/director/generate',self.request(),{})
  self.assertEqual(e.exception.code,403)
  headers={'Origin':base,'X-CSRF-Token':server.csrf};b=json.load(post('/api/director/generate',self.request(),headers));result=json.load(post('/api/director/select',{'source':self.request(),'bundle_digest':b['digest'],'concept_id':'editorial','acknowledge_rules':True},headers));self.assertEqual(result['project']['name'],'Editorial hierarchy')
