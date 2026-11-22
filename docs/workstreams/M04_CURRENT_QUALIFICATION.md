# Current integrated M4 release qualification

Prepared 2026-11-22. Status: NOT QUALIFIED. Gate D has not started.
Source under review: develop `cf65a74f7a442b244d185482d155a80e258e9ddc`,
plus planner fixture fix `cf52324` and continuation documentation `a2583d4`.
Historical Gate C is evidence of the 11 Nov build, not a pass for this source.

## Historical evidence inspected read-only

Directory: `Reel Studio_dev/tests/acceptance/M4_gateC/20261111_143119`.
The report records PASS, 31/31 app checks, narration 98/98, three-platform QA,
Telugu CER 16.7%, and 83% of words within 0.4 seconds. These are historical results.
File hashes below identify inspected inputs; they do not attest that the full evidence manifest was verified in this review.

| File | SHA-256 |
|---|---|
| GATE_C_REPORT.md | 24f35a512d4dd0aa758b583ff9dc6a5a5dfb6cff2af02cfae61a319078a3f315 |
| gatec_app.py | ba3c924e71085c64bc86d43ef8eda3547dabd5fc1295ddfcafa281cd734ef712 |
| GATE_C_EVIDENCE.sha256 | c87d8da925574b6de40bd9a0bf12bc66314dc04d7001ae1dddd23f32570ff9c4 |

## Coverage and execution readiness

The commands below are candidate entry points, not instructions to execute unchecked.
Except for the completed planner safety regression, dependency and transitive write review remains required.

| Area | Candidate entry point / evidence | Writes and prerequisites | Current verdict |
|---|---|---|---|
| Planner safety | `~/.venvs/reelstudio/bin/python -B tests/test_plan_checks.py` | Tracked transcript, provider config, brand references; read-only inputs | PASS, exit 0 on fixture fix |
| Engine settings, title and frame | `tests/test_milestone2.py` | Creates and deletes projects; invokes title/frame scripts; inspect callees before isolated run | NOT RUN |
| Narration contracts, approvals, memory stop, disclosure | `tests/test_narration.py --out <new-evidence-dir>` | Temporary projects and private heavy lock; ffmpeg, numpy, legacy `.preB1` files; fake worker is not model-quality proof | NOT RUN; inspect legacy input availability |
| Telugu and English STT | `tests/test_transcribe.py` | Writes tests/out, extracts audio; inspect reference source paths and workers; cached models required | NOT RUN |
| Local planner and approval integration | `tests/test_planner.py --models qwen3:14b --provider local` | Writes/deletes fixed zz_plan_te, tests/out, uses reel_002 project.json and words.json; local Ollama calls; render gate path | NOT READY: missing project inputs; isolate and adapt |
| Baseline and three-platform export | Historical `checkpoint.sh`, current isolated render-job API | Legacy script targets protected reel_002, writes exports/history and fixed /tmp file; shell output does not reliably propagate every failure | DO NOT RUN legacy script; design isolated parity harness |
| App approvals, captions, narration, export | Historical gatec_app.py (31 checks) | Hard-coded port 8765, historical demo inputs, project POST/PUT/PATCH, fixed-directory deletion, model and render jobs | DO NOT RUN unchanged; adapt server root, port, fixtures and cleanup |
| Production and evidence preservation | Before/after read-only SHA-256 manifests | Protected roots must never be output destinations; allow for concurrent user activity when interpreting differences | PENDING scoped manifest design |
| Runtime dependencies and model identities | Existing locks, asr.json, model manifests, environment inventory | Read-only inventory first; never install into shared environments | PENDING current-to-record comparison |
| Licensing and packaged runtime | docs/SBOM.json, DEPENDENCY_INVENTORY.md, LICENSE_COMPLIANCE.md, THIRD_PARTY_NOTICES.md | Compare actual candidate contents and versions; historical review is insufficient | PENDING |
| Offline runtime and recovery | tools/m6_offline_check.py; tools/m6_offline.sb; historical restore records | Checker resolves vendor relative to checkout parent; inspect subprocess/imports; static availability does not prove no external connections or successful restore | PENDING isolated runtime proof |
| Current frontend/M6/M7 compatibility | Existing web and integration suites | Earlier conversation reports passes; bind results to exact source, commands and retained logs before accepting release evidence | PENDING source-bound evidence |

## Safe execution order

1. Inventory tracked fixture, legacy backup, font, media and model prerequisites read-only.
   Record absent inputs explicitly; never copy historical projects wholesale into this branch.
2. Review test callees and absolute paths. Build a disposable execution root containing
   only required files, with output directories and a private heavy-model lock.
   Any API harness must address a server proven to use that root and an unused private port.
3. Run small deterministic checks first; retain command, source SHA, environment identity,
   exit status, full stdout/stderr and per-check results in a new evidence location.
4. Adapt necessary integration harnesses before a single consolidated model/render acceptance run.
   Never run heavy work alongside production; do not download models or change shared environments.
5. For each acceptance area record PASS, FAIL, BLOCKED or NOT RUN with evidence.
   Missing media or models is a qualification blocker, not automatically a product defect.
6. Produce the current candidate report. Production release and merging to main remain
   separate decisions requiring explicit owner approval.

No historical evidence was changed and no legacy gate, production render, or model job
was executed while preparing this checklist. M5 remains IN_PROGRESS.
