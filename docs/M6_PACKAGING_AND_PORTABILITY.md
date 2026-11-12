# M6 step 8: packaging, offline readiness and Windows audit (12 Nov 2026)

Status: analysis and checks done. No packaging change was made: the choice below is the owner's.

## 1. Offline readiness on this Mac: PASS

`tools/m6_offline_check.py` is read-only. It checks every requirement by name, size and version; it downloads, installs and starts nothing.

Result: **31 checks, 0 required missing.**

| Area | What is required | State |
|---|---|---|
| System | macOS on Apple Silicon | Darwin 25.6, arm64 |
| Python | `~/.venvs/reelstudio` (app, engine, M5 code), `rs_tts` (narration), `rs_asr` (Telugu STT), all 3.12.16 | present; all three archived in the M4 offline vendor bundle |
| Tools | ffmpeg/ffprobe, whisper-cli, ollama (required); node/npx (UI rebuild, M5 JS tests, HyperFrames) | present; every one has a Homebrew bottle in the vendor bundle |
| Models | Telugu STT (pinned weights), Whisper config, Indic Parler-TTS, flan-t5 tokenizer, whisper.cpp large-v3-turbo, Qwen3 14B (8B optional) | all files present, sizes match the vendor manifest (about 20.8 GB, on the same disk) |
| App | built UI, UI packages, engine fonts, M5 pinned fonts (hash-checked), engine models | present |
| Policy | paid AI providers | all switched off |

Not in the vendor bundle:
- HyperFrames 0.9.9 (global npm) and Google Chrome. Neither is needed by the app's own reel or poster flow. They are only used for hand-made motion compositions (like reel_002's) and M5's legacy renderer.
- The models themselves: a copy on another disk is still the owner's decision (vendor README).

## 2. No-network run: PASS

`tools/m6_offline.sb` is a macOS sandbox profile that blocks all traffic leaving the Mac. Loopback (the app's server, Ollama) and local sockets stay open. Proof first: inside it, `https://example.com` is unreachable while `http://127.0.0.1:8775` answers.

Inside the sandbox:
- all M6 suites pass: approved content 6, poster QA 8, brands 3, engine jobs 2, server routes 8;
- M5's own tests pass under M4's Python: binding 24, director 23;
- a full reel_002 render in an isolated job root passes QA on all 8 checks, including the locked baseline: 1849 frames, -14.1 LUFS, -1.4 dB, 19 s.

The built UI fetches nothing from outside. The only URLs in it are SVG/XML namespace identifiers, a React error-doc link in error text, and Tailwind's banner comment.

Not covered: a *clean* Mac (fresh user account, nothing installed) restored only from the vendor bundle. It needs a second machine or account, and an external copy of the 20.8 GB of models.

## 3. Windows: what blocks it today (static audit)

| # | Severity | Where | Problem on Windows | Fix direction |
|---|---|---|---|---|
| 1 | Critical | `engine/common.py` heavy-model lock, `engine/adapter.py` render lock | `os.kill(pid, 0)` is a liveness probe on POSIX but terminates the process on Windows | Platform-specific "is this pid alive" helper (engine change, needs a new release gate) |
| 2 | High | `m5/studio_manual_ui/service.py`, `m5/visual_poster_studio/brands.py` | `fcntl.flock` writer locks; M5 refuses to start on non-POSIX (`studio_local.py`) | Codex: portable lock (msvcrt.locking or lock files) |
| 3 | High | M5 `session.py` / `persistence.py` | Directory `fsync` via `os.open(dir)`, not supported on Windows. M5 blocks saving when sync fails | Codex: platform durability strategy |
| 4 | High | Telugu shaping | M4 titles/captions use Pillow with RAQM (HarfBuzz/FriBiDi). Windows Pillow wheels need FriBiDi supplied separately | Bundle and test FriBiDi; compare Telugu renders with the Mac |
| 5 | Medium | `app/server.py` job runner | `/usr/bin/time -l` (macOS) for peak memory; process groups (`start_new_session`, `killpg`) for cancel | Measure memory with a portable call; Windows job objects for cancel |
| 6 | Medium | `engine/asr.json`, `tts.json`, `app/engine_jobs.py`, tools | `~/.venvs/<env>/bin/python` paths (Windows venvs use `Scripts\python.exe`) | One configured interpreter path per environment |
| 7 | Medium | `app/engine_jobs.py`, M5 path checks | Symlinks for job-root fonts/models (need Developer Mode or admin on Windows); M5 refuses symlinks and hard links by design | Copy or junction on Windows; keep M5's refusal |
| 8 | Medium | Launcher | `Start Reel Studio.command` (bash, `open`, `curl`) | A small native shell (see §4) or a `.bat`/PowerShell launcher |
| 9 | Low | UI fonts | `.te` falls back to macOS Telugu fonts after Noto Sans Telugu | Bundle a Regular-weight Noto Sans Telugu (licence OFL), or accept Nirmala UI on Windows |
| 10 | Low | `engine/tts_worker.py` | `resource` module (POSIX) for memory limits | Platform check; Windows uses a job-object limit |
| — | Mac only | `tools/m6_offline.sb`, M5 legacy renderer, gate tools | `sandbox-exec`, Homebrew paths | Test tooling only; not part of the product |

Everything else checked is already portable: FFmpeg, Ollama, whisper.cpp, PyTorch on CPU, FastAPI, the React UI, and SQLite.
Models are the same files. Apple-specific acceleration is not used by the current product (M5's local AI is NO-GO).

Rough order: #1 and #2–3 are correctness/safety blockers. #4 is a quality blocker for Telugu. The rest is packaging work.

## 4. Packaging options (owner decision)

| Option | What the owner gets | New dependencies / network | Windows path | Recommendation |
|---|---|---|---|---|
| A. Keep the launcher (today) | Double-click `Start Reel Studio.command` on port 8775; app opens in the default browser | none | separate `.bat` launcher | Keep for M6 development and personal use now |
| B. Local `.app` wrapper | IDEAFRAME in the Dock and Launchpad with its own icon; same server + browser underneath | none (plain bundle + script, built offline) | — | Good small step once the approved logo vector master exists (icon) |
| C. Tauri 2 shell (MIT/Apache) | Real app window (WKWebView on Mac, WebView2 on Windows), Python server as a sidecar, installers, auto-start/stop | Rust toolchain + crates (one-time download, owner approval); signing and notarisation for distribution | yes, same code | Choose when the app is given to other people or Windows is needed |
| D. Electron | App window with its own Chromium | Large (~150 MB+) runtime; Codex already declined it in M5 | yes | Not recommended |

What any distributed build still needs, whichever shell is chosen:
- a relocatable Python runtime instead of `~/.venvs`;
- a first-run model installer with provenance and licences, including Indic Parler-TTS's gated-download terms;
- an FFmpeg licence review (current Homebrew build is GPL);
- signing and notarisation;
- the approved app icon;
- a clean-machine restore test.
