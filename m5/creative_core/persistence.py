"""Project-confined JSON persistence. No automatic recovery or migration."""
import hashlib
import json
import os
import tempfile
from .document import CreativeError, canonical
from .validation import confined, validate, require

MAX_BYTES = 16 * 1024 * 1024


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CreativeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise CreativeError(f"invalid JSON constant: {value}")


def _decode(data, root):
    require(len(data) <= MAX_BYTES, "document exceeds size limit")
    try:
        doc = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                         parse_constant=_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CreativeError(f"malformed creative JSON: {exc}") from exc
    return validate(doc, root)


def _read(path):
    require(path.is_file(), f"document not found: {path.name}")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, "document exceeds size limit")
    return data


def load(root, name="creative.json"):
    return _decode(_read(confined(root, name, must_exist=True)), root)


def file_digest(root, name="creative.json"):
    return hashlib.sha256(_read(confined(root, name, must_exist=True))).hexdigest()


def _atomic(path, data):
    """Flush bytes before replacement; cleanup temporary file on ordinary exceptions."""
    fd, temporary = tempfile.mkstemp(prefix=".creative-save-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save(doc, root, name="creative.json", expected_digest=None):
    validate(doc, root)
    target = confined(root, name)
    require(target.parent.is_dir(), "save parent directory must already exist")
    previous = confined(root, name + ".previous")
    data = canonical(doc) + b"\n"
    require(len(data) <= MAX_BYTES, "document exceeds size limit")
    if target.exists():
        old = _read(target)
        old_doc = _decode(old, root)  # Never overwrite malformed primary or its backup.
        require(doc["id"] == old_doc["id"], "cannot replace a different project identity")
        if expected_digest is not None:
            require(hashlib.sha256(old).hexdigest() == expected_digest,
                    "concurrent document change")
        if doc == old_doc:
            return hashlib.sha256(old).hexdigest()  # Preserve the actual previous revision.
        require(doc["revision"] >= old_doc["revision"], "revision would move backwards")
        require(doc == old_doc or doc["revision"] > old_doc["revision"],
                "changed document requires a newer revision")
        # Existing named versions are append-only, including their approval records.
        versions = {v["id"]: v for v in doc["versions"]}
        require(all(versions.get(v["id"]) == v for v in old_doc["versions"]),
                "cannot modify or delete saved named versions")
        _atomic(previous, old)
    else:
        require(expected_digest is None, "expected document is missing")
    _atomic(target, data)
    # Best-effort directory sync: unsupported filesystems may not permit this.
    try:
        directory = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError:
        pass
    return hashlib.sha256(data).hexdigest()


def recover_previous(root, name="creative.json"):
    """Return a validated previous revision. Caller explicitly saves to a NEW filename."""
    return load(root, name + ".previous")
