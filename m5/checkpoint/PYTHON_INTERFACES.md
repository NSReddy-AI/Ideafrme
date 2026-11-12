# Python interface inventory
Exact signatures, source lines, request key sets, explicit raise expressions and return expressions are in PYTHON_INTERFACES.json. Most source APIs have no type annotations; types below describe inspected behavior, not a newly frozen typing contract. Internal helpers remain provisional. No HTTP server is started for these APIs.

## visual_poster_studio/service.py
VisualStudio(root: Path, resume: bool=False) creates or validates an owned session, opens a lifetime nonblocking OS writer lock through Studio, scans journal/pair/export state and loads pinned Fonts. close()->None releases it. status()/analysis()/navigation()->dict; list_projects()->list[dict]; view()/create()/action()/reopen()->dict are headless application facades. identity is a canonical nonzero UUID string; revision is int. create request is exactly {name:str,text:str,language:en|te}. action dispatches strict named requests: common project_id,expected_revision,action plus edit_text(element_id,text), move(element_id,x,y), font_size(element_id,font_size), color(element_id,color), add_text(language), add_shape(shape), remove(element_id), undo/redo/save; reorder(view_id,ordered_element_ids,acknowledge_upgrade) and geometry(view_id,targets,acknowledge_upgrade). scene(identity,revision)->scene dict. begin({project_id,expected_revision})->token/scene dict; finish({token,revision,png,qa})->directory/manifest dict. context_checkpoint()->digest str is a recovery helper with persistent side effects, not a public migration API. UIError(ValueError) carries code/detail/status; OSError and core validation errors can propagate in lower paths. Session/project/export filesystem reads/writes occur, as do read-locking Brand Library checks when bound. manual.RLock protects mutations but not every public read/catalogue operation; integrations should serialize all calls on one owner and always close. This is a tested headless application API with implementation-coupled view DTOs, not a frozen SDK. No direct Qt/React assumptions.

- `VisualStudio.__init__(self, root, *, resume=False)` (line 12)
- `VisualStudio.close(self)` (line 43)
- `VisualStudio.status(self)` (line 44)
- `VisualStudio.analysis(self)` (line 47)
- `VisualStudio.list_projects(self)` (line 53)
- `VisualStudio.view(self, identity)` (line 66)
- `VisualStudio.create(self, request)` (line 68)
- `VisualStudio.action(self, request)` (line 71)
- `VisualStudio.context_checkpoint(self, identity, doc)` (line 146)
- `VisualStudio.reopen(self, identity, expected_revision=None)` (line 150)
- `VisualStudio.scene(self, identity, revision)` (line 158)
- `VisualStudio.begin(self, request)` (line 166)
- `VisualStudio.navigation(self)` (line 170)
- `VisualStudio.finish(self, request)` (line 187)

## visual_poster_studio/brands.py
Store(root:Path=ROOT) is a true headless separate metadata library. list()->dict gives brands/assets/initialized/creative_use_enabled; command(request:dict)->dict handles register_asset, rights, save, approve. Exact command keys are captured in JSON. register_asset receives bounded data_base64, name, kind, provenance and structured rights; no decoding of the opaque asset occurs. save receives brand_id|null, expected_head|null, payload; approve adds reviewer/acknowledge; rights uses asset_id/expected_rights/rights. transaction(create=False) yields sqlite3.Connection and commits/rolls back with exclusive nonblocking flock; do not nest it or share connections across threads. get/put/asset/eligibility/describe accept a live connection and dict/string values: these are lower-level transaction helpers, not independently atomic APIs. put returns hash str, get/asset return dict; eligibility returns eligible/reason/rights_hash; describe returns record+current status. canonical(dict)->bytes, now()->UTC str, string/identity/timestamp/payload/rights/validate_record return validated input, check()->None or raises UIError. Reads may create/open a lock file and SQLite transaction; an absent Store.list() is noncreating. sqlite3.Error maps to brand-storage UIError, filesystem errors may propagate. Store paths are configurable only underneath package WORKSPACE/.runtime/studio-ui; no root CLI switch. Status/rights are trusted-local assertions, not external authentication. Store command interface is usable through an adapter; persistence v1 is explicitly versioned, service API not separately frozen.

- `check(ok, message)` (line 13)
- `string(value, maximum=256, empty=False)` (line 15)
- `identity(value)` (line 20)
- `canonical(v)` (line 25)
- `now()` (line 26)
- `timestamp(v)` (line 27)
- `payload(v)` (line 33)
- `rights(v)` (line 47)
- `validate_record(v)` (line 57)
- `Store.__init__(self, root=ROOT)` (line 81)
- `Store.transaction(self, create=False)` (line 84)
- `Store.put(self, c, v)` (line 117)
- `Store.get(self, c, h)` (line 120)
- `Store.asset(self, c, i)` (line 125)
- `Store.eligibility(self, c, i, scope, destination)` (line 127)
- `Store.describe(self, c, h)` (line 133)
- `Store.list(self)` (line 138)
- `Store.command(self, request)` (line 146)

## visual_poster_studio/project_bindings.py
brief(value:dict)->same dict validates exact fields; validate(value,session_id:str,identity:str)->same dict validates binding. sha(bytes)->hex str; valid_commit(str)->regex Match|False|None (truthiness predicate, not guaranteed bool); check()->None or UIError. Pairs(session:Path,journal:Journal) requires an initialized Visual marker and caller-held session lock. directory()->Path; owns()->bool; usage()->int; head()->dict|None; pair()/chain()->dict containing document,binding,manifest,hash,origin,commit; load()->document dict updates in-memory heads/bindings; scan(manual)->None records per-project errors; compatible()->None validates; install()->None mutates manual caches; new()->binding dict; commit()->HEAD dict; candidates()->list[dict]. commit takes a full creative dict, binding dict, expected_head dict|null, publish bool and optional origin bytes. It performs exclusive immutable writes, CAS and pointer publication or records uncertainty; no HTTP dependence. Do not use it independently of journal budget, writer ownership and manual.RLock. This is a low-level storage contract implementation, not a standalone public repository interface. UIError plus OSError/core errors; some scan/candidate failures are converted into explicit invalid/error states. No external brand assets loaded.

- `check(ok, message)` (line 9)
- `sha(raw)` (line 11)
- `brief(value)` (line 12)
- `validate(value, session_id, identity)` (line 20)
- `valid_commit(value)` (line 31)
- `Pairs.__init__(self, session, journal)` (line 34)
- `Pairs.usage(self)` (line 36)
- `Pairs.directory(self, identity)` (line 43)
- `Pairs.owns(self, identity)` (line 44)
- `Pairs.head(self, identity)` (line 45)
- `Pairs.pair(self, identity, commit)` (line 49)
- `Pairs.chain(self, identity, commit)` (line 63)
- `Pairs.load(self, identity)` (line 75)
- `Pairs.scan(self, manual)` (line 78)
- `Pairs.compatible(self, before, after)` (line 84)
- `Pairs.install(self, manual, identity, doc)` (line 88)
- `Pairs.new(self, identity, pin, fields, origin=None)` (line 90)
- `Pairs.commit(self, identity, doc, binding, expected_head, publish=True, origin_raw=None)` (line 92)
- `Pairs.candidates(self, identity)` (line 126)

## studio_manual_ui/service.py
Studio(root:Path,resume=False,analysis_provider:Callable|None=None) is headless, acquiring writer flock for lifetime. create/view/document/list_projects/reopen/action/analysis expose dict/list/deep-copy document results. document()->dict; close()->None. Same legacy action request keys as above, excluding Visual-only reorder, geometry and remove. analysis_provider is optional status input; real media is forcibly disabled. Helpers exact()->None; text/color/project_id()->str; integer()->int; encoded()->bytes; pairs()->dict; decode(bytes)->JSON value; safe(Path)->Path; read(Path,max)->bytes; manual_subset(dict)->None. UIError carries code/detail/status; OSError possible. This service permits only the manual subset and requires package-local runtime. Do not mutate _working/_digests/_saved from an external integration. Original UI state handling is accepted legacy behavior; Visual wrapper is the preferred integration entry.

- `UIError.__init__(self, code, detail, status=400)` (line 21)
- `exact(value, keys)` (line 26)
- `text(value, maximum=10000)` (line 31)
- `integer(value, minimum, maximum)` (line 39)
- `color(value)` (line 45)
- `project_id(value)` (line 51)
- `encoded(value)` (line 59)
- `pairs(items)` (line 64)
- `decode(raw)` (line 72)
- `safe(path)` (line 81)
- `read(path, maximum)` (line 94)
- `manual_subset(document)` (line 104)
- `Studio.__init__(self, root, *, resume=False, analysis_provider=None)` (line 138)
- `Studio.close(self)` (line 163)
- `Studio.analysis(self)` (line 174)
- `Studio.document(self, identity)` (line 191)
- `Studio.view(self, identity)` (line 196)
- `Studio.create(self, request)` (line 211)
- `Studio.list_projects(self)` (line 232)
- `Studio.reopen(self, identity, expected_revision=None)` (line 242)
- `Studio.action(self, request)` (line 261)

## visual_poster_studio/binding_workflow.py
True headless orchestration on a VisualStudio object, NOT a Handler or self.server.studio. library(studio)->Store uses optional studio.brand_library else default. pin(studio,hash|null)->approved pin dict|null revalidates live metadata/rights/hard rules; eligible_versions()->dict; binding_state()->dict|null. create(studio,{name,text,language,brief,brand_hash,acknowledge})->view dict. proposal(studio,{project_id,expected_revision,expected_binding,expected_head,brand_hash,brief})->(impact:dict,impact_hash:str,target:dict|null,brief:dict). change(studio,{proposal,impact_hash,acknowledge})->view dict. save()->view dict, mark_saved()->None; bound_scene(studio,identity,scene)->scene dict. Caller must hold studio.manual.lock around create/proposal/change; server does so explicitly, functions do not all acquire it themselves. Reads may open Brand Library transaction; changes publish paired state and invalidate exports. UIError/OSError propagate; binding_state converts eligibility errors to status. These functions depend on concrete Visual internals; use a future narrow application adapter, not replication of pair writes.

- `library(studio)` (line 9)
- `pin(studio, value)` (line 10)
- `eligible_versions(studio)` (line 23)
- `binding_state(studio, identity)` (line 36)
- `mark_saved(studio, identity, doc)` (line 45)
- `save(studio, request)` (line 46)
- `create(studio, request)` (line 50)
- `proposal(studio, request)` (line 58)
- `change(studio, request)` (line 68)
- `bound_scene(studio, identity, scene)` (line 74)

## visual_poster_studio/scene.py
build_scene(doc:dict,fonts:Fonts)->dict with project_id,svg:str,svg_sha256,source_fingerprint,revision,profile,boxes,fonts. Pure mapping after manual_subset validation; no file/browser/server effects. Does not itself call full core.validate; direct callers must do so first. UIError on unsupported features, bounds, glyph or size. Use VisualStudio.scene for live rights/context identity; calling build_scene alone bypasses bound-context policy. Stable rendering mapping at visual-poster-draft@1, not general media renderer.

- `build_scene(doc, fonts)` (line 10)

## visual_poster_studio/fonts.py
Fonts() reads two hash-pinned local sfnt font files/notices, builds coverage/data URIs. css()->str; public()->dict; runs(text:str)->list[[lang,str]] preserving text; coverage(bytes)->frozenset[int]. coverage parses only qualified bounded pinned assets: not an untrusted font API. Missing/changed files or glyphs raise UIError; no fallback. Browser supplies shaping and actual ink measurement. Headless metadata/mapping available, no headless PNG shaping. This is a fixed font-profile implementation; arbitrary font loading unsupported.

- `coverage(data)` (line 13)
- `Fonts.__init__(self)` (line 40)
- `Fonts.css(self)` (line 53)
- `Fonts.public(self)` (line 55)
- `Fonts.runs(self, text)` (line 57)

## visual_poster_studio/exports.py
Exports(sessionroot:Path,resume=False) creates/validates exports dir; audit()->status dict reads retained files; cancel()->None; begin(identity:str,scene:dict)->{token,expires_seconds,scene}; finish(token:str,revision:int,png:base64str|null,qa:dict,current_revision:int)->{directory:str,manifest:dict}. Strict QA keys fonts_loaded,overflow,parity,embedded_fonts. Single mutable pending handshake requires external serialization. Writes exclusive draft artifacts, preserves partial evidence, no rendering/decoding. PNG validation is bounded signature/header/dimension plus browser-reported QA, not independent decoder or adversarial pixel proof. UIError/OSError on refusal/failure; caller through VisualStudio rechecks rights and stale context. Headless SVG retention works with valid QA; real PNG creation still needs a qualified browser, not this API.

- `Exports.__init__(self, root, *, resume=False)` (line 15)
- `Exports.audit(self)` (line 21)
- `Exports.cancel(self)` (line 55)
- `Exports.begin(self, identity, scene)` (line 56)
- `Exports.finish(self, token, revision, png, qa, current_revision)` (line 64)

## visual_poster_studio/director.py
generate(studio,request)->bundle dict; source(studio,request)->(document,binding); request exact keys project_id,expected_revision,expected_binding,expected_head,seed,acknowledge_brief. generate acquires manual.RLock and does not run a model. select(studio,{source,bundle_digest,concept_id,acknowledge_rules})->{project,bundle_digest,concept_id,approved:false}; acquires lock, regenerates/validates, writes immutable proposal receipt and a new paired editable project. retain()->None writes receipt with bounded count/bytes; document(identity,plan,binding)->creative dict is not storage publication. directions(binding,seed)->three plan dicts, palette()->tuple[str,str,bool], fitted()->(text,font_size), wrap()->str, luminance()->float, require()->None or UIError. Dependencies include current brief/pinned rights, core, scene and Fonts. No server required; internal Studio coupling and deterministic-only mode must remain explicit. No guarantee of arbitrary instruction/subjective brand understanding or originality certification. Tested deterministic headless workflow; operational AI adapters are separate NO-GO prototypes.

- `require(value, message)` (line 14)
- `source(studio, request)` (line 17)
- `wrap(text, columns)` (line 38)
- `fitted(text, width, height, preferred)` (line 47)
- `luminance(value)` (line 57)
- `palette(binding)` (line 60)
- `document(identity, plan, binding)` (line 67)
- `directions(binding, seed)` (line 79)
- `generate(studio, request)` (line 106)
- `retain(studio, bundle)` (line 121)
- `select(studio, request)` (line 133)

## HTTP-only boundaries
visual_poster_studio.server.Handler dispatch/body/guard/reply require BaseHTTPRequestHandler transport and self.server.studio, origin and CSRF state; they are not supported headless APIs. Server(studio,port) starts/binds loopback transport only when constructed. home.switch(server,request) mutates server.studio and server.csrf and therefore is server-bound. A future extraction should move only the validated session handover into a serialized application controller, with transport-owned CSRF rotation left outside. No extraction performed. Catalogue(parent) is callable without HTTP but marker validation still enforces runtime-root policy.
## Root configurability and integration caution
Session roots are constructor/CLI configurable only under the imported package RUNTIME. Brand Store accepts a root under the same tree; HTTP library routes use server.brand_root override, workflows use studio.brand_library. Integrations must configure both consistently; neither provides unrestricted external-root configuration. CLI lacks --brand-root. Frozen checkpoint is read-only and cannot be used as a writable application runtime: use a separately authorized working copy, not chmod or monkeypatch of the checkpoint. Python direct callers must supply the same locks, validation and live-rights checks as the existing server. A React client should use a validated transport adapter, never reach into filesystem storage.
