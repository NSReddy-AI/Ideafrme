# M4 completion report - feature by feature (11 Nov 2026, development copy)

Scope = the approved M4 handoff (Telugu/English branded reels; narration B1; safe areas B2; planner-to-reel B3) and CLAUDE.md.
Gate C (comprehensive regression) and Gate D (production release) are NOT done and NOT authorised. Nothing is ever published.
Start the app: double-click `Start Reel Studio.command` (or `~/.venvs/reelstudio/bin/python app/server.py`) -> http://127.0.0.1:8765

Legend: **App** = usable in the app screens; **CLI** = command line only; ✅ verified by a real run today.

## 1. Fully implemented and connected (app)
| Feature | Where in the app | Evidence |
|---|---|---|
| Project creation (brand × platform × style) | Home → New reel | ✅ app-created speaker, recorded, English projects |
| Project list, test projects hidden, archive / restore (nothing deleted) | Sidebar, project header | ✅ 3 check projects archived |
| Inputs: speaker video, slide pictures (renumbered), own recording, notes; remove a file (kept in inputs/.removed) | Step 1 Inputs | ✅ upload/remove via API |
| Source video change → old transcript/plan/edit moved to build/_superseded_* and approval withdrawn | automatic | ✅ (was a real bug: stale transcript reused) |
| Speaker framing (face position for the crop) with a frame preview | Step 1 → Framing | ✅ |
| Transcription (Telugu Whisper; English whisper.cpp) | Step 2 "Transcribe + draft the plan" | ✅ 63 s video; 17.5 % CER on the M3 reference, 4.4 GB peak |
| AI planning (local Qwen3 14B), hooks A-C + own hook D, number cards, tag, ❓ marks, full plan.md | Step 2 | ✅ |
| Caption spelling fixes (speaker's own words; original kept; approval withdrawn) | Step 2 → Captions | ✅ gate tested (PLAN_NOT_APPROVED until re-approved) |
| Plan approval (fingerprint; ❓ need "checked") | Step 2 → Approve | ✅ |
| AI narration: Prakash / Lalitha, News / Documentary, 1.0 / 1.15 / 1.20×, offline, 8 GB stop, cache, listening check | Step 2 (slides reels, Telugu brands) | ✅ demo reels 1-2 |
| Recorded narration (your own voice, any audio format) aligned to the approved script | Step 2 → "My recording" | ✅ m4a → 0.2 % error, QA PASS, no AI label |
| No narration (text + music) | Step 2 → "None" | ✅ demo reel 3 + English reel |
| Script review: written text, spoken numbers, ❓ number/long-sentence warnings, never rewritten; approve exact text | Step 2 | ✅ |
| Title page: own hook/sign/headline (slides) or approved hook (speaker); person cut-out + background uploads | Title page card | ✅ |
| Edit building (captions, number cards, graphics, music, AI disclosure) from approved material only | Step 3 Build | ✅ |
| Render + QA per platform (Instagram, YouTube, Facebook), versions, covers, contact sheets, safe-area warnings | Step 4 | ✅ 12/12 demo exports + app checks |
| Post copy draft per export (approved text + checked hashtags; AI-label reminder) | Step 4 → Post copy | ✅ |
| Job progress, readable errors with hints, peak memory, one job at a time, Cancel | Job panel | ✅ cancel stopped all 4 processes |
| System check (tools, Telugu layout, ASR/TTS envs, planner status, memory, settings problems) | Home | ✅ |
| reel_002 baseline read-only | automatic | ✅ API refuses writes |
| AI narration limited to Telugu brands (approved voices are Telugu narrators) | Step 2 | ✅ API refuses `ai` for English brands |

## 2. Command line only (not in the app) - by design or outside M4
| Feature | Status |
|---|---|
| Links / screenshots ingestion (`inputs/urls.txt`, Chrome headless) | assistant-driven step in CLAUDE.md, not an engine feature - not in M4 scope |
| `rs.py ingest` (inputs.json inventory) | not needed by the M4 flow (mode comes from the source video) |
| Face tracking (`facetrack.py`, M3, OFF by default) and background blur (`matte.py`) | manual M3 tools, not part of `build.py`; the app's Framing control covers the crop |
| English version of a Telugu reel (`assemble.py ... _EN`) | manual, outside M4 |
| Planner `--recheck` after hand edits of plan.json | the app has no hand-editing of plans (caption fixes + own hook D cover the approved needs) |
| Optional paid planners (Claude / Gemini / ChatGPT) | status shown in the app; off unless a key is set; never required |
| Narration speed method (rubberband / atempo) | engine default used |
| Changing a project's style/platform after creation | not in the app (create a new project; re-export covers platforms) |

## 3. Missing / incomplete approved functionality
None blocking. Open functional items (all in docs/M4_IMPROVEMENT_BACKLOG.md):
- Long narration scripts can hit the 8 GB voice stop on the last long sentence; a second press finishes it (the app now says so).
- Job list is kept in memory only (each job is also logged in the project history).
- No upload progress bar for large videos.
- English brands still have placeholder handles (@YOUR_..._HANDLE) - brand data for you to fill in.

## 4. Genuine blockers
None remaining. Fixed during M4 completion: no app layer; Telugu speech-to-text memory (24 GB → 4.4 GB, accuracy kept); slides title page crash;
no caption correction; no post copy; stale transcript after changing the source video.

## Checks run (targeted, 11 Nov)
- Full demo (once): 4 reels × 3 platforms, 12/12 QA PASS, 13 min 14 s, largest process 4.0 GB, no swapping.
- App checks: recorded narration (narrate 166 s, build 27 s, render 12 s, QA PASS); English text + music (build 15 s, render 6 s, QA PASS);
  source switch + framing + cancel; caption-fix gate; reel_002 write refused; AI narration refused for an English brand.

## Protections
Original `Reel Studio` folder: 127/127 files identical. reel_002 project, baseline file and exports unchanged. rs_tts / rs_asr unchanged.
New dependencies (approved 11 Nov): fastapi + uvicorn (~/.venvs/reelstudio, diff in tests/acceptance/M4_gateB/reelstudio_*_app.txt);
React / Vite / Tailwind in app/web (MIT). Engine files changed: asr_worker.py, transcribe.py, asr.json (backups *.preASRmem), new post.py.
