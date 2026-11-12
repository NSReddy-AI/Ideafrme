# History v3 and professional canvas geometry

Implemented in isolated M5 development; no production release or acceptance claimed.

## Contract

Content remains ai-reel-studio/creative@1, schema_version 1. No new element fields. Absent history.version remains legacy v1; v2 remains supported; v3 adds only `geometry` to the existing operation vocabulary. Unknown versions are refused. Legacy validation and ordinary edits do not upgrade documents.

Public core request: `{"op":"geometry","expected_revision":12,"view_id":"portrait","targets":[{"element_id":"title","x":80,"y":100,"width":800,"height":240}]}`. Targets must be nonempty, unique, same-view existing IDs with exactly all four geometry values. Existing finite-number geometry bounds apply. Stale revisions, booleans, invalid dimensions, foreign IDs, extra fields and whole-transaction no-ops are refused. Unchanged individual targets are allowed within an otherwise effective transaction. The commit deep-copies, validates all targets, performs one revision increment and snapshot pair, clears current approvals and truncates redo; it preserves IDs, paint order, content, other views, historical versions and exports. Persisted geometry history independently checks unchanged non-element content, element identities/order/nongeometry properties and exactly one changed view.

First v3 request from v1 OR v2 additionally requires acknowledge_upgrade:true and legacy_checkpoint_sha256. The Visual adapter creates a bounded immutable checkpoint using the existing journal quota/synchronization protocol; core verifies exact canonical pre-operation document bytes plus newline, SHA-256, confined path, single link, size and absent write permissions. Subsequent v3 requests omit upgrade fields at the core layer. Visual requests always include boolean acknowledge_upgrade, consumed by the adapter. Geometry validation failures leave working documents unchanged; a previously created checkpoint may remain as evidence.

V3 remains sticky through undo/redo, branching and reorder. Older v2 readers reject it as unsupported history. No silent downgrade, history stripping or migration. Retained old validator explicitly tested against legacy, v3 and undone v3.

## Canvas

Four native pointer resize handles for one selected layer; aspect lock defaults ON, Shift also locks. Opposite corner stays anchored; canvas bounds and positive dimensions enforced. Nearest integer pixel rounding can introduce subpixel ratio approximation. Grid snapping applies to resize deltas; Alt bypasses it. Width/Height provide keyboard precision resizing; with aspect lock, Width drives Height. Resizing text changes its layout box, not font size. Existing font/overflow/export qualification remains authoritative.

Group dragging uses union bounds, existing grid/edge/margin/centre/sibling snapping and one translated target list. Group alignment aligns each selected layer to the chosen canvas-margin edge/centre in one transaction, rather than moving the union as a rigid group. Precision Move X/Y by moves the complete selection atomically. Invalid/no-op requests do not partially apply. Single-layer ordinary dragging continues using existing move operations. Pending text blocks geometry until applied. Cancellation, capture loss, blur and stale gesture checks preserve source state. Live geometry gestures show staged outlines; the actual SVG refreshes after commit.

## Recovery

Explicit command from the workspace:

`python3 -B -m visual_poster_studio.checkpoint_restore --session '<absolute owned session>' --project '<project ID>' --checkpoint '<64 lowercase hex SHA-256>' --acknowledge-lost-subsequent-edits`

Requires canonical owned runtime source, exclusive writer lock, verified readonly single-link checkpoint, matching hash/project identity and valid manual document/history. Creates a NEW Visual-owned session and saves the restored document there with provenance. It never overwrites source primary, previous, checkpoint or exports. All edits after the checkpoint are excluded. Stop the running source service first. Restore accepts only the existing manual subset, not arbitrary asset-bearing projects. Physical power-loss durability remains unverified; unsupported synchronization retains existing blocked/degraded handling. No automatic checkpoint eviction or quota relaxation.

## Exact files

Modified (11):
- creative_core/operations.py
- creative_core/validation.py
- visual_poster_studio/service.py
- visual_poster_studio/app.js
- visual_poster_studio/index.html
- visual_poster_studio/styles.css
- visual_poster_studio/canvas.mjs
- visual_poster_studio/server.py
- tools/run_visual_resume_tests.py
- visual_poster_tests/test_canvas.mjs (group movement expectation)
- visual_poster_tests/test_compatibility.py (v3 now supported; unknown-version fixture v4)

Created (6):
- visual_poster_studio/geometry.mjs
- visual_poster_studio/checkpoint_restore.py
- visual_poster_tests/test_geometry.py
- visual_poster_tests/test_geometry.mjs
- visual_poster_tests/geometry_browser.mjs
- docs/VISUAL_GEOMETRY_HANDOFF.md

## Commands and results

All commands from AI Studio. No package manager or legacy full regression suite.

- `python3 -I -B tools/run_visual_resume_tests.py --track geometry --run-id visual-geometry-targeted-001`: exit 0, initial 10 tests.
- Same command with run ID visual-geometry-targeted-002: exit 0, final 13 geometry tests.
- `python3 -I -B tools/run_visual_resume_tests.py --track reorder --run-id visual-geometry-reorder-001`: exit 0, 17 tests.
- `python3 -I -B tools/run_visual_resume_tests.py --track canvas --run-id visual-geometry-canvas-001`: exit 0, 4 tests.
- `node visual_poster_tests/test_geometry.mjs`: exit 0, 11 checks.
- `node visual_poster_tests/test_canvas.mjs`: exit 0, 31 checks.
- `node --input-type=module --check < visual_poster_studio/app.js`: exit 0.
- `python3 -B -m visual_poster_studio --root '<workspace>/.runtime/studio-ui/visual-geometry-browser-01' --port 8774`: authorized loopback startup; stopped with SIGINT, exit 0.

Final targeted Python total: 34 passing, no failures/errors or rejected writes. All runners report no source drift, no R1 reads, no Gate A changes and no real-media execution. Session close/resume compares exact saved document and SVG; this batch does not repeat destructive/process fault experiments from prior milestones.

Browser route /#geometry-checks: nine passing workflow checks covering explicit acknowledgement, resize/undo, atomic group move/alignment/undo, reopen and two matching SVG/PNG exports. Existing PNG decoded-RGBA parity handshake remains required. SVG ec8bf950bcfa8669de9fc556876763bed4bd76ae774b2c5c91292f826564de8a; PNG cd8ff6dbf085a9b7315ba5084516e0f90d7d12be8267feaa4bc871cdb4a9e7d7. Native group drag: revision 8 to 9, primary (32,120) to (80,180). Native aspect resize: revision 9 to 10, 400x267 to 475x317; Undo revision 11 restores 400x267; Redo revision 12 restores 475x317. Native pointer checks are separate observations, not included in nine automated browser checks. Evidence: .runtime/studio-ui/visual-geometry-browser-01/browser-evidence-dd965984c86f396d.json, native-geometry-evidence.json and native-geometry-proof.png. Previously generated exports retained. Evidence session contains unsaved native edits after its last saved/exported revision; no claim those later edits were exported.

Before source bytes, before/after hashes and preservation report: .runtime/studio-ui/visual-geometry-baseline-01/. Baseline covers core, Visual and accepted manual UI, plus exact originals of modified tests/runner. No M4/production access; no R1 reads or changes; no dependencies installed. The previous canvas handoff is historical and remains unchanged; this batch resolves its geometry-operation blocker.

## Remaining work

No known blocking geometry failure. Full milestone acceptance, native Telugu IME/typography approval, comprehensive accessibility, distribution/offline rebuild closure and cross-browser/zoom/pointer-device coverage remain open. Multi-layer resizing, rotation handles, marquee selection and richer typography are not implemented. Next practical manual-editor batch: text-layout controls and keyboard/accessibility completion, followed by consolidated editor acceptance. Actual media analysis stays independently gated and OFF; R2–R6, M4 integration and production release are not authorized.
