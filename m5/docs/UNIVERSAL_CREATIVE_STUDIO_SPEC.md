# AI Reel Studio — universal Creative Studio architecture and UI specification

Revision: design draft 3, 2026-11-10. DESIGN REVIEW PENDING; documentation corrections only.
Independent read-only verification of corrected contracts is pending; no implementation approval.
Scope: product direction across industries; no accepted milestone is renumbered or
replaced. PROJECT_ENGINEERING_POLICY.md governs all adoption and implementation.

## 1. Product contract and present capability

Simple on the surface; intelligent underneath; professional control when needed.
The studio supports beginners, professional designers and repeat brand/campaign work
through one project, not separate incompatible applications. Industry profiles are
optional vocabulary, content and constraint aids, never separate template engines.

Verified existing evidence: Phase 1 recorded 37 core tests; Phase 2 recorded 55 total
tests and actual Chrome-rendered drafts, Sharp comparisons and calibration output.
Those historical logs are not newly rerun by this specification. Human Telugu/visual
acceptance, independent offline rebuild, editor implementation and M4 integration remain
open. Current renderer limits are in PHASE2_RENDER_CONTRACT.md and must remain visible
to implementation planning. No generalized professional renderer capability is implied.

The universal studio is the destination, not the claim of the current prototype.
Essential creation, editing, project storage, approvals and export must work offline
with manual/template fallback and without external accounts or mandatory paid services.

## 2. Experience levels and navigation

Quick Create: idea, optional materials, brand and destination; infer optional direction.
Guided Create: reveal purpose, audience, language, mood and composition when useful.
Professional Studio: direct object editing and contextual inspectors, timeline only for
supported reel workflows. Switching level changes UI density, not project meaning.
Every unsaved transaction, selection, variant and approval state survives mode switches.

Navigation: Home, Create, Projects, Brand Studio, Asset Library, Exports, Settings.
The Workspace contains the selected project and its views/versions. Do not add a second
brand editor or a separate format for professional-mode documents.

Desktop: left layers/assets tools; central aspect-correct canvas; right inspector;
bottom timeline only for supported reels. Top bar contains name, save state, undo/redo,
view/variant, preview, review and produce. AI refinements live in a collapsible panel.
At smaller widths inspectors become drawers; precision editing remains desktop-first.

## 3. Five primary Create decisions

1. Output: choose a supported deliverable, with campaign/custom outputs introduced later.
2. Idea: free text and/or files; voice input only once offline speech input is supported.
3. Brand: select a saved approved brand, start a draft brand, or explicitly choose none.
4. Direction: AI decides by default; optional guided controls, not a mandatory form.
5. Generate concepts: three distinct proposals, or open a blank/manual project.

Output size, language and platform are contextual summaries, editable beside the
relevant decision. Do not turn them into compulsory extra form pages. Unsupported
future features are absent from normal choices; an optional roadmap view can describe
them without a working-looking Generate/Export action.

## 4. Control taxonomy

This is the proposed full taxonomy. Labels/options are product design, not claims that
their underlying algorithms, codecs, fonts or models are installed. "Auto" always shows
the resolved choice before approval and can be overridden without losing the project.
Numeric precision uses fields/sliders; avoid pretending all controls are dropdowns.

### Create and brief

- Experience: Quick (default), Guided, Professional; remembers local preference.
- Deliverable: Poster; Reel; Poster + Reel; Carousel; Advertisement; Custom.
  Advertisement is a purpose preset with still/video subtypes, not a competing file type.
  Custom requires supported dimensions/features, not an arbitrary unlimited renderer.
- Start from: Idea (default), Blank, Saved template, Existing project, Approved variant.
- Input methods: text/files initially; optional voice and URL capture in later gates.
- Purpose: Auto, Announce, Promote, Explain, Inform, Invite, Celebrate, Recruit,
  Raise awareness, Showcase, Other (free text).
- Audience: Auto, General, Customers, Community, Professionals, Students/families,
  Event guests, Custom. Geography, age range and cultural context are optional text.
- Desired action: Auto, Learn more, Visit, Register, Book, Contact, Buy, Share,
  Attend, No action, Custom. Do not invent contact details or destinations.
- Domain: Auto, Food/hospitality, Sport, Health/wellbeing, Education, Property,
  Events/weddings, Entertainment, Technology, Retail/services, Community, Personal,
  Other. Domain changes suggestions, never factual authority.
- Brand: Recent approved brands, Draft brand, New brand, No brand.
- Language: Telugu, English, Separate Telugu/English variants; additional languages
  only after their font/shaping tests. No default automatic translation of approved text.
- Destination: General digital, Instagram, YouTube, Facebook, Custom digital;
  other social profiles, print and presentation outputs require separate accepted profiles.
- Aspect: Auto from destination, 1:1, 4:5, 9:16, 16:9, Custom supported dimensions.
  Current renderer only exposes its tested dimensions/pixel budget until expanded.
- Reel duration: Auto, Short, Standard, Custom supported seconds; actual durations
  resolve to validated frame counts. Disabled until reel integration is accepted.

### Creative direction (collapsed in Quick)

- Art direction: AI decides, Editorial, Minimal, Cinematic, Bold graphic,
  Documentary, Photographic, Illustrative, Typographic, Custom brief.
- Mood: Auto, Calm, Warm, Celebratory, Energetic, Serious, Elegant, Playful, Dramatic.
- Composition: Auto, Type-led, Image-led, Split, Grid, Central focus, Asymmetric,
  Frame/border, Reference-guided. These are structural intents, not fixed templates.
- Density: Spacious, Balanced (default), Information-rich. Never reduce legibility
  below a hard minimum to fit extra material.
- Color direction: Brand default, Light, Dark, Accent-led, Monochrome, Custom permitted
  palette. No option relaxes hard brand rules or contrast requirements.
- Typography direction: Brand pair (default), Display-led, Editorial, Geometric,
  Humanist, Custom approved pair; actual choices come from available licensed fonts.
- Image approach: Use supplied assets (default), Graphic-only, Approved library,
  Original generated imagery (future optional). Never imply an image model is available.
- Reference intent, per reference: Extract identity, Follow composition, Editable
  starting point, Broad inspiration only. Exact composition reuse requires rights.
- Variation scope: Composition, Type hierarchy, Color treatment, Asset treatment,
  Motion; choose individually. Protected content remains fixed.
- Creative preferences: Low/medium/high variation applies to soft preferences only;
  no global "brand strength" control can override logo, content or rights constraints.

### Selected-object inspector

- All objects: name, view, position/size, lock, visibility, paint order, opacity,
  alignment/distribution, duplicate/remove; preserve asset/content bindings.
- Text: source binding, language, approved font/fallback, available weight, size,
  explicit lines; later tracking, leading, alignment and text-on-path after acceptance.
- Shapes/vectors: supported primitive, dimensions, permitted fill/stroke and thickness;
  later gradients, path editing, masks, corner controls and effects.
- Logo: approved variant, proportional size, clear space, allowed placement;
  no free recolor/distortion unless the brand explicitly defines that variant.
- Photograph/product/subject: fit/crop/focal point; later masks, background separation,
  exposure and grading. Identity/face protection is a separate invariant.
- Effects: None initially; later Shadow, Glow, Grain, Texture, Depth with bounded
  numeric controls. Each effect requires a renderer capability and export test.
- Scene/motion: duration, entry/exit preset, easing, supported transform properties;
  keyframe editor only when persistence/render parity are accepted.
- Audio: source, timing, gain, fade, ducking and loudness; advanced tools deferred to
  separately accepted engine capabilities. No voice imitation or unsolicited generation.
- Export: supported format, dimensions, color space, background/alpha and quality;
  fps/codec/audio options only for accepted reel jobs. Print settings are separate.

## 5. Brief intelligence and question rules

Resolve purpose/action, message/hierarchy, audience/culture, available materials,
visual direction and destination. Store whether each field was user-specified,
inferred, derived from an approved brand, or unresolved. Do not show guesses as facts.

Ask only when omission blocks a credible or safe result: an event's date/location,
an unspecified offer, ambiguous target brand, missing critical logo, conflicting rights,
unresolved mandatory text or unknown destination constraints. Group questions, normally
at most three at once. Optional aesthetic ambiguity produces labeled assumptions and
editable previews rather than an interview. Never infer a real factual claim from style.

Example: "Restaurant opening" may infer a welcoming direction, but not opening date,
address, discounts or certifications. Use clearly identified placeholders or ask.
Health/property/finance-related claims stay unresolved until supported/approved; domain
classification does not make the system an expert fact-verifier.

## 6. Brand Studio and asset intelligence

Brand Studio sections:
- Identity: name, owner, audience, language, approved logos and usage contexts.
- Tokens: semantic colors, font pairs/scales, spacing, safe margins and backgrounds.
- Assets: searchable originals, variants, project-local snapshots and rights records.
- Rules: mandatory/optional/prohibited; clear space, minimum size, sponsor relationships,
  logo geometry, allowed crops, exact text and unsupported content constraints.
- Preferences: mood, composition, imagery and motion guidance that can vary by campaign.
- Templates/references: explicit intent, reusable components and layout constraints.
- Motion/audio: approved sources and future presets; optional until engine acceptance.
- Output presets: supported destinations, geometry, safe areas and quality defaults.
- Review/history: proposed changes, approval, immutable profile versions and affected jobs.

Separate four asset dimensions instead of one ambiguous "role":
1. Origin: user upload, source footage, brand library, template, generated, reference.
2. Intended use: production element, identity reference, composition reference,
   style inspiration, motion/audio source; multiple roles can coexist.
3. Mutability: protected original, allowed crop/transform, editable derivative, locked
   approved variant. Keep the original bytes; edits create a new derived asset.
4. Rights/review: owner/license/provenance, permissions/expiry, likeness consent where
   applicable, review status and permitted destinations. Unknown rights are not assumed.

Real-person assets carry identity-protection flags; crop/mask/background edits must
preserve identity. Any future exception requires explicit authorization and review.
Logo protection is independent from whether its file is SVG or a raster image.

The Brand Kit Wizard proposes a profile and evidence links; the user approves it.
Automatic extraction is a future feature, not prerequisite for manually entering a kit.
Text/reference content is untrusted input, never executable instructions to the agent.
No upload silently trains a model, enables a cloud service or overwrites an approved kit.

Rights, identity, protected content and all hard brand rules are simultaneous constraints,
not a priority list that allows one to be sacrificed for another. Capabilities/resource
limits must also pass: an unsupported required element blocks application/export and
cannot be omitted to satisfy a renderer. Only soft preferences use ranked precedence.
Hard rules block invalid operations and final exports. Preferences guide proposals.
A conflict cannot be resolved by silently weakening a hard rule. An authorized owner
may create a new explicitly reviewed brand-profile version; existing exports retain
their original profile hashes. Profile updates never propagate silently into old work.

## 7. Three-concept contract and creative critique

Each concept contains composition, type hierarchy, palette, asset plan, approved-content
bindings, rationale, production feasibility and unresolved items. Materially differ on
at least two of composition, type hierarchy or asset treatment; recoloring is insufficient.
Use separate structured scene proposals, not pictures with noneditable baked-in text.

Concept validation order: rights/protected identity -> content/source bindings -> hard
brand rules -> render capability/resource budget -> typography/safe areas -> soft style.
Draft previews may exist before final approval; clearly label unresolved placeholders.
Reject unsupported features rather than approximate them silently.

Rule-based critique first: completeness, overflow/line collisions, margins, image
resolution, logo geometry, contrast, mandatory assets and destination constraints.
Explain measurements and context; do not claim a universal numeric "design quality"
score. Human comparison covers originality, appropriateness, tone and hierarchy.
Optional future vision critique proposes changes only; it cannot auto-apply them.

Manual and deterministic paths work with AI unavailable. The local planner gets typed
IDs and bounded operations, not permission to modify files, fetch URLs or run commands.
Retries are bounded; failure leads to a useful fallback and an explanation.

## 8. Workspace interaction contract

Select an object to reveal relevant tools. Canvas selection and layers selection stay
synchronized. Locked objects are inspectable but not accidentally editable. Multi-select
exposes common properties only; mixed values are shown as mixed, not guessed.
Dragging groups previews; commit one reversible transaction on drop. Escape cancels;
failed validation restores the original state with a focused explanation.

Keyboard: undo/redo, delete subject to locks/rules, arrow nudges and explicit duplicate.
Provide keyboard-accessible layer navigation and numeric controls for precise edits.
Do not intercept shortcuts while entering Telugu through IME. Commit a text operation
after composition ends; never store intermediate IME fragments as separate approvals.

Changing shared content shows affected views/outputs before commit. Deliberate unlinking
creates a new content binding and is reversible; it never changes the original quote.
Typography changes preview with actual fonts. Font substitution or unsupported export
requires an explicit decision, never silently changes the approved appearance.

Conversational editing acts on the selection by default; ambiguous targets require
clarification. Show a before/after diff, affected outputs, rules and content changes.
Apply/Discard is explicit; one applied proposal is one reversible transaction.
Protected facts/quotes/identities cannot be changed through generic style requests.

Named variants are deliberate snapshots/branches. Mode switches do not fork variants.
Autosave preserves drafts; approvals reference immutable versions, not "latest".
Recovery must never mark a recovered older draft as currently approved.
Canonical creative-content/binding restoration is distinguished from whole-record byte
identity: revisions/audit/history may advance and affected approvals remain invalidated.
Atomic multi-operation editing/provenance is a future contract, not an existing core API.

## 9. Content and approval state model

Keep separate axes: document state, fact/source status, rights, brand compliance,
render QA and human approval. A rendered draft can pass geometry checks and still be
unapproved; a source-faithful quote need not be independently fact-verified.
Reference findings also separate origin/method, review, availability and confidence.
Approval cannot erase an observation's measured/inferred origin; reanalysis cannot
silently overwrite a human correction or its original evidence.

Content statuses: source-extracted, user-supplied, externally verified (with evidence and
date), unresolved, rejected. Review decisions name the reviewer and exact version.
User approval cannot relabel an unsupported claim as independently verified.
Creative text/translation review is distinct from fact and rights review.

Final readiness requires current content/rights/brand approvals, supported features,
passing QA and a render identity binding source, asset/font hashes, profile, renderer
and applicable destination. Editing any relevant input invalidates the affected approval.
Campaign outputs each retain readiness/export status; one passing poster does not
approve its reel or translated variant. Exports show exact source/version and QA.

## 10. Application and persistence architecture

Own the local project service, brief planner, brand/rule engine, asset metadata,
operation validator, review/export orchestration and renderer adapters. Reuse mature
canvas interaction, shaping, codecs, inference and media processing behind interfaces.
Local browser UI is the approved direction; backend/frontend packages remain subject
to scoped adoption and source-retention gates. No cloud service is essential.

Service boundaries: project/operations; brand/assets; brief/concepts; preview/render;
review/export. A separate worker runs renderer/media tasks in job-specific isolation.
The UI cannot call an unrestricted shell or direct native filesystem path supplied by AI.
Model/image and heavy-render jobs are scheduled to fit 24 GB, not launched in parallel
by default. SQLite may index folders, never replace them as project truth.

creative@1 remains authoritative for its existing creative content/layers/views/history.
It rejects unknown fields and does not support every proposed control. Do not append
gradients, masks, timelines, arbitrary typography options or new top-level keys silently.

Proposed future contracts, not implemented:
- Versioned brand-profile documents with explicit role/rule/provenance records.
- Versioned brief and concept records distinguishing inference from user decisions.
- Capability manifests for editor/renderer/engine and supported field semantics.
- Versioned portable project manifests and licensed asset closure.

Brand/brief sidecars have clear ownership and stable hashes. Any sidecar that changes
appearance/approval joins the render identity; it cannot become a hidden alternate
creative scene. A future schema version/migration requires a separate reviewed contract,
non-destructive conversion, unsupported-version refusal and golden-project regression.
Never use opaque sidecar data to bypass creative@1 validation.

Style Recipes are independently versioned. Approved revisions/dependency manifests are
immutable; working editors fork new draft revisions. Project dependency references pin
recipe ID, revision, schema and payload hash plus brand/reference/font/tool/capability
identities. Projects use immutable local snapshots, not floating library latest links.
Availability, revocation and current eligibility are recorded separately from historical
approval; they may block new use without rewriting approved historical bytes.
Opening old data never silently migrates or substitutes dependencies. An explicit
migration writes a new revision and requires review; original schemas/resources remain
identifiable and replayable where lawful pinned dependencies are available. Missing
closure is reported, never described as reproducible. See Reference spec sections 13–14.

Before any untrusted automated reference decode, accept the dedicated job-only write,
least-privilege read, no-network and enforced resource boundary in Reference spec section
15. The current synthetic Phase 2 renderer is not that security boundary. Environment
variables, sampled memory and Python hooks alone do not establish native-worker isolation.

## 11. Open-source dependency assessment (research only)

Penpot: useful architectural reference for tokens, components, variants and libraries.
Its repository declares MPL-2.0; copying covered code entails license/source duties
for covered files. Do not embed/fork the complete product or adopt its full hosted
application stack for this local foundation. Pin/audit specific files and dependencies
only if a future proposal justifies reuse. Local installation and offline rebuild on
this Mac have not been established. Sources:
https://github.com/penpot/penpot
https://raw.githubusercontent.com/penpot/penpot/develop/LICENSE
https://help.penpot.app/user-guide/design-systems/
https://help.penpot.app/technical-guide/getting-started/

MLT: a multimedia framework with plugin/filter/transition composition. Repository
COPYING contains LGPL-2.1; individual files/modules/build options and native dependencies
need separate inspection before any exact SPDX/redistribution claim for a shipped build.
Defer it: a second media engine does not justify disturbing FFmpeg/HyperFrames. No local
arm64 capability, memory performance or offline build was verified. Sources:
https://github.com/mltframework/mlt
https://raw.githubusercontent.com/mltframework/mlt/master/COPYING
https://www.mltframework.org/docs/

Fabric remains the provisional primary editor, subject to Telugu IME/caret/shaping and
preview/export tests. Konva remains fallback. Neither becomes the document format.
Polotno is a separately commercial SDK; Konva's MIT terms do not grant rights to it.
Exclude mandatory Polotno adoption under the zero-cost policy. Sources:
https://github.com/fabricjs/fabric.js
https://github.com/konvajs/konva
https://polotno.com/sdk/pricing

resvg remains a static SVG candidate (MIT OR Apache-2.0), not an animation engine.
Chrome/Puppeteer and Sharp remain temporary prototype tools with known parity,
isolation and dependency-ownership limits. Reuse the existing accepted FFmpeg/HyperFrames
engine through a future approved adapter. Sources and details:
https://github.com/linebender/resvg
PHASE2_RENDER_CONTRACT.md, ../THIRD_PARTY_INVENTORY.md, ../OFFLINE_BUILD_STRATEGY.md.

All candidates need exact version/commit/hash, native/transitive/license/security audit,
retained source/build inputs, measured hardware feasibility and replacement strategy
before adoption. No repository, model, package or third-party code was acquired for
this specification. No new candidate is approved or installed by this design.

## 12. Capability and implementation gates

G0 — Design review: approve/change this specification, first-release boundaries and
navigation. Review existing poster drafts and Telugu calibration separately. No code.

G1 — Brand/asset/brief contracts: approve the minimal data model and synthetic fixtures,
hard/soft rules, permissions and source manifest. Manual brand entry first; automatic
brand extraction/vision is deferred. Specify whether creative@1 suffices or a future
version is needed before implementing new fields.
Include independently versioned recipe/dependency and eventual atomic transaction
contracts. Contract approval does not authorize changing creative@1 or implementing R1.
The manual-R1 subset now has draft concrete contracts in
[G1_STYLE_RECORD_CONTRACTS.md](G1_STYLE_RECORD_CONTRACTS.md),
[G1_CANONICAL_TEST_VECTORS.md](G1_CANONICAL_TEST_VECTORS.md) and
[G1_PERSISTENCE_PROTOCOL.md](G1_PERSISTENCE_PROTOCOL.md).
These await independent read-only verification and user acceptance; broader G1 and
later-phase contracts remain scoped by their own entry requirements. R1 is not authorized.

G2 — Minimal editing slice: choose exactly one canvas library after its license/source
closure proposal. Prove Telugu IME, caret/selection, shaping, explicit line editing,
undo/redo, save/reopen and renderer parity. Implement only supported current controls.
Any install/acquisition is separately authorized. No gradients/masks/timeline promises.

G3 — Brief-to-concepts: implement typed brief resolution, three structurally different
concepts, deterministic checks, preview/apply/discard and model-off fallback. Local model
service use must not disturb the other M4 agent. No additional model assumed.

G4 — Universal workflow integration: connect Create, Brand Studio, Workspace, Review
and Exports; approve recovery/accessibility/usability on real tasks. Add supported media
and richer typography/effects through separate capability/schema gates.

G5 — Shared poster/reel adapter: only after full M4 acceptance, identified source
baseline, authorized source manifest and compatibility plan. Preserve reel_002 and both
approval gates; test in isolated copied jobs. No engine replacement or production swap.

G6 — Campaigns/advanced outputs: carousel sequencing, multi-size recomposition, linked
variants, multilingual expansion, motion presets and project portability, each with its
own acceptance. Print/PDF-X/CMYK, new codecs and 4K video need specific separate gates.

G7 — Independent distribution: authorized retained dependency closure, clean offline
install/rebuild/recovery, license bundle, stronger job/read isolation and regression.
No mandatory dependency on a global app's private packages or external licensing server.

These are feature gates, not replacements for the existing milestone roadmap. G1/G2
can be planned next after review; no implementation gate is opened by this document.
Reference phase dependencies are explicitly mapped in REFERENCE_STYLE_ACCEPTANCE_MATRIX.md:
R1 structured form needs G1 contracts, not G2 canvas; R2 needs accepted isolation;
R3 editor entry needs G2 and atomic provenance; R4 needs G3 only for automatic concepts
and G4 for full entry-point integration. R5 analysis alone never executes M4; actual
production requires G5/full M4 acceptance and separately approved isolated jobs.

## 13. Acceptance scenarios

Restaurant announcement: only supplied dates/address/offers; three distinct editable
concepts; logo remains intact; missing essential information prompts a focused question.
Sports sponsor poster: sponsor hierarchy/clear space cannot be weakened by energetic
style; approved logo variants only; unsupported effects refused, not silently flattened.
Community Telugu event: glyph/line/IME tests pass; translation is independently approved;
language switching preserves project and named versions.
Healthcare information: source/user-supplied/unresolved claims stay visibly distinct;
creative styling cannot invent a medical claim or imply independent verification.
Professional edit: selecting text reveals type tools, logo selection reveals approved
variants; undo restores source state; mode switches lose no edits or approval metadata.
Resize: a new view recomposes by constraints and previews every change; no automatic
cropping of protected faces/logos or silent endorsement of unreviewed new layout.
Offline/model unavailable: manual/template create/edit/save/preview/review/export still
work; any online fetch is explicit and optional; unavailable AI does not block projects.
Portability: a licensed project package restores pinned source/resources and reports
omitted assets/rights restrictions rather than silently substituting.

## 14. Decisions for user review

Approve the philosophy and three progressive control levels; one shared document and
workspace; hard rules separated from preferences; asset roles/rights/mutability model;
capability-based controls; own architecture with Penpot/MLT as reference/deferred only.
Choose first-release scope: recommend supported still posters, manual brand entry,
brief capture and a minimal editor before broad effects/campaign/video UI.
Confirm whether existing Phase 2 drafts/calibration are visually acceptable or need
specific typography/layout corrections. No automatic acceptance is inferred.
Separately authorize the next bounded implementation, any schema work and dependencies.

## 15. Reference Style Studio Pro

The detailed design in [REFERENCE_STYLE_STUDIO_SPEC.md](REFERENCE_STYLE_STUDIO_SPEC.md)
is part of this universal product specification. It defines one shared capability
available from Create, Brand Studio and the Editor; post-analysis multi-reference
mixing; editable evidence/confidence-aware findings; Locked/Guided/Free protection;
versioned portable Style Recipes; scoped reversible operations; and three-way comparison.

Reference dimensions can come from different sources, while hard brand rules, original
assets, identities and exact content stay protected. Overall influence affects only soft
transferable preferences. Poster/poster, poster/reel, reel/poster and reel/reel paths
are designed but capability-gated. Recipe approval is separate from final export approval.

The addendum introduces design gates R0–R6 linked to the existing G0–G7 roadmap; it does
not authorize a new milestone sequence, schema change or analyzer implementation.
Manual recipe authoring and installed-tool measurements precede optional vision models.
The M5 core/render prototype, M4 and production remain unchanged.

The [acceptance traceability register](REFERENCE_STYLE_ACCEPTANCE_MATRIX.md) assigns
every R1–R6 criterion its prerequisite, fixture, measurable evidence, failure outcome
and approval authority. It incorporates compatibility/migration, historical identity,
dedicated decoding security and failure/recovery rules from the reference specification.
All criteria remain unexecuted/not authorized. The user sequence is documentation
corrections -> separate read-only design verification -> possible bounded manual R1
authorization -> separate R2–R6 authorizations after their prerequisite/exit evidence.
No documentation self-check advances a gate or approves implementation.

No application code, creative schema, assets, tests, installed tools, M4 or production
files were changed for this specification. This draft is documentation only.
