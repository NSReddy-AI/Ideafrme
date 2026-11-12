"""Gate A2 preparation - READ-ONLY dependency verification and lock proposal for Indic Parler-TTS (authorised 10 Nov 2026).
Run on the Mac:  ~/.venvs/reelstudio/bin/python tools/gate_a2_lock.py

It does NOT create environments, install packages, download model weights, log in anywhere or change existing files.
It only reads public metadata and writes new files into tests/acceptance/M4_gateA2/:
  1. pypi_torch_torchaudio.json - official PyPI metadata: release dates, macOS arm64 / Python 3.12 wheels, torchaudio's torch requirement.
  2. Two candidate locks, each resolved with `pip install --dry-run --report` (nothing installed):
       A = as resolved by the library (torch 2.15.0 + torchaudio 2.11.1)
       B = era-matched pair released with transformers 4.46.1 (torch 2.5.1 + torchaudio 2.5.1)
     lock_<A|B>_wheels.txt  (exact versions + sha256 hashes from PyPI)   and   git_pins.txt (GitHub sources pinned to a commit).
  3. lfs_check.txt - clones the two GitHub sources into a temporary folder WITHOUT Git LFS and checks that no file the
     packages install is an LFS pointer (temporary folder deleted afterwards).
  4. proposal.md - the summary table."""
import json, os, subprocess, sys, tempfile, urllib.request, shutil, time, platform

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateA2"); os.makedirs(OUT, exist_ok=True)
GIT = {"parler-tts": ("https://github.com/huggingface/parler-tts", "d108732cd57788ec86bc857d99a6cabd66663d68", "parler_tts"),
       "descript-audiotools": ("https://github.com/descriptinc/audiotools", "348ebf2034ce24e2a91a553e3171cb00c0c71678", "audiotools")}
SETS = {"A": {}, "B": {"torch": "2.5.1", "torchaudio": "2.5.1"}}
NO_LFS = {"GIT_LFS_SKIP_SMUDGE": "1", "GIT_CONFIG_COUNT": "3", "GIT_CONFIG_KEY_0": "filter.lfs.process", "GIT_CONFIG_VALUE_0": "",
          "GIT_CONFIG_KEY_1": "filter.lfs.smudge", "GIT_CONFIG_VALUE_1": "cat", "GIT_CONFIG_KEY_2": "filter.lfs.required", "GIT_CONFIG_VALUE_2": "false"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "reel-studio-gateA2"}), timeout=60) as r: return json.loads(r.read())

def head(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers={"User-Agent": "reel-studio-gateA2"}), timeout=30) as r:
            return int(r.headers.get("Content-Length") or 0)
    except Exception: return 0

def vkey(v):
    return tuple(int(p) if p.isdigit() else 0 for p in v.split("+")[0].split(".")[:3])

def mac_wheel(files):
    for f in files:
        n = f["filename"]
        if n.endswith(".whl") and "macosx" in n and "arm64" in n and ("cp312" in n or "py3-none" in n): return n, f["upload_time"][:10], f["digests"]["sha256"]
    return None, (files[0]["upload_time"][:10] if files else ""), ""

def pypi_meta():
    out = {}
    for name in ("torch", "torchaudio", "transformers"):
        d = get(f"https://pypi.org/pypi/{name}/json"); rel = {}
        for v, files in d["releases"].items():
            if not files or any(c.isalpha() for c in v.replace(".", "")): continue
            if vkey(v) < ((2, 4, 0) if name != "transformers" else (4, 46, 0)): continue
            if name == "transformers" and v != "4.46.1": continue
            w, date, sha = mac_wheel(files); rel[v] = dict(first_upload=date, mac_arm64_py312_wheel=w, sha256=sha)
            if name == "torchaudio":
                try: rel[v]["requires_dist"] = [r for r in (get(f"https://pypi.org/pypi/torchaudio/{v}/json")["info"].get("requires_dist") or []) if "torch" in r]
                except Exception as e: rel[v]["requires_dist"] = [f"error {e}"]
        out[name] = dict(latest=d["info"]["version"], requires_python=d["info"].get("requires_python"),
                         releases=dict(sorted(rel.items(), key=lambda kv: vkey(kv[0]))))
    json.dump(out, open(os.path.join(OUT, "pypi_torch_torchaudio.json"), "w"), indent=1)
    return out

def dry_run(tag, pins):
    rep = os.path.join(OUT, f"dryrun_{tag}.json"); tmp = tempfile.mkdtemp(prefix=f"gateA2{tag}_")
    reqs = [f"parler-tts @ git+{GIT['parler-tts'][0]}.git@{GIT['parler-tts'][1]}"] + [f"{k}=={v}" for k, v in pins.items()]
    cmd = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--no-cache-dir", "--quiet", "--report", rep] + reqs
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PIP_NO_CACHE_DIR="1", TMPDIR=tmp, **NO_LFS))
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode: return None, (r.stderr or r.stdout)[-1500:]
    d = json.load(open(rep)); wheels, gits, total = [], [], 0
    for it in d["install"]:
        m, di = it["metadata"], it["download_info"]
        if "vcs_info" in di: gits.append(f"{m['name']} @ git+{di['url']}@{di['vcs_info']['commit_id']}"); continue
        sha = di.get("archive_info", {}).get("hashes", {}).get("sha256") or di.get("archive_info", {}).get("hash", "").split("=")[-1]
        size = head(di["url"]); total += size
        wheels.append(dict(name=m["name"], version=m["version"], sha256=sha, url=di["url"], size=size))
    wheels.sort(key=lambda w: w["name"].lower())
    with open(os.path.join(OUT, f"lock_{tag}_wheels.txt"), "w") as f:
        f.write(f"# Gate A2 lock {tag} - macOS arm64, Python {platform.python_version()} - generated {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write("# install with: pip install --require-hashes --no-deps -r this file   (then the git_pins with --no-deps)\n")
        for w in wheels: f.write(f"{w['name']}=={w['version']} \\\n    --hash=sha256:{w['sha256']}\n")
    return dict(wheels=wheels, gits=gits, total=total, n=len(wheels) + len(gits)), None

def lfs_check():
    lines, ok = [], True
    for name, (url, commit, pkg) in GIT.items():
        tmp = tempfile.mkdtemp(prefix="gateA2lfs_"); env = dict(os.environ, **NO_LFS)
        try:
            subprocess.run(["git", "clone", "--quiet", "--no-checkout", url, tmp], check=True, env=env, capture_output=True)
            subprocess.run(["git", "-C", tmp, "checkout", "--quiet", commit], check=True, env=env, capture_output=True)
            files = subprocess.run(["git", "-C", tmp, "ls-files"], capture_output=True, text=True, check=True).stdout.split()
            ptr = [f for f in files if os.path.isfile(os.path.join(tmp, f)) and open(os.path.join(tmp, f), "rb").read(40).startswith(b"version https://git-lfs")]
            in_pkg = [f for f in ptr if f.startswith(pkg + "/")]
            attrs = open(os.path.join(tmp, ".gitattributes")).read().strip() if os.path.exists(os.path.join(tmp, ".gitattributes")) else "(none)"
            ok &= not in_pkg
            lines += [f"== {name} @ {commit}", f"   files: {len(files)}; LFS pointer files: {len(ptr)}; inside the installed package '{pkg}/': {len(in_pkg)}",
                      f"   .gitattributes: {attrs[:300]}"] + [f"   pointer: {p}" for p in ptr[:40]] + [f"   PACKAGE FILE IS LFS: {p}" for p in in_pkg]
        except subprocess.CalledProcessError as e:
            ok = False; lines.append(f"== {name}: clone/checkout failed: {(e.stderr or b'')[-400:]}")
        finally: shutil.rmtree(tmp, ignore_errors=True)
    lines.append("RESULT: " + ("no installed file is an LFS object - the no-LFS method is safe" if ok else "STOP - an installed file is an LFS object (or the check failed)"))
    open(os.path.join(OUT, "lfs_check.txt"), "w").write("\n".join(lines) + "\n")
    return ok, lines

def main():
    t0 = time.time(); print("Gate A2 verification (read-only; nothing will be installed)\n", flush=True)
    meta = pypi_meta(); print("1. PyPI metadata read", flush=True)
    res = {}
    for tag, pins in SETS.items():
        res[tag], err = dry_run(tag, pins); print(f"2. lock {tag}: " + (f"{res[tag]['n']} packages, {round(res[tag]['total'] / 1e6)} MB" if res[tag] else "FAILED"), flush=True)
        if err: open(os.path.join(OUT, f"dryrun_{tag}_error.txt"), "w").write(err)
    ok, lfs = lfs_check(); print("3. " + lfs[-1], flush=True)
    for tag in ("A", "B"):
        if res[tag]: open(os.path.join(OUT, "git_pins.txt"), "w").write("\n".join(res[tag]["gits"]) + "\n"); break
    ta, tb = meta["torchaudio"]["releases"], meta["torch"]["releases"]
    L = ["# Gate A2 dependency proposal - evidence", "", f"Generated {time.strftime('%Y-%m-%d %H:%M')} on {platform.platform()}, Python {platform.python_version()}. Read-only; {round(time.time() - t0)} s.", "",
         "## Official PyPI metadata", "", f"- torch latest: {meta['torch']['latest']} (requires Python {meta['torch']['requires_python']})",
         f"- torchaudio latest: {meta['torchaudio']['latest']}", "", "| version | torch first upload | torch mac arm64 py3.12 wheel | torchaudio first upload | torchaudio wheel | torchaudio needs |", "| --- | --- | --- | --- | --- | --- |"]
    for v in sorted(set(ta) | set(tb), key=vkey):
        a, b = tb.get(v, {}), ta.get(v, {})
        L.append(f"| {v} | {a.get('first_upload', '-')} | {'yes' if a.get('mac_arm64_py312_wheel') else 'no'} | {b.get('first_upload', '-')} | {'yes' if b.get('mac_arm64_py312_wheel') else 'no'} | {'; '.join(b.get('requires_dist', [])) or '-'} |")
    tf = meta["transformers"]["releases"].get("4.46.1", {}); L += ["", f"- transformers 4.46.1 first upload: {tf.get('first_upload')}", ""]
    for tag in ("A", "B"):
        r = res[tag]; L += [f"## Lock {tag}" + (" (torch 2.15.0 + torchaudio 2.11.1, as resolved)" if tag == "A" else " (torch 2.5.1 + torchaudio 2.5.1, era-matched)"), ""]
        if not r: L += ["Resolution FAILED - see dryrun_%s_error.txt" % tag, ""]; continue
        key = {w["name"].lower(): w for w in r["wheels"]}
        L += [f"- packages: {r['n']} ({len(r['wheels'])} wheels with sha256 + {len(r['gits'])} git commits); download {round(r['total'] / 1e6)} MB"]
        for k in ("torch", "torchaudio", "transformers", "tokenizers", "numpy", "protobuf", "huggingface-hub", "safetensors"):
            if k in key: L.append(f"- {k} {key[k]['version']} sha256 {key[k]['sha256'][:16]}... {round(key[k]['size'] / 1e6, 1)} MB")
        L += [f"- git: {g}" for g in r["gits"]] + [""]
    L += ["## Git LFS check", "", "```"] + lfs + ["```"]
    open(os.path.join(OUT, "proposal.md"), "w").write("\n".join(L) + "\n")
    print(f"\nDone. Evidence: tests/acceptance/M4_gateA2/ (proposal.md, lock_A_wheels.txt, lock_B_wheels.txt, git_pins.txt, lfs_check.txt)")

if __name__ == "__main__":
    main()
