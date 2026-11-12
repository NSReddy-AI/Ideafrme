"""Library-independent creative@1 documents. No I/O or external dependencies."""
from copy import deepcopy
import hashlib
import json

FORMAT = "ai-reel-studio/creative@1"
CORE_KEYS = ("format", "schema_version", "id", "project", "brand", "languages",
             "views", "assets", "content", "elements")
TOP_KEYS = set(CORE_KEYS) | {"revision", "approvals", "versions", "history"}


class CreativeError(ValueError):
    """Rejected document, transaction or filesystem operation."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def core(document):
    return deepcopy({key: document[key] for key in CORE_KEYS})


def fingerprint(document):
    return "sha256:" + hashlib.sha256(canonical(core(document))).hexdigest()


def new_document(identity="synthetic-project"):
    return {
        "format": FORMAT, "schema_version": 1, "id": identity, "revision": 0,
        "project": {"name": "Synthetic creative project", "outputs": ["poster"]},
        "brand": None, "languages": ["te", "en"],
        "views": [{"id": "portrait", "width": 1080, "height": 1350,
                   "language": "te"}],
        "assets": [],
        "content": [{"id": "headline", "text": "కొత్త ఆలోచన / New idea",
                     "language": "te", "kind": "editorial"}],
        "elements": [{"id": "title", "type": "text", "view_id": "portrait",
                      "content_id": "headline", "x": 80, "y": 100,
                      "width": 920, "height": 200,
                      "style": {"font_size": 72, "fill": "#ffffff"}}],
        "approvals": [], "versions": [],
        "history": {"cursor": 0, "transactions": []},
    }
