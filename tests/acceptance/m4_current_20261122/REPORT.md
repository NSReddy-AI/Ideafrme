# M4 current qualification report — 22 Nov 2026

**Verdict: BLOCKED for full qualification; no production release approval.**
Development implementation is present. This pass repaired test portability, ran available checks,
and retained current evidence. It does not declare M4 released or Gate C re-passed.

## Source and isolation

Branch: feature/module-04-release-gates, isolated checkout under projects/agents.
Execution base: 83b2a90; ASR harness repair: 4bcdd82. See source_identity.json for full identities
and engine hashes. The current engine matches the execution root byte for byte.
All test outputs went to disposable roots or this new evidence directory. Historical engine
comparison files were selectively copied read-only; execution.json records their SHA-256 values.
Only four historical baseline render inputs were copied to the disposable root; their hashes
are in render_input_sha256.json. No historical project was copied into the source branch.
The original repository, production, main and historical evidence were not written by these checks.

## Results

| Check | Result | Evidence |
|---|---|---|
| Title/frame for all three brands | PASS, exit 0 | milestone2.log |
| Planner safety | PASS, exit 0 | planner_safety.log |
| Narration contracts and legacy parity | 96/98, exit 1; NOT PASS | narration.log; narration/test_narration.json |
| Frontend logic | 8 test files pass | web_tests.log |
| Frontend production build | PASS | web_build.log |
| Isolated engine-job contracts | 2/2 PASS | engine_jobs.log |
| Approved content gates | 6/6 PASS | approved_content.log |
| Brand bridge | 3/3 PASS | brand_bridge.log |
| App HTTP integration | BLOCKED: localhost bind denied | creative_routes.log |
| ASR harness controlled verdicts | 3/3 PASS; not model accuracy evidence | transcribe_harness.log |
| Three-platform baseline render | PASS; unchanged engine; all QA checks pass | render_job_manifest.json; render.log |
| Environment compatibility | Three pip freezes unchanged; all pip checks pass | environment_comparison.json |
| Licence metadata inventory | Collected; metadata gaps match existing recorded package/version entries | deps_m4.json; licence_metadata_reconciliation.json |
| Offline enforcement and model memory monitor | BLOCKED by session permissions | host_constraints.json |

Each of the Instagram, YouTube and Facebook renders has 1849 frames, -14.1 LUFS and -1.4 dB
true peak. QA includes baseline frame count and file-size bounds, not bit-identical encoded video.
This rendered the preserved edit with the current engine; it does not prove current ASR,
planner, or fresh AI-narrated end-to-end generation.

## Fixes completed

- The planner safety test now uses an exact tracked historical transcript fixture.
- Historical Gate C and current release qualification are distinguished in release documents.
- ASR acceptance now returns exit 1 for threshold/English failures, supports an explicit
  read-only --source, and supports a fresh --out directory. Controlled matching transcript,
  bad Telugu and failed English cases confirm the process verdict. No accuracy limits were relaxed.

## Remaining qualification blockers

1. Narration memory-limit and warning checks fail in this session. macOS top is denied;
   the fake worker reports TTS_FAILED instead of TTS_MEMORY_LIMIT. Preserve these failures.
   Rerun on the supported unrestricted Mac host, with working memory monitoring. If either
   still fails there, investigate the watchdog as a product defect before real TTS acceptance.
2. Localhost bind is denied, so the existing app route suite cannot start its isolated server.
   The historical 31-check M4 app harness also needs explicit isolated-root/port/fixture adaptation;
   it was not run unchanged against port 8765.
3. sandbox-exec sandbox_apply is denied (exit 71). Current runtime no-network proof is pending.
   Cache presence and worker offline settings do not replace that proof.
4. Real Telugu/English ASR, Qwen3 planning and fresh AI narration remain NOT RUN in this pass.
   Do not load real heavy models without working memory monitoring and concurrency controls.
5. Packaged runtime closure, the three absent optional vision-model files, notice completeness,
   and an isolated restore rehearsal remain pending for a concrete current release candidate.
   The licence scanner's missing metadata alone is not proof of absent licence: recorded rows
   exist for the same versions. This is not a new distribution/legal approval.

## Host continuation

Use a disposable execution root and a new evidence directory, never production or protected
reel_002. Reuse only verified legacy comparison files. Required next commands include the
narration suite, isolated app route suite, and the repaired ASR test with explicit source/output.
Adapt the historical app acceptance harness before executing it; no automatic Gate D script
is authorised. After all host checks pass, prepare a current release candidate, evaluate its
licences and recovery procedure, and request explicit production release approval.

Full M4 completion cannot be certified from this restricted session. Historical Gate C stays
PASS for its own build. Gate D stays NOT STARTED. M5 stays IN_PROGRESS.
