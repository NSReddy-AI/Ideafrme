"""M6 step 7: render an M4 project with the UNCHANGED engine inside an isolated job root.

The engine finds every folder from its own location (engine/common.py: ROOT = parent of engine/). A job root is therefore a
new folder under jobs/ that looks like a Reel Studio workspace:
    engine/      byte-for-byte copies of the engine's .py/.json files (hashed in the manifest); fonts/ and models/ are links
    platforms/ styles/ providers.json      copies
    brands/<id>/  a copy of M6's brands/<id>/, or an APPROVED Brand Library brand rebuilt by app/brand_bridge.py
    projects/<name>/   a COPY of the project (the original is never touched)
    exports/      empty; the engine writes the render here
The one shared resource, the heavy-model lock, stays shared: RS_HEAVY_LOCK points at M6's own lock file.
The unchanged `engine/adapter.py render` runs there (approval gate, QA, versions as always). JOB_MANIFEST.json records
inputs, engine hashes, command, events and outputs. Nothing outside the job root is written."""
import hashlib, json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
JOBS = WORKSPACE / "jobs"
PY = os.environ.get("RS_PYTHON") or str(Path.home() / ".venvs/reelstudio/bin/python")


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def _tree(d, skip=()):
    return {str(p.relative_to(d)): sha_file(p) for p in sorted(Path(d).rglob("*")) if p.is_file() and not p.is_symlink() and not any(s in p.parts for s in skip)}


def make_root(project, brand_dir=None, brand_store=None, brand_id=None):
    """Build the job root. Brand: brand_dir (a folder to copy) or an approved Library brand (brand_store + brand_id)."""
    src = WORKSPACE / "projects" / project
    if not (src / "project.json").is_file(): raise ValueError(f"no project {project}")
    P = json.loads((src / "project.json").read_text(encoding="utf-8"))
    root = JOBS / f"{time.strftime('%Y%m%d-%H%M%S')}-{project[:40]}-{uuid.uuid4().hex[:6]}"
    (root / "engine").mkdir(parents=True)
    eng = WORKSPACE / "engine"
    for f in sorted(eng.iterdir()):                                     # code: real copies, so the manifest proves what ran
        if f.is_file() and f.suffix in (".py", ".json"): shutil.copy2(f, root / "engine" / f.name)
    for d in ("fonts", "models"): os.symlink(eng / d, root / "engine" / d)   # large, read-only data: links
    for d in ("platforms", "styles"): shutil.copytree(WORKSPACE / d, root / d)
    shutil.copy2(WORKSPACE / "providers.json", root / "providers.json")
    bdst = root / "brands" / P["brand"]
    if brand_store is not None:
        sys.path.insert(0, str(WORKSPACE / "app")); import brand_bridge
        m = brand_bridge.export_engine_brand(brand_store, brand_id, bdst)
        if m["m4_brand_id"] != P["brand"]: shutil.rmtree(root); raise ValueError(f"Library brand is {m['m4_brand_id']}, project needs {P['brand']}")
        brand_source = dict(kind="brand-library", brand_id=brand_id, version=m["brand_version"], reviewer=m["reviewer"], approved_at=m["approved_at"])
    else:
        shutil.copytree(brand_dir or WORKSPACE / "brands" / P["brand"], bdst)
        brand_source = dict(kind="folder", path=str(brand_dir or Path("brands") / P["brand"]))
    shutil.copytree(src, root / "projects" / project, ignore=shutil.ignore_patterns("__pycache__", ".render.lock"))
    (root / "exports").mkdir()
    return root, brand_source


def render(project, platforms=("instagram",), baseline=None, **brand):
    """Render in a fresh job root. Returns the manifest (also written to <root>/JOB_MANIFEST.json)."""
    t0 = time.time(); root, brand_source = make_root(project, **brand)
    engine_src = _tree(WORKSPACE / "engine", skip=("fonts", "models", "__pycache__"))
    engine_job = _tree(root / "engine")
    cmd = [PY, "engine/adapter.py", "render", project] + sum([["--platform", p] for p in platforms], []) + (["--baseline", str(Path(baseline).resolve())] if baseline else [])
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", RS_HEAVY_LOCK=str(WORKSPACE / ".heavy_model.lock"))
    p = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    events = []
    for line in p.stdout.splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: pass
    done = next((e for e in reversed(events) if e.get("event") == "done"), {})
    outputs = []
    for o in done.get("outputs", []):
        qa = json.loads(Path(o["qa_report"]).read_text()) if o.get("qa_report") and Path(o["qa_report"]).is_file() else None
        outputs.append(dict(platform=o["platform"], path=str(Path(o["path"]).relative_to(root)), sha256=sha_file(o["path"]), bytes=os.path.getsize(o["path"]),
                            qa_passed=o.get("qa_passed"), qa={k: qa.get(k) for k in ("frames", "file_size", "loudness_lufs", "true_peak_db", "passed")} if qa else None,
                            checks={c["name"]: c.get("pass_", c.get("passed")) for c in (qa or {}).get("checks", [])}))
    proj = root / "projects" / project
    manifest = dict(format="ideaframe-engine-job@1", job=root.name, project=project, created=time.strftime("%Y-%m-%d %H:%M:%S"),
                    engine=dict(unchanged=engine_job == {k: v for k, v in engine_src.items() if "/" not in k and k.endswith((".py", ".json"))}, files=engine_job),
                    brand=brand_source, project_inputs={f: sha_file(proj / f) for f in ("project.json", "build/plan.json", "build/narration.json", "build/edit.mp4", "build/edit_audio.wav") if (proj / f).is_file()},
                    command=cmd[1:], exit_code=p.returncode, ok=bool(done.get("ok")), qa_passed=bool(done.get("qa_passed")),
                    errors=[e for e in events if e.get("event") == "error"], outputs=outputs, seconds=round(time.time() - t0, 1),
                    stderr_tail=p.stderr.strip().splitlines()[-5:] if p.returncode else [])
    (root / "JOB_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    manifest["root"] = str(root)
    return manifest
