# Visual Poster Studio — editing improvement batch

Date: 2026-11-10, America/Toronto. Authorized controlled editing improvement batch. Implemented and tested; not full product/milestone acceptance. Native Telugu IME and complete accessibility signoff remain open.

## Changes

1. Composition-aware text entry. Browser compositionstart/compositionend, KeyboardEvent.isComposing and legacy keyCode 229 are respected. While composing, application commits, exports, layer switching and application shortcuts are blocked; the text control is not disabled or rewritten. Availability refresh does not rerender the editor during composition, preserving text and caret. No normalization, transliteration, shaping implementation or OS input-source change was added.
2. Explicit text status: code-point and line counts, composition status and a warning when preview represents the last applied revision. Pending text disables export until explicitly applied/saved. Ctrl/Cmd+Enter applies text, Ctrl/Cmd+S saves, and application undo/redo shortcuts operate outside editable fields. Native text undo remains with the browser.
3. Draft-safe layer selection. Pending text is applied through the unchanged public transaction path before switching layers. A single selected layer participates in the Tab sequence; Arrow Up/Down and Home/End select layers. Focus returns after layer selection and text application. Applied text remains in normal undo/redo history.
4. Accessibility improvements: skip link, labelled fieldset and preview region, layer keyboard guidance, text descriptions, live notices, busy state, stronger focus outlines and improved text contrast. These changes are not a WCAG conformance or VoiceOver certification.
5. Professional workspace layout: layers adjacent to the preview, responsive inspector placement, internally scrollable poster stage, Fit/25/50/75/100% preview zoom, better Telugu/English editing typography using already-loaded pinned fonts, and automatic collapse of New project after creation. Zoom changes presentation only; source geometry and export resolution stay fixed.
6. Preview response identity checks prevent an outdated request from replacing the current project's scene. Editing remains locked until the operation's preview check completes; source edits during export are disabled in the UI. Backend stale-export checks remain unchanged.

## Exact files

Modified:

```text
visual_poster_studio/app.js
visual_poster_studio/index.html
visual_poster_studio/styles.css
visual_poster_studio/server.py
tools/run_visual_resume_tests.py
```

Created:

```text
visual_poster_studio/editing.mjs
visual_poster_tests/test_editing.mjs
visual_poster_tests/editing_browser.mjs
visual_poster_tests/test_editing_ui.py
docs/VISUAL_EDITING_BATCH_HANDOFF.md
```

No creative_core, accepted manual UI, R1, renderer mapping, font, export, journal, agent, M4 or production implementation was modified. Gate A remains unchanged. No real image/video/OCR execution, installation, package manager, model or paid service was used. Existing evidence was retained.

Before editing, target paths/ancestors were checked and a 154-file in-scope baseline captured under `.runtime/studio-ui/visual-editing-batch-20261110-01/`. R1 source/tests and R1/G1 records were excluded from content reads. `completion.json` records exact before/after hashes, created-file hashes, unchanged baseline verification and final evidence identity. No forensic whole-machine or independent R1 hash audit is claimed.

## Reuse and rendering preservation

Reuse native HTML textareas, browser composition events, focus controls and keyboard behavior; no canvas interaction framework or font shaping system was implemented. UI Events reference consulted: https://www.w3.org/TR/uievents/#events-compositionevents . The only new JS helper is small application policy for composition/shortcuts, text statistics, layer navigation and zoom. Tests use existing Node's built-in assert and Python's standard library. No third-party dependency/licence adoption occurred.

`scene.py`, `fonts.py`, `exports.py`, source format, render profile and pinned font bytes are unchanged. Preview remains the same deterministic SVG; PNG is still browser-native with exact decoded RGBA comparison and fail-closed qualification. The editing textarea can use the already-loaded local fonts; its visual font fallback behavior does not alter export font policy or document bytes.

## Commands and results

From `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`:

```sh
env -u NODE_COMPILE_CACHE node visual_poster_tests/test_editing.mjs
env -u NODE_COMPILE_CACHE node --check visual_poster_studio/app.js
env -u NODE_COMPILE_CACHE node --check visual_poster_tests/editing_browser.mjs
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-editing-regression-001
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-editing-regression-002
```

Initial pure-policy test exited 1 because the fixture incorrectly expected eight code points for `తెలుగు\né`; the exact count is nine. Fixture expectation corrected; policy implementation unchanged. Subsequent policy checks passed all 27 assertions.

Regression run 001: exit 0, 118 tests, zero failures/errors/rejected operations. Includes 37 existing core, 43 existing Visual, 35 reorder/resume/compatibility/recovery and three new semantic UI checks. The new runner imports existing tests unchanged and redirects core fixtures to its fresh evidence root. No legacy runner is executed. Existing bounded synthetic child-server, ENOSPC, sync and SIGKILL tests remain included, with loopback-only traffic and fresh output roots.

Final run 002 covers final source after browser fixes; `results.json` and `tests.txt` are authoritative for count, exits and source identities. Final JS policy/syntax output is retained at `.runtime/studio-ui/visual-editing-batch-20261110-01/editing-policy-tests.txt` and completion metadata. Node compile cache is unset; no package manager or browser package is installed.

## Browser acceptance and failures retained

A fresh Visual-owned root was started with:

```sh
python3 -B -m visual_poster_studio --root "/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/studio-ui/visual-editing-browser-20261110-01" --port 8769
```

The test-only harness is loaded only by `http://127.0.0.1:8769/#editing-checks`. It creates a synthetic project through UI actions and dispatches synthetic CompositionEvent/KeyboardEvent events. It does not establish physical keyboard input, macOS Telugu IME correctness, candidate-window behavior or actual native composition cancellation.

Initial browser run failed the focus-restoration timing check. It also revealed that some property buttons remained individually disabled after composition ended. Both were fixed before further work: operation controls now remain locked until preview completion and focus restoration; property and acknowledgement controls are recomputed correctly. The failed result remains in `initial-browser-failure.txt`; its synthetic project was explicitly saved and retained.

Corrected browser run: all 12 checks passed. Evidence: `browser-evidence-f74e1d60f5a2e890.json` inside the fresh browser root. Checks cover composition commit/shortcut refusal, caret/text preservation through availability refresh, explicit Apply after composition, exact Unicode, focus return, preview-only zoom, Home/End layer selection/focus, draft preservation on layer switching, saved Telugu/combining marks, analysis OFF and skip-link/descriptions. Native IME verification is explicitly false in the evidence.

The normal UI was then checked without the harness: open the saved project, select/reposition geometry, save and export. `browser-proof.json` records UI source revision, preview/export identity, composition results and console errors; `editing-workspace.jpg` is the full-page visual evidence. No final browser console errors were observed.

Actual export:

`.runtime/studio-ui/visual-editing-browser-20261110-01/exports/draft-52fd4895d8c7c7ef/`

```text
SVG a516b0434f35f71a3ce22e9070352ffc061b8c3972a1cbcc7a21f220da49378f
PNG cdc3c3a0e0d1063a10e730d80ba05b494ccd88aa0cdba1a01f1276c43115e63f
```

Manifest reports exact preview-raster/PNG-decoded RGBA equality. Exports remain draft only. Native Telugu visual/editorial approval and cross-browser pixel identity are not inferred. The service was stopped with SIGINT, exit 0.

## Startup and remaining issues

Start normally with `python3 -B -m visual_poster_studio --port 8766`, or explicit `--resume --root <new-Visual-owned-root> --port 0`; prior legacy-session adoption remains deferred. No migration or release follows this batch.

Remaining noncritical items:

- Hands-on native macOS Telugu keyboard/IME, candidate selection and composition cancellation testing. Synthetic composition guards are implemented; this acceptance requirement is not closed.
- VoiceOver and broader keyboard/accessibility audit, browser zoom/mobile-device checks, and independent native Telugu visual approval. Contrast was improved, not comprehensively certified.
- Existing discard/reopen browser-confirm interactions remain outside this batch; a consistent in-page unsaved-change workflow is a reasonable next UX improvement.
- No direct canvas drag/resize, rich text, font chooser, automatic wrapping or new geometry transactions were added.
- Existing history-v2 old-reader incompatibility, explicit-only recovery and offline distribution/build closure remain documented limitations.

Recommended next batch: hands-on native Telugu IME and VoiceOver acceptance, then bounded in-page unsaved-change/recovery guidance and selection/geometry workflow improvements through reviewed existing contracts. Keep renderer/profile identity and exact export parity checks as regression gates. No image/OCR/video backend activation is implied.

STOP: this editing batch is complete pending independent acceptance. No full Visual Poster Studio, M5 or production release claim is made.
