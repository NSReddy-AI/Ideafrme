"""Pure transactions: callers receive a new validated document or an error."""
from copy import deepcopy
from uuid import uuid4
from .document import CORE_KEYS, core, fingerprint
from .validation import validate, require, fields, MAX_HISTORY


def _commit(doc, candidate, root, label):
    before, after = core(doc), core(candidate)
    require(before != after, "operation has no effect")
    history = candidate["history"]
    history["transactions"] = history["transactions"][:history["cursor"]]
    require(len(history["transactions"]) < MAX_HISTORY, "history limit reached")
    history["transactions"].append({"id": str(uuid4()), "operation": label,
                                     "before": before, "after": after})
    history["cursor"] += 1
    candidate["approvals"] = []
    candidate["revision"] += 1
    return validate(candidate, root)


def apply(doc, operation, root):
    validate(doc, root)
    require(isinstance(operation, dict), "operation must be an object")
    kind = operation.get("op")
    specs = {"add": ("element",), "move": ("element_id", "x", "y"),
             "restyle": ("element_id", "style"),
             "edit_text": ("element_id", "text"), "remove": ("element_id",),
             "reorder": ("view_id", "ordered_element_ids", "expected_revision"),
             "geometry": ("view_id", "targets", "expected_revision")}
    require(isinstance(kind, str) and kind in specs, "unsupported operation")
    fields(operation, ("op", *specs[kind]), ("acknowledge_upgrade", "legacy_checkpoint_sha256") if kind in ("reorder", "geometry") else (), label="operation")
    candidate = deepcopy(doc)
    if kind == "geometry":
        require(type(operation["expected_revision"]) is int and operation["expected_revision"] == doc["revision"], "stale geometry revision")
        view = operation["view_id"]
        require(type(view) is str and any(v["id"] == view for v in doc["views"]), "unknown geometry view")
        targets = operation["targets"]
        require(type(targets) is list and 0 < len(targets) <= len(doc["elements"]), "invalid geometry targets")
        seen = set()
        for target in targets:
            fields(target, ("element_id", "x", "y", "width", "height"), label="geometry target")
            identity = target["element_id"]
            require(type(identity) is str and identity not in seen, "duplicate or invalid geometry identity")
            seen.add(identity)
            matches = [e for e in candidate["elements"] if e["id"] == identity and e["view_id"] == view]
            require(len(matches) == 1, "unknown or foreign geometry identity")
            from .validation import number
            for key in ("x", "y", "width", "height"):
                number(target[key], key, key in ("width", "height"))
                matches[0][key] = target[key]
        require(core(candidate) != core(doc), "geometry has no effect")
        if doc["history"].get("version", 1) < 3:
            require(operation.get("acknowledge_upgrade") is True, "history v3 upgrade acknowledgement required")
            import hashlib, re
            from .validation import confined
            from .document import canonical
            digest = operation.get("legacy_checkpoint_sha256")
            require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest), "legacy checkpoint required")
            checkpoint = confined(root, "legacy-checkpoints/" + digest + ".json", must_exist=True)
            info = checkpoint.stat()
            require(info.st_nlink == 1 and info.st_mode & 0o222 == 0 and info.st_size <= 8*1024*1024, "checkpoint is not immutable or bounded")
            with checkpoint.open("rb") as stream: raw = stream.read(8*1024*1024+1)
            require(hashlib.sha256(raw).hexdigest() == digest and raw == canonical(doc) + b"\n", "legacy checkpoint does not match document")
        else:
            require("acknowledge_upgrade" not in operation and "legacy_checkpoint_sha256" not in operation, "upgrade fields not applicable to history version 3")
        candidate["history"]["version"] = 3
    elif kind == "reorder":
        require(type(operation["expected_revision"]) is int and operation["expected_revision"] == doc["revision"], "stale reorder revision")
        view = operation["view_id"]
        require(isinstance(view, str) and any(v["id"] == view for v in doc["views"]), "unknown reorder view")
        ids = operation["ordered_element_ids"]
        current = [e["id"] for e in doc["elements"] if e["view_id"] == view]
        require(type(ids) is list and all(type(i) is str for i in ids) and len(ids) == len(current)
                and len(set(ids)) == len(ids) and set(ids) == set(current), "reorder requires complete same-view permutation")
        require(ids != current, "reorder has no effect")
        if doc["history"].get("version", 1) == 1:
            require(operation.get("acknowledge_upgrade") is True, "history upgrade acknowledgement required")
            import hashlib
            import re
            from .validation import confined
            from .document import canonical
            digest = operation.get("legacy_checkpoint_sha256")
            require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest), "legacy checkpoint required")
            checkpoint = confined(root, "legacy-checkpoints/" + digest + ".json", must_exist=True)
            info = checkpoint.stat()
            require(info.st_nlink == 1 and info.st_mode & 0o222 == 0 and info.st_size <= 8*1024*1024,
                    "checkpoint is not immutable or bounded")
            with checkpoint.open("rb") as stream: raw = stream.read(8*1024*1024+1)
            require(hashlib.sha256(raw).hexdigest() == digest and raw == canonical(doc) + b"\n",
                    "legacy checkpoint does not match document")
        else:
            require("acknowledge_upgrade" not in operation and "legacy_checkpoint_sha256" not in operation,
                    "upgrade fields not applicable to history version 2")
        candidate["history"]["version"] = max(2, doc["history"].get("version", 1))
        ordered = iter(ids); elements = {e["id"]: e for e in candidate["elements"]}
        candidate["elements"] = [elements[next(ordered)] if e["view_id"] == view else e for e in candidate["elements"]]
    elif kind == "add":
        candidate["elements"].append(deepcopy(operation["element"]))
    else:
        matches = [el for el in candidate["elements"] if el["id"] == operation["element_id"]]
        require(bool(matches), "element not found")
        el = matches[0]
        if kind == "move":
            el.update(x=operation["x"], y=operation["y"])
        elif kind == "restyle":
            require(isinstance(operation["style"], dict), "style must be an object")
            el["style"].update(deepcopy(operation["style"]))
        elif kind == "edit_text":
            require(el["type"] == "text", "edit_text requires a text element")
            text = next(t for t in candidate["content"] if t["id"] == el["content_id"])
            require(text["kind"] == "editorial", "claims and quotes cannot be edited by this API")
            text["text"] = operation["text"]
        elif kind == "remove":
            candidate["elements"].remove(el)
    return _commit(doc, candidate, root, kind)


def _travel(doc, root, delta):
    validate(doc, root)
    candidate = deepcopy(doc)
    history = candidate["history"]
    cursor = history["cursor"]
    require(cursor > 0 if delta < 0 else cursor < len(history["transactions"]),
            "nothing to undo" if delta < 0 else "nothing to redo")
    tx = history["transactions"][cursor - 1 if delta < 0 else cursor]
    state = tx["before" if delta < 0 else "after"]
    for key in CORE_KEYS:
        candidate[key] = deepcopy(state[key])
    history["cursor"] += delta
    candidate["approvals"] = []
    candidate["revision"] += 1
    return validate(candidate, root)


def undo(doc, root):
    return _travel(doc, root, -1)


def redo(doc, root):
    return _travel(doc, root, 1)


def approve(doc, reviewer, root):
    """Record a caller-confirmed human review; not authentication or factual verification."""
    validate(doc, root)
    require(all("sha256" in asset for asset in doc["assets"]),
            "approval requires pinned asset hashes")
    candidate = deepcopy(doc)
    candidate["approvals"].append({"id": str(uuid4()), "reviewer": reviewer,
                                     "fingerprint": fingerprint(doc)})
    candidate["revision"] += 1
    return validate(candidate, root)


def snapshot(doc, name, root):
    validate(doc, root)
    candidate = deepcopy(doc)
    candidate["versions"].append({"id": str(uuid4()), "name": name,
                                    "snapshot": core(doc), "fingerprint": fingerprint(doc),
                                    "approvals": deepcopy(doc["approvals"])})
    candidate["revision"] += 1
    return validate(candidate, root)
