"""Gate A1 - READ-ONLY dependency dry run for Indic Parler-TTS (approved 10 Nov 2026).
Run on the Mac:  ~/.venvs/reelstudio/bin/python tools/gate_a1_dryrun.py

What it does
  1. pip install --dry-run --ignore-installed --report : resolves the exact packages for THIS Mac (macOS arm64, Python 3.12).
     Nothing is installed; the reelstudio environment is not changed (dry run). pip may clone the two GitHub sources
     (parler-tts, descript-audiotools) into a temporary folder to read their requirements; the folder is deleted.
  2. For every resolved file: asks the server for its size (HTTP HEAD, nothing is downloaded) and reads the licence
     from the package metadata.
  3. Writes tests/acceptance/M4_gateA1/dryrun_report.json (pip's own report) and summary.md (the evidence table).
What it does NOT do: create environments, install packages, download model weights, log in to Hugging Face,
or change any existing file."""
import json, os, subprocess, sys, tempfile, urllib.request, time, platform, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateA1"); os.makedirs(OUT, exist_ok=True)
REQ = "parler-tts @ git+https://github.com/huggingface/parler-tts.git"
ALLOWED = ("mit", "bsd", "apache", "isc", "psf", "python software foundation", "public domain", "unlicense", "0bsd", "zlib",
           "gpl", "lgpl", "agpl", "gnu general public", "gnu lesser", "ofl", "hpnd", "historical permission")
RESTRICTED = ("non-commercial", "noncommercial", "cc-by-nc", "research", "proprietary", "commercial license", "openrail", "llama")

def licence_of(meta):
    lic = (meta.get("license_expression") or "").strip()
    if not lic:
        lic = (meta.get("license") or "").strip().splitlines()[0][:80] if meta.get("license") else ""
    cls = [c.split("::")[-1].strip() for c in meta.get("classifier", []) if c.startswith("License ::")]
    if (not lic or len(lic) > 60 or lic.upper() in ("UNKNOWN", "OTHER")) and cls: lic = "; ".join(cls)
    return lic or "not stated"

def verdict(lic):
    l = lic.lower()
    if any(r in l for r in RESTRICTED): return "RESTRICTED - stop"
    if l == "not stated": return "check by hand"
    if "mpl" in l or "mozilla" in l: return "review (MPL-2.0 is not in the policy list)"
    if any(a in l for a in ALLOWED): return "ok"
    return "check by hand"

def head_size(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "reel-studio-gateA1"})
        with urllib.request.urlopen(req, timeout=30) as r: return int(r.headers.get("Content-Length") or 0)
    except Exception: return 0

def main():
    t0 = time.time(); rep = os.path.join(OUT, "dryrun_report.json"); tmp = tempfile.mkdtemp(prefix="gateA1_")
    env = dict(os.environ, PIP_NO_CACHE_DIR="1", TMPDIR=tmp, GIT_LFS_SKIP_SMUDGE="1",
               # descript-audiotools keeps test files in Git LFS, which is not installed here. For THIS run only, git is told
               # not to run the LFS filter (the files stay as small pointers; they are not needed to read requirements).
               # Nothing is installed and the user's git settings are not changed.
               GIT_CONFIG_COUNT="3", GIT_CONFIG_KEY_0="filter.lfs.process", GIT_CONFIG_VALUE_0="",
               GIT_CONFIG_KEY_1="filter.lfs.smudge", GIT_CONFIG_VALUE_1="cat", GIT_CONFIG_KEY_2="filter.lfs.required", GIT_CONFIG_VALUE_2="false")
    cmd = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--no-cache-dir", "--quiet", "--report", rep, REQ]
    print("Gate A1 dry run (nothing will be installed):\n  " + " ".join(cmd[2:]), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode:
        print("DRY RUN FAILED - nothing was installed.\n" + (r.stderr or r.stdout)[-3000:]); sys.exit(1)
    data = json.load(open(rep)); rows, total, flags = [], 0, []
    for it in data.get("install", []):
        m = it.get("metadata", {}); url = it.get("download_info", {}).get("url", ""); git = "vcs_info" in it.get("download_info", {})
        size = 0 if git else head_size(url); total += size; lic = licence_of(m); v = verdict(lic)
        rows.append(dict(name=m.get("name"), version=m.get("version"), file=url.rsplit("/", 1)[-1] if not git else "git: " + url,
                         size_mb=round(size / 1e6, 1), licence=lic, verdict=v, requires_python=m.get("requires_python") or ""))
        if v != "ok": flags.append(f"{m.get('name')} {m.get('version')}: {lic} -> {v}")
    rows.sort(key=lambda x: -x["size_mb"])
    pins = {x["name"].lower(): x["version"] for x in rows}
    risks = ["descript-audiotools is installed from GitHub and its repository uses Git LFS; git-lfs is not on this Mac. "
             "A2 must either install git-lfs (a new tool - needs approval) or install with the LFS filter switched off as in this dry run"]
    if pins.get("transformers") != "4.46.1": risks.append(f"transformers resolved to {pins.get('transformers')} (library pins 4.46.1)")
    risks.append(f"transformers {pins.get('transformers')} vs transcription environment 5.22 -> a separate environment is required")
    if "torch" in pins: risks.append(f"torch {pins['torch']} for macOS arm64 / Python {platform.python_version()}")
    for heavy in ("tensorboard", "matplotlib", "ipython", "librosa", "numba", "llvmlite"):
        if heavy in pins: risks.append(f"{heavy} {pins[heavy]} is pulled in by descript-audiotools (not needed for speaking, adds size)")
    L = ["# Gate A1 - Indic Parler-TTS dependency dry run", "",
         f"Run {time.strftime('%Y-%m-%d %H:%M')} on {platform.platform()} with Python {platform.python_version()} ({sys.executable}). "
         f"pip {data.get('pip_version')}. Nothing was installed. {round(time.time() - t0)} s.", "",
         f"**Packages:** {len(rows)}  |  **Download (packages only):** {round(total / 1e6)} MB  |  "
         f"**Model files at A2:** 3.75 GB weights + about 12 MB tokenizer + description tokenizer (source read from the model config at A2)", "",
         "| Package | Version | Download (MB) | Licence | Verdict | File |", "| --- | --- | --- | --- | --- | --- |"]
    L += [f"| {x['name']} | {x['version']} | {x['size_mb']} | {x['licence']} | {x['verdict']} | {x['file']} |" for x in rows]
    L += ["", "## Needs attention", ""] + ([f"- {f}" for f in flags] or ["- none"])
    L += ["", "## Compatibility notes", ""] + [f"- {x}" for x in risks]
    L += ["", "Installed size is usually 2-3x the download for these packages; it is measured exactly at A2 if approved."]
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:6])); print(f"\n{len(flags)} licence item(s) need attention. Full table: tests/acceptance/M4_gateA1/summary.md")

if __name__ == "__main__":
    main()
