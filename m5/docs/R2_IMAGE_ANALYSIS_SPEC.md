# R2 — bounded image analysis technical specification

Draft 1, 2026-11-10. DESIGN/RESEARCH ONLY. No implementation, install, source/model
acquisition, tests, schema migration or integration authorized. R1 remains conditionally
accepted under [its acceptance record](M5_R1_ACCEPTANCE_RECORD.md), unchanged.

Companions: [research](R2_OPEN_SOURCE_RESEARCH.md), [dependency/licence matrix](R2_DEPENDENCY_AND_LICENCE_MATRIX.md),
[security](R2_ARCHITECTURE_AND_SECURITY.md), [acceptance](R2_ACCEPTANCE_MATRIX.md).
Authority: ../PROJECT_ENGINEERING_POLICY.md, ../THIRD_PARTY_INVENTORY.md and
../OFFLINE_BUILD_STRATEGY.md; universal spec G1/G7 and Reference spec sections 6, 13–15.
Historical documents saying R1 is unauthorized are superseded only by its user acceptance;
no such supersession authorizes R2. This proposal creates no executable schema or fixture.

## 1. Decision and entry blockers

Recommend a replaceable **Pillow worker plus small deterministic analysis components**,
with Tesseract benchmarked separately for English and Telugu. Use existing licensed,
compatible installed artifacts only after isolation and artifact identity qualification.
Do not load another environment's native modules into R1's Python 3.15 interpreter.
Sharp is a performance comparator, not a permanent private-HyperFrames dependency.
No vision-language model, cloud API, neural aesthetic scorer or optional R6 model.

Two material prerequisites remain unresolved:

1. **Isolation implementation:** an OS-enforced aggregate 1 GiB memory bound and 128 MiB
   job-storage bound have not been demonstrated on this Mac. Monitoring/termination alone
   is not enforcement. No automated decode may be enabled until the security gate passes.
2. **Data compatibility:** accepted R1 explicitly rejects measured/inferred origins,
   regions, OCR content and unknown properties. Direct automated Finding import would
   fail or mislabel provenance. Use the separate analysis-report proposal below and an
   explicit manual R1 bridge; separately review that new contract before implementation.

The documents constitute a complete bounded proposal, not proof that these gates are
closed or that the full requested R2 is implementation-ready today.

## 2. Scope and feature commitments

One local PNG reference per job, analysis-only. Retain original bytes; never apply
styles, create creative layers, alter brand assets, change projects or approve exports.
PNG acceptance details and all bounds are in the security companion. JPEG, WebP, TIFF,
SVG, PDF, animated images and video are explicitly unsupported in the initial profile.
They are not passed through an unrestricted decoder for format detection.

Full proposed R2 requires the following report sections. Staging delivery does not
permit declaring full R2 accepted with OCR or another mandatory section silently absent.
Unavailable individual observations are allowed only where their criterion explicitly
requires abstention; an entire missing capability is a blocked gate or approved scope change.

- Inspection: raw/display dimensions, exact aspect ratio, format, bit depth, channel
  mode, alpha coverage, declared/assumed color interpretation, metadata orientation,
  missing DPI and resolution warnings. Never infer print resolution from pixels alone.
- Color: up to eight swatches, alpha-weighted coverage, secondary/accent candidates,
  spatial occupancy, gradient hypotheses, local foreground/background relationships
  and contrast. Human assigns semantic palette roles; dominance is not brand authority.
- Typography: OCR text regions, line geometry, relative size and density, alignment,
  line-gap measures and proposed heading/body hierarchy. OCR is recognized text, not
  approved wording. Exact fonts/weights/tracking are unavailable unless separately
  supported; Telugu glyph shaping makes character-gap-to-tracking inference unsafe.
- Composition: edge/occupancy maps, measured margins/alignments, negative-space proxies,
  candidate grids and high-contrast regions. Focal subject, hierarchy, balance and
  layer-like regions are interpretations, never recovered layers or semantic truth.
- Treatment: brightness/luma percentiles, saturation proxy, dark/light occupancy,
  local contrast and normalized sharpness/noise proxies. Lighting direction, texture,
  visual depth and separation are uncertain interpretations of those measurements.
  Do not reconstruct a physical lighting rig, editing history or original depth map.
- Every section explains measurable evidence, uncertainty, omissions and a possible
  design implication. Recommendations are suggestions and never executable operations.

## 3. Deterministic analysis profile proposal

Pin source-byte hash, algorithm/profile hash, decoder/interpreter/native identities,
OCR binary and language-data hashes, color transforms, thread count, rounding and
sampling parameters. No random seeds, wall-clock inputs or network state in measurements.
Run one analysis job at a time; decoder and OCR stages serially, CPU-only, one thread
where configurable. Changing a dependency/profile creates a new result, never reinterpretation.

Normalization: accept single-frame 8-bit PNG color types 0/2/3/4/6, initially noninterlaced.
Expand palette/gray to RGBA, apply validated EXIF orientation 1–8 if present, retain raw
and display dimensions. Missing orientation means identity, explicitly recorded. No OCR
orientation detection or osd model is assumed. Valid sRGB is the target; absent profile
means recorded assumed-sRGB, not detected sRGB. ICC/gamma conflicts, unsupported profiles
or failed pinned CMS conversion cause unsupported status; never silently discard them.
Freeze decoder/CMS conversion settings before color evaluation. Alpha is not composited
onto a guessed background. Fully transparent pixels contribute no palette weight.

Downscale only when display edge exceeds 2048 using pinned LANCZOS in the agreed alpha
policy; retain aspect ratio and record integer coordinate mapping. Geometry observations
refer to display pixels and normalized ratios, never raw-orientation coordinates silently.
Keep full-resolution metadata separate from downscaled feature results.

Palette: reuse Pillow's RGB MEDIANCUT quantizer with eight colors and dithering disabled;
do not select optional libimagequant. Use deterministic raster-grid samples, at most
65,536, omit alpha=0, and assign weights alpha/255. Quantizer input contains only actual
visible RGB samples; do not pad a tile with invented black/white samples. Coverage is
weighted assignment of visible samples to palette RGB by squared channel distance.
Sort by descending integer alpha-weight then RGB lexicographic order; document tie rules.
All-transparent input returns an explicit empty palette. Map swatches to semantic
primary/accent only through human choice. Accuracy gate inherits existing R2-B tolerances.

Gradients: on fixed tiles, compare horizontal/vertical/diagonal channel ramps and residuals;
return direction only if the frozen synthetic-ramp criterion passes and a texture/edge
gate permits it. A colorful photograph is not automatically a gradient. Own the bounded
decision/uncertainty rule; reuse image statistics/resampling instead of new codecs.

Contrast: report local sampled color pairs and relative-luminance ratio using the
[W3C sRGB definition](https://www.w3.org/TR/WCAG22/#dfn-relative-luminance). An image sample
does not establish complete WCAG conformance or actual text-background ownership.
Composition uses fixed edge filters/row-column occupancy and OCR geometry. Sharpness
uses a declared derivative-response statistic; noise uses a declared flat-region residual.
Neither metric is a universal aesthetic score. All formula coefficients, windows and
tile sizes belong to the versioned profile before implementation acceptance.

OCR: proposed Tesseract 5.5.4, OEM 1, PSM 3, explicit eng/tel or eng+tel by user-selected
profile. No OSD/equ/other language data loaded. Pass only supervisor-validated normalized
PGM input, not the untrusted original. Text boxes and raw confidence are observations;
confidence numbers are not calibrated probabilities. Preserve original recognized Unicode
exactly; human correction is a new record. No automatic translation, spelling repair,
brand-copy replacement, font identification or training. Exact traineddata commits/hashes
remain an entry gate; fast versus best is chosen by the frozen benchmark, not popularity.

## 4. Proposed new result contract — not a change to R1

Use new namespaced formats in a future R2 module, pending separate design approval:
`image-analysis-index@1`, `image-observation-page@1`, `image-ocr-page@1`,
`image-analysis-review@1`, and `image-analysis-job@1`, all prefixed ai-reel-studio/.
These names do NOT add formats to accepted R1's validator/store.

Proposed closed fields (all required; ? means nullable):

```text
Index: format, source_sha256, profile_sha256, normalized_sha256,
       raw_width, raw_height, display_width, display_height,
       color_policy, orientation, page_refs, limitations
ObservationPage: format, source_sha256, profile_sha256, observations
Observation: observation_id, dimension, value, region?, origin,
             method_sha256, evidence_refs, confidence, confidence_reason, limitations
OCRPage: format, source_sha256, profile_sha256, language_profile, words
Word: region, text, raw_confidence, status
Review: format, record_id, created_at, created_by, subject_ref,
        observation_id?, previous_review?, decision, corrected_value?, reason, authority
Job: format, job_id, source_sha256, profile_sha256, result_ref?,
     state, started_at, completed_at?, failure?, resource_evidence_ref
```

Proposed scalar rules reuse G1 UUID/Hash/Time/Decimal/Value definitions, strict UTF-8,
duplicate-key rejection and scalar-key canonical sorting. Analysis content references
are a NEW closed `{format, sha256}` shape, not G1 Ref: index/pages have no UUID field.
They resolve by exact supported format and canonical payload hash. Review/Job IDs use
G1 UUIDs. No analysis reference is accepted by R1's existing Ref validator.
Review subject is an Index (observation_id=null) or Page (required observation_id matching
one original observation). previous_review pins the latest review of that exact subject/
observation. authority is A/B/C; decision is corrected/approve/exclude/reject/revoke.
Only corrected has a nonnull corrected_value, checked against the metric's value type.
It creates a draft correction; a later approve reviews the latest preceding correction
or unchanged original, never silently resets it. All other decisions have null corrected_value.
The original observation stays immutable and its measured/inferred origin is retained.
Whole-report approval requires current approved included observations and resolved
exclusions; low-confidence critical items cannot disappear by omission. Review actor/
role confirmation remains trusted-local-user attestation, not cryptographic identity.
Origins measured/inferred;
subjective interpretation is inferred with explicit limitation, never measured. Units
use a closed R2 catalog: px/ratio/degree/channel-level/contrast-ratio, defined per metric.
Region is x/y/width/height display-pixel integers plus normalized ratio coordinates;
bounds must agree with Index. Value kinds color/decimal/text/choice or closed metric
tuples; no arbitrary CSS, paths, executable payloads or hidden creative scene.
Dimensions are the feature names in section 2, with exact metric subkeys frozen in the
profile. Exact executable JSON Schemas and independent vectors are a PRE-entry review
item, not left for an implementation agent to invent silently.

Index/page payloads have no timestamps/random IDs: observation_id is a hash of source,
profile, metric key and region, with collision/duplicate refusal. Worker output is sorted
by metric/region, not completion order. Round computed fractions explicitly to six
decimal places, half-even, then use canonical decimal strings. Raw OCR text is unchanged.
Store self hashes outside payloads. Job timing/IDs/resource telemetry are separate so
repeated measurement hashes can match while execution manifests differ.

Each page/envelope <=1 MiB, depth32, aggregate500 members/4096 array items/4096-scalar
strings as G1 canonical helpers require. At most eight observations or 32 words/page;
global result <=64 observations, 512 words, 16,384 OCR scalars, 32 pages and 1 MiB total.
Split by deterministic metric/reading order; overflow is explicit incomplete/failed,
never silent truncation. A canonical sorted index pins every page. Review state derives
from append-only review events, availability from validated job/dependency state.
Correction creates a new value/revision linked to the unchanged original observation.
Reanalysis produces a new result; it cannot erase prior corrections or transfer approval.

## 5. R1 compatibility route

Accepted `schema.py` requires user-entered origin and null source/method/region/interval;
its property catalog cannot represent OCR, gradients or arbitrary region measurements.
Do not loosen that validator, masquerade automation as manual measurement or serialize
R2 formats into its Store. Native automatic Finding import is NOT currently supported.

Recommended compatible bridge: keep measured/inferred observations and their review
events in the separately reviewed R2 report namespace. User explicitly selects/edits
allowlisted abstract properties into a NEW R1 manual Finding/Recipe revision. Its origin
is honestly user-entered because it is the user's choice; its evidence includes pinned
Dependency records for the original reference, analysis report and extractor/profile.
Original method/region/uncertainty remain inspectable in the immutable report. R1's
source/method remain null as required. Palette roles are chosen, not inferred brand rules.
Typography/layout proxies are not copied into actual font/tracking values without review.

The bridge creates no Finding automatically before explicit user action. It reuses public
R1 factories/validation/Store only for accepted R1 records; no private-method monkeypatch.
Rights/availability confirmations and subsequent Finding/Recipe reviews remain explicit.
Analysis review, Recipe-definition approval and future R3 application approval are distinct.
New source/profile/report hash invalidates associated current analysis; old R1 manual
choices are never rewritten. Mark pinned report/reference dependencies stale through
explicit existing events and require fresh review; restoration does not revive approval.
Partial bridge failure must not expose a cleared Recipe. Preserve prior HEAD or explicit
draft state; cancellation before commit creates no Recipe. Never mutate creative@1.

Alternative direct-native measured Finding support requires a separately proposed R1
extension/new version and authorization; it is rejected for this unchanged-R1 assignment.
Review the sidecar/bridge contract before enabling measured+approved R2-C acceptance.

## 6. Report experience and sequence

Default: summary cards for Palette, Text, Layout and Treatment, each with evidence and
Available/Uncertain/Unavailable labels. Expand for region overlays, metric/profile IDs,
confidence reasons and original-versus-corrected values. Offer Correct/Exclude/Review;
never a one-click Apply. Example presentation (illustrative, not a measured result):
"Large high-contrast text near the upper third may lead attention; text-region geometry
supports that suggestion. Subject importance and exact font are unknown. Try increasing
the measured low-contrast label's contrast in a future separately approved design."
Font and palette recommendations must respect the pinned Brand Kit, Locked/Guided/Free,
rights and protected assets; a reference never overrides them. No originality/legal
clearance score, copied slogan/logo or recovered-layer claim.

Future sequence, each separately authorized: (1) finalize new report/bridge schemas and
fixtures, dependency identities and hard-limit mechanism; (2) prove job isolation using
synthetic adversarial fixtures; (3) metadata/color/geometry/treatment; (4) gradients and
OCR benchmark/enablement per language; (5) corrections/manual R1 bridge and full matrix
evaluation; (6) independent review and user R2 acceptance. No R3 application or M4 action.

Performance expectations are targets, not measurements: one job at a time on M4 Pro/24GB,
usual <=2048-edge PNG end-to-end p95 <=10 s, every worker <=15 s, job <=60 s, <=1 GiB
aggregate workers, <=128 MiB staging. OCR may time out on complex posters; report it,
do not exceed bounds or silently enable a larger model. No benchmark was run here.

Unresolved decisions: hard-limit/isolation facility; runtime/ABI and legal artifact closure;
traineddata commit/hash and fast/best selection; CMS/profile subset; exact new schemas/
metric profile; threshold ratification and native Telugu/design reviewer designation.
Recommend review of these five documents first. No R2 implementation authorization requested
as already granted, and no full implementation readiness claim until these entry gates close.
