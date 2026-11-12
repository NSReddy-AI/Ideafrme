# Visual Poster Studio — integrated manual workflow batch

Date: 2026-11-11, America/Toronto. Controlled development under the existing Visual Studio scope. Implemented a working manual workflow; **not full AI Reel Studio completion, independent acceptance or release**. Actual image/poster analysis, English/Telugu OCR and reel/video reference analysis remain required but disabled pending separate qualification/authorization. Gate A is unchanged.

## Implemented

- Remove selected layer through the existing public core `remove` operation, with current-revision validation and one core transaction. Undo restores exact layer identity/order/content; content records remain preserved. Approval invalidation is inherited unchanged from the core.
- In-page native HTML dialog choices replace application `window.confirm` calls for reopen and pending-text undo/redo. Cancel preserves drafts. Reopen offers Save and reopen, Discard and reopen, or Cancel. Pending-text undo can explicitly apply text before undo, preserving it on the redo branch. Removal explicitly warns that Undo restores the layer and saved files remain unchanged until Save.
- Confirmation captures project identity, revision and selection. Stale local confirmation is refused; backend current-revision checks remain authoritative against changes from another tab.
- Alt+arrows nudge selected layers by one source pixel; Alt+Shift+arrows use ten. Editable fields and IME composition retain their native keyboard handling. This reuses the accepted move operation, without adding geometry/schema APIs.
- Targeted backend, policy and integrated browser coverage. No new renderer, engine, font, dependency, media or approval feature.

## Exact file changes

Modified:

```text
visual_poster_studio/service.py
visual_poster_studio/app.js
visual_poster_studio/index.html
visual_poster_studio/styles.css
visual_poster_studio/editing.mjs
visual_poster_tests/test_editing.mjs
visual_poster_tests/editing_browser.mjs
tools/run_visual_resume_tests.py
```

Created:

```text
visual_poster_tests/test_workflow.py
docs/VISUAL_WORKFLOW_BATCH_HANDOFF.md
```

Paths and symlink ancestors were checked before edits. A 159-file in-scope baseline is retained in `.runtime/studio-ui/visual-workflow-batch-20261111-01/baseline.json`. Completion metadata records exact changed/new hashes, unchanged baseline files and test-source association. R1 source/tests and R1/G1 records were excluded from content reads. No M4 or production access occurred. All generated data is in fresh runtime roots; previous evidence remains retained.

`creative_core`, accepted manual UI, scene mapper, fonts, exports implementation, journal, session ownership and Media Analysis Agent remain unchanged. Existing history-version and recovery guarantees remain in force. No schema/API change or dependency installation was made.

## Tests and commands

```sh
env -u NODE_COMPILE_CACHE node visual_poster_tests/test_editing.mjs
env -u NODE_COMPILE_CACHE node --check visual_poster_studio/app.js
env -u NODE_COMPILE_CACHE node --check visual_poster_tests/editing_browser.mjs
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-workflow-regression-001
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-workflow-regression-002
```

Run 001 passed 126 Python tests, zero failures/errors/rejected operations. This includes the existing 118 checks and eight new removal tests: atomic revision/history, identity-preserving undo/redo, stale/unknown rejection, saved-file preservation, approval invalidation, empty-layer document/restoration and sticky history v2. Pure JS policy checks passed 35 assertions. Existing bounded process restart, recovery fault injection and protected-source checks remain included; no legacy runner or package manager executed.

Run 002 covers the final UI fixes and this handoff. Its results.json/tests.txt are authoritative. JavaScript output/exits are retained beside completion metadata. All suites write to their fresh roots and retain the existing bounded loopback/child-process guard.

## Integrated browser workflow

One fresh acceptance session:

```sh
python3 -B -m visual_poster_studio --root "/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/studio-ui/visual-workflow-browser-20261111-01" --port 8770
```

The test harness runs only with `#editing-checks`. It drives normal UI actions and synthetic composition events. Final run passed all 20 checks, including Telugu/combining-mark preservation, composition locks/caret, text application/focus, preview-only zoom, keyboard layer selection, draft preservation, removal confirmation/cancellation, remove/undo, cancelled reopen, save-and-reopen, explicit discard and keyboard nudge. Native OS IME remains explicitly unverified.

Retained failures:

- `browser-evidence-02f8dcb20dc5c6e1.json`: harness advanced after layer selection before the operation completed; waiting now includes the editor's busy state.
- `browser-evidence-f3a264c0c558efec.json`: new confirmation buttons remained disabled after composition. Fixed by explicitly restoring them when opening the dialog, refusing duplicate open requests and testing that Cancel actually closes it.
- Final passing evidence: `browser-evidence-f7a1394b60c9aa99.json`.

These files and their synthetic projects were retained; no old evidence was overwritten. No backend data-integrity failure was observed. The final normal UI opened the saved workflow project and exported SVG/PNG. `browser-proof.json` captures results and an empty console-error inspection; `workflow-workspace.jpg` captures the normal editor.

Actual draft export:

`.runtime/studio-ui/visual-workflow-browser-20261111-01/exports/draft-865f681815f70d0e/`

```text
SVG c10f4fa7865d3a9b7309fa63470a64eae043bd3da1985fdb719e2f7124e39224
PNG 0a4b7e9ff58fe716e2c655aa20c7c668339b9e54b672aca55c85235e56fb602f
```

Manifest reports exact decoded RGBA parity. This is a functional fixture, not a professional-poster quality endorsement. The renderer/font profile and deterministic SVG mapping were not changed. The test service stopped with SIGINT, exit 0.

## Operational scope and remaining work

Start fresh with `python3 -B -m visual_poster_studio --port 8766`, or use explicit `--resume --root <Visual-owned-root> --port 0`. The manual path now covers create, text/geometry editing, layer selection/reorder/removal, undo/redo, saving, reopening and draft SVG/PNG export. Process restart/resume and recovery remain covered by existing tests.

Still open: native macOS Telugu IME/candidate/cancellation testing; native Telugu visual signoff; full screen-reader/accessibility assessment; offline distribution/build closure; legacy-session adoption; direct canvas manipulation and richer typography/layout capabilities. Real image/OCR/reel/video processing and M4 integration are not authorized by this batch. No production deployment or paid-service action occurred.

Recommended next controlled development: selection-on-preview and bounded layout controls that can use existing contracts, plus clearer project/session/export navigation. Any new geometry transaction or persisted format should receive compatibility design before changing accepted core behavior. Consolidate remaining native IME/accessibility acceptance alongside those product improvements; do not block unrelated safe development on them.

No full product acceptance is implied by passing tests. Completed this bounded implementation/evidence checkpoint; further routine Visual Studio work remains governed by the user's standing controlled-development authorization.
