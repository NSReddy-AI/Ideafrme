"""Optional standalone loopback PNG workflow UI. Never imported by manual Studio."""
import base64,json,secrets,time,signal
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from studio_manual_ui.service import decode,exact
from .controller import Refused,safe
def serve(workflow,port):
 token=secrets.token_urlsafe(32);origin=f'http://127.0.0.1:{port}';pending={}
 def deadline(*_):raise TimeoutError('60-second complete job deadline')
 signal.signal(signal.SIGALRM,deadline)
 class Handler(BaseHTTPRequestHandler):
  def setup(self):super().setup();self.connection.settimeout(3)
  def log_message(self,*args):pass
  def send(self,code,data,kind='application/json'):
   if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
   self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; img-src blob: data:; font-src data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'");self.end_headers();self.wfile.write(data)
  def boundary(self,post=False):
   if self.headers.get('Host')!=f'127.0.0.1:{port}':raise Refused('Host refused')
   if self.headers.get('Origin') not in (None,origin):raise Refused('Origin refused')
   if self.headers.get('Sec-Fetch-Site') not in (None,'same-origin','none'):raise Refused('Cross-site request refused')
   if post and (self.headers.get('Origin')!=origin or self.headers.get('X-CSRF-Token')!=token):raise Refused('Origin/CSRF refused')
  def do_GET(self):
   try:
    self.boundary()
    if self.path=='/':return self.send(200,(Path(__file__).with_name('index.html')).read_bytes(),'text/html; charset=utf-8')
    if self.path in ('/app.js','/style.css'):return self.send(200,Path(__file__).with_name(self.path[1:]).read_bytes(),'text/javascript' if self.path.endswith('.js') else 'text/css')
    if self.path=='/browser_acceptance.js':return self.send(200,(Path(__file__).resolve().parents[1]/'visual_poster_tests/browser_acceptance.js').read_bytes(),'text/javascript')
    if self.path=='/fonts':
     from visual_poster_studio.fonts import Fonts
     return self.send(200,Fonts().public())
    if self.path=='/state':
     state=workflow.current();return self.send(200,{'csrf':token,'head':workflow.token(),'state':state,'analysis':'OFF','asset_choices':state['binding']['brand']['record']['payload']['asset_ids'],'runtime_root':str(workflow.root),'warning':'Separate media workflow v2; manual readers cannot open it. Drafts only.'})
    if self.path=='/scene':
     scene=workflow.scene();pending.clear();pending.update(head=scene['head'],sha256=scene['sha256'],expires=time.monotonic()+15);return self.send(200,scene)
    if self.path.startswith('/export/'):
     parts=self.path.split('/')
     import re
     if len(parts)!=4 or not re.fullmatch('[0-9a-f]{32}',parts[2]) or parts[3] not in ('draft.svg','draft.png'):raise Refused('Export path refused')
     workflow.scene(export_svg=True) # rights rechecked before downloading old artifacts
     p=safe(workflow.root/'exports'/parts[2]/parts[3]);raw=p.read_bytes()
     if len(raw)>8*1024*1024:raise Refused('Export limit')
     return self.send(200,raw,'image/svg+xml' if p.suffix=='.svg' else 'image/png')
    return self.send(404,{'error':'Not found'})
   except (ValueError,OSError,KeyError,TypeError) as e:return self.send(409,{'error':str(e)[:1024]})
  def do_POST(self):
   try:
    self.boundary(True)
    if self.headers.get('Content-Type')!='application/json':raise Refused('JSON required')
    lengths=self.headers.get_all('Content-Length',[])
    if len(lengths)!=1 or not lengths[0].isdigit() or not 0<int(lengths[0])<=12*1024*1024 or self.headers.get('Transfer-Encoding'):raise Refused('Request length refused')
    value=decode(self.rfile.read(int(lengths[0])))
    signal.alarm(60)
    if self.path=='/place':
     exact(value,{'head','asset_id','geometry'});identity=workflow.place(value['asset_id'],value['geometry'],value['head']);return self.send(200,{'id':identity})
    if self.path=='/action':
     exact(value,{'head','action','id','geometry'});workflow.action(value['action'],value['head'],value['id'],value['geometry']);return self.send(200,{'saved':True})
    if self.path=='/export':
     exact(value,{'head','scene_sha256','png'})
     if not pending or time.monotonic()>pending['expires'] or value['head']!=pending['head'] or value['scene_sha256']!=pending['sha256']:raise Refused('Export handshake expired or stale; refresh preview')
     expires=pending['expires'];pending.clear();raw=base64.b64decode(value['png'],validate=True);name=workflow.export(value['head'],raw,value['scene_sha256'],expires=expires);return self.send(200,{'svg':'/export/'+name+'/draft.svg','png':'/export/'+name+'/draft.png','name':name})
    return self.send(404,{'error':'Not found'})
   except (ValueError,OSError,KeyError,TypeError) as e:return self.send(409,{'error':str(e)[:1024]})
   finally:signal.alarm(0)
 server=HTTPServer(('127.0.0.1',port),Handler);server.timeout=1
 print(origin,flush=True)
 try:server.serve_forever()
 finally:server.server_close();workflow.close()
