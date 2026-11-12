# R2 pre-implementation readiness and scoped execution roadmap

2026-11-10. **Final readiness: BLOCKED.** Documentation is complete for review; no
experimental gate is passed by this proposal. No worker, decoder, model, fixture or
implementation was created, acquired or run. R1 remains conditionally accepted.

## 1. Gate assessment and evidence

| Gate | Status | Resolved by planning | Unresolved before implementation |
|---|---|---|---|
| A security | BLOCKED; enforcement UNVERIFIED | Native/VM candidates, threat model, unchanged limits and proof plan documented | Complete supported resource/confinement mechanism, literal memory/quota/time accounting and measured fail-closed proof |
| B contracts/bridge | CONDITIONAL draft, not accepted | Five precise proposed formats, pagination/identity/review/recovery rules, computed vectors, public-API mapping | User/independent contract approval; conformance experiments; decision on standalone R1 external-revocation gap |
| C artifacts | BLOCKED; binary closure UNVERIFIED | Three exact official commit anchors, separate model/code licence texts and acquisition checklist | Runtime/native/guest/SDK builds and licence/security closure; artifact SHA/bytes and approved acquisition |
| D evaluation | UNVERIFIED | All21 criteria reviewed, integer split margins and scorer/refinement proposal | Actual lawful images, family-disjoint split, native reviewers/annotations, profile/threshold ratification |

Evidence documents: [security](R2_SECURITY_GATE_DECISION.md),
[report](R2_REPORT_CONTRACT_PROPOSAL.md), [bridge](R2_R1_BRIDGE_CONTRACT_PROPOSAL.md),
[vectors](R2_CANONICAL_VECTOR_SPEC.md), [artifacts](R2_ARTIFACT_QUALIFICATION_PLAN.md),
[freeze plan](R2_FIXTURE_AND_BENCHMARK_FREEZE_PLAN.md). No gate is silently promoted PASS.

## 2. Critical findings and explicit refinements

1. Native App Sandbox/XPC is useful but no full native aggregate-memory/PID/scratch
   solution has been established. Linux cgroup memory can transiently exceed memory.max;
   VM guest RAM is not total host footprint. Strict1GiB compliance remains a proof duty.
2. SBPL/sandbox-exec is not the preferred supported product boundary. A signed helper
   is not a memory quota. A byte ledger is not safe scratch unless all other sinks
   are denied. No Python hook/polling/environment setting substitutes for OS enforcement.
3. Pillow introduces native decoding/CMS exposure but reimplementing a codec would add
   risk. Use patched minimal features INSIDE proven isolation, not inside the supervisor.
4. Source RGBA64MiB, normalized RGBA16MiB and PGM4MiB plus native scratch/models
   belong inside the worker budget; trusted host VM-launcher overhead is measured
   separately. Stages must release buffers serially. No evidence yet establishes peak fit or cold
   OCR within the SHARED15s processing and60s whole-job budget.
5. Earlier redundant Region coordinates could break500-member pages. Proposed pixel-only
   Region and bounded entries allow512 words+64 observations in24 pages; conservative
   encoded budget839,168 bytes fits1MiB, but exact checks/conformance remain mandatory.
6. Palette metric+region alone cannot identify eight whole-image colors. Proposed slot
   participates in ID/sort and resolves collisions. No existing approved schema changed.
7. R2 content/reviews must not collapse origin, correction, approval and availability.
   Immutable Job generations publish review events; raw worker files never approve.
8. Manual R1 provenance can be explicit via resource/selection receipt hashes, but R1
   will not autonomously follow R2 revocation. Dual authority checks are necessary for
   R2 consumers; unchanged standalone R1 cannot provide that guarantee. No cross-store
   atomicity or real-project association is claimed. This requires an explicit scope decision.
9. Canonical primitive arithmetic agrees in Python/JS for10 documented vectors. This
   does not prove new schema/state-machine semantics, library version portability or
   actual report reproducibility. Raw Unicode remains unchanged; metric rounding explicit.
10.120 images are a stratified pilot, not broad professional-quality proof. Family
    leakage, sparse cross-cells, language-specific clean eligibility and calibration
    sample correlation need frozen annotation/evaluation evidence, not invented truth.
11.256MiB deployment includes mandatory guest artifacts if VM selected. Feasibility
    is unmeasured; cannot exclude the guest or waive the limit silently. Source retention
    and complete offline rebuild remain open, beyond installed offline runtime evidence.
12.No paid model, hosted API, subscription or paid VM product is selected. Entitlement/
    signing/distribution feasibility still needs proof without assuming a mandatory
    paid service or disabling OS protections.

These refine prior unapproved R2 drafts explicitly; earlier five documents and all
accepted R1 records remain untouched. A must ratify refinements before execution.

## 3. Separate authorization packets before any phase starts

Packet1: A/B review these contracts, native-versus-VM proof scope, exact intended
memory/scratch accounting and standalone-R1 revocation limitation. No experiment implied.
Packet2: proposed per-file acquisition/retention manifest with known bytes/identities/
licences and unresolved discovery steps, funding/storage/prerequisites. A approves
exact acquisition; B reviews rights. No installs to shared environments.
Packet3: resource-only PoC in a new isolated location using approved artifacts and
synthetic resource/access probes, NO PNG decoding/OCR. Includes rollback and baseline
manifest. This separately authorized experiment can fail; no decoder enabled on failure.
Packet4: actual lawful fixture/annotation/profile/threshold freeze by A/B/C, new-contract
conformance experiments and later per-phase implementation authorization. Human decisions
and measurements cannot be replaced by these planning documents.

## 4. Proposed R2-A — security/import foundation

Entry: Gate A mechanism qualified by resource-only PoC; B contracts accepted; exact C
artifacts approved; D security/analytic fixtures and thresholds frozen; scoped A approval.
Scope: separate launcher/worker boundary, immutable handle import, PNG-only validation,
hard limits/process tree, cancellation/deadlines, job lifecycle/publication/recovery.
Deliverables: isolated import contract/service, minimal validated normalization path,
policy/artifact manifests and fresh failure/isolation evidence. No style extraction,
OCR model execution, source/project mutation, R1 extension or Apply.
Acceptance: existing I01/S01–03/R02 plus contract conformance, actual denial of all resource/
access probes and baseline hashes. Failed enforcement disables all automated imports.
Rollback: stop job/VM, preserve quarantined evidence, disable new entry route; do not
remove acquired materials or delete old projects without separate cleanup authorization.
Exit: independent read-only review and A accepts exact R2-A slice. Does NOT authorize B.

## 5. Proposed R2-B — deterministic visual analysis

Entry: R2-A accepted; exact analysis profile/metrics/CMS behavior and synthetic/real
fixture freeze; resource/native artifacts qualified; separate A implementation approval.
Scope: metadata, palette/coverage, gradients, sampled contrast, geometry/occupancy,
treatment proxies and deterministic bounded report pages/index. No OCR invocation,
subject-semantic certainty, editable-layer recovery, R1 bridge, editor or reel change.
Deliverables: replaceable feature adapters, evidence-linked reports, strict validation,
repeatability/latency/resource and synthetic accuracy evidence under existing21-row map.
Acceptance: I02/C01–03/G01/M01/D01/O02 and continued S/R02 checks. Unsupported or ambiguous
metrics report explicit unavailable/inferred status, not missing mandatory capabilities.
Rollback: disable analysis adapter/profile, retain immutable reports and previous valid
job state; no historical reinterpretation or approved asset substitution.
Exit: independent review and A/B acceptance; new profile review if a frozen threshold
fails, never tune holdout or enlarge limits silently. No authorization for C follows.

## 6. Proposed R2-C — typography/OCR/review/manual bridge

Entry: R2-A/B accepted; English and Telugu exact model/engine closure and language
reviewers qualified; report/bridge contracts approved including revocation limits;
heldout/transcripts/metrics frozen; separate A implementation authorization.
Scope: serial bounded English/Telugu OCR, text geometry/proxies, confidence, human
correction/exclusion/approval and explicitly confirmed manual R1 Recipe draft creation.
No automatic measured imports, unchanged R1 schemas, no project Apply or R3 application.
Deliverables: separate language evaluations, provenance/choice receipts, new immutable
review chains, explicit R1 dependency events and partial-failure/rollback evidence.
Acceptance: T01–04/G02/U01/O01/R01 and continued security, repeatability/performance/
baseline checks. Missing Telugu support or unmet thresholds blocks full requested R2
acceptance; it is not silently deferred because English passed.
Rollback: disable OCR/bridge, stop workers, retain unapproved reports/drafts and exact
outcome refs. Completed R1 draft commits cannot be pretended undone; use explicit new
manual revisions/reviews, never rewrite historical approved records. Incomplete dependency
propagation blocks R2 consumers and is reported; raw R1 limitation remains disclosed.
Exit: independent audit of all in-scope21 criteria and explicit A acceptance with B/C.
R2 exit does not authorize R3–R6, M4 integration, production swap or release.

## 7. Exact unresolved decisions and final stop

A must decide whether to authorize resource-only PoC acquisition/provisioning and which
backend candidate; no blanket R2 authorization requested as already given. Resolve hard
memory/transient accounting and timing semantics WITHOUT relaxing original maxima.
Approve/reject proposed contracts/refinements and bounded bridge authority limitation;
if global R1 enforcement is required, authorize a separate extension proposal, not edits.
Name B/native C reviewers, approve actual manifests and freeze thresholds/fixtures.
Exact costs/sizes/licences/artifact hashes remain required before obtaining anything.

Until those decisions and proofs exist: **BLOCKED**, not implementation-ready.
Recommend review of this packet, then a separately scoped resource-only PoC decision.
STOP. No R2 implementation, image decoding, dependencies, migrations, protected workspace
access, or R3–R6 work was performed. R1 acceptance/evidence and Phase2 remain unchanged.
