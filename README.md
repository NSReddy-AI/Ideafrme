# IDEAFRAME — Reel Studio

**Offline-first, human-controlled AI video-production studio for macOS.** Transform scripts, speeches, transcripts and media into Telugu/English short-form videos for Instagram, YouTube and Facebook.

> Status: **development foundation only**, not a production release. Local model adapters, narration, editor UI and full M4–M7 qualification are pending.

## Implemented foundation
- Local versioned JSON project manifests (UTF-8 Telugu/English)
- Offline deterministic scene planning (not yet AI-generated)
- Human approval fields for scenes, factual claims, quotes, timing and export
- FFmpeg export to vertical 1080×1920 H.264/AAC MP4
- Unit tests, macOS CI and release roadmap

## Setup (macOS)
```sh
brew install python@3.11 ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Usage
```sh
printf 'A compelling opening. A practical conclusion.\n' > script.txt
ideaframe init script.txt workspace/demo.json --title 'My Reel' --language en
ideaframe plan workspace/demo.json
```

Open `workspace/demo.json` in a text editor and review the proposed scenes. Set each scene's `approved` field to `true` **only after reviewing it**. After factual claims, quotations, timing and export are reviewed, set the four corresponding approval fields to `true`.

```sh
ideaframe export workspace/demo.json input.mp4 exports/demo.mp4 --profile reels
```

Exports are **blocked by default** until every gate is approved. This foundation requires an existing source video; it does not yet synthesize scenes, narration, or captions. There is no automatic publishing.

## Architecture and release readiness
See [architecture](docs/ARCHITECTURE.md) and [roadmap](docs/ROADMAP.md). All core workflows are designed to run locally; future adapters may use Whisper, Qwen3, and Indic Parler-TTS with explicit model integrity and licensing checks.
