# M4 qualification prerequisite inventory

Read-only inventory, 2026-11-22. No models loaded, no downloads, installs or tests run.
Presence and size do not prove integrity, compatibility, or runtime readiness.

| Area | Input | Result | Location / detail |
|---|---|---|---|
| Narration legacy | title | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/title.py.preB1 |
| Narration legacy | frame | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/frame.py.preB1 |
| Narration legacy | slides | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/slides.py.preB1 |
| Narration legacy | qa | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/qa.py.preB1 |
| Narration legacy | voice | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/voice.py.preB1 |
| Narration legacy | adapter | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/adapter.py.preB1 |
| Narration legacy | rs | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/rs.py.preB1 |
| Narration legacy | mix | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/mix.py.preB1 |
| Narration optional | narrate.preB12 | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/narrate.py.preB12 |
| Fonts | NotoSansTelugu-Black.ttf | PRESENT | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/fonts/NotoSansTelugu-Black.ttf |
| Fonts | Inter-Bold.otf | PRESENT | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/fonts/Inter-Bold.otf |
| Fonts | DejaVuSans-Bold.ttf | PRESENT | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/fonts/DejaVuSans-Bold.ttf |
| Models bundled | rvm.onnx | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/models/rvm.onnx |
| Models bundled | face_landmarker.task | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/models/face_landmarker.task |
| Models bundled | RealESRGAN_x4plus.pth | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/engine/models/RealESRGAN_x4plus.pth |
| Planner input | project.json | PRESENT | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/projects/2026-11-03_reel_002_development/project.json |
| Planner input | build/words.json | MISSING | /Users/Nadish/projects/agents/ideafrme-m4-release-gates/projects/2026-11-03_reel_002_development/build/words.json |
| ASR audio | resolved from isolated checkout | MISSING | /Users/Nadish/projects/agents/raw footage/What jagan said.mov |
| ASR audio | resolved from original checkout | PRESENT | /Users/Nadish/projects/AI Video Editor./raw footage/What jagan said.mov |
| Python env | reelstudio | PRESENT | /Users/Nadish/.venvs/reelstudio/bin/python |
| Python env | rs_asr | PRESENT | /Users/Nadish/.venvs/rs_asr/bin/python |
| Python env | rs_tts | PRESENT | /Users/Nadish/.venvs/rs_tts/bin/python |
| Executable | ffmpeg | PRESENT | /opt/homebrew/bin/ffmpeg |
| Executable | ffprobe | PRESENT | /opt/homebrew/bin/ffprobe |
| Executable | whisper-cli | PRESENT | /opt/homebrew/bin/whisper-cli |
| Executable | ollama | PRESENT | /opt/homebrew/bin/ollama |
| Executable | node | PRESENT | /opt/homebrew/bin/node |
| Vendor | model manifest | PRESENT | /Users/Nadish/projects/AI Video Editor./Reel Studio_M4_offline_vendor_2026-11-11/model_manifest.json |
| Cached model | vasista22/whisper-telugu-large-v2 | SIZE MATCH | 10 entries; 0 unavailable or wrong size |
| Cached model | openai/whisper-large-v2 (config) | SIZE MATCH | 1 entries; 0 unavailable or wrong size |
| Cached model | ai4bharat/indic-parler-tts | SIZE MATCH | 8 entries; 0 unavailable or wrong size |
| Cached model | google/flan-t5-large (tokenizer) | SIZE MATCH | 4 entries; 0 unavailable or wrong size |
| Cached model | ggml-large-v3-turbo.bin | SIZE MATCH | 1 entries; 0 unavailable or wrong size |
| Cached model | ollama qwen3:14b | SIZE MATCH | 5 entries; 0 unavailable or wrong size |

## Findings and next work

- Treat missing inputs as qualification blockers, not demonstrated engine defects.
- Legacy narration parity files must be recovered selectively from a verified historical source,
  with provenance and hashes, or replaced by a reviewed compatibility strategy. Do not silently skip parity.
- Planner project metadata is present; its build/words.json is missing. The model integration test
  needs a reviewed fixture override in a disposable root, rather than writing into protected reel_002.
- The ASR reference uses a sibling raw-footage path. An isolated run needs an explicit copied input
  and a reviewed reference-path override; do not point a writing harness at a historical project.
- `test_transcribe.py` prints a verdict but does not set a failing process exit status when thresholds fail.
  Any acceptance runner must inspect its JSON and enforce CER <= 0.25, timing >= 0.8, and English success.
- Vendor discovery is relative to checkout parent in the existing offline checker; the isolated checkout
  needs explicit configuration before that checker can represent the supported installation.
- Next: inspect and prepare the deterministic title/frame self-test in a disposable execution root,
  resolving missing fonts and brand assets first. Keep model/render acceptance deferred until inputs are ready.
