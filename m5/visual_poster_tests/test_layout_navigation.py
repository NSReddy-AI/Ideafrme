import hashlib
import json
import http.client
import threading
from pathlib import Path
from test_service import ServiceCase
from studio_manual_ui.service import UIError
from visual_poster_studio.server import Server

class LayoutNavigationTests(ServiceCase):
    def test_readonly_navigation(self):
        files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()};doc=self.s.manual.document(self.p['project_id']);nav=self.s.navigation()
        self.assertEqual(nav['runtime_root'],str(self.root));self.assertEqual(nav['analysis'],'OFF');self.assertEqual(len(nav['projects']),1);self.assertEqual(nav['exports'],[])
        self.assertEqual(files,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()});self.assertEqual(doc,self.s.manual.document(self.p['project_id']))
    def test_saved_export_receipt(self):
        self.action('font_size',element_id=self.p['elements'][0]['id'],font_size=40);self.action('save')
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':self.p['revision']});saved=self.s.finish({'token':b['token'],'revision':self.p['revision'],'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}})
        receipt=self.s.navigation()['exports'][0];self.assertEqual(receipt['state'],'draft');self.assertEqual(receipt['svg_sha256'],saved['manifest']['svg_sha256']);self.assertEqual(receipt['directory'],saved['directory'])
    def test_incomplete_receipt_metadata(self):
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':self.p['revision']});saved=self.s.finish({'token':b['token'],'revision':self.p['revision'],'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}})
        manifest=Path(saved['directory'])/'manifest.json';value=json.loads(manifest.read_text());value.pop('revision');manifest.write_text(json.dumps(value))
        nav=self.s.navigation();self.assertEqual(nav['exports'][0]['state'],'review-required');self.assertTrue(nav['export_status']['blocked'])
    def test_partial_and_corrupt_exports(self):
        (self.s.exports.root/'partial').mkdir();bad=self.s.exports.root/'corrupt';bad.mkdir();(bad/'manifest.json').write_text('{}');nav=self.s.navigation()
        states={item['id']:item['state'] for item in nav['exports']};self.assertEqual(states,{'corrupt':'review-required','partial':'partial'});self.assertTrue(nav['export_status']['blocked'])
    def test_navigation_rejects_alias(self):
        (self.s.exports.root/'alias').symlink_to(self.root/'projects',target_is_directory=True)
        with self.assertRaises(UIError):self.s.navigation()
    def test_alignment_move_undo_and_svg(self):
        e=self.p['elements'][0];old=self.s.scene(self.p['project_id'],self.p['revision']);self.action('move',element_id=e['id'],x=80,y=575);self.assertEqual(self.p['elements'][0]['y'],575);self.action('undo');self.assertEqual(old['svg'],self.s.scene(self.p['project_id'],self.p['revision'])['svg'])

class NavigationHTTPTests(ServiceCase):
    def setUp(self):
        super().setUp();self.server=Server(self.s,0);self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01});self.thread.start();self.addCleanup(self.stop)
    def stop(self):self.server.shutdown();self.thread.join(2);self.server.server_close()
    def get(self,path,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2);h={'Host':self.server.host};h.update(headers or {});c.request('GET',path,headers=h);r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
    def test_fixed_local_modules(self):
        for path in ['/layout.mjs','/layout_browser.mjs']:self.assertEqual(self.get(path)[0],200)
    def test_navigation_route(self):
        status,raw=self.get('/api/navigation');self.assertEqual(status,200);self.assertEqual(json.loads(raw)['runtime_root'],str(self.root))
    def test_navigation_host_and_origin(self):
        self.assertEqual(self.get('/api/navigation',{'Host':'evil.test'})[0],403);self.assertEqual(self.get('/api/navigation',{'Origin':'http://evil.test'})[0],403)
    def test_no_path_arguments(self):
        self.assertEqual(self.get('/api/navigation?root=/tmp')[0],400);self.assertEqual(self.get('/api/navigation/../../outside')[0],404)
