# M5 R1 — manual Style Recipe implementation handoff

2026-11-10. User authorized the reviewed G1 manual-R1 design and six bounded R1
capabilities. IMPLEMENTED / ACCEPTANCE REQUESTED. R1 user acceptance remains separate;
R2–R6, M4 integration and production release remain NOT AUTHORIZED. Historical G1 draft
headers describe their drafting stage; this authorization does not silently edit them.

## Delivered architecture

Independent `style_recipes` Python module and structured CLI; no existing core/renderer
replacement. Manual creation/editing makes immutable Findings and Recipe revisions.
Closed schemas, bounded strict JSON, exact decimal strings, SHA-256 payload identities,
explicit project/dependency refs, Brand snapshots and structured rights records follow
the reviewed manual-R1 contract. Review and availability events are append-only and
current eligibility is separate from historical approval. Revocation/correction/adverse
dependency events invalidate affected Recipes; restoration requires fresh ordered reviews.

Persistence uses exclusive immutable record creation, write/reopen/hash verification,
single-writer flock, expected HEAD checks, file fsync + F_FULLFSYNC, directory fsync and
atomic HEAD replacement. Normal writes preserve a valid PREVIOUS before HEAD publication;
recovery compares captured raw HEAD generation, preserves synced quarantine evidence,
keeps PREVIOUS unchanged and invalidates current approval eligibility. A failed directory
sync after publication returns UNCERTAIN rather than a false rollback/success claim.
Only tested local macOS APFS is writable; paths/links/devices/unsupported formats fail
closed. Store writes are restricted to AI Studio/r1_data or .runtime/r1.

No actual brand, source media or project was cleared by the tests. All test reviews,
rights decisions and associations are synthetic; their actor labels are not user signoff.

## Files created and changed

Created application files:
- style_recipes/__init__.py — public style-only primitives.
- style_recipes/canonical.py — strict bounded JSON and canonical bytes/hashes.
- style_recipes/schema.py — closed schemas/property catalog.
- style_recipes/state.py — graph/history validation and eligibility/invalidation.
- style_recipes/store.py — isolated store, qualification, commit/recovery.
- style_recipes/manual.py — manual factories, edits, reviews and associations.
- style_recipes/__main__.py — structured CLI.

Created acceptance files:
- r1_tests/__init__.py, helpers.py — synthetic fixtures and actor/time constants.
- r1_tests/test_contracts.py — schemas, canonicalization, lifecycle, rights and compatibility.
- r1_tests/test_persistence.py — crash/fault/concurrency/recovery/OS isolation.
- r1_tests/test_cli.py — actual manual CLI create/edit/rejection workflow.
- r1_tests/fault_worker.py — isolated subprocess crash/lock/failure/probe worker.
- r1_tests/fixtures/canonical.json — frozen cross-language cases.
- r1_tests/fixtures/records.json — frozen full records and expected payload hashes.
- tools/r1_canonical.mjs — independent JavaScript parser checks/serializer/hash verifier.
- tools/run_r1.py — reproducible suite/evidence/protected-file verification.
- docs/R1_TEST_ISOLATION.sb — dedicated macOS no-network/R1-only-write test policy.

Created documentation: docs/R1_DEPENDENCY_DECISIONS.md, docs/R1_MANUAL_USAGE.md and this
M5_R1_HANDOFF.md. Changed existing file: THIRD_PARTY_INVENTORY.md, R1 inventory addition
only. No G1 specification, creative_core, poster_render, existing test/tool/example or
existing Phase 1/2 handoff was edited. All generated fixtures, failed-transaction orphans,
stores and evidence are retained under .runtime/r1; these are not real user projects.

## Executed evidence

R1 command:
`/usr/bin/sandbox-exec -f docs/R1_TEST_ISOLATION.sb python3 -B tools/run_r1.py`

Final run: **43 tests, zero failures/errors, zero audit violations**, exit 0, about
42.34 seconds. Runtime: Python 3.15.2, Node v26.13.0, macOS arm64. The dedicated OS
sandbox inherited by subprocesses denied network and writes outside R1 data; explicit
denial probes passed. Nested sandbox application needed desktop permission; it was not
weakened. An earlier evidence-only platform metadata helper attempted /dev/null writes,
which the guard denied; it was removed and the complete suite rerun successfully.

Cross-language evidence: **46 cases agree byte-for-byte and hash-for-hash** between
Python and independently written JavaScript/Node, with rejection agreement. Includes
all 13 documented vectors, Unicode scalar versus UTF-16 sorting, Telugu/English,
NFC/NFD distinction, alternate escapes, controls, signed-64 endpoints, duplicate decoded
keys, invalid numeric/encoding forms and all nine complete record types. Node uses
BigInt/source-aware parsing so signed-64 values are not rounded through Number.

Persistence evidence: **148 instrumented fault scenarios**:
- 42 abrupt process-exit cases across normal commit stages.
- 32 abrupt process-exit cases across recovery stages.
- 42 ENOSPC-injection cases across normal stages.
- 32 ENOSPC-injection cases across recovery stages.

Old/new committed snapshots reopen consistently after normal interruptions; recovery
faults retain PREVIOUS byte-for-byte. Tests also execute SIGKILL mid-write, lock release,
stale lock metadata, two real competing writer processes, stale HEAD/recovery generations,
partial records, real OS RLIMIT_FSIZE write failure, corrupt payloads, missing HEAD,
link/FIFO guards, failed sync and unsupported-platform qualification. Real local probes
passed file sync, F_FULLFSYNC, directory sync, exclusive lock and replace/reopen checks.

Existing regression command: `python3 -B tests/run_isolated.py` — **55 tests passed**,
zero isolation violations, approximately 1.99 seconds. This executed existing Python
core/render-policy tests; no browser renders, M4 scripts or production tests were run.
An explicit creative@1 save-free compatibility test verifies unchanged canonical source
and its existing validator/fingerprint while project associations remain style-only.

Machine-readable evidence:
- .runtime/r1/acceptance-results.json — test result, environment, source hashes, boundary audit.
- .runtime/r1/latest-tests.txt — complete final R1 unittest transcript.
- .runtime/r1/cross-language-results.json — each case's canonical hex/hash or rejection.
- .runtime/r1/persistence-fault-results.json — each fault/stage/expected preservation result.
- .runtime/r1/filesystem-qualification.json — actual local primitive probe results.
- .runtime/r1/isolation-results.json — actual kernel denial probe results.
- .runtime/r1/protected-baseline.json — preimplementation hashes of 25 protected files.
- .runtime/r1/runtime-identity.json — local executable/notice hashes and locations.
- .runtime/r1/existing-regression-results.json — recorded completed regression-run summary.
- .runtime/r1/tests/ — retained synthetic stores, immutable records and recovery evidence.

Full R1 source/fixture SHA-256 values are in acceptance-results.json, not inferred from
test counts. Existing-regression-results.json records the completed tool result rather
than pretending to contain an unretained full regression transcript. The commands above
reproduce both suites using installed runtimes; they do not install anything.

## Architecture/dependency decision and closure

See docs/R1_DEPENDENCY_DECISIONS.md: existing standard-library primitives and Node test
runtime were researched before building. Zero new runtime packages/paid services/models.
Python authoring is independent of Chrome/HyperFrames/private node_modules; existing reel
engine remains untouched. No bundled runtime distribution, license-complete native SBOM
or clean independent offline rebuild is claimed. Exact installed source/notice paths and
remaining G7 acquisition/build closure work are recorded, not waived.

## Known limitations and acceptance boundaries

- This is a CLI/library authoring slice, not the interactive canvas or integrated studio.
- ENOSPC was injected at real persistence boundaries; the host volume was NOT filled.
  A real OS file-size failure was separately exercised. Do not label injected ENOSPC as
  a physically full APFS volume test.
- Actual process crashes, SIGKILL and sync/rename probes are not physical power-loss or
  drive-firmware certification. No clean offline runtime rebuild was performed.
- One trusted local actor. Labels/confirmation flags are explicit attestations, not
  cryptographic identity, evidence retrieval or proof of legal ownership. Plain files
  remain modifiable by the local owner; hash checks detect changes, not malicious re-signing.
- Rights with unimplemented obligations fail closed. Restricted project-scope grants
  can be validated for their exact project context; generic Finding/Recipe approval
  currently conservatively refuses project-limited resource clearance without context.
- Capability support is manual-style-authoring only. Unsupported dimensions, features,
  schemas, motion and measured/inferred findings are rejected; no silent approximation.
- Project associations are synthetic-only snapshots; no real creative project receives
  bindings/edits. Atomic creative+sidecar transactions remain R3, not claimed here.
- History graph bounds (64 depth, 4096 records, 64 MiB and 32 active roots plus aggregate
  JSON limits) eventually stop writes. No automatic pruning/checkpoint/migration/GC.
- Unique bounded staging files are used inside staging rather than transaction subfolders;
  scratch remains nonauthoritative and writer-owned. Only HEAD publishes state. Failed
  staging/orphan records are retained; no automatic destructive cleanup/salvage exists.
- Missing/invalid PREVIOUS, oversized damaged pointers, corrupt immutable hash paths or
  unsupported filesystems fail closed and need separate explicit salvage/repair decisions.

## Protected-workspace confirmation and stop point

All 25 preimplementation protected core/renderer/test/tool/example files match their
baseline hashes. The agent made no writes or setup actions in Reel Studio or
Reel Studio_dev, did not contact/interfere with the M4 agent, and ran no M4/production
commands. The other agent may independently change M4; this report does not claim a
global filesystem freeze. The R1 suite's kernel write fence protects both workspaces.
No dependency install, Git initialization/worktree/merge, model acquisition, engine
replacement, production swap or paid service activation occurred.

Stop here for user review of R1 implementation and evidence. R1 acceptance and any
R2–R6 implementation require separate user approval; no next-phase work has begun.
