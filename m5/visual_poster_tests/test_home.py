import os,uuid,unittest
from pathlib import Path
from types import SimpleNamespace
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.home import catalogue,switch
from visual_poster_studio.session import marker
from studio_manual_ui.service import UIError

class HomeTests(unittest.TestCase):
 def setUp(self):
  self.parent=Path(os.environ['VISUAL_TEST_ROOT']);self.source=self.parent/('home-source-'+uuid.uuid4().hex);self.target=self.parent/('home-target-'+uuid.uuid4().hex)
  self.a=VisualStudio(self.source);b=VisualStudio(self.target);self.target_id=marker(self.target)['manual_id'];b.close();self.server=SimpleNamespace(studio=self.a,csrf='old');self.addCleanup(lambda:self.server.studio.close());self.addCleanup(self.a.close)
 def request(self):return {'current_session_id':marker(self.source)['manual_id'],'target_session_id':self.target_id,'directory':self.target.name}
 def test_catalogue_metadata_only(self):
  rows=catalogue(self.parent);row=next(r for r in rows if r['directory']==self.target.name);self.assertEqual(row['session_id'],self.target_id);self.assertNotIn('project_name',row);self.assertIn('folder_modified_ns',row)
 def test_resume_success_lock_handover(self):
  # API targets direct runtime children; scoped test patches only the catalogue parent.
  from unittest.mock import patch
  with patch('visual_poster_studio.home.RUNTIME',self.parent):result=switch(self.server,self.request())
  self.assertTrue(result['reload_required']);self.assertEqual(self.server.studio.root,self.target);self.assertNotEqual(self.server.csrf,'old');again=VisualStudio(self.source,resume=True);again.close()
 def test_unsaved_project_blocks(self):
  from unittest.mock import patch
  self.a.create({'name':'Unsaved','text':'తెలుగు','language':'te'})
  with patch('visual_poster_studio.home.RUNTIME',self.parent),self.assertRaises(UIError):switch(self.server,self.request())
  self.assertIs(self.server.studio,self.a);self.assertEqual(self.server.csrf,'old')
 def test_stale_identity_refused(self):
  r=self.request();r['current_session_id']=str(uuid.uuid4())
  with self.assertRaises(UIError):switch(self.server,r)
 def test_paths_refused(self):
  for name in ['../escape','/tmp','a/b','a\\b','..']:
   r=self.request();r['directory']=name
   with self.assertRaises(UIError):switch(self.server,r)
 def test_target_identity_changed(self):
  from unittest.mock import patch
  r=self.request();r['target_session_id']=str(uuid.uuid4())
  with patch('visual_poster_studio.home.RUNTIME',self.parent),self.assertRaises(UIError):switch(self.server,r)
  self.assertIs(self.server.studio,self.a)
 def test_duplicate_writer_retains_current(self):
  from unittest.mock import patch
  contender=VisualStudio(self.target,resume=True)
  try:
   with patch('visual_poster_studio.home.RUNTIME',self.parent),self.assertRaises(UIError):switch(self.server,self.request())
   self.assertIs(self.server.studio,self.a)
  finally:contender.close()
 def test_navigation_reports_history_v3(self):self.assertEqual(self.a.navigation()['history_support'],[1,2,3])
 def test_saved_project_resume_exact(self):
  from unittest.mock import patch
  p=self.a.create({'name':'Saved','text':'తెలుగు é','language':'te'});self.a.action({'project_id':p['project_id'],'expected_revision':0,'action':'save'});before=self.a.manual.document(p['project_id'])
  with patch('visual_poster_studio.home.RUNTIME',self.parent):switch(self.server,self.request())
  self.server.studio.close();self.server.studio=VisualStudio(self.source,resume=True);self.assertEqual(before,self.server.studio.manual.document(p['project_id']))

 def test_server_shutdown_closes_active_session(self):
  from unittest.mock import patch
  from visual_poster_studio.server import Server,ManualServer
  fake=object.__new__(Server);fake.studio=self.a
  with patch.object(ManualServer,'server_close'):
   fake.server_close()
  self.assertIsNone(self.a.manual._fd)
 def test_invalid_ownership_unavailable(self):
  import json
  path=self.target/'visual-session.json';value=json.loads(path.read_text());value['visual_session']=99;path.write_text(json.dumps(value))
  row=next(r for r in catalogue(self.parent) if r['directory']==self.target.name);self.assertIsNone(row['session_id']);self.assertIn('unavailable',row['status'])
 def test_pending_export_blocks_switch(self):
  from unittest.mock import patch
  self.a.exports.pending={'synthetic':True}
  with patch('visual_poster_studio.home.RUNTIME',self.parent),self.assertRaises(UIError):switch(self.server,self.request())
  self.assertIs(self.server.studio,self.a)
