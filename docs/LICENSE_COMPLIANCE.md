# Licence compliance - Reel Studio

Generated 2026-11-10. Policy (approved 10 Nov): **free and unrestricted only.** Everything Reel Studio needs must be free of charge
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


## M4 release update (11 Nov 2026) - verified from installed metadata and licence files
Scan: `tools/scan_licences_m4.py` (read-only). Result: **no GPL/AGPL package** in any Python environment or the npm tree.
| Group | M4 items | Status |
| --- | --- | --- |
| Permissive | 173 Python packages across 3 environments, 56 npm packages, Indic Parler-TTS, flan-t5, Telugu Whisper, Qwen3, Ollama | OK: keep notices |
| Weak copyleft | certifi (MPL-2.0), tqdm (MPL-2.0 AND MIT), soxr (LGPL-2.1-or-later, wraps libsoxr; licence texts inside the wheel), lightningcss (MPL-2.0, build-time only, not shipped) | OK unmodified; keep notices; soxr dynamically linked and replaceable |
| Strong copyleft | FFmpeg build (`--enable-gpl --enable-version3`, x264, x265) = GPL-3.0-or-later; Robust Video Matting `engine/models/rvm.onnx` (GPL-3.0) | OK for use on this Mac; obligations on distribution (below) |
| Not open source | Gemma 2 (Gemma Terms of Use) - cached in Ollama, NOT used | **Excluded** from every release |

| # | Finding | Action | When |
| --- | --- | --- | --- |
| 14 | Indic Parler-TTS (Apache-2.0) is a **gated** download on Hugging Face | Licence allows commercial use; keep the local cache (~/.cache/rs_tts_hf, revision 660bc53c) and its backup - re-download needs an account | release |
| 15 | parler-tts 0.2.2 has no licence metadata (installed from git d108732) | Verified: Apache-2.0 LICENSE inside the package | done |
| 16 | Telugu Whisper (vasista22, Apache-2.0 per M3 record) - model card not cached locally | Pinned to ba19a24b (weights sha256 1c3388d4…). Re-confirm the card licence online before any redistribution | before distribution |
| 17 | Qwen3 14B / 8B licence | Verified locally (`ollama show --license`): Apache License 2.0 | done |
| 18 | M4 app dependencies | All permissive (see THIRD_PARTY_NOTICES, M4 section) | done |
| 19 | Paid providers (Claude, Gemini, OpenAI, ElevenLabs) | Still optional, key-gated, off by default; nothing requires them | ongoing |

### Distribution obligations (apply only if Reel Studio is given to anyone else; a release on this Mac is not distribution)
- **FFmpeg (GPL-3.0-or-later build):** Reel Studio calls the Homebrew `ffmpeg` program, it does not contain it. If a package ever bundles
  FFmpeg: include the GPL-3.0 text, the exact source of FFmpeg 9.0.2 + x264 + x265 (or a written offer), and the build configuration;
  alternative: an LGPL build using Apple VideoToolbox (must pass the reel_002 baseline again).
- **Robust Video Matting (`engine/models/rvm.onnx`, GPL-3.0):** used only by the optional, manual `matte.py` (not part of the M4 build
  path). A distributed package must include the GPL-3.0 text and the model's source/offer - or leave `matte.py` + `rvm.onnx` out.
- **MPL-2.0 / LGPL parts:** ship unmodified with their licence texts; keep soxr replaceable (it is a separate shared library in the wheel).
- **Brand assets:** rights/likeness confirmations per brand (finding 9) still apply before publishing.

## Rules for adding anything new
1. Record name, version, licence and why, in this register, before installing.
2. Install only into Reel Studio's own environment (never system-wide).
3. Prefer permissive licences; GPL/AGPL allowed with a written note on how obligations are met.
4. Model weights and fonts are checked separately from the code that loads them.
5. Re-run `checkpoint.sh` (locked baseline) after every change.
