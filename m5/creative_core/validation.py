"""Strict creative@1 subset validation, including project-local asset checks."""
import math
from pathlib import Path, PurePosixPath
from .document import (CORE_KEYS, TOP_KEYS, FORMAT, CreativeError, canonical,
                       fingerprint)

MAX_ITEMS = 1000
MAX_HISTORY = 200


def require(condition, message):
    if not condition:
        raise CreativeError(message)


def fields(value, required, optional=(), label="object"):
    require(isinstance(value, dict), f"{label}: expected object")
    require(set(required) <= value.keys(), f"{label}: missing required fields")
    require(value.keys() <= set(required) | set(optional), f"{label}: unknown fields")


def string(value, label):
    require(isinstance(value, str) and 0 < len(value) <= 10000
            and "\x00" not in value, f"{label}: invalid string")


def number(value, label, positive=False):
    require(type(value) in (int, float) and math.isfinite(value),
            f"{label}: expected finite number")
    require(0 < value <= 32768 if positive else abs(value) <= 1000000,
            f"{label}: geometry out of range")


def records(value, label, maximum=MAX_ITEMS):
    require(isinstance(value, list) and len(value) <= maximum, f"{label}: invalid list")
    result = {}
    for item in value:
        require(isinstance(item, dict), f"{label}: expected record")
        string(item.get("id"), f"{label}.id")
        require(item["id"] not in result, f"{label}: duplicate ID {item['id']}")
        result[item["id"]] = item
    return result


def confined(root, relative, must_exist=False):
    """Reject all symlinks, traversal and platform-ambiguous relative paths.

    This is defense in depth for a trusted local project, not a race-proof OS sandbox.
    """
    string(relative, "path")
    p = PurePosixPath(relative)
    require(not p.is_absolute() and "\\" not in relative and ":" not in relative
            and all(part not in ("", ".", "..") for part in relative.split("/")),
            "path: must be a normalized project-relative path")
    root = Path(root).absolute()
    require(root.is_dir(), "project root must exist")
    for parent in (root, *root.parents):
        require(not parent.is_symlink(), "project root contains a symlink")
    target = root
    for part in p.parts:
        target = target / part
        require(not target.is_symlink(), "path: symlinks are not allowed")
    require(target.resolve().is_relative_to(root.resolve()), "path escapes project root")
    if must_exist:
        require(target.is_file(), f"missing asset: {relative}")
    return target


def validate_core(doc, root):
    fields(doc, CORE_KEYS, label="core")
    require(doc["format"] == FORMAT and type(doc["schema_version"]) is int
            and doc["schema_version"] == 1, "unsupported document version")
    string(doc["id"], "document.id")
    fields(doc["project"], ("name", "outputs"), label="project")
    string(doc["project"]["name"], "project.name")
    outputs = doc["project"]["outputs"]
    require(isinstance(outputs, list) and outputs
            and all(type(x) is str and x in ("poster", "reel") for x in outputs)
            and len(set(outputs)) == len(outputs), "invalid outputs")
    langs = doc["languages"]
    require(isinstance(langs, list) and langs
            and all(type(x) is str and x in ("te", "en") for x in langs)
            and len(set(langs)) == len(langs), "unsupported languages")
    views = records(doc["views"], "views")
    require(bool(views), "at least one view required")
    for view in views.values():
        fields(view, ("id", "width", "height", "language"), label="view")
        number(view["width"], "view.width", True)
        number(view["height"], "view.height", True)
        require(view["language"] in langs, "view language missing")
    assets = records(doc["assets"], "assets")
    for asset in assets.values():
        fields(asset, ("id", "path", "kind"), ("sha256",), "asset")
        require(asset["kind"] in ("image", "vector", "logo", "video", "font", "brand"),
                "unsupported asset kind")
        path = confined(root, asset["path"], must_exist=True)
        if "sha256" in asset:
            import hashlib
            digest = asset["sha256"]
            require(isinstance(digest, str) and len(digest) == 64
                    and all(c in "0123456789abcdef" for c in digest), "invalid asset hash")
            hasher = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    hasher.update(chunk)
            require(hasher.hexdigest() == digest, "asset hash mismatch")
    if doc["brand"] is not None:
        fields(doc["brand"], ("id", "asset_id"), label="brand")
        string(doc["brand"]["id"], "brand.id")
        require(doc["brand"]["asset_id"] in assets
                and assets[doc["brand"]["asset_id"]]["kind"] == "brand",
                "missing brand asset")
    content = records(doc["content"], "content")
    for text in content.values():
        fields(text, ("id", "text", "language", "kind"), ("source_ref",), "content")
        string(text["text"], "content.text")
        require(text["language"] in langs, "content language missing")
        require(text["kind"] in ("editorial", "claim", "quote"), "invalid content kind")
        if text["kind"] in ("claim", "quote"):
            require("source_ref" in text, "claim/quote requires source asset")
        if "source_ref" in text:
            require(text["source_ref"] in assets, "missing content source")
    elements = records(doc["elements"], "elements")
    for el in elements.values():
        fields(el, ("id", "type", "view_id", "x", "y", "width", "height", "style"),
               ("content_id", "asset_id"), "element")
        kind = el["type"]
        require(kind in ("text", "shape", "vector", "image", "logo", "video"),
                "unsupported element type")
        require(el["view_id"] in views, "missing view reference")
        for key in ("x", "y", "width", "height"):
            number(el[key], key, key in ("width", "height"))
        style = el["style"]
        fields(style, (), ("fill", "stroke", "stroke_width", "font_size", "opacity",
                           "rotation", "font_asset_id", "shape", "path"), "style")
        for key, value in style.items():
            if key in ("stroke_width", "font_size", "opacity", "rotation"):
                number(value, f"style.{key}")
                if key == "opacity": require(0 <= value <= 1, "opacity out of range")
                if key in ("stroke_width", "font_size"):
                    require(value >= 0 if key == "stroke_width" else value > 0,
                            "invalid style size")
            else:
                string(value, f"style.{key}")
        if "font_asset_id" in style:
            require(style["font_asset_id"] in assets
                    and assets[style["font_asset_id"]]["kind"] == "font", "missing font")
        if kind == "text":
            require(el.get("content_id") in content and "asset_id" not in el,
                    "text requires content binding only")
        elif kind in ("image", "logo", "video"):
            require(el.get("asset_id") in assets and "content_id" not in el,
                    "missing media asset reference")
            require(assets[el["asset_id"]]["kind"] == kind, "asset kind mismatch")
        elif kind == "vector":
            require("content_id" not in el, "vector cannot bind text")
            require(("path" in style) != ("asset_id" in el),
                    "vector requires either path or asset")
            if "asset_id" in el:
                require(el["asset_id"] in assets and assets[el["asset_id"]]["kind"]
                        in ("vector", "logo"), "missing vector asset")
        else:
            require("content_id" not in el and "asset_id" not in el
                    and style.get("shape") in ("rectangle", "ellipse"), "invalid shape")


def _validate(doc, root):
    confined(root, "creative.json")  # Check root even for documents without assets.
    fields(doc, TOP_KEYS, label="document")
    validate_core({key: doc[key] for key in CORE_KEYS}, root)
    require(type(doc["revision"]) is int and doc["revision"] >= 0, "invalid revision")
    approvals = records(doc["approvals"], "approvals")
    if approvals:
        require(all("sha256" in a for a in doc["assets"]), "approved assets must be pinned")
    for item in approvals.values():
        fields(item, ("id", "fingerprint", "reviewer"), label="approval")
        string(item["reviewer"], "reviewer")
        require(item["fingerprint"] == fingerprint(doc), "stale approval")
    versions = records(doc["versions"], "versions", 100)
    names = set()
    for item in versions.values():
        fields(item, ("id", "name", "snapshot", "fingerprint", "approvals"), label="version")
        string(item["name"], "version.name")
        require(item["name"] not in names, "duplicate version name")
        names.add(item["name"])
        validate_core(item["snapshot"], root)
        require(item["fingerprint"] == fingerprint(item["snapshot"]), "version hash mismatch")
        if item["approvals"]:
            require(all("sha256" in a for a in item["snapshot"]["assets"]),
                    "approved snapshot assets must be pinned")
        for approval in records(item["approvals"], "snapshot approvals").values():
            fields(approval, ("id", "fingerprint", "reviewer"), label="snapshot approval")
            string(approval["reviewer"], "reviewer")
            require(approval["fingerprint"] == item["fingerprint"], "snapshot approval mismatch")
    history = doc["history"]
    fields(history, ("cursor", "transactions"), ("version",), label="history")
    version = history.get("version", 1)
    require(type(version) is int and (("version" not in history and version == 1) or version in (2, 3)),
            "unsupported history version")
    txs = records(history["transactions"], "transactions", MAX_HISTORY)
    require(type(history["cursor"]) is int and 0 <= history["cursor"] <= len(txs),
            "invalid history cursor")
    previous = None
    ordered = list(txs.values())
    for tx in ordered:
        fields(tx, ("id", "operation", "before", "after"), label="transaction")
        require(tx["operation"] in (("add", "move", "restyle", "edit_text", "remove", "reorder", "geometry") if version == 3 else (("add", "move", "restyle", "edit_text", "remove", "reorder") if version == 2 else ("add", "move", "restyle", "edit_text", "remove"))),
                "unsupported history operation")
        validate_core(tx["before"], root)
        validate_core(tx["after"], root)
        if tx["operation"] == "geometry":
            before, after = tx["before"], tx["after"]
            require(all(before[k] == after[k] for k in CORE_KEYS if k != "elements"), "geometry changed non-element content")
            old, new = before["elements"], after["elements"]
            require(len(old) == len(new), "geometry changed element count")
            changed_views = set()
            for a, b in zip(old, new):
                require({k:v for k,v in a.items() if k not in ("x","y","width","height")} == {k:v for k,v in b.items() if k not in ("x","y","width","height")}, "geometry changed identity, paint order or non-geometry fields")
                if a != b: changed_views.add(a["view_id"])
            require(len(changed_views) == 1, "geometry must change exactly one view")
        if tx["operation"] == "reorder":
            before, after = tx["before"], tx["after"]
            require(all(before[k] == after[k] for k in CORE_KEYS if k != "elements"),
                    "reorder changed non-order content")
            old, new = before["elements"], after["elements"]
            require({e["id"]: e for e in old} == {e["id"]: e for e in new},
                    "reorder changed element identities or properties")
            require([e["view_id"] for e in old] == [e["view_id"] for e in new],
                    "reorder changed view slots")
            changed = [v["id"] for v in before["views"]
                       if [e["id"] for e in old if e["view_id"] == v["id"]]
                       != [e["id"] for e in new if e["view_id"] == v["id"]]]
            require(len(changed) == 1, "reorder must change exactly one view")
        if previous is not None:
            require(previous == tx["before"], "broken history chain")
        previous = tx["after"]
    if ordered:
        cursor = history["cursor"]
        state = ordered[cursor - 1]["after"] if cursor else ordered[0]["before"]
        require(state == {key: doc[key] for key in CORE_KEYS}, "history state mismatch")


def validate(doc, root):
    """Validate without modifying the document; normalize failures to CreativeError."""
    try:
        canonical(doc)
        _validate(doc, root)
    except CreativeError:
        raise
    except (TypeError, KeyError, ValueError, OverflowError, RecursionError, OSError) as exc:
        raise CreativeError(f"invalid document: {exc}") from exc
    return doc
