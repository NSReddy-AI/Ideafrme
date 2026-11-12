"""M6 step 7: turn a poster into an ordinary M4 slides reel project ("Both": poster + reel from one design).

Nothing new is invented for the engine. The converter does exactly what a person would do in the Reels screen:
  1. rs.py new <brand> <platform> <style> <slug>                      (unchanged CLI, a normal M4 project in projects/)
  2. inputs/slide_01.png ... : the poster's exported PNG, one copy per sentence (slides reel: one slide per sentence)
  3. rs.py narration <project> none                                   (text + music; voice can be changed later in Reels)
  4. rs.py script <project> inputs/script.txt                         (PREPARED for review, NOT approved)
The script is the poster's text layers, top to bottom, exactly as written (line breaks inside a layer become spaces).
Approval stays with the owner: the reel cannot be built or rendered until the script is approved in Reels, even when
every line came from another reel's approved words (each M4 project has its own approval).
The PNG must be a poster export of the CURRENT poster: its SVG hash must equal the current scene's and the PNG bytes must
match the hash in the export manifest. build/conversion.json records the poster, revision, hashes and linked approved lines."""
import hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]


def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class ConvertError(ValueError):
    def __init__(self, code, message, status=409): super().__init__(message); self.code, self.status = code, status


def current_png(studio, doc, scene):
    """The export folder whose SVG is exactly the current scene and which has a verified PNG."""
    for d in sorted((studio.root / "exports").iterdir(), reverse=True):
        m = d / "manifest.json"
        if not m.is_file(): continue
        v = json.loads(m.read_text(encoding="utf-8"))
        if v.get("svg_sha256") == scene["svg_sha256"] and v.get("revision") == doc["revision"] and v.get("png_sha256"):
            png = d / "poster.draft.png"
            if png.is_file() and _sha(png) == v["png_sha256"]: return png, v, d
    raise ConvertError("export-png-first", "Export a PNG of the poster as it is now, then make the reel.")


def script_lines(doc):
    text = {c["id"]: c["text"] for c in doc["content"]}
    layers = sorted((e for e in doc["elements"] if e["type"] == "text"), key=lambda e: (e["y"], e["x"]))
    lines = [re.sub(r"\s*\n\s*", " ", text.get(e["content_id"], "")).strip() for e in layers]
    return [l for l in lines if l]


def convert(studio, project_id, brand, platform, style, slug, links=(), python=None, projects_dir=None):
    python = python or os.environ.get("RS_PYTHON") or str(Path.home() / ".venvs/reelstudio/bin/python")
    doc = studio.manual.document(project_id)
    scene = studio.scene(project_id, doc["revision"])
    png, manifest, export_dir = current_png(studio, doc, scene)
    lines = script_lines(doc)
    if not lines: raise ConvertError("no-text", "The poster has no text to use as the reel's script.")
    slug = re.sub(r"[^a-z0-9_]+", "_", slug.lower()).strip("_")
    if not slug: raise ConvertError("slug", "Give the reel a short name.", 400)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    run = lambda *a: subprocess.run([python, *a], cwd=WORKSPACE, env=env, capture_output=True, text=True, timeout=120)
    r = run("engine/rs.py", "new", brand, platform, style, slug)
    if r.returncode: raise ConvertError("new", (r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else "could not create the reel", 400)
    name = os.path.basename(r.stdout.strip().splitlines()[-1]); d = Path(projects_dir or WORKSPACE / "projects") / name
    for i in range(1, len(lines) + 1): shutil.copyfile(png, d / "inputs" / f"slide_{i:02d}.png")
    (d / "inputs" / "script.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for step in (("engine/rs.py", "narration", name, "none"), ("engine/rs.py", "script", name, str(d / "inputs" / "script.txt"))):
        r = run(*step)
        if r.returncode: raise ConvertError("prepare", f"{step[1]} failed: " + ((r.stderr or r.stdout).strip().splitlines() or ["?"])[-1], 500)
    record = dict(format="ideaframe-poster-to-reel@1", created=time.strftime("%Y-%m-%d %H:%M:%S"), project=name,
                  poster=dict(project_id=project_id, name=doc["project"]["name"], revision=doc["revision"], source_fingerprint=manifest.get("source_fingerprint"),
                              svg_sha256=manifest["svg_sha256"], png_sha256=manifest["png_sha256"], export=export_dir.name),
                  slides=len(lines), script=lines, script_approved=False,
                  approved_lines=[dict(reel=l["reel"], item_id=l["item_id"], ok=l["ok"]) for l in links])
    (d / "build").mkdir(exist_ok=True)
    (d / "build" / "conversion.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return record
