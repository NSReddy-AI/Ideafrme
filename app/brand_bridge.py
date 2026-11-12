"""M6 step 5: M4 content brands (brands/<id>/) <-> M5 Brand Library, without changing either format.

Import (M4 -> Library), per brand:
  - every file of the brand folder that the engine or planner reads (brand.json, style-sheet.md, approved_hooks.json and
    each file brand.json names under "assets") is registered as an opaque, hash-pinned Library asset;
  - one more asset, the ENGINE PROFILE (JSON, format ideaframe-m4-engine-brand@1), records the M4 id and every file's
    relative path + SHA-256, so the exact folder can be rebuilt later;
  - a DRAFT brand version is saved: the Library's own fields are filled from brand.json (name, colours, fonts, rules,
    defaults) for people to read; the engine never uses them;
  - rights are recorded as "unknown" for every asset. Rights are legal statements only the owner can make, so the
    Library refuses to approve these drafts until the owner records rights for each asset.
Export (Library -> engine), for an APPROVED brand version only:
  - each pinned asset must still be cleared for commercial_design / reel (current rights, not expired or revoked);
  - the folder is rebuilt from the engine profile into a NEW destination folder, every file checked against its hash.
  It never writes into brands/ (the engine's own folder) and never overwrites anything.
The Library is used through its public Store.command / list API; reading asset bytes and rights uses its documented
v1 tables (m5/checkpoint/DATA_CONTRACTS_AND_COMPATIBILITY.md) read-only."""
import base64, hashlib, json, os, re
from pathlib import Path

PROFILE_FORMAT = "ideaframe-m4-engine-brand@1"
PROFILE_NAME = "engine-profile.json"
EXTRA_FILES = ("style-sheet.md", "approved_hooks.json")   # read by the planner when present
HEX = re.compile(r"#[0-9A-Fa-f]{6}\Z")
KIND = {".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image"}   # anything else (json, md, mp4) = template
UNKNOWN_RIGHTS = {"status": "unknown", "authority": "", "evidence": "", "scopes": [], "destinations": [], "expires": None}


def sha(data): return hashlib.sha256(data).hexdigest()


def _files(brand_dir: Path, brand: dict):
    """Relative paths the engine/planner read, in a stable order; refuses anything outside the brand folder."""
    paths = ["brand.json"] + [f for f in EXTRA_FILES if (brand_dir / f).is_file()]
    paths += sorted({p for p in brand.get("assets", {}).values() if p})
    root = brand_dir.resolve()
    for p in paths:
        full = (brand_dir / p).resolve()
        if not full.is_relative_to(root) or full.is_symlink() or not full.is_file(): raise ValueError(f"{brand_dir.name}: {p} is missing or outside the brand folder")
    return paths


def _colours(brand):
    seen, out = set(), []
    for v in [*brand.get("title", {}).values(), brand.get("captions", {}).get("color"), brand.get("captions", {}).get("highlight"), brand.get("frame", {}).get("border_color")]:
        if isinstance(v, str) and HEX.match(v) and v.lower() not in seen: seen.add(v.lower()); out.append(v.upper())
    return out[:16]


def plan(brand_dir: Path):
    """What an import would register, without touching the Library."""
    brand_dir = Path(brand_dir); raw = (brand_dir / "brand.json").read_bytes(); brand = json.loads(raw)
    files = []
    for p in _files(brand_dir, brand):
        data = (brand_dir / p).read_bytes()
        if not 0 < len(data) <= 8 * 1024 * 1024: raise ValueError(f"{brand_dir.name}: {p} is {len(data)} bytes; the Library takes 1 byte to 8 MiB")
        logo = p in {brand.get("assets", {}).get(k) for k in ("logo_left", "logo_right")}
        files.append(dict(path=p, label=p.replace("/", "__"), kind="logo" if logo else KIND.get(Path(p).suffix.lower(), "template"), sha256=sha(data), bytes=len(data)))
    profile = dict(format=PROFILE_FORMAT, m4_brand_id=brand_dir.name, files=[{k: f[k] for k in ("path", "sha256", "bytes")} for f in files])
    cap = brand.get("captions", {}); music = brand.get("music", {}); frame = brand.get("frame", {})
    notes = (f"Imported from M4 brands/{brand_dir.name} (brand.json SHA-256 {sha(raw)[:16]}). Handle {brand.get('handle', '-')}, "
             f"language {brand.get('language', '-')}. The engine uses only the exact files pinned in {PROFILE_NAME}; "
             f"the fields above are a readable summary. Change engine settings by editing the M4 brand and importing again.")
    payload = dict(
        name=brand["name"][:256], colors=_colours(brand),
        typography=dict(english="Inter Bold (engine captions and titles)", telugu="Noto Sans Telugu Black (engine captions and titles)"),
        mandatory_rules=[r[:256] for r in brand.get("rules", [])][:32],
        preferences=[p for p in [f"Default reel style: {brand.get('default_style')}" if brand.get("default_style") else None,
                                 f"Default platforms: {', '.join(brand.get('default_platforms', []))}" if brand.get("default_platforms") else None,
                                 f"Frame: {frame.get('type')}" if frame.get("type") else None,
                                 f"Captions: {cap.get('size')} px, colour {cap.get('color')}, highlight {cap.get('highlight')}" if cap else None,
                                 f"Music: {music.get('style')}, {music.get('bpm')} BPM" if music else None] if p],
        inspiration=[brand["category"][:256]] if brand.get("category") else [], notes=notes[:2000], asset_ids=[])
    return dict(m4_brand_id=brand_dir.name, files=files, profile=profile, payload=payload)


def _marker(m4_id): return f"Imported from M4 brands/{m4_id} "


def imported(store):
    """M4 brand ids that already have a Library brand (found by the import note)."""
    found = {}
    for b in store.list().get("brands", []):
        notes = b.get("record", {}).get("payload", {}).get("notes", "")
        m = re.match(r"Imported from M4 brands/([A-Za-z0-9_\-]+) ", notes)
        if m: found[m.group(1)] = b["record"]["brand_id"]
    return found


def import_brand(store, brand_dir: Path, owner: str):
    """Register the files + engine profile and save ONE draft brand. Refuses a brand that was already imported."""
    brand_dir = Path(brand_dir); p = plan(brand_dir)
    if p["m4_brand_id"] in imported(store): raise ValueError(f"{p['m4_brand_id']} is already in the Brand Library; edit that brand instead of importing twice")
    provenance = dict(owner=owner[:256], source=f"M4 brands/{p['m4_brand_id']}"[:256], license="unknown - to be confirmed by the owner")
    ids = []
    for f in p["files"]:
        data = (brand_dir / f["path"]).read_bytes()
        if sha(data) != f["sha256"]: raise ValueError(f"{f['path']} changed during import")
        r = store.command(dict(action="register_asset", name=f["label"][:128], kind=f["kind"], provenance=provenance,
                               data_base64=base64.b64encode(data).decode(), rights=UNKNOWN_RIGHTS))
        ids.append(r["asset_id"])
    prof = json.dumps(p["profile"], ensure_ascii=False, sort_keys=True, indent=2).encode()
    r = store.command(dict(action="register_asset", name=PROFILE_NAME, kind="template", provenance=dict(provenance, source="generated by IDEAFRAME M6 brand import"),
                           data_base64=base64.b64encode(prof).decode(), rights=UNKNOWN_RIGHTS))
    payload = dict(p["payload"], asset_ids=[r["asset_id"]] + ids)
    saved = store.command(dict(action="save", brand_id=None, expected_head=None, payload=payload))
    return dict(m4_brand_id=p["m4_brand_id"], brand_id=saved["record"]["brand_id"], head=saved["hash"], state=saved["record"]["state"],
                assets=len(payload["asset_ids"]), bytes=sum(f["bytes"] for f in p["files"]) + len(prof))


def export_engine_brand(store, brand_id: str, dest: Path):
    """Rebuild the M4 brand folder from the CURRENT APPROVED head into dest (must not exist yet). Returns a manifest."""
    dest = Path(dest)
    if dest.exists(): raise ValueError(f"{dest} already exists; export only into a new folder")
    with store.transaction() as c:
        row = c.execute("SELECT hash FROM heads WHERE id=?", (brand_id,)).fetchone()
        if not row: raise ValueError("brand not found")
        rec = store.get(c, row[0])
        if rec["state"] != "approved": raise ValueError("only an approved brand version can be exported to the engine")
        files = {}
        for b in rec["bindings"]:
            e = store.eligibility(c, b["asset_id"], "commercial_design", "reel")
            if not e["eligible"]: raise ValueError(f"asset {b['asset_id']} is not cleared for commercial reel use ({e['reason']})")
            if e["rights_hash"] != b["rights_hash"]: raise ValueError(f"asset {b['asset_id']}: rights changed since approval; approve the brand again")
            data = c.execute("SELECT data FROM blobs WHERE hash=?", (b["sha256"],)).fetchone()[0]
            if sha(data) != b["sha256"]: raise ValueError(f"asset {b['asset_id']} bytes do not match the approved hash")
            files[b["sha256"]] = (store.asset(c, b["asset_id"])["name"], bytes(data))
    profiles = [d for n, d in files.values() if n == PROFILE_NAME]
    if len(profiles) != 1: raise ValueError("approved brand has no single engine profile; it was not imported from M4")
    profile = json.loads(profiles[0])
    if profile.get("format") != PROFILE_FORMAT: raise ValueError("unknown engine profile format")
    plan_out = []
    for f in profile["files"]:
        rel = Path(f["path"])
        if rel.is_absolute() or ".." in rel.parts: raise ValueError(f"unsafe path in engine profile: {f['path']}")
        if f["sha256"] not in files: raise ValueError(f"{f['path']} is not among the approved assets")
        plan_out.append((rel, files[f["sha256"]][1]))
    dest.mkdir(parents=True)
    for rel, data in plan_out:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        with open(dest / rel, "xb") as out: out.write(data)
    manifest = dict(format="ideaframe-engine-brand-export@1", m4_brand_id=profile["m4_brand_id"], brand_id=brand_id, brand_version=row[0],
                    reviewer=rec["reviewer"], approved_at=rec["approved_at"], files={str(r): sha(d) for r, d in plan_out})
    with open(dest / "EXPORT_MANIFEST.json", "x", encoding="utf-8") as out: json.dump(manifest, out, ensure_ascii=False, indent=2)
    return manifest
