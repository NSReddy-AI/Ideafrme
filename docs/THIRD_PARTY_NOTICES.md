# Third-party notices - Reel Studio

Reel Studio uses the following third-party software, models and fonts. Each remains under its own licence.
Full licence texts must be collected into `licenses/` before the Mac app is distributed (Milestone 6).
Generated 2026-11-10.

- **absl-py 2.5.1** - Apache-2.0
- **certifi 2026.10.23** - MPL-2.0
- **cffi 2.1.1** - MIT-0
- **contourpy 1.4.0** - BSD-3-Clause
- **cycler 0.12.1** - BSD-3-Clause
- **flatbuffers 25.12.19** - Apache-2.0
- **fonttools 4.68.0** - MIT
- **kiwisolver 1.5.1** - BSD-3-Clause
- **matplotlib 3.11.2** - LicenseRef-Matplotlib (PSF-based)
- **mediapipe 1.2.2** - Apache-2.0
- **numpy 2.5.4** - BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0
- **onnxruntime 1.31.1** - MIT
- **opencv-contrib-python 5.0.0.93** - Apache-2.0
- **opencv-python 5.0.0.93** - Apache-2.0
- **packaging 26.3** - Apache-2.0 OR BSD-2-Clause
- **pillow 13.0.0** - MIT-CMU
- **pip 26.3** - MIT
- **protobuf 7.36.2** - BSD-3-Clause
- **pycparser 3.12** - BSD-3-Clause
- **pyparsing 3.3.3** - MIT
- **python-dateutil 4.0.0** - BSD-3-Clause
- **scipy 1.18.1** - BSD-3-Clause
- **sounddevice 0.5.6** - MIT
- **tzdata 2026.6** - Apache-2.0

- **Python 3.12.16** - PSF-2.0
- **whisper.cpp (whisper-cli) 1.9.5** - MIT
- **DeepFilterNet deep-filter 0.5.6** - MIT OR Apache-2.0
- **FFmpeg 9.0.2** - GPL-3.0-or-later
- **x264 (inside FFmpeg) Homebrew** - GPL-2.0-or-later
- **Node.js 26.13.0** - MIT
- **npm 11.20.0** - Artistic-2.0
- **HyperFrames 0.9.9** - Apache-2.0
- **OpenAI Whisper to confirm** - MIT
- **libraqm 0.11.0** - MIT
- **HarfBuzz 15.1.0** - MIT
- **FriBidi 1.0.18** - LGPL-2.1-or-later
- **FreeType 2.15.0** - FTL OR GPL-2.0-or-later
- **Robust Video Matting** (`engine/models/rvm.onnx`) - GPL-3.0-only. Source: PeterL1n/RobustVideoMatting; GPL: keep as a separate component, offer source if distributed
- **Real-ESRGAN x4plus weights** (`engine/models/RealESRGAN_x4plus.pth`) - BSD-3-Clause. Source: xinntao/Real-ESRGAN
- **MediaPipe BlazeFace short range** (`engine/models/blaze_face_short_range.tflite`) - Apache-2.0. Source: Google MediaPipe model card
- **MediaPipe Face Landmarker** (`engine/models/face_landmarker.task`) - Apache-2.0. Source: Google MediaPipe model card
- **MediaPipe Pose Landmarker lite** (`engine/models/pose_landmarker_lite.task`) - Apache-2.0. Source: Google MediaPipe model card
- **Noto Sans Telugu Black** (`engine/fonts/NotoSansTelugu-Black.ttf`) - OFL-1.1. Source: Google Noto fonts
- **Inter Bold** (`engine/fonts/Inter-Bold.otf`) - OFL-1.1. Source: rsms/inter
- **DejaVu Sans Bold** (`engine/fonts/DejaVuSans-Bold.ttf`) - LicenseRef-Bitstream-Vera. Source: Bitstream Vera licence + public-domain DejaVu changes
- **Anton** (`engine/fonts/Anton-Regular.ttf`) - OFL-1.1. Source: google/fonts, licence text in engine/fonts/licences
- **Six Caps** (`engine/fonts/SixCaps.ttf`) - OFL-1.1. Source: google/fonts, licence text in engine/fonts/licences
- **Telugu speech model vasista22/whisper-telugu-large-v2 (IIT Madras)** - Apache-2.0
- **whisper.cpp model ggml-large-v3-turbo** - MIT
- **Test-only models: ggml-large-v3 (MIT), ggml-te-small (Apache-2.0), faster-whisper models (MIT), OpenAI Whisper turbo/large-v3 (MIT)** - MIT / Apache-2.0

FFmpeg is used as a separate program (GPL-3.0-or-later build). Robust Video Matting is GPL-3.0. Their source code is available from their projects;
if Reel Studio is distributed with them, the corresponding source and licence texts must be offered with it.

## M4 app (added 11 Nov 2026, Gate C licence review)
Backend (in ~/.venvs/reelstudio, runs locally only):
- **FastAPI 0.162.4** - MIT · **Starlette 1.10.0** - BSD-3-Clause · **Uvicorn 0.54.0** - BSD-3-Clause · **Pydantic 2.14.3 / pydantic-core 2.50.4** - MIT
- Their dependencies: anyio (MIT), h11 (MIT), click (BSD-3-Clause), idna (BSD-3-Clause), typing_extensions (PSF-2.0), typing-inspection (MIT),
  annotated-types (MIT), annotated-doc (MIT), opentelemetry-api (Apache-2.0)
Web app (app/web; only React and React DOM are inside the built app app/web/dist, everything else is a build tool):
- **React 19.3.1 / React DOM 19.3.1** - MIT (shipped in app/web/dist)
- Build tools: Vite 8.3.8 (MIT), Tailwind CSS 4.3.5 + @tailwindcss/vite (MIT), @vitejs/plugin-react (MIT), TypeScript 7.0.2 (Apache-2.0), oxlint (MIT)
- Whole npm tree (57 packages): 47 MIT, 3 Apache-2.0, 2 ISC, 2 0BSD, 1 BSD-3-Clause, 2 MPL-2.0 (**lightningcss**, a CSS build tool used
  by Tailwind/Vite at build time only - not shipped in app/web/dist; MPL-2.0 is file-level copyleft, commercially usable; its source is
  public, and any change to lightningcss itself would have to be shared).
No new model weights, fonts or scripts are loaded from the internet: the app is served from this Mac (127.0.0.1) and uses the system Telugu font.

## M4 narration, planner and model notices (added 11 Nov 2026, release preparation)
- **Indic Parler-TTS** (ai4bharat/indic-parler-tts, revision 660bc53c) - Apache-2.0 · voice-description tokenizer **google/flan-t5-large** (0613663d) - Apache-2.0
- **parler-tts 0.2.2** (huggingface/parler-tts, git d108732) - Apache-2.0 · **descript-audio-codec 1.0.0** - MIT · **soxr 1.1.0** - LGPL-2.1-or-later
  (bundles libsoxr, LGPL; licence texts inside the package) · **tqdm** - MPL-2.0 AND MIT · **torch** - BSD-3-Clause (+ bundled permissive parts)
  · **transformers** - Apache-2.0
- **Telugu Whisper vasista22/whisper-telugu-large-v2** (revision ba19a24b) - Apache-2.0 · generation config from **openai/whisper-large-v2** - Apache-2.0 / MIT
- **Qwen3 14B and 8B** (Alibaba Qwen, via Ollama) - Apache-2.0 · **Ollama 0.40.16** - MIT
- Complete per-package list: docs/M4_DEPENDENCY_TABLES.md and docs/SBOM.json.
- **Not included:** Gemma 2 (cached in Ollama on this Mac, not used by Reel Studio; Gemma Terms of Use are not an open-source licence).
