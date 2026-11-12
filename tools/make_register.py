"""Builds the dependency register from tools/deps_raw.json (made by tools/dump_deps.py on the Mac).
Writes docs/DEPENDENCY_INVENTORY.md, docs/THIRD_PARTY_NOTICES.md, docs/LICENSE_COMPLIANCE.md, docs/SBOM.json.
Licence facts that package metadata cannot give (tools, models, fonts, web assets) are recorded below by hand."""
import json, os, datetime, uuid
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = json.load(open(os.path.join(ROOT, "tools", "deps_raw.json")))
DOCS = os.path.join(ROOT, "docs"); os.makedirs(DOCS, exist_ok=True); TODAY = datetime.date.today().isoformat()
# --- Python packages: SPDX licence (checked against metadata) and why it is installed
SPDX = {"absl-py": "Apache-2.0", "certifi": "MPL-2.0", "cffi": "MIT-0", "contourpy": "BSD-3-Clause", "cycler": "BSD-3-Clause", "flatbuffers": "Apache-2.0",
        "fonttools": "MIT", "kiwisolver": "BSD-3-Clause", "matplotlib": "LicenseRef-Matplotlib (PSF-based)", "mediapipe": "Apache-2.0",
        "numpy": "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0", "onnxruntime": "MIT", "opencv-contrib-python": "Apache-2.0",
        "opencv-python": "Apache-2.0", "packaging": "Apache-2.0 OR BSD-2-Clause", "pillow": "MIT-CMU", "pip": "MIT", "protobuf": "BSD-3-Clause",
        "pycparser": "BSD-3-Clause", "pyparsing": "MIT", "python-dateutil": "BSD-3-Clause", "scipy": "BSD-3-Clause", "sounddevice": "MIT", "tzdata": "Apache-2.0"}
ROLE = {"pillow": "direct: titles, frames, captions", "numpy": "direct: everywhere", "scipy": "direct: music and sound effects",
        "opencv-python": "direct: background blur, face tracking", "onnxruntime": "direct: background blur model (RVM)",
        "mediapipe": "direct, optional: face tracking (off by default)", "opencv-contrib-python": "via mediapipe (duplicate of opencv-python)",
        "absl-py": "via mediapipe", "flatbuffers": "via mediapipe, onnxruntime", "protobuf": "via onnxruntime, mediapipe", "packaging": "via onnxruntime, matplotlib",
        "matplotlib": "via mediapipe (not used by Reel Studio)", "contourpy": "via matplotlib", "cycler": "via matplotlib", "fonttools": "via matplotlib",
        "kiwisolver": "via matplotlib", "pyparsing": "via matplotlib", "python-dateutil": "via matplotlib", "tzdata": "via python-dateutil",
        "sounddevice": "via mediapipe (not used; bundles PortAudio, MIT)", "cffi": "via sounddevice", "pycparser": "via cffi", "certifi": "via mediapipe",
        "pip": "installer only"}
NOTE = {"opencv-python": "Wheels bundle FFmpeg (LGPL-2.1) and other libraries; their notices ship inside the wheel.",
        "opencv-contrib-python": "Same files as opencv-python plus extra modules; keep only this one in the Mac app bundle.",
        "certifi": "MPL-2.0 is file-level copyleft: fine unmodified; keep the notice.",
        "matplotlib": "Pulled in by MediaPipe; candidate to leave out of the app bundle if MediaPipe works without it."}
# --- everything that is not a Python package
TOOLS = [
 ("Python", "3.12.16", "PSF-2.0", "runtime", "Homebrew python@3.12, own environment ~/.venvs/reelstudio", "pkg:generic/python@3.12.16"),
 ("whisper.cpp (whisper-cli)", "1.9.5", "MIT", "English speech to text (engine/transcribe.py)", "Homebrew; pulls ggml (MIT), libomp (Apache-2.0 WITH LLVM-exception), llama.cpp (MIT), SDL3 (Zlib)", "pkg:brew/whisper-cpp@1.9.5"),
 ("DeepFilterNet deep-filter", "0.5.6", "MIT OR Apache-2.0", "cleaning the voice in the soundtrack (engine/mix.py)", "official GitHub release binary in ~/.cache/rs_tools", "pkg:github/Rikorose/DeepFilterNet@v0.5.6"),
 ("FFmpeg", "9.0.2", "GPL-3.0-or-later", "video engine (all scripts)", "Homebrew build with --enable-gpl --enable-version3, libx264 and libx265 (GPL): the whole binary is GPL-3.0", "pkg:brew/ffmpeg@9.0.2"),
 ("x264 (inside FFmpeg)", "Homebrew", "GPL-2.0-or-later", "H.264 encoding of every reel", "Reason the FFmpeg build is GPL", "pkg:brew/x264"),
 ("Node.js", "26.13.0", "MIT", "runs HyperFrames", "Homebrew", "pkg:brew/node@26.13.0"),
 ("npm", "11.20.0", "Artistic-2.0", "installs HyperFrames", "comes with Node", "pkg:npm/npm@11.20.0"),
 ("HyperFrames", "0.9.9", "Apache-2.0", "motion graphics (HTML -> transparent video)", "npm global; renders with a headless browser it downloads (Chromium, BSD-3-Clause and others) - inventory its own dependencies before M6", "pkg:npm/hyperframes@0.9.9"),
 ("OpenAI Whisper", "to confirm", "MIT", "speech to text", "separate install at ~/.local/bin/whisper (wrapper script); version not readable from here", "pkg:pypi/openai-whisper"),
 ("libraqm", "0.11.0", "MIT", "Telugu text shaping for Pillow", "Homebrew", "pkg:brew/libraqm@0.11.0"),
 ("HarfBuzz", "15.1.0", "MIT", "text shaping (via libraqm)", "Homebrew", "pkg:brew/harfbuzz@15.1.0"),
 ("FriBidi", "1.0.18", "LGPL-2.1-or-later", "text direction (via libraqm)", "Homebrew; dynamic library: keep it replaceable, ship notice", "pkg:brew/fribidi@1.0.18"),
 ("FreeType", "2.15.0", "FTL OR GPL-2.0-or-later", "font rendering", "Homebrew (2.13.3 also present); use under FTL, credit required", "pkg:brew/freetype@2.15.0"),
]
MODELS = {
 "engine/models/rvm.onnx": ("Robust Video Matting", "GPL-3.0-only", "background blur / cut-outs", "PeterL1n/RobustVideoMatting; GPL: keep as a separate component, offer source if distributed"),
 "engine/models/RealESRGAN_x4plus.pth": ("Real-ESRGAN x4plus weights", "BSD-3-Clause", "4K upscaling of title photos", "xinntao/Real-ESRGAN"),
 "engine/models/blaze_face_short_range.tflite": ("MediaPipe BlazeFace short range", "Apache-2.0", "face tracking (optional)", "Google MediaPipe model card"),
 "engine/models/face_landmarker.task": ("MediaPipe Face Landmarker", "Apache-2.0", "face tracking: mouth movement (optional)", "Google MediaPipe model card"),
 "engine/models/pose_landmarker_lite.task": ("MediaPipe Pose Landmarker lite", "Apache-2.0", "face tracking: hand at mouth (optional)", "Google MediaPipe model card"),
 "engine/fonts/NotoSansTelugu-Black.ttf": ("Noto Sans Telugu Black", "OFL-1.1", "Telugu titles and captions", "Google Noto fonts"),
 "engine/fonts/Inter-Bold.otf": ("Inter Bold", "OFL-1.1", "Latin titles and captions", "rsms/inter"),
 "engine/fonts/DejaVuSans-Bold.ttf": ("DejaVu Sans Bold", "LicenseRef-Bitstream-Vera", "? and ! marks on title pages", "Bitstream Vera licence + public-domain DejaVu changes"),
 "engine/fonts/Anton-Regular.ttf": ("Anton", "OFL-1.1", "numbers and English in motion graphics", "google/fonts, licence text in engine/fonts/licences"),
 "engine/fonts/SixCaps.ttf": ("Six Caps", "OFL-1.1", "end-card display text", "google/fonts, licence text in engine/fonts/licences"),
}
OTHER = [
 ("Telugu speech model vasista22/whisper-telugu-large-v2 (IIT Madras)", "Apache-2.0", "Telugu speech to text (default)", "~/.cache/huggingface; fine-tuned from OpenAI Whisper (MIT); uses the openai/whisper-large-v2 generation settings (MIT)"),
 ("whisper.cpp model ggml-large-v3-turbo", "MIT", "English speech to text", "~/.cache/rs_asr"),
 ("Test-only models: ggml-large-v3 (MIT), ggml-te-small (Apache-2.0), faster-whisper models (MIT), OpenAI Whisper turbo/large-v3 (MIT)", "MIT / Apache-2.0", "M3 comparisons only, not used by the engine", "can be deleted to free several GB"),
 ("GSAP", "-", "REMOVED 10 Nov", "motion graphics now use the browser's Web Animations API (engine/motion.py); old reel_002 GSAP composition kept only as a reference"),
 ("Fonts in motion graphics", "OFL-1.1", "graphic text", "now copied beside each composition from engine/fonts - nothing loads from the internet"),
 ("Claude, Gemini, OpenAI APIs", "paid service terms", "OPTIONAL planning/script providers", "never required; local open model is the default (providers.py)"),
 ("ElevenLabs API", "paid service terms", "EXCLUDED by policy", "voice.py kept dormant; the app will not use or require it"),
 ("Brand assets (logos, photos, end cards, icons)", "brand-owned / third-party marks", "brand kits", "not software licences: rights and permissions belong to the brand owner"),
]
pk = {p["name"].lower(): p for p in D["packages"]}
def md_table(head, rows): return "| " + " | ".join(head) + " |\n| " + " | ".join("---" for _ in head) + " |\n" + "".join("| " + " | ".join(str(c) for c in r) + " |\n" for r in rows)
# 1. inventory
inv = [f"# Dependency inventory - Reel Studio\n\nGenerated {TODAY} from `tools/deps_raw.json` (read on the Mac: {D['mac']}, Python {D['python'].split()[0]}). Regenerate with `tools/dump_deps.py` then `tools/make_register.py`.\n",
       "## Python packages (Reel Studio's own environment)\n", md_table(["Package", "Version", "Licence (SPDX)", "Why it is there", "Note"],
       [(p["name"], p["version"], SPDX.get(p["name"].lower(), "UNKNOWN - check"), ROLE.get(p["name"].lower(), "?"), NOTE.get(p["name"].lower(), "")) for p in D["packages"]]),
       "\n## Speech-tools environment (~/.venvs/rs_asr, separate Python)\n",
       md_table(["Package", "Version", "Licence (from metadata)", "Used by the engine?"],
                [(p["name"], p["version"], p.get("license_expression") or ", ".join(c.split("::")[-1].strip() for c in p.get("classifiers", [])) or (p.get("license") or "UNKNOWN - check")[:60],
                  {"transformers": "yes: Telugu speech to text", "torch": "yes: Telugu speech to text", "faster-whisper": "no (tested, not adopted)", "ctranslate2": "no (tested, not adopted)",
                   "scenedetect": "no (tested, not adopted)"}.get(p["name"].lower(), "dependency")) for p in D.get("asr_packages", [])]) if D.get("asr_packages") else "(not captured - run tools/dump_deps.py)\n",
       "\n## Tools and system libraries\n", md_table(["Component", "Version", "Licence", "Used for", "Note"], [(n, v, l, u, note) for n, v, l, u, note, _ in TOOLS]),
       "\n## Models and fonts in the project\n", md_table(["File", "What", "Licence", "Used for", "Size", "SHA-256 (first 16)"],
       [(f["path"], MODELS.get(f["path"], ("?",))[0], MODELS.get(f["path"], ("", "UNKNOWN"))[1], MODELS.get(f["path"], ("", "", "?"))[2], f"{f['bytes']/1e6:.1f} MB", f["sha256"][:16]) for f in D["models_fonts"]]),
       "\n## Other things the reels depend on\n", md_table(["Item", "Licence / terms", "Used for", "Note"], OTHER)]
open(os.path.join(DOCS, "DEPENDENCY_INVENTORY.md"), "w").write("\n".join(inv))
# 2. notices
no = [f"# Third-party notices - Reel Studio\n\nReel Studio uses the following third-party software, models and fonts. Each remains under its own licence.\nFull licence texts must be collected into `licenses/` before the Mac app is distributed (Milestone 6).\nGenerated {TODAY}.\n"]
for p in D["packages"]: no.append(f"- **{p['name']} {p['version']}** - {SPDX.get(p['name'].lower(), 'see package metadata')}")
no.append("")
for n, v, l, u, note, _ in TOOLS: no.append(f"- **{n} {v}** - {l}")
for path, (n, l, u, src) in MODELS.items(): no.append(f"- **{n}** (`{path}`) - {l}. Source: {src}")
for n, l, u, note in OTHER[:3]: no.append(f"- **{n}** - {l}")
no.append("\nFFmpeg is used as a separate program (GPL-3.0-or-later build). Robust Video Matting is GPL-3.0. Their source code is available from their projects;\nif Reel Studio is distributed with them, the corresponding source and licence texts must be offered with it.\n")
open(os.path.join(DOCS, "THIRD_PARTY_NOTICES.md"), "w").write("\n".join(no))
# 3. compliance
co = f"""# Licence compliance - Reel Studio

Generated {TODAY}. Policy (approved 10 Nov): **free and unrestricted only.** Everything Reel Studio needs must be free of charge
and free to use for any purpose, including commercial use, with no usage limits. Allowed: MIT, Apache, BSD, ISC, PSF, OFL, public
domain, and GPL/LGPL/AGPL (free to use; their obligations only apply when redistributing or offering modified versions).
Excluded from the core: anything paid or metered, "free but proprietary" licences (e.g. GSAP), non-commercial licences (e.g. CC-BY-NC),
and models with custom usage-restriction licences (e.g. Llama, Gemma).
Exception (approved 10 Nov): Claude, Gemini and OpenAI may be used as OPTIONAL planning/script providers when the user chooses them for
better results. The app must work fully without them; the local open model is the default. This is an engineering register, not legal advice; have the final Mac app and any web service
reviewed by an open-source licensing lawyer before commercial release.

## Summary
| Group | Count | Status |
| --- | --- | --- |
| Permissive (MIT, BSD, Apache, ISC, PSF, OFL fonts) | most | OK: keep notices |
| Weak copyleft (MPL-2.0 certifi, LGPL FriBidi, LGPL FFmpeg inside OpenCV wheels) | 3 | OK: unmodified, dynamically linked; keep notices, keep replaceable |
| Strong copyleft (GPL FFmpeg build with x264/x265, GPL Robust Video Matting) | 2 | OK for local use; obligations when distributed |
| Not open source (GSAP, online AI services, brand assets) | 3 | Needs a decision (below) |
| Unknown | 1 | Whisper install version to confirm |

## Findings and actions
| # | Finding | Risk | Action | When |
| --- | --- | --- | --- | --- |
| 1 | FFmpeg is a GPL-3.0 build (x264, x265) | None for your own use. If shipped inside the Mac app, GPL source and licence obligations apply | Either ship it with source offer and notices, or bundle an LGPL build that encodes with Apple VideoToolbox (must then pass the locked baseline again) | M6 |
| 2 | Robust Video Matting model is GPL-3.0 | Same as above when distributed; running it on our own server is not distribution | Keep it a separate component; offer source if distributed; or swap for a permissive matting model | M6 |
| 3 | GSAP was not open source | Excluded by policy | DONE 10 Nov: replaced by the Web Animations API (engine/motion.py); same output, HyperFrames lint 0 errors | done |
| 4 | Compositions loaded GSAP and Google Fonts from the internet | Renders failed offline | DONE 10 Nov: fonts copied from engine/fonts, no internet references | done |
| 5 | Two OpenCV packages installed (opencv-python and opencv-contrib-python, same version) | Uninstalling either breaks cv2 | Keep only opencv-contrib in the app bundle | M6 |
| 6 | matplotlib and sounddevice come only via MediaPipe and are unused | Extra size and notices | Test leaving them out of the bundle | M6 |
| 7 | Speech to text | - | DONE 10 Nov: Telugu = IIT Madras model (Apache-2.0, 4x fewer errors), English = whisper.cpp (MIT), in ~/.venvs/rs_asr (transformers Apache-2.0, torch BSD-3); openai-whisper (pipx) no longer used by the engine | done |
| 11 | Test-only installs (faster-whisper, PySceneDetect, extra models) | Disk space only | Not adopted; can be removed after M3 | M3 wrap-up |
| 12 | torch is large (about 1 GB) | App size | Keep speech tools as a separate component in the Mac app | M6 |
| 13 | DeepFilterNet binary from GitHub | - | MIT/Apache-2.0; record the release checksum when bundling | M6 |
| 8 | Paid online services (Claude, Gemini, OpenAI, ElevenLabs) | Claude/Gemini/OpenAI allowed as optional providers only; ElevenLabs excluded | Default planning on a local open model (Ollama MIT + Qwen3 Apache-2.0); paid providers selectable per project when they give better results; voice only from an open, commercially usable Telugu TTS, otherwise text + music | M4 |
| 9 | Brand assets (logos, photos, end cards) | Rights, trademarks and likeness, not software licences | Brand owner confirms permission for each brand kit | Before publishing |
| 10 | Ultralytics / YOLO (AGPL) | Not installed | Not needed while MediaPipe passes | - |

## Rules for adding anything new
1. Record name, version, licence and why, in this register, before installing.
2. Install only into Reel Studio's own environment (never system-wide).
3. Prefer permissive licences; GPL/AGPL allowed with a written note on how obligations are met.
4. Model weights and fonts are checked separately from the code that loads them.
5. Re-run `checkpoint.sh` (locked baseline) after every change.
"""
open(os.path.join(DOCS, "LICENSE_COMPLIANCE.md"), "w").write(co)
# 4. SBOM (CycloneDX 1.5)
def lic(x): return [{"expression": x}] if (" OR " in x or " AND " in x) else [{"license": ({"id": x} if not x.startswith("LicenseRef") and " " not in x else {"name": x})}]
comps = [dict(type="library", name=p["name"], version=p["version"], purl=f"pkg:pypi/{p['name'].lower()}@{p['version']}", licenses=lic(SPDX.get(p["name"].lower(), "NOASSERTION"))) for p in D["packages"]]
comps += [dict(type="application", name=n, version=v, purl=purl, licenses=lic(l), description=u) for n, v, l, u, note, purl in TOOLS]
for f in D["models_fonts"]:
    n, l, u, src = MODELS.get(f["path"], (f["path"], "NOASSERTION", "", ""))
    comps.append(dict(type="data" if "models" in f["path"] else "file", name=n, version="as-installed", licenses=lic(l), description=f"{u} ({f['path']})",
                      hashes=[{"alg": "SHA-256", "content": f["sha256"]}]))
comps.append(dict(type="library", name="gsap", version="3.12.5", purl="pkg:npm/gsap@3.12.5", licenses=[{"license": {"name": "GSAP Standard No Charge License"}}], description="loaded from CDN in HyperFrames compositions"))
sbom = {"bomFormat": "CycloneDX", "specVersion": "1.5", "serialNumber": f"urn:uuid:{uuid.uuid4()}", "version": 1,
        "metadata": {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "component": {"type": "application", "name": "AI Reel Studio engine", "version": "M2"}},
        "components": comps}
json.dump(sbom, open(os.path.join(DOCS, "SBOM.json"), "w"), indent=1)
print("wrote 4 files to", DOCS, "|", len(comps), "SBOM components")
