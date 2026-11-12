# R2 — measurable acceptance and phase evidence register

Draft 1, 2026-11-10. PROPOSED / NOT EXECUTED / NOT AUTHORIZED.
Companions: [technical spec](R2_IMAGE_ANALYSIS_SPEC.md), [security](R2_ARCHITECTURE_AND_SECURITY.md),
[licence decisions](R2_DEPENDENCY_AND_LICENCE_MATRIX.md).
Refines, never silently replaces, Reference matrix R2-A/B/C. R1 conditional acceptance
remains unchanged; G1 new R2 report/bridge contracts and the R2 isolation gate remain open.

## Authorities, prerequisites and benchmark freeze

A = user/Nadish, phase entry/exit and scope authority. B = explicitly designated brand/
rights/design reviewer (defaults to A). C = designated Telugu/English content reviewer;
native Telugu review must actually be available, not inferred from an actor label.
An engineer reports evidence; passing tests do not authorize deployment or the next phase.

P1 = accepted R1 manual subset/conditions; P2 = reviewed exact R2 report/bridge/profile
contracts and canonical vectors; P3 = pinned licensed runtime/native/model closure;
P4 = proven hard worker boundary. No analysis fixture decode before P3/P4. Contract-only
test preparation later needs its own authorization; no fixtures are created here.

Freeze before implementation/evaluation: corpus bytes/hashes and lawful rights, source
annotations, split membership, all thresholds below, algorithm/version/profile hashes,
matching rules, exclusions, confidence definitions and evaluator source. A/B/C ratify
these proposed engineering targets; no target is a measured accuracy claim. Failed
holdout performance requires reporting failure or a separately approved design revision,
not threshold tuning on the same holdout. Publish per-fixture failures and denominators.

Proposed realistic corpus: 120 owned/rights-cleared images, 40 development and 80 heldout;
40 English, 40 Telugu, 40 mixed-script. Balance eight genres (editorial, sports, product,
cultural, event, restaurant advertising, general poster, complex collage), 15 each.
Cross-stratify clean/complex/degraded quality before splitting; publish actual counts,
not merely a random seed. Typography ground truth is manually transcribed independently
and reconciled by C, with word/line boxes and language labels. Never use OCR output as truth.

Separate analytic fixtures: S1 flat colors/alpha; S2 known ramps and false ramps;
S3 primitive boxes/grids/text baselines; S4 known blur/noise/luma transformations;
S5 adversarial/truncated/oversized PNGs and access/resource probes; S6 source/profile/
rights changes and manual corrections; S7 disconnected provisioning/runtime scenarios.
Synthetic geometry/ramps give exact truth; real-image hierarchy/design labels require
reviewer annotations and ambiguity labels, not invented objective aesthetics.

CER = scalar-character Levenshtein distance / ground-truth scalar count, with insertions
included. Evaluate NFC-normalized copies only; retain original observed/approved Unicode
unchanged. Report raw-string error too, by language and quality stratum. Missed regions
count as deletions, extra text as insertions; do not score only detected text. Clean OCR
eligibility is frozen visible printed text >=20 display px x-height, readable without
perspective distortion, with enough examples retained per language; report smaller and
degraded strata separately. Word/line matching uses one-to-one highest-IoU assignment at
IoU>=0.5, deterministic ties by annotation ID. Confidence is not OCR raw-score probability.

## Acceptance matrix

Every row requires retained fixture/profile/source hashes, exact commands/exit codes,
expected/actual results, per-case errors, limits/probes and A/B/C decisions as applicable.
"Evidence" entries below add row-specific material. Failed prerequisite = BLOCKED.

| ID / existing parent | Prerequisites | Fixtures / ground truth | Measurement | Proposed frozen threshold | Failure behavior | Required evidence | Authority |
|---|---|---|---|---|---|---|---|
| R2-I01 / R2-A import | P1/P2/P3/P4 | S5 valid/bad signature, truncation, extra payload, links/FIFO/device/archive/APNG/16-bit/interlace | Input allowlist and immutable-byte checks | Every forbidden input refused; all supported valid fixtures admitted; original SHA unchanged | No worker/result for refused input; source unchanged | Refusal stage/code, handle/source hash, 100% case list | A |
| R2-I02 / R2-B metadata | I01 | S1 PNG dimensions, alpha, profiles, orientation1–8 and absent metadata | Compare raw/display dimensions, exact ratios, modes/profile labels | Exact metadata on every analytic fixture; unsupported/conflicting profile explicit; no invented DPI | Unsupported result or specific unavailable field, no assumed conversion hidden | Expected/actual metadata and transform hash | A+B |
| R2-C01 / R2-B palette | I02 | S1 major flat regions each >=20% opaque area; transparent border and all-transparent input | One-to-one swatch match; 8-bit sRGB channel error and alpha-weighted coverage | Each major region represented within 8/channel; coverage error <=5 percentage points; all-transparent returns empty | Unreviewed/failed palette; no semantic/brand certainty | Swatches, weight counts, normalized image hash, omitted-region report | A+B |
| R2-C02 / R2-B gradients | C01 | S2 linear ramps at0/45/90/135 degrees, flat fills, checkerboard/photo-like negatives | Direction modulo180; ramp residual RMSE; false-positive count | On analytic ramps direction error<=10 degrees and channel RMSE<=8; zero gradient claims on fixed flat/checkerboard negatives | Gradient unavailable/inferred low confidence; no false measured direction | Per-fixture angles/residuals/abstentions, frozen texture gate | A+B |
| R2-C03 / R2-B contrast | C01 | S1 declared foreground/background pairs and transparent ambiguity | Relative luminance/ratio against reference arithmetic | Ratio absolute error<=0.02 on opaque exact fixtures; ambiguous pairing marked inferred/unavailable | No WCAG compliance claim; show sampled pair only | Pair regions, reference calculation, alpha policy | A+B |
| R2-T01 / R2-C text regions | I02 and OCR artifacts approved | S3 + clean heldout en/te/mixed annotated boxes | One-to-one IoU matching, precision/recall per language | Precision and recall each>=0.90 on frozen clean strata, IoU>=0.5; report all missing/extra regions | Text map not approved; manual region entry remains possible | TP/FP/FN, box matches, ignored labels decided before evaluation | A+C |
| R2-T02 / R2-C English OCR | T01 | Heldout clean English/mixed spans, C-verified transcript; >=2000 English truth scalars | CER including missed/extra regions, pooled and per-poster results | Pooled clean English CER<=0.05; no silent correction; publish distribution/degraded scores | English OCR remains experimental/unapproved; no full OCR claim | Raw OCR, truth hashes, alignments, CER/WER tables, raw scores | A+C |
| R2-T03 / R2-C Telugu OCR | T01 | Separate heldout Telugu/mixed spans; >=2000 Telugu truth scalars; native review | Same CER method, Telugu normalization/error categories reported separately | Pooled clean Telugu CER<=0.10; no English result used as substitute; approved wording byte-exact | Telugu OCR unapproved; preserve manual Telugu entry; full requested R2 exit blocked | Telugu annotations, scalar edit traces, missing signs/joins and reviewer decision | A+C |
| R2-T04 / R2-C typography | T01–T03 | S3 known baselines/sizes/alignment plus annotated real hierarchy | Line-height ratio/gap and alignment residuals; inferred hierarchy reviewed separately | Synthetic ratio error<=0.1, gap/alignment error<=2 display px; no unsupported exact font/weight/tracking claims | Return geometry only or unavailable; hierarchy stays inferred | Measurements, region overlays, provenance and unsupported-field list | A+C |
| R2-G01 / R2-B composition | I02/T01 where text used | S3 exact margins/grids/occupancy; real collages annotated ambiguous | Primitive geometry error and negative-space fraction | Analytic margins/lines error<=2 display px, empty-area fraction error<=0.03; no semantic subject/layer certainty | Abstain grid/subject interpretation if ambiguous | Exact fixture geometry, measured/inferred split, misses | A+B |
| R2-G02 / R2-C focal/hierarchy | G01 | >=30 heldout annotated nonambiguous layouts plus explicitly ambiguous examples | B's blinded region/rationale rubric: evidence supported, no invented facts, safe uncertainty | All hard factual/provenance checks pass; >=24/30 rationales supported; ambiguous fixtures abstain or clearly infer | Focal interpretation remains unapproved; geometry usable without semantic claim | Frozen rubric, independent scores/disagreements, region evidence | A+B+C |
| R2-M01 / R2-B treatment | I02 | S4 generated luma/saturation/blur/noise ramps and flat-color negatives | Luma percentiles and monotonic response of specified proxies | Luma error<=1 level on exact fixtures; declared blur/noise sequences monotonic; no high-noise claim on fixed flat negatives | Affected proxy unavailable; no physical-lighting/edit-history claim | Metric formula/profile, paired transformations, errors and exclusions | A+B |
| R2-U01 / R2-C confidence | Applicable quality rows passed | Heldout observations grouped measured/inferred, high/medium/low/not-assessed; C/B validity labels | High-label precision against frozen per-feature tolerance; coverage reported | High label only after >=30 heldout high predictions with >=0.90 correct; otherwise disable high. Never convert detector score to probability | Downgrade/disable uncalibrated label; low-confidence critical result requires correction/exclusion | Calibration counts and coverage per feature/language, false-confident examples | A+B+C |
| R2-D01 / R2-B repeatability | P2/P3 and extraction rows | Same source/profile/model hashes, 10 fresh worker runs for each analytic fixture | Compare normalized bytes, canonical pages/index; ignore separate job timing IDs | All 10 measurement payloads/hashes equal in pinned environment | Result not deterministic; no acceptance until cause/profile corrected | Full hashes, exact builds/threads/rounding, separate telemetry | A |
| R2-S01 / R2-A hard bounds | P2/P3; before other media processing | S5 each boundary-1/exact/+1, lying headers, bombs, allocations/mmap/fork/output flood | Observe enforced denial under approved OS mechanism, not just sample RSS | All table limits enforced, 1GiB aggregate/128MiB scratch; zero unauthorized read/write/network/IPC | Disable automated decoding; no weaker fallback | Enforcement config, syscall/probe outcomes, descendant and quota/OOM evidence | A |
| R2-S02 / R2-A cancel/recovery | S01 | S5 cancel during decode/extract/OCR/validate, worker crash/hang and cleanup failure | Monotonic cancellation/timeouts, process-tree count, original/HEAD hashes | Worker work<=15s, total job<=60s; descendants stopped within2s of cancel/deadline; no completed/approved partial result | Failed/canceled/quarantined job; explicit bounded retry only | Stage trace, actual process exits, retained-file report, pointer/source equality | A |
| R2-S03 / R2-A persistence failures | P2/S01 | S6 interruptions, denied writes, injectedENOSPC, real bounded write failure, stale writers | New report namespace publication/reopen and manual bridge boundary | Prior valid state or explicit recoverable draft; no orphan approval; no cross-store atomicity claim | Preserve bytes, UNCERTAIN if publication cannot be confirmed, explicit recovery | Failure positions, before/after refs, corruption evidence, recovery choice | A |
| R2-O01 / R2-C offline/runtime | P3/S01 and applicable extractors | S7 all paid/network services disabled, eng/tel files absent/changed, offline reopen | Network denial plus required artifact availability; fail-closed data loading | No network/account/charge required; missing data blocks only affected OCR, manual R1 stays usable | No fetch or silent model substitute; full OCR acceptance withheld | No-network probes, exact dependencies/notices, absent-model behavior | A |
| R2-O02 / R2-B performance | S01, frozen representative corpus | Heldout <=2048-edge accepted inputs, cold and warm groups on M4Pro/24GB | End-to-end wall time and enforced resource telemetry | p95<=10s separately cold/warm; every worker<=15s and job<=60s; resource maxima never exceeded | Do not relax bounds; mark unsupported/failed job and review design | All timings, quantiles, workload/background conditions, peak evidence | A |
| R2-R01 / R2-C R1 bridge | P1/P2; report review and rights cleared | S6 correction/exclusion/reanalysis, stale profile, adverse brand/rights, samebatch Finding chains | Hash/pin/provenance and approval transitions; unchanged R1 validator | No automatic measured->user-entered relabel; only explicit manual choice; originals/corrections retained; stale/adverse dependencies block; no approval transfer | No bridge approval, preserve old Recipe; incompatible native import refused | New sidecar schemas/vectors, original/R1 source hashes, event/selection traces | A+B+C |
| R2-R02 / R2-A protected baseline | All rows and release candidate scoped | Accepted R1 source/evidence/acceptance record, creative@1 and protected manifests | Pre/post hashes and OS write boundary; no external workspace access needed | Zero protected changes; all outputs only fresh authorized directories; no R3–R6/M4 code paths | Stop, investigate and restore only by separately authorized procedure | Baseline manifest, artifact diff, command/source/policy hashes | A |

The numerical OCR/design thresholds are proposed measurable engineering goals, not
claims derived from unrun benchmarks. Coverage, denominator floors and fixture partitions
prevent passing by emitting nothing or evaluating only easy detected regions. Optional
suggestions can abstain, but mandatory OCR/color/security rows cannot be waived silently.

## Exit and review gates

Full R2 acceptance requires every in-scope row passed, retained fresh immutable evidence,
documented rights/dependency closure, independent read-only review and A's explicit exit
decision with B/C reviews. A color-only or security-only slice is not full R2 acceptance.
R2-A maps to I01/S01–03/R02; R2-B to I02/C01–03/G01/M01/D01/O02;
R2-C to T01–04/G02/U01/O01/R01. No G2 canvas or M4 prerequisite is invented; R3 requires
its own operations/application contracts and later authorization.

G7 clean offline install/rebuild/recovery and distribution clearance remain separate
open requirements; network-denied runtime is not that evidence. Physical power-loss
durability is not inferred from injected faults. No tests or datasets were generated
or evaluated during this documentation task. No R2 implementation is authorized.
