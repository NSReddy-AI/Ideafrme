"""M6 brand bridge (app/brand_bridge.py) from the command line. Only M6's own Brand Library is touched
(m5/.runtime/studio-ui/brand-library); brands/ is only read.

  ~/.venvs/reelstudio/bin/python -B tools/m6_brands.py plan                       what an import would register (no changes)
  ~/.venvs/reelstudio/bin/python -B tools/m6_brands.py import --owner "Name"      import every M4 brand not yet in the Library, as DRAFTS
  ~/.venvs/reelstudio/bin/python -B tools/m6_brands.py status                     Library brands and the rights state of their assets
  ~/.venvs/reelstudio/bin/python -B tools/m6_brands.py export <brand_id> <new folder>   rebuild an APPROVED brand for the engine

Rights are never granted by this tool: approving a brand needs the owner's own rights decision for each asset."""
import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "app"), str(ROOT / "m5")]
import brand_bridge as B                                   # noqa: E402
from visual_poster_studio.brands import Store              # noqa: E402


def m4_brands(): return sorted(p.parent for p in (ROOT / "brands").glob("*/brand.json"))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan"); sub.add_parser("status")
    i = sub.add_parser("import"); i.add_argument("--owner", required=True, help="who holds these brands (recorded as provenance)")
    e = sub.add_parser("export"); e.add_argument("brand_id"); e.add_argument("dest")
    a = ap.parse_args(); store = Store()
    if a.cmd == "plan":
        done = B.imported(store) if store.list().get("initialized") else {}
        for d in m4_brands():
            p = B.plan(d)
            print(json.dumps(dict(m4_brand_id=p["m4_brand_id"], already_imported=p["m4_brand_id"] in done, files=[(f["path"], f["kind"], f["bytes"]) for f in p["files"]],
                                  payload={k: v for k, v in p["payload"].items() if k != "notes"}), ensure_ascii=False, indent=1))
    elif a.cmd == "import":
        done = B.imported(store) if store.list().get("initialized") else {}
        for d in m4_brands():
            if d.name in done: print(json.dumps(dict(m4_brand_id=d.name, skipped="already imported", brand_id=done[d.name]))); continue
            print(json.dumps(B.import_brand(store, d, a.owner)))
    elif a.cmd == "status":
        lib = store.list()
        assets = {x["record"]["id"]: x for x in lib.get("assets", [])} if lib.get("initialized") else {}
        for b in lib.get("brands", []):
            r = b["record"]
            print(json.dumps(dict(brand_id=r["brand_id"], name=r["payload"]["name"], state=r["state"], revision=r["revision"],
                                  approval_current=b.get("approval_current"),
                                  rights={assets[i]["record"]["name"]: (assets[i]["rights"] or {}).get("status") for i in r["payload"]["asset_ids"] if i in assets}), ensure_ascii=False))
    else:
        print(json.dumps(B.export_engine_brand(store, a.brand_id, Path(a.dest)), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
