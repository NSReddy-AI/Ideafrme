# Dependency inventory - Reel Studio

Generated 2026-11-10 from `tools/deps_raw.json` (read on the Mac: macOS-26.6.2-arm64-arm-64bit, Python 3.12.16). Regenerate with `tools/dump_deps.py` then `tools/make_register.py`.


> **M4 update (11 Nov 2026, release preparation):** complete, verified tables for all three Python environments (`reelstudio`,
> `rs_tts`, `rs_asr`), the web app's npm tree and every model are in **docs/M4_DEPENDENCY_TABLES.md**, generated from the installed
> metadata by `tools/scan_licences_m4.py` + `tools/make_register_m4.py` (raw scan: tools/deps_m4.json). Machine-readable: docs/SBOM.json
> (CycloneDX 1.5, 222 components). The sections below are the M2/M3 register, kept for history.
>
> M4 additions in short: app backend FastAPI / Starlette / Uvicorn / Pydantic (+ deps, all permissive) in `reelstudio`; web app React +
> React DOM (MIT, shipped) and build tools (Vite, Tailwind, TypeScript, oxlint, lightningcss MPL-2.0 - not shipped); new environment
> `rs_tts` (Indic Parler-TTS: parler-tts 0.2.2 Apache-2.0 from git commit d108732, torch, transformers, descript-audio-codec MIT,
> soxr LGPL-2.1+); models Indic Parler-TTS + flan-t5 tokenizer (Apache-2.0), Telugu Whisper pinned ba19a24b (Apache-2.0),
> Qwen3 14B / 8B via Ollama (Apache-2.0 / Ollama MIT). Excluded: Gemma 2 (cached in Ollama, unused, not open source).

## Python packages (Reel Studio's own environment)

| Package | Version | Licence (SPDX) | Why it is there | Note |
| --- | --- | --- | --- | --- |
| absl-py | 2.5.1 | Apache-2.0 | via mediapipe |  |
| certifi | 2026.10.23 | MPL-2.0 | via mediapipe | MPL-2.0 is file-level copyleft: fine unmodified; keep the notice. |
| cffi | 2.1.1 | MIT-0 | via sounddevice |  |
| contourpy | 1.4.0 | BSD-3-Clause | via matplotlib |  |
| cycler | 0.12.1 | BSD-3-Clause | via matplotlib |  |
| flatbuffers | 25.12.19 | Apache-2.0 | via mediapipe, onnxruntime |  |
| fonttools | 4.68.0 | MIT | via matplotlib |  |
| kiwisolver | 1.5.1 | BSD-3-Clause | via matplotlib |  |
| matplotlib | 3.11.2 | LicenseRef-Matplotlib (PSF-based) | via mediapipe (not used by Reel Studio) | Pulled in by MediaPipe; candidate to leave out of the app bundle if MediaPipe works without it. |
| mediapipe | 1.2.2 | Apache-2.0 | direct, optional: face tracking (off by default) |  |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | direct: everywhere |  |
| onnxruntime | 1.31.1 | MIT | direct: background blur model (RVM) |  |
| opencv-contrib-python | 5.0.0.93 | Apache-2.0 | via mediapipe (duplicate of opencv-python) | Same files as opencv-python plus extra modules; keep only this one in the Mac app bundle. |
| opencv-python | 5.0.0.93 | Apache-2.0 | direct: background blur, face tracking | Wheels bundle FFmpeg (LGPL-2.1) and other libraries; their notices ship inside the wheel. |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | via onnxruntime, matplotlib |  |
| pillow | 13.0.0 | MIT-CMU | direct: titles, frames, captions |  |
| pip | 26.3 | MIT | installer only |  |
| protobuf | 7.36.2 | BSD-3-Clause | via onnxruntime, mediapipe |  |
| pycparser | 3.12 | BSD-3-Clause | via cffi |  |
| pyparsing | 3.3.3 | MIT | via matplotlib |  |
| python-dateutil | 4.0.0 | BSD-3-Clause | via matplotlib |  |
| scipy | 1.18.1 | BSD-3-Clause | direct: music and sound effects |  |
| sounddevice | 0.5.6 | MIT | via mediapipe (not used; bundles PortAudio, MIT) |  |
| tzdata | 2026.6 | Apache-2.0 | via python-dateutil |  |


## Speech-tools environment (~/.venvs/rs_asr, separate Python)

| Package | Version | Licence (from metadata) | Used by the engine? |
| --- | --- | --- | --- |
| annotated-doc | 0.0.5 | MIT | dependency |
| annotated-types | 0.8.0 | MIT | dependency |
| anyio | 4.16.0 | MIT | dependency |
| av | 19.0.2 | BSD-3-Clause | dependency |
| click | 8.5.1 | BSD-3-Clause | dependency |
| ctranslate2 | 4.8.5 | MIT | no (tested, not adopted) |
| faster-whisper | 1.2.1 | MIT License | no (tested, not adopted) |
| filelock | 4.2.10 | MIT | dependency |
| flatbuffers | 25.12.19 | Apache Software License | dependency |
| fsspec | 2026.9.0 | BSD-3-Clause | dependency |
| h11 | 0.16.0 | MIT License | dependency |
| hf-xet | 1.8.0 | Apache-2.0 | dependency |
| httpcore2 | 2.16.0 | BSD-3-Clause | dependency |
| httpx2 | 2.16.0 | BSD-3-Clause | dependency |
| huggingface_hub | 2.4.0 | Apache Software License | dependency |
| idna | 3.20 | BSD-3-Clause | dependency |
| Jinja2 | 3.1.6 | BSD License | dependency |
| markdown-it-py | 4.2.0 | MIT License | dependency |
| MarkupSafe | 3.0.4 | BSD-3-Clause | dependency |
| mdurl | 0.1.2 | MIT License | dependency |
| mpmath | 1.3.0 | BSD License | dependency |
| networkx | 3.7 | BSD-3-Clause | dependency |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | dependency |
| onnxruntime | 1.31.1 | MIT License | dependency |
| opencv-python | 5.0.0.93 | Apache Software License | dependency |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | dependency |
| pip | 26.2.2 | MIT | dependency |
| platformdirs | 4.14.5 | MIT | dependency |
| protobuf | 7.36.2 | 3-Clause BSD License | dependency |
| pydantic | 2.14.3 | MIT | dependency |
| pydantic_core | 2.50.4 | MIT | dependency |
| Pygments | 2.21.0 | BSD-2-Clause | dependency |
| PyYAML | 6.0.3 | MIT License | dependency |
| regex | 2026.11.9 | Apache-2.0 AND CNRI-Python | dependency |
| rich | 15.0.0 | MIT License | dependency |
| safetensors | 0.8.0 | Apache Software License | dependency |
| scenedetect | 0.7.3 | BSD-3-Clause | no (tested, not adopted) |
| setuptools | 84.2.1 | MIT | dependency |
| shellingham | 1.5.4 | ISC License (ISCL) | dependency |
| sympy | 1.14.0 | BSD License | dependency |
| tokenizers | 0.23.3 | Apache Software License | dependency |
| torch | 2.15.0 | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND ISC AND MIT AND Zlib | yes: Telugu speech to text |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | dependency |
| transformers | 5.22.2 | Apache 2.0 License | yes: Telugu speech to text |
| truststore | 0.10.5 | MIT | dependency |
| typer | 0.29.0 | MIT | dependency |
| typing-inspection | 0.4.5 | MIT | dependency |
| typing_extensions | 4.16.0 | PSF-2.0 | dependency |


## Tools and system libraries

| Component | Version | Licence | Used for | Note |
| --- | --- | --- | --- | --- |
| Python | 3.12.16 | PSF-2.0 | runtime | Homebrew python@3.12, own environment ~/.venvs/reelstudio |
| whisper.cpp (whisper-cli) | 1.9.5 | MIT | English speech to text (engine/transcribe.py) | Homebrew; pulls ggml (MIT), libomp (Apache-2.0 WITH LLVM-exception), llama.cpp (MIT), SDL3 (Zlib) |
| DeepFilterNet deep-filter | 0.5.6 | MIT OR Apache-2.0 | cleaning the voice in the soundtrack (engine/mix.py) | official GitHub release binary in ~/.cache/rs_tools |
| FFmpeg | 9.0.2 | GPL-3.0-or-later | video engine (all scripts) | Homebrew build with --enable-gpl --enable-version3, libx264 and libx265 (GPL): the whole binary is GPL-3.0 |
| x264 (inside FFmpeg) | Homebrew | GPL-2.0-or-later | H.264 encoding of every reel | Reason the FFmpeg build is GPL |
| Node.js | 26.13.0 | MIT | runs HyperFrames | Homebrew |
| npm | 11.20.0 | Artistic-2.0 | installs HyperFrames | comes with Node |
| HyperFrames | 0.9.9 | Apache-2.0 | motion graphics (HTML -> transparent video) | npm global; renders with a headless browser it downloads (Chromium, BSD-3-Clause and others) - inventory its own dependencies before M6 |
| OpenAI Whisper | to confirm | MIT | speech to text | separate install at ~/.local/bin/whisper (wrapper script); version not readable from here |
| libraqm | 0.11.0 | MIT | Telugu text shaping for Pillow | Homebrew |
| HarfBuzz | 15.1.0 | MIT | text shaping (via libraqm) | Homebrew |
| FriBidi | 1.0.18 | LGPL-2.1-or-later | text direction (via libraqm) | Homebrew; dynamic library: keep it replaceable, ship notice |
| FreeType | 2.15.0 | FTL OR GPL-2.0-or-later | font rendering | Homebrew (2.13.3 also present); use under FTL, credit required |


## Models and fonts in the project

| File | What | Licence | Used for | Size | SHA-256 (first 16) |
| --- | --- | --- | --- | --- | --- |
| engine/models/RealESRGAN_x4plus.pth | Real-ESRGAN x4plus weights | BSD-3-Clause | 4K upscaling of title photos | 67.0 MB | 4fa0d38905f75ac0 |
| engine/models/blaze_face_short_range.tflite | MediaPipe BlazeFace short range | Apache-2.0 | face tracking (optional) | 0.2 MB | b4578f35940bf5a1 |
| engine/models/face_landmarker.task | MediaPipe Face Landmarker | Apache-2.0 | face tracking: mouth movement (optional) | 3.8 MB | 64184e229b263107 |
| engine/models/pose_landmarker_lite.task | MediaPipe Pose Landmarker lite | Apache-2.0 | face tracking: hand at mouth (optional) | 5.8 MB | 59929e1d1ee95287 |
| engine/models/rvm.onnx | Robust Video Matting | GPL-3.0-only | background blur / cut-outs | 15.0 MB | 88d4531297118f59 |
| engine/fonts/Anton-Regular.ttf | Anton | OFL-1.1 | numbers and English in motion graphics | 0.2 MB | a4ba3a92350ebb03 |
| engine/fonts/DejaVuSans-Bold.ttf | DejaVu Sans Bold | LicenseRef-Bitstream-Vera | ? and ! marks on title pages | 0.7 MB | 5c1247acef7f2b85 |
| engine/fonts/Inter-Bold.otf | Inter Bold | OFL-1.1 | Latin titles and captions | 0.6 MB | 00fd6f4691ee8884 |
| engine/fonts/NotoSansTelugu-Black.ttf | Noto Sans Telugu Black | OFL-1.1 | Telugu titles and captions | 0.2 MB | 42a3167fc2d8ca08 |
| engine/fonts/SixCaps.ttf | Six Caps | OFL-1.1 | end-card display text | 0.0 MB | 7b54a46671722fb6 |


## Other things the reels depend on

| Item | Licence / terms | Used for | Note |
| --- | --- | --- | --- |
| Telugu speech model vasista22/whisper-telugu-large-v2 (IIT Madras) | Apache-2.0 | Telugu speech to text (default) | ~/.cache/huggingface; fine-tuned from OpenAI Whisper (MIT); uses the openai/whisper-large-v2 generation settings (MIT) |
| whisper.cpp model ggml-large-v3-turbo | MIT | English speech to text | ~/.cache/rs_asr |
| Test-only models: ggml-large-v3 (MIT), ggml-te-small (Apache-2.0), faster-whisper models (MIT), OpenAI Whisper turbo/large-v3 (MIT) | MIT / Apache-2.0 | M3 comparisons only, not used by the engine | can be deleted to free several GB |
| GSAP | - | REMOVED 10 Nov | motion graphics now use the browser's Web Animations API (engine/motion.py); old reel_002 GSAP composition kept only as a reference |
| Fonts in motion graphics | OFL-1.1 | graphic text | now copied beside each composition from engine/fonts - nothing loads from the internet |
| Claude, Gemini, OpenAI APIs | paid service terms | OPTIONAL planning/script providers | never required; local open model is the default (providers.py) |
| ElevenLabs API | paid service terms | EXCLUDED by policy | voice.py kept dormant; the app will not use or require it |
| Brand assets (logos, photos, end cards, icons) | brand-owned / third-party marks | brand kits | not software licences: rights and permissions belong to the brand owner |
