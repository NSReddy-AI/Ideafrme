# Visual Poster Studio — versioned reorder and explicit resume

Date: 2026-11-10, America/Toronto. Bounded implementation and verification report; **not full Visual Poster Studio or product acceptance**. Gate A remains unchanged. No R1, M4, production, image/OCR/video processing, dependency acquisition or paid services are involved.

## Exact authorized file boundary

Modified only:

```text
creative_core/operations.py
creative_core/validation.py
visual_poster_studio/service.py
visual_poster_studio/index.html
visual_poster_studio/app.js
visual_poster_studio/__main__.py
visual_poster_studio/exports.py
```

Created only:

```text
visual_poster_studio/session.py
visual_poster_studio/recovery.py
visual_poster_tests/test_reorder.py
visual_poster_tests/test_compatibility.py
visual_poster_tests/test_resume.py
visual_poster_tests/test_recovery.py
tools/run_visual_resume_tests.py
docs/VISUAL_REORDER_RESUME_CONTRACT.md
```

Before writing, all 15 paths and ancestors were checked for symlinks, new paths checked unused and existing targets checked regular/single-link. Exact before-source bytes and SHA-256 baseline are retained in `.runtime/studio-ui/reorder-resume-implementation-20261110-01/`. Its `completion.json` records exact before/after hashes, eight new-file hashes and final source/test associations. The baseline covers 143 inspected non-runtime files; accepted R1 source/tests and R1/G1 records were excluded from content reads. No whole-machine or independently observed R1 hash-preservation claim is made. Task writes were confined to the seven approved modifications, eight creations and new isolated runtime roots.

Accepted manual UI files, creative-core document/persistence/public-export files, prior Visual renderer/font/server files, existing tests, previous handoffs and frozen R2 formats remain unchanged. Relevant existing core and Visual tests are imported unchanged by the new runner. Existing test outputs/evidence are not reused or overwritten.

## Track A: history protocol version 2

Content remains `ai-reel-studio/creative@1`, schema_version 1. Absent `history.version` means legacy history v1. The only explicit envelope version supported is integer 2; explicit 1, unknown versions and booleans are rejected. V1 documents remain unmodified by validation and ordinary operations. The first acknowledged reorder adds the v2 envelope marker in the same transaction; undo/redo and history branching never remove it.

Public apply operation:

```json
{"op":"reorder","expected_revision":12,"view_id":"portrait","ordered_element_ids":["layer-b","layer-a"],"acknowledge_upgrade":true,"legacy_checkpoint_sha256":"<64 lowercase hex characters>"}
```

The two upgrade fields are required for first upgrade and must be absent on subsequent v2 core operations. The Visual adapter handles checkpoint creation and only forwards these fields when upgrading. The existing public apply function signature is unchanged; its accepted operation set is explicitly extended.

The operation validates current integer revision and a complete exact same-view permutation. No-op, duplicate, missing, foreign-view and unknown IDs are refused. It deep-copies the document and replaces only that view's occupied element-array positions. The central commit performs one before/after transaction, one revision increment, redo truncation, current approval clearing and history-limit enforcement. No remove/add simulation, UUID ordering or direct array mutation is used as a transaction substitute.

Persisted reorder validation independently verifies unchanged non-element core content, identical ID-to-element mappings, identical view-slot positions and exactly one changed view sequence. This rejects non-order mutations hidden inside reorder history. Normal undo/redo restores complete snapshot arrays without restoring current approvals. Historical named snapshots, their approvals and previous export artifacts remain unchanged.

### Explicit acknowledgement and checkpoint

The UI exposes backward/forward controls with edge disabling. First use shows an in-page warning, unchecked acknowledgement and disabled confirmation button. Confirmation creates/verifies a checkpoint and then calls the public core operation. The warning states that older readers cannot open the upgraded history, even after Undo. Cancel performs no reorder.

Checkpoint: `projects/<project-id>/legacy-checkpoints/<sha256>.json`, exact canonical legacy document bytes plus newline, including existing history, current approvals and historical snapshots. Checkpoint creation is exclusive, file/parent synchronized, mode 0444 and read back. The core verifies confined path, digest, exact matching legacy bytes, single-link status, byte bound and absent write permissions before upgrading. Checkpoints count toward the shared recovery budget and are never evicted.

This is immutable by application policy and filesystem permissions under the trusted-local-user model; it is not WORM storage or protection from a malicious owner changing permissions. Checkpoint verification does not authenticate user identity.

### Compatibility and rollback

New readers accept legacy documents and v2 histories. A retained copy of the actual pre-extension validator was executed against fixtures: legacy accepted; v2 rejected, including after undo. No historical content snapshots or their fingerprints are rewritten for migration. Historical snapshot content does not contain the history-envelope field.

Rollback to an old reader requires using the retained legacy checkpoint as an explicit separate working copy, losing subsequent work. No automatic downgrade, history stripping or bulk migration exists. Restoring old code alone cannot open a v2 history. No checkpoint or source document is silently rewritten to make it load.

## Track B: explicit Visual-owned resume

Fresh startup creates a distinct `visual-session.json` linking the accepted manual session ID to Visual ownership version 1, the exact renderer profile and pinned font hashes. Resume refuses missing/unknown markers, wrong identity links, changed profiles, aliases, external paths and incomplete session layouts. Legacy Visual roots without the marker are not adopted, including prior acceptance evidence roots.

Ownership markers are validated before calling accepted Studio resume. Its OS flock is acquired before project inspection/recovery. A second writer is rejected; stale lock-file existence is not treated as a live lock and lock files are not removed. Current directory synchronization is explicitly checked on resume. Marker identity is application ownership metadata, not protection from a hostile local user forging all files.

Saved documents, histories and manual subset are validated under the writer lock. Invalid/conflicting/interrupted projects are withheld from normal editing and reported in session status. New font failures disable rendering/exports with diagnostics while validated manual source remains available. No font/profile fallback, schema migration or automatic repair occurs. Analysis remains OFF. Export handshakes are memory-only and expire at restart; each server receives a fresh CSRF token.

### Append-only recovery journal

`recovery/<project-id>/<8-digit-generation>/` retains:

- `before.json` when a previous saved primary exists;
- `after.json`, exact proposed bytes;
- `intent.json`, version, project/generation, revision and before/after SHA-256;
- `complete.json`, published after accepted core save, exact primary readback and explicit directory sync.

Files are exclusively created, flushed and synchronized; candidate/intent/completion records are read-only. Generations and save ancestry are checked. Previous completed recovery data is never replaced, even when a later save fails. Core persistence itself is unchanged. Normal explicit Save still uses its existing primary/previous replacement behavior; recovery never automatically repairs those files.

The strict 128 MiB application budget includes retained journal and legacy-checkpoint file bytes, with an 8192-entry scan bound and conservative reservation overhead before writes. Filesystem metadata and physical allocation are not a filesystem-enforced disk quota. Exhaustion refuses further saves/checkpoints; no history/evidence eviction occurs. Source editing can continue in memory, but unsaved work is not durable and must not be mistaken for a successful save.

Interrupted writes produce explicit `interrupted-save`, `primary-conflict`, `untracked-document`, `invalid-document` or live `durability-unconfirmed` states. A failed save is not reported successful. The journal classifies an unfinished intent's primary as previous, candidate or unknown without replacing it. Hash-invalid or incomplete metadata is not interpreted optimistically. Unsupported sync blocks startup/resume or the affected save; valid-looking completion bytes cannot clear the live failure state automatically.

Actual OS crash and physical power loss are not proven. fsync/readback/application crash testing do not prove storage-controller or power-loss behavior. Unsaved in-memory edits are not auto-journaled.

### Explicit recovery copy

For a hash-verifiable retained intent, the CLI can select before/after explicitly and create a NEW Visual-owned session with the same validated document/history bytes. Original primary, previous, checkpoints, journal and exports remain unchanged. The new session records provenance. No in-place finalization/replacement is performed.

Incomplete/hash-invalid intent metadata has no automatic recovery-copy path; the project remains blocked and its retained data requires separate inspection. Recovery does not invent missing hashes or select a candidate by UUID order. Legacy session adoption remains deferred.

### Retained export audit

Resume counts all export directories, including partial ones; totals retained artifact bytes; validates complete draft manifests and SVG/PNG hashes; and rejects aliases. Partial exports remain retained and count toward quotas. Corrupt/unknown exports block new exports while manual editing remains available. No files are deleted to free space. New outputs use new directories and original artifact hashes remain unchanged. Existing browser PNG qualification remains conditional, with exact RGBA checks and no backend substitution.

## Commands and evidence

From `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`:

```sh
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-reorder-resume-001
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-reorder-resume-002
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-reorder-resume-003
python3 -I -B tools/run_visual_resume_tests.py --track all --run-id visual-reorder-resume-004
env -u NODE_COMPILE_CACHE node --check visual_poster_studio/app.js
```

Runner also supports `--track reorder`, `--track resume`, `--track regression`, each requiring a fresh run ID. The `all` run reports per-suite counts. No legacy runner or package manager runs.

- Run 001: exit 1, 110 tests, 3 failures/29 errors. Host denied loopback setup; the initial audit guard also misresolved fd-relative in-root cleanup paths as outside writes. Rejected operations did not establish external writes. All evidence retained.
- Run 002: exit 0, 110 tests, zero failures/errors/rejected operations after directory-FD-aware confinement and authorized loopback permission.
- Run 003: exit 0, 114 tests, zero failures/errors/rejected operations; additional history/checkpoint and sync failure coverage.
- Run 004: final source, including port-failure diagnostics and final UI acknowledgement; actual counts/results are authoritative in `.runtime/studio-ui/visual-reorder-resume-004/results.json` and `tests.txt`.

The runner allows only its own explicitly parameterized child-server entry point, whose Python audit guard is re-established before server startup. All child roots are beneath the fresh evidence root, sockets are loopback-only, bytecode is disabled and process waits/suite runtime are bounded. Existing core fixtures are redirected through their module runtime binding, without changing their source. The runner does not inspect R1 source. Python audit hooks are trusted synthetic-test instrumentation, not hostile-code OS isolation.

Process checks stop and restart real Python servers, require exact saved document/history/SVG equality, verify fresh CSRF, inject SIGKILL immediately before and after primary replacement, and verify explicit recovery-copy source preservation. These are process-termination checks, not OS-crash or power-loss experiments. ENOSPC and unsupported synchronization are injected, with no physical disk exhaustion or destructive filesystem testing.

### Browser acceptance

Fresh session root: `.runtime/studio-ui/visual-reorder-browser-20261110-01`.

Browser actions: create Telugu/English text; add overlapping violet rectangle and gold ellipse; save and export legacy order; explicitly acknowledge history upgrade in-page; reorder ellipse backward; undo and redo once; save/export; fully stop server; resume the same root; reopen project; export again to a new directory. Browser-confirm dialog automation initially failed and was replaced by the final explicit in-page checkbox/confirmation. An earlier unsaved test reorder was discarded by stopping the synthetic session and reopening its saved v1 state; its retained checkpoint was not removed or overwritten.

Evidence:

- `before-reorder.jpg` — original paint order.
- `browser-before-resume.json` — exact saved revision-8 history/document/exports hashes.
- `browser-after-resume.json` — observed reopened revision, layer order, SVG identity, restored quotas and console results.
- `restart-verification.json` — independent byte/hash comparison; document, history, SVG and original exports identical; three export sets after one additional export; repeated reordered PNG hash identical.
- `after-resume.jpg` — final browser screenshot.

Before reorder SVG/PNG hashes:

```text
4ec29f8aebe92b0178a428fff3e9bbd298778b2941e14c49ec0d8b3c5b2a5bc4
f822cc5956f8c380679690f771f0679a00acd56be71ef2f72e09bcae7afc69bf
```

Reordered SVG/PNG, unchanged after full restart:

```text
92076f59174740147e981536a7aae1d4a01663461072e5ff7fb1593372536412
0568a3f324c5d7ad4e8306c535b5998dfd4f2d5acba997df53a72906e7acd4b2
```

Both export manifests report exact preview-raster/PNG-decoded RGBA parity. Paint-order change visibly occludes the gold ellipse with the upper violet rectangle. The original export set remains intact. Native Telugu reader approval is not inferred from these screenshots. No browser console errors were observed in final evidence.

Browser startup commands used the fresh explicit root on 8766, then explicit resumes on 8767 and 8768. Each successful server was stopped with SIGINT, exit 0. One immediate resume attempt on 8766 exited 2 with the then-generic startup diagnostic; using free 8767 succeeded without session repair. The final CLI now reports EADDRINUSE explicitly and recommends `--port 0` or a free port. Busy-port refusal is covered by a bounded injected regression. Process tests use port 0 and record exact child commands in results.json.

## Use and rollback

Fresh:

```sh
python3 -B -m visual_poster_studio --port 8766
```

Explicit resume (root must have the new Visual ownership marker):

```sh
python3 -B -m visual_poster_studio --resume --root "/absolute/Visual-owned/runtime/root" --port 0
```

Read the printed loopback URL. Select the saved project from This session. Resume does not modify source, projects or exports just to make them compatible.

Explicit recovery copy, after inspecting a blocked project's state:

```sh
python3 -B -m visual_poster_studio --resume --root "/absolute/Visual-owned/runtime/root" --recover-copy "<project UUID>" --candidate after --port 0
```

Choose `before` instead when explicitly desired and present. A fresh destination is generated; it never adopts an old acceptance-evidence root. Unsaved drafts remain memory-only. Keep the source root and checkpoint for rollback.

Rollback: stop the new application. The old reader can still use untouched legacy documents/checkpoints. It cannot open v2 histories. Do not strip version flags or restore old source files over current work without a separate reviewed rollback. Accepted manual UI source/behavior and core persistence are unchanged, but all applications importing the shared core see the now-explicit supported history extension.

## Remaining conditions

No independent acceptance is implied. Full Visual Poster Studio still needs native Telugu typography/IME and accessibility review, distribution/offline rebuild closure and human acceptance of reorder/resume. Legacy Visual-session adoption remains deferred. No hard hostile-actor filesystem boundary, authenticated browser QA, physical-power-loss durability, cross-browser pixel identity or automatic recovery of incomplete/hash-invalid metadata is claimed.

STOP after bounded implementation and evidence reporting. No real-media execution or further milestone authorization follows.
