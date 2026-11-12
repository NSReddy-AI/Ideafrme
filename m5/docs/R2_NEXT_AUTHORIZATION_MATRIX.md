# R2 next-authorization decision matrix

Date: 2026-11-10. Documentation only. This matrix grants no implementation, testing,
acquisition, provisioning or integration permission. Read the
[decision record](R2_ARCHITECTURE_DECISION_RECORD.md) and
[safe roadmap](R2_SAFE_DEVELOPMENT_ROADMAP.md) for exact boundaries.

Gate A=Security; B=Contracts/Bridge; C=Dependencies/Licensing; D=Evaluation. Reviewer
roles A/B/C in older documents are not gate identifiers. User approval is required
for each scoped start and later acceptance; engineer test results cannot grant either.

## 1. Workstream decisions

| Workstream | Independent of Gate A? / present status | Required authorization and prerequisites | R1 / M4 / production risk | Acceptance evidence | Rollback / failure expectation |
|---|---|---|---|---|---|
| Track 1: pure synthetic schemas, IDs, closure and review/job state | Yes, only trusted bounded fixtures; proposed, NOT authorized | Explicit Track 1 implementation approval; frozen contracts/APIs/fixtures; existing runtime identity and scoped license check | R1 risk: imports/format registration or false authority leakage; forbid both. No M4/production access | Two-reader byte/hash and semantic agreement; positive/negative/boundary matrix; synthetic labels; unchanged accepted hashes | Disable new synthetic route; retain immutable fixtures/evidence; no automatic operational promotion |
| Track 1: synthetic persistence and recovery | Yes for trusted test writer, not hostile media; proposed, NOT authorized | Separately explicit write/fault/child-process scope within Track 1; fresh root and verified runner confinement; supported filesystem assumptions | R1 risk: accidental store reuse/evidence overwrite; separate namespace. No protected workspace probes | Commit/reopen/order and failure-point evidence; expected-HEAD conflicts; PREVIOUS preservation; UNCERTAIN behavior; bounded injected ENOSPC/process exits | Preserve last valid pointer and damaged evidence; explicit recovery; no destructive disk/power tests or data deletion |
| Track 1: synthetic bridge preconditions | Yes for in-memory stubs only; operational bridge excluded | Explicit inclusion in Track 1 tests; no R1 store writes, new Findings, real project association or authority calls | False approval/current-eligibility claims are principal R1 risk; stub cannot authorize real use | Rejected partial/stale/revoked/unknown-rights cases and unchanged R1 compatibility; simulation clearly labelled | Discard uncommitted simulation state; keep evidence; no cross-store rollback claim |
| Track 2: review existing Phase 2 draft outputs | Yes; visual/Telugu acceptance remains open | Separate human review scope; no rerendering/decoding experiment or source edits | No R1/M4/production changes; do not approve new content on user's behalf | Exact existing-output identity and actual English/Telugu reviewer findings; acceptance remains user's decision | Keep outputs unchanged; record unresolved visual failures; no automatic fixes |
| Track 2: manual briefs, brand metadata, supported forms/layout drafts | Yes within roadmap exclusions; new proposed features | Per-feature contract/file/API proposal and user implementation approval; appropriate universal G1/G2/G3 requirements; scoped dependency review | Existing core/R1 mutation, schema bypass, hidden Apply and accidental rendering; forbid each. No M4/production integration | Synthetic text/geometry, reversible drafts, fail-closed hard rules, historical approval preservation, public-API compatibility | Disable new route; retain prior project/profile revisions; no silent migration or overwrite |
| Track 3: PNG decoding, normalization, OCR, image analysis, previews | No; BLOCKED | Qualified Gate A plus relevant B/C/D evidence and separate R2-A/B/C approval; exact approved artifacts/fixtures | Compromised native processing could access protected data; no fallback through accepted renderer/R1 | Full unchanged hard-bound/access/lifecycle proof, actual quality/performance evidence and independent review | No launch while blocked; later failure quarantines result, disables backend and preserves evidence; no weaker fallback |
| Track 3: actual media report review/manual R1 bridge | No operational path now; BLOCKED despite provisional contract design | Accepted actual report provenance, current R2/R1/rights checks, scoped bridge approval, new conformance evidence | Stale eligibility, partial cross-store failure, provenance loss; standalone R1 cannot auto-follow R2 | Explicit human selections, no approval transfer, generation checks, receipts and adverse-event failure evidence | Preserve durable draft refs; withhold completion on uncertainty; block R2 consumers when propagation fails; never pretend committed R1 data rolled back |
| Track 4: specific alternative containment / explicit requirement decision | Research could be read-only; NOT currently commissioned | Separate finite design authorization; no generic restart of native/VM work; no execution permission | Scope creep into provisioning or changed budgets; preserve all protected milestones | Specific supported mechanisms and complete accounting argument, finite go/no-go with remaining proof obligations | Reject infeasible candidate; retain original limits unless user separately approves a justified revision |
| Acquisition, signing, compilation, VM/probe execution | No permission; BLOCKED | Exact per-artifact/command/write/license approval after credible design; no installs to shared environments | External writes, paid prerequisites and protected workspace exposure | Artifact identities, bounded execution policy and independent experiment review | No action now; later stop/quarantine on policy failure, no automatic cleanup of retained evidence |
| R3–R6, M4 integration, production/release | Outside all safe tracks; unauthorized | Separate milestone approval; G5 requires accepted M4 baseline and compatibility plan; distribution G7 remains separate | Direct protected-milestone risk | Milestone-specific acceptance, isolation/regression and release closure | No integration or swap; preserve current baselines |

## 2. Approval gates for a possible Track 1 request

1. User chooses the exact contract-only scope. The roadmap's file allowlist is a proposal,
   not permission to create its files; resolve existing-path collisions before approval.
2. Freeze requirement-to-fixture-to-test/reader mapping, signatures, source/runtime hashes,
   synthetic evidence ownership, error outcomes and bounded write/child-process scope.
   No code, tests, fixtures or runner execution is authorized by this documentation task.
3. Only after implementation authorization, create named new files and run approved tests
   in a fresh `.runtime/r2-contracts/<run-id>/` root. Never overwrite old evidence or run a
   legacy fixed-path runner without demonstrated isolation.
4. Return independent conformance/failure evidence and unchanged protected hashes. Test
   counts and pass results must be observed, not inferred from old R1 runs or ten vectors.
5. User separately accepts or rejects the synthetic milestone. Gate A, operational bridge,
   image evaluation, clean offline rebuild and full R2 remain unaccepted regardless.

## 3. Cross-cutting conditions

- Use only existing compatible, identified tools after scoped review; no installs,
  downloads, model/font acquisition, network resolution or mandatory paid services.
- No accepted R1/creative@1/Phase 1/2 source or old evidence changes. Manual features must
  not become R3 style application or real project association under another name.
- Synthetic state-machine completion is not real analysis. Test resource/rights stubs
  cannot be accepted as operational security/rights evidence. No decoder in trusted code.
- Keep 1 GiB aggregate memory, 128 MiB scratch, 15s/60s deadlines, four-process maximum,
  one configured compute thread/serial stages and all remaining input/output limits.
  Actual enforcement is still unqualified; contract validation is not enforcement proof.
- Physical power-loss durability, R1 security limitations and independent offline
  build/distribution closure remain open. Track 1 may not silently claim to close them.
- Complete mandatory deployment closure must meet 256 MiB compressed; retained build
  sources/toolchains remain separately declared and legally qualified per existing policy.
  A contract-only stdlib milestone does not establish full processing distribution fit.

**STOP: only these three documentation deliverables are authorized now. No implementation,
tests, processing, probes, provisioning, R2-A, R3–R6 or protected-workspace actions follow.**
