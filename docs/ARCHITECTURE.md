# IDEAFRAME / Reel Studio architecture

## Operating principles
Offline-first macOS pipeline, local files, optional locally installed AI models, explicit human editorial gates, reproducible media exports. No cloud calls in the foundation package. Never auto-publish.

## Seven modules (proposed mapping; verify against existing M1–M7 ownership)
- M1: ingest scripts, speeches, transcripts, media; normalize metadata.
- M2: local transcription and Telugu/English language handling (Whisper adapter planned).
- M3: local AI storyboarding, hooks, captions, claim extraction (Qwen3 adapter planned).
- M4: narration / voice pipeline and release qualification (Indic Parler-TTS adapter planned; not qualified).
- M5: editing, scene composition, subtitle timing (incomplete).
- M6: FFmpeg render, profiles and media QA.
- M7: packaging, release readiness, integrity verification and deployment (not production ready).

These names are an implementation proposal, **not** a claim that pre-existing modules have been inspected or integrated.

## Current foundation
`models.py`: versioned JSON manifest and explicit approval fields. `planning.py`: deterministic offline scene suggestions, not AI generation. `render.py`: gated FFmpeg export for 1080x1920 MP4. `cli.py`: local project initialization, planning, export.

## Security and integrity
Scripts and model output are untrusted. FFmpeg runs as a fixed argument list, not a shell command. Never bundle model weights, private media, credentials, or licensed voices in Git. Human approvals are editable local manifest fields: this is a **prototype gate, not tamper-proof authorization**. Add signed audit logs, model checksums, provenance, safety review, and operator identity before release.

## Qualification gates
M4 voice quality and language evaluation; M5 scene/caption correctness; M6 audiovisual QA (duration, loudness, black frames, clipping, aspect ratio); M7 model integrity, notarized macOS packaging, regression tests and human sign-off. No production release claim until gates pass.

## Deployment
Local macOS Python 3.11+ runtime and system FFmpeg (`brew install ffmpeg`). Install with `pip install -e '.[dev]'`. No server deployment or cloud API key required. Future macOS distribution should be signed/notarized and ship optional model downloads with verified hashes and licensing review.
