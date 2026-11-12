"""M6 step 3: M5 poster editing, Brand Library and deterministic Creative Director behind the M6 FastAPI server.

The M5 code in ../m5 is called as a library, unchanged. Its own HTTP server (studio_manual_ui / visual_poster_studio
server.py) is NOT used; this module re-creates its request rules:
  - one owner: a single VisualStudio instance, every call serialized by one lock (Codex handoff, PYTHON_INTERFACES.md);
  - strict bodies: one Content-Length, exactly application/json, M5's own JSON decoder, the same size limits per route;
  - local only: Host must be 127.0.0.1/localhost; a browser Origin, when sent, must be a loopback origin
    (blocks other websites and DNS rebinding; JSON bodies already force a CORS preflight that is never granted);
  - errors: M5's UIError keeps its code/status; anything else becomes a generic 500 (no private text in logs).
Storage: M5 derives its root from its own folder, so sessions and the Brand Library live in m5/.runtime/studio-ui/
(M6 data, never Codex's). IDEAFRAME_M6_SESSION / IDEAFRAME_M6_BRANDS name other folders there (tests only).
Not exposed: session switching (M5 home.switch is bound to its own server) and browser test evidence.
AI inference is not wired: Codex rated M5 AI integration NO-GO; the Director here is deterministic."""
import os, sys, json, threading
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

M5 = Path(__file__).resolve().parents[1] / "m5"
if str(M5) not in sys.path: sys.path.insert(0, str(M5))
sys.dont_write_bytecode = True
from studio_manual_ui.service import RUNTIME, UIError, decode, exact, project_id   # noqa: E402

SESSION = RUNTIME / os.environ.get("IDEAFRAME_M6_SESSION", "m6-studio")
BRANDS = os.environ.get("IDEAFRAME_M6_BRANDS")          # None = M5's default Brand Library folder (brand-library)
LINKS = RUNTIME / os.environ.get("IDEAFRAME_M6_LINKS", "m6-content-links")       # step 6: approved words placed on posters
WORKSPACE = Path(__file__).resolve().parents[1]
REELS = Path(os.environ.get("IDEAFRAME_M6_REELS") or WORKSPACE / "projects")      # M4 reel projects (tests point elsewhere)
ENGINE = str(WORKSPACE / "engine")

DEFAULT_LIMIT = 64 * 1024                                # studio_manual_ui/server.py MAX_REQUEST
LIMITS = {"/api/creative/export/finish": 12 * 1024 * 1024, "/api/brands/asset": 12 * 1024 * 1024,
          "/api/brands/restore-preview": 100 * 1024 * 1024, "/api/brands/restore": 100 * 1024 * 1024}
LOOPBACK = {"127.0.0.1", "localhost", "::1"}

_lock = threading.Lock()          # one owner: every M5 call goes through here
_studio = None


def _store():
    from visual_poster_studio.brands import Store, ROOT as BRAND_ROOT
    return Store(RUNTIME / BRANDS if BRANDS else BRAND_ROOT)


def _owner():
    """Open (or resume) M6's single Visual session on first use, so the reel app starts even if M5 cannot."""
    global _studio
    if _studio is None:
        from visual_poster_studio.service import VisualStudio
        resume = (SESSION / "visual-session.json").is_file()
        _studio = VisualStudio(SESSION, resume=resume)
        if BRANDS: _studio.brand_library = _store()
    return _studio


def close():
    global _studio
    with _lock:
        if _studio is not None: _studio.close(); _studio = None


router = APIRouter(on_shutdown=[close])


def _guard(request: Request):
    host = urlsplit("//" + request.headers.get("host", "")).hostname
    if host not in LOOPBACK: raise UIError("host", "Host refused.", 403)
    origins = request.headers.getlist("origin")
    if len(origins) > 1: raise UIError("origin", "Origin refused.", 403)
    if origins:
        o = urlsplit(origins[0])
        if o.scheme != "http" or o.hostname not in LOOPBACK: raise UIError("origin", "Origin refused.", 403)
    if request.headers.get("transfer-encoding") or request.headers.get("content-encoding"):
        raise UIError("encoding", "Transfer/content encodings are unsupported.")
    if request.url.query: raise UIError("path", "Only fixed local routes are supported.")


async def _body(request: Request):
    sizes = request.headers.getlist("content-length")
    if len(sizes) != 1 or not sizes[0].isascii() or not sizes[0].isdigit(): raise UIError("length", "A single Content-Length is required.", 411)
    limit = LIMITS.get(request.url.path, DEFAULT_LIMIT)
    if len(sizes[0]) > 10 or not 0 < int(sizes[0]) <= limit: raise UIError("limit", "Request body limit exceeded.", 413)
    if request.headers.getlist("content-type") != ["application/json"]: raise UIError("content-type", "JSON content required.", 415)
    raw = await request.body()
    if len(raw) != int(sizes[0]): raise UIError("json", "Incomplete request body.")
    return decode(raw)                                    # M5's strict decoder (duplicate keys, NaN ... refused)


def _call(fn):
    with _lock: return fn(_owner())


def _reply(status, value):
    return JSONResponse(value, status_code=status, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


async def _handle(request: Request, fn, status=200, body=True):
    try:
        _guard(request)
        value = await _body(request) if body else None
        result = await run_in_threadpool(_call, (lambda s: fn(s, value)) if body else fn)
        return _reply(status, result)
    except UIError as exc:
        return _reply(exc.status, {"error": exc.code, "detail": exc.detail})
    except Exception as exc:                              # never echo private text; the type is enough to debug
        print(f"creative: {request.url.path} failed: {type(exc).__name__}", file=sys.stderr, flush=True)
        return _reply(500, {"error": "internal", "detail": "Request failed; no automatic retry or repair."})


# ---------------------------------------------------------------- poster projects (VisualStudio)
@router.get("/api/creative/session")
async def session(request: Request):
    return await _handle(request, lambda s: {"analysis": s.analysis()}, body=False)

@router.get("/api/creative/projects")
async def projects(request: Request):
    return await _handle(request, lambda s: {"projects": s.list_projects()}, body=False)

@router.get("/api/creative/projects/{identity}")
async def project(identity: str, request: Request):
    return await _handle(request, lambda s: {"project": s.view(project_id(identity))}, body=False)

@router.post("/api/creative/projects")
async def create(request: Request):
    return await _handle(request, lambda s, v: {"project": s.create(v)}, status=201)

@router.post("/api/creative/action")
async def action(request: Request):
    return await _handle(request, lambda s, v: {"project": s.action(v)})

def _reopen(s, v):
    exact(v, {"project_id", "expected_revision"}); return {"project": s.reopen(v["project_id"], v["expected_revision"])}
@router.post("/api/creative/reopen")
async def reopen(request: Request): return await _handle(request, _reopen)

@router.get("/api/creative/navigation")
async def navigation(request: Request):
    return await _handle(request, lambda s: s.navigation(), body=False)

@router.get("/api/creative/fonts")
async def fonts(request: Request):
    return await _handle(request, lambda s: {"fonts": s.fonts.public() if s.fonts else None, "error": s.font_error}, body=False)

def _scene(s, v):
    exact(v, {"project_id", "expected_revision"}); return s.scene(v["project_id"], v["expected_revision"])
@router.post("/api/creative/scene")
async def scene(request: Request): return await _handle(request, _scene)

def _qa(s, v):
    """Poster QA (app/poster_qa.py) on the current working document, at the revision the client is looking at."""
    import poster_qa
    exact(v, {"project_id", "expected_revision"})
    identity = project_id(v["project_id"]); s._ready(identity)
    doc = s.manual.document(identity)
    if type(v["expected_revision"]) is not int or v["expected_revision"] != doc["revision"]: raise UIError("conflict", "Stale QA revision.", 409)
    cover = {k: f["coverage"] for k, f in s.fonts.faces.items()} if s.fonts else None
    result = poster_qa.check(doc, cover)
    for row in _link_status(doc):                          # step 6: approved words must stay exactly as approved
        result["checks"].append(dict(name="approved_text", level="error", passed=row["ok"], element_id=row["element_id"],
                                     detail=f"{row['item_id']} from {row['reel']}: {row['detail']}"))
        if not row["ok"]: result["errors"] += 1; result["passed"] = False
    return dict(result, revision=doc["revision"], fonts_checked=cover is not None)
@router.post("/api/creative/qa")
async def qa(request: Request): return await _handle(request, _qa)

@router.post("/api/creative/export/begin")
async def export_begin(request: Request): return await _handle(request, lambda s, v: s.begin(v))

@router.post("/api/creative/export/finish")
async def export_finish(request: Request): return await _handle(request, lambda s, v: s.finish(v))

def _cancel(s, v):
    exact(v, set()); s.exports.cancel(); return {"cancelled": True}
@router.post("/api/creative/export/cancel")
async def export_cancel(request: Request): return await _handle(request, _cancel)


# ---------------------------------------------------------------- deterministic Creative Director + brand/brief workflow
def _director(name):
    def run(s, v):
        from visual_poster_studio import director
        return getattr(director, name)(s, v)
    return run
@router.post("/api/creative/director/generate")
async def director_generate(request: Request): return await _handle(request, _director("generate"))

@router.post("/api/creative/director/select")
async def director_select(request: Request): return await _handle(request, _director("select"))

def _eligible(s):
    from visual_poster_studio.binding_workflow import eligible_versions
    return eligible_versions(s)
@router.get("/api/creative/workflow/brands")
async def workflow_brands(request: Request): return await _handle(request, _eligible, body=False)

def _workflow(kind):
    def run(s, v):
        from visual_poster_studio import binding_workflow as workflow
        with s.manual.lock:
            if kind == "create": return {"project": workflow.create(s, v)}
            if kind == "preview":
                impact, h, _, _ = workflow.proposal(s, v); return {"impact": impact, "impact_hash": h}
            if kind == "change": return {"project": workflow.change(s, v)}
            exact(v, {"project_id"}); return {"candidates": s.pairs.candidates(v["project_id"])}
    return run
def _workflow_route(kind):
    async def endpoint(request: Request): return await _handle(request, _workflow(kind))
    endpoint.__name__ = f"workflow_{kind}"
    return endpoint
for _kind in ("create", "preview", "change", "recovery"):
    router.add_api_route(f"/api/creative/workflow/{_kind}", _workflow_route(_kind), methods=["POST"])


# ---------------------------------------------------------------- Brand Library (metadata only; asset bytes are never decoded)
def _library(fn):
    return lambda s, v=None: fn(getattr(s, "brand_library", None) or _store(), v)

@router.get("/api/brands")
async def brands(request: Request):
    return await _handle(request, lambda s: _library(lambda lib, _: lib.list())(s), body=False)

def _brand_command(asset_route):
    def run(lib, v):
        if type(v) != dict or asset_route != (v.get("action") == "register_asset"):
            raise UIError("brand-contract", "Use the fixed bounded action route.")
        return lib.command(v)
    return _library(run)
@router.post("/api/brands/action")
async def brands_action(request: Request): return await _handle(request, _brand_command(False))

@router.post("/api/brands/asset")
async def brands_asset(request: Request): return await _handle(request, _brand_command(True))

def _portability(kind):
    def run(lib, v):
        from visual_poster_studio.brand_portability import save_backup, preview, restore, upload
        if kind == "backup": exact(v, set()); return save_backup(lib)
        if kind == "preview": exact(v, {"data_base64"}); return preview(lib, upload(v["data_base64"]))
        exact(v, {"data_base64", "expected_destination", "expected_package", "acknowledge"})
        return restore(lib, upload(v["data_base64"]), v["expected_destination"], v["expected_package"], v["acknowledge"])
    return _library(run)
@router.post("/api/brands/backup")
async def brands_backup(request: Request): return await _handle(request, _portability("backup"))

@router.post("/api/brands/restore-preview")
async def brands_restore_preview(request: Request): return await _handle(request, _portability("preview"))

@router.post("/api/brands/restore")
async def brands_restore(request: Request): return await _handle(request, _portability("restore"))


# ---------------------------------------------------------------- step 6: approved reel words on posters
def _reel_dir(name):
    if not isinstance(name, str) or not name or "/" in name or "\\" in name or name.startswith("."): raise UIError("reel", "Unknown reel project.", 404)
    d = REELS / name
    if not (d / "project.json").is_file(): raise UIError("reel", "Unknown reel project.", 404)
    return d


def _derive(name):
    import approved_content as A
    try: return A.derive(_reel_dir(name), ENGINE)
    except A.ApprovalError as e: raise UIError(e.code.lower().replace("_", "-"), str(e), 409)


def _link_status(doc):
    """Every recorded link on this poster whose layer still exists, checked against a fresh derivation."""
    import approved_content as A
    from content_links import Links
    text = {c["id"]: c["text"] for c in doc["content"]}; layers = {e["id"]: e for e in doc["elements"]}
    out, cache = [], {}
    for r in Links(LINKS).get(doc["id"]):
        e = layers.get(r["element_id"])
        if not e or e.get("content_id") != r["content_id"]: continue
        if r["reel"] not in cache:
            try: cache[r["reel"]] = A.derive(_reel_dir(r["reel"]), ENGINE)
            except (A.ApprovalError, UIError) as exc: cache[r["reel"]] = exc
        ok, detail = A.item_status(cache[r["reel"]], r["item_id"], r["item_sha256"], text.get(r["content_id"]))
        out.append(dict(r, ok=ok, detail=detail))
    return out


def _reels(s):
    import approved_content as A
    rows = []
    for d in sorted(p for p in REELS.iterdir() if (p / "project.json").is_file()):
        try:
            doc = A.derive(d, ENGINE)
            rows.append(dict(project=d.name, ok=True, approvals=[a["type"] for a in doc["approvals"]], items=len(doc["items"]), fingerprint=doc["fingerprint"]))
        except A.ApprovalError as e: rows.append(dict(project=d.name, ok=False, code=e.code, detail=str(e)))
    return {"reels": rows}
@router.get("/api/creative/approved/reels")
async def approved_reels(request: Request): return await _handle(request, _reels, body=False)

@router.get("/api/creative/approved/reels/{name}")
async def approved_reel(name: str, request: Request): return await _handle(request, lambda s: _derive(name), body=False)

def _links(identity):
    def run(s):
        identity_ = project_id(identity); s._ready(identity_)
        return {"links": _link_status(s.manual.document(identity_))}
    return run
@router.get("/api/creative/approved/links/{identity}")
async def approved_links(identity: str, request: Request): return await _handle(request, _links(identity), body=False)

def _insert(s, v):
    """Place one approved line on a poster as a new text layer, exactly as approved, and record the link."""
    from content_links import Links
    exact(v, {"project_id", "expected_revision", "reel", "item_id", "expected_fingerprint"})
    doc = _derive(v["reel"])
    if v["expected_fingerprint"] != doc["fingerprint"]: raise UIError("stale-approval", "The reel's approved content changed; reload it and choose again.", 409)
    item = next((x for x in doc["items"] if x["id"] == v["item_id"]), None)
    if item is None: raise UIError("item", "Unknown approved line.", 404)
    with s.manual.lock:
        before = s.view(project_id(v["project_id"]))
        if before["revision"] != v["expected_revision"]: raise UIError("conflict", "Stale poster revision.", 409)
        added = s.action({"project_id": before["project_id"], "expected_revision": before["revision"], "action": "add_text", "language": item["language"]})
        new = [e for e in added["elements"] if e["id"] not in {x["id"] for x in before["elements"]}]
        if len(new) != 1: raise UIError("insert", "Could not identify the new text layer.", 500)
        try:
            done = s.action({"project_id": added["project_id"], "expected_revision": added["revision"], "action": "edit_text", "element_id": new[0]["id"], "text": item["text"]})
        except Exception:
            s.action({"project_id": added["project_id"], "expected_revision": added["revision"], "action": "undo"}); raise
        element = next(e for e in done["elements"] if e["id"] == new[0]["id"])
        others = [e for e in done["elements"] if e["id"] != element["id"] and e["type"] == "text"]
        below = max((e["y"] + e["height"] for e in others), default=None)        # place it under existing text, not on top of it
        if below is not None and below + 24 + element["height"] <= done["view"]["height"] - 64:
            done = s.action({"project_id": done["project_id"], "expected_revision": done["revision"], "action": "move", "element_id": element["id"], "x": element["x"], "y": below + 24})
            element = next(e for e in done["elements"] if e["id"] == element["id"])
        content = next(c for c in done["content"] if c["id"] == element["content_id"])
        if content["text"] != item["text"]: raise UIError("insert", "The poster did not keep the approved text exactly.", 500)
        link = Links(LINKS).add(done["project_id"], dict(element_id=element["id"], content_id=content["id"], reel=v["reel"], item_id=item["id"], kind=item["kind"],
                                                          item_sha256=item["sha256"], source_fingerprint=doc["fingerprint"], approvals=[a["type"] for a in doc["approvals"]]))
        return {"project": done, "link": link}
@router.post("/api/creative/approved/insert")
async def approved_insert(request: Request): return await _handle(request, _insert)


# ---------------------------------------------------------------- step 7: poster -> ordinary M4 slides reel (script left unapproved)
def _to_reel(s, v):
    import poster_to_reel as T
    exact(v, {"project_id", "expected_revision", "brand", "platform", "style", "slug"})
    identity = project_id(v["project_id"]); s._ready(identity)
    with s.manual.lock:
        doc = s.manual.document(identity)
        if v["expected_revision"] != doc["revision"]: raise UIError("conflict", "Stale poster revision.", 409)
        if s.view(identity)["dirty"]: raise UIError("save-first", "Save the poster first.", 409)
        try: return T.convert(s, identity, v["brand"], v["platform"], v["style"], v["slug"], links=_link_status(doc))
        except T.ConvertError as e: raise UIError(e.code, str(e), e.status)
@router.post("/api/creative/to-reel")
async def to_reel(request: Request): return await _handle(request, _to_reel)
