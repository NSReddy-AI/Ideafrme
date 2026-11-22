import copy,json,os,threading,time,unittest,http.client
from pathlib import Path
from visual_poster_studio import hybrid_jobs as jobs,binding_workflow as flow
from visual_poster_studio.server import Server
from studio_manual_ui.service import UIError
from test_ai_hybrid import HybridTests,GOOD
from test_ai_adapter import IDENTITY
class Synthetic:
 identity=IDENTITY
 def __init__(self,mode='good'):self.mode=mode
 def available(self):return self.mode!='missing'
 def execute(self,path,request,cancel,stage):
  stage('inferencing')
  if self.mode=='wait':
   cancel.wait(3)
   if cancel.is_set():raise jobs.Cancelled()
  if self.mode=='timeout':raise UIError('ai-timeout','Synthetic timeout')
  if self.mode=='fault':raise UIError('ai-termination-unconfirmed','Synthetic unconfirmed termination')
  return b'{bad' if self.mode=='invalid' else json.dumps(GOOD).encode()
class JobTests(unittest.TestCase):
 brand=HybridTests.brand
 asset_brand=HybridTests.asset_brand
 def prepare(self):return HybridTests.prepare(self)
 def setUp(self):HybridTests.setUp(self);self.j=jobs.Jobs(self.s,Synthetic());self.addCleanup(self.j.close)
 def request(self):return {'source':copy.deepcopy(self.req['source']),'measurements':copy.deepcopy(self.measure)}
 def wait(self):
  deadline=time.monotonic()+3
  while self.j.active and time.monotonic()<deadline:time.sleep(.01)
  self.assertFalse(self.j.active);return self.j.status()['job']
 def test_status_does_not_launch(self):self.assertIsNone(self.j.status()['job']);self.assertFalse((self.s.root/'hybrid-jobs').exists())
 def test_success_selection_paired_and_export_identity(self):
  old=self.s.manual.document(self.p['project_id']);self.j.start(self.request());v=self.wait();self.assertEqual(v['state'],'ready');p=self.j.select({'job_id':v['id'],'concept_id':'1','acknowledge_rules':True})['project'];self.assertTrue(p['saved']);self.assertEqual(p['approval_count'],0);self.assertEqual(p['binding']['record']['brief'],self.p['binding']['record']['brief']);self.assertIn('binding_identity',self.s.scene(p['project_id'],0));self.assertEqual(old,self.s.manual.document(self.p['project_id']))
 def test_cancel_is_terminal_no_project_creation(self):
  self.j.executor=Synthetic('wait');before=self.s.list_projects();j=self.j.start(self.request());self.j.cancel({'job_id':j['id']});v=self.wait();self.assertEqual(v['state'],'cancelled');self.assertEqual(before,self.s.list_projects())
  with self.assertRaises(UIError):self.j.select({'job_id':v['id'],'concept_id':'0','acknowledge_rules':True})
 def test_busy_and_session_close(self):
  self.j.executor=Synthetic('wait');self.j.start(self.request())
  with self.assertRaises(UIError):self.j.start(self.request())
  self.j.close();self.assertFalse(self.j.active);self.assertFalse(self.j.thread.is_alive())
 def test_timeout_and_invalid_output_do_not_publish(self):
  old=self.s.manual.document(self.p['project_id'])
  for mode,state in [('timeout','timeout'),('invalid','failed')]:
   self.j.executor=Synthetic(mode);self.j.start(self.request());self.assertEqual(self.wait()['state'],state);self.assertEqual(old,self.s.manual.document(self.p['project_id']))
 def test_unconfirmed_termination_blocks_future_jobs(self):
  self.j.executor=Synthetic('fault');self.j.start(self.request());self.assertEqual(self.wait()['state'],'fault');self.assertFalse(self.j.status()['available'])
  with self.assertRaises(UIError):self.j.start(self.request())
 def test_missing_model_no_acquisition(self):
  self.j.executor=Synthetic('missing')
  with self.assertRaises(UIError):self.j.start(self.request())
  self.assertFalse((self.s.root/'hybrid-jobs').exists())
 def test_duplicate_and_unacknowledged_selection_refused(self):
  j=self.j.start(self.request());self.wait()
  with self.assertRaises(UIError):self.j.select({'job_id':j['id'],'concept_id':'0','acknowledge_rules':False})
  self.j.select({'job_id':j['id'],'concept_id':'0','acknowledge_rules':True})
  with self.assertRaises(UIError):self.j.select({'job_id':j['id'],'concept_id':'0','acknowledge_rules':True})
 def test_edit_after_generation_blocks_selection(self):
  j=self.j.start(self.request());self.wait();e=self.p['elements'][0];self.s.action({'action':'move','project_id':self.p['project_id'],'expected_revision':0,'element_id':e['id'],'x':90,'y':100})
  with self.assertRaises(UIError):self.j.select({'job_id':j['id'],'concept_id':'0','acknowledge_rules':True})
 def test_bad_path_fields_and_measurements_refused(self):
  for req in [dict(self.request(),path='/tmp/x'),{'source':self.req['source'],'measurements':{} }]:
   with self.assertRaises(UIError):self.j.start(req)
 def test_cancel_ready_discards_selection(self):
  j=self.j.start(self.request());self.wait();self.assertEqual(self.j.cancel({'job_id':j['id']})['state'],'cancelled')
 def test_rights_revocation_before_selection(self):
  from test_brands import UNKNOWN
  a,b=self.asset_brand();self.p=flow.create(self.s,{'name':'Brand source','text':'Source','language':'en','brief':self.p['binding']['record']['brief'],'brand_hash':b['hash'],'acknowledge':True});self.req=self.prepare();j=self.j.start(self.request());self.wait();self.s.brand_library.command({'action':'rights','asset_id':a['asset_id'],'expected_rights':a['rights_hash'],'rights':dict(UNKNOWN,status='denied',authority='Owner',evidence='withdrawn')})
  with self.assertRaises(UIError):self.j.select({'job_id':j['id'],'concept_id':'0','acknowledge_rules':True})
 def test_publication_failure_keeps_source(self):
  j=self.j.start(self.request());self.wait();old=self.s.pairs.head(self.p['project_id'])
  def fault(phase):
   if phase=='before-publication':raise OSError('Synthetic ENOSPC')
  self.s.pairs.fault=fault
  with self.assertRaises(UIError):self.j.select({'job_id':j['id'],'concept_id':'0','acknowledge_rules':True})
  self.assertEqual(self.s.pairs.head(self.p['project_id']),old)
 def test_diagnostic_validation_failure_blocks_results(self):
  from unittest.mock import patch
  original=jobs.exclusive
  def refuse_status(path,*args,**kwargs):
   if path.name=='status.json':raise UIError('path','Synthetic unsafe evidence path')
   return original(path,*args,**kwargs)
  with patch.object(jobs,'exclusive',side_effect=refuse_status):
   self.j.start(self.request());self.j.thread.join(2)
  self.assertEqual(self.j.status()['job']['state'],'fault');self.assertFalse(self.j.status()['available'])
class JobHTTPTests(JobTests):
 def setUp(self):
  super().setUp();self.server=Server(self.s,0);self.server.brand_root=self.s.brand_library.root;self.server._hybrid=self.j;self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01});self.thread.start();self.addCleanup(self.stop)
 def stop(self):self.server.shutdown();self.thread.join(2);self.server.server_close()
 def http(self,path,body=None,headers=None):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2);h={'Host':self.server.host}
  if body is not None:h.update({'Origin':self.server.origin,'X-CSRF-Token':self.server.csrf,'Content-Type':'application/json'})
  h.update(headers or {});c.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,h);v=c.getresponse();data=v.read();c.close();return v.status,json.loads(data)
 def test_http_security_and_live_status(self):
  self.assertEqual(self.http('/api/hybrid/status',headers={'Host':'evil.test'})[0],403)
  self.assertEqual(self.http('/api/hybrid/start',self.request(),{'X-CSRF-Token':'bad'})[0],403)
  self.assertEqual(self.http('/api/hybrid/start',self.request(),{'Origin':'http://evil.test'})[0],403)
  self.j.executor=Synthetic('wait');status,j=self.http('/api/hybrid/start',self.request());self.assertEqual(status,200);self.assertEqual(self.http('/api/hybrid/status')[0],200)
  self.assertEqual(self.http('/api/session/switch',{})[0],409);self.assertEqual(self.http('/api/hybrid/cancel',{'job_id':j['id']})[0],200);self.assertEqual(self.wait()['state'],'cancelled')
# Run HTTP-specific test only, rather than duplicate inherited cases.
