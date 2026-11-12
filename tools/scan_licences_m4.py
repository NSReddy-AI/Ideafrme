"""Read-only licence scan for the M4 release (11 Nov 2026). Installs, downloads and changes nothing.
Reads licence metadata from what is actually installed on this Mac:
  - the three Python environments (~/.venvs/reelstudio, rs_tts, rs_asr) via their own importlib.metadata
  - the web app's npm tree (app/web/node_modules) and what is shipped in app/web/dist
  - model cards / licence files in the local Hugging Face caches, Ollama model licences (`ollama show --license`, local)
  - tool builds (FFmpeg configure flags, Homebrew formula licences from the local install receipts)
Writes tools/deps_m4.json. Run:  ~/.venvs/reelstudio/bin/python tools/scan_licences_m4.py"""
import os, json, re, glob, subprocess, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); HOME = os.path.expanduser("~")
def run(*a, timeout=60):
    try: return subprocess.run(a, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as e: return f"ERROR {e}"
PERMISSIVE = re.compile(r"\b(MIT|BSD|Apache|ISC|PSF|Python-2\.0|0BSD|Zlib|Unlicense|CC0|MIT-CMU|HPND|BSL-1\.0|OFL|Artistic|PIL)\b", re.I)
WEAK = re.compile(r"\b(MPL|LGPL|EPL|CDDL)\b", re.I); STRONG = re.compile(r"\b(GPL|AGPL)\b", re.I)
def classify(lic):
    if not lic or lic.strip() in ("UNKNOWN", ""): return "unknown"
    if STRONG.search(lic) and not re.search(r"LGPL", lic, re.I): return "strong-copyleft"
    if WEAK.search(lic): return "weak-copyleft"
    if PERMISSIVE.search(lic): return "permissive"
    return "check"
SCAN = r'''
import json, importlib.metadata as md
out = []
for d in md.distributions():
    m = d.metadata; cl = [c.split("::")[-1].strip() for c in (m.get_all("Classifier") or []) if c.startswith("License")]
    lic = m.get("License-Expression") or ((m.get("License") or "").splitlines()[0][:80] if m.get("License") else "") or "; ".join(cl)
    if len(lic) > 80 or lic.lower().startswith(("copyright", "the ", "this ")): lic = "; ".join(cl) or lic[:80]
    out.append(dict(name=m["Name"], version=d.version, license=lic.strip(), classifiers=cl))
print(json.dumps(sorted(out, key=lambda x: x["name"].lower())))
'''
R = dict(generated=run("date", "+%Y-%m-%d %H:%M").strip(), python={}, npm={}, models=[], ollama={}, tools={})
for env in ("reelstudio", "rs_tts", "rs_asr"):
    py = os.path.join(HOME, ".venvs", env, "bin", "python")
    pk = json.loads(run(py, "-I", "-c", SCAN, timeout=120) or "[]")
    for p in pk: p["class"] = classify(p["license"])
    R["python"][env] = pk
# npm tree (app/web) + what is shipped in the built app
nm = os.path.join(ROOT, "app", "web", "node_modules"); seen = {}
for pj in glob.glob(os.path.join(nm, "**", "package.json"), recursive=True):
    rel = os.path.relpath(pj, nm)
    if rel.count("node_modules") > 3 or "/test" in rel or "/fixtures" in rel: continue
    try: j = json.load(open(pj))
    except Exception: continue
    if not j.get("name") or not j.get("version") or os.path.dirname(rel).split("/")[-1] not in (j["name"].split("/")[-1],): continue
    lic = j.get("license") if isinstance(j.get("license"), str) else json.dumps(j.get("license") or j.get("licenses") or "")
    seen[f'{j["name"]}@{j["version"]}'] = dict(name=j["name"], version=j["version"], license=lic, class_=classify(lic))
web = json.load(open(os.path.join(ROOT, "app", "web", "package.json")))
R["npm"] = dict(packages=sorted(seen.values(), key=lambda x: x["name"]), shipped=sorted(web.get("dependencies", {})), build_only=sorted(web.get("devDependencies", {})))
# models: Hugging Face caches (model card licence in README front matter when cached) + vendored engine models + whisper.cpp
for hub in (os.path.join(HOME, ".cache", "huggingface", "hub"), os.path.join(HOME, ".cache", "rs_tts_hf", "hub")):
    for d in sorted(glob.glob(os.path.join(hub, "models--*"))):
        name = os.path.basename(d)[8:].replace("--", "/"); main = open(os.path.join(d, "refs", "main")).read().strip() if os.path.exists(os.path.join(d, "refs", "main")) else None
        card = next(iter(glob.glob(os.path.join(d, "snapshots", "*", "README.md"))), None); lic = None
        if card:
            m = re.search(r"^license:\s*(\S+)", open(card, errors="ignore").read(), re.M); lic = m.group(1) if m else None
        R["models"].append(dict(name=name, cache=hub.replace(HOME, "~"), revision_main=main, licence_from_card=lic, card_cached=bool(card),
                                size_gb=round(sum(os.path.getsize(f) for f in glob.glob(os.path.join(d, "blobs", "*"))) / 1e9, 2)))
for f in sorted(glob.glob(os.path.join(ROOT, "engine", "models", "*"))) + sorted(glob.glob(os.path.join(HOME, ".cache", "rs_asr", "*"))):
    R["models"].append(dict(name=os.path.basename(f), path=f.replace(HOME, "~"), size_gb=round(os.path.getsize(f) / 1e9, 3) if os.path.isfile(f) else None))
# Ollama (local server): model licences + digests
try:
    tags = json.loads(run("curl", "-s", "http://127.0.0.1:11434/api/tags") or "{}").get("models", [])
    for t in tags:
        lic = run("ollama", "show", t["name"], "--license", timeout=30)
        R["ollama"][t["name"]] = dict(digest=t["digest"], size_gb=round(t["size"] / 1e9, 2), licence_first_line=(lic.strip().splitlines() or [""])[0][:120],
                                      licence_mentions_apache=("Apache License" in lic), used_by_reel_studio=t["name"] in ("qwen3:14b", "qwen3:8b"))
except Exception as e: R["ollama"]["error"] = str(e)
# tools
R["tools"]["ffmpeg_configuration"] = [x for x in run("ffmpeg", "-hide_banner", "-buildconf").split() if x.startswith("--enable-")]
R["tools"]["ffmpeg_version"] = run("ffmpeg", "-version").splitlines()[0]
for f in ("ffmpeg", "node", "ollama", "whisper-cpp", "python@3.12"):
    rec = glob.glob(f"/opt/homebrew/Cellar/{f}/*/INSTALL_RECEIPT.json") + glob.glob(f"/opt/homebrew/Cellar/{f}/*/.brew/*.rb")
    R["tools"][f] = dict(installed=[os.path.basename(os.path.dirname(x)) for x in glob.glob(f"/opt/homebrew/Cellar/{f}/*/")],
                         licence=next((m.group(1) for r in rec if r.endswith(".rb") for m in [re.search(r'license\s+(.+)', open(r).read())] if m), None))
R["summary"] = {env: {c: sum(1 for p in pk if p["class"] == c) for c in ("permissive", "weak-copyleft", "strong-copyleft", "check", "unknown")} for env, pk in R["python"].items()}
R["summary"]["npm"] = {c: sum(1 for p in R["npm"]["packages"] if p["class_"] == c) for c in ("permissive", "weak-copyleft", "strong-copyleft", "check", "unknown")}
json.dump(R, open(os.path.join(ROOT, "tools", "deps_m4.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(R["summary"], indent=1))
for env, pk in R["python"].items():
    for p in pk:
        if p["class"] != "permissive": print(f"  {env}: {p['name']} {p['version']} | {p['license']} | {p['class']}")
for p in R["npm"]["packages"]:
    if p["class_"] != "permissive": print(f"  npm: {p['name']} {p['version']} | {p['license']} | {p['class_']}")
