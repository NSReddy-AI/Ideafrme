# Visual canvas batch — partial delivery, protected contract boundary

Implemented single-layer native pointer drag using existing move transactions; staged outline only during movement, one revision on release, no source edits on cancellation, stale-project/revision refusal, and pending-text protection. Browser default image dragging is disabled. Shift constrains axes; Alt bypasses snapping. Optional 1–100px grid, edge/margin/centre/sibling snapping, canvas clamping and existing numeric position/nudge controls operate in source pixels. Multi-selection supports modifier-click, Select all, Keep primary and union bounds; unsupported group edits are disabled.

## Genuine remaining blocker

Resize handles, aspect-protected resizing, atomic multi-layer movement and alignment are NOT implemented. The protected dispatcher provides single-element move and restyle, but no width/height mutation or atomic batch geometry operation. History validation enumerates supported operations. Repeated independent moves or remove/recreate would violate atomic undo or identity guarantees. No core/schema/history version changes were made. The next batch needs an explicitly authorized versioned geometry transaction covering expected revision, same-view unique IDs, complete before/after snapshots, width/height bounds, aspect policy, atomic group transforms, approval invalidation, redo truncation and older-reader refusal. Historical exports must remain immutable. This requested batch is therefore incomplete at that boundary.

## Files

Modified: visual_poster_studio/app.js, index.html, styles.css, server.py; tools/run_visual_resume_tests.py.
Created: visual_poster_studio/canvas.mjs; visual_poster_tests/test_canvas.mjs, test_canvas_transactions.py, canvas_browser.mjs; this handoff.
No new dependency. Uses native Pointer Events (https://www.w3.org/TR/pointerevents3/). The scene mapper, export implementation, font assets, creative_core and accepted manual UI are unchanged.

## Verification and reproducibility

Commands from the workspace root:
- env -u NODE_COMPILE_CACHE node visual_poster_tests/test_canvas.mjs — 31 checks passed, exit 0.
- python3 -I -B tools/run_visual_resume_tests.py --track canvas --run-id visual-canvas-targeted-001 — 4 tests passed, exit 0. Final-source run: visual-canvas-targeted-002.
- python3 -B -m visual_poster_studio --root <absolute fresh .runtime/studio-ui session> --port 8773 — loopback startup succeeded with permission; stopped after verification. Initial sandboxed launch returned 2 and its partial session was retained unchanged.
- Browser test route /#canvas-checks: final nine checks passed. Initial two runs stopped on a harness-only layer lookup; both failed evidence records are retained. A native pointer trial initially cancelled due to default image drag; fixed via draggable=false and dragstart prevention. Native retry moved (110,140) to (194,244), revision 4 to 5, with source move notice. Synthetic evidence truthfully labels its own pointer checks synthetic; native proof is separately recorded.

Evidence: .runtime/studio-ui/visual-canvas-browser-20261111-02/browser-evidence-26e7736d09f49b5b.json and native-drag-proof.png. The saved scene exported twice with identical SVG 3579113c189a978ddc23b544949892377d2aa7c6c7dc006f182893469ffe3295 and PNG 2800be8835ca3d2f9857cbd5d294e48578bdabe50a3311d72a6059ff074f7dff. This establishes repeatability for that fixture, not broad cross-browser pixel qualification. Existing preview/export parity mechanisms were preserved.

Baseline evidence: .runtime/studio-ui/visual-canvas-batch-20261111-01/baseline.json and completion.json. No R1 reads; M4/production not accessed. Media Analysis remains OFF; Gate A unchanged. No installs or real-media execution. Native Telugu IME, full accessibility and offline distribution closure remain previously open. Multi-touch, every browser/zoom combination and pointer capture loss on all OSes remain consolidated acceptance work. Full milestone acceptance is not claimed.
