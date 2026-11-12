import http.client
import json
import threading
from test_service import ServiceCase
from visual_poster_studio.server import Server

class HTTPTests(ServiceCase):
    def setUp(self):
        super().setUp();self.server=Server(self.s,0);self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01});self.thread.start();self.addCleanup(self.stop)
    def stop(self):self.server.shutdown();self.thread.join(2);self.server.server_close()
    def req(self,path='/',body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        h={'Host':self.server.host};h.update(headers or {})
        if body is not None:h.update({'Content-Type':'application/json','Origin':self.server.origin,'X-CSRF-Token':self.server.csrf})
        if headers:h.update(headers)
        c.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,h);r=c.getresponse();data=r.read();result=(r.status,data,dict(r.getheaders()));c.close();return result
    def test_static_and_csp(self):
        status,body,headers=self.req();self.assertEqual(status,200);self.assertIn(b'poster-preview',body);self.assertIn("img-src blob:",headers['Content-Security-Policy'])
    def test_bad_host(self):self.assertEqual(self.req(headers={'Host':'evil.test'})[0],403)
    def test_bad_origin(self):self.assertEqual(self.req('/api/export/cancel',{}, {'Origin':'http://evil.test'})[0],403)
    def test_bad_csrf(self):self.assertEqual(self.req('/api/export/cancel',{}, {'X-CSRF-Token':'bad'})[0],403)
    def test_path_refusal(self):
        for path in ['/../creative_core/document.py','/styles.css?x=1','/api/project/../../outside']:
            self.assertIn(self.req(path)[0],(400,404))
    def test_scene_revision(self):self.assertEqual(self.req('/api/scene',{'project_id':self.p['project_id'],'expected_revision':99})[0],409)
    def test_unknown_fields(self):self.assertEqual(self.req('/api/scene',{'path':'/tmp/other'})[0],400)
    def test_analysis(self):self.assertIn(b'agent-not-connected',self.req('/api/session')[1])

    def test_malformed_json(self):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        c.request('POST','/api/scene',b'{',{'Host':self.server.host,'Origin':self.server.origin,'X-CSRF-Token':self.server.csrf,'Content-Type':'application/json'})
        response=c.getresponse();response.read();self.assertEqual(response.status,400);c.close()
    def test_body_size_refused(self):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        c.request('POST','/api/export/finish',None,{'Host':self.server.host,'Origin':self.server.origin,'X-CSRF-Token':self.server.csrf,'Content-Type':'application/json','Content-Length':str(12*1024*1024+1)})
        response=c.getresponse();response.read();self.assertEqual(response.status,413);c.close()
