"""Quick self-test (about 20 s): settings are valid, and every brand can make a title page and frame.
Run: python3 tests/test_milestone2.py"""
import os, sys, subprocess, shutil, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "engine"))
import rs
from common import load, save
ok = True
errs = [e for e in rs.validate() if "handle not set" not in e]
print("settings:", "ok" if not errs else errs); ok &= not errs
for b in rs.brands():
    c = load(os.path.join(ROOT, "brands", b, "brand.json"))
    d = rs.new(b, c["default_platforms"][0], c["default_style"], f"_selftest_{b}")
    p = os.path.join(d, "project.json"); j = load(p)
    j.update(hook=dict(line1="Test line one", line2="Test two", line3="Test three!", tag_top="Tag", tag_bottom="Test"), title=["Self test", "headline"]); save(j, p)
    n = os.path.basename(d)
    for s in ("title.py", "frame.py"):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "engine", s), n], capture_output=True, text=True)
        good = r.returncode == 0; ok &= good; print(f"{b:20} {s:9}", "ok" if good else r.stderr[-400:])
    shutil.rmtree(d, ignore_errors=True)
print("\nALL PASSED" if ok else "\nSOME TESTS FAILED"); sys.exit(0 if ok else 1)
