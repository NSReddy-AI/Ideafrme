# Reference Style Studio Pro — design specification

Design draft 2, 2026-11-10. DESIGN REVIEW PENDING; documentation corrections only.
Part of UNIVERSAL_CREATIVE_STUDIO_SPEC.md. Independent read-only verification is pending.
No upload/analyzer, model, dependency, editor or renderer change is authorized here.
PROJECT_ENGINEERING_POLICY.md applies. Existing M5 foundations and M4 remain untouched.

## 1. Purpose and scope

Learn transferable visual/motion principles from references, then create an original,
editable design. Support all industries through the shared brief/brand/project system.
Do not treat similarity to the reference as the primary quality goal.

One reference service is accessible from Create, Brand Studio and the Editor. Entry
context sets destination and selection; it does not create three analysis implementations.
Quick/Guided/Professional modes use the same observations, recipe and operation plan.

Present capability: this is a proposed workflow. Existing Phase 2 creates synthetic
posters; it does not analyze arbitrary references. Unsupported gradients, masks,
typography controls, audio/motion, groups and scene operations remain capability-gated.

## 2. Minimal UI and progressive disclosure

Initial screen: Add references; choose intent; Analyze. Show local/offline status,
accepted formats/budgets, source rights questions and destination summary contextually.
Intent: Original inspiration; Brand/campaign extraction; Authorized layout adaptation;
Motion/editing direction. No inference that owning an uploaded file grants reuse rights.

After analysis reveal tabs: Findings, Style Mixer, Protection, Compare, Save Recipe.
Findings appear as editable observations with evidence and uncertainty. The mixer should
not imply that unobserved or unsupported properties have already been extracted.
No global percentage suggests a measurable amount of legal/originality compliance.

Reference cards show name/type/hash, assigned purposes, import status, rights/review
status, exclusion masks/regions (when supported), and selected frame/time range.
Removing a card never deletes the user's original file. Broken reference links are
reported; an approved recipe cannot silently resolve to different reference bytes.

## 3. Multi-reference Style Mixer

Dimensions: color, typography, composition, imagery treatment, lighting/atmosphere,
effects/texture, motion/camera direction, pacing/transitions, and audio direction.

For each dimension choose: approved brand; selected reference A/B/etc.; user-defined;
AI proposal; retain current design; or exclude. No selection copies source artwork.
For motion/audio dimensions, disable application unless the accepted engine supports it.

Choose one primary source per dimension by default. Advanced blending can add secondary
sources with explicit weights/ranges and a visible explanation. Weights control soft
preferences only, never protected assets, factual text, identity or rights. Do not average
incompatible font identities, layout constraints or transition types into meaningless data.

Example: brand palette + A's lighting cues + B's typographic hierarchy + C's pacing;
keep source logo, photographs, exact text and approved content bindings unchanged.
Typography cues refer to scale, weight, width, spacing and contrast, not an unsupported
claim of identifying a proprietary font. Suggest available licensed alternatives.

Hard constraints are conjunctive: rights, identity, source integrity, protected content
and hard brand rules must ALL pass. Capabilities/resource limits must also pass; a
renderer limitation blocks the proposed operation and never permits omitting a required
brand element. There is no priority order that sacrifices one hard constraint for another.
Only soft preferences are ranked: explicit permitted dimension choices, then guided
brand preferences, then inferred defaults. Equal-priority soft conflicts require a user
decision or an explicitly excluded property, not an undocumented arbitrary winner.
An explicit user preference cannot silently override a hard brand rule. Propose a new
separately reviewed brand-profile version when a brand change is truly intended.

## 4. Locked, Guided and Free

Locked: required text, approved logos/variants, protected photographs/regions, faces,
rights restrictions, hard brand rules. Generic style application cannot alter them.
Guided: preferred palette/type/layout/lighting; permitted changes stay within bounds.
Free: areas approved for redesign, still subject to rights, content, identity, capability
and export constraints. "Free" never means unrestricted use of copyrighted material.

Assign protection per asset, region, object, binding or rule where supported. Protection
overrides selection and influence settings. Editing a protection rule itself needs an
explicit reviewed operation; it must never happen as a side effect of a style request.
Do not distort/recolor a logo, rewrite an approved quote or replace a face to satisfy
the recipe. Preview blocked operations with reasons and offer a compliant alternative.

## 5. Import and analysis pipeline

1. Import/validate: local file type/signature, hashes, dimensions, streams/timebase,
   duration, decoded resource budget, provenance and rights/reuse intent. Isolate native
   decoding with job-only writes, bounded reads/timeouts and blocked outbound networking.
2. Measure: palette distributions, image geometry and bounded frame samples; optional
   detected cuts/fades. Preserve color-profile/timebase information in evidence.
3. Interpret: propose hierarchy, type characteristics, focal regions, lighting/depth,
   mood, apparent motion and uncertainties. Separate interpretation from measurements.
4. Draft recipe: normalize findings into bounded editable properties and source evidence.
5. Review: user corrects findings, excludes dimensions, resolves conflicts and approves
   a recipe version. Recipe approval is not approval of every eventual output.
6. Apply/compare: generate a validated operation plan, preview original alternatives,
   show protected/affected elements, then explicitly apply or discard.

No URL fetch is implicit in media probing. ffprobe accepts URLs, so callers must supply
only validated project-local paths and explicitly constrain network-capable protocols.
Imported media/metadata/reference text is untrusted data, never instructions for tools.
No model receives filesystem/shell authority. No auto-download of models or codecs.

Initial proposed analysis budgets for a future spike: one image first; later up to
three references, bounded 2048-pixel analysis images and selected clips up to 60 seconds.
These are provisional product limits, not verified performance claims. Longer video
uses explicit sampling/downscaling choices and reports omissions. Never exhaust 24 GB
by loading a planner, vision model and full-resolution video concurrently.
The binding pre-analysis security envelope and failure rules are specified in section
15 below. The limits above describe UI scope only; they do not weaken that envelope.

## 6. Findings report and confidence

For every finding record: dimension, value/range/unit, reference hash, region or exact
time interval, method/tool/version, evidence, uncertainty and independent state axes:
- Origin/method: measured, inferred or user-entered, retaining tool/version and source.
- Review: unreviewed, corrected, approved, excluded or rejected.
- Availability: available, missing, stale, unsupported or failed.
- Confidence: high/medium/low or not assessed, with reason and calibration scope.
A measured finding can also be approved. Corrections append a proposed value and its
author/reason; the original measurement and evidence remain identifiable. Reanalysis
creates new observations and does not replace a correction or review decision.
Confidence labels: high/medium/low with reason and scope, not uncalibrated percentages.
Detector score/threshold is not probability of correctness or a copyright verdict.

Report surfaces (future UI): editable swatches; gradient hypotheses; type characteristics
and local font alternatives; composition/focal-point suggestions; lighting/texture/depth
notes; shot thumbnails, timing and transitions; protected/excluded material.
Distinguish source image colors from brand colors, and visual lighting cues from a
recovered physical lighting rig. A flattened poster does not reveal its original layers.
Apparent camera motion may be a crop, zoom, stabilization or edit; report ambiguity.
Cut detection cannot prove narrative intent; audio rhythm cannot grant soundtrack rights.

The user can inspect evidence and correct values. Correction produces a new draft
recipe version; automated analysis must not overwrite a human correction silently.
Low-confidence critical decisions stay unresolved until corrected or excluded.

## 7. Style Recipe contract (proposed, not implemented)

A future versioned `style-recipe@1` record includes:
- Stable ID, schema version, name, revision, draft/approval status and immutable versions.
- Reference IDs/hashes, provenance and reuse/redistribution permissions; no binary media
  embedded by default. Include tool/method versions and measured sampling parameters.
- Transferable properties by dimension, units/ranges, evidence and uncertainty.
- Dimension source assignments, selected weights and conflict resolutions.
- Locked/guided/free targets, brand-profile version/hash and protected-content bindings.
- Applicable output types, required renderer/engine capabilities and unsupported findings.
- Human changes/approvals, compatibility requirements and recipe fingerprint.

No hidden copy of artwork, people, logos, captions or audio becomes a recipe property.
Recipes store design language, not a reconstruction of a third-party composition unless
the authorized-layout mode explicitly applies and the source rights support that use.

Store recipes as authoritative recipe records within the project/library folder model;
creative.json remains authoritative for creative layers/content. Bind applied recipe
ID/version/hash into the future operation/export provenance contract. Do not add unknown
fields to creative@1 or use a recipe sidecar to bypass its validation. New bindings,
group/scene operations or property types require a separate schema/operation proposal.
Approved recipes are independently versioned immutable artifacts. Working editors create
new revisions, never mutate an approved historical artifact. Project links pin explicit
recipe identity/revision/hash and dependency references, never a floating "latest".
Sections 13–14 define persistence, dependency invalidation and compatibility behavior.
The concrete G1 draft 2 derives review/availability from append-only events pointing to
exact immutable Findings; review changes do not create or rewrite Finding payloads.
Its structured RightsDecision and deterministic eligibility rules govern the manual-R1
subset, pending acceptance. Original method/confidence remain separate axes.

Portable recipes retain legal notices and evidence metadata. Export reference images,
video frames, original fonts or other licensed assets only when permission permits;
otherwise include hashes/descriptions and an explicit missing-resource report. Thumbnails
are derived content and also require a rights assessment. A missing source must not be
silently replaced; user-approved abstract properties can remain useful offline.
Campaign memory stores opt-in approved recipes, not automatic model training or a rule
that every campaign must repeat the same layout. New projects snapshot recipe versions.

## 8. Selective, reversible application

Targets: selected object, supported group, supported scene, chosen views or whole project.
Scope is explicit and visible. Group/scene targets are future capabilities, not current
creative@1 functionality. Changing shared content shows affected outputs before apply.

Translate only selected supported dimensions into allowlisted typed operations, with
base revision/hash preconditions. Validate references, locks, brand rules and resource
limits before preview. Reject unsupported dimensions; never bake text/logos into a
flattened image to hide an unsupported edit. Source/reference files remain immutable.

Show before/after, proposed operations, protected targets, blocked changes and affected
approvals. Apply a proposal atomically as one reversible transaction; failure leaves
the original unchanged. Current core's single-operation API must not be represented as
already providing this multi-operation transaction behavior. Undo/redo and save/reopen
must preserve recipe provenance and correct approval invalidation when implemented.
"Restore" means canonical creative content/layers/bindings and selected recipe dependency
references return to the intended state. Revision counters, audit events/history cursor
and invalidated approvals need not equal the old whole JSON. Undo never resurrects a
stale approval. A separate accepted transaction/provenance contract is required at R3.

Recipe approval confirms the intended transferable characteristics. Application review
confirms the proposed edit. Final content/brand/rights/render approval remains separate;
previous approval never authorizes unreviewed wording, translation or resized layout.

## 9. Input/output combinations

Poster -> poster: derive visual language and compose new editable layers.
Poster -> reel: propose motion from hierarchy; do not claim to recover hidden layers.
Reel -> poster: propose key-art from representative moments and a deliberate still
composition, not an arbitrary extracted frame; content/likeness/rights still apply.
Reel -> reel: infer timing/shot/motion patterns, not copy footage, soundtrack or exact
editorial sequence. Route eventual production through the accepted existing engine.

These paths share a recipe contract but have distinct capability/acceptance gates.
No M4 integration or FFmpeg/HyperFrames replacement is authorized by this specification.
For every path, preserve the source and create a separately identified output version.
Transfer palette/type hierarchy/composition principles only where supported. Motion,
audio and temporal measurements are excluded from still application, not flattened or
silently converted. Motion inferred from a poster is a NEW proposal requiring review.
For reel -> poster, record the chosen reference frame/time range and intentional still
recomposition; no arbitrary frame selection or extraction of unlicensed imagery.
For poster -> reel and reel -> reel, record source-to-output property mappings and
timebase/scene mappings. Missing required mappings block the proposed application;
optional unsupported dimensions can be excluded only through an explicit reviewed choice.
Recipe approval does not approve any adapted output. Output content/brand/rights/render
review is independent per variant. R5-B and R5-C separately test analysis and production.

## 10. Three-way comparison

Reference -> reviewed recipe -> proposed original design. Show which dimensions were
used, changed, excluded or blocked; expose differences in available fonts/layout/motion.
For future video, synchronize relative scene/beat timing with an explicit time mapping,
not a misleading claim of frame-accurate equivalence across different durations.

Similarity checks are warning aids: detect exact/near duplicates when benchmarked,
show evidence and request redesign where appropriate. They cannot prove originality,
non-infringement or legal reuse. A low similarity score is not a license approval.
Offer independent concepts rather than iterating toward maximum reference similarity.

## 11. Open-source-first assessment

PySceneDetect: BSD-3-Clause upstream; detects scene changes including cuts/fades,
not cinematographic meaning. Preserve source/binary notices and non-endorsement terms.
Current official docs identify 0.7.3. Read-only local inspection found 0.7.3 metadata in
~/.venvs/rs_asr; the existing inventory calls it tested, not adopted. Do not modify that
shared environment or adopt its entire dependency tree implicitly. Upstream dependencies
include NumPy, OpenCV, Click, platformdirs and tqdm; exact chosen artifacts, native/codecs,
security, arm64 runtime and offline source/build closure need separate adoption review.
Recommendation: benchmark only after a scoped video-analysis authorization. Sources:
https://github.com/Breakthrough/PySceneDetect
https://raw.githubusercontent.com/Breakthrough/PySceneDetect/main/LICENSE
https://raw.githubusercontent.com/Breakthrough/PySceneDetect/main/pyproject.toml
https://www.scenedetect.com/docs/latest/

ffprobe: executable observed at /opt/homebrew/bin/ffprobe; reuse is preferable to building
a media metadata parser. Structured metadata does not interpret style or prove safe
rights. Binary version/flags/hash and linked codecs require audit before adoption or
distribution; FFmpeg's LGPL/GPL terms depend on its build. Do not invoke M4 scripts.
Sources: https://ffmpeg.org/ffprobe.html ; https://ffmpeg.org/legal.html

Color Thief (meirdev/color-thief): the referenced repository is a small Python palette
project, not automatically the original Color Thief implementation. Its page labels
MIT and lists multiple algorithms; no published release was shown. Exact LICENSE and
dependency-file retrieval could not be completed in this research, so exact-version
adoption remains UNAPPROVED pending verification. Local installation not established.
Do not infer production quality/maintenance from public availability. Source:
https://github.com/meirdev/color-thief

Prefer first benchmarking installed Pillow quantization and/or Sharp statistics against
hand-labeled palette fixtures before adding a palette dependency. Existing codec and
quantization capabilities should be reused; build our own semantic role/brand mapping,
not a new quantizer. Representative colors are not necessarily useful design colors.
Source: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize
Existing-tool/compliance limits remain those in THIRD_PARTY_INVENTORY.md.

Typography recognition, semantic composition and motion interpretation have no approved
new model in this design. Start with user-entered observations and deterministic
measurements, then separately benchmark commercially suitable local models/weights.
Exact licenses, transitive sources, memory/speed/security and offline rebuilding must
be recorded; no mandatory cloud API, no downloading, no simultaneous large model loads.

## 12. Implementation and acceptance gates

R0: review this spec and its integration with universal Brand Studio/brief/editor gates.
R1: manual recipe contract/editor and protection rules using synthetic findings; no AI
or media decoder needed. "Editor" here means structured fields, NOT the G2 canvas editor.
Requires approved G1 recipe/brand/reference contracts, but does not require G2/G3/G4/G5
implementation or M4 release. Approve data contracts before coding; creative@1 unchanged.
R2: bounded image palette/geometry analysis using installed tools, with source manifest,
decoding isolation and annotated fixtures; user reviews uncertain findings. Depends on
R1 and G1 contracts plus section 15 isolation acceptance; not on G2 or M4 integration.
R3: single-image recipe-to-poster preview/application; prove atomic undo/redo, source
preservation, approval invalidation and renderer parity before multi-reference blending.
Depends on R2 and accepted G1 transaction/provenance contract. G2 selection/preview
capabilities are required for editor entry; a separately approved structured preview
path may precede G2. No G3 concept model or G5/M4 integration is implicit.
R4: multi-reference dimension mixing/conflict resolution, portability and three-way
comparison. Depends on R3; G3 is required only for automatic concept generation, G4 for
the complete integrated three-entry UI. Core mixing can be tested without either.
No reference media included in exports without rights clearance.
R5: separately approved video shot/metadata analysis and motion interpretation; actual
reel production still requires accepted M4 baseline and isolated adapter approval.
Analysis-only R5-A/B requires R4 and G1 media contracts, not permission to execute M4.
Production R5-C additionally requires G5, full M4 acceptance and its exact baseline.
R6: optional vision/font/similarity models only after separate code/weight/dependency,
quality, hardware and independence gates. Requires R1–R5 analysis acceptance; any affected
G2/G3/G4/G5 integration gates must already be accepted. Model-off fallback remains usable.

Acceptance proposals:
- A supplies lighting, B type hierarchy, brand palette: every applied property traces
  to the selected source; excluded dimensions and locked elements are unchanged.
- Palette conflicts with brand: hard rule wins or application stops for a decision;
  overall influence never bypasses protection.
- Same flattened font could be several families: report characteristics/alternatives,
  not a certain font identification. Human correction survives reanalysis.
- Poster/reel input-output paths use correct capability checks and no silent flattening.
- Missing/changed reference hash invalidates affected findings; source bytes unchanged.
- Transaction fails halfway: no partial edits; undo/redo/save/reopen restore canonical
  creative content and pinned references, with revision/audit/approval rules in section 8.
- Cut/fade fixtures: report precision/recall and boundary error against annotated clips;
  accept thresholds before evaluation. Never claim semantic understanding from cuts.
- Offline/model absent: manual recipe review/apply works with no external accounts.
- Malformed/oversized/remote references and executable metadata are refused; no external
  writes/network activity; cancellation stops workers and marks partial findings as draft.
- Portability preserves supported abstract properties and explicitly reports omitted
  licensed media. Reimport does not replace source or silently change approved recipes.

All R1–R6 acceptance requirements are enumerated by ID in
[REFERENCE_STYLE_ACCEPTANCE_MATRIX.md](REFERENCE_STYLE_ACCEPTANCE_MATRIX.md). The scenarios
above map to that register; they do not independently authorize work. Any new criterion
must add its prerequisite, fixture, evidence, failure outcome and approval authority.

## 13. Independent recipe persistence and dependency contract

Concrete manual-R1 draft companions: [record contracts](G1_STYLE_RECORD_CONTRACTS.md),
[canonical vectors](G1_CANONICAL_TEST_VECTORS.md) and
[persistence protocol](G1_PERSISTENCE_PROTOCOL.md). Independent verification pending;
no G1 acceptance or R1 implementation authorization. These refine this section's
proposals for review; any conflict blocks acceptance rather than silently taking priority.
In the concrete shape, parent_revision_id is represented by a hash-pinned parent Ref,
schema version is bound by format (and explicit recipe schema_version), and draft/review
status is derived from immutable records/events, never an editable approval field.

Proposed identities: `recipe_id` (stable logical recipe), `revision_id` (unique immutable
revision), explicit `schema_version`, canonical payload hash and `parent_revision_id`.
Names are labels, not identities. The proposed recipe canonicalization is UTF-8 without
BOM/trailing newline, recursive object keys sorted by Unicode scalar value, unchanged
array order, no insignificant whitespace, unescaped non-ASCII scalars, JSON-required
quote/backslash/control escaping, and SHA-256 over those bytes. Reject duplicate keys,
lone surrogates, non-finite values and raw floating-point numbers. JSON integer fields
are signed 64-bit; fractional recipe parameters use typed decimal strings plus units,
without exponent/leading plus/leading zeros/trailing fractional zeros or negative zero
(examples: "0.65", "-1.5", "0"). This is the recipe-specific canonical contract, not a
change to creative@1 or a claim of RFC 8785 compliance. Format input explicitly before
review; never normalize approved Unicode wording or round values during load/hash.
Escape quote/backslash as \" and \\, backspace/tab/newline/form-feed/carriage-return
as \b/\t/\n/\f/\r, and other U+0000–001F controls as lowercase four-digit \u escapes;
do not escape solidus or other valid Unicode scalars. Example input keys b then a with
values "తెలుగు" and "0.65" canonicalize to {"a":"0.65","b":"తెలుగు"}.
Hash the full payload INCLUDING pinned dependency manifest; self hash and separate review
events are excluded. R1-A must use these rules and frozen control/Unicode/number vectors
so independent readers produce the same bytes. Any rule change needs a schema revision.

Approved revision payloads and their dependency manifests are immutable. An edit forks
a new draft revision with a parent link. Approval is a separate append-only review event
that identifies revision/hash, reviewer, time and scope. This is integrity checking, not
a claim that plain files or reviewer labels provide cryptographic authentication.
R1 is single local writer; actor authority is the explicitly confirming user. Shared
editing/authentication would require a separate security/identity contract.

Project dependency records pin recipe_id/revision_id/hash/schema_version, brand-profile
identity/version/hash, reference hashes/rights-record IDs, font hashes, extractor version
and parameters, required capabilities, render-profile and renderer identities. A project
keeps an immutable local recipe snapshot; a library link is optional and cannot override
it. Snapshot equality is verified on import. Updating a library is an explicit new
project dependency revision and must preview its effect. No implicit upgrade to latest.

Do not insert these fields into creative@1. Approve a versioned project-dependency
manifest/operation-provenance contract at G1 before R1, and an atomic integration contract
before R3. The manifest identifies dependencies, not hidden alternative creative layers.
The current core/renderer are not changed by this design correction.

Validate on load/save/approve/apply. Use staged sibling writes, flush/atomic replacement
where supported and a retained previous valid draft; approved revision artifacts are
write-once by the application. Use a single-writer lock plus expected revision/hash;
conflict creates no overwrite. A crash between payload and review-event writes must
resolve to a valid draft or a fully hash-matched approved revision, never false approval.
Recovery is explicit, preserves corrupt bytes, reports missing dependencies and never
silently changes recipe state. R1 tests both interruption points and disk-full errors.
R1 manual recipe JSON is also untrusted: cap encoded input at 1 MiB, nesting at 32 and
properties at 500 before accepting it; reject non-JSON executable serialization, links,
unsupported versions and duplicate keys. R1 must not decode embedded media or resolve
remote reference locations. Future limits require explicit scope review.

Availability, permissions and current eligibility are separate append-only dependency
events. Missing/changed fonts or reference bytes, revoked/expired rights, applicable
adverse brand changes, unsupported capabilities or changed renderer/extractor do not
rewrite history. They mark affected current analysis/application/production eligibility
stale or blocked through dependency edges. A new brand version alone is not an adverse
event; classify it under the brand-change rules in section 14 before deciding its effect.
Existing export bytes remain immutable, but must not be
presented as newly cleared for publication. Rights restoration or dependency substitution
requires an explicit reviewed event/new revision, not automatic reactivation of approval.

## 14. Compatibility, migration and historical reproducibility

Version recipes independently of creative@1. Opening is read-only validation, not
migration. Unknown newer major schemas/required features are refused for editing/apply;
raw original bytes may be preserved/exported with a clear unsupported-format message.
No unsafe partial load. An older supported revision opens using its original schema
and interpretation. An explicit migration writes a NEW revision/artifact, preserves the
original bytes/hash and records source/target schema plus migration-tool version/hash.
No migration edits an approved historical recipe or transfers approval automatically.

Font change: retain the old font bytes/metrics; substitution is a new dependency revision
with visual review. Renderer/profile change: keep original identity and resource closure
for historical replay; new output requires parity testing and a new render approval.
Brand-profile changes: brand-version snapshots are immutable. A/B review (B is the
designated brand/rights authority, defaulting to A) explicitly classifies each change
and its affected dependency pins in retained review evidence; unknown classification
blocks affected use pending review, rather than assuming benign. Distinguish:

- Benign addition: an optional logo variant, font or palette choice that changes no
  applicable restriction or existing resource permission. Existing projects keep their
  pinned version and current approvals; merely adding a version causes no invalidation.
- Adverse hard-rule change: a mandatory logo restriction, prohibited color or changed
  protection rule. The authority identifies whether it applies to existing pins or
  only future adoption. For affected existing pins, commit a DependencyEvent with state
  stale (review required) or revoked (known prohibition) against each exact kind-brand
  Dependency before acknowledging the change as processed. Until reassessed, affected
  application/approval/export is blocked; a pinned old version cannot bypass an
  applicable hard restriction. Unsupported enforcement remains blocked.
- Adverse rights change: revoked/withdrawn permission or expiry blocks affected use
  immediately when known/effective, including old pins. Use the existing RightsDecision
  deny/revoke chain and affected DependencyEvents revoked/expired; time-based expiry
  also blocks at evaluation without waiting for an event. No review grace period.

Record classification, authority, reason, applicability and affected pins in review
evidence and event reasons; do not invent a new schema or silently change Brand bytes.
Persist all identified adverse dependency events before reporting the change fully
processed. If persistence or scope determination fails, refuse affected current use
and report the incomplete invalidation; do not leave a successful/cleared UI state.
Invalidation follows affected dependency edges to Findings, Recipes and associated
outputs under G1 section 6.1, not blanket invalidation of unrelated project work. If an
output requires a blocked dependency, that output stays blocked. Historical approved
projects/exports retain their original bytes and identities, not renewed publication
permission. Restoration requires fresh ordered reviews; no automatic reactivation.

Explicit version adoption is separate: user choice creates a new project dependency/
association revision pinning the new immutable snapshot and reassesses affected
approvals. It never repoints an old pin, edits approved history or silently migrates
creative@1. Actual project integration remains separately gated at R3 and beyond;
this clarification authorizes neither implementation nor migration.
Extractor/capability change: keep original observations/parameters; reanalysis creates
new findings/revision and does not relabel old guesses as measurements. Unsupported
required properties block application; optional exclusions require reviewed new plans.

Historical approved recipes remain identifiable by immutable revision/hash and approval
event. Reproduction is conditional on legal access to pinned dependencies and a supported
original interpreter/renderer environment. If available, replay the original closure;
if missing, report exactly what cannot be reproduced. Do not claim reproducibility from
hashes alone or quietly use a replacement. Distinguish byte identity, decoded pixel
identity and declared behavior equivalence in evidence. Rights limits are not bypassed
to retain or replay unavailable components.

At adoption, retain legally permitted source/build/resource closure and notices under
the project inventory policy. The strategy in ../OFFLINE_BUILD_STRATEGY.md and G7 remains
the independent install/rebuild/recovery gate; successful disconnected runtime is not
that gate. Every phase records closure gaps. No missing closure is silently declared
complete; temporary prototypes must remain labeled and separately authorized.

## 15. Untrusted reference security and failure boundary

BEFORE R2 automated decoding, approve and demonstrate a dedicated worker boundary.
The Phase 2 synthetic renderer, its whole-workspace write policy, readable user files
and nested-sandbox workaround are NOT accepted as this boundary. Installed does not mean
safe to expose to untrusted media. No decoder/plugin runs in the project/editor process.

Required controls: immutable validated input copies or read-only handles, no path/URL
chosen by AI, no remote protocols/delegates or automatic first-run downloads, bounded
header parsing and decoder subprocesses. Verify signature/format matches; reject links,
traversal, devices, FIFOs, archives and unsupported content. SVG/scripts/documents are
not accepted by the first image-analysis slice. Treat EXIF/text/embedded instructions as
untrusted data. Color/orientation interpretation must be explicit and recorded.

Worker reads: only the selected inputs, pinned tools/libraries and declared job resources.
Worker writes: only its unique job staging directory; no project-source, other-job,
production, Reel Studio_dev, home, model cache, venv or global-install writes. Prevent
symlink/hard-link escapes and path-check/open races using approved handle-based or OS
isolation controls. Environment variables, Python audit hooks and sampling alone do
not prove this isolation. Deny outbound networking and unneeded local IPC; any essential
IPC exception must be narrow, documented and tested. No unrestricted file picker path
becomes permission for the worker to enumerate unrelated files.

Initial enforced R2 envelope, subject to design verification: PNG only, one input/job,
10 MiB encoded, maximum 8192 pixels per edge and 16,777,216 decoded pixels; analysis
output at most 2048 pixels per edge; at most 1 GiB worker memory, 15 s wall time,
60 s total job deadline and 128 MiB temporary output. Reject excess before full decode
where possible and enforce memory/output/time limits during decode, including misleading
headers and decompression bombs. If the chosen OS/runtime cannot enforce a bound, R2
stays blocked; sampled telemetry alone is not enforcement. Expansion needs approval.

Initial R4 envelope: at most three references, processed serially under per-input R2
bounds; aggregate job deadline 180 s and 384 MiB staging, not three concurrent decoders.
Initial R5 envelope: one explicitly selected local clip, 100 MiB encoded, 60 s, at most
3840x2160 source frames, 120 decoded frames/s and 7200 decoded frames; analysis samples
at most 120 frames downscaled to 1280x720. Worker memory 2 GiB, wall deadline 120 s,
512 MiB staging; variable frame rate uses actual timestamp/timebase checks. Unsupported
containers/codecs remain blocked until an exact allowlist and decoder audit are approved
before R5 starts. No whole-clip decoding into memory or invented constant-frame timing.
R6 must propose its own enforced model/resource envelope before approval; none is assumed.

Cancel/timeout/resource failure terminates the entire job process tree. No partial
results become approved or applied; retain explicitly labeled draft findings only on
user choice. Verify workers stopped, close handles and clean only job-owned temporary
files. Cleanup failure quarantines that job, reports retained bytes and blocks reuse;
never deletes the reference/original project. Disk-full/permission errors preserve the
last valid recipe/project and produce no successful export manifest.

Stale preview (recipe/reference/brand/font/profile/revision changed): refuse Apply and
rebuild a draft preview, preserving edits/corrections. Missing font/asset/capability:
block affected apply/export; offer explicit substitution/exclusion for review, never
fallback silently. Worker crash/malformed result: reject result schema, preserve source
and report failed stage/retryability. Retry is bounded, user-visible and starts a fresh
job; it does not loop on malicious input. No-network/model-unavailable paths preserve
manual R1 use. Error logs redact secrets/private content and record safe IDs/hashes.

## 16. Documentation verification and authorization

Corrections only are authorized. All R1–R6 states remain NOT AUTHORIZED. Next is a
separate read-only verification of this spec, the universal spec and the acceptance
register. That review must check traceability completeness and no dependency cycles,
compatible contracts, hard-rule conjunction and the safety envelope. An engineering
self-check of document links/IDs is not user design acceptance.

Only after that verification may the user consider a separately bounded R1 authorization
for structured MANUAL recipe authoring. R2–R6 each need their own prerequisite/exit
evidence and explicit user approval. No creative@1 change, M4 action, dependency install,
source acquisition or integration is included in this documentation task.
