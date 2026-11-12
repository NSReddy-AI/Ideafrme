"""Render an M4 project in an isolated job root with the unchanged engine (app/engine_jobs.py).
  ~/.venvs/reelstudio/bin/python -B tools/m6_render_job.py <project> [--platform instagram ...] [--baseline tests/baseline_reel_002.json]
      [--library-brand <brand_id>]    use an APPROVED Brand Library brand instead of brands/<id>
Prints the job manifest. The project, brands/ and exports/ of M6 are not touched; everything lands in jobs/<job>/."""
import argparse, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "app"), str(ROOT / "m5")]
import engine_jobs                                            # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--platform", action="append"); ap.add_argument("--baseline")
ap.add_argument("--library-brand")
a = ap.parse_args()
brand = {}
if a.library_brand:
    from visual_poster_studio.brands import Store
    brand = dict(brand_store=Store(), brand_id=a.library_brand)
m = engine_jobs.render(a.project, platforms=tuple(a.platform or ["instagram"]), baseline=a.baseline, **brand)
print(json.dumps({k: v for k, v in m.items() if k != "engine"} | {"engine_unchanged": m["engine"]["unchanged"]}, ensure_ascii=False, indent=1))
sys.exit(0 if m["ok"] and m["qa_passed"] and m["engine"]["unchanged"] else 1)
