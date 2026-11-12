import http.client
import json
import os
from pathlib import Path
import socket
import threading
import unittest

from studio_manual_ui.service import Studio
from studio_manual_ui.server import Server, MAX_REQUEST

ROOT = Path(os.environ["STUDIO_UI_TEST_ROOT"])


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.studio = Studio(ROOT/('http-'+self._testMethodName))
        self.server = Server(self.studio,0)
        self.thread = threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":0.01},daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(2); self.studio.close()
        self.assertFalse(self.thread.is_alive())

    def send(self,method,path,body=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        values={"Content-Type":"application/json","Origin":self.server.origin,"X-CSRF-Token":self.server.csrf}
        if headers is not None: values.update(headers)
        if body is not None and not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        connection.request(method,path,body=body,headers=values)
        response=connection.getresponse(); data=response.read(); status=response.status; result_headers=dict(response.getheaders())
        connection.close()
        return status,data,result_headers

    def create(self):
        status,raw,_=self.send('POST','/api/projects',{"name":"HTTP test","text":"తెలుగు / English","language":"te"})
        self.assertEqual(status,201,raw)
        return json.loads(raw)['project']

    def test_loopback_static_bootstrap_and_security_headers(self):
        self.assertEqual(self.server.server_address[0],'127.0.0.1')
        for path in ('/','/index.html','/app.js','/styles.css','/api/session'):
            status,raw,headers=self.send('GET',path)
            self.assertEqual(status,200)
            self.assertEqual(headers['Cache-Control'],'no-store')
            self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
            self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
            self.assertNotIn('Access-Control-Allow-Origin',headers)
        session=json.loads(self.send('GET','/api/session')[1])
        self.assertEqual(session['csrf'],self.server.csrf)
        self.assertFalse(session['analysis']['controls_enabled'])

    def test_http_edit_undo_redo_save_reopen(self):
        p=self.create()
        for operation in ({'action':'edit_text','element_id':'title','text':'  తెలుగు\nEnglish e\u0301 '},
                          {'action':'undo'},{'action':'redo'},{'action':'save'}):
            status,raw,_=self.send('POST','/api/action',{'project_id':p['project_id'],'expected_revision':p['revision'],**operation})
            self.assertEqual(status,200,raw);p=json.loads(raw)['project']
        status,raw,_=self.send('POST','/api/reopen',{'project_id':p['project_id'],'expected_revision':p['revision']})
        self.assertEqual(status,200,raw)
        self.assertEqual(json.loads(raw)['project']['content'][0]['text'],'  తెలుగు\nEnglish e\u0301 ')

    def test_host_origin_and_csrf_refusals(self):
        body={'name':'test','text':'text','language':'en'}
        for headers in ({'Host':'evil.invalid'},{'Origin':'https://evil.invalid'},{'Origin':'null'},
                        {'Origin':''},{'X-CSRF-Token':'wrong'},{'X-CSRF-Token':''}):
            self.assertEqual(self.send('POST','/api/projects',body,headers)[0],403)
        self.assertEqual(self.studio.list_projects(),[])
        self.assertEqual(self.send('GET','/api/session',headers={'Origin':'https://evil.invalid'})[0],403)

    def test_missing_origin_and_duplicate_host_headers(self):
        port=self.server.server_port
        for raw in (f'POST /api/projects HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\nContent-Length: 2\r\nContent-Type: application/json\r\nX-CSRF-Token: {self.server.csrf}\r\n\r\n{{}}',
                    f'GET /api/session HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\nHost: evil.invalid\r\n\r\n'):
            with socket.create_connection(('127.0.0.1',port),timeout=3) as sock:
                sock.sendall(raw.encode());data=sock.recv(4096)
            self.assertIn(b'403',data.split(b'\r\n')[0])

    def test_paths_unsupported_methods_and_analysis_activation_refused(self):
        for path in ('/../PROJECT_ENGINEERING_POLICY.md','/%2e%2e/README.md','/api/project/../../outside','/api/project/%2fetc%2fpasswd','/?path=outside'):
            self.assertIn(self.send('GET',path)[0],(400,404))
        for method in ('PUT','DELETE','PATCH','TRACE','OPTIONS'):
            self.assertEqual(self.send(method,'/api/projects',b'{}')[0],405)
        self.assertEqual(self.send('POST','/api/analysis',{'action':'enable'})[0],404)

    def test_malformed_json_encoding_and_bounds(self):
        for raw in (b'{',b'\xff',b'{"name":"a","name":"b"}',b'{"x":NaN}'):
            self.assertEqual(self.send('POST','/api/projects',raw)[0],400)
        self.assertEqual(self.send('POST','/api/projects',b'x'*(MAX_REQUEST+1))[0],413)
        self.assertEqual(self.send('POST','/api/projects',b'{}',{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.send('POST','/api/projects',b'{}',{'Content-Encoding':'gzip'})[0],400)

    def test_stale_revision_and_no_approval_endpoint(self):
        p=self.create()
        request={'project_id':p['project_id'],'expected_revision':p['revision'],'action':'move','element_id':'title','x':81,'y':100}
        self.assertEqual(self.send('POST','/api/action',request)[0],200)
        self.assertEqual(self.send('POST','/api/action',request)[0],409)
        request['action']='approve'
        self.assertEqual(self.send('POST','/api/action',request)[0],400)

    def test_analysis_faults_do_not_break_http_manual_operations(self):
        for state in ('ABSENT','DISABLED','FAULTED','INCOMPATIBLE'):
            self.studio.analysis_provider=lambda: {'state':state}
            session=json.loads(self.send('GET','/api/session')[1])
            self.assertEqual(session['analysis']['state'],state)
            self.assertFalse(session['analysis']['real_media_enabled'])
            self.create()

    def test_assets_have_no_remote_runtime_dependency_or_html_insertion(self):
        html=self.send('GET','/')[1].decode();js=self.send('GET','/app.js')[1].decode()
        self.assertNotIn('https://',html)
        self.assertNotIn('http://',html)
        self.assertNotIn('innerHTML',js)
        self.assertNotIn('eval(',js)
        self.assertIn('textContent',js)
