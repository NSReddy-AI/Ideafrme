# Project Binding & Creative Brief implementation handoff

Implemented in isolated M5; not a production release or independently accepted milestone. No AI concept generation, media application, real-media processing, R2–R6 or M4 integration.

## Contract and workflow

See PROJECT_BINDING_CONTRACT.md for exact binding, paired publication, rights and render identity contracts. Optional new-project brand/brief selection is explicit. Empty legacy Create remains unchanged. Approved brand metadata is pinned by hash; brief fields preserve Unicode. Context revisions require impact preview, acknowledgement, current document revision, binding hash and HEAD. Current approvals clear; historical snapshots remain unchanged. Context revisions are separate from creative Undo. Existing unbound projects are never silently adopted.

## Persistence and compatibility

Immutable paired generations publish creative document and binding through one HEAD replacement. Exclusive writes, readback, file/directory synchronization and the existing OS writer lock are reused. Candidate generations, geometry checkpoints and journal storage share the 128 MiB recovery budget. Failed publication retains prior complete generation; an uncertain post-publication result blocks further work until restart/recovery validation. Invalid bound projects are blocked independently of legacy projects. No physical power-loss durability claim.

Older Studio versions cannot list/open bound projects: there is intentionally no legacy primary mirror that would discard context. creative@1/history v3 themselves are unchanged. Rollback can continue opening legacy projects; bound projects require this implementation or explicit paired recovery, never silent downgrade. Future backup tools must retain the whole bound-project namespace, not just a creative.json file.

Explicit recovery command: python3 -B -m visual_poster_studio.binding_recover --help. Select one validated complete pair into a fresh session; source is never repaired in place. Recovery clears current approvals, advances document revision and records new binding identity/origin. Immediate source ancestry is retained verbatim under origin-history. Raw legacy checkpoint recovery refuses bound IDs.

## Eligibility and exports

Pinned library record and pinned rights are rechecked for brand-dependent use. Every registered asset requires current preview/metadata and commercial/poster scope. Revoked/expired or insufficient rights block affected use; saves remain allowed to prevent data loss. Later adverse mandatory-rule declarations block old pins; benign preference changes do not migrate them. Plain-text rules require human review: this is draft/manual use, not automated compliance approval. No asset bytes are applied.

Bound SVG metadata and export manifests include binding, brief, brand and workflow identities; the core creative fingerprint retains its original meaning. Begin/finish recheck eligibility and stale context. Prior exports are retained. Browser restart reproduced the exact SVG and PNG hashes while preserving earlier export files.

## Verification

Commands (all exit 0):
- python3 -I -B tools/run_binding_tests.py --run-id visual-binding-targeted-004 — 24/24.
- python3 -I -B tools/run_home_tests.py --run-id visual-binding-home-001 — 12/12.
- python3 -I -B tools/run_visual_resume_tests.py --track reorder --run-id visual-binding-reorder-001 — 17/17.
- node --input-type=module --check < visual_poster_studio/app.js — syntax passed.
- Final binding rerun: visual-binding-targeted-final (results.json records final source hashes).

Earlier bounded binding runs -001/-002/-003 are retained; counts are not added together. Fault evidence uses injected ENOSPC and publication interruption, not actual disk exhaustion or OS/power failure. Checks cover CAS, corruption, approval preservation, v3 checkpoint/undo compatibility, recovery-copy ancestry, quotas, revocation, scope checks and export identity tampering.

Browser evidence: .runtime/studio-ui/visual-binding-browser-01/restart-verification.json and browser-brief.png. Tested explicit pin selection, Telugu/decomposed combining-mark brief, confirmed version switch, service stop/restart, reopening revision1/bindingr2 and SVG+PNG export. Synthetic metadata brands contained no media assets. Test server stopped. Existing exports were not overwritten.

SVG after switch/restart: 9f0c0f9aa88a2a38d9025b9a8c94f6ae76d0151ec471d5138a728efabbed09f1
PNG before/after metadata switch/restart: f87ad806e6382be6486e19c6c59d1fb3a4adc6d3ed2f365edb139e5e45617c3f

## Dependencies and limitations

Reused Python standard library and existing SQLite brand store/helpers. Official os.replace documentation informed same-filesystem publication; no third-party code, packages or models acquired. No new mandatory cloud/paid dependency. Existing full offline distribution/licensing closure remains open. Native IME/accessibility acceptance is not newly claimed. Final small layout class reuse was syntax/source checked; the saved browser screenshot precedes that layout-only adjustment.

Poster format only. No automatic asset/font application, automated brand-rule compliance or concept generation. Human review remains required. A next separately authorized batch can design the local AI Creative Director: qualify retained model/runtime licences and offline artifacts, then produce three distinct editable concepts from the pinned brand and brief with explicit review. This handoff does not authorize it.

## Files

Modified:
- visual_poster_studio/service.py
- visual_poster_studio/recovery.py
- visual_poster_studio/exports.py
- visual_poster_studio/server.py
- visual_poster_studio/index.html
- visual_poster_studio/app.js
- visual_poster_studio/home.py
- visual_poster_studio/checkpoint_restore.py
- tools/studio_local.py

Created:
- visual_poster_studio/project_bindings.py
- visual_poster_studio/binding_workflow.py
- visual_poster_studio/binding_recover.py
- visual_poster_tests/test_project_bindings.py
- tools/run_binding_tests.py
- docs/PROJECT_BINDING_CONTRACT.md
- docs/PROJECT_BINDING_HANDOFF.md

Protected baseline: all captured files outside the nine changes matched their original hashes. R1, M4 and production were not accessed or modified; no broader external-filesystem no-write audit is claimed. See completion.json for exact before/after hashes. STOP after this implementation batch.
