"""Gate A2.2 - READ-ONLY check of a sentencepiece version that works with the locked protobuf 4.25.9.
Run on the Mac:  /opt/homebrew/bin/python3.12 tools/gate_a2_2_sp_check.py

Why: sentencepiece 0.2.3 (Lock B) ships sentencepiece_model_pb2.py that imports google.protobuf.runtime_version
(protobuf >= 5.26 only), but descript-audiotools requires protobuf < 5, so Lock B resolved protobuf 4.25.9.
The model's prompt tokenizer needs that file -> ImportError at step 8.

What it does (nothing is installed, no environment or file is changed):
  - reads PyPI metadata for sentencepiece 0.2.0, 0.2.1, 0.2.3 (release date, licence, macOS arm64 cp312 wheel + sha256)
  - fetches each wheel INTO MEMORY (about 1 MB each), checks its sha256, and reads only sentencepiece_model_pb2.py
  - imports that pb2 file from a temporary folder with the rs_tts Python (protobuf 4.25.9) and parses the model's own
    tokenizer.model from the rs_tts cache with it - this is exactly what failed at step 8
  - temporary folder removed; evidence in tests/acceptance/M4_gateA2_2/sp_check_<date_time>/"""
import hashlib, io, json, os, shutil, subprocess, sys, tempfile, time, urllib.request, zipfile, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateA2_2", "sp_check_" + time.strftime("%Y%m%d_%H%M%S"))
VPY = os.path.expanduser("~/.venvs/rs_tts/bin/python")
TOKM = glob.glob(os.path.expanduser("~/.cache/rs_tts_hf/hub/models--ai4bharat--indic-parler-tts/snapshots/660bc53c64ae83150613264111708a0465211237/tokenizer.model"))
VERSIONS = ["0.2.0", "0.2.1", "0.2.3"]
TEST = r'''
import sys, json; sys.path.insert(0, sys.argv[1])
import google.protobuf as gp
r = dict(protobuf=gp.__version__)
try:
    import sentencepiece_model_pb2 as m
    p = m.ModelProto(); p.ParseFromString(open(sys.argv[2], "rb").read())
    r.update(import_ok=True, pieces=len(p.pieces), model_type=int(p.trainer_spec.model_type))
except Exception as e: r.update(import_ok=False, error=f"{type(e).__name__}: {str(e)[:200]}")
print(json.dumps(r))
'''

def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "reel-studio-gateA2.2"}), timeout=60) as r:
        b = r.read(); return b if binary else json.loads(b)

def main():
    if not os.path.exists(VPY): sys.exit("rs_tts environment not found")
    if not TOKM: sys.exit("tokenizer.model not in the rs_tts cache")
    os.makedirs(OUT); res = {}
    for v in VERSIONS:
        d = get(f"https://pypi.org/pypi/sentencepiece/{v}/json"); info = d["info"]
        w = [f for f in d["urls"] if f["filename"].endswith(".whl") and "cp312" in f["filename"] and "macosx" in f["filename"] and "arm64" in f["filename"]]
        r = dict(released=min((f["upload_time"][:10] for f in d["urls"]), default="?"), licence=info.get("license_expression") or info.get("license") or "",
                 classifiers=[c for c in info.get("classifiers", []) if c.startswith("License")], requires_dist=info.get("requires_dist"))
        if not w: r["wheel"] = None; res[v] = r; continue
        f = w[0]; blob = get(f["url"], binary=True); sha = hashlib.sha256(blob).hexdigest()
        r.update(wheel=f["filename"], sha256=f["digests"]["sha256"], sha256_ok=sha == f["digests"]["sha256"], bytes=len(blob))
        pb2 = zipfile.ZipFile(io.BytesIO(blob)).read("sentencepiece/sentencepiece_model_pb2.py").decode()
        r["pb2_imports_runtime_version"] = "runtime_version" in pb2
        r["pb2_header"] = [l for l in pb2.splitlines() if "Protobuf Python Version" in l or l.startswith("from google")][:6]
        tmp = tempfile.mkdtemp(prefix="sp_check_")
        try:
            open(os.path.join(tmp, "sentencepiece_model_pb2.py"), "w").write(pb2)
            p = subprocess.run([VPY, "-I", "-c", TEST, tmp, TOKM[0]], capture_output=True, text=True, timeout=120)
            r["with_rs_tts_protobuf"] = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else {"error": p.stderr[-400:]}
        finally: shutil.rmtree(tmp, ignore_errors=True)
        res[v] = r
    json.dump(res, open(os.path.join(OUT, "sp_check.json"), "w"), indent=1)
    L = ["# sentencepiece vs protobuf 4.25.9 (read-only)", "", "| version | released | wheel sha256 ok | pb2 needs protobuf>=5.26 | works with rs_tts protobuf | licence |", "| --- | --- | --- | --- | --- | --- |"]
    for v, r in res.items():
        t = r.get("with_rs_tts_protobuf", {})
        L.append(f"| {v} | {r['released']} | {r.get('sha256_ok')} | {r.get('pb2_imports_runtime_version')} | "
                 f"{'yes, ' + str(t.get('pieces')) + ' pieces read' if t.get('import_ok') else 'NO ' + str(t.get('error', ''))[:80]} | {r['licence'][:30]} {r['classifiers']} |")
    L += ["", "Candidate hash lines (for approval only - not installed):"] + [f"sentencepiece=={v} --hash=sha256:{r['sha256']}" for v, r in res.items() if r.get("sha256")]
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L)); print(f"\nEvidence: {os.path.relpath(OUT, ROOT)}/")

if __name__ == "__main__":
    main()
