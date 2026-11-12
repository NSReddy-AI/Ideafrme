# R2 safe development roadmap — separately authorized tracks

Date: 2026-11-10. Planning only. Read the
[architecture decision](R2_ARCHITECTURE_DECISION_RECORD.md) and
[authorization matrix](R2_NEXT_AUTHORIZATION_MATRIX.md) first. **No implementation is
approved**, including the technically independent work below. R2-A remains NO-GO.

## 1. Dependency separation and authority

Gate A=Security, B=Contracts/Bridge, C=Dependencies/Licensing, D=Evaluation. A technically
independent slice may test contract behavior without a qualified image worker; it cannot
claim to complete R2, qualify an image boundary or accept the production report pipeline.
Gate B design is provisional; independent conformance remains required. Gate C checks
for an existing stdlib-only test runtime can be scoped independently of decoder adoption.
Gate D image benchmarks cannot be replaced with synthetic contract fixtures.

The user approves exact implementation/file/test/write scope before any track starts,
then separately accepts its evidence. Passing a track grants no next-track permission.
No current task runs tests or creates modules, executable fixtures or runtime evidence.

## 2. Track 1 — synthetic report and persistence conformance

### Purpose and exclusions

Implement, only after separate authorization, the five proposed R2 record contracts,
their deterministic identities, review/job transitions and isolated persistence using
small, first-party synthetic JSON/opaque byte resources. No actual image/model/font,
PNG signature/parser/decoder, pixel arrays, OCR, renderer, resource probe or subprocess
worker. A literal Telugu string is contract data, not OCR or shaping evidence.

Synthetics may carry schema-required measured/inferred fields to exercise validation,
but are visibly labelled fabricated test values and never described as actual findings.
Their source/normalized hashes identify supplied dummy bytes or deliberately missing
resources, not an image. Missing resources fail eligibility; a resolver must not fetch
or manufacture bytes to satisfy a hash.

Synthetic progression through decoding/extracting/ocr states tests the state machine
only. No real processing occurred. Resource evidence comes from a test-only provider
that cannot be configured as an operational qualification source. All test stores and
their evidence stay in a synthetic namespace; no operational publication route exists.
A later real supervisor must validate qualified resource/rights evidence before accepting
reports; test success or human review does not bypass that obligation.

### Exact proposed file allowlist (none created now)

Workspace-relative paths below would be the complete initial write allowlist for a later
Track 1 request. New files only; if any already exist at authorization time, stop and
review collisions rather than overwrite. All paths resolve beneath AI Studio.

| Proposed path | Boundary / permitted responsibility |
|---|---|
| `r2_contracts/__init__.py` | Explicit library exports; no initialization writes or process launches |
| `r2_contracts/canonical.py` | Thin wrapper over unchanged public R1 canonical helpers; no new R1 formats |
| `r2_contracts/schema.py` | Exact five R2 shapes/enums/values and envelope bounds |
| `r2_contracts/identity.py` | Observation/word preimages and deterministic IDs |
| `r2_contracts/closure.py` | Page/index ordering, counts, resource pins and aggregate limits |
| `r2_contracts/state.py` | Review ancestry, immutable Job transitions, sticky invalidation and current eligibility |
| `r2_contracts/persistence.py` | New synthetic-only store, expected-HEAD commits and explicit recovery; never R1 private Store reuse |
| `r2_contract_tests/__init__.py` | Test package marker only |
| `r2_contract_tests/support.py` | Synthetic record/resource builders, deterministic clock/role/resource stubs and fault adapter |
| `r2_contract_tests/test_schema.py` | Closed shapes, metric/word/region and per-envelope rejection |
| `r2_contract_tests/test_canonical.py` | G1/R2 vectors, exact bytes/hashes and invalid numeric/Unicode cases |
| `r2_contract_tests/test_closure.py` | Referential/aggregate/identity bounds and missing resource cases |
| `r2_contract_tests/test_state.py` | Generation/review/approval/recovery eligibility behavior |
| `r2_contract_tests/test_persistence.py` | Isolated save/reopen, concurrency and injected-failure behavior |
| `r2_contract_tests/test_isolation.py` | Import/write allowlist and accepted-source preservation; not hostile-native isolation |
| `r2_contract_tests/fixtures/synthetic-records.json` | Frozen invented records/resources and expected outcomes, no actual media |
| `r2_contract_tests/fixtures/canonical-vectors.json` | Exact documented vectors and independently reviewed additions |
| `tools/run_r2_contract_conformance.py` | Explicit trusted synthetic-only runner, fresh evidence root, no default launch on import |
| `tools/r2_contract_verify.mjs` | Independent JavaScript schema/identity/closure/state reader, no renderer/network/package lookup |
| `.runtime/r2-contracts/<fresh-run-id>/**` | All test stores, subprocess inputs/outputs if separately approved, locks, temps, caches and evidence |

No new operational CLI, backend adapter, bridge writer, worker launcher or arbitrary
external report importer belongs to this allowlist. No `r2_data/` is created. No changes
to `style_recipes/`, `creative_core/`, `poster_render/`, existing `tools/`, tests, examples,
handoffs, manifests or old evidence. Only the two specifically named NEW tool files may
be added under tools. A later handoff path requires explicit inclusion in that request.

### Reuse and public interface proposal

Read-only inspection identified `loads`, `bounds`, `canonical` and `digest` in the existing
`style_recipes/canonical.py`. Freeze their exact compatibility/signatures before approval;
reuse compatible bounded serialization/hashing behavior read-only. Do not use R1-specific
`ref` construction for R2 CRefs, or weaken bounds,
register R2 schemas there, monkeypatch it or copy its entire implementation unnecessarily.
Reuse stdlib JSON/hash/integer/decimal/locking/filesystem primitives rather than installing
a schema/database package. The separate JavaScript reader must not merely invoke the
Python validator or compare Python-generated expected values to themselves. Existing
Node is only a conformance comparator, not a required production runtime.

Proposed library operations: validate a record/envelope; calculate observation/word ID;
validate a complete Index/page closure; evaluate a proposed Job/review transition and
current eligibility using explicit trusted time/roles/resource status; create/read a
synthetic store, commit with expected HEAD, and explicitly recover selected PREVIOUS.
Freeze names/signatures, error taxonomy and mutation guarantees in the later request;
they are not authority to invent new stored fields or expand the format.

### Mandatory test inventory

1. **Canonical/schema:** reproduce all ten documented R2 hashes and G1-compatible Unicode,
   scalar key order, signed64, decimal-string, half-even and escape cases in two readers.
   Reject duplicate decoded keys, unknown fields/version, missing nullable fields, bool
   as Int, floats/exponents/-0, invalid UTF-8/surrogates/BOM and each size/depth/member
   boundary. Preserve Telugu and composed/decomposed strings exactly.
2. **Identity/closure:** slot/region/profile/source/reading-order mutations; duplicate
   logical IDs; palette ranks; exact page ordering/contiguity/source binding; coverage
   sums, missing/wrong resources and hashes; partial versus complete capabilities;
   every page/word/scalar/observation/byte limit at minus-one/exact/plus-one where valid.
   Do not fabricate a successful truncated result.
3. **Lifecycle/authority:** all allowed and forbidden operation/state pairs from the
   report contract; immutable generations; wrong/stale expected HEAD; competing sibling
   reviews; exact subject/previous-review binding; correction retained through exclusion,
   revocation and fresh approval; subject-then-whole-report ordering; invalidation/recovery
   watermarks; restored resources do not revive approval. Exercise role/time/rights
   absence, expiry and revocation with explicit test stubs. Stubs do not prove authentication.
4. **Persistence:** durable publication order, exclusive immutable writes, lock contention,
   two-writer conflict, interrupted writes at every publication step, injected ENOSPC/EIO,
   replace/directory-sync failure, post-publication UNCERTAIN, corrupt/missing HEAD,
   invalid PREVIOUS, orphan records, recovery ancestry and last-valid-pointer preservation.
   Reopen rejects invalid closure; no UUID/time arbitration, orphan promotion or auto-repair.
   Unsupported filesystem/atomic-replacement capability fails closed without fallback.
5. **Recovery/concurrency:** repeat recovery without rotating PREVIOUS, valid next normal
   commit, unchanged historical bytes, stale lock-file versus OS-lock ownership, and
   released locks after a bounded test process exit. SIGKILL tests, if separately authorized,
   target only named synthetic test children; they are not worker/security probes.
6. **Isolation/compatibility:** imports have no side effects; no production entry route;
   rejected path traversal/symlink/alias cases use only fabricated fixtures inside the
   evidence root; no R1 store commits or real project associations. Verify unchanged
   accepted source hashes. R2 CRefs stay outside R1 and creative@1. Bridge compatibility
   may use an in-memory recording stub only, not create R1 records or execute the bridge.

Use R2_CANONICAL_VECTOR_SPEC.md N01–N20 as traceable requirements. N13–15/N18 and bridge
failure scenarios remain simulation/compatibility evidence only, not bridge acceptance.
Record a fixture-to-requirement-to-reader/test map before execution; do not promise a
test count before fixtures exist. Independent readers must agree on semantic rejection,
not only the ten hash calculations. Filesystem protocol testing remains separate evidence.

### Prerequisites and later execution safeguards

- User approves this exact Track 1 slice and frozen report/fixture/API interpretations;
  unresolved contract questions return for review rather than change accepted schemas.
- Read-only inventory confirms compatible existing Python/Node identities and licenses;
  no install/download or external environment borrow. Pin accepted inputs and source hashes.
- Inspect all runners before approval: no fixed legacy evidence paths, subprocesses,
  caches or default temporary locations outside the fresh root. Existing runners are not
  automatically safe. Later environment/cache/bytecode settings supplement, not prove,
  confinement. No shared config or global cache writes are permitted.
- Establish the trusted synthetic test writer's documented filesystem assumptions and
  permit only explicitly named test children. Native hostile-media isolation is neither
  required nor claimed for small trusted test programs; no image bytes are admitted.
- Bound fault/concurrency attempts and test storage in advance. Inject ENOSPC; never fill
  the host disk, power-cycle it, create volumes or run destructive filesystem experiments.
  Physical power-loss/OS-crash durability remains unverified, even if process-kill tests pass.
- Keep old evidence immutable. Record commands, exit codes, runtime/source/fixture hashes,
  reader outputs, failure positions and preserved-state hashes in a fresh run directory.

Acceptance is a **synthetic contract-conformance milestone only**, independently reviewed
and separately accepted by the user. All specified cases pass or are explicitly blocked;
unsupported filesystem assumptions prevent persistence qualification. No claim of actual
analysis, image security, full Gate B, clean offline rebuild or full R2 completion.
Rollback disables the new synthetic entry points, preserves previous heads and evidence,
and stops on uncertainty. Do not delete data, rewrite accepted code or migrate stores.

## 3. Track 2 — independent manual creative work (proposed, not approved)

Existing foundations must not be relabelled as newly accepted features:

| Existing area | Evidence/status carried forward | Relevant limitation |
|---|---|---|
| Phase 1 creative@1 core | Reported implemented with 37 tests in M5_HANDOFF.md; not rerun here | Bounded operations/history/persistence; no full editor or arbitrary media boundary |
| Phase 2 poster prototype | Reported implemented, 55-test suite and draft exports in M5_PHASE2_HANDOFF.md | Human visual/Telugu acceptance and independent distribution remain open; no hostile import guarantee |
| R1 manual Recipe CLI/library | User conditionally accepted; acceptance record governs | No automatic Apply, real project integration or automatic R2 revocation subscription |
| Universal Create/Brand/editor workflows | Design proposals in universal specification | Not implemented/accepted merely because specified |

Possible independent slices, each needing its own bounded proposal/authorization:

- **Existing-output human review:** inspect already generated Phase 2 posters/calibration
  for Telugu/English visual quality; record review without rerendering or editing source.
  Requires suitable human language review; does not establish general typography support.
- **Manual brief/concept authoring:** typed user-entered brief and manually authored concept
  drafts, no model, extraction or image reference analysis. Proposed G1/G3 contracts and
  project association need their own review. No automatic concept generation implied.
- **Manual brand-profile authoring:** user-entered tokens, hard/soft constraints and immutable
  profile revisions. Use metadata or existing approved asset pins, not asset decoding or
  extraction. Broader G1 contract still pending; simultaneous rights/protection constraints
  and Locked/Guided/Free semantics must be reviewed before implementation. No hidden scene.
- **Structured creative controls:** a separate trusted-input form/library browser over
  already supported creative@1 operations or read-only R1 APIs. No R1 behavioral change,
  schema extension or Recipe-to-project Apply. Pure state/UI logic can be designed/tested
  independently; a render/canvas/preview path needs separate G2/dependency/typography review.
- **Manual template/layout drafts:** first-party text/geometry only, within the current
  creative@1 vocabulary and capability limits. No generated font shaping/codecs, arbitrary
  imported media, renderer invocation or schema-bypass sidecars. Templates are proposals,
  not previously accepted library content. Export remains a separate approval boundary.

No source filenames or dependencies for Track 2 are authorized here. Each later request
must name NEW modules/fixtures, intended public APIs, exact write roots, acceptance and
rollback. Reuse accepted APIs read-only; if an API/schema change is necessary, stop for
separate review. Do not modify the Phase 1/2 or R1 implementation as a convenience.

All Track 2 slices are technically independent of R2 decoding only within those exclusions.
Any image preview, asset import, model service, font processing, canvas-library acquisition,
reel adapter or automatic Recipe application leaves that safe scope. R3–R6, full Brand
Studio/editor integration and G5/M4 integration remain unauthorized. Acceptance requires
reversible drafts, unchanged historical approvals, capability/brand/rights checks and an
explicit human decision; rollback disables the new route while retaining prior data.

## 4. Track 3 — untrusted media processing (blocked)

Decoding, normalization, extraction, OCR, hostile previews, actual media-derived reports,
resource probes and operational R1 bridging remain blocked. Entry requires qualified
Gate A, scope-appropriate Gate B/C/D closure and separate R2-A/B/C authorizations.
Contract tests cannot supply real rights, source images or resource evidence. No decoder
is loaded in the controller or legacy renderer to bypass the missing boundary. No
acquisition or provisional dependency adoption follows from this roadmap.

## 5. Track 4 — containment architecture decision (future authorization)

No current research execution is commissioned. A future request must identify a specific
supported alternative or explicitly proposed requirement revision, with attributable
host-memory/sink/lifecycle/thread mechanisms, offline/license/size feasibility and finite
go/no-go criteria. It must not restart the closed native/VM investigation under a new name.
Design review, exact artifact approval, provisioning, experiments and implementation are
separate decisions. No silent relaxation of caps or reinterpretation of allocations.

## 6. Completion and stop

Documentation closure supplies an ADR, four-track plan and decision matrix only. Suggested
next decision: whether to request the bounded Track 1 implementation proposal; not to
begin it. Track 2 may be separately prioritized without accepting an R2 security solution.
No claim of R1 production readiness, R2 implementation approval or full M5 completion.

**STOP. Await explicit implementation authorization naming the chosen track and scope.**
