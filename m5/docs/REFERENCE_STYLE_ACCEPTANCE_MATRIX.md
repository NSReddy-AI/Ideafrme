# Reference Style Studio — phase traceability and acceptance register

Revision 2, 2026-11-10. DOCUMENTATION ONLY; DESIGN VERIFICATION PENDING.
All R1–R6 implementation is NOT AUTHORIZED. This register defines future evidence,
not completed tests. No fixtures, dependencies or implementation are created by it.
Normative companion: REFERENCE_STYLE_STUDIO_SPEC.md, sections 12–16.

## Reading and authority

Each criterion has an ID, prerequisite, named synthetic/annotated fixture, measurable
pass evidence, failure outcome and approval authority. "Pass" always requires retained
commands/results, exact source/tool/fixture hashes and limitations. No fixture is an
unapproved download or copied private project. Preparing fixtures needs phase approval.

A = Nadish/the user: explicit phase entry/exit and implementation authority. Automated
checks/engineers report evidence but cannot grant A approval. B = brand/rights reviewer
explicitly designated by A; until delegation, A holds that role. C = content/native
language reviewer explicitly designated by A; until delegation, A holds that role.
Approval of one criterion is not permission to execute the next phase.

Universal gate references use UNIVERSAL_CREATIVE_STUDIO_SPEC.md section 12:
G1 contracts; G2 canvas editing; G3 concept planning; G4 integrated application; G5
accepted-M4 engine adapter. G7 is the independent-distribution/rebuild gate, not a
substitute for per-phase offline runtime/resource evidence. No gate is presumed passed.

## Explicit dependency map (no implicit milestones)

- R1: approved G1 recipe/brand/dependency contracts. Structured form only, no G2 canvas,
  G3 model, G4 app integration or G5/M4 dependency.
- R2: R1 exit plus G1 import/result contracts and accepted isolation proof. No G2–G5/M4.
- R3: R2 exit plus G1 atomic transaction/provenance contract. Editor-entry tests require
  G2; a separately scoped structured preview can run without G2. No implicit G3–G5/M4.
- R4: R3 exit; G3 only for automatic concepts, G4 only for full three-entry integration.
  Manual core mixing is separately testable without G3/G4; no G5/M4 required.
- R5-A/B: R4 exit and G1 media/timebase contracts. Analysis ONLY, independent of M4.
  R5-C: additionally accepted G5, full M4 acceptance, exact approved baseline and source
  manifest. Never run M4 scripts merely to complete R5-A/B.
- R6: R1–R5 ANALYSIS exit plus approved model task/license/resource contract; require
  G2/G3/G4/G5 only for functionality touching those integrations. G5/M4 is mandatory for
  actual reel production, not an invented prerequisite for every model experiment.

No R phase is a prerequisite for the G1 contracts that it consumes. G2/G3/G4 do not
require the completed Reference Studio. This separation avoids circular entry gates.

## R1 — structured manual recipes (not canvas editing)

G1 concrete draft inputs for R1-A/B/C:
[record contracts](G1_STYLE_RECORD_CONTRACTS.md),
[canonical vectors](G1_CANONICAL_TEST_VECTORS.md),
[persistence protocol](G1_PERSISTENCE_PROTOCOL.md). Draft availability does not meet
the approved-G1 prerequisite. Separate read-only verification and A acceptance remain.

| ID | Prerequisite | Fixture | Required pass evidence | Failure outcome | Authority |
|---|---|---|---|---|---|
| R1-A | Approved G1 schema/canonicalization/dependency manifest | F1 valid manual recipes; older/newer schemas; malformed/duplicate-key records | All supported fixtures validate and save/reopen with equal canonical payloads and pinned references; all invalid/unsupported editing requests refused; independently written serializers in two languages agree on canonical bytes/hashes and strict invalid-input rejection; no creative@1 changes | Refuse record without rewriting original; R1 exit blocked | A |
| R1-B | R1-A contract; protection and reviewer-role definitions | F2 approved recipe, library update, project snapshot, conflicting hard rules | Editing creates a new revision; approved bytes/hash unchanged; project never follows latest; all hard-rule conflicts blocked; manual user-entered finding keeps independent origin/review/availability axes; revoke, correction, resource change and rights expiry/revocation transitively block affected recipes; restoration requires fresh ordered reviews; missing/out-of-scope/unknown rights deny approval | Keep prior revision; mark conflicting draft unresolved; no approval | A + B |
| R1-C | Atomic save/locking/review-event protocol specified | F3 staged interruption, disk-full, denied write, stale writer, missing dependency, corrupt file | Every failure preserves last valid data or explicit recoverable draft; no false approved revision; concurrent writer cannot overwrite; stale normal/recovery generations refused; recovery preserves PREVIOUS at every Q transition and requires exact-generation user choice; reference/source bytes unchanged; real filesystem qualification and fault evidence required, not inferred from document checks | Preserve originals; quarantine invalid staging; block approval/apply and report failure stage | A |

R1-B is manual-only. Measured/inferred finding acceptance belongs to R2-C after R2
prerequisites; it is not an R1 import/edit exception. R1-A cross-language agreement and
R1-C real failure/durability evidence are future implementation exit requirements.

## R2 — bounded deterministic image analysis

| ID | Prerequisite | Fixture | Required pass evidence | Failure outcome | Authority |
|---|---|---|---|---|---|
| R2-A | R1 exit; G1 input contract; section 15 OS/worker envelope approved | F4 malformed PNG/signature mismatch, bomb/oversize, links/device/FIFO/remote input, forged result; external read/write/network probes | Every forbidden input/action denied; no unauthorized access; enforced encoded/pixel/memory/output/deadline bounds; cancellation/crash stops descendants; limits not inferred solely from sampling | Do not enable automated analysis; no weakened sandbox; original inputs untouched; quarantine failed job | A |
| R2-B | R2-A; approved tool/configuration/hash and color/orientation policy | F5 PNG flat-color regions, transparent border, known dimensions; each tested color covers at least 20% of opaque pixels | Every major region represented by a returned swatch within 8/channel in normalized 8-bit sRGB; estimated coverage within 5 percentage points; exact dimensions/orientation; repeated pinned runs equal; sampling/omissions reported | Findings stay failed/unreviewed; no claim of semantic palette understanding; correct method or explicitly revise design before reevaluation | A + B |
| R2-C | R2-A/B; independent finding axes defined | F6 ambiguous type/lighting, human correction, model absent, canceled job, changed source hash | Measured and inferred findings can each be independently approved/revoked without changing origin; both axes and original evidence retained; measurements and inference labeled separately; corrections/original evidence survive reanalysis; changed hash marks affected findings stale; manual R1 remains usable with IP networking denied; no font-ID certainty invented | Keep manual recipe; block affected approval; no silent fallback or partial approved result | A + C |

R2-B tolerances apply to the synthetic deterministic palette benchmark, not a claim of
universal aesthetic quality. Set other task-specific thresholds BEFORE any corresponding
test; unresolved metrics cannot be marked passed or tuned after viewing a failed holdout.

## R3 — selective poster application

| ID | Prerequisite | Fixture | Required pass evidence | Failure outcome | Authority |
|---|---|---|---|---|---|
| R3-A | R2 exit; accepted G1 atomic operation/provenance contract; G2 only if editor selection used | F7 manual recipe with font/color/layout changes, locked logo/photo/text, stale preview | Only chosen supported properties/targets change; every change traces to pinned recipe; locks/brand/rights all pass; stale preconditions refuse Apply; no partial commit on injected operation failure | Leave project unchanged; explain blocked targets; regenerate draft preview | A + B |
| R3-B | R3-A; canonical content equality/approval rules specified | F8 apply/undo/redo/save/reopen cycle and interrupted transaction | Canonical creative payload/bindings/pinned references restore exactly; named approved recipes unchanged; revision/audit counters follow contract; affected approvals stay invalid until reviewed | No successful application/export; explicit recovery; no restoration of stale approval | A |
| R3-C | R3-A/B; accepted renderer/font profile; G2 required for editor-preview route | F9 reviewed Telugu/English poster and missing/changed font/profile | Exact approved text; no overflow or line collision; correct pinned fonts; zero protected-asset changes; decoded repeat pixels equal under pinned environment; human appearance review recorded | No final export; preserve draft and require font/layout/profile correction and review | A + B + C |

## R4 — multi-reference mixing and portable recipes

| ID | Prerequisite | Fixture | Required pass evidence | Failure outcome | Authority |
|---|---|---|---|---|---|
| R4-A | R3 exit; source-assignment/conflict contract; G3 only for automatic concepts | F10 three sources: A lighting, B type, brand palette; equal-rank soft conflict and hard-rule conflict | Every property traces to chosen source(s)/weights; no incompatible averaging; all hard rules jointly pass; unresolved equal-rank conflicts prompt choice/exclusion; locked bytes unchanged | No Apply for unresolved proposal; keep prior approved recipe and project | A + B |
| R4-B | R4-A; licensing/export/dependency rules; G4 only for full integrated three-entry UI | F11 portable recipe with permitted media, restricted thumbnails/fonts, missing source and hash mismatch | Export includes only permitted bytes and notices; import preserves recipe/revision/hash; omitted resources explicitly listed; no substitution/training; snapshot remains stable after library update | Reject mismatched import; missing dependencies block affected use, not historical identity; no restricted bytes exported | A + B |
| R4-C | R4-A/B; comparison/selection scope defined; G4 for Create/Brand/Editor integration claim | F12 selected-layer and whole-view applications from each enabled entry | Same service/recipe semantics; Compare identifies used/excluded/blocked dimensions; scope explicit; Apply/Discard and cancellation lose no edits; no assertion of legal clearance from similarity score | Block affected route; integrated G4 claim withheld; preserve manual core workflow | A + B |

## R5 — video analysis, then separately gated production

| ID | Prerequisite | Fixture | Required pass evidence | Failure outcome | Authority |
|---|---|---|---|---|---|
| R5-A | R4 exit; approved G1 media allowlist/timebase contract; section 15 limits and audited decoder | F13 malformed/oversized/video-bomb/remote clips, variable frame rate, timeout/cancel | Correct bounded stream metadata/timestamps; no forced constant-frame assumption; all limits/access denials enforced; no whole-clip frame buffering; source unchanged | Reject/stop job and descendants; preserve labeled manual observations only; no M4 execution | A |
| R5-B | R5-A; frozen detector configuration and heldout annotations | F14 owned synthetic hard cuts, fades, no-cut movement and digital zoom | Cut precision and recall each >=0.90; matched cut error <=2 decoded frames; >=90% annotated fades have start/end error <=0.25 s; zero invented certain camera-production explanations; manual corrections survive | Detector findings remain unapproved; report errors; no motion-application permission | A + C |
| R5-C | R5-A/B and R4; accepted G5 + full M4 acceptance + exact baseline/source manifest | F15 poster->reel, reel->poster, reel->reel and poster->poster mappings | Source project immutable; separate target version; unsupported motion/audio excluded from stills only by reviewed plan; chosen-frame provenance retained; each output independently approved; accepted reel_002 regression unchanged in isolated jobs | No integration/final output; keep source/old outputs; no production swap; rollback isolated candidate | A + B + C |

R5-B matching uses one-to-one annotated boundaries, without double-counting detections.
Freeze annotations, matching window and detector threshold before evaluation. Report
full confusion/error counts, not just averages. R5-C is separately authorized even if
analysis-only R5-A/B pass. Video analysis does not grant reuse of footage or audio.

## R6 — optional local models, not a prerequisite for deterministic work

| ID | Prerequisite | Fixture | Required pass evidence | Failure outcome | Authority |
|---|---|---|---|---|---|
| R6-A | R1–R5 analysis exit; approved task/model-specific envelope, code/weight/tokenizer/native audit and acquisition manifest | F16 model closure with missing/restricted artifact, no-account offline install/runtime, absent model | All essential artifacts/version/hash/notices and legal retention rights accounted for; independently declared install/rebuild gaps remain visible; no unapproved model acquisition or implicit runtime fetch | Candidate unapproved; acquire nothing; deterministic/manual workflow stays usable | A |
| R6-B | R6-A; frozen heldout rubric/resource limits; relevant G2/G3/G4/G5 integrations accepted before use | F17 >=20 rights-cleared heldout examples spanning Telugu/English and ambiguous evidence | All hard invariants pass; >=80% task suggestions judged useful by designated reviewer under frozen rubric; uncertainty/factual error counts reported; no unsupported exact-font/legal/camera certainty; enforced task-specific memory/time limits met on 24 GB Mac | Model stays optional/unapproved for task; retain manual/rule-based path; no benchmark retuning on holdout | A + B + C |
| R6-C | R6-A/B; dependency migration and fallback policy; G7 required for independent release claim | F18 model/tool update, upstream unavailable, invalid result, timeout, clean retained-closure restore | New version gets separate findings/approval; old revisions not reinterpreted; invalid model ops rejected atomically; offline/manual workflow passes; actual clean install/rebuild/recovery evidence required for G7 claim | Refuse upgrade/application or independence claim; keep last accepted lawful version/fallback; no silent download | A |

R6 model budgets/rubric must be concretely approved BEFORE R6-A entry; they cannot be
left unspecified in an implementation authorization. The absence of a selected model
currently blocks R6, not R1–R5. No model quality or fit is established by these targets.

## Shared evidence, failure and exit rules

For EVERY row, evidence includes criterion ID, prerequisite approvals, fixture hashes,
exact commands/tool versions/configuration, expected/actual results, source immutability,
resource/isolation results where relevant, dependency closure gaps and reviewer decision.
Any failed prerequisite means BLOCKED, not skipped/pass. A criterion can be excluded
only by a user-approved scope revision that explicitly removes the corresponding feature.

Phase exit requires all in-scope rows passed AND A's explicit acceptance, with B/C review
where listed. User acceptance never overrides license/rights constraints or turns absent
test evidence into a pass. It does not authorize the following phase. A new dependency,
schema/property or resource-envelope change reopens affected contracts/criteria.

R1–R6 all preserve creative@1 and existing M5 code unless a future explicit authorization
names a separate change. M4/production remain protected. Even R5-C tests run only in
authorized isolated jobs; production merge/release is a separate decision.

Historical reproducibility: every phase that approves a recipe/output retains its
exact recipe/dependency/render identity and reports unavailable closure honestly. Full
offline build/recovery acceptance is additionally G7 under OFFLINE_BUILD_STRATEGY.md.

## Review-finding traceability

1. Phase-specific acceptance: all R*-* rows and shared exit rules.
2. Gate dependencies: explicit map plus each row's prerequisite field.
3. Persistence/dependency invalidation: spec sections 13–14; R1-A/B/C, R4-B, R6-C.
4. Independent finding axes: spec section 6; R1-B and R2-C.
5. Conjunctive hard rules: spec sections 3–4; R1-B, R3-A and R4-A.
6. Cross-format contracts: spec section 9; R5-C, with analysis/production split.
7. Failure/recovery and content equality: spec sections 8, 13 and 15; R1-C, R3-B,
   R2-A/C, R5-A and R6-C.
Additional requirements: matrix fields in every row; migration/reproducibility section
14 and G7 references; dedicated untrusted-input boundary section 15 and R2-A/R5-A.

Current status for every row: NOT EXECUTED / NOT AUTHORIZED. Documentation correction
does not approve its own design; a separate read-only verification is the next action.
