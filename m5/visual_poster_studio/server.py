"""New loopback adapter, fixed routes and CSP; accepted HTTP handler untouched."""
import json
from pathlib import Path
from studio_manual_ui.server import Server as ManualServer, Handler as ManualHandler
from studio_manual_ui.service import UIError, exact, read

HERE=Path(__file__).parent
ASSETS={'/brand_application.mjs':('brand_application.mjs','text/javascript; charset=utf-8'),'/hybrid-acceptance':('../visual_poster_tests/hybrid_browser.html','text/html; charset=utf-8'),'/hybrid.mjs':('hybrid.mjs','text/javascript; charset=utf-8'),'/hybrid_browser.mjs':('../visual_poster_tests/hybrid_browser.mjs','text/javascript; charset=utf-8'),'/director.mjs':('director.mjs','text/javascript; charset=utf-8'),'/brands.mjs':('brands.mjs','text/javascript; charset=utf-8'),'/home.mjs':('home.mjs','text/javascript; charset=utf-8'),'/text_layout.mjs':('text_layout.mjs','text/javascript; charset=utf-8'),'/text_completion_browser.mjs':('../visual_poster_tests/text_completion_browser.mjs','text/javascript; charset=utf-8'),'/geometry_browser.mjs':('../visual_poster_tests/geometry_browser.mjs','text/javascript; charset=utf-8'),'/geometry.mjs':('geometry.mjs','text/javascript; charset=utf-8'),'/canvas.mjs':('canvas.mjs','text/javascript; charset=utf-8'),'/canvas_browser.mjs':('../visual_poster_tests/canvas_browser.mjs','text/javascript; charset=utf-8'),'/layout.mjs':('layout.mjs','text/javascript; charset=utf-8'),'/layout_browser.mjs':('../visual_poster_tests/layout_browser.mjs','text/javascript; charset=utf-8'),'/editing.mjs':('editing.mjs','text/javascript; charset=utf-8'),'/editing_browser.mjs':('../visual_poster_tests/editing_browser.mjs','text/javascript; charset=utf-8'),'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/styles.css':('styles.css','text/css; charset=utf-8'),
 '/acceptance':('../visual_poster_tests/browser_acceptance.html','text/html; charset=utf-8'),
 '/browser_acceptance.js':('../visual_poster_tests/browser_acceptance.js','text/javascript; charset=utf-8')}
class Server(ManualServer):
    @property
    def media(self):
        from .media_bridge import Media
        value=getattr(self,'_media',None)
        if value is None or value.studio is not self.studio:
            if value:value.close()
            self._media=Media(self)
        return self._media
    @property
    def hybrid(self):
        from .hybrid_jobs import Jobs
        existing=getattr(self,'_hybrid',None)
        if existing is None or existing.studio is not self.studio:
            if existing:existing.close()
            self._hybrid=Jobs(self.studio)
        return self._hybrid
    def server_close(self):
        media=getattr(self,'_media',None)
        if media:media.close()
        planner=getattr(self,'_hybrid',None)
        if planner:planner.close()
        try:super().server_close()
        finally:self.studio.close()
    def finish_request(self,request,client_address):Handler(request,client_address,self)
class Handler(ManualHandler):
    def reply(self,status,body,kind='application/json; charset=utf-8'):
        if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        for name,value in {'Content-Type':kind,'Content-Length':str(len(body)),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
            'Cross-Origin-Resource-Policy':'same-origin','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src blob:; font-src data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"}.items():self.send_header(name,value)
        self.end_headers();self.wfile.write(body)
    def body(self):
        # Fixed PNG/opaque-asset/package routes alone permit larger bounded JSON bodies.
        if self.path not in {'/api/export/finish','/api/media/export/finish','/api/brands/asset','/api/brands/restore-preview','/api/brands/restore'}:return super().body()
        values=self.headers.get_all('Content-Length',[])
        if len(values)!=1 or not values[0].isascii() or not values[0].isdigit() or len(values[0])>(9 if self.path in {'/api/brands/restore-preview','/api/brands/restore'} else 8):raise UIError('length','Invalid bounded length.',411)
        n=int(values[0])
        if n<1 or n>(100*1024*1024 if self.path in {'/api/brands/restore-preview','/api/brands/restore'} else 12*1024*1024):raise UIError('limit','Export request too large.',413)
        if self.headers.get_all('Content-Type',[])!=['application/json']:raise UIError('content-type','JSON required.',415)
        from studio_manual_ui.service import decode
        raw=self.rfile.read(n)
        if len(raw)!=n:raise UIError('json','Incomplete body.')
        return decode(raw)
    def dispatch(self,method):
        try:
            path=self.guard(mutation=method=='POST')
            if method=='GET' and path in ('/product.mjs','/media_gestures.mjs'):return self.reply(200,(HERE/path[1:]).read_bytes(),'text/javascript; charset=utf-8')
            if path in ('/api/product/create','/api/product/history','/api/product/status'):
                from . import product
                if method=='GET' and path=='/api/product/status':return self.reply(200,product.capabilities(self.server))
                if method=='POST' and path!='/api/product/status':return self.reply(200,(product.create if path.endswith('/create') else product.history)(self.server,self.body()))
                raise UIError('method','Unsupported product method',405)
            if method=='GET' and path=='/media.mjs':return self.reply(200,(HERE/'media.mjs').read_bytes(),'text/javascript; charset=utf-8')
            if method=='GET' and path=='/api/media':return self.reply(200,self.server.media.listing())
            if method=='GET' and path.startswith('/api/media/download/'):
                import re
                match=re.fullmatch(r'/api/media/download/([0-9a-f]{32})/([0-9a-f]{32})/(draft\.(?:svg|png))',path)
                if not match:raise UIError('media-path','Fixed media export identity required.')
                identity,export,name=match.groups();w=self.server.media.get(identity);w.scene(export_svg=True)
                from studio_png_sandbox.controller import safe
                payload=read(safe(w.root/'exports'/export/name),8*1024*1024)
                return self.reply(200,payload,'image/svg+xml' if name.endswith('.svg') else 'image/png')
            if method=='POST' and path.startswith('/api/media/'):
                routes={'/api/media/recovery':'recovery','/api/media/recover':'recover','/api/media/fork':'fork','/api/media/open':'open','/api/media/action':'action','/api/media/scene':'scene','/api/media/overlay':'overlay','/api/media/assets':'assets','/api/media/navigation':'navigation','/api/media/export/begin':'begin','/api/media/export/finish':'finish'}
                if path=='/api/media/export/cancel':self.server.media.pending=None;return self.reply(200,{'cancelled':True})
                if path not in routes:raise UIError('media-route','Unsupported media route.',404)
                import signal,threading
                from studio_png_sandbox.controller import Refused
                if threading.current_thread() is not threading.main_thread():raise UIError('media-runtime','Media route requires the qualified single-thread main server.',409)
                def expired(*_):raise TimeoutError('Complete media job deadline exceeded')
                previous=signal.signal(signal.SIGALRM,expired);signal.alarm(60)
                try:return self.reply(200,getattr(self.server.media,routes[path])(self.body()))
                except (Refused,ValueError,OSError,KeyError,TypeError) as exc:raise UIError('media-refused',str(exc)[:1024],409) from exc
                finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
            if method=='GET' and path in ASSETS:
                name,kind=ASSETS[path];return self.reply(200,(HERE/name).read_bytes(),kind)
            if method=='POST' and path in {'/api/brands/backup','/api/brands/restore-preview','/api/brands/restore'}:
                from .brands import Store,ROOT as BRAND_ROOT
                from .brand_portability import save_backup,preview,restore,upload
                library=Store(getattr(self.server,'brand_root',BRAND_ROOT));value=self.body()
                if path=='/api/brands/backup':exact(value,set());result=save_backup(library)
                elif path=='/api/brands/restore-preview':exact(value,{'data_base64'});result=preview(library,upload(value['data_base64']))
                else:
                    exact(value,{'data_base64','expected_destination','expected_package','acknowledge'})
                    result=restore(library,upload(value['data_base64']),value['expected_destination'],value['expected_package'],value['acknowledge'])
                return self.reply(200,result)
            if (method=='GET' and path=='/api/brands') or (method=='POST' and path in {'/api/brands/action','/api/brands/asset'}):
                try:from .brands import Store,ROOT as BRAND_ROOT
                except ImportError:raise UIError('brand-unavailable','Installed Python lacks SQLite support. Brand Studio unavailable; manual editing remains independent.',503)
                library=Store(getattr(self.server,'brand_root',BRAND_ROOT))
                if method=='GET':return self.reply(200,library.list())
                value=self.body()
                if type(value)!=dict or (path=='/api/brands/asset')!=(value.get('action')=='register_asset'):raise UIError('brand-contract','Use the fixed bounded action route.')
                return self.reply(200,library.command(value))
            if (method=='GET' and path=='/api/hybrid/status') or (method=='POST' and path in {'/api/hybrid/start','/api/hybrid/cancel','/api/hybrid/select'}):
                from .brands import Store,ROOT as BRAND_ROOT
                self.server.studio.brand_library=Store(getattr(self.server,'brand_root',BRAND_ROOT))
                jobs=self.server.hybrid
                if method=='GET':return self.reply(200,jobs.status())
                value=self.body()
                action={'/api/hybrid/start':jobs.start,'/api/hybrid/cancel':jobs.cancel,'/api/hybrid/select':jobs.select}[path]
                return self.reply(200,action(value))
            if method=='POST' and path in {'/api/director/generate','/api/director/select'}:
                from .director import generate,select
                s=self.server.studio
                if hasattr(self.server,'brand_root'):
                    from .brands import Store
                    s.brand_library=Store(self.server.brand_root)
                return self.reply(200,(generate if path.endswith('/generate') else select)(s,self.body()))
            if method=='GET' and path=='/api/workflow/brands':
                from .binding_workflow import eligible_versions
                if hasattr(self.server,'brand_root'):
                    from .brands import Store
                    self.server.studio.brand_library=Store(self.server.brand_root)
                return self.reply(200,eligible_versions(self.server.studio))
            if method=='POST' and path in {'/api/workflow/create','/api/workflow/preview','/api/workflow/change','/api/workflow/recovery'}:
                from . import binding_workflow as workflow
                value=self.body();s=self.server.studio
                if hasattr(self.server,'brand_root'):
                    from .brands import Store
                    s.brand_library=Store(self.server.brand_root)
                with s.manual.lock:
                    if path=='/api/workflow/create':result={'project':workflow.create(s,value)}
                    elif path=='/api/workflow/preview':
                        impact,h,_,_=workflow.proposal(s,value);result={'impact':impact,'impact_hash':h}
                    elif path=='/api/workflow/change':result={'project':workflow.change(s,value)}
                    else:
                        exact(value,{'project_id'});result={'candidates':s.pairs.candidates(value['project_id'])}
                return self.reply(200,result)
            if method=='GET' and path=='/api/sessions':
                from .home import catalogue
                from .session import marker
                return self.reply(200,{'current_session_id':marker(self.server.studio.root)['manual_id'],'sessions':catalogue()})
            if method=='POST' and path=='/api/session/switch':
                from .home import switch
                if getattr(self.server,'_hybrid',None) and self.server._hybrid.active:raise UIError('ai-busy','Cancel generation and wait for confirmed stop before switching sessions.',409)
                result=switch(self.server,self.body())
                media=getattr(self.server,'_media',None)
                if media and media.studio is not self.server.studio:media.close();self.server._media=None
                return self.reply(200,result)
            if method=='GET' and path=='/api/navigation':return self.reply(200,self.server.studio.navigation())
            if method=='GET' and path=='/api/fonts':
                s=self.server.studio
                return self.reply(200,{'fonts':s.fonts.public() if s.fonts else None,'error':s.font_error})
            if method=='POST' and path in {'/api/scene','/api/export/begin','/api/export/finish','/api/export/cancel','/api/browser-evidence'}:
                request=self.body();s=self.server.studio
                if path=='/api/scene':
                    exact(request,{'project_id','expected_revision'});result=s.scene(request['project_id'],request['expected_revision'])
                elif path=='/api/export/begin':
                    import time
                    pending=getattr(getattr(self.server,'_media',None),'pending',None)
                    if pending and time.monotonic()-pending['started']<=15:raise UIError('busy','One media export in flight.',409)
                    result=s.begin(request)
                elif path=='/api/export/finish':result=s.finish(request)
                elif path=='/api/export/cancel':exact(request,set());s.exports.cancel();result={'cancelled':True}
                else:
                    exact(request,{'results'})
                    if type(request['results'])!=dict:raise UIError('evidence','Object required.')
                    import secrets
                    if len(list(s.root.glob('browser-evidence-*.json')))>=20:raise UIError('limit','Browser evidence count exhausted.')
                    target=s.root/('browser-evidence-'+secrets.token_hex(8)+'.json')
                    with target.open('x',encoding='utf-8') as stream:json.dump(request,stream,ensure_ascii=False,indent=2)
                    result={'evidence':str(target)}
                return self.reply(200,result)
            return super().dispatch(method)
        except UIError as exc:self.reply(exc.status,{'error':exc.code,'detail':exc.detail})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:self.reply(500,{'error':'internal','detail':'Request failed; no automatic retry.'})
