# M5 Home, Projects and explicit session navigation

## Functionality

Default launch now opens a same-document Home screen: Create poster, Open project, Resume session and persistent Home/Projects/Editor/Recovery navigation. Home/Projects/Recovery hide existing editor panels without replacing their DOM or project state. Unapplied text, current selection and working edits survive return navigation. Create uses the accepted form; Open uses the accepted project API and existing draft-apply behavior. The skip link opens Editor instead of focusing a hidden panel.

Projects displays only metadata actually provided by the active service: project name, full ID, saved availability and dirty status. Other sessions are listed from validated ownership markers; their project documents are not inspected until explicit resume under the existing OS writer lock. Ordering uses observed folder modification time and is labeled as such, not invented last-opened metadata. Nested/test sessions outside the direct owned runtime-session list are not recursively discovered. Unknown/invalid ownership/profile is unavailable. Empty and service-failure states are explicit.

Resume requires a listed directory, matching current/target ownership IDs, explicit checkbox and user action. Path inputs, stale identities, active target, pending export and any unsaved current working project refuse switching. Unapplied current-tab drafts are refused in UI. Target VisualStudio resumes and acquires its OS writer lock before project loading, while source remains locked; failure preserves source. Only after target opens does source close. Server replaces its current service, rotates CSRF and client reloads onto Projects. Existing tokens then fail mutation checks. Server shutdown closes the active service, including a replacement session. No new daemon, worker, process launch, retry or persisted session registry.

Important limitation: other browser tabs' unapplied text drafts are not observable by the service; the acknowledgement instructs closing other Studio tabs. Their old tokens become invalid after handover. Current server-side unsaved work across all loaded projects is protected. No force-discard or silent save is added.

Recovery screen shows active-session blocked project IDs/states from existing navigation data, explains v2/v3 upgrade checkpoints and links back to Editor controls. CLI recovery-copy and checkpoint-restore instructions remain explicit, require stopping the service and create a separate session. This screen never repairs, restores or overwrites files automatically. Candidate example uses `after`; select `before` explicitly when appropriate to the validated journal. Existing core/history/ownership/journal formats are unchanged.

## Exact source files

Modified five:
- visual_poster_studio/app.js — navigation adapter, same-document project/create callbacks.
- visual_poster_studio/index.html — Home/Projects/Recovery sections and navigation.
- visual_poster_studio/styles.css — simple shell layout and active navigation styles.
- visual_poster_studio/server.py — fixed home module, read-only session catalogue, protected POST handover and active-service shutdown cleanup.
- visual_poster_studio/service.py — correct navigation history_support to [1,2,3]; no document/history change.

Created five:
- visual_poster_studio/home.py
- visual_poster_studio/home.mjs
- visual_poster_tests/test_home.py
- tools/run_home_tests.py
- docs/M5_HOME_PROJECTS_HANDOFF.md

No dependencies installed. Reuses Python standard library, native browser DOM, existing Visual/Manual APIs, locks and validators. No external assets/CDN or new persisted metadata. Core, renderer, fonts, accepted manual UI, R1, M4, production and Gate A untouched. Source kit's existing source-category capture automatically includes the new Home modules in future kits; prior kit/evidence files remain unchanged.

## Tests and commands

- python3 -I -B tools/run_home_tests.py --run-id visual-home-targeted-001: exit 0; initial 9 tests.
- Same runner, visual-home-targeted-002: exit 1; 10 tests, one test-only error. Shutdown test called a super()-using instance method on a SimpleNamespace rather than a Server instance. Production shutdown had no observed error.
- visual-home-targeted-003: exit 1; 12 tests, same test-only error (already running while prior result was inspected).
- visual-home-targeted-004: exit 0; final 12 tests, zero errors/failures/source drift/rejected writes/processes. Fixed mock uses an uninitialized Server instance with parent shutdown mocked; no socket needed. Adds invalid ownership and pending-export refusal tests. All failed evidence retained.
- node --input-type=module --check < visual_poster_studio/app.js: exit 0.
- node --check visual_poster_studio/home.mjs: exit 0.
- python3 -B -m visual_poster_studio --root '<workspace>/.runtime/studio-ui/visual-home-browser-01' --port 8777: authorized loopback startup; stopped with Ctrl+C, exit 0 after switching to the target session.

Two fresh owned browser fixtures were necessary to verify real session handover. Target session visual-home-resume-browser-01 contained one saved synthetic Telugu project. Browser checks: Home empty state; Create navigation/form/project; unapplied Telugu draft preserved across Home/Editor; Save; real Projects metadata; explicit target selection/ack/resume/reload; target project listing; exact saved text in Editor; Recovery/upgrade guidance; return Home active session. Eleven observed native browser checks, not a separate automated browser suite. Source draft intentionally overflowed its box; existing export refusal remained active and no export was attempted. This was navigation verification, not typography approval.

Evidence: .runtime/studio-ui/visual-home-browser-01/browser-workflow-evidence.json and home-resumed-proof.png. Minor final skip-link/candidate-example changes were syntax checked; the main browser sequence was not repeated for those changes.

Live HTTP checks: GET /api/sessions 200; mutation without Origin/CSRF 403; authorized invalid path 400; wrong Host 403; current session unchanged after refusals. Evidence: http-security-evidence.json. No raw CSRF tokens recorded. Saved source/target project records were not migrated or rewritten by session switching.

Before-source bytes and exact before/after hashes: .runtime/studio-ui/visual-home-baseline-01/baseline.json, before/, completion.json. No R1 content read or M4/production access. All generated sessions/test data/evidence stay in fresh isolated .runtime/studio-ui directories.

## Remaining product work

No known blocking failure for the implemented scope. Catalogue scans are bounded to 4096 direct runtime entries; no recursive project indexing, thumbnail import, project metadata invention or cross-tab draft synchronization. Browser Back/Forward view-history integration is deferred; explicit navigation is supported. Recovery execution remains CLI-only. Brand/Asset contracts, broader workflow gates, native Telugu IME/human typography approval, comprehensive accessibility, offline runtime/install/build/distribution closure and separately qualified actual image/OCR/video analysis remain outstanding. No full M5 acceptance, release, R2–R6 or M4 integration is implied.
