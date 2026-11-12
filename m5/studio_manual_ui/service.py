"""Manual creative@1 operations in owned runtime projects; accepted core stays unchanged."""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import uuid

import creative_core as core

WORKSPACE = Path(__file__).resolve().parents[1]
RUNTIME = WORKSPACE / ".runtime" / "studio-ui"
MAX_DOCUMENT = 8 * 1024 * 1024
MAX_ELEMENTS = 64


class UIError(ValueError):
    def __init__(self, code, detail, status=400):
        self.code, self.detail, self.status = code, detail, status
        super().__init__(detail)


def exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise UIError("request", "Missing or unsupported request fields.")


def text(value, maximum=10000):
    if type(value) is not str or not 0 < len(value) <= maximum or "\x00" in value:
        raise UIError("text", "Enter nonempty text within the supported length.")
    try: value.encode("utf-8")
    except UnicodeError as exc: raise UIError("text", "Invalid Unicode text.") from exc
    return value  # no trimming, normalization or spelling changes


def integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise UIError("number", "Number is outside the supported range.")
    return value


def color(value):
    if type(value) is not str or re.fullmatch(r"#[0-9a-fA-F]{6}", value) is None:
        raise UIError("color", "Use a six-digit hexadecimal color.")
    return value


def project_id(value):
    try:
        if type(value) is str and str(uuid.UUID(value)) == value and uuid.UUID(value).int:
            return value
    except ValueError: pass
    raise UIError("project", "A canonical project ID is required.")


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise UIError("json", "Duplicate JSON key.")
        result[key] = value
    return result


def decode(raw):
    def constant(_): raise UIError("json", "Nonfinite numbers are unsupported.")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, UIError): raise
        raise UIError("json", "Malformed JSON.") from exc


def safe(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts or path.resolve() != path:
        raise UIError("path", "Noncanonical path refused.")
    for p in (path, *path.parents):
        if p.is_symlink(): raise UIError("path", "Symlinks are not permitted.")
    if path.exists() and (not path.is_file() and not path.is_dir()):
        raise UIError("path", "Special files are not permitted.")
    if path.is_file() and path.stat().st_nlink != 1:
        raise UIError("path", "Hard-linked files are not permitted.")
    return path


def read(path, maximum):
    path = safe(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        if os.fstat(stream.fileno()).st_nlink != 1: raise UIError("path", "File alias refused.")
        raw = stream.read(maximum + 1)
    if len(raw) > maximum: raise UIError("limit", "Stored document exceeds UI size limit.")
    return raw


def manual_subset(document):
    """Check all historical states BEFORE accepted validation could open asset references."""
    try:
        states = [document]
        states += [state for tx in document["history"]["transactions"] for state in (tx["before"], tx["after"])]
        states += [v["snapshot"] for v in document["versions"]]
        for state in states:
            if state["assets"] != [] or state["brand"] is not None or state["project"]["outputs"] != ["poster"]:
                raise UIError("unsupported", "Only manual text/geometry projects are supported.")
            if len(state["elements"]) > MAX_ELEMENTS or len(state["content"]) != 32:
                raise UIError("limit", "Manual project capacity exceeded.")
            for content in state["content"]:
                if set(content) != {"id", "text", "language", "kind"} or content["kind"] != "editorial":
                    raise UIError("unsupported", "External or protected content is unsupported.")
                text(content["text"])
            for element in state["elements"]:
                style = element["style"]
                if element["type"] == "text":
                    if set(style) != {"fill", "font_size"}: raise UIError("unsupported", "Unsupported text style.")
                    integer(style["font_size"], 1, 512)
                elif element["type"] == "shape":
                    if set(style) != {"fill", "shape"} or style["shape"] not in {"rectangle", "ellipse"}:
                        raise UIError("unsupported", "Unsupported geometry.")
                else: raise UIError("unsupported", "Media, paths and rendering are disabled.")
                color(style["fill"])
                for key in ("x", "y"): integer(element[key], -1000000, 1000000)
                for key in ("width", "height"): integer(element[key], 1, 4096)
        if len(encoded(document)) + 1 > MAX_DOCUMENT: raise UIError("limit", "Manual document size limit reached.")  # core.save adds newline
    except (KeyError, TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as exc:
        if isinstance(exc, UIError): raise
        raise UIError("document", "Unsupported or malformed manual document.") from exc


class Studio:
    def __init__(self, root, *, resume=False, analysis_provider=None):
        root = safe(Path(root))
        if not root.is_relative_to(RUNTIME) or root == RUNTIME:
            raise UIError("path", "Use a named root inside .runtime/studio-ui.")
        if resume:
            marker = decode(read(root / "studio-session.json", 1024))
            exact(marker, {"manual_ui", "id"})
            if type(marker["manual_ui"]) is not int or marker["manual_ui"] != 1: raise UIError("session", "Unsupported session.")
            project_id(marker["id"])
        else:
            root.mkdir(parents=True, exist_ok=False, mode=0o700)
        self.root, self.projects = root, safe(root / "projects")
        self.projects.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self._fd = os.open(safe(root / "studio.lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try: fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._fd)
            raise UIError("lock", "This UI session already has an owner.") from exc
        if not resume:
            with (root / "studio-session.json").open("xb") as stream:
                stream.write(encoded({"manual_ui": 1, "id": str(uuid.uuid4())}))
        self._working, self._digests, self._saved = {}, {}, {}
        self.analysis_provider = analysis_provider

    def close(self):
        if self._fd is not None: os.close(self._fd); self._fd = None

    def _directory(self, identity):
        return safe(self.projects / project_id(identity))

    def _validate(self, doc, directory):
        manual_subset(doc)
        try: core.validate(doc, directory)
        except core.CreativeError as exc: raise UIError("document", "creative@1 validation refused the document.") from exc

    def analysis(self):
        value = {"availability": "unavailable", "state": "ABSENT", "enabled": False,
                 "error": "agent-not-connected", "controls_enabled": False,
                 "real_media_enabled": False, "gate_a": "BLOCKED"}
        if self.analysis_provider is None: return value
        try:
            supplied = self.analysis_provider()
            state = supplied["state"]
            if state not in {"ABSENT", "DISABLED", "STOPPED", "STARTING", "READY", "BUSY", "STOPPING", "FAULTED", "INCOMPATIBLE"}:
                raise ValueError()
            value["state"] = state
            value["availability"] = "unavailable" if state in {"ABSENT", "INCOMPATIBLE"} else "disabled"
            value["error"] = {"FAULTED": "agent-faulted", "INCOMPATIBLE": "agent-incompatible", "ABSENT": "agent-not-connected"}.get(state, "qualification-required")
        except Exception:
            value.update(state="INCOMPATIBLE", error="status-unavailable")
        return value  # providers cannot enable controls or media, even if they claim READY

    def document(self, identity):
        identity = project_id(identity)
        if identity not in self._working: self.reopen(identity)
        return copy.deepcopy(self._working[identity])

    def view(self, identity):
        doc = self.document(identity)
        active = {e.get("content_id") for e in doc["elements"] if e["type"] == "text"}
        used = active
        remaining = {lang: sum(c["language"] == lang and c["id"] not in used for c in doc["content"]) for lang in ("en", "te")}
        cursor = doc["history"]["cursor"]
        return {"project_id": identity, "name": doc["project"]["name"], "revision": doc["revision"],
                "view": doc["views"][0], "elements": doc["elements"],
                "content": [c for c in doc["content"] if c["id"] in active],
                "can_undo": cursor > 0, "can_redo": cursor < len(doc["history"]["transactions"]),
                "saved": self._digests.get(identity) is not None,
                "dirty": self._saved.get(identity) != hashlib.sha256(encoded(doc)).hexdigest(),
                "remaining_text_slots": remaining, "element_limit": MAX_ELEMENTS,
                "approval_count": len(doc["approvals"])}

    def create(self, request):
        exact(request, {"name", "text", "language"})
        name, initial = text(request["name"], 128), text(request["text"])
        language = request["language"]
        if language not in ("en", "te"): raise UIError("language", "Choose English or Telugu.")
        with self.lock:
            if len(list(self.projects.iterdir())) >= 100: raise UIError("limit", "Session project limit reached.")
            identity = str(uuid.uuid4()); directory = self._directory(identity); directory.mkdir()
            doc = core.new_document(identity)
            doc["project"]["name"] = name
            doc["content"][0].update(text=initial, language=language)
            doc["views"][0]["language"] = language
            for lang in ("en", "te"):
                for i in range(16 - int(lang == language)):
                    doc["content"].append({"id": f"text-{lang}-{i}", "text": "New text" if lang == "en" else "కొత్త పాఠ్యం",
                                           "language": lang, "kind": "editorial"})
            self._validate(doc, directory)
            self._working[identity] = doc
            self._digests[identity] = None
            return self.view(identity)

    def list_projects(self):
        with self.lock:
            result = []
            for path in sorted(self.projects.iterdir()):
                identity = project_id(path.name); self._directory(identity)
                if identity not in self._working and not (path / "creative.json").exists(): continue
                value = self.view(identity)
                result.append({k: value[k] for k in ("project_id", "name", "dirty", "saved")})
            return result

    def reopen(self, identity, expected_revision=None):
        with self.lock:
            identity = project_id(identity); directory = self._directory(identity)
            if expected_revision is not None: self._expected(identity, expected_revision)
            try: raw = read(directory / "creative.json", MAX_DOCUMENT)
            except FileNotFoundError as exc: raise UIError("not-saved", "Save the project before reopening it.", 404) from exc
            doc = decode(raw); self._validate(doc, directory)
            if doc["id"] != identity: raise UIError("identity", "Project identity mismatch.")
            self._working[identity] = doc
            self._digests[identity] = hashlib.sha256(raw).hexdigest()
            self._saved[identity] = hashlib.sha256(encoded(doc)).hexdigest()
            return self.view(identity)

    def _expected(self, identity, revision):
        integer(revision, 0, 1000000000)
        doc = self.document(identity)
        if doc["revision"] != revision: raise UIError("conflict", "Project changed; reload its current state.", 409)
        return doc

    def action(self, request):
        if type(request) is not dict: raise UIError("request", "Object required.")
        action = request.get("action")
        extras = {"edit_text": {"element_id", "text"}, "move": {"element_id", "x", "y"},
                  "font_size": {"element_id", "font_size"}, "color": {"element_id", "color"},
                  "add_text": {"language"}, "add_shape": {"shape"}, "undo": set(), "redo": set(), "save": set()}
        if type(action) is not str or action not in extras: raise UIError("operation", "Unsupported manual operation.")
        exact(request, {"project_id", "expected_revision", "action"} | extras[action])
        with self.lock:
            identity = project_id(request["project_id"]); directory = self._directory(identity)
            doc = self._expected(identity, request["expected_revision"])
            try:
                if action == "save":
                    self._validate(doc, directory)
                    target = safe(directory / "creative.json"); safe(directory / "creative.json.previous")
                    if target.exists():
                        old = decode(read(target, MAX_DOCUMENT)); self._validate(old, directory)
                        if self._digests.get(identity) is None: raise UIError("conflict", "Unexpected saved project.", 409)
                    digest = core.save(doc, directory, expected_digest=self._digests.get(identity))
                    self._digests[identity] = digest
                    self._saved[identity] = hashlib.sha256(encoded(doc)).hexdigest()
                    return self.view(identity)
                if action in {"undo", "redo"}:
                    candidate = getattr(core, action)(doc, directory)
                else:
                    if action.startswith("add_"):
                        if len(doc["elements"]) >= MAX_ELEMENTS: raise UIError("limit", "Layer limit reached.")
                        element = {"id": "layer-" + str(uuid.uuid4()), "view_id": doc["views"][0]["id"],
                                   "x":80,"y":100,"width":800,"height":160}
                        if action == "add_text":
                            language = request["language"]
                            if language not in ("en", "te"): raise UIError("language", "Choose English or Telugu.")
                            used = {e.get("content_id") for e in doc["elements"]}
                            slot = next((c for c in doc["content"] if c["language"] == language and c["id"] not in used), None)
                            if slot is None: raise UIError("limit", "No unused text slots for this language.")
                            element.update(type="text", content_id=slot["id"], style={"fill":"#ffffff","font_size":64})
                        else:
                            if request["shape"] not in ("rectangle", "ellipse"): raise UIError("shape", "Unsupported shape.")
                            element.update(type="shape", width=300, height=200, style={"fill":"#6366f1","shape":request["shape"]})
                        operation = {"op":"add","element":element}
                    else:
                        selected = next((e for e in doc["elements"] if e["id"] == request["element_id"]), None)
                        if selected is None: raise UIError("element", "Choose an existing layer.")
                        if action == "edit_text":
                            if selected["type"] != "text": raise UIError("element", "This layer has no text.")
                            operation={"op":"edit_text","element_id":selected["id"],"text":text(request["text"])}
                        elif action == "move": operation={"op":"move","element_id":selected["id"],"x":integer(request["x"],-1000000,1000000),"y":integer(request["y"],-1000000,1000000)}
                        else:
                            if action == "font_size" and selected["type"] != "text": raise UIError("element", "Font size is for text layers.")
                            style={"font_size":integer(request["font_size"],1,512)} if action == "font_size" else {"fill":color(request["color"])}
                            operation={"op":"restyle","element_id":selected["id"],"style":style}
                    candidate = core.apply(doc, operation, directory)
                self._validate(candidate, directory)
                self._working[identity] = candidate
                return self.view(identity)
            except core.CreativeError as exc:
                if "concurrent document change" in str(exc):
                    raise UIError("conflict", "Saved file changed; reopen it before saving again.", 409) from exc
                raise UIError("core-validation", "Operation refused: no change, history limit, or invalid/stale saved state.") from exc
