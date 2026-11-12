# Visual Poster Studio — bounded implementation handoff

Date: 2026-11-10, America/Toronto. **Implemented draft subset; NOT an independently accepted or complete Visual Poster Studio milestone.** Layer reordering remains an outstanding acceptance requirement. Native Telugu typography approval, native IME and full accessibility remain open.

Workspace: `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`.
Authority: user's bounded 18-new-file implementation and synthetic browser-test authorization. No accepted source or frozen format was modified. No real media, OCR, agent activation, M4 integration or production deployment occurred. Gate A remains BLOCKED and unchanged.

## Exact new files

```text
visual_poster_studio/__init__.py
visual_poster_studio/__main__.py
visual_poster_studio/service.py
visual_poster_studio/server.py
visual_poster_studio/scene.py
visual_poster_studio/fonts.py
visual_poster_studio/exports.py
visual_poster_studio/index.html
visual_poster_studio/app.js
visual_poster_studio/styles.css
visual_poster_tests/test_scene.py
visual_poster_tests/test_fonts.py
visual_poster_tests/test_service.py
visual_poster_tests/test_http.py
visual_poster_tests/browser_acceptance.html
visual_poster_tests/browser_acceptance.js
tools/run_visual_poster_tests.py
docs/VISUAL_POSTER_HANDOFF.md
```

All paths were checked unused, including ancestor symlinks, before creation. One frontend authoring command stopped because the new test directory had not yet been created; that directory was then explicitly created and authoring completed. No accepted file was involved. All task edits are confined to these files and fresh runtime roots. The initial 154-file non-runtime baseline is retained at `.runtime/studio-ui/visual-implementation-20261110-01/baseline.json`. Final source, baseline and artifact association is recorded alongside it in `completion.json`; none of the earlier evidence was overwritten.

## Architecture and dependencies

`VisualStudio` composes the unchanged manual `Studio` for creation, edits, undo/redo, save and reopen. It uses accepted creative@1 source, without adding font assets, modifying content, creating approvals or changing accepted persistence contracts. Existing 32 content slots and 64 total layers remain. A new read-only scene projection checks the manual subset and maps the authoritative elements in array paint order to one deterministic SVG.

The app displays that exact SVG as an image. The browser rasterizes the same bytes through Canvas, PNG-encodes them, decodes the PNG and checks every RGBA byte against the raster before submitting an explicit draft export. Selection/UI decorations are excluded. The server saves the exact generated SVG and bounded browser-generated PNG, with source fingerprint, revision, profile, SHA-256 identities, font hashes and browser-reported QA. No alternative backend is substituted.

Pinned local fonts are reused directly, not copied or installed:

- Inter Bold: `00fd6f4691ee8884a33b46bf45851b341927c37c30064f558e1befb242971c49`.
- Noto Sans Telugu Black: `42a3167fc2d8ca089b03dcbfcdfe673ecaa176545944ea9c50377144947ae383`.

Both font files and their adjacent OFL-1.1 notices are checked at startup. SVG metadata includes both full copyright/licence notices so the embedded font copies travel with their required notices. Fonts remain unmodified. Other renderer/runtime redistribution and clean offline browser/Python rebuild closure are not established.

Browser FontFace performs shaping; application code only reads cmap coverage from hash-qualified sfnt files. No shaping, codec, canvas-interaction framework or PNG encoder was rebuilt. No new dependency, download, package manager, model, font import or cloud service was used. Python standard library and existing browser facilities are required. The prior Puppeteer/Sharp/HyperFrames adapter is neither invoked nor changed.

## Supported profile and failure behavior

Fixed 1080×1350, transparent, two pinned weights, explicit newlines, baseline 1.02×size and line spacing 1.65×size. Text is never trimmed, normalized, automatically wrapped or shrunk. Unsupported characters, styles or views produce diagnostics. Only text, rectangles and ellipses render; no image/video or arbitrary SVG import exists.

The browser checks ink bounds against each layer box and canvas, plus line overlap. Invalid output disables export while manual editing remains available. Unsupported glyphs are refused instead of silently choosing a system font. Font-load failure disables exports. Embedded-font probes compare pinned-font SVG raster output with explicit monospace controls; this is useful browser qualification evidence, not proof that every complex-script glyph sequence is correct. Native-reader visual approval remains required.

Bounds: 64 layers, 32 text layers, 8 MiB stored project, 20,000 active Unicode code points, 64 explicit lines/layer, 4 MiB SVG, 8 MiB PNG, one in-flight export, 15-second handshake, 20 retained export sets and 256 MiB export storage/session. Failed/incomplete export directories count toward quota and are retained. No quota eviction or overwriting occurs. Client operations have individual timeouts; server rejects expired/stale handshakes. These application bounds do not establish a hard browser RSS/CPU quota and do not revise Gate A.

## Local security boundary

Loopback binding only. Accepted Host/Origin/CSRF rules are reused. Ordinary requests retain the accepted 64 KiB limit; only generated-PNG completion allows up to 12 MiB JSON, with PNG decoded-byte bound 8 MiB. Requests cannot choose filesystem paths. New files use fresh server-generated directories and exclusive creation, with symlink/hard-link checks. SVG contains escaped text and fixed generated elements/styles/font URIs; no script, events, external links, imported markup, foreignObject, filters or animation. New CSP permits self-hosted modules, generated styles, blob images and embedded data fonts, without external network destinations.

PNG headers/dimensions are checked without decoding arbitrary submitted media on the server. This is a trusted-local browser-generated export workflow, NOT an untrusted PNG import API. A hostile local API caller can forge browser-reported QA; receipts are not authenticated visual attestations or approval records. Concurrent malicious filesystem races and local malicious actors remain outside the inherited manual tool's threat model. There is no hostile-media sandbox or production-security claim.

## Commands and reproducible tests

Run from the exact workspace above:

```sh
python3 -I -B tools/run_visual_poster_tests.py --run-id visual-tests-20261110-01
python3 -I -B tools/run_visual_poster_tests.py --run-id visual-tests-20261110-02
python3 -I -B tools/run_visual_poster_tests.py --run-id visual-tests-20261110-03
python3 -I -B tools/run_visual_poster_tests.py --run-id visual-tests-20261110-04
env -u NODE_COMPILE_CACHE node --check visual_poster_studio/app.js
env -u NODE_COMPILE_CACHE node --check visual_poster_tests/browser_acceptance.js
python3 -B -m visual_poster_studio --port 8766
```

- Run 01: exit 1, 35 tests, 0 assertion failures, 8 HTTP setup errors from the host's loopback-binding restriction. Preserved.
- Run 02 with authorized loopback permission: exit 0, 35 tests, no failures/errors.
- Run 03 after additional boundary regressions: exit 0, 42 tests, no failures/errors.
- Final run 04 adds embedded font-notice coverage and tests final source: expected 43; actual results/transcript are authoritative in `.runtime/studio-ui/visual-tests-20261110-04/`.
- JS syntax checks passed before initial browser testing and are rechecked against final source. No legacy test suite or package manager ran.

The runner permits writes only to its fresh named evidence root, denies child processes and external network endpoints, and enforces a 60-second suite deadline. It tests text capacity/line refusal, deterministic SVG/Unicode/geometry/order, source immutability, missing/changed fonts, malformed requests, CSRF/Host/Origin, aliases, stale/duplicate/expired exports, output count/storage, approval non-resurrection and analysis OFF. Alias-negative fixtures remain entirely inside the fresh root. Results retain source and protected-baseline hashes. Audit hooks are scoped evidence, not an OS sandbox.

Startup was exercised three times on loopback, each with a distinct fresh root. The first process was lost with the deliberately interrupted tool session; later scoped process inspection found it absent. The second test server exited 0 on SIGINT. The final server is stopped after verification; its exit is recorded in the completion report.

## Browser evidence and actual draft artifacts

The final in-app browser reported Chrome/157.0.0.0. No browser process was provisioned by the app. Final browser evidence:

`.runtime/studio-ui/visual-session-20261111T035056-81b69b5b/browser-evidence-57a7ea702f68646f.json`

All 14 browser checks passed: embedded-font differential probes; origin-clean PNG encode/decode; exact full RGBA equality; saved SVG identity; Telugu/mixed bounds; undo/redo; exact save/reopen; intentional overflow; Telugu conjuncts, ZWJ/ZWNJ, vowel signs; composed/decomposed Latin accents; multiline mixed text; analysis OFF. These checks show repeatable rendering behavior, not linguistic correctness. Console error inspection was empty.

Final licensed SVG/PNG pair:

`.runtime/studio-ui/visual-session-20261111T035056-81b69b5b/exports/draft-88b05d8848264cea/`

- SVG SHA-256: `d5077f930fa6d4689ea74bb12832444ec86e9ea538b1f6c705d043d4b5a9b9e2`.
- PNG SHA-256: `387c1596a135013e10168972b7a8514f56b495148beb95787c314976eedfa20e`.
- Manifest: draft only, revision 1, font hashes and browser QA retained.

Earlier preserved UI browser calibration exercised text sizing, rectangle/ellipse addition, position, fill, save and actual PNG export. It has its own manifest and screenshot:

`.runtime/studio-ui/visual-session-20261111T034816-d9d9e2f4/exports/draft-0aa0676e4c383e35/`

`.runtime/studio-ui/visual-session-20261111T034816-d9d9e2f4/browser-visual.jpg`

The later SVG adds licence metadata without changing raster pixels. Earlier artifacts remain intact. Visual inspection showed legible Telugu/English lines on the checkerboard preview, with no visible tofu/clipping in the inspected fixture. This is not a native Telugu typography signoff. No claim of cross-browser pixel identity, print colour fidelity, professional design quality or complete glyph coverage is made.

## Startup, storage and rollback

```sh
cd "/Users/Nadish/projects/AI Video Editor./Codex/AI Studio"
python3 -B -m visual_poster_studio --port 8766
```

Open `http://127.0.0.1:8766/`. Startup prints the exact fresh runtime root. Use Create, Apply edits, Save and Reopen; browser PNG becomes available only after local qualification. Export paths/hashes are shown in the UI. Files are saved locally, not automatically downloaded to the browser's Downloads folder. Analysis controls remain disabled.

This CLI intentionally starts fresh sessions; Visual Studio session-resume/import is not implemented. Save/reopen works in the running session and saved creative.json persists after shutdown. Unsaved drafts are lost on exit. There is no silent migration, scanning of previous accepted sessions, automatic repair or stronger power-loss guarantee.

Rollback: save work, stop this service with Ctrl-C and run the unchanged `studio_manual_ui` separately on 8765. Retain all outputs/evidence. No project migration, file removal, accepted-code replacement, agent rollback or production swap is required.

## Separately reviewable reorder transaction proposal — NOT IMPLEMENTED

The accepted public core API has no reorder operation. Do not simulate reorder through remove/add, UUID sorting, direct private mutation, or multiple history transactions.

Proposed future API operation: `{op: "reorder", view_id: <existing-view-id>, ordered_element_ids: <complete-permutation>}`. Implementation requires separate explicit authorization to extend accepted core APIs; it is not part of this 18-file milestone.

Preconditions: validate the complete document; validate exact fields and types; check current revision under the UI writer lock; require every and only element belonging to that view exactly once. Reject duplicate, missing, foreign-view or unknown IDs and no-op permutations. No implicit inclusion of other views.

Candidate construction: deep-copy the current document; replace only the slots occupied by the target view's elements with references to the copied elements in requested order. Preserve every element's identity/fields, all content/assets, other-view relative order and all non-order properties. Validate the candidate.

Commit: one ordinary accepted transaction with full before/after core snapshots, operation label `reorder`, one revision increment, redo-tail truncation, standard history-limit handling and current approvals cleared. Reuse the central core commit path only after it is formally extended; never copy private commit logic into the UI. No persisted field/schema change should be necessary, but compatibility review must confirm operation-label handling. Undo/redo restores exact arrays without resurrecting approvals. Prior approved snapshots/export manifests remain immutable and identifiable.

Acceptance: full permutation validation, cross-view preservation, atomic failure, stale revisions, history limit, single-step undo/redo, no approval resurrection, source/save/reopen compatibility, visual overlap fixtures demonstrating paint order and matching SVG/PNG. Review the exact future core diff and compatibility evidence before allowing UI reorder controls. User acceptance or explicit deferral is required before the entire Visual Poster Studio milestone can close.

## Outstanding acceptance conditions

- Layer reordering is not implemented or accepted; full milestone remains open.
- Native Telugu visual review and native IME composition; full accessibility review.
- Browser/runtime variation and complete offline distribution/build/licensing closure.
- Exact glyph coverage plus font loading does not prove all contextual shaping behavior.
- Fresh-session-only CLI; no Visual Studio session-resume workflow.
- Browser QA uses trusted-local reports, not an authenticated approval mechanism.
- Ordinary inherited persistence and filesystem race limitations; physical power-loss durability unverified.
- Actual image/poster reference analysis, English/Telugu OCR and reel/video analysis remain required eventual capabilities, disabled pending separately authorized Gate A qualification.

STOP: bounded implementation and evidence reporting only. No R2–R6, M4 integration or production authorization follows.
