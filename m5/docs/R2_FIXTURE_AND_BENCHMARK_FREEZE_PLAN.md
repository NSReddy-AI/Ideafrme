# R2 Gate D — fixture and measurement freeze plan

2026-11-10. NO fixtures, annotations, decoding, tests or measurements created/run.
Gate D **UNVERIFIED**. The21 proposed criteria remain targets, not achieved accuracy.
Read [existing matrix](R2_ACCEPTANCE_MATRIX.md), [report contract](R2_REPORT_CONTRACT_PROPOSAL.md),
[roadmap](R2_IMPLEMENTATION_READINESS_ROADMAP.md). Any refinement here requires A/B/C
ratification; it does not silently rewrite thresholds in earlier documents.

## 1. What can be specified now

Retain120 lawful images,40 development/80 heldout,40 English/40 Telugu/40 mixed,
eight genres15 each. Exact split/annotation membership cannot be frozen before files,
rights and reviewers exist. Treat this as a pilot evaluation, not universal accuracy.

Proposed INTEGER target margins:

| Script | Total clean/complex/degraded | Development clean/complex/degraded | Heldout clean/complex/degraded |
|---|---|---|---|
| English |16/16/8|6/5/3 (14)|10/11/5 (26)|
| Telugu |16/16/8|5/5/3 (13)|11/11/5 (27)|
| Mixed |16/16/8|5/6/2 (13)|11/10/6 (27)|
| Total |48/48/24 (120)|16/16/8 (40)|32/32/16 (80)|

Genre margins: editorial, sports, product, cultural, event, restaurant advertising,
general poster and collage:15 each,5 development/10 heldout. Do not claim a fully
crossed script x genre x quality factorial: cells would be too sparse. Future curators
must provide the actual integer joint table and expose sparse/empty cells before freeze.
No duplicates, near-duplicates, template families, font/asset render variants or same
campaign split across development/holdout. Assign source/template-family clusters first,
then stratify; publish hashes/cluster/split IDs, not merely random seed.

Divide40 development images into20 tuning and20 calibration (family-disjoint); use
80 holdout only after thresholds/profile are frozen. Further fitting after viewing
holdout invalidates that holdout for acceptance and requires a fresh approved split.
At least10 clean posters containing English and10 containing Telugu, independently
transcribed, must survive in heldout, plus>=2000 ground-truth scalars each. Mixed spans
count in their script stratum and total, never as extra independent posters.

## 2. Ground truth and OCR scoring

C must include an actually available native Telugu reviewer and an English reviewer;
two independent transcriptions reconciled without viewing engine output. B/design
reviewer separately labels geometry, region applicability and ambiguous hierarchy.
Retain disagreements/adjudication and source rights. Annotators cannot invent a font,
lighting rig, semantic subject or editable layer from raster evidence.

The earlier "20px x-height" is not script-neutral. Proposed operational refinement:
clean eligibility uses median visible glyph-body height >=20 DISPLAY pixels measured
on adjudicated line crops, excluding ascender/descender extremes where identifiable;
Telugu reviewer defines body/combining-mark handling with examples BEFORE evaluation.
If this cannot be consistently annotated, that clean subset is UNFROZEN, not discarded
after OCR failure. Retain all degraded/small-text cases and report their separate errors.

CER: Levenshtein scalar edits / truth scalar count, with substitutions/deletions/
insertions all included, no rounding before pooling. Evaluate NFC copies only; original
Unicode unchanged. Freeze line/reading order by adjudicated regions. Collapse runs of
whitespace to one ASCII space, trim line edges, preserve punctuation/case/digits and
Telugu marks in the PRIMARY score. Also report raw unnormalized errors and case/spacing
diagnostics; never silently delete hard characters. Empty truth contributes insertion
counts but no fabricated zero denominator; show false text on blank fixtures separately.
Missing regions count as deletions, spurious text as insertions, including timeouts.

Mixed-script spans are annotated before OCR. Align full poster in frozen reading order,
attribute deletions/substitutions to truth span, insertions to adjacent annotated span
(tie goes to preceding span), leading insertions to first span; show ambiguous assignments
separately. Report mixed overall and per-script errors to prevent English masking Telugu.
One-to-one highest-IoU box matching atIoU>=0.5, deterministic annotation-ID ties;
publish misses/extra boxes and matching ambiguity. Do not score only recognized regions.

## 3. All21 criteria — interpretation and remaining freeze evidence

| ID | Retained target / precise review | Not yet frozen or proved |
|---|---|---|
| I01 | All forbidden input cases rejected; supported PNG admitted | Actual allowlist fixtures, hashes, CRC/truncation/metadata/path-race cases |
| I02 | Exact raw/display metadata; explicit unknown profile/DPI | Known orientation/profile PNGs and CMS build/profile hashes |
| C01 | Every major>=20% region within8/channel, coverage error<=5pp | One-to-one palette matching minimizes total squared RGB error; unmatched major region fails; alpha-weight denominator and analytic truth must be pinned |
| C02 | Ramp angle<=10deg modulo180, residual<=8; zero fixed negative claims | Include checkerboard, textured/photographic, lighting and compressed-band negatives; analytic sampler/window/profile and all ramp endpoints need freeze |
| C03 | Ratio error<=0.02 on known opaque pairs | Exact pair/region truth and reference arithmetic; ambiguous backgrounds cannot become compliance claims |
| T01 | Precision/recall>=0.90 per clean language stratum, IoU>=0.5 | Reviewer boxes, denominator/eligibility and reading order |
| T02 | English pooled clean CER<=0.05 | Actual corpus and per-poster distribution, no accuracy claim today |
| T03 | Telugu pooled clean CER<=0.10 independently | Native annotation/body-height agreement, truth scalars and poster counts |
| T04 | Synthetic ratio error<=0.1, gap/alignment<=2px | Analytic baseline/spacing truth, Telugu ligature/mark ambiguity; no exact tracking inference |
| G01 | Geometry<=2px, empty fraction error<=0.03 on analytic fixtures | Ground-truth occupancy definition and finite grid tests; not semantic layout recovery |
| G02 | Hard factual checks all pass;>=24/30 supported rationales | Human rubric: cited evidence, defensible interpretation, uncertainty and no invented fact; blind independent scores/adjudication. This is a human usefulness count, not aesthetic truth |
| M01 | Luma error<=1, declared blur/noise ramps monotonic, flat negatives safe | Coefficients/kernels/flat masks and monotonic/tie policy |
| U01 | High only with>=30 predictions and>=90% correct per feature/language | Require>=10 source posters, separate calibration from holdout; report counts/coverage and clustered uncertainty.27/30 is not a90% reliability guarantee. Insufficient data disables high |
| D01 |10 repeat payload/hash matches per analytic fixture | Exact CPU/thread/native/profile builds and normalized bytes; job timing excluded |
| S01 | Every hard bound and denied access demonstrated | Complete OS mechanism, exact byte accounting, adversarial probes; remains Gate A blocker |
| S02 |15s work/60s job and2s termination confirmation | Confirm2s is verification latency, not extra allowed work; cold setup and kill scheduling need measured evidence |
| S03 | Prior valid state or explicit recoverable draft, no false approval | New report-store crash matrix, uncertainty/recovery and bridge partial failures |
| O01 | No account/network/payment or runtime fetch; missing model blocks affected path | Offline artifact manifest, absent/changed data runs; not clean rebuild proof |
| O02 | p95<=10s cold/warm separately; all hard deadlines retained | nearest-rank p95=76th of80 attempts, all failures/timeouts included as60s for quantile accounting; cold=fresh VM/process with declared cache state, warm=retained approved runtime but fresh job. Report boot separately AND in end-to-end time |
| R01 | Explicit manual choice, immutable provenance, no approval transfer | Gate B contract approval and standalone-R1 revocation gap decision; invalid bridge choices included |
| R02 | Zero protected changes and fresh output boundary | Manifest/policy/command/source hashes; no protected-workspace probes/access needed |

These labels are the suffixes of existing R2-I01 etc; none is removed or counted twice.
Thresholds are not tuned using imaginary measurements. They may be infeasible under
the15s shared OCR deadline; that requires an openly reviewed scope/algorithm revision,
not a larger hidden budget or silently disabling Telugu.

## 4. Objective evidence versus judgment

Pixels, exact color/geometry, contrast arithmetic, OCR edits and repeated hashes are
objective within their defined measurements. Focal hierarchy, visual balance, mood,
emotional effect and creative appropriateness require human review. Semantic findings
remain inferred; a reviewer can mark ambiguous/unavailable rather than invent truth.
A high-contrast region is not automatically the subject; texture score is not mood.

All80 applicable heldout attempts stay in denominators. Unsupported/timeouts do not
disappear as "not completed"; applicable mandatory failures block their criterion.
Abstention is allowed only where the frozen criterion explicitly permits it. Report
completion rate, every failure/reason, language/quality/genre counts and poster-level
error spread. Do not pass performance by retaining only successful jobs. No new95%
completion allowance is substituted for mandatory quality/security criteria.

## 5. Freeze protocol and status

Can draft now: integer margins, evaluator rules, profile keys, thresholds, annotation
instructions, rights manifest fields and attack-probe taxonomy. Still requires A/B/C
ratification before FROZEN. Cannot freeze now: actual lawful image bytes/IDs/hashes,
annotations/reviewer availability, full joint allocation, exact native/model profile,
latency/quality/security behavior or archive sizes. No ground truth was invented.

Future evidence bundle includes signed-off split/rights/annotation/profile/evaluator
manifests and input hashes BEFORE worker evaluation. Benchmark tools themselves need
separate authorization; code-only contract/vector arithmetic here is not an image trial.
Gate D stays UNVERIFIED until manifests exist and are accepted; measured pass evidence
will only follow separately authorized experiments. No R2 implementation begins here.
