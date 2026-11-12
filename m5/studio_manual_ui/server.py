"""Loopback-only, same-origin HTTP adapter; static filenames and JSON actions only."""
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import TCPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit

from .service import Studio, UIError, decode, exact, project_id

MAX_REQUEST = 65536
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/styles.css": ("styles.css", "text/css; charset=utf-8")}


class Server(HTTPServer):
    allow_reuse_address = False

    def __init__(self, studio, port=0):
        if type(port) is not int or not 0 <= port <= 65535: raise UIError("port", "Invalid local port.")
        self.studio = studio
        self.csrf = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.host = f"127.0.0.1:{self.server_port}"

    def server_bind(self):
        TCPServer.server_bind(self)  # avoid reverse-DNS lookup on local startup
        self.server_name, self.server_port = "127.0.0.1", self.server_address[1]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # bounded request, no pipelining or indefinite keep-alive
    server_version = "ManualStudio"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(2)

    def log_message(self, *_): pass  # no raw URLs, tokens or private text in logs

    def reply(self, status, body, kind="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; font-src 'none'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def guard(self, mutation=False):
        hosts = self.headers.get_all("Host", [])
        origins = self.headers.get_all("Origin", [])
        if hosts != [self.server.host]: raise UIError("host", "Host refused.", 403)
        if len(origins) > 1 or (origins and origins != [self.server.origin]):
            raise UIError("origin", "Origin refused.", 403)
        if mutation:
            if origins != [self.server.origin]: raise UIError("origin", "Same-origin POST required.", 403)
            tokens = self.headers.get_all("X-CSRF-Token", [])
            if len(tokens) != 1 or not tokens[0].isascii() or not hmac.compare_digest(tokens[0], self.server.csrf):
                raise UIError("csrf", "CSRF token refused.", 403)
        if self.headers.get_all("Transfer-Encoding") or self.headers.get_all("Content-Encoding"):
            raise UIError("encoding", "Transfer/content encodings are unsupported.")
        split = urlsplit(self.path)
        if split.scheme or split.netloc or split.query or split.fragment or split.path != self.path:
            raise UIError("path", "Only fixed local routes are supported.")
        return split.path

    def body(self):
        sizes = self.headers.get_all("Content-Length", [])
        if len(sizes) != 1 or not sizes[0].isascii() or not sizes[0].isdigit():
            raise UIError("length", "A single Content-Length is required.", 411)
        if len(sizes[0]) > 6: raise UIError("limit", "Request body limit exceeded.", 413)
        size = int(sizes[0])
        if not 0 < size <= MAX_REQUEST: raise UIError("limit", "Request body limit exceeded.", 413)
        if self.headers.get_all("Content-Type", []) != ["application/json"]:
            raise UIError("content-type", "JSON content required.", 415)
        raw = self.rfile.read(size)
        if len(raw) != size: raise UIError("json", "Incomplete request body.")
        return decode(raw)

    def dispatch(self, method):
        try:
            path = self.guard(mutation=method == "POST")
            if method == "GET":
                if path in ASSETS:
                    name, kind = ASSETS[path]
                    return self.reply(200, Path(__file__).with_name(name).read_bytes(), kind)
                if path == "/api/session":
                    return self.reply(200, {"csrf": self.server.csrf, "analysis": self.server.studio.analysis()})
                if path == "/api/projects": return self.reply(200, {"projects": self.server.studio.list_projects()})
                if path.startswith("/api/project/"):
                    return self.reply(200, {"project": self.server.studio.view(project_id(path[len('/api/project/'):]))})
            elif method == "POST":
                request = self.body()
                if path == "/api/projects": result = self.server.studio.create(request)
                elif path == "/api/action": result = self.server.studio.action(request)
                elif path == "/api/reopen":
                    exact(request, {"project_id", "expected_revision"})
                    result = self.server.studio.reopen(request["project_id"], request["expected_revision"])
                else: raise UIError("route", "Unknown route.", 404)
                return self.reply(201 if path == "/api/projects" else 200, {"project": result})
            else: raise UIError("method", "Method not supported.", 405)
            raise UIError("route", "Unknown route.", 404)
        except UIError as exc:
            self.reply(exc.status, {"error": exc.code, "detail": exc.detail})
        except (BrokenPipeError, ConnectionResetError): pass
        except Exception:
            self.reply(500, {"error": "internal", "detail": "Request failed; no automatic retry or repair."})

    def do_GET(self): self.dispatch("GET")
    def do_POST(self): self.dispatch("POST")
    def do_OPTIONS(self): self.dispatch("OPTIONS")
    def do_HEAD(self): self.dispatch("HEAD")
    def do_PUT(self): self.dispatch("PUT")
    def do_DELETE(self): self.dispatch("DELETE")
    def do_PATCH(self): self.dispatch("PATCH")
    def do_TRACE(self): self.dispatch("TRACE")
