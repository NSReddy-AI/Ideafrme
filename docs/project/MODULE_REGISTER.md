# Seven-module register

The word “module” refers to a product milestone and responsibility area. The modules build on one another; they are not seven independent copies of the application.

| Module | Responsibility | Latest active source | Status | Provenance |
|---|---|---|---|---|
| M1 | Reel-engine foundation: project layout, rendering primitives, brands, platforms and styles | Superseded by the current `engine/`, `brands/`, `platforms/` and `styles/` | Historical boundary inferred; no independently named M1 checkpoint found | Earliest surviving Reel Studio folder and later milestone documentation |
| M2 | Structured Brand × Platform × Style reel pipeline, project records, packaging and baseline regression | Current reel engine and `tests/test_milestone2.py` | Implemented and carried forward | `Reel Studio_old_M2_2026-11-10`, then M3/M4/M6 successors |
| M3 | Telugu/English transcription, face tracking, motion, scene processing, audio checks and dependency records | Current `engine/` and relevant tests | Implemented and carried forward; individual models remain external | `Reel Studio_old_M3_2026-11-11` plus its full manifest |
| M4 | Local web application, planning, narration, approval gates, builds, multi-platform rendering and QA | Current `app/`, `engine/` and M4 documents/tests inside this repository | Development-complete scope; Gate C/D and production release were not completed | Production `Reel Studio`, `Reel Studio_dev`, and M6 seed commit `7f2e597` |
| M5 | Creative documents, poster studio, brand library, concepts, editing, local-AI experiments and poster export | Latest reviewed `Codex/AI Studio` source integrated under `m5/` | Overall `IN_PROGRESS`; 30 compatibility tests and 11 M5 sprint checks pass | Frozen checkpoint, integrated checksum baseline and newer live M5 status manifest |
| M6 | IDEAFRAME shell and integration of M4 reel workflows with M5 poster workflows | Commits `7f2e597` through `b480103` | Implemented development integration | `M6_WORKSPACE.md`, checksum baseline and Git history |
| M7 | Professional UX, brand rights, accessibility, task orchestration, capabilities, combined poster-to-reel flow and reliability fixes | Commits `edd1245` through `e6a592c`, plus preserved current working changes | Latest development implementation; production approval remains open | `docs/M7_HANDOFF.md`, acceptance evidence and current working snapshot |

## Selection rules

1. The current M7 integration is the base because it contains the latest carried-forward M1–M4 engine and the M6 integration work.
2. Older milestone folders are evidence and recovery sources, not candidates for copying wholesale into the active tree.
3. A newer file is selected only when its contract, dependencies and tests are compatible with the active application.
4. The live M5 source was integrated only after testing it behind the existing M6 boundary in a disposable trial checkout.
5. Missing, blocked or unverified functionality remains clearly labelled rather than being represented as production-ready.
