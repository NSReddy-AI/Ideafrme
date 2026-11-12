# R2 architecture decision record — containment unresolved

Date: 2026-11-10 (America/Toronto). Status: documentation closure and proposed planning
baseline only. Authority: the user's documentation-only authorization in this conversation.
**R2 implementation, provisioning and experiments remain NO-GO.** No backend is qualified.

## 1. Scope and precedence

This record closes the architecture review's documentation conditions. It does not
close security, conformance, licensing, evaluation or implementation acceptance gates.
Read with [safe roadmap](R2_SAFE_DEVELOPMENT_ROADMAP.md) and
[next authorization matrix](R2_NEXT_AUTHORIZATION_MATRIX.md).

Preserve the substantive contracts in [report proposal](R2_REPORT_CONTRACT_PROPOSAL.md),
[bridge proposal](R2_R1_BRIDGE_CONTRACT_PROPOSAL.md) and
[canonical vectors](R2_CANONICAL_VECTOR_SPEC.md). Their bounded design is provisionally
acceptable following the separate review and user scope decisions; executable conformance,
recovery and integration are not accepted. Earlier draft headers remain historical.
The precise report proposal's closed grammar/refinements take precedence over the
earlier informal shapes in R2_IMAGE_ANALYSIS_SPEC.md; no new schema is introduced here.

This record explicitly supersedes these planning recommendations, without editing their
historical text or weakening their limits:

- R2_ARCHITECTURE_AND_SECURITY.md section 4: native macOS as the preferred next candidate.
- R2_SECURITY_GATE_DECISION.md sections 3 and 5: preferred VM design and resource-only
  PoC execution as a proposed next step.
- R2_IMPLEMENTATION_READINESS_ROADMAP.md sections 3 and 7: PoC provisioning/execution
  packets as the immediate next action. Sections 4–6 remain historical, conditional
  R2-A/B/C scope proposals, not authorization.
- R2_IMAGE_ANALYSIS_SPEC.md section 6: any reading of the future sequence as permission
  to run an isolation experiment or decode fixtures now.

The safe roadmap separates possible future contract-only work from those blocked steps.
No older recommendation authorizes acquisition, compilation, signing, launch or probes.

## 2. Stable gates and present status

Gate names are not renumbered. Universal G1–G7, Reference R1–R6, R2-A/B/C delivery
stages, and reviewer roles A/B/C are different namespaces from these gate letters.

| Gate | Meaning | Current status |
|---|---|---|
| A | Security/resource containment | BLOCKED; no qualified processing backend |
| B | Contracts/Bridge | Provisionally acceptable bounded design; conformance, recovery and bridge implementation evidence pending |
| C | Dependencies/Licensing | BLOCKED for processing adoption/distribution; actual closure unqualified |
| D | Evaluation | UNVERIFIED; lawful image fixtures, annotations and measurements not frozen/proven |

Integration is a separate authorization decision, not a newly substituted Gate E.
Passing a contract-only slice would not pass Gate A, full Gate B, R2-A or full R2.

## 3. Target and architectural decision

Target: user's 14-inch November 2024 MacBook Pro, Apple M4 Pro ARM64, 24 GB unified
memory, macOS Tahoe 26.6.2; approximately 700 GB available storage is a reported capacity,
not a quota, security guarantee or reserved allocation. Future evidence must record
actual versions/hardware/storage at execution time. No new hardware benchmark ran.

Use two independently bounded planes:

- Trusted control plane: rights and input admission, scheduling, policy configuration,
  bounded output validation, immutable publication/recovery, human review and bridge
  authority. It must not decode hostile images, invoke OCR, render hostile previews or
  interpret reference content as instructions. Byte identity/size admission is not decoding.
- Untrusted processing plane: replaceable backend for PNG decoding/normalization,
  extraction and English/Telugu OCR. These are conceptual stages, not separately approved
  processes. They share one aggregate job budget and possess no R1, brand or project-store
  authority. Stages remain disabled until containment is independently qualified.

CPU-only initial processing; no worker GPU/Metal devices, queues or buffers. Future GPU
support requires a separate accounting/security proposal, not a performance toggle.
Prefer ARM64 and serial bounded work only after feasibility; capacity does not prove safety.
The backend interface may be planned but is not implemented or selected by this record.

Native App Sandbox/XPC and the investigated fixed-memory Linux VM are **unqualified
historical candidates**, not defaults or approved implementations. Native investigation
is stopped. The VM remains a historical research preference only; no renewed native/VM
investigation is commissioned. No cloud service is an essential fallback. Alternative
containment needs a separately authorized decision, not another generic PoC cycle.

## 4. Unchanged resource and input contract

| Quantity | Binding maximum / restriction |
|---|---|
| Input | One PNG, 10 MiB = 10,485,760 encoded bytes; existing 8-bit, single-frame/noninterlaced allowlist unchanged |
| Source geometry | 8192 pixels per edge and 16,777,216 pixels total |
| Normalized analysis | Maximum edge 2048 pixels |
| Aggregate untrusted memory | 1 GiB = 1,073,741,824 bytes |
| Aggregate worker scratch | 128 MiB = 134,217,728 bytes |
| Worker processing | 15 seconds total wall time across decode, extraction and both OCR languages |
| Complete job | 60 seconds including setup, validation, cancellation and cleanup |
| Concurrent jobs | One |
| Worker processes | At most four across the entire job |
| Threads | Serial stages; one compute thread where configurable, as in existing specs; no uncontrolled pools; separately enforced total thread bound still requires qualification |
| Result | 1 MiB aggregate canonical envelopes including Index, at most 32 pages |
| Result density | 64 observations, 512 OCR words, 16,384 OCR scalars; 8 observations or 32 words per page |
| Deployment | 256 MiB compressed complete mandatory deployment closure; no exclusion of guest/runtime/models/notices to appear compliant |

Existing depth/member/string/history bounds in the report contract remain unchanged.
One configured compute thread is not an OS-enforced total-thread quota; do not invent
a larger total or treat configuration as proof. Failure to qualify a bound stays blocked.

Memory includes descendants, shared allocations counted once, native/CMS/OCR allocations,
memory-backed scratch and worker-attributable host transport/device/output allocations.
Trusted supervisor overhead is measured separately; worker-induced buffers cannot be
exempted merely because their allocator is trusted. For a future VM, guest memory plus
additional attributable host allocations must remain within 1 GiB without double-counting.
A smaller guest is not sufficient without a defensible upper bound on the second term.

Scratch includes all worker-controlled writable sinks, including alternate temporary
locations, memory-backed files, open-deleted files and bounded host-side output. Scratch
in RAM also counts against memory. Trusted persistent review history is separate, with
its existing graph/size bounds; it cannot be used as a spill route for worker output.
No polling, sampled RSS, delayed termination or best-effort quota is a hard-bound proof.

The existing two-second descendant-termination confirmation target is verification
latency, not two extra seconds of processing after the 15-second deadline. Scheduling,
kill and cleanup guarantees remain proof obligations. Cold/warm p95 <=10 seconds remains
an unmeasured evaluation target, not a replacement for either hard deadline.

## 5. R1, review and compatibility invariants

R1 remains [conditionally accepted](M5_R1_ACCEPTANCE_RECORD.md) in its reviewed manual
CLI/library scope. Preserve creative@1, Phase 1/2, R1 source/schema/store/evidence, M4 and
production. No silent migration, historical rewrite, automatic Apply or approval transfer.

Every future R2-backed workflow must check current R2 AND R1 eligibility, exact generations,
rights/dependencies and explicit actor confirmation. Uncertain checks fail closed.
Standalone R1 remains a separate manual workflow: it does not automatically discover later
R2 revocations. Explicit R1 dependency events remain necessary; failed propagation blocks
R2 consumers and must be reported, never described as synchronous global enforcement.
There is no cross-store atomic transaction or authenticated multi-user authority.

R1 manual-style-authoring rights do not establish reference-analysis permission. Partial,
stale, excluded, revoked or unreviewed reports cannot bridge. Measured/inferred evidence
never becomes an automatic user-entered Finding. Bridge execution is out of the safe track.

Worker output and worker resource claims remain untrusted. A syntactically valid report,
an approved human correction, a synthetic resource manifest, or successful contract tests
cannot establish that actual decoding occurred within a qualified boundary.

## 6. Open conditions and stop

Gate A's attributable-memory, writable-sink, lifecycle and thread enforcement remain
unresolved. Gate C retains exact artifact/ABI/license/source/build closure and signing
qualification gaps. Retained build sources/toolchains are separately declared under the
existing artifact plan, not silently omitted or asserted distributable. Gate D retains
lawful image/annotation/profile/reviewer and measured quality/performance gaps.
R1 physical power-loss and clean offline rebuild/distribution conditions stay open.

Follow [engineering policy](../PROJECT_ENGINEERING_POLICY.md) and
[offline strategy](../OFFLINE_BUILD_STRATEGY.md): reuse suitable existing components first,
separate code/model/font rights, retain permitted closure, no mandatory account/payment/
network service, and no shared environment changes. No dependency is adopted here.

**STOP: documentation only. No R2 code, test execution, media processing, containment
experiment, provisioning, R3–R6, M4 integration or production action is authorized.**
