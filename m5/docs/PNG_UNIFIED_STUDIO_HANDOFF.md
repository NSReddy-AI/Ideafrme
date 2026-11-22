# Unified M5 PNG Studio — implementation handoff

2026-11-12. **GO for the isolated unified manual/PNG editor pilot.** No production release or next gated feature started. PNG profile limits, native-runtime trust assumptions and the absence of a kernel-enforced total-host-memory quota remain as recorded in PNG_SANDBOX_HANDOFF.md. No new dependencies, downloads, model execution or decoder changes.

## Working user workflow

Start/restart the existing main Visual Poster Studio from this project directory using the unchanged launcher or `python3 -B -m visual_poster_studio --port 0`. Use Home/Projects to open an existing creative-brief/approved-brand-bound poster (including an already selected Creative Director concept). In Editor, the new **PNG brand assets · Unified workspace** section requires explicit acknowledgement before **Create unified PNG workspace**. Pending text/brand/brief fields must be applied/saved or discarded first.

This creates a separate media v3 copy with a verified immutable source checkpoint. Original projects and accepted version-2 standalone workspaces are not migrated or rewritten. Main text, font-size, geometry, positioning, brand palette, layer operations and existing keyboard controls edit the versioned media copy. PNG selection/placement, aspect-ratio resizing/movement and removal use its PNG panel beside the same poster preview. Main Undo/Redo traverses one combined text/geometry/PNG timeline. Every action is autosaved atomically; main Save and Reopen controls work against the media project. Draft SVG/PNG export uses the existing embedded-font, missing-glyph, measured-overflow and pixel-parity checks, then the qualified PNG decoder and current rights validation.

Projects now has a distinct **Unified PNG projects · v3** catalogue with IDs, allowing explicit reopening after main-service restart. PNG panel includes retained export links and explicit recovery candidate/copy controls. Source projects remain separately selectable through normal project navigation. Restart with the existing `--resume --root '/ABSOLUTE/OWNED/VISUAL-SESSION'` startup options; do not use acceptance-evidence folders for ordinary work.

## Compatibility and history

New authoritative envelope **studio-media-workflow@3**, owner **studio-png-session@2**, in owned `png-unified-<32-hex-id>` roots within a main Studio session. Older manual/v2 readers refuse it. A separate source checkpoint contains the original document and unchanged pinned source-binding snapshot. This is a fork, not an in-place upgrade. Existing v2 frozen-base workspaces continue using their unchanged standalone workflow; bulk import/adoption of those existing workspaces is not implemented.

`creative@1`/schema1, core history versions1–3, project-binding@1, Brand Library and approval semantics are unchanged. Core documents still contain no media assets; qualified overlays live explicitly in the new media envelope. Core operations and schema validation are reused unchanged. An in-memory facade reuses accepted manual action handling and Brand Application A; it never calls legacy persistence for media edits.

A separate combined timeline records complete before/after document plus PNG-placement/history states. PNG edits retain the base and append their existing media transaction. Base edits use one validated accepted core transaction and preserve overlay state. Expected-head plus generation checks refuse stale tabs. Core history upgrades retain the existing acknowledgement and canonical-newline immutable-checkpoint contract. History compatibility floor remains sticky through combined Undo/Redo, including after branching; PNG actions cannot forge an upgrade. Current approvals stay empty; original/historical approved snapshots and previous exports are not rewritten. Every committed state and its ancestry are revalidated on reopening. Geometry changes still use history v3 rather than introducing another core-history version.

## Security, rights and persistence

The qualified Wasmtime/LodePNG module, controller, resource limits, global single-job lock and normalized-pixel receipts are reused byte-for-byte. Only the previously qualified static noninterlaced RGB8/RGBA8 PNG subset is available. SVG inputs, uploaded fonts and other formats remain refused. No raw/unqualified media enters ordinary rendering. Main HTTP Host/Origin/CSRF/encoding/path guards remain active; new routes use fixed IDs, explicit media context and bounded request bodies. Media POST operations have a60-second complete-operation alarm; the decoder retains its15-second worker limits and confirmed termination/fault behavior. No automatic retry/restart.

Brand pins/expiry/revocation/hash checks remain active before decoding and publication, with the Brand Library transaction held across final eligibility validation and atomic metadata/export publication. Brand source context is read-only in a media workspace; to change a pin/brief, use the source workflow and make an explicit new copy. Palette application works in the unified editor. Invalid colors/geometry, asset/text overlap, aspect changes, revoked rights and unsupported hard rules refuse without a partial state change. SVG embedding additionally requires redistribution clearance. All exports remain unapproved drafts; browser QA remains browser-reported, not independently rerendered on the server.

Existing immutable generation/HEAD publication, receipt verification,128 MiB retained-session budget,20 retained export sets,8 MiB PNG/4 MiB SVG bounds and other inherited caps remain in place. Incomplete artifacts count toward usage and are never automatically deleted. Main service closure/session switching releases media writers and cancels pending handshakes. Recovery copies the selected complete source/document/PNG/combined-history/checkpoint ancestry into a fresh owned workspace; it excludes later edits and old exports and records provenance. Original records are preserved. Invalid ownership/corrupt primary state fails closed; no automatic repair, physical power-loss guarantee or generalized offline recovery tooling is claimed.

Reference analysis stays OFF. Local AI concept generation remains in the original manual Create flow; direct AI/brief mutation routes are rejected while a media workspace is active. No R2–R6, Reference Style Studio, cinematic reels or cross-milestone integration added.

## Exact changes

Modified existing files:
- visual_poster_studio/app.js — explicit media routing/context invalidation, shared controls and read-only source context.
- visual_poster_studio/index.html — media project catalogue and capability wording.
- visual_poster_studio/server.py — fixed media routes, bounded bodies, writer lifecycle and deadline handling.

Created:
- studio_png_sandbox/unified.py — version3 envelope, combined timeline, core-operation reuse, validation and recovery.
- visual_poster_studio/media_bridge.py — fixed-ID service adapter, pin/rights checks, scene/export/navigation.
- visual_poster_studio/media.mjs — main-editor PNG controls and explicit fork/open/recovery UI.
- png_sandbox_tests/test_unified.py — focused integrity and mixed-edit regressions.
- tools/run_png_unified_tests.py — fresh bounded test runner.
- docs/PNG_UNIFIED_STUDIO_HANDOFF.md — this handoff.

Before/after hashes are in `.runtime/png-unified-001/completion.json`. All other scoped baseline files—including qualified PNG decoder sources, legacy v2 workflow, manual service, creative core, brand/binding formats and Phase2F/2G components—are unchanged. Hash helper excludes R1 contents/runtime/dependencies; no exhaustive external-workspace hash claim is made. R1 contents, frozen checkpoint, M4, M6 and production were not read or modified. No Git/configuration/install actions.

## Evidence

Final command, exit0:
```
python3 -I -B tools/run_png_unified_tests.py --evidence '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/studio-ui/visual-unified-tests-final-02'
```
**12/12 targeted Python tests passed**, including exact original preservation, older-reader rejection, English/Telugu/combining text, mixed PNG/text Undo/Redo, branch truncation, approved palette/default geometry, sticky geometry upgrade/checkpoint, stale/invalid/overlap refusal, save/reopen/SVG identity, atomic interrupted save, rights revocation, explicit recovery and forged-upgrade rejection. No broad legacy suite run. Node syntax checks for app.js and media.mjs passed. No decoder/source/dependency requalification rerun because those components were unchanged.

Earlier fresh attempts are retained, not overwritten: initial adapter checkpoint lacked the newline required by the existing core contract; fixed only in the adapter. A stricter final ancestry check initially classified final Redo as both travel and edit; corrected by prioritizing unchanged-history travel, with explicit new-edit/floor validation and a forged-upgrade regression. Failed results remain in visual-unified-tests-01 and visual-unified-tests-final; successful final-02 evidence is authoritative.

Browser/HTTP evidence: `.runtime/studio-ui/visual-unified-browser-01/`.
- Main Home/Projects → approved source → acknowledged media copy → PNG placement → English/Telugu text editing → PNG movement/aspect resize → shared Undo/Redo → main Save/Reopen → SVG/PNG export passed.
- Both exports passed the existing browser font/overflow and exact decoded-RGBA parity path. A separate qualified-decoder check of actual exported pixels confirms both posters contain the expected opaque-red PNG overlay, not merely two matching empty renders (`overlay-pixel-proof.json`).
- Full process stop/restart, catalogue discovery and explicit media reopening passed. Telugu text, PNG coordinates and retained downloads survived; resumed SVG prefix c1b11f489cd5 matched before subsequent explicit color/Undo/remove/Undo browser edits.16 original source files remained byte-identical. All retained pre-restart immutable files stayed unchanged; the subsequent explicit edits changed only the appropriate media HEAD and added generations.
-9 HTTP checks passed: Host, Origin, missing CSRF, traversal ID, stale media head, unacknowledged fork, unsupported route, and unchanged original English/Telugu legacy views.
- Final validator separately reopened both browser-created projects and verified all retained SVG/PNG hashes (`final-reopen-proof.json`). Main test server stopped; no user service was stopped.
- Browser screenshots and AX records: english-main.jpg/.txt, telugu-main.jpg/.txt, resumed-telugu.jpg/.txt. Fixtures use generated first-party red pixels only; no real customer assets were decoded.

## Remaining limits and stop

PNG overlays retain their existing top-of-base paint order and numeric placement controls; they are not interleaved into the legacy layer array or its drag handles. Existing v2 projects stay standalone. Media v3 brand/brief switching and in-workspace AI generation are intentionally unavailable. Native Telugu human/IME review, full accessibility, broader creative-quality testing, complete offline source rebuild/licensing-distribution closure and physical power-loss durability remain open. The approved memory target is not a kernel-enforced total-host-memory quota; no stronger sandbox claim is made. No production readiness or full M5 completion claim.

**STOP: unified manual/PNG integration delivered in isolated M5; no release or next gated module started.**
