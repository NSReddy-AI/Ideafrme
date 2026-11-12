"""Is this Mac ready to run IDEAFRAME (M6) with no network? READ-ONLY: it looks at files, names and sizes and asks local
binaries for their version. It downloads, installs, starts and changes nothing, and does not re-hash multi-GB model files.

  ~/.venvs/reelstudio/bin/python -B tools/m6_offline_check.py [--json]

Sources: the M4 offline vendor bundle's model_manifest.json (required model files, sizes), engine/asr.json (pinned weights),
providers.json (planner), the app's own folders (built UI, node_modules, fonts) and M5's pinned fonts."""
import argparse, glob, hashlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
VENDOR = ROOT.parent / "Reel Studio_M4_offline_vendor_2026-11-11"
rows = []


def add(area, item, ok, detail, required=True):
    rows.append(dict(area=area, item=item, ok=bool(ok), required=required, detail=detail))


def version(cmd):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[0][:80]
    except Exception as e: return f"not runnable ({type(e).__name__})"


def bottles():
    return {b.name.split("--")[0] for b in (VENDOR / "homebrew_bottles").glob("*.tar.gz")} | {k.name.replace("keg_", "").split(".")[0] for k in (VENDOR / "homebrew_kegs").glob("*")} if VENDOR.is_dir() else set()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    vend = bottles()
    add("system", "macOS on Apple Silicon", platform.system() == "Darwin" and platform.machine() == "arm64", f"{platform.system()} {platform.release()} {platform.machine()}")
    # Python environments (M4 engine, voice, speech-to-text) - M5 needs only the standard library of the first
    for env, use in (("reelstudio", "app + engine (and M5 code)"), ("rs_tts", "AI narration"), ("rs_asr", "Telugu speech-to-text")):
        py = HOME / ".venvs" / env / "bin" / "python"
        add("python", env, py.exists(), f"{version([str(py), '--version']) if py.exists() else 'missing'} - {use}; vendored: {(VENDOR / 'python_envs' / f'venv_{env}.tar.gz').exists()}")
    # Command-line tools
    for tool, required, note in (("ffmpeg", True, "all video work"), ("ffprobe", True, "QA"), ("whisper-cli", True, "English speech-to-text (whisper.cpp)"),
                                 ("ollama", True, "local planner"), ("node", False, "only for rebuilding the UI and M5 JS tests"),
                                 ("npx", False, "HyperFrames, only for hand-made motion compositions (not the app's own flow)")):
        p = shutil.which(tool)
        formula = {"ffprobe": "ffmpeg", "whisper-cli": "whisper.cpp", "npx": "node"}.get(tool, tool)
        add("tools", tool, p, f"{p or 'missing'} - {note}; Homebrew bottle in vendor bundle: {formula in vend}", required)
    hf = Path("/opt/homebrew/lib/node_modules/hyperframes/package.json")
    add("tools", "HyperFrames (global npm)", hf.exists(), (json.loads(hf.read_text()).get("version", "?") if hf.exists() else "missing") + " - not in the vendor bundle; optional for the app's own flow", False)
    add("tools", "Google Chrome", Path("/Applications/Google Chrome.app").exists(), "used by HyperFrames and M4's link screenshots only; the app itself runs in any modern browser", False)
    # Models (sizes from the vendor manifest; existence + size only)
    man = json.loads((VENDOR / "model_manifest.json").read_text()) if (VENDOR / "model_manifest.json").exists() else []
    for m in man:
        need = m["use"].startswith("REQUIRED")
        if not need and "optional" not in m["use"]: continue
        base = Path(os.path.expanduser(m["path"])); missing = []
        if m.get("files"):
            for f in m["files"]:   # resolve through the snapshot, as the model loader does (blobs may be links into a shared store)
                b = base / "snapshots" / m["revision"] / f["file"]
                if not (b.exists() and b.stat().st_size == f["bytes"]): missing.append(f["file"])
        elif m.get("layers"):
            for l in m["layers"]:
                b = base / "blobs" / l["digest"].replace(":", "-")
                if not (b.exists() and b.stat().st_size == l["bytes"]): missing.append(l["kind"])
        else:
            if not (base.exists() and base.stat().st_size == m.get("bytes")): missing.append(base.name)
        add("models", m["model"], not missing, ("all files present, sizes match" if not missing else "missing or wrong size: " + ", ".join(missing[:4])) + f" - {m['use']}", need)
    asr = json.loads((ROOT / "engine" / "asr.json").read_text())["te"]
    pinned = list(Path(os.path.expanduser("~/.cache/huggingface/hub/models--vasista22--whisper-telugu-large-v2/blobs")).glob(asr["model_weights_sha256"]))
    add("models", "Telugu STT pinned weights (asr.json)", bool(pinned), f"blob {asr['model_weights_sha256'][:12]} {'present' if pinned else 'missing'}")
    # Application files
    add("app", "built UI (app/web/dist)", (ROOT / "app/web/dist/index.html").exists(), "served by the app; rebuilding needs node + node_modules")
    add("app", "UI packages (app/web/node_modules)", (ROOT / "app/web/node_modules/vite").exists(), "only for rebuilding the UI; `npm ci --offline` from the local npm cache", False)
    for f in ("NotoSansTelugu-Black.ttf", "Inter-Bold.otf", "Anton-Regular.ttf", "DejaVuSans-Bold.ttf", "SixCaps.ttf"):
        add("fonts", f"engine/fonts/{f}", (ROOT / "engine/fonts" / f).exists(), "bundled")
    sys.path.insert(0, str(ROOT / "m5"))
    try:
        from visual_poster_studio.fonts import SPECS
        for lang, (name, digest, *_x) in SPECS.items():
            p = ROOT / "m5/examples/posters/assets/fonts" / name
            add("fonts", f"M5 pinned {name}", p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, "hash matches the pin" if p.exists() else "missing")
    except Exception as e: add("fonts", "M5 pinned fonts", False, f"could not read M5 font pins: {e}")
    add("app", "engine/models (face tracking, matting, upscaling)", all((ROOT / "engine/models" / f).exists() for f in ("rvm.onnx", "face_landmarker.task", "RealESRGAN_x4plus.pth")), "bundled in the workspace")
    prov = json.loads((ROOT / "providers.json").read_text())
    paid_on = [k for k, v in prov["providers"].items() if k != "local" and v.get("enabled") is not False]
    add("policy", "paid AI providers switched off", not paid_on, "all off" if not paid_on else "enabled: " + ", ".join(paid_on))

    if a.json: print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows: print(f"{'OK  ' if r['ok'] else ('MISS' if r['required'] else 'opt ')}  {r['area']:7} {r['item']:45} {r['detail']}")
    bad = [r for r in rows if r["required"] and not r["ok"]]
    print(f"\n{len(rows)} checks, {len(bad)} required missing", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
