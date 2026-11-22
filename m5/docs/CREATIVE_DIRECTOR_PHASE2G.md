# Phase 2G — Hybrid Creative Director UI pilot

Decision: GO for the bounded implemented/tested local UI pilot; human acceptance and production readiness are NOT claimed. No real-media, offline distribution, M6 integration or release authorization is implied.

## Implemented workflow

Create a new project through Home/Create, enter exact initial text and an explicitly acknowledged creative brief, optionally select an immutable eligible approved brand version, then acknowledge the saved brief in Creative Director. Choose Generate with local AI. Browser measures exact topic/purpose at sizes16..80 with pinned fontRuns/fitTextBox/SVG ink metrics; no approximate font fallback. One background job verifies pinned runtime/model artifacts, executes the existing Qwen3-14B/llama.cpp text-only task, then compiles through unchanged Phase2F. UI shows explicit availability, queued/artifact verification/inferencing/compiling/ready/cancelling/failure states, elapsed time and an indeterminate progress indicator. Tested slow mode expectation94–128s remains labelled historical; pilot observed81.2/133.0s, maximum240s. No fabricated percentage or automatic generation retry.

Three SVG thumbnails, AI interpretation, application-authored factual rationales, exact brief, pinned metadata, rules and provenance are available for comparison. Browser ink overflow blocks selection. Review acknowledgement required. Selection uses server-held request/raw output/measurements and revalidates source revision, binding, HEAD, current rights/capabilities and exact compilation. A new unapproved editable project is published through existing Pairs commit; the source remains unchanged. Duplicate selection refuses, never overwrites. Selected drafts use existing editing/Undo/Redo/save/reopen, bound SVG/PNG identity and export handling. Human-entered brief text is never silently normalized/truncated or replaced by AI copy. Model interpretation remains untrusted; it cannot grant rights or alter poster text/fonts/palette/geometry directly.

Cancellation requests verified termination rather than assuming a UI abort stopped work. Runtime subprocess gets a private process group, TERM then KILL if needed, bounded waits and a group-absence check. Unconfirmed termination faults the planner and blocks new jobs. Timeout stops the process and provides explicit fallback/error guidance. Real native cancellation during inference was exercised, not merely a cancelled fetch. Failed/cancelled jobs never publish a project. Existing deterministic planning remains an explicit separately labelled button; it was invoked through the UI with no extra model job. It does not silently replace failed AI output. Session switching refuses while generation is active; closing the service cancels/joins the worker. Restart does not automatically resume/retry inference. Completed proposal comparison is process-local; on restart use saved projects, or explicitly generate a new comparison. This limitation does not prevent reopening selected drafts.

## Architecture and bounded storage

New hybrid_jobs.Jobs is one controller per HTTP service/current VisualStudio, with one active planning job. Inference runs in one worker thread; the existing sequential loopback HTTP server remains responsive to status/cancel/edit requests. The model uses one CPU compute/batch thread; no Metal change or new daemon/service. No machine-wide concurrency quota is claimed: separate manually launched Studio processes could each request a job. Heavy local memory use from Phase2F remains a limitation; no new peak-RSS measurement is claimed here.

Native identity: llama-completion0.9.0 commit cd959bae99ff4bed22bef2604f45241c09bbb8c8, executable SHA256 74cf11468e49effb467313dad495e299423950d5b0c11abf83363efb60ffb850, Qwen3-14B Q4_K_M SHA256 a8cc1361f3145dc01f6d77c6c82c9116b9ffe3c97b34716fe20418455876c40e. Existing absolute artifact paths are explicit prototype dependencies, not self-contained provisioning. Full hashes verified before each execution. No acquisition, package manager, downloads, alternative model or backend substitution.

Final launch path uses the current Python interpreter with isolated/-B flags and a constant single-thread helper that sets RLIMIT_FSIZE1MiB and RLIMIT_CORE0, then execs the exact verified llama command in the same PID. No Python preexec_fn executes after forking from the multithreaded host. Helper code is constant application source; user data enters separate argv/files, never shell/evaluated code. start_new_session preserves a private process group. Resource probe verified both hard/soft limits and private group. Final real English launch regression produced identical intent/documents/SVG and confirmed group absence. The original three UI launch attempts preceded this safety correction; unchanged UI/compile paths plus the final15 controller tests and real launch regression verify the correction without repeating both browser workflows.

Context2048,output384,temperature0,seed19,CPU only,offline flag; total artifact/inference diagnostic deadline240s. stdout/stderr bounded by per-file process limit; request/measurement limits32KiB, compilation16MiB. Evidence under session/hybrid-jobs/<random-id>, up to10 job directories/1024 entries and a64MiB application budget with20MiB reservation per new job. No automatic deletion; quota exhaustion requests a new session. Request, measurements, command/launch, prompt/schema, stdout/stderr, immutable compilation/status and termination records retained. These are application bounds for trusted-text planning, NOT a hard aggregate security boundary for untrusted media or a relaxation/qualification of Gate A. Additional native cache/filesystem overhead is not kernel-budget proven. Existing session recovery128MiB and export20sets/256MiB bounds remain unchanged; planning evidence is separate. Retain the whole owned session, including hybrid-jobs, for provenance. Selected project UUIDs in immutable compilation link to the existing paired projects without adding protected contract fields.

HTTP routes: GET /api/hybrid/status; POST /api/hybrid/start {source,measurements}, /cancel {job_id}, /select {job_id,concept_id,acknowledge_rules}. They inherit loopback binding, strict fixed paths, bounded JSON body, Host/Origin/CSRF and CSP. Model/filesystem paths cannot be supplied by HTTP. Diagnostics are local trusted-actor data, not authenticated clearance or a hostile-decoder sandbox. Missing/changed model/runtime refuses AI only; original deterministic/manual workflow remains independent. Model status checks do not launch inference. No image/video/audio import, OCR or Media Analysis activation.

## Exact files

Created seven:
- visual_poster_studio/hybrid_jobs.py
- visual_poster_studio/hybrid.mjs
- visual_poster_tests/test_hybrid_jobs.py
- visual_poster_tests/hybrid_browser.mjs
- visual_poster_tests/hybrid_browser.html
- tools/run_hybrid_ui_tests.py
- docs/CREATIVE_DIRECTOR_PHASE2G.md

Modified six:
- visual_poster_studio/server.py — fixed hybrid routes, lazy controller, shutdown and switch guard, fixed test/static routes.
- visual_poster_studio/director.mjs — reuse existing editor adapter and review acknowledgement for hybrid/deterministic paths.
- visual_poster_studio/index.html — explicit slow-mode controls/status/comparison section.
- tools/studio_local.py — report implemented pilot/human-acceptance-pending instead of stale AI integration NO-GO.
- studio_ui_tests/test_local_tools.py — verify that truthful readiness label.
- docs/LOCAL_STUDIO_START.md — update the same current status; no runtime acquisition or startup redesign.

No accepted manual UI, core/history, R1, binding/brand persistence, Phase2F semantic/compiler, renderer/font files or protected workspaces changed. No architecture rewrite, migrations, production deployment or M6 access. Frozen checkpoint remains byte-identical/read-only. Exact before/after source hashes and final new-file hashes in .runtime/studio-ui/visual-director-2g-01/completion-final.json.

## Commands and targeted results

All successful final commands exit0:
- python3 -I -B tools/run_hybrid_ui_tests.py --run-id visual-director-2g-launch-final --measurements .runtime/studio-ui/visual-director-2c-01/measure-session/browser-evidence-873568072427a6c3.json —15passed,0failures/errors, no source drift/rejected writes/child commands. Synthetic controller and real loopback HTTP tests: availability/no launch, ready/select/bound export, cancel/close/busy, timeout, malformed output, unconfirmed termination fault, missing artifacts, acknowledgement/duplicates/staleness, malformed paths/metrics, revocation, failed pair publication and diagnostic-validation fault. Final HTTP needed sandbox-approved loopback access. First run's13 non-HTTP checks passed; its HTTP bind was sandbox-denied before HTTP testing. That evidence is retained, not counted as a product failure or passing HTTP check.
- python3 -I -B tools/run_ai_hybrid_tests.py --run-id visual-director-2g-foundation-regression-001 --measurements <same measurement path> —12passed.
- python3 -I -B tools/run_local_tools_tests.py --run-id visual-director-2g-startup-final —9passed, including source-kit integrity and local dependency reporting.
- node --check visual_poster_studio/hybrid.mjs; node --check visual_poster_studio/director.mjs; node --check visual_poster_tests/hybrid_browser.mjs —syntax checks passed.

Total36 final targeted Python tests; earlier development reruns are not added. No full/legacy suite or R1 execution. tools runner source_hashes plus final completion associate exact code with evidence; the runner's concept_generation:false means no actual inference in that synthetic suite, not absence of synthetic draft compilation.

Browser server: python3 -I -B .runtime/studio-ui/visual-director-2g-browser-01/start.py, loopback8785, isolated fresh session and first-party synthetic approved brand metadata; stopped exit0. A real native inference cancellation was confirmed after11.69s, exit-15 and group_absent=true, no source changes. Separate English and Telugu UI jobs then completed, exit0,81.2s/133.0s with accurate narrow family-reading intent. No retry-to-manufacture-success. Brand pin and permitted palette/font metadata were selected in actual Create forms; no registered asset bytes were applied. English and Telugu were filled directly, not an OS-native IME test.

Actual UI actions for each language: create bound source; request generation; observe three previews and rationale/intent; acknowledge review; select first concept; change position; Undo; Save; Reopen; Export SVG+PNG. Separate browser harness /hybrid-acceptance then ran17 checks/language (34total): ready real proposal, embedded fonts/origin clean, all three scenes' ink bounds and exact decoded PNG/RGBA, Undo/save/reopen/exact text, no approval resurrection, bound export identity, selected bound PNG parity, identical SVG export path, prior exports preserved, Media Analysis OFF. Chrome157 browser user agent in evidence; default narrow viewport used, not broad responsive/accessibility qualification.

Evidence:
- .runtime/studio-ui/visual-director-2g-browser-01/session/browser-evidence-c1421ee772668f37.json —English17/17.
- .runtime/studio-ui/visual-director-2g-browser-01/session/browser-evidence-8b2b0bec1b4895a1.json —Telugu17/17.
- session/hybrid-jobs/c90a94373fbf47dc80b99471fd34f80b —real cancellation.
- session/hybrid-jobs/e89d7899132b4310aad2f1fecd19ef26 —English request/output/compilation/termination.
- session/hybrid-jobs/97fb44c924bb4f39b59ffc1fdaa79729 —Telugu request/output/compilation/termination.
- .runtime/studio-ui/visual-director-2g-01/safe-launch-regression/verification.json —final launch92.64s, identical English intent/documents/SVG, exit0/group absent; additional completion verifies launch change, not a prompt/model tuning retry.
- .runtime/studio-ui/visual-director-2g-01/helper-resource-verification.json —single-thread helper limit/group probe, no model execution.

Full stop/restart: python3 -I -B .runtime/studio-ui/visual-director-2g-browser-01/resume.py —explicit same-session resume, four saved projects/four existing exports restored with no errors. All74 session files were byte-identical immediately after restart (restart-verification.json). Browser reopened selected Telugu through Projects and exported again; fifth export retained previous four and reproduced exact SVG/PNG hashes. Inference did not restart. Resumed service stopped exit0. This is process-restart proof, not power-loss proof. No model job left running; successful/cancelled process-group checks retained.

Selected artifacts:
- English SVG b6588fd821d748e7847eda63ba533f21b12def543efc6ece9beb9d8334a8f414; PNG80d9d17e2ec0a736a3f84b706263ab98263b1b5c545917c49fdec7c1509ed700.
- Telugu SVG fb5708958d22a348723a45d54cbf5a612c49fa79e04e182c92ef9d025d5cc943; PNG9599fafa8abc3abc2ca183f61325598a9551bb165b5ba83d88f291d16feaf194.

## Remaining limitations / next decision

Pilot GO only. Text/vector-only fixed1080x1350/two pinned weights/two exact displayed text roles; three generic deterministic compositions, not unconstrained art direction. AI intent quality and subjective brand/originality claims require review; English/Telugu evidence is one brief each. Native Telugu visual/IME and full accessibility approval still pending. Slow/high-memory local inference remains a product limitation; no throughput benchmark, machine-wide scheduler or aggregate containment guarantee. Status compares current process-local proposal only; restart retains saved projects and provenance but does not restore an executable ready job/comparison. No automatic retry, restart or repair; failed publication can retain a blocked orphan candidate as recovery evidence, never corrupt an existing source.

No new licensing adoption. Existing runtime/model/font qualification reused; matching source/native/tokenizer/conversion/build/distribution/reprovisioning gaps remain open. Using already installed local tools is not independent offline distribution closure. Gate A real-media qualification, image/OCR/video capabilities, offline distribution, M6 integration and production release remain separate decisions. No work on those gates commenced.

STOP after Phase2G implementation/evidence. User acceptance remains separate; do not proceed automatically into a new gated milestone.
