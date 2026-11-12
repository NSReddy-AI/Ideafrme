"""Gate A2.2 - install Indic Parler-TTS in an ISOLATED environment from the verified Lock B (approved 10 Nov 2026).
Run on the Mac with Homebrew Python 3.12 (NOT a Reel Studio environment):
  cd "/Users/Nadish/projects/AI Video Editor./Reel Studio_dev"
  HF_TOKEN="$(security find-generic-password -a "$USER" -s AI_REEL_STUDIO_HF_READ -w)" /opt/homebrew/bin/python3.12 tools/gate_a2_2_install.py

Steps (each one STOPS on failure; no version is ever changed automatically; nothing is deleted):
  1 pre-checks         disk >= 10 GB free; ~/.venvs/rs_tts must not exist; fingerprints of reelstudio + rs_asr environments
                       and of the original Reel Studio folder
  2 environment        create ~/.venvs/rs_tts from this Python (3.12.16)
  3 packages           pip --require-hashes --no-deps from lock_B_wheels.txt (93 wheels + 2 source archives, sha256 enforced)
  4 git packages       parler-tts + descript-audiotools at the pinned commits, --no-deps, --no-build-isolation, Git LFS filter off
  4b Lock B.1          sentencepiece 0.2.3 -> 0.2.0 (approved), hash-checked; any other difference stops
  5 consistency        pip check; installed set == Lock B.1 exactly; licences re-read (allowed: MIT/BSD/Apache/ISC/PSF/MPL-2.0/GPL family)
  6 smoke test         imports + versions + numpy interop + Apple GPU check, before any model download
  7 download           model @ 660bc53c... and the 4 flan-t5-large tokenizer files @ 0613663d... into a SEPARATE cache
                       ~/.cache/rs_tts_hf (the transcription model cache is not touched); total download <= 4.5 GB
  8 offline proof      HF_HUB_OFFLINE=1 + every outside network connection blocked inside the process; load, speak one Telugu
                       sentence on CPU; peak memory <= 8 GB
  9 samples            2 voices (Prakash, Lalitha) x 2 styles (News, Documentary) - offline - for YOUR review only
 10 isolation proof    fingerprints from step 1 unchanged; bash checkpoint.sh matches the reel_002 baseline
Evidence: tests/acceptance/M4_gateA2_2/<date_time>/ (summary.md, log.txt, json files, samples/*.wav). The token is never written."""
import hashlib, json, os, re, platform, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
VENV = os.path.join(HOME, ".venvs", "rs_tts")
VPY = os.path.join(VENV, "bin", "python")
HF_HOME = os.path.join(HOME, ".cache", "rs_tts_hf")
LOCK = os.path.join(ROOT, "tests", "acceptance", "M4_gateA2", "lock_B1_wheels.txt")   # Lock B + the one approved change below
APPROVED_CHANGES = {"sentencepiece": ("0.2.3", "0.2.0")}   # approved 10 Nov 2026 (evidence M4_gateA2_2/sp_check_20261110_154131)
GITS = [("parler-tts", "https://github.com/huggingface/parler-tts.git", "d108732cd57788ec86bc857d99a6cabd66663d68"),
        ("descript-audiotools", "https://github.com/descriptinc/audiotools", "348ebf2034ce24e2a91a553e3171cb00c0c71678")]
MODEL, MODEL_REV = "ai4bharat/indic-parler-tts", "660bc53c64ae83150613264111708a0465211237"
TOK, TOK_REV = "google/flan-t5-large", "0613663d0d48ea86ba8cb3d7a44f0f65dc596a2a"
TOK_FILES = ["tokenizer_config.json", "special_tokens_map.json", "spiece.model", "tokenizer.json"]
MODEL_FILES = ["config.json", "generation_config.json", "preprocessor_config.json", "special_tokens_map.json",
               "tokenizer.json", "tokenizer.model", "tokenizer_config.json", "model.safetensors"]
WATCH = {"reelstudio_env": os.path.join(HOME, ".venvs", "reelstudio"), "rs_asr_env": os.path.join(HOME, ".venvs", "rs_asr"),
         "original_Reel_Studio": os.path.join(os.path.dirname(ROOT), "Reel Studio")}
NO_LFS = {"GIT_LFS_SKIP_SMUDGE": "1", "GIT_CONFIG_COUNT": "3", "GIT_CONFIG_KEY_0": "filter.lfs.process", "GIT_CONFIG_VALUE_0": "",
          "GIT_CONFIG_KEY_1": "filter.lfs.smudge", "GIT_CONFIG_VALUE_1": "cat", "GIT_CONFIG_KEY_2": "filter.lfs.required", "GIT_CONFIG_VALUE_2": "false"}
ALLOWED = ("mit", "bsd", "apache", "isc", "psf", "python software foundation", "mpl", "mozilla", "public domain", "unlicense", "0bsd",
           "zlib", "hpnd", "historical permission", "gpl", "gnu", "cc0", "matplotlib", "boost", "bsl-1.0")
LIMIT_DL, LIMIT_MEM, MIN_FREE = 4.5e9, 8e9, 10e9
SENTENCE = "అక్కచెల్లెమ్మలకు ముప్పై ఒక్క లక్షల ఇళ్ల పట్టాలు ఇచ్చారు."
SAMPLE = "అక్కచెల్లెమ్మలకు ముప్పై ఒక్క లక్షల ఇళ్ల పట్టాలు. సొంతింటి కల నెరవేర్చేలా పదిహేడు వేల జగనన్న కాలనీలు. పేదవాడి ఆరోగ్యానికి పదివేల విలేజ్ క్లినిక్‌లు."
STYLES = {"news": "speaks in a clear, neutral and authoritative news-reading tone at a moderate, measured pace, with very little emotion.",
          "documentary": "speaks in a natural, warm and gently expressive documentary narration style at a slightly slow pace."}
QUALITY = " The recording is of very high quality, with the speaker's voice sounding clear and very close up, with no background noise."

RESUME = "--resume" in sys.argv   # re-use ~/.venvs/rs_tts from an earlier run: steps 2-4 skipped, step 5 re-verifies it EXACTLY
OUT = os.path.join(ROOT, "tests", "acceptance", "M4_gateA2_2", time.strftime("%Y%m%d_%H%M%S"))
LOG, RES = [], {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "steps": {}}

class Stop(Exception): pass

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"; print(line, flush=True); LOG.append(line)

LAST = {}
def run(cmd, env=None, cwd=None, timeout=3600):
    e = dict(os.environ, **(env or {})); e.pop("HF_TOKEN", None) if "HF_TOKEN" not in (env or {}) else None
    r = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=cwd, timeout=timeout)
    LAST.update(stdout=r.stdout or "", stderr=r.stderr or "")
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def result_json(tag):
    """The child's JSON result = last stdout line that is a JSON object. stdout/stderr are saved as <tag>.log (token scrubbed)."""
    tok = os.environ.get("HF_TOKEN") or "\0"
    open(os.path.join(OUT, f"{tag}.log"), "w").write(("== stdout\n" + LAST["stdout"] + "\n== stderr\n" + LAST["stderr"]).replace(tok, "***"))
    for line in reversed(LAST["stdout"].strip().splitlines()):
        if line.startswith("{"):
            try: return json.loads(line)
            except ValueError: pass
    raise Stop(f"{tag}: no result line from the child process (see {tag}.log)")

def warnings_of(): return [l[:300] for l in LAST["stderr"].splitlines() if "warn" in l.lower()][:20]

def fingerprint(path):
    """Fast manifest of a folder: every file's relative path, size and modification time -> one sha256."""
    if not os.path.exists(path): return None
    h, n = hashlib.sha256(), 0
    for dp, dn, fn in os.walk(path):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            try: st = os.lstat(p)
            except OSError: continue
            h.update(f"{os.path.relpath(p, path)}|{st.st_size}|{int(st.st_mtime)}\n".encode()); n += 1
    return {"files": n, "sha256": h.hexdigest()}

def norm(n): return re.sub(r"[-_.]+", "-", n).lower()

def lock_set():
    out = {}
    for line in open(LOCK):
        line = line.strip()
        if "==" in line and not line.startswith("#"):
            n, v = line.split(" ")[0].split("=="); out[norm(n)] = v
    return out

# ----------------------------------------------------------------------------------------------------------- steps
def step1():
    if sys.version_info[:3] != (3, 12, 16): raise Stop(f"run with Homebrew Python 3.12.16, this is {platform.python_version()}")
    if sys.prefix != sys.base_prefix: raise Stop("this is a virtual environment - run with /opt/homebrew/bin/python3.12")
    if os.path.exists(VENV) and not RESUME: raise Stop(f"{VENV} already exists - nothing will be changed")
    if RESUME and not os.path.exists(VPY): raise Stop("--resume given but ~/.venvs/rs_tts does not exist")
    if not os.path.exists(LOCK): raise Stop("Lock B file missing")
    free = shutil.disk_usage(HOME).free
    if free < MIN_FREE: raise Stop(f"only {free / 1e9:.1f} GB free (need 10 GB)")
    if not os.environ.get("HF_TOKEN"): raise Stop("no token (Keychain item AI_REEL_STUDIO_HF_READ)")
    fp = {k: fingerprint(p) for k, p in WATCH.items()}
    for k, v in fp.items(): log(f"fingerprint {k}: {v['files'] if v else 'not present'} files")
    return dict(free_gb=round(free / 1e9, 1), python=sys.executable, fingerprints=fp, lock_sha256=hashlib.sha256(open(LOCK, "rb").read()).hexdigest())

def step2():
    rc, out = run([sys.executable, "-m", "venv", VENV])
    if rc: raise Stop("could not create the environment:\n" + out[-800:])
    rc, out = run([VPY, "-c", "import sys,ssl;print(sys.version.split()[0])"])
    if rc or out.strip() != "3.12.16": raise Stop("new environment is not Python 3.12.16")
    _, pipv = run([VPY, "-m", "pip", "--version"])
    return dict(path=VENV, pip=pipv.strip())

def lock_entries():
    """Lock B as [(normalised name, 'name==ver \\\n    --hash=sha256:...')] - the lines are used verbatim, hashes untouched."""
    lines, out = open(LOCK).read().splitlines(), []
    for i, l in enumerate(lines):
        if "==" in l and not l.startswith("#"):
            out.append((norm(l.split(" ")[0].split("==")[0]), l + "\n" + lines[i + 1] + "\n"))
    return out

def step3():
    # 93 entries are wheels; argbind 0.3.9 and randomname 0.2.1 exist only as source archives on PyPI (seen in dryrun_B.json).
    # Wheels go first (--only-binary). The two source archives are then built from the SAME hash-locked lines with the
    # locked setuptools already in the environment (--no-build-isolation), so no unpinned build tool is fetched.
    rep = json.load(open(os.path.join(os.path.dirname(LOCK), "dryrun_B.json")))
    src = {norm(it["metadata"]["name"]) for it in rep["install"] if "vcs_info" not in it["download_info"] and not it["download_info"]["url"].endswith(".whl")}
    ent = lock_entries(); whl = [t for n, t in ent if n not in src]; sd = [t for n, t in ent if n in src]
    if {n for n, _ in ent if n in src} != src: raise Stop(f"source archives {sorted(src)} not all in Lock B")
    fw, fs = os.path.join(OUT, "lock_B_part1_wheels.txt"), os.path.join(OUT, "lock_B_part2_source.txt")
    open(fw, "w").write("".join(whl)); open(fs, "w").write("".join(sd))
    rc, out = run([VPY, "-m", "pip", "install", "--require-hashes", "--no-deps", "--only-binary", ":all:", "--no-cache-dir", "-r", fw])
    open(os.path.join(OUT, "pip_wheels.log"), "w").write(out)
    if rc: raise Stop("hash-checked wheel install failed (see pip_wheels.log):\n" + out[-1200:])
    rc, out = run([VPY, "-m", "pip", "install", "--require-hashes", "--no-deps", "--no-binary", ":all:", "--no-build-isolation", "--no-cache-dir", "-r", fs])
    open(os.path.join(OUT, "pip_source.log"), "w").write(out)
    if rc: raise Stop("hash-checked source install failed (see pip_source.log):\n" + out[-1200:])
    return dict(wheels=len(whl), source_archives=sorted(src), total=len(ent))

def step4():
    for name, url, commit in GITS:
        rc, out = run([VPY, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "--no-cache-dir", f"{name} @ git+{url}@{commit}"], env=NO_LFS)
        open(os.path.join(OUT, f"pip_{name}.log"), "w").write(out)
        if rc: raise Stop(f"{name} install failed:\n" + out[-1200:])
    return dict(git=[f"{n}@{c[:12]}" for n, _, c in GITS])

def step4b():
    """Bring an earlier Lock B install to Lock B.1: only versions listed in APPROVED_CHANGES may change; anything else stops."""
    _, frz = run([VPY, "-m", "pip", "freeze", "--all"]); got = {norm(l.split("==")[0]): l.split("==")[1] for l in frz.splitlines() if "==" in l and " @ " not in l}
    want = lock_set(); todo = []
    for n in sorted(set(want) & set(got)):
        if want[n] == got[n]: continue
        if n in APPROVED_CHANGES and APPROVED_CHANGES[n] == (got[n], want[n]): todo.append(n); continue
        raise Stop(f"{n}: installed {got[n]}, Lock B.1 wants {want[n]} - not an approved change")
    if not todo: return dict(changed=[], note="environment already matches Lock B.1")
    f = os.path.join(OUT, "lock_B1_change.txt"); open(f, "w").write("".join(t for n, t in lock_entries() if n in todo))
    rc, out = run([VPY, "-m", "pip", "install", "--require-hashes", "--no-deps", "--only-binary", ":all:", "--no-cache-dir", "-r", f])
    open(os.path.join(OUT, "pip_lock_B1_change.log"), "w").write(out)
    if rc: raise Stop("approved Lock B.1 change failed (see pip_lock_B1_change.log):\n" + out[-1200:])
    return dict(changed=[f"{n} {got[n]} -> {want[n]}" for n in todo])

def step5():
    rc, out = run([VPY, "-m", "pip", "check"]); chk = out.strip()
    _, frz = run([VPY, "-m", "pip", "freeze", "--all"]); open(os.path.join(OUT, "pip_freeze.txt"), "w").write(frz)
    want = lock_set(); got = {}
    for l in frz.splitlines():
        if "==" in l and " @ " not in l: n, v = l.split("=="); got[norm(n)] = v
    extra = sorted(set(got) - set(want) - {"pip"}); missing = sorted(set(want) - set(got)); diff = sorted(k for k in set(want) & set(got) if want[k] != got[k])
    gits_ok = all(c in frz for _, _, c in GITS)
    code = ("import json,importlib.metadata as m\nout={}\nfor d in m.distributions():\n md=d.metadata; l=md.get('License-Expression') or ''\n"
            " if not l or len(l)>80: l=(md.get('License') or '').strip().splitlines()[0][:80] if md.get('License') else ''\n"
            " c=[x.split('::')[-1].strip() for x in (md.get_all('Classifier') or []) if x.startswith('License ::')]\n"
            " out[md['Name']]={'version':md['Version'],'licence':l,'classifiers':c}\nprint(json.dumps(out))")
    rc2, lj = run([VPY, "-c", code]); lic = result_json("licence_read") if rc2 == 0 else {}
    open(os.path.join(OUT, "licences.json"), "w").write(json.dumps(lic, indent=1))
    known = {"parler-tts": "Apache-2.0 (repository LICENSE, checked at A1)", "parler_tts": "Apache-2.0 (repository LICENSE, checked at A1)",
             "descript-audiotools": "MIT (repository)", "cycler": "BSD-3-Clause", "kiwisolver": "BSD-3-Clause", "matplotlib": "Matplotlib licence (PSF-based)"}
    bad = []
    for n, d in lic.items():
        text = " ".join([d["licence"]] + d["classifiers"]).lower()
        if n.lower() in known or any(a in text for a in ALLOWED): continue
        bad.append(f"{n} {d['version']}: '{d['licence'][:60]}' {d['classifiers']}")
    r = dict(pip_check=chk, extra=extra, missing=missing, version_diff=diff, git_pinned=gits_ok, licence_unknown=bad)
    if rc: raise Stop(f"pip check failed: {chk[-600:]}")
    if extra or missing or diff or not gits_ok: raise Stop(f"installed set differs from Lock B.1: extra={extra} missing={missing} changed={diff} git_ok={gits_ok}")
    if bad: raise Stop("licence not on the approved list: " + "; ".join(bad))
    return r

SMOKE = r'''
import json, numpy, torch, torchaudio, transformers, parler_tts, soundfile, sentencepiece
from sentencepiece import sentencepiece_model_pb2   # failed with 0.2.3 + protobuf 4.25.9 (Lock B); must work with Lock B.1
x = torch.from_numpy(numpy.arange(6, dtype=numpy.float32)).reshape(2, 3)
mps = torch.backends.mps.is_available(); y = None
if mps: y = float((x.to("mps") * 2).sum().cpu())
print(json.dumps(dict(torch=torch.__version__, torchaudio=torchaudio.__version__, transformers=transformers.__version__,
      numpy=numpy.__version__, sentencepiece=sentencepiece.__version__, parler_tts=getattr(parler_tts, "__version__", "?"), numpy_interop=float(x.sum()) == 15.0, mps=mps, mps_op=y)))
'''
def step6():
    rc, out = run([VPY, "-c", SMOKE])
    if rc: open(os.path.join(OUT, "smoke.log"), "w").write(out); raise Stop("smoke test failed (no version is changed automatically):\n" + out[-1500:])
    d = result_json("smoke"); d["stderr_warnings"] = warnings_of()
    want = {"torch": "2.5.1", "torchaudio": "2.5.1", "transformers": "4.46.1", "sentencepiece": "0.2.0"}
    wrong = {k: d[k] for k, v in want.items() if not d[k].startswith(v)}
    if wrong or not d["numpy_interop"]: raise Stop(f"smoke test: wrong versions {wrong} or numpy interop failed")
    return d

DL = r'''
import json, os
from huggingface_hub import hf_hub_download
out = {}
for repo, rev, files in json.loads(os.environ["RS_DL"]):
    for f in files:
        p = hf_hub_download(repo, f, revision=rev, token=os.environ["HF_TOKEN"])
        out[f"{repo}/{f}"] = dict(path=p, bytes=os.path.getsize(os.path.realpath(p)))
print(json.dumps(out))
'''
def step7():
    plan = [[MODEL, MODEL_REV, [f for f in MODEL_FILES if f != "model.safetensors"]], [TOK, TOK_REV, TOK_FILES], [MODEL, MODEL_REV, ["model.safetensors"]]]
    small = [[MODEL, MODEL_REV, plan[0][2]], [TOK, TOK_REV, TOK_FILES]]
    env = {"HF_HOME": HF_HOME, "HF_TOKEN": os.environ["HF_TOKEN"], "HF_HUB_DISABLE_TELEMETRY": "1"}
    rc, out = run([VPY, "-c", DL], env=dict(env, RS_DL=json.dumps(small)))
    if rc: raise Stop("small-file download failed:\n" + out[-800:].replace(os.environ["HF_TOKEN"], "***"))
    got = result_json("download_small"); log("small files done; downloading the 3.75 GB model file (this takes a while)...")
    rc, out = run([VPY, "-c", DL], env=dict(env, RS_DL=json.dumps([plan[2]])), timeout=7200)
    if rc: raise Stop("model download failed:\n" + out[-800:].replace(os.environ["HF_TOKEN"], "***"))
    got.update(result_json("download_model"))
    total = sum(v["bytes"] for v in got.values()) + 223_000_000
    if total > LIMIT_DL: raise Stop(f"download {total / 1e9:.2f} GB is over the 4.5 GB ceiling")
    if any("ylacombe" in k for k in got): raise Stop("something was fetched from ylacombe/dac_44khz")
    return dict(files={k: v["bytes"] for k, v in got.items()}, total_with_packages_gb=round(total / 1e9, 3), cache=HF_HOME)

SPEAK = r'''
import json, os, resource, socket, sys, time
_real = socket.socket.connect
def _guard(self, addr):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in ("127.0.0.1", "::1", "localhost"): raise RuntimeError(f"BLOCKED network attempt to {host}")
    return _real(self, addr)
socket.socket.connect = _guard
import torch, soundfile
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
cfg = json.loads(os.environ["RS_SPEAK"]); t0 = time.time()
model = ParlerTTSForConditionalGeneration.from_pretrained(cfg["model"], revision=cfg["model_rev"]).to("cpu").eval()
tok = AutoTokenizer.from_pretrained(cfg["model"], revision=cfg["model_rev"])
dtok = AutoTokenizer.from_pretrained(cfg["tok"], revision=cfg["tok_rev"])
load_s = time.time() - t0; res = []
for job in cfg["jobs"]:
    torch.manual_seed(1234); t1 = time.time()
    d = dtok(job["desc"], return_tensors="pt"); p = tok(job["text"], return_tensors="pt")
    with torch.no_grad():
        g = model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask, prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
    a = g.cpu().numpy().squeeze(); soundfile.write(job["out"], a, model.config.sampling_rate)
    res.append(dict(out=os.path.basename(job["out"]), audio_s=round(len(a) / model.config.sampling_rate, 2), synth_s=round(time.time() - t1, 1)))
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss   # bytes on macOS
print(json.dumps(dict(load_s=round(load_s, 1), jobs=res, peak_rss_bytes=peak, sampling_rate=model.config.sampling_rate)))
'''
def speak(jobs, tag):
    env = {"HF_HOME": HF_HOME, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1",
           "RS_SPEAK": json.dumps(dict(model=MODEL, model_rev=MODEL_REV, tok=TOK, tok_rev=TOK_REV, jobs=jobs))}
    rc, out = run([VPY, "-c", SPEAK], env=env, timeout=7200)
    if rc:
        open(os.path.join(OUT, f"{tag}.log"), "w").write(out)
        raise Stop(("network was attempted while offline: " if "BLOCKED network" in out else "offline inference failed: ") + out[-1500:])
    return dict(result_json(tag), stderr_warnings=warnings_of())

def step8():
    os.makedirs(os.path.join(OUT, "samples"), exist_ok=True)
    r = speak([dict(text=SENTENCE, desc="Prakash" + " " + STYLES["news"] + QUALITY, out=os.path.join(OUT, "samples", "offline_proof_prakash_news.wav"))], "offline_proof")
    if r["peak_rss_bytes"] > LIMIT_MEM: raise Stop(f"peak memory {r['peak_rss_bytes'] / 1e9:.2f} GB is over the 8 GB limit")
    return dict(r, peak_gb=round(r["peak_rss_bytes"] / 1e9, 2), network="blocked in-process + HF_HUB_OFFLINE=1; no attempt made")

def step9():
    jobs = [dict(text=SAMPLE, desc=f"{v} {STYLES[s]}{QUALITY}", out=os.path.join(OUT, "samples", f"sample_{v.lower()}_{s}.wav"))
            for v in ("Prakash", "Lalitha") for s in ("news", "documentary")]
    r = speak(jobs, "samples")
    if r["peak_rss_bytes"] > LIMIT_MEM: raise Stop(f"peak memory {r['peak_rss_bytes'] / 1e9:.2f} GB is over the 8 GB limit")
    return dict(r, peak_gb=round(r["peak_rss_bytes"] / 1e9, 2), script=SAMPLE, note="draft sample text for review; numbers written as Telugu words")

def step10(before):
    after = {k: fingerprint(p) for k, p in WATCH.items()}
    changed = [k for k in WATCH if before.get(k) != after.get(k)]
    if changed: raise Stop(f"isolation broken - changed: {changed}")
    log("running checkpoint.sh (reel_002 baseline, about 2 minutes)...")
    rc, out = run(["bash", "checkpoint.sh"], cwd=ROOT, timeout=1800)
    open(os.path.join(OUT, "checkpoint.txt"), "w").write(out)
    if rc or "CHECKPOINT DONE" not in out or "FAIL" in out: raise Stop("checkpoint.sh did not pass (see checkpoint.txt)")
    return dict(fingerprints_unchanged=True, checkpoint="passed (checkpoint.txt)")

def write(final):
    RES["final"] = final; RES["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    open(os.path.join(OUT, "log.txt"), "w").write("\n".join(LOG) + "\n")
    json.dump(RES, open(os.path.join(OUT, "results.json"), "w"), indent=1, ensure_ascii=False)
    L = ["# Gate A2.2 - install + offline proof", "", f"{RES['started']} -> {RES['finished']}  |  FINAL: **{final}**", ""]
    for k, v in RES["steps"].items(): L.append(f"- **{k}**: {json.dumps(v, ensure_ascii=False)[:600]}")
    if "stop" in RES: L += ["", f"**STOPPED:** {RES['stop']}", "", "Nothing was deleted or rolled back; the environment stays as it is for inspection."]
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")

def main():
    if os.path.exists(OUT): print("evidence folder exists - wait a second and run again"); sys.exit(2)
    os.makedirs(OUT); before = None
    steps = [("1 pre-checks", step1), ("2 environment", step2), ("3 wheels (hash-checked)", step3), ("4 git packages", step4),
             ("4b Lock B.1 change", step4b), ("5 consistency + licences", step5), ("6 smoke test", step6), ("7 download", step7), ("8 offline proof", step8),
             ("9 samples", step9), ("10 isolation proof", None)]
    if RESUME:
        steps = [x for x in steps if x[0][:2] not in ("2 ", "3 ", "4 ")]   # 4b stays
        RES["resumed"] = "steps 2-4 (environment + hash-checked install) were done by an earlier run; step 5 re-verifies the installed set; isolation fingerprints are re-taken at the start of this run (first run printed reelstudio 8870, rs_asr 32652, original 127 files)"
        log("RESUME: re-using ~/.venvs/rs_tts - nothing is re-installed or changed; step 5 re-checks it against Lock B")
    try:
        for name, fn in steps:
            log(f"STEP {name} ...")
            r = step10(before) if fn is None else fn()
            if name.startswith("1 "): before = r["fingerprints"]
            RES["steps"][name] = r; log(f"STEP {name}: ok")
        write("PASS"); log(f"FINAL: PASS - evidence {os.path.relpath(OUT, ROOT)}/summary.md")
    except Stop as e:
        RES["stop"] = str(e).replace(os.environ.get("HF_TOKEN", "\0") or "\0", "***")
        write("STOP"); log(f"STOP: {RES['stop'][:800]}"); log(f"evidence {os.path.relpath(OUT, ROOT)}/summary.md"); sys.exit(2)
    except Exception as e:   # any unexpected error is also a STOP with evidence (no traceback values, token scrubbed)
        import traceback
        RES["stop"] = ("unexpected error in the runner: " + "".join(traceback.format_exception_only(type(e), e)).strip()[:600]).replace(os.environ.get("HF_TOKEN") or "\0", "***")
        RES["where"] = traceback.extract_tb(e.__traceback__)[-1].name
        write("STOP"); log(f"STOP: {RES['stop']}"); log(f"evidence {os.path.relpath(OUT, ROOT)}/summary.md"); sys.exit(2)

if __name__ == "__main__":
    main()
