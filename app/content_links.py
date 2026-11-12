"""Which poster layers hold approved reel words (M6 step 6). M6's own small store, kept OUTSIDE M5's session folder so
M5's documents and recovery rules stay untouched: m5/.runtime/studio-ui/<IDEAFRAME_M6_LINKS or m6-content-links>/<poster>.json.
One record per inserted layer: poster id, layer id, M5 content id, reel, item id, item SHA-256, source fingerprint, approvals."""
import json, os, re, tempfile
from pathlib import Path

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


class Links:
    def __init__(self, root: Path): self.root = Path(root)

    def _file(self, poster_id):
        if not UUID.match(poster_id): raise ValueError("invalid poster id")
        return self.root / f"{poster_id}.json"

    def get(self, poster_id):
        f = self._file(poster_id)
        if not f.is_file(): return []
        with open(f, encoding="utf-8") as h: return json.load(h)

    def add(self, poster_id, record):
        rows = [r for r in self.get(poster_id) if r["element_id"] != record["element_id"]] + [record]
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(dir=self.root, prefix=".links-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as h: json.dump(rows, h, ensure_ascii=False, indent=1); h.flush(); os.fsync(h.fileno())
            os.replace(tmp, self._file(poster_id))           # all or nothing
        except BaseException:
            if os.path.exists(tmp): os.remove(tmp)
            raise
        return record
