"""Read-only: lists what Reel Studio uses on this Mac (Python packages with licence metadata, tools, models, fonts)
and writes tools/deps_raw.json. Installs and changes nothing. Run:
  ~/.venvs/reelstudio/bin/python tools/dump_deps.py"""
import json, os, sys, shutil, subprocess, platform, hashlib, importlib.metadata as md
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def run(*a):
    try: return subprocess.run(a, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e: return f"ERROR {e}"
pk = []
for d in md.distributions():
    m = d.metadata
    pk.append(dict(name=m["Name"], version=d.version, license=(m.get("License") or "")[:200], license_expression=m.get("License-Expression"),
                   classifiers=[c for c in (m.get_all("Classifier") or []) if c.startswith("License")], home=m.get("Home-page"),
                   urls=m.get_all("Project-URL"), requires=d.requires))
tools = {}
for t in ("ffmpeg", "ffprobe", "node", "npx", "whisper", "brew"):
    p = shutil.which(t); tools[t] = dict(path=p)
tools["ffmpeg"]["version"] = run("ffmpeg", "-hide_banner", "-version").splitlines()[:3]
tools["node"]["version"] = run("node", "--version")
tools["hyperframes"] = dict(version=run("npx", "--no-install", "hyperframes", "--version"))
w = shutil.which("whisper")
if w:
    head = open(w, errors="ignore").readline().strip(); tools["whisper"]["python"] = head
    py = head[2:].strip() if head.startswith("#!") else None
    if py and os.path.exists(py.split()[0]):
        tools["whisper"]["packages"] = run(py.split()[0], "-c", "import importlib.metadata as m, json; print(json.dumps({d.metadata['Name']: [d.version, d.metadata.get('License') or ''] for d in m.distributions()}))")
brew = {}
for f in ("ffmpeg", "node", "libraqm", "python@3.12", "harfbuzz", "fribidi", "freetype"):
    brew[f] = run("brew", "list", "--versions", f)
files = []
for sub in ("engine/models", "engine/fonts"):
    for fn in sorted(os.listdir(os.path.join(ROOT, sub))):
        p = os.path.join(ROOT, sub, fn)
        if os.path.isfile(p): files.append(dict(path=f"{sub}/{fn}", bytes=os.path.getsize(p), sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()))
npm = run("npm", "ls", "-g", "--depth=0", "--json")
# speech / audio tools environment (separate Python) and model files outside the project
asr_py = os.path.expanduser("~/.venvs/rs_asr/bin/python"); asr = []
if os.path.exists(asr_py):
    code = ("import importlib.metadata as md, json; print(json.dumps([dict(name=d.metadata['Name'], version=d.version, license=(d.metadata.get('License') or '')[:120], "
            "license_expression=d.metadata.get('License-Expression'), classifiers=[c for c in (d.metadata.get_all('Classifier') or []) if c.startswith('License')]) for d in md.distributions()]))")
    try: asr = json.loads(run(asr_py, "-c", code).splitlines()[-1])
    except Exception: asr = []
tools["whisper-cli"] = dict(path=shutil.which("whisper-cli"), brew=run("brew", "list", "--versions", "whisper-cpp"))
dfb = os.path.expanduser("~/.cache/rs_tools/deep-filter"); tools["deep-filter"] = dict(path=dfb if os.path.exists(dfb) else None, version=run(dfb, "--version") if os.path.exists(dfb) else None)
ext = []
for pat in ("~/.cache/rs_asr/*.bin", "~/.cache/huggingface/hub/models--*"):
    import glob
    for f in sorted(glob.glob(os.path.expanduser(pat))):
        sz = os.path.getsize(f) if os.path.isfile(f) else sum(os.path.getsize(os.path.join(a, x)) for a, _, fs in os.walk(f) for x in fs)
        ext.append(dict(path=f.replace(os.path.expanduser("~"), "~"), bytes=sz))
out = dict(python=sys.version, executable=sys.executable, mac=platform.platform(), machine=platform.machine(),
           packages=sorted(pk, key=lambda x: x["name"].lower()), tools=tools, brew=brew, models_fonts=files, npm_global=npm,
           asr_packages=sorted(asr, key=lambda x: x["name"].lower()), external_models=ext)
p = os.path.join(ROOT, "tools", "deps_raw.json"); json.dump(out, open(p, "w"), indent=1)
print(f"{len(pk)} Reel Studio packages, {len(asr)} speech-tools packages, {len(files)} model/font files, {len(ext)} external models -> {p}")
