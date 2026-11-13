"""M7-C: extra facts about posters and their exports, without changing anything M5 owns.

- When a poster last changed: the newest file time under M5's own folders for that poster (read only).
- Whether a poster is one of the concepts made from a brief, and which brief: M5 keeps a receipt for every concept
  bundle (concept-proposals/<digest>.json) and gives each concept poster an id derived from that receipt. Recomputing
  the id proves the link. A poster with a brief but no receipt is only called "from a brief"; nothing is guessed.
- Which poster an export came from: M5's export record does not name its poster, so M6 writes one small line of its
  own when an export finishes (ExportIndex, in M6's links folder, outside M5's session). Older exports stay unnamed.
"""
import json, os, tempfile, time, uuid
from pathlib import Path

_fmt = lambda t: time.strftime("%Y-%m-%d %H:%M", time.localtime(t))


def modified(session: Path, identity: str):
    newest = 0.0
    for folder in (session / "projects" / identity, session / "bound-projects" / identity):
        if not folder.is_dir(): continue
        for base, _dirs, files in os.walk(folder):
            for f in files:
                try: newest = max(newest, os.path.getmtime(os.path.join(base, f)))
                except OSError: pass
    return _fmt(newest) if newest else None


def roles(session: Path, session_id: str, ids, bound):
    """id -> (role, source id). role: concept (proved by a receipt), brief-source (concepts were made from it),
    brief (has a brief, no receipt says more), plain."""
    concept, sources = {}, set()
    receipts = session / "concept-proposals"
    if receipts.is_dir() and session_id:
        for f in sorted(receipts.glob("*.json")):
            try:
                r = json.loads(f.read_text(encoding="utf-8")); src = r["inputs"]["source_project"]; digest = r["digest"]
                made = [str(uuid.uuid5(uuid.UUID(session_id), digest + ":" + c["id"])) for c in r["concepts"]]
            except Exception: continue          # an unreadable receipt proves nothing
            hit = [m for m in made if m in ids]
            for m in hit: concept[m] = src
            if hit: sources.add(src)
    out = {}
    for i in ids:
        if i in concept: out[i] = ("concept", concept[i])
        elif i in sources: out[i] = ("brief-source", None)
        elif i in bound: out[i] = ("brief", None)
        else: out[i] = ("plain", None)
    return out


class ExportIndex:
    """export folder name -> the poster it came from. One JSON file, replaced atomically."""
    FORMAT = "ideaframe-export-index@1"

    def __init__(self, root: Path): self.file = Path(root) / "export-index.json"

    def all(self):
        try:
            d = json.loads(self.file.read_text(encoding="utf-8"))
            return d["exports"] if d.get("format") == self.FORMAT and isinstance(d.get("exports"), dict) else {}
        except Exception: return {}

    def add(self, export_dir: str, project_id: str, name: str, revision: int):
        rows = self.all(); rows[os.path.basename(export_dir)] = dict(project_id=project_id, name=name, revision=revision, at=_fmt(time.time()))
        self.file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(dir=self.file.parent, prefix=".export-index-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as h: json.dump(dict(format=self.FORMAT, exports=rows), h, ensure_ascii=False, indent=1); h.flush(); os.fsync(h.fileno())
            os.replace(tmp, self.file)
        except BaseException:
            if os.path.exists(tmp): os.remove(tmp)
            raise
