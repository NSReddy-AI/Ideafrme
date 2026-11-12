import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from test_reorder import ReorderTests
from studio_manual_ui.service import UIError
from visual_poster_studio.service import VisualStudio
from visual_poster_studio.session import MARKER

class ResumeTests(ReorderTests):
    def restart(self):
        self.s.close();self.s=VisualStudio(self.root,resume=True);self.addCleanup(self.s.close);self.p=self.s.view(self.p['project_id'])
    def test_reopen_exact_history_and_svg(self):
        self.reorder();self.act('save');doc=self.s.manual.document(self.p['project_id']);scene=self.s.scene(self.p['project_id'],self.p['revision']);raw=(self.root/'projects'/self.p['project_id']/'creative.json').read_bytes()
        self.restart();self.assertEqual(doc,self.s.manual.document(self.p['project_id']));self.assertEqual(scene,self.s.scene(self.p['project_id'],self.p['revision']));self.assertEqual(raw,(self.root/'projects'/self.p['project_id']/'creative.json').read_bytes())
    def test_concurrent_writer(self):
        with self.assertRaises(UIError):VisualStudio(self.root,resume=True)
    def test_marker_link_and_legacy_refusal(self):
        marker=self.root/MARKER;value=json.loads(marker.read_text());value['manual_id']='00000000-0000-0000-0000-000000000001';marker.write_text(json.dumps(value));self.s.close()
        with self.assertRaises(UIError):VisualStudio(self.root,resume=True)
        marker.unlink()
        with self.assertRaises(UIError):VisualStudio(self.root,resume=True)
    def test_profile_change_refused(self):
        marker=self.root/MARKER;value=json.loads(marker.read_text());value['render_profile']['baseline']=9;marker.write_text(json.dumps(value));self.s.close()
        with self.assertRaises(UIError):VisualStudio(self.root,resume=True)
    def test_exports_and_expired_handshake(self):
        self.act('save');b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':self.p['revision']});saved=self.s.finish({'token':b['token'],'revision':self.p['revision'],'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}})
        directory=Path(saved['directory']);hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()};old=self.s.begin({'project_id':self.p['project_id'],'expected_revision':self.p['revision']});(self.s.exports.root/'partial-test').mkdir()
        self.restart();self.assertEqual(self.s.exports.status['sets'],2);self.assertEqual(len(self.s.exports.status['partial']),1)
        self.assertEqual(hashes,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()})
        with self.assertRaises(UIError):self.s.finish({'token':old['token'],'revision':self.p['revision'],'png':None,'qa':{}})
    def test_corrupt_export_blocks_exports_only(self):
        self.act('save');bad=self.s.exports.root/'bad';bad.mkdir();(bad/'manifest.json').write_text('{}');self.restart()
        self.assertTrue(self.s.exports.status['blocked'])
        with self.assertRaises(UIError):self.s.begin({'project_id':self.p['project_id'],'expected_revision':self.p['revision']})
        self.act('move',element_id=self.p['elements'][0]['id'],x=150,y=100)
    def test_missing_font_disables_render(self):
        self.act('save');self.s.close()
        with patch('visual_poster_studio.service.Fonts',side_effect=UIError('font','Missing font')):self.s=VisualStudio(self.root,resume=True)
        self.addCleanup(self.s.close);self.assertIsNone(self.s.fonts);self.assertEqual(self.s.view(self.p['project_id'])['project_id'],self.p['project_id'])
        with self.assertRaises(UIError):self.s.scene(self.p['project_id'],self.p['revision'])

    def test_port_conflict_explicit(self):
        import errno,io,sys,uuid
        from contextlib import redirect_stdout
        from visual_poster_studio.__main__ import main
        output=io.StringIO();root=self.root.parent/('port-'+uuid.uuid4().hex)
        with patch.object(sys,'argv',['visual','--root',str(root),'--port','0']),patch('visual_poster_studio.__main__.Server',side_effect=OSError(errno.EADDRINUSE,'injected busy port')),redirect_stdout(output):
            self.assertEqual(main(),2)
        self.assertEqual(json.loads(output.getvalue())['error'],'port-in-use')

class ProcessResumeTests(unittest.TestCase):
    def setUp(self):
        import uuid
        self.root=Path(os.environ['VISUAL_TEST_ROOT'])/('process-'+uuid.uuid4().hex);self.children=[]
        self.addCleanup(self.cleanup)
    def cleanup(self):
        for p in self.children:
            if p.poll() is None:p.kill();p.wait(timeout=3)
    def start(self,resume=False,fault=None,recover=None):
        import select,subprocess,sys
        script=Path(__file__).resolve().parents[1]/'tools/run_visual_resume_tests.py'
        cmd=[sys.executable,'-I','-B',str(script),'--child-server','--root',str(self.root)]
        if resume:cmd.append('--resume')
        if fault:cmd+=['--fault',fault]
        if recover:cmd+=['--recover-copy',recover,'--candidate','after']
        p=subprocess.Popen(cmd,cwd=script.parents[1],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=os.environ.copy());self.children.append(p)
        if not select.select([p.stdout],[],[],8)[0]:raise AssertionError('Child startup timed out')
        startup=json.loads(p.stdout.readline())
        if 'url' not in startup:raise AssertionError(str(startup))
        self.proc=p;self.origin=startup['url'];self.actual_root=Path(startup['runtime_root']);self.csrf=self.api('/api/session')['csrf'];return startup
    def api(self,path,body=None):
        import http.client
        from urllib.parse import urlsplit
        url=urlsplit(self.origin);c=http.client.HTTPConnection(url.hostname,url.port,timeout=4)
        headers={'Host':url.netloc}
        if body is not None:headers.update({'Origin':self.origin,'X-CSRF-Token':self.csrf,'Content-Type':'application/json'})
        c.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers)
        try:
            r=c.getresponse();data=json.loads(r.read())
            if r.status>=400:raise AssertionError(str(data))
            return data
        finally:c.close()
    def stop(self):
        import signal
        self.proc.send_signal(signal.SIGINT);self.assertEqual(self.proc.wait(timeout=4),0)
    def create(self):
        self.p=self.api('/api/projects',{'name':'Process restart','text':'తెలుగు é','language':'te'})['project']
    def action(self,kind,**extra):
        self.p=self.api('/api/action',{'project_id':self.p['project_id'],'expected_revision':self.p['revision'],'action':kind,**extra})['project']
    def test_full_process_restart_and_csrf(self):
        self.start();oldcsrf=self.csrf;self.create();self.action('add_shape',shape='rectangle')
        self.action('reorder',view_id='portrait',ordered_element_ids=[e['id'] for e in self.p['elements']][::-1],acknowledge_upgrade=True);self.action('save')
        raw=(self.root/'projects'/self.p['project_id']/'creative.json').read_bytes();scene=self.api('/api/scene',{'project_id':self.p['project_id'],'expected_revision':self.p['revision']});self.stop()
        self.start(resume=True);self.assertNotEqual(self.csrf,oldcsrf);p=self.api('/api/project/'+self.p['project_id'])['project'];self.assertEqual(self.p,p)
        self.assertEqual(raw,(self.root/'projects'/p['project_id']/'creative.json').read_bytes());self.assertEqual(scene,self.api('/api/scene',{'project_id':p['project_id'],'expected_revision':p['revision']}));self.stop()
    def crash(self,where):
        self.start();self.create();self.action('save');before=(self.root/'projects'/self.p['project_id']/'creative.json').read_bytes();self.stop()
        self.start(resume=True,fault=where);self.action('move',element_id=self.p['elements'][0]['id'],x=199,y=100)
        with self.assertRaises(Exception):self.action('save')
        self.assertEqual(self.proc.wait(timeout=4),-9)
        self.start(resume=True);status=self.api('/api/session')['analysis']['session_status'];self.assertEqual(status['recovery'][self.p['project_id']]['state'],'interrupted-save')
        if where=='before-primary':self.assertEqual((self.root/'projects'/self.p['project_id']/'creative.json').read_bytes(),before)
        self.stop()
    def test_sigkill_before_primary(self):self.crash('before-primary')
    def test_sigkill_after_primary_and_recovery_copy(self):
        self.crash('after-primary');original={str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        self.start(resume=True,recover=self.p['project_id']);self.assertNotEqual(self.actual_root,self.root)
        reopened=self.api('/api/project/'+self.p['project_id'])['project'];self.assertEqual(reopened['elements'][0]['x'],199);self.stop()
        self.assertEqual(original,{str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()})
