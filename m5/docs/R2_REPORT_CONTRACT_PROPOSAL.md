# R2 report contract — precise proposed namespace

Draft 1, 2026-11-10. PROPOSED, NOT APPROVED OR IMPLEMENTED. R1 and all prior documents
remain unchanged. Read [bridge](R2_R1_BRIDGE_CONTRACT_PROPOSAL.md),
[vectors](R2_CANONICAL_VECTOR_SPEC.md), [security decision](R2_SECURITY_GATE_DECISION.md)
and [roadmap](R2_IMPLEMENTATION_READINESS_ROADMAP.md). This refines the earlier informal
R2 shapes; user review must explicitly ratify the differences in section 9.

## 1. Closed grammar and common bounds

Every field listed below is required; `?` means JSON null is allowed, never omission.
Unknown fields/versions, duplicates, coercion and partial interpretation are rejected.
Format literals use prefix `ai-reel-studio/` plus the named suffix. H=64 lowercase hex;
ID=nonzero canonical lowercase UUID; Time=valid UTC YYYY-MM-DDTHH:MM:SSZ; Int=signed64
JSON integer, no -0/exponent/fraction. Positive counts also have the bounds stated below.
D=canonical decimal STRING: G1 decimal grammar, <=32 ASCII characters, computed values
rounded once to six fractional places, half-even, then redundant zeros removed. Original
recognized/approved text is never normalized or rounded. No JSON floating numbers.

CRef = `{format,sha256:H}` where format is exactly one of the five proposed R2 formats.
It resolves to canonical payload bytes of the exact type. It is NOT an accepted R1 Ref.
ResourceRef = `{kind,sha256:H}` with kind source/profile/normalized; source/profile/
normalized hashes refer to immutable opaque bytes in the approved resource manifest,
not executable paths. No resource fetching, floating latest or filesystem paths in data.
Envelope = `{payload,sha256:H}`; SHA-256 of canonical payload only. No signatures claimed.

Canonical UTF-8/no BOM/no terminal newline; recursively sort keys by Unicode scalar
sequence, preserve arrays, no insignificant whitespace/non-ASCII escaping. Quote,
backslash/C0 escapes match G1; reject duplicate decoded keys, invalid UTF-8/surrogates,
nonfinite/raw float values and out-of-range integers. Each envelope <=1MiB, depth32,
500 total object members, 4096 array entries, 4096 scalars/string. Reuse public R1
canonical helpers only; do not change their bounds or register new R1 record formats.

Short=0..128 scalars, Explanation=1..256 scalars, Note=0..256 scalars. No C0 controls in
report prose except tab/newline; codes are ASCII closed enums below. Limitations is a
unique sorted array of <=2 Short strings. Empty explanations are invalid. Review reason
is 1..256 scalars. OCR word text is 1..64 scalars, with no C0 controls. Every count,
aggregate member/byte bound is checked before unrestricted allocation and on publication.

Region = `{x:Int,y:Int,width:Int,height:Int}` in DISPLAY source pixels after orientation,
origin top-left, half-open rectangle. x/y>=0, width/height>0, x+width<=display_width,
y+height<=display_height; checked integer arithmetic. Store coordinates only once.
Normalized presentation derives x/W, y/H, width/W, height/H with declared rounding,
never stores a redundant approximation as a second authority. Analysis-image box edges
map back by floor(left/top), ceil(right/bottom), then clamp; report that transform.

## 2. Index and page payloads

```text
image-analysis-index@1 = {
 format, source_sha256:H, profile_sha256:H, normalized_sha256:H,
 raw:{width:Int,height:Int,bit_depth:Int,color_type:Int},
 display:{width:Int,height:Int,orientation:Int,alpha_present:boolean},
 analysis:{width:Int,height:Int}, color_policy,
 observation_pages:[CRef], ocr_pages:[CRef],
 coverage:{observations:Int,words:Int,ocr_scalars:Int,status}, limitations
}
image-observation-page@1 = {
 format, source_sha256:H, profile_sha256:H, page_no:Int, observations:[Observation]
}
image-ocr-page@1 = {
 format, source_sha256:H, profile_sha256:H, page_no:Int, language_profile, words:[Word]
}
Observation = {
 observation_id:H, metric, slot:Int, value:Value, region:Region?, origin,
 method_sha256:H, evidence_refs:[ResourceRef], confidence,
 confidence_reason:Explanation, limitations
}
Word = {
 observation_id:H, region:Region, text, raw_confidence:D?,
 status, reading_order:Int
}
```

Index source edges1..8192, pixels<=16,777,216, bit_depth=8, color_type=0/2/3/4/6.
Display dimensions follow orientation1..8; analysis edges1..2048 with preserved aspect
ratio under the pinned integer sizing rule. color_policy is declared-srgb/assumed-srgb/
icc-to-srgb. profile pins conversion/alpha/resampling/metric/OCR settings and every
executable/native/model hash. No unversioned tunable or OCR language override at runtime.

Page numbers contiguous from1 SEPARATELY in each list. Index lists refs in page-number
order, not digest order. Pages bind exact source/profile and must resolve locally.
Observation sort key=(metric,x,y,width,height,slot), with null region before nonnull; one
Observation per key. Word reading_order is globally contiguous1..N across OCR pages,
from pinned engine block/paragraph/line/word order, not arbitrary filesystem order.
Duplicate word region is allowed when reading_order differs; duplicate IDs/orders fail.

Observation ID = SHA-256 of canonical `{source_sha256,profile_sha256,metric,region,slot}`.
Word ID uses the same preimage plus reading_order, metric literal `ocr.word`. No ID
depends on pagination, time, random UUID or confidence/review state. Duplicate logical
keys are rejected, not overwritten. Hash collision with differing payload is a conflict.
method_sha256 equals profile_sha256 in this profile. Evidence list contains exactly
source/profile/normalized ResourceRefs sorted by kind, matching the Index's hashes.

At most8 observations/page,32 words/page; global64 observations,512 words,16,384 OCR
scalars,32 total pages and1MiB aggregate canonical ENVELOPES INCLUDING Index. Page count
at maxima is8+16=24, leaving headroom, not a requirement to emit32. Sum of page counts,
texts and refs must equal coverage. Empty arrays mean zero coverage, not success by
omission. coverage.status=complete/partial. Complete requires all metrics mandatory for
the accepted stage profile; OCR absence cannot become complete R2-C. A partial index is
inspectable but not eligible for whole-report approval/bridge. Exceeding any bound fails
publication as result-limit, never truncates. A schema-valid object is not proven output.

Word status=recognized/uncertain; these are recognizer outputs, never approved facts.
raw_confidence is null or -1..100 decimal from pinned engine; it is not a calibrated
probability. language_profile=eng/tel/eng+tel. No guessed text inserted into Word; inferred
interpretations are separate Observations. Preserve raw Unicode including Telugu marks.

## 3. Closed metric/value catalogue

Value is one of `{kind:"color",rgba}` (lowercase #rrggbbaa),
`{kind:"decimal",value:D,unit}`, `{kind:"text",value}` (<=256 scalars),
or `{kind:"choice",value}`. No generic maps, CSS, executable extensions or hidden scene.
Decimal unit=px/ratio/degree/channel-level/contrast-ratio. Ranges are inclusive.

| Metric | Value/range | Region | Origin |
|---|---|---|---|
| palette.swatch | color; one swatch per distinct spatial Region/key | required | measured |
| palette.coverage | decimal ratio0..1 for corresponding Region | required | measured |
| gradient.direction | degree0..<180 | required | inferred |
| gradient.residual | channel-level0..255 | required | measured |
| contrast.local | contrast-ratio1..21 | required | measured; pair selection limitation required |
| text.height, text.line_gap, layout.margin, layout.alignment_error | px0..8192 | required | measured |
| text.size_ratio | ratio0..100 | required | measured |
| layout.empty_fraction, layout.occupancy, text.density | ratio0..1 | required | measured |
| treatment.luma_p10, treatment.luma_p50, treatment.luma_p90, treatment.sharpness_rms, treatment.noise_rms | channel-level0..255 | optional | measured |
| treatment.saturation, treatment.dark_fraction, treatment.light_fraction | ratio0..1 | optional | measured |
| text.hierarchy | choice heading/body/caption/unknown | required | inferred |
| layout.grid | choice single-column/multi-column/modular/unknown | required | inferred |
| layout.focal, layout.balance, treatment.lighting, treatment.texture, treatment.depth, suggestion.rationale | text | optional | inferred |

slot is0..7; nonpalette slot=0. Palette uses rank0..7 consistently for swatch/coverage
and a whole-display Region. This resolves identical palette-region key collisions
without inventing separate bounding boxes or dropping colors. Word IDs use slot=0.
This is a proposed refinement of the earlier informal shapes, not an R1 schema change.

Confidence=high/medium/low/not-assessed. It describes the method's qualified evidence,
not approval or availability. High requires the frozen per-feature/language calibration
gate. Unsupported exact font, tracking, true lighting/depth/layer identity are absent,
never filled as measured values. Uncertain critical interpretations require review or
explicit exclusion; availability is determined separately by job/resource state.

## 4. Reviews, corrections and deterministic eligibility

```text
image-analysis-review@1 = {
 format, record_id:ID, created_at:Time, created_by:ID, job_id:ID,
 base_generation:CRef, subject_ref:CRef, observation_id:H?,
 previous_review:CRef?, decision, corrected_value:Value?, reason, authority
}
```

subject_ref is the job's Index (observation_id=null) or one of its pages (ID required
and must identify an original Observation/Word). No review of unrelated job/page.
Word's review value is text; exact original evidence is never changed. authority=A/B/C
as existing register; content/language needs C, rights/brand needs B, A accepts phases.
decision=corrected/approve/exclude/reject/revoke. corrected_value is nonnull ONLY for
corrected and type/range matches the metric or Word text. All other decisions null.
Corrected cannot apply to whole Index; whole-report exclude is invalid. Correction
creates unapproved effective value; next approve reviews the latest correction, not
the original silently. Exclude/reject/revoke does not delete that correction chain.

previous_review must equal latest committed review for the exact (job,subject,ID).
base_generation equals the preceding Job HEAD. Commit ONE review per generation;
competing same-base events conflict, never resolve by UUID/time. No hash cycles: Review
points to old Job and page; new Job points to Review. All original observations remain.

At one current Job HEAD and trusted UTC time: original origin/evidence stays measured/
inferred; effective value is latest corrected value in that subject chain; review is
latest decision, initially unreviewed. Corrected is not approved. Availability=available/
missing/stale/unsupported/failed derives from job state, resource manifest and current
rights/profile validity. Eligibility requires available AND latest approve after the
latest adverse event/recovery AND valid current rights/dependencies. Required subjects
must be approved or explicitly validly excluded; exclusions cannot remove mandatory
capabilities or make an incomplete result complete. Whole-report approve follows all
included subject approvals. Later subject correction/revoke invalidates whole-report
eligibility until fresh subject-then-report reviews. Restoring resources never restores
approval. No review may be minted by a worker.

## 5. Job as publication/commit log

```text
image-analysis-job@1 = {
 format, record_id:ID, job_id:ID, created_at:Time, created_by:ID,
 revision:Int, previous_job:CRef?, operation, source_sha256:H, profile_sha256:H,
 state, availability, result_ref:CRef?, review_ref:CRef?, failure:Failure?,
 resource_evidence_sha256:H?, recovery_from:Recovery?
}
Failure={code,stage,detail:Note}
Recovery={head_present:boolean,head_bytes_sha256:H,previous:CRef}
```

Job snapshots are immutable; job_id stable, record_id new each revision. Normal
operations require previous_job=exact current HEAD, same job/source/profile and revision
=previous revision+1. Initial revision1 has null previous_job, selected state, unknown
availability and null result/review/failure/evidence/recovery fields. Recovery is the
explicit exception: previous_job=validated recovery_from.previous, revision=THAT selected
Job.revision+1, not damaged HEAD.revision+1. Damaged HEAD bytes remain evidence, not a
required valid ancestor. Full CRef, not revision alone, identifies a generation/branch.

operation=progress/review/invalidate/revalidate/recover. state=selected/preflight/decoding/
extracting/ocr/validating/draft-complete/partial/failed/canceled/quarantined. Progress
follows that sequence, optionally skips OCR only by accepted profile; nonterminal states
may fail/cancel/quarantine. Terminal states never restart workers; retry is a NEW job_id.

| Operation | Permitted state transition | Availability | failure |
|---|---|---|---|
| progress | Forward work state, then draft-complete/partial/failed/canceled/quarantined | In-progress unknown; complete available; other terminal failed or unsupported | Required for partial/failed/canceled/quarantined; null otherwise |
| review | draft-complete -> same state, only while currently available | available, unchanged | null |
| invalidate | draft-complete -> same execution state, result retained | missing/stale/unsupported/failed | Required, code dependency, stage validate |
| revalidate | Previously invalidated or recovered draft-complete -> same state; external dependency checks only, no worker | available | null |
| recover | Selected valid PREVIOUS complete -> draft-complete; otherwise quarantined | stale if complete, otherwise failed | Required, storage/recover |

result_ref is required Index only for draft-complete/partial, null otherwise. review_ref
is required only for review, null otherwise. Review preserves result/state/execution
evidence. recovery_from is required only for recover, null otherwise. The failure
predicate in the table is exhaustive; there is no conflicting generic null rule.
Failure code=input/unsupported/resource/time/cancel/storage/schema/hash/worker/result-limit/
dependency; stage=import/decode/extract/ocr/validate/publish/cleanup/recover. Detail is a
bounded safe diagnostic, never raw private OCR. Supervisor-owned resource_evidence_sha256
is required on terminal states and metadata operations, may be null while initial/work
state; it is not worker proof. Failed/quarantined/partial/canceled results cannot become
complete by revalidate; a fresh authorized job is required.

Every invalidate/recover creates a sticky review watermark at that Job revision.
Restoring resources never revives approvals: fresh subject then whole-report reviews
must follow the watermark. Recovery never inherits pre-recovery approval for current use.
Current eligibility ALSO checks source/profile/rights at use time, including expiry before
an invalidation record can be committed. Uncertain checks fail closed. Record adverse
state before acknowledging it processed; no worker may clear availability.

Unavailable per-metric DISPLAY state is derived from the frozen profile's expected metric
instances, absent emitted observations and bounded supervisor failure evidence. It is
not an Observation with an invented Value. Missing mandatory metrics forces partial;
optional omission permits complete only when explicitly allowed by the accepted profile.
A successful OCR run recognizing zero words reports that fact, not certainty that no text
exists; evaluation still counts missed truth. Absent reason evidence is 'not emitted',
not an invented diagnosis. The mandatory stage/capability cannot disappear by omission.

Job HEAD is the ONLY review/result publication authority, a canonical CRef <=1024 bytes.
Publication: lock + expected generation -> validate entire reachable DAG -> durable
exclusive pages/index/review/resource evidence -> durable new Job -> retain valid old
HEAD as PREVIOUS on NORMAL updates -> atomic HEAD replacement -> directory sync -> success.
Review base/previous refs are rechecked under lock. Raw worker/job files are never authority.
Any error before publication preserves old state; sync failure after publication UNCERTAIN.
Recovery uses explicit captured raw HEAD presence/hash plus valid PREVIOUS, preserves
damaged bytes durably, never rotates PREVIOUS, publishes a recovery Job and invalidates
approval. No auto orphan promotion, initialization of damaged stores, overwrite or GC.
This is a NEW store contract, not reuse of R1's private Store internals or its test pass.

## 6. Closure, bounds and migrations

Review/history storage is trusted metadata, separate from 1MiB worker-result cap and
128MiB worker scratch. Bound reachable review/job graph to4096 records/64MiB/depth2048;
future implementation must traverse iteratively. Stop writes on bounds; no pruning.
No CRef cycles, wrong source/profile/page IDs, duplicate orders/keys or changed bytes
under the same hash. Job manifest and Review schemas must fit per-envelope G1 bounds.

Current source/resource/rights change blocks affected current eligibility and bridge;
old records stay immutable. Applicable adverse changes must be recorded, not just shown
as a warning. Trusted time failure blocks expiry-sensitive use. No automatic migration;
unknown newer schema refused for interpretation. Any future migration is explicit new
artifact with old hash preserved and no approval transfer, requiring separate authorization.

## 7. Size proof obligation

With pixel-only Region, Word has6 members plus4 region members:32 words/page stays
below500, with page headers. Eight bounded Observations/page also fit. At512 words,
64 observations there are24 pages, below32. Each Word <=64 scalars and Observation
text/notes bounded above; bound encoded Observation entries to7000 bytes, Word entries
to700, each page's nonentry overhead to512 bytes and Index envelope to16,384 bytes.
Even a conservative32-page budget is64*7000+512*700+32*512+16384=839,168 bytes, below1MiB.
Exact encoded byte/member checks are still mandatory. Aggregate includes envelopes/index.
No assumption that all individually valid pages fit collectively. Overflow refuses
publication and is visible as result-limit, not a truncated successful report.

## 8. Gate assessment

Precise draft contracts supplied; executable schemas, independent reader validation,
publication/recovery behavior and current-authority service are UNVERIFIED. User approval
and contract-only conformance experiment authorization are required. No R2 code or fixture
has been created by this document.

## 9. Explicit differences requiring ratification

Earlier R2 docs had informal shapes, duplicated normalized coordinates and unspecified
metric identities. This proposal derives normalized coordinates, adds slot to avoid
palette-key collision, makes page order explicit, and uses immutable Job generations
to publish reviews without a sixth format. It tightens strings to make pagination
plausible. It does NOT silently amend old documents, accepted R1 or creative@1.
