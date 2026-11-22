# IDEAFRAME M5 — master engineering handover

**M5 IN_PROGRESS. Preservation only; no new product functionality or integration.**

- [A. Executive summary](#a-executive-summary)
- [B. Original requirements and traceability](#b-original-requirements-and-traceability)
- [C. Architecture and data flow](#c-architecture-and-data-flow)
- [D. Implemented modules and exact APIs](#d-implemented-modules-and-exact-apis)
- [E. Protected interfaces and compatibility](#e-protected-interfaces-and-compatibility)
- [F. Security, dependencies and licensing](#f-security-dependencies-and-licensing)
- [G. Working journey and evidence scope](#g-working-journey-and-evidence-scope)
- [H. Missing functionality](#h-outstanding-requirements-and-acceptance-work)
- [I. Known issues](#i-known-issues-and-technical-debt)
- [J. Development history](#j-development-history-and-decisions)
- [K. Tests and verification](#k-tests-and-verification-evidence)
- [L. Restart and recovery](#l-restart-and-recovery)
- [M. Next development plan](#m-next-development-plan)

Source paths are relative to the original M5 root, or `source/` inside the package. Exact byte identities, API signatures/line numbers, evidence associations and external artifact pins are in the accompanying manifests. Protected R1 and private state are intentionally excluded; do not confuse a source checkpoint with full cold-machine restoration.

## A. Executive summary

IDEAFRAME (source retains the former AI Reel Studio name) aims at an offline-first, zero-mandatory-subscription, commercially suitable creative application for editable English/Telugu posters and eventually coordinated reels, brand/style/reference and localAI workflows. M5 owns the creative-document/editor/brand/director expansion; it must not replace the accepted FFmpeg/HyperFrames reel engine or silently couple to M4/M6/production.

**M5 IN_PROGRESS. Active feature work is paused for this preservation task.** Current supported journey:launch →Home/Create(Quick/Guided/Professional) →exact idea/brief →optional approved pinnedbrand →actual local HybridAI →three distinct supported poster proposals →review/select a separate editable draft →text/geometry/layout/BrandA →explicit media-v3 copy →qualified PNG logo/image editing →canonical-editautosave/UndoRedo →restart/reopen →draftSVG/PNG. The narrow latest smoke passed, not full product acceptance.

Not functional/fullyaccepted:PNGstacking/interleaving, conversational atomic editing and advanced inspector breadth; native Telugu IME/full accessibility/creative quality; generic external fonts/SVG/otherimages; R2reference/OCR/video and laterR3–R6; AI image generation; cinematicreel/poster-reeladapter; clean independent offline provisioning/distribution/licenseclosure and final production approval. Requirements remain explicit. Protected R1 content/evidence is deliberately excluded; its previously reported conditional acceptance is not independently re-audited here.

The next developer must verify both manifest and archive receipt, read the module/requirements/security maps, restore into a fresh approved working directory, check exact external artifacts without acquisition or migration, and start with the smallest explicitly authorized missing contract/function. Do not rerun AI/broad regressions merely to read this package. Historical NO-GO records are not erased; current code and associated evidence distinguish superseded scopes from still-blocked gates.

This is a byte-exact checkpoint of the listed authorized source, not a whole-machine/private-project/protected-R1 backup or self-contained installer. Modelweights/native runtimes/SDKs/private libraries/sessions/frozen checkpoint/other milestones are not copied. No external workspace is entered; only parent directory names were inventoried to seek Complete Modules. No destination was confirmed, no externalcopy attempted. Internal archive placement does not integrate or release M5.


## B. Original requirements and traceability
# M5 original requirements and traceability

Status vocabulary is exactly the seven classes in M5_STATUS_MANIFEST.json. COMPLETE AND VERIFIED is bounded to the cited profile/cases; historical tests are not a fresh full-source certification. Original broad taxonomy includes proposed/future capabilities: they remain visible and do not become approved implementation automatically.

| ID | Requirement | Classification | Source/spec | Source code | Evidence |
|---|---|---|---|---|---|
|M5-001|Authoritative editable creative documents|IMPLEMENTED BUT NOT FULLY VERIFIED|M5_HANDOFF.md; docs/ARCHITECTURE.md|creative_core/document.py; creative_core/validation.py; creative_core/operations.py; creative_core/persistence.py|core, sprint|
|M5-002|Layered SVG poster rendering|COMPLETE AND VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §7; docs/VISUAL_POSTER_HANDOFF.md|visual_poster_studio/scene.py; visual_poster_studio/app.js; studio_png_sandbox/unified.py|sprint, png-unified|
|M5-003|Draft local SVG and PNG export|COMPLETE AND VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §9; docs/PNG_UNIFIED_STUDIO_HANDOFF.md|visual_poster_studio/exports.py; visual_poster_studio/media_bridge.py; studio_png_sandbox/workflow.py|sprint, png-unified|
|M5-004|Quick Create|COMPLETE AND VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §2–5; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md|visual_poster_studio/product.py; visual_poster_studio/product.mjs|sprint|
|M5-005|Guided Create|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §2–5|visual_poster_studio/product.mjs; visual_poster_studio/product.py|sprint|
|M5-006|Professional Studio mode|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §2,8|visual_poster_studio/product.mjs; visual_poster_studio/app.js; visual_poster_studio/styles.css|sprint|
|M5-007|Home/Projects/Create/Brand/Editor navigation|COMPLETE AND VERIFIED|docs/M5_HOME_PROJECTS_HANDOFF.md; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md|visual_poster_studio/home.py; visual_poster_studio/home.mjs; visual_poster_studio/product.mjs|sprint|
|M5-008|Real local AI editorial interpretation|COMPLETE AND VERIFIED|docs/CREATIVE_DIRECTOR_PHASE2F.md; docs/CREATIVE_DIRECTOR_PHASE2G.md|visual_poster_studio/ai_hybrid.py; visual_poster_studio/hybrid_jobs.py|sprint, hybrid-f, hybrid-g|
|M5-009|Three structurally distinct editable concepts|COMPLETE AND VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §7; docs/CREATIVE_DIRECTOR_PHASE2F.md|visual_poster_studio/ai_hybrid.py; visual_poster_studio/ai_semantic.py; visual_poster_studio/ai_constrained.py|sprint, hybrid-f|
|M5-010|Concept comparison, selection and manual refinement|COMPLETE AND VERIFIED|docs/CREATIVE_DIRECTOR_PHASE2G.md|visual_poster_studio/hybrid.mjs; visual_poster_studio/director.mjs; visual_poster_studio/hybrid_jobs.py|sprint, hybrid-g|
|M5-011|Meaningful traceable rationales and creative critique|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §7; docs/CREATIVE_DIRECTOR_PHASE2F.md|visual_poster_studio/ai_hybrid.py; visual_poster_studio/brand_application.py|hybrid-f, sprint|
|M5-012|Progress, cancel, timeout, error and explicit fallback|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/CREATIVE_DIRECTOR_PHASE2G.md|visual_poster_studio/hybrid_jobs.py; visual_poster_studio/hybrid.mjs; visual_poster_studio/product.mjs|hybrid-g, sprint|
|M5-013|Multiple saved brand profiles and immutable approved versions|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/BRAND_ASSET_FOUNDATION_CONTRACT.md|visual_poster_studio/brands.py; visual_poster_studio/brands.mjs|brand, binding, sprint|
|M5-014|Asset identity, provenance, rights scope and expiry|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/BRAND_ASSET_FOUNDATION_CONTRACT.md; docs/PNG_SANDBOX_HANDOFF.md|visual_poster_studio/brands.py; studio_png_sandbox/workflow.py|brand, png-workflow|
|M5-015|Brand-library backup, restore and portability|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/BRAND_LIBRARY_PORTABILITY_CONTRACT.md|visual_poster_studio/brand_portability.py; visual_poster_studio/brands.mjs|brand-portability|
|M5-016|Project binding and editable creative brief|COMPLETE AND VERIFIED|docs/PROJECT_BINDING_CONTRACT.md|visual_poster_studio/project_bindings.py; visual_poster_studio/binding_workflow.py|binding, sprint|
|M5-017|Explicit brand-version switching and adverse invalidation|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/PROJECT_BINDING_CONTRACT.md; docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §6|visual_poster_studio/binding_workflow.py; visual_poster_studio/app.js|binding, brand-a|
|M5-018|Brand Application A colors, supported typography, rules|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/BRAND_APPLICATION_A.md|visual_poster_studio/brand_application.py; visual_poster_studio/brand_application.mjs|brand-a, sprint|
|M5-019|Approved PNG logo/image placement|COMPLETE AND VERIFIED|docs/PNG_SANDBOX_HANDOFF.md; docs/PNG_UNIFIED_STUDIO_HANDOFF.md|studio_png_sandbox/controller.py; studio_png_sandbox/workflow.py; visual_poster_studio/media_bridge.py|png-security, png-workflow, sprint|
|M5-020|Unified PNG and base text/geometry editing|COMPLETE AND VERIFIED|docs/PNG_UNIFIED_STUDIO_HANDOFF.md|studio_png_sandbox/unified.py; visual_poster_studio/media.mjs; visual_poster_studio/app.js|png-unified, sprint|
|M5-021|Direct PNG positioning and proportional resizing|COMPLETE AND VERIFIED|docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md|visual_poster_studio/media_gestures.mjs; visual_poster_studio/media.mjs|sprint|
|M5-022|PNG stacking and base/media interleaving|BLOCKED BY SECURITY OR CONTRACT|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8; docs/M5_FUNCTIONAL_STATUS.json|studio_png_sandbox/unified.py; studio_png_sandbox/workflow.py; visual_poster_studio/media.mjs|sprint|
|M5-023|Core layer ordering and atomic geometry|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/VISUAL_REORDER_RESUME_CONTRACT.md; docs/VISUAL_GEOMETRY_HANDOFF.md|creative_core/operations.py; creative_core/validation.py; visual_poster_studio/geometry.mjs|geometry, resume|
|M5-024|Text alignment, wrapping, leading and fitting|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §4,8; docs/VISUAL_TEXT_COMPLETION_HANDOFF.md|visual_poster_studio/text_layout.mjs; visual_poster_studio/scene.py; visual_poster_studio/fonts.py|text, sprint|
|M5-025|English/Telugu exact Unicode editing and shaping|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/VISUAL_POSTER_HANDOFF.md; docs/VISUAL_TEXT_COMPLETION_HANDOFF.md|visual_poster_studio/fonts.py; visual_poster_studio/app.js; visual_poster_studio/product.py|sprint, text|
|M5-026|Native Telugu IME acceptance|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/VISUAL_TEXT_COMPLETION_HANDOFF.md; docs/M5_FUNCTIONAL_STATUS.json|visual_poster_studio/app.js; visual_poster_studio/product.mjs; visual_poster_studio/media_gestures.mjs|text|
|M5-027|Keyboard editing and full accessibility|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8; docs/M5_FUNCTIONAL_STATUS.json|visual_poster_studio/editing.mjs; visual_poster_studio/geometry.mjs; visual_poster_studio/media_gestures.mjs; visual_poster_studio/index.html|text, sprint|
|M5-028|Undo/Redo, autosave and read-only history|COMPLETE AND VERIFIED|docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md|visual_poster_studio/app.js; visual_poster_studio/product.py; studio_png_sandbox/unified.py|sprint|
|M5-029|Explicit session resume and crash-safe recovery|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/VISUAL_REORDER_RESUME_CONTRACT.md; docs/PROJECT_BINDING_CONTRACT.md; docs/PNG_UNIFIED_STUDIO_HANDOFF.md|visual_poster_studio/session.py; visual_poster_studio/recovery.py; visual_poster_studio/binding_recover.py; studio_png_sandbox/unified.py|resume, sprint, png-workflow|
|M5-030|Named variants, historical approvals and export records|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8–9|creative_core/operations.py; creative_core/validation.py; visual_poster_studio/exports.py|core, sprint|
|M5-031|Conversational editing with atomic diff/provenance|BLOCKED BY SECURITY OR CONTRACT|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8|visual_poster_studio/app.js; creative_core/operations.py|sprint|
|M5-032|Advanced inspector lock/visibility/opacity/duplicate/unlink/crop|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §4,8|creative_core/validation.py; studio_manual_ui/service.py; visual_poster_studio/app.js|sprint|
|M5-033|Reference Style manual R1|UNKNOWN / REQUIRES CONFIRMATION|docs/REFERENCE_STYLE_STUDIO_SPEC.md; protected R1 records excluded by instruction|No scoped implementation / protected exclusion|excluded-r1|
|M5-034|R2 synthetic report-contract conformance|NOT IMPLEMENTED|docs/R2_SAFE_DEVELOPMENT_ROADMAP.md; docs/R2_NEXT_AUTHORIZATION_MATRIX.md|docs/R2_REPORT_CONTRACT_PROPOSAL.md; docs/R2_CANONICAL_VECTOR_SPEC.md|r2-design|
|M5-035|Bounded reference image/poster analysis and English/Telugu OCR|BLOCKED BY SECURITY OR CONTRACT|docs/R2_IMAGE_ANALYSIS_SPEC.md; docs/R2_ARCHITECTURE_DECISION_RECORD.md|media_analysis_agent/backends.py; studio_media_workflow/containment.py|r2-design, agent|
|M5-036|Selective reference application, multi-reference mixing, video style|BLOCKED BY SECURITY OR CONTRACT|docs/REFERENCE_STYLE_STUDIO_SPEC.md; docs/REFERENCE_STYLE_ACCEPTANCE_MATRIX.md|No scoped implementation / protected exclusion|r2-design|
|M5-037|Independent optional media agent lifecycle|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/MEDIA_AGENT_COMPLETION_HANDOFF.md; docs/MEDIA_ANALYSIS_AGENT_HANDOFF.md|media_analysis_agent/controller.py; media_analysis_agent_v2/controller.py; media_analysis_agent_v2/packages.py|agent|
|M5-038|Local AI image generation|NOT IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §4; docs/M5_FUNCTIONAL_STATUS.json|No scoped implementation / protected exclusion|sprint|
|M5-039|Cinematic reel creation and poster/reel adaptation|BLOCKED BY SECURITY OR CONTRACT|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md G5; docs/M5_FUNCTIONAL_STATUS.json|No scoped implementation / protected exclusion|r2-design, sprint|
|M5-040|Expanded outputs, dimensions, carousel/campaign/custom|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §3–4, G6|visual_poster_studio/scene.py; poster_render/scene.py|phase2, sprint|
|M5-041|Final content/fact/brand/legal approval workflow|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §9|creative_core/operations.py; poster_render/approval.py; visual_poster_studio/exports.py|core, phase2|
|M5-042|Offline/local independence and no mandatory subscription|PARTIALLY IMPLEMENTED|PROJECT_ENGINEERING_POLICY.md; OFFLINE_BUILD_STRATEGY.md|tools/studio_local.py; visual_poster_studio/hybrid_jobs.py; studio_png_sandbox/controller.py|sprint, png-security|
|M5-043|Open-source/licensing/commercial distribution closure|PARTIALLY IMPLEMENTED|THIRD_PARTY_INVENTORY.md; docs/PNG_SANDBOX_DEPENDENCIES.json|docs/CREATIVE_DIRECTOR_PHASE2A.md; docs/CREATIVE_DIRECTOR_PHASE2D.md|dependency|
|M5-044|Production integration, engine modification and release|OUTSIDE M5 SCOPE|PROJECT_ENGINEERING_POLICY.md; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md|No scoped implementation / protected exclusion|sprint|
|M5-045|Frozen checkpoint and milestone isolation|COMPLETE AND VERIFIED|PROJECT_ENGINEERING_POLICY.md; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md|tools/studio_local.py|sprint|
|M5-046|Deterministic fallback when AI absent|IMPLEMENTED BUT NOT FULLY VERIFIED|docs/CREATIVE_DIRECTOR_PHASE1.md; docs/CREATIVE_DIRECTOR_PHASE2G.md|visual_poster_studio/director.py; visual_poster_studio/director.mjs; visual_poster_studio/product.mjs|hybrid-g, sprint|
|M5-047|Brand Kit Wizard and automatic extraction|NOT IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §6|No scoped implementation / protected exclusion|r2-design|
|M5-048|Source facts/claims, identity, logo and hard-rule protection|PARTIALLY IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §5–6|creative_core/operations.py; visual_poster_studio/brand_application.py; studio_png_sandbox/workflow.py|brand-a, png-workflow|
|M5-049|Recovery package and independent agent continuation|COMPLETE AND VERIFIED|Current handover instruction; docs/M5_MASTER_HANDOVER.md|M5_STATUS_MANIFEST.json|checkpoint|
|M5-050|Voice/URL input, advanced effects, motion/audio and print|NOT IMPLEMENTED|docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §3–4, G6|No scoped implementation / protected exclusion|r2-design|

## M5-001 — Authoritative editable creative documents

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: M5_HANDOFF.md; docs/ARCHITECTURE.md
- Current source: `creative_core/document.py`; `creative_core/validation.py`; `creative_core/operations.py`; `creative_core/persistence.py`
- Dependencies: python
- Verification: core, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Schema1 remains;37 original tests predate later additive history2/3. Do not claim the old run verifies current code in full.
- Acceptance criteria: Validate old and current histories without content reinterpretation; retain source-associated targeted evidence.

## M5-002 — Layered SVG poster rendering

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §7; docs/VISUAL_POSTER_HANDOFF.md
- Current source: `visual_poster_studio/scene.py`; `visual_poster_studio/app.js`; `studio_png_sandbox/unified.py`
- Dependencies: fonts, browser
- Verification: sprint, png-unified (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Verified only current1080×1350 supported primitives and restricted PNG overlays; not arbitrary vector/media imports.
- Acceptance criteria: Same-source deterministic SVG, safe paint order, bounds/font refusal and exact Unicode.

## M5-003 — Draft local SVG and PNG export

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §9; docs/PNG_UNIFIED_STUDIO_HANDOFF.md
- Current source: `visual_poster_studio/exports.py`; `visual_poster_studio/media_bridge.py`; `studio_png_sandbox/workflow.py`
- Dependencies: browser, png-runtime
- Verification: sprint, png-unified (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Draft-only; browser-side parity is not independent server rerender or final legal/brand approval.
- Acceptance criteria: Current rights, one-use15s handshake, exact SVG identity and same-browser decoded-RGBA parity.

## M5-004 — Quick Create

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §2–5; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md
- Current source: `visual_poster_studio/product.py`; `visual_poster_studio/product.mjs`
- Dependencies: python, sqlite
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Generic purpose/audience defaults are disclosed, not model-inferred facts;180-codepoint idea limit.
- Acceptance criteria: Create optional branded brief, launch explicit local AI, preserve exact headline and recorded defaults.

## M5-005 — Guided Create

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §2–5
- Current source: `visual_poster_studio/product.mjs`; `visual_poster_studio/product.py`
- Dependencies: python
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Same brief contract and additional instructions; not every proposed taxonomy control is implemented.
- Acceptance criteria: All guided fields round-trip; switching retains pending text; no mode-driven source migration.

## M5-006 — Professional Studio mode

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §2,8
- Current source: `visual_poster_studio/product.mjs`; `visual_poster_studio/app.js`; `visual_poster_studio/styles.css`
- Dependencies: browser
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: UI-density mode exposes existing controls, not the full proposed inspector taxonomy.
- Acceptance criteria: Same underlying project/history; keyboard and pointer access; preserve unapplied fields on mode changes.

## M5-007 — Home/Projects/Create/Brand/Editor navigation

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/M5_HOME_PROJECTS_HANDOFF.md; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md
- Current source: `visual_poster_studio/home.py`; `visual_poster_studio/home.mjs`; `visual_poster_studio/product.mjs`
- Dependencies: python, browser
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Recent sessions sorted by observed modification time, not actual last-opened history.
- Acceptance criteria: Continuous one-service journey; explicit session selection; empty/error/recovery states.

## M5-008 — Real local AI editorial interpretation

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/CREATIVE_DIRECTOR_PHASE2F.md; docs/CREATIVE_DIRECTOR_PHASE2G.md
- Current source: `visual_poster_studio/ai_hybrid.py`; `visual_poster_studio/hybrid_jobs.py`
- Dependencies: llama, model
- Verification: sprint, hybrid-f, hybrid-g (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Pinned Qwen3-14B CPU mode,96.7–103.9s latest; not general reasoning/creative-quality certification.
- Acceptance criteria: Actual model executes locally; strict output validation; interpretation never grants rights or replaces exact copy.

## M5-009 — Three structurally distinct editable concepts

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §7; docs/CREATIVE_DIRECTOR_PHASE2F.md
- Current source: `visual_poster_studio/ai_hybrid.py`; `visual_poster_studio/ai_semantic.py`; `visual_poster_studio/ai_constrained.py`
- Dependencies: model, fonts, browser
- Verification: sprint, hybrid-f (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Bounded top/middle/bottom two-role composition family; not unlimited AI art direction.
- Acceptance criteria: At least2 measured structural differences per pair; fit/bounds/brand/font checks;3 editable docs.

## M5-010 — Concept comparison, selection and manual refinement

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/CREATIVE_DIRECTOR_PHASE2G.md
- Current source: `visual_poster_studio/hybrid.mjs`; `visual_poster_studio/director.mjs`; `visual_poster_studio/hybrid_jobs.py`
- Dependencies: browser
- Verification: sprint, hybrid-g (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Comparison job state is process-local; selected drafts persist. Duplicate selection refuses rather than overwrites.
- Acceptance criteria: Rule acknowledgement, current source/pin/head recheck, new unapproved paired project; source unchanged.

## M5-011 — Meaningful traceable rationales and creative critique

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §7; docs/CREATIVE_DIRECTOR_PHASE2F.md
- Current source: `visual_poster_studio/ai_hybrid.py`; `visual_poster_studio/brand_application.py`
- Dependencies: model, fonts
- Verification: hybrid-f, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Rationales are application-authored layout facts linked to AI response. Broader originality/editorial/visual critique is human-review work.
- Acceptance criteria: Complete fact-derived explanation; no fabricated AI authorship or universal quality score; human creative approval.

## M5-012 — Progress, cancel, timeout, error and explicit fallback

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/CREATIVE_DIRECTOR_PHASE2G.md
- Current source: `visual_poster_studio/hybrid_jobs.py`; `visual_poster_studio/hybrid.mjs`; `visual_poster_studio/product.mjs`
- Dependencies: llama, python
- Verification: hybrid-g, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Latest smoke exercised progress/success; prior2G cancellation/timeout checks belong to historical identities. No machine-wide model concurrency quota.
- Acceptance criteria: TERM/KILL/reap/group absence; unconfirmed termination faults; no auto-retry; failed job publishes no project.

## M5-013 — Multiple saved brand profiles and immutable approved versions

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/BRAND_ASSET_FOUNDATION_CONTRACT.md
- Current source: `visual_poster_studio/brands.py`; `visual_poster_studio/brands.mjs`
- Dependencies: sqlite
- Verification: brand, binding, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Trusted-local reviewer labels; not authenticated legal ownership. No private library is packaged.
- Acceptance criteria: Append-only records, explicit revisions, approval pins assets/rights; restart and deny missing clearance.

## M5-014 — Asset identity, provenance, rights scope and expiry

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/BRAND_ASSET_FOUNDATION_CONTRACT.md; docs/PNG_SANDBOX_HANDOFF.md
- Current source: `visual_poster_studio/brands.py`; `studio_png_sandbox/workflow.py`
- Dependencies: sqlite, png-runtime
- Verification: brand, png-workflow (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Registration/hash is never permission; claims remain user assertions. Unknown/expired/revoked/insufficient scope deny.
- Acceptance criteria: Live checks before/after decode and under publication transaction; no permission resurrection after restore.

## M5-015 — Brand-library backup, restore and portability

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/BRAND_LIBRARY_PORTABILITY_CONTRACT.md
- Current source: `visual_poster_studio/brand_portability.py`; `visual_poster_studio/brands.mjs`
- Dependencies: sqlite, python
- Verification: brand-portability (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Separate trusted metadata package; not arbitrary hostile ZIP sandbox. Missing legal blob clearance yields explicit omission; imports may quarantine grants.
- Acceptance criteria: Whole-package integrity/lineage preview, stale-plan refusal, one SQLite transaction, immutable history retained.

## M5-016 — Project binding and editable creative brief

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/PROJECT_BINDING_CONTRACT.md
- Current source: `visual_poster_studio/project_bindings.py`; `visual_poster_studio/binding_workflow.py`
- Dependencies: sqlite, python
- Verification: binding, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Independent creative Undo does not revert binding revisions. Existing unbound projects remain valid.
- Acceptance criteria: One immutable document/binding pair publication, expected head/revision, exact Unicode, reopen same pair.

## M5-017 — Explicit brand-version switching and adverse invalidation

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/PROJECT_BINDING_CONTRACT.md; docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §6
- Current source: `visual_poster_studio/binding_workflow.py`; `visual_poster_studio/app.js`
- Dependencies: sqlite
- Verification: binding, brand-a (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Benign later versions do not migrate pins; mandatory-rule changes and current rights can block old use. Media-v3 binding is frozen/read-only.
- Acceptance criteria: Impact preview/confirmation, new paired revision, current approval clearing; historical records untouched.

## M5-018 — Brand Application A colors, supported typography, rules

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/BRAND_APPLICATION_A.md
- Current source: `visual_poster_studio/brand_application.py`; `visual_poster_studio/brand_application.mjs`
- Dependencies: fonts, sqlite
- Verification: brand-a, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Exact supported rule vocabulary only; unknown hard declarations refuse. Only InterBold/NotoTeluguBlack, no uploaded fonts.
- Acceptance criteria: Independent checks before generation/edit/render/export; palette constraints; no AI rule override.

## M5-019 — Approved PNG logo/image placement

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/PNG_SANDBOX_HANDOFF.md; docs/PNG_UNIFIED_STUDIO_HANDOFF.md
- Current source: `studio_png_sandbox/controller.py`; `studio_png_sandbox/workflow.py`; `visual_poster_studio/media_bridge.py`
- Dependencies: png-runtime, sqlite
- Verification: png-security, png-workflow, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Static noninterlaced RGB8/RGBA8 IHDR/IDAT/IEND only; no metadata/APNG/palette. Narrow smoke not all production inputs.
- Acceptance criteria: Qualified decode+hash+rights pins before publication; rejected media never enters ordinary rendering.

## M5-020 — Unified PNG and base text/geometry editing

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/PNG_UNIFIED_STUDIO_HANDOFF.md
- Current source: `studio_png_sandbox/unified.py`; `visual_poster_studio/media.mjs`; `visual_poster_studio/app.js`
- Dependencies: png-runtime, browser
- Verification: png-unified, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Explicit media-v3 copy required; no silent migration. Source manual project stays separate; brief/pin read-only in media copy.
- Acceptance criteria: Combined reversible timeline, editable core, PNG edit/save/reopen/export in main UI.

## M5-021 — Direct PNG positioning and proportional resizing

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md
- Current source: `visual_poster_studio/media_gestures.mjs`; `visual_poster_studio/media.mjs`
- Dependencies: browser, png-runtime
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Pointer movement/resize smoke passed; full keyboard/assistive acceptance remains separate.
- Acceptance criteria: Captured source head; one geometry transaction/drop; aspect ratio; Escape cancellation; stale rejection.

## M5-022 — PNG stacking and base/media interleaving

- Classification: BLOCKED BY SECURITY OR CONTRACT
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8; docs/M5_FUNCTIONAL_STATUS.json
- Current source: `studio_png_sandbox/unified.py`; `studio_png_sandbox/workflow.py`; `visual_poster_studio/media.mjs`
- Dependencies: versioned-media
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: v3 allows place/geometry/remove, not reorder. PNG overlays are above base. Do not fake reorder by identity replacement.
- Acceptance criteria: Explicit approved new envelope/transaction; complete permutation; one Undo; strict replay/old-reader rejection.

## M5-023 — Core layer ordering and atomic geometry

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/VISUAL_REORDER_RESUME_CONTRACT.md; docs/VISUAL_GEOMETRY_HANDOFF.md
- Current source: `creative_core/operations.py`; `creative_core/validation.py`; `visual_poster_studio/geometry.mjs`
- Dependencies: python, browser
- Verification: geometry, resume (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: History2/3 sticky; first upgrade needs explicit acknowledgement and verified checkpoint. Full older suites not rerun for package.
- Acceptance criteria: Complete same-view permutations/targets, current revision, atomic one-step undo/redo, no unauthorized deltas.

## M5-024 — Text alignment, wrapping, leading and fitting

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §4,8; docs/VISUAL_TEXT_COMPLETION_HANDOFF.md
- Current source: `visual_poster_studio/text_layout.mjs`; `visual_poster_studio/scene.py`; `visual_poster_studio/fonts.py`
- Dependencies: fonts, browser
- Verification: text, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Current text is left aligned,1.65× spacing; wrap inserts explicit newlines for review. Arbitrary leading/alignment/tracking not implemented.
- Acceptance criteria: Any future extension needs persisted/render-parity contract; current fit never silently changes approved copy.

## M5-025 — English/Telugu exact Unicode editing and shaping

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/VISUAL_POSTER_HANDOFF.md; docs/VISUAL_TEXT_COMPLETION_HANDOFF.md
- Current source: `visual_poster_studio/fonts.py`; `visual_poster_studio/app.js`; `visual_poster_studio/product.py`
- Dependencies: fonts, browser
- Verification: sprint, text (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Exact text and browser font probes pass; native speaker semantic/typographic acceptance is open.
- Acceptance criteria: Exact combining marks/script runs; no normalization/fallback; native visual approval and input-method checks.

## M5-026 — Native Telugu IME acceptance

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/VISUAL_TEXT_COMPLETION_HANDOFF.md; docs/M5_FUNCTIONAL_STATUS.json
- Current source: `visual_poster_studio/app.js`; `visual_poster_studio/product.mjs`; `visual_poster_studio/media_gestures.mjs`
- Dependencies: browser
- Verification: text (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Composition safeguards exist; no native Telugu OS IME acceptance was performed.
- Acceptance criteria: Real input method composition/candidate selection; no interim mutation/navigation shortcuts; save/reopen exact result.

## M5-027 — Keyboard editing and full accessibility

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8; docs/M5_FUNCTIONAL_STATUS.json
- Current source: `visual_poster_studio/editing.mjs`; `visual_poster_studio/geometry.mjs`; `visual_poster_studio/media_gestures.mjs`; `visual_poster_studio/index.html`
- Dependencies: browser
- Verification: text, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Core keyboard paths and labels exist; new PNG keyboard and full screen-reader/focus/contrast acceptance incomplete.
- Acceptance criteria: Keyboard-only complete journey, IME-safe shortcuts, focus restoration, assistive-technology review.

## M5-028 — Undo/Redo, autosave and read-only history

- Classification: COMPLETE AND VERIFIED
- Original specification: docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md
- Current source: `visual_poster_studio/app.js`; `visual_poster_studio/product.py`; `studio_png_sandbox/unified.py`
- Dependencies: python
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Autosave commits canonical operations only, not every raw text keystroke. Media timeline capped100; no automatic deletion.
- Acceptance criteria: One user operation per transaction; no approval resurrection; restart preserves current cursor and complete snapshots.

## M5-029 — Explicit session resume and crash-safe recovery

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/VISUAL_REORDER_RESUME_CONTRACT.md; docs/PROJECT_BINDING_CONTRACT.md; docs/PNG_UNIFIED_STUDIO_HANDOFF.md
- Current source: `visual_poster_studio/session.py`; `visual_poster_studio/recovery.py`; `visual_poster_studio/binding_recover.py`; `studio_png_sandbox/unified.py`
- Dependencies: python, local-filesystem
- Verification: resume, sprint, png-workflow (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Writer locks, validated pointers and recovery copies; physical power loss, hostile concurrent filesystem and arbitrary filesystems unproven.
- Acceptance criteria: Full stop/resume exact state; ENOSPC/sync failures fail closed; explicit recovery never overwrites source or revives approval.

## M5-030 — Named variants, historical approvals and export records

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8–9
- Current source: `creative_core/operations.py`; `creative_core/validation.py`; `visual_poster_studio/exports.py`
- Dependencies: python
- Verification: core, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Core snapshots supported; not a full campaign branching/multi-output management UI. Reviewer strings not authentication.
- Acceptance criteria: Immutable snapshots/old exports; new edits clear current approval; history travel never resurrects it.

## M5-031 — Conversational editing with atomic diff/provenance

- Classification: BLOCKED BY SECURITY OR CONTRACT
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §8
- Current source: `visual_poster_studio/app.js`; `creative_core/operations.py`
- Dependencies: future-edit-contract
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: No implemented selection-scoped AI diff/apply transaction. Imperative manual edits are not this feature.
- Acceptance criteria: Separate approved atomic multi-operation/provenance version; explicit Apply/Discard; one reversible action; protected facts unchanged.

## M5-032 — Advanced inspector lock/visibility/opacity/duplicate/unlink/crop

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §4,8
- Current source: `creative_core/validation.py`; `studio_manual_ui/service.py`; `visual_poster_studio/app.js`
- Dependencies: future-edit-contract, browser
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Some fields exist in broad core schema but strict manual/render subset does not expose/accept all. Crop/masks and persistent locks/visibility not complete.
- Acceptance criteria: Capability/contract matrix before enabling; persisted identities and shared-content semantics; undo/export parity.

## M5-033 — Reference Style manual R1

- Classification: UNKNOWN / REQUIRES CONFIRMATION
- Original specification: docs/REFERENCE_STYLE_STUDIO_SPEC.md; protected R1 records excluded by instruction
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: protected-r1
- Verification: excluded-r1 (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Previously conditionally accepted per task context; source/evidence deliberately not opened or copied. This checkpoint cannot recover that protected module.
- Acceptance criteria: Owner-authorized separate R1 preservation and independent evidence review; do not infer approval from this package.

## M5-034 — R2 synthetic report-contract conformance

- Classification: NOT IMPLEMENTED
- Original specification: docs/R2_SAFE_DEVELOPMENT_ROADMAP.md; docs/R2_NEXT_AUTHORIZATION_MATRIX.md
- Current source: `docs/R2_REPORT_CONTRACT_PROPOSAL.md`; `docs/R2_CANONICAL_VECTOR_SPEC.md`
- Dependencies: future-r2-contract
- Verification: r2-design (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Planning contracts exist; no separate r2 contract implementation package found in scoped source. Not implemented by media-agent protocol.
- Acceptance criteria: Explicit authorized frozen allowlist/API preflight; synthetic-only tests; no sixth format/real decoding.

## M5-035 — Bounded reference image/poster analysis and English/Telugu OCR

- Classification: BLOCKED BY SECURITY OR CONTRACT
- Original specification: docs/R2_IMAGE_ANALYSIS_SPEC.md; docs/R2_ARCHITECTURE_DECISION_RECORD.md
- Current source: `media_analysis_agent/backends.py`; `studio_media_workflow/containment.py`
- Dependencies: future-media-boundary
- Verification: r2-design, agent (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Independent optional agent/defaultOFF; no qualified real backend/OCR/language models. PNG logo decoder does not qualify R2.
- Acceptance criteria: Separate R2 authorization; GateA/B/C/D; real fixtures, resource/isolation/security and OCR language acceptance.

## M5-036 — Selective reference application, multi-reference mixing, video style

- Classification: BLOCKED BY SECURITY OR CONTRACT
- Original specification: docs/REFERENCE_STYLE_STUDIO_SPEC.md; docs/REFERENCE_STYLE_ACCEPTANCE_MATRIX.md
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: future-r2-contract, future-media-boundary
- Verification: r2-design (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: R2–R6 separately gated; requirements retained, not current implementation or authorization.
- Acceptance criteria: Each phase prerequisites/review/rights/contracts/fixtures; reversible protected-asset-safe adaptation.

## M5-037 — Independent optional media agent lifecycle

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/MEDIA_AGENT_COMPLETION_HANDOFF.md; docs/MEDIA_ANALYSIS_AGENT_HANDOFF.md
- Current source: `media_analysis_agent/controller.py`; `media_analysis_agent_v2/controller.py`; `media_analysis_agent_v2/packages.py`
- Dependencies: python
- Verification: agent (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Synthetic lifecycle/replaceable package foundation only; ordinary Studio showsOFF/ABSENT. Not broad resource-containment certification.
- Acceptance criteria: Explicit enable/start/cancel/stop; no auto retry; confirmed exit/fault; strict validated communication; UI independent.

## M5-038 — Local AI image generation

- Classification: NOT IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §4; docs/M5_FUNCTIONAL_STATUS.json
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: future-image-model
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: No adopted qualified image model/runtime/weights/rights package. Listed as future optional in taxonomy but remains an eventual product requirement, not silently removed.
- Acceptance criteria: Separate authorized stack selection/rights/security/resource gate and editable integration; do not substitute PNG decoding or templates.

## M5-039 — Cinematic reel creation and poster/reel adaptation

- Classification: BLOCKED BY SECURITY OR CONTRACT
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md G5; docs/M5_FUNCTIONAL_STATUS.json
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: m4-interface, m6-interface
- Verification: r2-design, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: No authorized accepted cross-milestone adapter; M4/M6 workspaces untouched. Still required eventual coordination.
- Acceptance criteria: Accepted identified engine baseline, separate adapter authorization, poster/reel content/rights mapping and independent approvals.

## M5-040 — Expanded outputs, dimensions, carousel/campaign/custom

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §3–4, G6
- Current source: `visual_poster_studio/scene.py`; `poster_render/scene.py`
- Dependencies: future-render-profile
- Verification: phase2, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Current editor fixed1080×1350; legacy prototype larger stills do not qualify editable multi-output product.
- Acceptance criteria: Versioned supported profiles/pixel budgets, linked-view semantics, export parity and explicit acceptance per output.

## M5-041 — Final content/fact/brand/legal approval workflow

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §9
- Current source: `creative_core/operations.py`; `poster_render/approval.py`; `visual_poster_studio/exports.py`
- Dependencies: future-approval-contract
- Verification: core, phase2 (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Core fingerprint approval/helper exists; current UI exports drafts only. No integrated final factual/legal/brand release authority.
- Acceptance criteria: Separate review axes, current immutable inputs, QA/rights evidence and authorized approval; drafts never relabeled final.

## M5-042 — Offline/local independence and no mandatory subscription

- Classification: PARTIALLY IMPLEMENTED
- Original specification: PROJECT_ENGINEERING_POLICY.md; OFFLINE_BUILD_STRATEGY.md
- Current source: `tools/studio_local.py`; `visual_poster_studio/hybrid_jobs.py`; `studio_png_sandbox/controller.py`
- Dependencies: python, model, png-runtime, browser
- Verification: sprint, png-security (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Existing runtime works locally; exact runtime/model/source/SDK/transitive closure and clean offline provisioning NOT proved.
- Acceptance criteria: Retain legal source/build inputs/notices; clean no-network provision/build/recover on target; no hidden paid fallback.

## M5-043 — Open-source/licensing/commercial distribution closure

- Classification: PARTIALLY IMPLEMENTED
- Original specification: THIRD_PARTY_INVENTORY.md; docs/PNG_SANDBOX_DEPENDENCIES.json
- Current source: `docs/CREATIVE_DIRECTOR_PHASE2A.md`; `docs/CREATIVE_DIRECTOR_PHASE2D.md`
- Dependencies: licenses
- Verification: dependency (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: MIT/Apache/Zlib/OFL research recorded; first-party release license not selected; transitive/native/model-conversion notice gaps remain.
- Acceptance criteria: Independent exact artifact/transitive/notice audit; rights to media separate; no release until closure.

## M5-044 — Production integration, engine modification and release

- Classification: OUTSIDE M5 SCOPE
- Original specification: PROJECT_ENGINEERING_POLICY.md; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: m4-interface, m6-interface
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Outside this isolated M5 development/checkpoint authorization, not removed from overall product release process.
- Acceptance criteria: Explicit owner authorization, accepted interfaces, recovery/regression/rollback and release signoff before action.

## M5-045 — Frozen checkpoint and milestone isolation

- Classification: COMPLETE AND VERIFIED
- Original specification: PROJECT_ENGINEERING_POLICY.md; docs/M5_FUNCTIONAL_SPRINT_HANDOFF.md
- Current source: `tools/studio_local.py`
- Dependencies: workspace-boundary
- Verification: sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Current task is no-touch; no new protected-workspace or238-file frozen-checkpoint hash audit. Scoped source hashes verify only included authorized files.
- Acceptance criteria: No M4/M6/production/frozen/R1 access; fresh outputs only; no overwrite or silent migration.

## M5-046 — Deterministic fallback when AI absent

- Classification: IMPLEMENTED BUT NOT FULLY VERIFIED
- Original specification: docs/CREATIVE_DIRECTOR_PHASE1.md; docs/CREATIVE_DIRECTOR_PHASE2G.md
- Current source: `visual_poster_studio/director.py`; `visual_poster_studio/director.mjs`; `visual_poster_studio/product.mjs`
- Dependencies: python, fonts, browser
- Verification: hybrid-g, sprint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Explicit separate user selection only. No model means no claim of AI interpretation.
- Acceptance criteria: Visible deterministic label; manual remains usable; AI failure never silently publishes templates.

## M5-047 — Brand Kit Wizard and automatic extraction

- Classification: NOT IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §6
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: future-media-boundary
- Verification: r2-design (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Manual profile foundation exists; automatic extraction is explicitly future in the design and no prerequisite for entering a kit.
- Acceptance criteria: Separate bounded extraction evidence/uncertainty/rights/review gate; human approval before publication.

## M5-048 — Source facts/claims, identity, logo and hard-rule protection

- Classification: PARTIALLY IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §5–6
- Current source: `creative_core/operations.py`; `visual_poster_studio/brand_application.py`; `studio_png_sandbox/workflow.py`
- Dependencies: sqlite, future-approval-contract
- Verification: brand-a, png-workflow (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Claims/quotes lack general automatic verification; PNG aspect/text protection applies, not full identity/face editing or all prose rules.
- Acceptance criteria: Preserve approved exact content/identities; unknown hard rules block; no stylistic override or invented factual claims.

## M5-049 — Recovery package and independent agent continuation

- Classification: COMPLETE AND VERIFIED
- Original specification: Current handover instruction; docs/M5_MASTER_HANDOVER.md
- Current source: `M5_STATUS_MANIFEST.json`
- Dependencies: python
- Verification: checkpoint (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Only authorized source recovery; protected R1, private sessions and runtime artifacts excluded. Verification result must pass before acceptance.
- Acceptance criteria: Every included byte verified; separate recovery/portable manifests; fresh extraction; source unchanged; explicit exclusions.

## M5-050 — Voice/URL input, advanced effects, motion/audio and print

- Classification: NOT IMPLEMENTED
- Original specification: docs/UNIVERSAL_CREATIVE_STUDIO_SPEC.md §3–4, G6
- Current source: No scoped implementation; see exclusion/status.
- Dependencies: future-media-boundary, future-render-profile
- Verification: r2-design (evidence inventory resolves paths and source identities).
- Limitations and remaining implementation: Proposed/later optional capabilities, not currently enabled or silently declared complete. Commitment priority requires owner confirmation where design labels future.
- Acceptance criteria: Separate accepted runtime/persistence/profile/security/rights gates; do not treat design taxonomy as installed capability.

## C. Architecture and data flow
# Architecture and data flow

```mermaid
flowchart TD
  Launcher[Start Studio.command / studio_local.py] --> HTTP[Visual loopback server / Host-Origin-CSRF]
  HTTP --> Entry[Home / Projects / Quick-Guided-Professional]
  Entry --> Pair[Whole document and brand-brief pair]
  Pair --> AI[Explicit local Qwen3-14B job]
  AI --> Intent[Strict untrusted editorial intent]
  Intent --> Compiler[Deterministic measured three compositions]
  Compiler --> Review[Compare / acknowledge / select new draft]
  Review --> Editor[Shared Visual editor]
  Brands[SQLite Brand Library / immutable pins / live rights] --> Pair
  Brands --> Rules[Brand A policy]
  Rules --> Compiler
  Rules --> Editor
  Editor --> Core[creative@1 / history v1-v3 / checkpoints]
  Editor --> Fork[Explicit media-v3 source copy]
  Fork --> Unified[Combined base and PNG timeline]
  Brands --> Qualified[Hash and current rights checks]
  Qualified --> Decoder[No-import Wasm LodePNG / Wasmtime helper]
  Decoder --> Pixels[Qualified RGBA receipt / normalized PNG]
  Pixels --> Unified
  Core --> Scene[One deterministic SVG / pinned fonts]
  Unified --> Scene
  Scene --> QA[Browser font-ink-overflow checks / RGBA parity]
  QA --> Export[Draft SVG-PNG / immutable manifests]
  Agent[Optional synthetic media agent OFF] -. no real backend .-> Entry
```

Data authority: core content is not a media envelope; context uses immutable paired commits; PNG receipts/placements use a separately versioned workflow. The single main Studio exposes these explicitly instead of disguising media inside creative@1. No arrow to M4/M6/production is implemented or authorized by this archive.


## D. Implemented modules and exact APIs
# Actual module architecture and source/API inventory

The catalogue was parsed from the captured source with Python AST and named JavaScript function/import scanning. This does not execute/import product modules. Source filenames and identifiers below are observed, not invented architecture. Private helpers are listed for audit context; they are not all stable public APIs.


## core — Creative document core

1. Purpose: Canonical schema1 editable content, operations, immutable snapshots and persistence.
2. Capabilities: Canonical schema1 editable content, operations, immutable snapshots and persistence. Document dictionaries + allowlisted operations + project root → new validated documents or CreativeError.
3. Source: `creative_core/__init__.py`, `creative_core/document.py`, `creative_core/operations.py`, `creative_core/persistence.py`, `creative_core/validation.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Document dictionaries + allowlisted operations + project root → new validated documents or CreativeError.
6. Formats: creative@1/schema1; history1/2/3; named versions; fingerprint approvals
7. Dependencies: python
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Canonical schema1 editable content, operations, immutable snapshots and persistence. Document dictionaries + allowlisted operations + project root → new validated documents or CreativeError.
10. Security: No automatic migration; unsupported history rejects; approved historical snapshots never edited.
11. Limitations: Historical37/55 tests predate additive operations; current smoke covers only supported subset.
12. Tests: `tests/run_isolated.py`, `tests/test_core.py`, `tests/test_render_policy.py`; evidence IDs core, sprint
13. Remaining: Historical37/55 tests predate additive operations; current smoke covers only supported subset.

## manual — Accepted manual CLI/UI

1. Purpose: Dependency-light local manual project service retained independently from Visual/media.
2. Capabilities: Dependency-light local manual project service retained independently from Visual/media. Strict JSON create/edit/save/reopen → view/document; UIError has code/detail/status.
3. Source: `studio_manual_ui/__init__.py`, `studio_manual_ui/__main__.py`, `studio_manual_ui/app.js`, `studio_manual_ui/index.html`, `studio_manual_ui/server.py`, `studio_manual_ui/service.py`, `studio_manual_ui/styles.css`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Strict JSON create/edit/save/reopen → view/document; UIError has code/detail/status.
6. Formats: Owned manual session; creative@1 strict text/rectangle/ellipse subset
7. Dependencies: python, browser
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Dependency-light local manual project service retained independently from Visual/media. Strict JSON create/edit/save/reopen → view/document; UIError has code/detail/status.
10. Security: Loopback, Host/Origin/CSRF, fixed paths; no opaque asset decoding.
11. Limitations: Do not modify accepted source or use it to coerce media documents.
12. Tests: `studio_ui_tests/test_http.py`, `studio_ui_tests/test_local_tools.py`, `studio_ui_tests/test_service.py`; evidence IDs manual, sprint
13. Remaining: Do not modify accepted source or use it to coerce media documents.

## visual — Visual editor and renderer

1. Purpose: Shared deterministic SVG preview, canvas operations and conditional native-browser PNG.
2. Capabilities: Shared deterministic SVG preview, canvas operations and conditional native-browser PNG. Core document/view + pinned fonts → SVG scene, diagnostics; UI computes geometry then submits one validated transaction.
3. Source: `visual_poster_studio/app.js`, `visual_poster_studio/canvas.mjs`, `visual_poster_studio/editing.mjs`, `visual_poster_studio/geometry.mjs`, `visual_poster_studio/index.html`, `visual_poster_studio/layout.mjs`, `visual_poster_studio/scene.py`, `visual_poster_studio/service.py`, `visual_poster_studio/styles.css`, `visual_poster_studio/text_layout.mjs`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Core document/view + pinned fonts → SVG scene, diagnostics; UI computes geometry then submits one validated transaction.
6. Formats: Fixed1080×1350;8 MiB doc;64 layers/32text;20k active codepoints;64explicit lines;4MiBSVG/8MiBPNG
7. Dependencies: python, browser, fonts
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Shared deterministic SVG preview, canvas operations and conditional native-browser PNG. Core document/view + pinned fonts → SVG scene, diagnostics; UI computes geometry then submits one validated transaction.
10. Security: Invalid glyphs/fonts/overflow/unsupported styles refuse export; draft only; no fallback rasterizer.
11. Limitations: Text alignment left and1.65× leading; full advanced inspector/IME/accessibility incomplete.
12. Tests: `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs visual, geometry, text, sprint
13. Remaining: Text alignment left and1.65× leading; full advanced inspector/IME/accessibility incomplete.

## product — Entry modes, Home and navigation

1. Purpose: One continuous Create route and UI-only experience density over existing records.
2. Capabilities: One continuous Create route and UI-only experience density over existing records. Exact idea/brief/mode/optional brand → paired draft; read-only history/status; session IDs, not arbitrary paths.
3. Source: `visual_poster_studio/home.mjs`, `visual_poster_studio/home.py`, `visual_poster_studio/product.mjs`, `visual_poster_studio/product.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Exact idea/brief/mode/optional brand → paired draft; read-only history/status; session IDs, not arbitrary paths.
6. Formats: Existing brief/binding only; mode localStorage, not new document fields
7. Dependencies: python, sqlite, browser
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: One continuous Create route and UI-only experience density over existing records. Exact idea/brief/mode/optional brand → paired draft; read-only history/status; session IDs, not arbitrary paths.
10. Security: Pending/composing input guard; explicit resume; defaults labelled; no silent fallback.
11. Limitations: Recent sessions not a verified last-opened database; comparison jobs process-local.
12. Tests: `studio_ui_tests/test_http.py`, `studio_ui_tests/test_local_tools.py`, `studio_ui_tests/test_service.py`, `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs sprint, home
13. Remaining: Recent sessions not a verified last-opened database; comparison jobs process-local.

## brands — Brand & Asset Library

1. Purpose: Append-only hashed brand/asset/rights records and reviewed immutable pins.
2. Capabilities: Append-only hashed brand/asset/rights records and reviewed immutable pins. Exact command objects → metadata views, hashes and current eligibility.
3. Source: `visual_poster_studio/brands.mjs`, `visual_poster_studio/brands.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Exact command objects → metadata views, hashes and current eligibility.
6. Formats: SQLite application/user_version1; records/blobs/heads/assets/rights_heads;100assets/1000records/32MiBblobs/64MiBDB
7. Dependencies: python, sqlite
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Append-only hashed brand/asset/rights records and reviewed immutable pins. Exact command objects → metadata views, hashes and current eligibility.
10. Security: No decoding at registration; granted scope/destination/expiry authority required; unknown denies.
11. Limitations: Trusted local legal assertions; not external legal authentication or general media support.
12. Tests: `studio_ui_tests/test_http.py`, `studio_ui_tests/test_local_tools.py`, `studio_ui_tests/test_service.py`; evidence IDs brand, binding, sprint
13. Remaining: Trusted local legal assertions; not external legal authentication or general media support.

## brand-portability — Library backup and restore

1. Purpose: Deterministic metadata/legally permitted BLOB backup with preview and conservative rights quarantine.
2. Capabilities: Deterministic metadata/legally permitted BLOB backup with preview and conservative rights quarantine. ZIP_STORED package + expected destination/package hashes → validated plan/atomic SQLite restore.
3. Source: `visual_poster_studio/brand_portability.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: ZIP_STORED package + expected destination/package hashes → validated plan/atomic SQLite restore.
6. Formats: studio-brand-backup@1;72 MiB;1101members; strict records/blobs paths;20backups/256 MiB
7. Dependencies: python, sqlite
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Deterministic metadata/legally permitted BLOB backup with preview and conservative rights quarantine. ZIP_STORED package + expected destination/package hashes → validated plan/atomic SQLite restore.
10. Security: Never extract attacker paths; all integrity/lineage checked; no overwritten immutable record or revived revoked grant.
11. Limitations: Incoming advancing grants may become unknown; missing blob clearance blocks effective restore.
12. Tests: `studio_ui_tests/test_http.py`, `studio_ui_tests/test_local_tools.py`, `studio_ui_tests/test_service.py`; evidence IDs brand-portability
13. Remaining: Incoming advancing grants may become unknown; missing blob clearance blocks effective restore.

## bindings — Project/brand pin and creative brief

1. Purpose: One publication pointer for document/context pairs and explicit impact-confirmed context changes.
2. Capabilities: One publication pointer for document/context pairs and explicit impact-confirmed context changes. Project revision, binding/head, impact acknowledgement → immutable paired commit; recovery selects one whole pair.
3. Source: `visual_poster_studio/binding_recover.py`, `visual_poster_studio/binding_workflow.py`, `visual_poster_studio/project_bindings.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Project revision, binding/head, impact acknowledgement → immutable paired commit; recovery selects one whole pair.
6. Formats: studio-project-binding@1; studio-bound-commit@1; studio-bound-head@1
7. Dependencies: python, sqlite
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: One publication pointer for document/context pairs and explicit impact-confirmed context changes. Project revision, binding/head, impact acknowledgement → immutable paired commit; recovery selects one whole pair.
10. Security: No independent document/binding publication, legacy mirror or silent adoption; rights live rechecked.
11. Limitations: Creative Undo never rewinds context; media binding frozen; old reader cannot list paired storage.
12. Tests: `studio_ui_tests/test_http.py`, `studio_ui_tests/test_local_tools.py`, `studio_ui_tests/test_service.py`, `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs binding, sprint
13. Remaining: Creative Undo never rewinds context; media binding frozen; old reader cannot list paired storage.

## brand-a — Brand Application A

1. Purpose: Approved palette, supported typography resolution and independently enforced bounded rule vocabulary.
2. Capabilities: Approved palette, supported typography resolution and independently enforced bounded rule vocabulary. Pinned record + brief + current document → policy/issues/rejection; one layer style operation.
3. Source: `visual_poster_studio/brand_application.mjs`, `visual_poster_studio/brand_application.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Pinned record + brief + current document → policy/issues/rejection; one layer style operation.
6. Formats: brand-application-a@1; exact aliases plus margin/font/contrast declaration regexes
7. Dependencies: sqlite, fonts
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Approved palette, supported typography resolution and independently enforced bounded rule vocabulary. Pinned record + brief + current document → policy/issues/rejection; one layer style operation.
10. Security: Unknown hard rule/unsupported font refuses; preferences cannot override restrictions; no external asset loading.
11. Limitations: Not arbitrary prose rule understanding; solid-shape nominal contrast only; bulk restyle absent.
12. Tests: `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs brand-a, sprint
13. Remaining: Not arbitrary prose rule understanding; solid-shape nominal contrast only; bulk restyle absent.

## director — Deterministic Creative Director

1. Purpose: Explicit non-AI alternative, source validation, layout mapping, retained plans and new paired selections.
2. Capabilities: Explicit non-AI alternative, source validation, layout mapping, retained plans and new paired selections. Saved brief/pin/seed → three supported editable proposals; selection never overwrites source.
3. Source: `visual_poster_studio/director.mjs`, `visual_poster_studio/director.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Saved brief/pin/seed → three supported editable proposals; selection never overwrites source.
6. Formats: Separate deterministic bundles using protected creative/binding records unchanged
7. Dependencies: python, fonts, browser
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Explicit non-AI alternative, source validation, layout mapping, retained plans and new paired selections. Saved brief/pin/seed → three supported editable proposals; selection never overwrites source.
10. Security: Exact copy/current rights/capability checks; deterministic label; no hidden substitute for AI.
11. Limitations: Finite generic layouts; not actual AI interpretation by itself.
12. Tests: `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs director, hybrid-g
13. Remaining: Finite generic layouts; not actual AI interpretation by itself.

## ai — Local AI adapters and hybrid inference

1. Purpose: Historical qualification adapters plus current true model editorial-intent/deterministic geometry hybrid.
2. Capabilities: Historical qualification adapters plus current true model editorial-intent/deterministic geometry hybrid. Pinned runtime/model + saved source + browser measurements → strict intent, three docs/scenes, rationales, raw provenance; explicit Jobs selection.
3. Source: `visual_poster_studio/ai_adapter.py`, `visual_poster_studio/ai_capabilities.py`, `visual_poster_studio/ai_constrained.py`, `visual_poster_studio/ai_hybrid.py`, `visual_poster_studio/ai_semantic.py`, `visual_poster_studio/hybrid.mjs`, `visual_poster_studio/hybrid_jobs.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Pinned runtime/model + saved source + browser measurements → strict intent, three docs/scenes, rationales, raw provenance; explicit Jobs selection.
6. Formats: studio-ai-hybrid-request@1; studio-ai-hybrid-compilation@1; hybrid-rationale@1; historical semantic contracts remain unchanged
7. Dependencies: python, llama, model, fonts, browser
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Historical qualification adapters plus current true model editorial-intent/deterministic geometry hybrid. Pinned runtime/model + saved source + browser measurements → strict intent, three docs/scenes, rationales, raw provenance; explicit Jobs selection.
10. Security: No model tool/file execution; strict JSON/length/enums; live rights/staleness; one job/controller;240s deadline, no retry.
11. Limitations: Qwen14B ~13 GiB child RSS historically; CPU slow, Metal unqualified; no machine-wide AI quota or distribution closure.
12. Tests: `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs hybrid-f, hybrid-g, sprint
13. Remaining: Qwen14B ~13 GiB child RSS historically; CPU slow, Metal unqualified; no machine-wide AI quota or distribution closure.

## persistence — Visual session, history and recovery

1. Purpose: Visual ownership/OS writer lock, journal/checkpoints, strict resume and explicit recovery copies.
2. Capabilities: Visual ownership/OS writer lock, journal/checkpoints, strict resume and explicit recovery copies. Canonical owned root + resume flag → locked validated session; selected recovery → fresh root, never overwrite.
3. Source: `visual_poster_studio/checkpoint_restore.py`, `visual_poster_studio/recovery.py`, `visual_poster_studio/session.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Canonical owned root + resume flag → locked validated session; selected recovery → fresh root, never overwrite.
6. Formats: visual-session@1; existing manual owner; journal/checkpoints;128 MiB combined recovery budget
7. Dependencies: python, local-filesystem
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Visual ownership/OS writer lock, journal/checkpoints, strict resume and explicit recovery copies. Canonical owned root + resume flag → locked validated session; selected recovery → fresh root, never overwrite.
10. Security: Lock before project reads; sync failures block/degrade; immutable checkpoints; no auto-delete or automatic repair.
11. Limitations: No physical power-loss certification, arbitrary filesystem durability or hostile-local filesystem guarantee.
12. Tests: `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs resume, geometry, sprint
13. Remaining: No physical power-loss certification, arbitrary filesystem durability or hostile-local filesystem guarantee.

## exports — Draft exports and identities

1. Purpose: Pinned font coverage, embedded CSS, source/context scene identity, one-use QA-bound publication.
2. Capabilities: Pinned font coverage, embedded CSS, source/context scene identity, one-use QA-bound publication. Current scene + browser font/overflow/parityQA + optional bounded PNG → draft SVG/PNG/manifest.
3. Source: `visual_poster_studio/exports.py`, `visual_poster_studio/fonts.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Current scene + browser font/overflow/parityQA + optional bounded PNG → draft SVG/PNG/manifest.
6. Formats: 15s handshake, one export;20 sets;256 MiB Visual export quota; media root stricter128 MiB total
7. Dependencies: fonts, browser, python
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Pinned font coverage, embedded CSS, source/context scene identity, one-use QA-bound publication. Current scene + browser font/overflow/parityQA + optional bounded PNG → draft SVG/PNG/manifest.
10. Security: Font hash/glyph refuse; stale source/context/rights blocks; historical export bytes retained.
11. Limitations: Browser parity is trusted-local client evidence, not independent approved-final server rendering.
12. Tests: `visual_poster_tests/browser_acceptance.html`, `visual_poster_tests/browser_acceptance.js`, `visual_poster_tests/canvas_browser.mjs`, `visual_poster_tests/editing_browser.mjs`, `visual_poster_tests/geometry_browser.mjs`, `visual_poster_tests/hybrid_browser.html`, `visual_poster_tests/hybrid_browser.mjs`, `visual_poster_tests/layout_browser.mjs`, `visual_poster_tests/test_ai_adapter.py`, `visual_poster_tests/test_ai_constrained.py`, `visual_poster_tests/test_ai_editorial.py`, `visual_poster_tests/test_ai_hybrid.py`, `visual_poster_tests/test_ai_semantic.py`, `visual_poster_tests/test_brand_application.py`, `visual_poster_tests/test_brand_portability.py`, `visual_poster_tests/test_brands.py`, `visual_poster_tests/test_canvas.mjs`, `visual_poster_tests/test_canvas_transactions.py`, `visual_poster_tests/test_compatibility.py`, `visual_poster_tests/test_director.py`, `visual_poster_tests/test_editing.mjs`, `visual_poster_tests/test_editing_ui.py`, `visual_poster_tests/test_fonts.py`, `visual_poster_tests/test_geometry.mjs`, `visual_poster_tests/test_geometry.py`, `visual_poster_tests/test_home.py`, `visual_poster_tests/test_http.py`, `visual_poster_tests/test_hybrid_jobs.py`, `visual_poster_tests/test_layout.mjs`, `visual_poster_tests/test_layout_navigation.py`, `visual_poster_tests/test_project_bindings.py`, `visual_poster_tests/test_recovery.py`, `visual_poster_tests/test_reorder.py`, `visual_poster_tests/test_resume.py`, `visual_poster_tests/test_scene.py`, `visual_poster_tests/test_service.py`, `visual_poster_tests/test_text_completion.py`, `visual_poster_tests/test_text_layout.mjs`, `visual_poster_tests/test_workflow.py`, `visual_poster_tests/text_completion_browser.mjs`; evidence IDs visual, png-unified, sprint
13. Remaining: Browser parity is trusted-local client evidence, not independent approved-final server rendering.

## quarantine — Original media admission foundation

1. Purpose: Historical metadata-only quarantine namespace preserved, not the active PNG backend.
2. Capabilities: Historical metadata-only quarantine namespace preserved, not the active PNG backend. Approved pin/asset declaration → quarantined metadata admission; processing always refuses.
3. Source: `studio_media_workflow/__init__.py`, `studio_media_workflow/__main__.py`, `studio_media_workflow/containment.py`, `studio_media_workflow/contracts.py`, `studio_media_workflow/store.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Approved pin/asset declaration → quarantined metadata admission; processing always refuses.
6. Formats: studio-media-workflow@1; studio-media-session@1; studio-media-head@1
7. Dependencies: python, sqlite
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Historical metadata-only quarantine namespace preserved, not the active PNG backend. Approved pin/asset declaration → quarantined metadata admission; processing always refuses.
10. Security: containment.require_qualified always refuses; no force enable, no real parser.
11. Limitations: Broad original GateA unresolved; do not reinterpret v1 as PNG-v2/v3 live format.
12. Tests: `media_workflow_tests/test_boundary.py`; evidence IDs media-foundation
13. Remaining: Broad original GateA unresolved; do not reinterpret v1 as PNG-v2/v3 live format.

## png — PNG capability sandbox and standalone workflow

1. Purpose: Qualified narrow decoder, immutable PNG media generations, standalone v2 and combined v3 subclass.
2. Capabilities: Qualified narrow decoder, immutable PNG media generations, standalone v2 and combined v3 subclass. Exact bounded registered PNG+hash+rights → qualified RGBA receipt, normalized PNG; head-bound edits/scenes/draft export.
3. Source: `studio_png_sandbox/__init__.py`, `studio_png_sandbox/__main__.py`, `studio_png_sandbox/app.js`, `studio_png_sandbox/controller.py`, `studio_png_sandbox/decoder.c`, `studio_png_sandbox/helper.c`, `studio_png_sandbox/index.html`, `studio_png_sandbox/server.py`, `studio_png_sandbox/style.css`, `studio_png_sandbox/unified.py`, `studio_png_sandbox/workflow.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Exact bounded registered PNG+hash+rights → qualified RGBA receipt, normalized PNG; head-bound edits/scenes/draft export.
6. Formats: studio-media-workflow@2/@3; studio-png-session@1/@2; studio-png-export@1; studio-png-rgba@1 profile
7. Dependencies: python, png-runtime, sqlite, fonts, browser
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Qualified narrow decoder, immutable PNG media generations, standalone v2 and combined v3 subclass. Exact bounded registered PNG+hash+rights → qualified RGBA receipt, normalized PNG; head-bound edits/scenes/draft export.
10. Security: No-import/WASI Wasm; one helper/globaljoblock; hard64 MiB guest;15s worker; measured128 MiB helper/controllerRSS; no kernel total ceiling.
11. Limitations: Only static8-bitRGB/RGBA PNG; v3 no reorder/interleaving; metadata-only source remains explicit copy; runtime rpath absolute.
12. Tests: `png_sandbox_tests/test_security.py`, `png_sandbox_tests/test_unified.py`, `png_sandbox_tests/test_workflow.py`; evidence IDs png-security, png-workflow, png-unified, sprint
13. Remaining: Only static8-bitRGB/RGBA PNG; v3 no reorder/interleaving; metadata-only source remains explicit copy; runtime rpath absolute.

## unified — Main Studio media adapter and direct manipulation

1. Purpose: Main server fixed-ID media routes and shared editor Undo/Redo/preview/export.
2. Capabilities: Main server fixed-ID media routes and shared editor Undo/Redo/preview/export. Project/revision acknowledgement → explicit source checkpoint/copy; id/head capture → media or core operation.
3. Source: `visual_poster_studio/media.mjs`, `visual_poster_studio/media_bridge.py`, `visual_poster_studio/media_gestures.mjs`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Project/revision acknowledgement → explicit source checkpoint/copy; id/head capture → media or core operation.
6. Formats: Existing media-v3 namespace and combined timeline; no protected schema changes
7. Dependencies: png-runtime, browser, sqlite
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Main server fixed-ID media routes and shared editor Undo/Redo/preview/export. Project/revision acknowledgement → explicit source checkpoint/copy; id/head capture → media or core operation.
10. Security: Single-thread main media routes60s alarm, current rights, strict IDs, head checks; PNGcannot obscure text.
11. Limitations: Binding/brief read-only in media workspace; new concepts from manual source; PNG ordering disabled.
12. Tests: `png_sandbox_tests/test_security.py`, `png_sandbox_tests/test_unified.py`, `png_sandbox_tests/test_workflow.py`; evidence IDs png-unified, sprint
13. Remaining: Binding/brief read-only in media workspace; new concepts from manual source; PNG ordering disabled.

## agent — Optional independent media-agent foundations

1. Purpose: Synthetic lifecycle, validated bounded protocol and independent versioned first-party deployment.
2. Capabilities: Synthetic lifecycle, validated bounded protocol and independent versioned first-party deployment. Explicit enable/start/synthetic request → strict result or fault; stop/cancel confirms termination.
3. Source: `media_analysis_agent/README.md`, `media_analysis_agent/__init__.py`, `media_analysis_agent/__main__.py`, `media_analysis_agent/backends.py`, `media_analysis_agent/controller.py`, `media_analysis_agent/policy.py`, `media_analysis_agent/protocol.py`, `media_analysis_agent/storage.py`, `media_analysis_agent/worker.py`, `media_analysis_agent_v2/README.md`, `media_analysis_agent_v2/__init__.py`, `media_analysis_agent_v2/__main__.py`, `media_analysis_agent_v2/controller.py`, `media_analysis_agent_v2/packages.py`, `media_analysis_agent_v2/worker.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Explicit enable/start/synthetic request → strict result or fault; stop/cancel confirms termination.
6. Formats: Synthetic agent protocol/config and deployment/admission receipts; NOT frozen R2analysis report formats
7. Dependencies: python
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Synthetic lifecycle, validated bounded protocol and independent versioned first-party deployment. Explicit enable/start/synthetic request → strict result or fault; stop/cancel confirms termination.
10. Security: DefaultOFF; real backends absent/disabled; no automatic retry; do not infer resource qualification from lifecycle tests.
11. Limitations: No image/OCR/video analysis; Studio remains usable when absent, crashed or incompatible.
12. Tests: `media_agent_tests/test_agent.py`, `media_agent_v2_tests/test_completion.py`; evidence IDs agent, r2-design
13. Remaining: No image/OCR/video analysis; Studio remains usable when absent, crashed or incompatible.

## legacy-renderer — Phase2 renderer prototype

1. Purpose: Historical renderer-neutral mapper and Chrome/Puppeteer/Sharp comparison, not current hostile-media path.
2. Capabilities: Historical renderer-neutral mapper and Chrome/Puppeteer/Sharp comparison, not current hostile-media path. Synthetic creative+renderpolicy → scene/SVG; isolated tool → draft PNG/metrics.
3. Source: `poster_render/__init__.py`, `poster_render/approval.py`, `poster_render/backend.mjs`, `poster_render/isolation.sb`, `poster_render/scene.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: Synthetic creative+renderpolicy → scene/SVG; isolated tool → draft PNG/metrics.
6. Formats: Phase2renderpolicy/receipts; multiple prototype still sizes
7. Dependencies: python, legacy-node, fonts
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Historical renderer-neutral mapper and Chrome/Puppeteer/Sharp comparison, not current hostile-media path. Synthetic creative+renderpolicy → scene/SVG; isolated tool → draft PNG/metrics.
10. Security: Use only mandatory isolation runner; never invoke backend.mjs directly or treat old SVG handling as asset qualification.
11. Limitations: Depends on external private HyperFrames package tree; Sharp not a visually equivalent replacement; no distribution closure.
12. Tests: `tests/run_isolated.py`, `tests/test_core.py`, `tests/test_render_policy.py`; evidence IDs phase2
13. Remaining: Depends on external private HyperFrames package tree; Sharp not a visually equivalent replacement; no distribution closure.

## launcher — Local launcher and internal source kit

1. Purpose: Absolute-path startup/check/session listing and explicitly limited internal code kit.
2. Capabilities: Absolute-path startup/check/session listing and explicitly limited internal code kit. check/start/sessions/kit flags → truthful readiness or owned new/resumed service.
3. Source: `Start Studio.command`, `tools/studio_local.py`
4. Important classes/functions: see the exact per-file catalogue below and `manifests/SOURCE_API_CATALOGUE.json`; line numbers/signatures resolve to captured bytes.
5. Inputs/outputs: check/start/sessions/kit flags → truthful readiness or owned new/resumed service.
6. Formats: Package-local runtime roots; kit fixedmanifest, bounds; not an installer
7. Dependencies: python, browser, fonts
8. Interfaces: internal/external import edges are recorded per file in the catalogue; all protected interfaces remain versioned.
9. Runtime: Absolute-path startup/check/session listing and explicitly limited internal code kit. check/start/sessions/kit flags → truthful readiness or owned new/resumed service.
10. Security: No automatic acquisition/browser/model launch; Visual needs sqlite3; no private brand/session capture in code kits.
11. Limitations: Old text docs lag code; new comprehensive checkpoint supersedes source-kit breadth, not product contracts.
12. Tests: `studio_ui_tests/test_http.py`, `studio_ui_tests/test_local_tools.py`, `studio_ui_tests/test_service.py`; evidence IDs local, sprint
13. Remaining: Old text docs lag code; new comprehensive checkpoint supersedes source-kit breadth, not product contracts.

## Per-file exact implementation catalogue


### `creative_core/__init__.py`

M5 Phase 1: independent, local-only creative document core.

SHA-256 `de661c1577c67cf9e9b5e11330dc066ae205abc877e2f93d6f6e2597d4a0de8f`; bytes 501. Imports: `.document`, `.operations`, `.persistence`, `.validation`


### `creative_core/document.py`

Library-independent creative@1 documents. No I/O or external dependencies.

SHA-256 `3d413228600be1aad8ff9abdbf676a4f8a3d45e8ebb910fdb4320eb39ede988a`; bytes 1766. Imports: `copy`, `hashlib`, `json`

- `CreativeError` at line 12
- `canonical(value)` at line 16
- `core(document)` at line 21
- `fingerprint(document)` at line 25
- `new_document(identity='synthetic-project')` at line 29

### `creative_core/operations.py`

Pure transactions: callers receive a new validated document or an error.

SHA-256 `e5cbbc032981964e3643f3dd2414afc019aab2787c2882ddb7457496194795cf`; bytes 8951. Imports: `.document`, `.validation`, `copy`, `hashlib`, `re`, `uuid`

- `_commit(doc, candidate, root, label)` at line 8
- `apply(doc, operation, root)` at line 22
- `_travel(doc, root, delta)` at line 119
- `undo(doc, root)` at line 136
- `redo(doc, root)` at line 140
- `approve(doc, reviewer, root)` at line 144. Record a caller-confirmed human review; not authentication or factual verification.
- `snapshot(doc, name, root)` at line 156

### `creative_core/persistence.py`

Project-confined JSON persistence. No automatic recovery or migration.

SHA-256 `04f279c0364cada548a89eb5eef830a1dea2c8c802ab25179c48fa69b274a62f`; bytes 3903. Imports: `.document`, `.validation`, `hashlib`, `json`, `os`, `tempfile`

- `_pairs(pairs)` at line 12
- `_constant(value)` at line 21
- `_decode(data, root)` at line 25
- `_read(path)` at line 35
- `load(root, name='creative.json')` at line 43
- `file_digest(root, name='creative.json')` at line 47
- `_atomic(path, data)` at line 51. Flush bytes before replacement; cleanup temporary file on ordinary exceptions.
- `save(doc, root, name='creative.json', expected_digest=None)` at line 65
- `recover_previous(root, name='creative.json')` at line 104. Return a validated previous revision. Caller explicitly saves to a NEW filename.

### `creative_core/validation.py`

Strict creative@1 subset validation, including project-local asset checks.

SHA-256 `ace69a7e7ea503477c0c7ee8c1be13f72104853b78a8cde329bfc21016931174`; bytes 13137. Imports: `.document`, `hashlib`, `math`, `pathlib`

- `require(condition, message)` at line 11
- `fields(value, required, optional=(), label='object')` at line 16
- `string(value, label)` at line 22
- `number(value, label, positive=False)` at line 27
- `records(value, label, maximum=MAX_ITEMS)` at line 34
- `confined(root, relative, must_exist=False)` at line 45. Reject all symlinks, traversal and platform-ambiguous relative paths.  This is defense in depth for a trusted local project, not a race-proof OS sandbox.
- `validate_core(doc, root)` at line 69
- `_validate(doc, root)` at line 167
- `validate(doc, root)` at line 243. Validate without modifying the document; normalize failures to CreativeError.

### `media_analysis_agent/__init__.py`

Optional trusted-synthetic agent foundation. No import-time IO or media processing.

SHA-256 `e046a133ef841ecbf5c5339504eef535c63a4b1f92b15acd345d20fc44894505`; bytes 113. Imports: None statically recorded.


### `media_analysis_agent/__main__.py`

Independent JSON-line CLI. Main Studio does not import or start this CLI.

SHA-256 `b30242ff38278f780bbfc229a0c96a5ddabcf4bd240432ec206be5f888afe480`; bytes 2752. Imports: `.backends`, `.controller`, `.policy`, `.protocol`, `argparse`, `asyncio`, `json`, `sys`

- `serve(args)` at line 12
- `main()` at line 46

### `media_analysis_agent/backends.py`

Replaceable interface; no real decoder imports or executable selection by callers.

SHA-256 `e79e9e8948cac6a5f2853e9d5bb64f39b266af5b3517e4f78f7173a75e63002f`; bytes 1905. Imports: `.policy`, `dataclasses`, `pathlib`, `sys`

- `MediaRequest` at line 10
- `Backend` at line 19
  - `Backend.command(self, session, startup)` at line 25
- `select(name)` at line 41
- `capabilities()` at line 50

### `media_analysis_agent/controller.py`

Async optional controller. Only the fixed trusted synthetic backend may launch.

SHA-256 `1c9b2f4e0c47b7b2062c7f50e26f8849bbccdfbc00300bd30b2b56130cafebab`; bytes 14354. Imports: `.`, `.policy`, `.storage`, `asyncio`, `copy`, `fcntl`, `os`, `uuid`

- `Agent` at line 14
  - `Agent.__init__(self, root, *, timeout=WORKER_SECONDS, startup_timeout=START_SECONDS)` at line 15
  - `Agent._log(self, event, code='ok')` at line 41
  - `Agent._status(self)` at line 48
  - `Agent.status(self)` at line 56
  - `Agent._check_open(self)` at line 59
  - `Agent._set_disabled(self)` at line 63
  - `Agent.enable(self, backend='synthetic')` at line 70
  - `Agent._frame(self, proc)` at line 82
  - `Agent._monitor(self, proc)` at line 92
  - `Agent.start(self, *, startup='normal')` at line 101
  - `Agent._confirm_exit(self, proc)` at line 152
  - `Agent._terminate(self)` at line 159
  - `Agent._fail(self, code)` at line 192
  - `Agent.submit(self, value, *, scenario='echo')` at line 202
  - `Agent.submit_media(self, request)` at line 225
  - `Agent._run_job(self, proc, raw, job_id)` at line 233
  - `Agent.wait(self)` at line 252
  - `Agent._stop(self, *, disable, cancel)` at line 261
  - `Agent.stop(self)` at line 283
  - `Agent.cancel(self)` at line 287
  - `Agent.disable(self)` at line 291
  - `Agent.recover(self)` at line 295
  - `Agent.rollback(self)` at line 308
  - `Agent.close(self)` at line 311

### `media_analysis_agent/policy.py`

Unchanged ceilings; these constants are NOT a hostile-worker enforcement boundary.

SHA-256 `bfe5bc2060a6a74d4b44badc1e12515e3838645db66f9d459db1909d657fadf1`; bytes 940. Imports: `pathlib`

- `AgentError` at line 23
  - `AgentError.__init__(self, code, message)` at line 24

### `media_analysis_agent/protocol.py`

Small closed control protocol, NOT a persisted R2 format or media report.

SHA-256 `0b7d0e153869ef10ae5be1eee2e1e4fcc687e1a53d1e05410d5ecd8577b716cb`; bytes 3901. Imports: `.policy`, `json`, `uuid`

- `identifier(value)` at line 8
- `_pairs(pairs)` at line 15
- `decode(raw)` at line 24
- `encode(value)` at line 71
- `ready(value, session)` at line 81
- `result(value, session, job_id)` at line 89
- `request(value, session, scenarios)` at line 97

### `media_analysis_agent/storage.py`

Small trusted-local configuration/diagnostics store restricted to agent runtime.  Reject aliases; this is not a race-proof sandbox against a concurrent hostile local user.

SHA-256 `a1a102b6f876bcd18b8ffd8d3ac1c79bc0322f491b03883ef8f4aca444c65ed6`; bytes 4465. Imports: `.policy`, `fcntl`, `json`, `os`, `pathlib`

- `Files` at line 13
  - `Files.__init__(self, root)` at line 14
  - `Files._path(self, name)` at line 40
  - `Files._open(self, name, flags)` at line 48
  - `Files.read_config(self)` at line 55
  - `Files.config(self, enabled)` at line 77
  - `Files.diagnostic(self, event, code, state)` at line 92
  - `Files.close(self)` at line 103

### `media_analysis_agent/worker.py`

Trusted single-thread synthetic child. No image processing or descendant launches.

SHA-256 `cc9d0de6ffc11f2a3aee95917a2180cd814232985ed5fc32d23a45891716fcc4`; bytes 3461. Imports: `argparse`, `media_analysis_agent.policy`, `media_analysis_agent.protocol`, `os`, `pathlib`, `select`, `signal`, `sys`

- `guard(event, args)` at line 15
- `main()` at line 24

### `media_analysis_agent_v2/__init__.py`

Second, isolated optional-agent revision. No import-time IO or media activation.

SHA-256 `83a4e18bab5d0b702f6614d591ca6123a47b7b1e8225aff6212b99d7f21bd312`; bytes 109. Imports: None statically recorded.


### `media_analysis_agent_v2/__main__.py`

Explicit standalone controller and isolated package management. No Studio integration.

SHA-256 `2b59798fa3b33c528e58c5fc89c6288844befe739003fc4906c36f076a665081`; bytes 3806. Imports: `argparse`, `asyncio`, `json`, `media_analysis_agent`, `media_analysis_agent.backends`, `media_analysis_agent.policy`, `media_analysis_agent_v2.controller`, `media_analysis_agent_v2.packages`, `pathlib`, `sys`

- `serve(args)` at line 16
- `main()` at line 43

### `media_analysis_agent_v2/controller.py`

Synthetic-only completion revision. Reuses the unchanged first foundation.

SHA-256 `ae44cc5a1724fb014440f421d3fd067b8ea201b94b21d271a59dc45817976f94`; bytes 11420. Imports: `.`, `asyncio`, `fcntl`, `media_analysis_agent`, `media_analysis_agent.controller`, `media_analysis_agent.policy`, `os`, `pathlib`, `sys`, `uuid`

- `Agent` at line 15
  - `Agent.__init__(self, root, *, timeout=15.0, startup_timeout=2.0, job_timeout=JOB_SECONDS, wire_limit=16384, session_limit=RESULT_BYTES)` at line 16
  - `Agent._status(self)` at line 34
  - `Agent._revoke(self)` at line 42
  - `Agent._charge(self, count, *, transmit=False)` at line 46
  - `Agent._pending_response(self, job_id=None)` at line 56
  - `Agent._frame(self, proc)` at line 63
  - `Agent._receive(self, proc)` at line 69
  - `Agent._monitor(self, proc)` at line 94
  - `Agent.start(self, *, startup='normal')` at line 98
  - `Agent._terminate(self)` at line 150
  - `Agent._fail(self, code)` at line 162
  - `Agent.submit(self, value, *, scenario='echo')` at line 170
  - `Agent._schedule_expiry(self)` at line 187
  - `Agent._expire(self)` at line 190
  - `Agent._after_validation(self)` at line 198
  - `Agent._run_job(self, proc, raw, job_id)` at line 201
  - `Agent.wait(self)` at line 226

### `media_analysis_agent_v2/packages.py`

Offline first-party bundles and isolated local deployment; no dependency installs.  Package metadata is NOT an R2 analysis format or security qualification certificate.

SHA-256 `2217df25977aef46d8eb04c05c082d701eda7d9967d53e94c3237f3746b676f6`; bytes 10567. Imports: `contextlib`, `fcntl`, `hashlib`, `json`, `media_analysis_agent.policy`, `os`, `pathlib`, `re`, `stat`, `sys`, `zipfile`

- `sha(raw)` at line 25
- `safe(path)` at line 28
- `version(value)` at line 39
- `admission()` at line 46
- `build(destination, release, *, protocol_version=1)` at line 55
- `inspect_bundle(bundle, expected_sha256)` at line 97
- `Deployment` at line 123
  - `Deployment.__init__(self, root)` at line 124
  - `Deployment.install(self, bundle, *, expected_sha256)` at line 128
  - `Deployment.verify(self, release)` at line 142
  - `Deployment.selection(self)` at line 160
  - `Deployment._publish(self, active, previous)` at line 168
  - `Deployment.activate(self, release)` at line 179
  - `Deployment.rollback(self, agent=None)` at line 187
  - `Deployment.command(self, instance)` at line 197

### `media_analysis_agent_v2/worker.py`

Finite synthetic replay/compatibility cases, never real reference media.

SHA-256 `774b318edd564da12e2f0942683d86738f20790c409980aea1b8b4de307898f6`; bytes 2667. Imports: `argparse`, `media_analysis_agent`, `media_analysis_agent.policy`, `media_analysis_agent.worker`, `os`, `pathlib`, `select`, `signal`, `sys`

- `main()` at line 15

### `poster_render/__init__.py`

Phase 2 poster rendering; independent of editor and reel engine.

SHA-256 `18aa6a8920a16fa719918b3ae6dfd9a7e8c62451f4c2112a8bccc0a640d8c3dd`; bytes 165. Imports: `.scene`


### `poster_render/approval.py`

Final export gate. Drafts never create approval records.

SHA-256 `3b2711531ba3048a287a5373fce4833006d51d0f0df94c3b8198a03f46c57200`; bytes 905. Imports: `.scene`, `creative_core`, `creative_core.validation`

- `check_export(doc, policy, engine, receipt=None, draft=True)` at line 7

### `poster_render/backend.mjs`

Temporary external-tool adapter. No installs or automatic provisioning.

SHA-256 `1e664690977db180f310dd0a5a15982b01e6e199ad8ac75aa01a71353e47326e`; bytes 6169. Imports: `node:fs/promises`, `node:module`, `node:path`, `node:perf_hooks`


### `poster_render/scene.py`

Strict render policy and renderer-neutral SVG mapping for creative@1.  No browser, codecs, external resources or creative source modifications here.

SHA-256 `85672084a6e7070b35bf9f2fb79fbc36230714dbc0c56633498eee9f042af880`; bytes 11738. Imports: `base64`, `creative_core`, `creative_core.document`, `creative_core.validation`, `hashlib`, `html`, `json`, `pathlib`, `re`, `struct`, `xml.etree.ElementTree`

- `sha(data)` at line 28
- `_safe_svg(data)` at line 32
- `_asset(asset, root)` at line 56
- `render_identity(doc, policy, engine)` at line 82
- `build_scene(doc, root, view_id, policy)` at line 90. Return derived SVG + layout metadata. Policy is a separately hashed sidecar.  Policy keys: background, safe_margin, required_elements, palette, fonts. Font IDs map to verified family names and scripts (te/en).

### `studio_manual_ui/__init__.py`

Independent manual Studio UI. No import-time IO, agents, renderers or media.

SHA-256 `5899c2ddcf9eb804576097dc4b4d30aa78c1fbc8a3b685eed270dc0251048298`; bytes 83. Imports: None statically recorded.


### `studio_manual_ui/__main__.py`

Explicit local startup; no automatic browser, analysis or renderer launch.

SHA-256 `17059854ca97afefe4559b6fc69e1e235ea46b8686cf6355a32a786f11c057fc`; bytes 1570. Imports: `.server`, `.service`, `argparse`, `datetime`, `json`, `pathlib`, `uuid`

- `main()` at line 12

### `studio_manual_ui/app.js`

Local DOM/form UI only. No renderer, media inputs, external assets or agent launches.

SHA-256 `17b3f14d1ad4df5f5acab5113924b1261321d92193e03c60044b6b419aed2466`; bytes 10775. Imports: None statically recorded.

- `notice` at line 6
- `request` at line 11
- `element` at line 28
- `content` at line 29
- `pendingText` at line 30
- `render` at line 35
- `refreshProjects` at line 86
- `action` at line 97
- `flushText` at line 102
- `run` at line 106
- `commit` at line 122
- `refreshAnalysis` at line 161

### `studio_manual_ui/index.html`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `aa15809612bd8f71e3e6de20dd7dfb9009c85001ff47416d492fa2930b527c61`; bytes 5799. Imports: None statically recorded.


### `studio_manual_ui/server.py`

Loopback-only, same-origin HTTP adapter; static filenames and JSON actions only.

SHA-256 `d1d0d13714529a9d671806f433e96f4dc475022bc0235054e3828bd49facd761`; bytes 6684. Imports: `.service`, `hmac`, `http.server`, `json`, `pathlib`, `secrets`, `socketserver`, `urllib.parse`

- `Server` at line 19
  - `Server.__init__(self, studio, port=0)` at line 22
  - `Server.server_bind(self)` at line 30
- `Handler` at line 35
  - `Handler.setup(self)` at line 40
  - `Handler.log_message(self, *_)` at line 44
  - `Handler.reply(self, status, body, kind='application/json; charset=utf-8')` at line 46
  - `Handler.guard(self, mutation=False)` at line 61
  - `Handler.body(self)` at line 79
  - `Handler.dispatch(self, method)` at line 92
  - `Handler.do_GET(self)` at line 121
  - `Handler.do_POST(self)` at line 122
  - `Handler.do_OPTIONS(self)` at line 123
  - `Handler.do_HEAD(self)` at line 124
  - `Handler.do_PUT(self)` at line 125
  - `Handler.do_DELETE(self)` at line 126
  - `Handler.do_PATCH(self)` at line 127
  - `Handler.do_TRACE(self)` at line 128

### `studio_manual_ui/service.py`

Manual creative@1 operations in owned runtime projects; accepted core stays unchanged.

SHA-256 `0b157a707c9a27d19d7f29eb9fcc453e0e46151dd15dc6c177461a5e10a02305`; bytes 17329. Imports: `copy`, `creative_core`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `re`, `threading`, `uuid`

- `UIError` at line 20
  - `UIError.__init__(self, code, detail, status=400)` at line 21
- `exact(value, keys)` at line 26
- `text(value, maximum=10000)` at line 31
- `integer(value, minimum, maximum)` at line 39
- `color(value)` at line 45
- `project_id(value)` at line 51
- `encoded(value)` at line 59
- `pairs(items)` at line 64
- `decode(raw)` at line 72
- `safe(path)` at line 81
- `read(path, maximum)` at line 94
- `manual_subset(document)` at line 104. Check all historical states BEFORE accepted validation could open asset references.
- `Studio` at line 137
  - `Studio.__init__(self, root, *, resume=False, analysis_provider=None)` at line 138
  - `Studio.close(self)` at line 163
  - `Studio._directory(self, identity)` at line 166
  - `Studio._validate(self, doc, directory)` at line 169
  - `Studio.analysis(self)` at line 174
  - `Studio.document(self, identity)` at line 191
  - `Studio.view(self, identity)` at line 196
  - `Studio.create(self, request)` at line 211
  - `Studio.list_projects(self)` at line 232
  - `Studio.reopen(self, identity, expected_revision=None)` at line 242
  - `Studio._expected(self, identity, revision)` at line 255
  - `Studio.action(self, request)` at line 261

### `studio_manual_ui/styles.css`

apply-text, #apply-position { margin-top: 8px; }

SHA-256 `8e5491de15e02171ba70cf0b86a7428ff902c7f369f84377a7f7b47f7224d6b2`; bytes 5897. Imports: None statically recorded.


### `studio_media_workflow/__init__.py`

Quarantined media-workflow foundation, separate from metadata-only Studio.

SHA-256 `6383e50c05df3c1df02d8584ecb9d90e42ca738a88feb6d0f9719314d3d31889`; bytes 165. Imports: `.containment`, `.store`


### `studio_media_workflow/__main__.py`

Explicit quarantined CLI. No imports, processing, rendering, migration or automatic recovery.

SHA-256 `fa94551f34846f97cd90d42c36096dbaaabbce9acb8ce4106007ba3d7418be22`; bytes 2444. Imports: `.containment`, `.store`, `argparse`, `json`, `pathlib`, `visual_poster_studio.brands`

- `main()` at line 8

### `studio_media_workflow/containment.py`

Fail-closed processing admission. No decoder, worker, sandbox shortcut or launch API.

SHA-256 `9be317296cdbf922d3a507234fde3974c28423144ceb01a1cc9c7288b665d3d4`; bytes 2003. Imports: `importlib.util`, `pathlib`, `platform`, `shutil`, `studio_manual_ui.service`

- `status()` at line 12
- `require_qualified()` at line 21

### `studio_media_workflow/contracts.py`

New quarantined envelope; embedded creative/binding records keep their original versions.

SHA-256 `4e4b48acf6ba75560b50c66e4650a364f8fc50e4bc8dcfecf10004ead85b2916`; bytes 4276. Imports: `creative_core`, `creative_core.document`, `hashlib`, `re`, `studio_manual_ui.service`, `visual_poster_studio.brands`, `visual_poster_studio.project_bindings`

- `require(ok, message)` at line 11
- `commit_name(v)` at line 13
- `digest(v)` at line 14
- `validate(value, root, session_id)` at line 15

### `studio_media_workflow/store.py`

Own namespace, immutable metadata generations, CAS publication and explicit recovery copy.

SHA-256 `f86533586711658c90c808215880e2a591c9d0b515bcb85c8aeefbe98c50f452`; bytes 11712. Imports: `.`, `.contracts`, `copy`, `creative_core`, `creative_core.document`, `fcntl`, `hashlib`, `os`, `pathlib`, `studio_manual_ui.service`, `threading`, `types`, `uuid`, `visual_poster_studio.binding_workflow`, `visual_poster_studio.project_bindings`, `visual_poster_studio.session`

- `sha(v)` at line 14
- `Store` at line 16
  - `Store.__init__(self, root, *, create=False, library=None, name='Quarantined media project', fields=None, brand_hash=None, recovery=None)` at line 17
  - `Store.close(self)` at line 43
  - `Store._pin(self, identity)` at line 45
  - `Store._head(self)` at line 50
  - `Store.head_token(self)` at line 54
  - `Store._generation(self, name)` at line 56
  - `Store._chain(self, name)` at line 61
  - `Store.current(self)` at line 73
  - `Store._reserve(self, size)` at line 76
  - `Store._commit(self, value, expected)` at line 83
  - `Store._admission(self, value, identity, declared_format)` at line 99
  - `Store.admit(self, identity, declared_format, expected_head)` at line 108
  - `Store.request_processing(self, identity)` at line 111
  - `Store.candidates(self)` at line 114
  - `Store.recover_copy(self, commit, destination, *, acknowledge=False)` at line 121

### `studio_png_sandbox/__init__.py`

PNG capability sandbox. Live placement is disabled pending recorded qualification.

SHA-256 `385cf2e9236eab91ca24fc5bcdbcf3dc832ca0431e926acb8f9951eec52c5635`; bytes 89. Imports: None statically recorded.


### `studio_png_sandbox/__main__.py`

Standalone explicit CLI: no change to the accepted Studio launch path.

SHA-256 `5ed24617b51d329d0005d620223e551c51560f822dccdbb869df091e49e1d3b3`; bytes 1924. Imports: `.controller`, `.server`, `.workflow`, `argparse`, `json`, `pathlib`, `studio_manual_ui.service`, `types`, `uuid`, `visual_poster_studio.binding_workflow`, `visual_poster_studio.brands`

- `main()` at line 7

### `studio_png_sandbox/app.js`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `3aae064477328780ce62a86285c1e85bd3f2f8eba15c6126a45af3893317d00a`; bytes 3934. Imports: `/browser_acceptance.js`

- `api` at line 5
- `geometry` at line 6
- `load` at line 7
- `run` at line 8

### `studio_png_sandbox/controller.py`

One-job supervisor for the pinned no-import PNG module. No network or auto retry.

SHA-256 `ade0a16fe2df7dbb73c75d11b649cf58709d526266fcc1399790510476de199f`; bytes 6274. Imports: `dataclasses`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `resource`, `selectors`, `signal`, `subprocess`, `time`

- `Refused` at line 11
- `sha(raw)` at line 12
- `file_sha(path)` at line 13
- `safe(path)` at line 19
- `Pixels` at line 27
- `Decoder` at line 35
  - `Decoder.__init__(self, build)` at line 41
  - `Decoder.decode(self, raw, *, expected_sha256, cancel=None, timeout=15)` at line 53
  - `Decoder._run(self, raw, identity, cancel, timeout)` at line 66

### `studio_png_sandbox/decoder.c`

Application-owned ABI wrapper; LodePNG is compiled unmodified alongside it.

SHA-256 `f73a81ccf6e331d89a4c7e66949e408226f2d4054b63ad420ad678a3210a4d8b`; bytes 2581. Imports: None statically recorded.


### `studio_png_sandbox/helper.c`

Trusted minimal Wasmtime embedding. Receives PNG on stdin, returns header+RGBA.

SHA-256 `825bc4f8df1ca4f12d074125ee4be2b7702146ac7ae2141d5fe3e3db085466ba`; bytes 6163. Imports: None statically recorded.


### `studio_png_sandbox/index.html`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `994dbfe9a611598d578fb4eefb2a7ec41ffbd8611106e44a54926981206146c4`; bytes 1776. Imports: None statically recorded.


### `studio_png_sandbox/server.py`

Optional standalone loopback PNG workflow UI. Never imported by manual Studio.

SHA-256 `68296957edc4c9b05fa2a513c4f9c250bceddb77d268a39d80956ad3b44dbc0f`; bytes 5338. Imports: `.controller`, `base64`, `http.server`, `json`, `pathlib`, `re`, `secrets`, `signal`, `studio_manual_ui.service`, `time`, `visual_poster_studio.fonts`

- `serve(workflow, port)` at line 7

### `studio_png_sandbox/style.css`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `9066891b5ee55cee294875afd3ede7a30a360e0001b6a8cb8ddee50031fb1c02`; bytes 943. Imports: None statically recorded.


### `studio_png_sandbox/unified.py`

Explicit media-workflow@3: accepted core operations + PNGs in one timeline.  Version2 remains frozen-base. No legacy reader or protected schema is extended.

SHA-256 `28298448e1095a0b0c266edf135dab408364cdc26b9b1bcd08f400513362bc79`; bytes 18009. Imports: `.controller`, `.workflow`, `copy`, `creative_core`, `creative_core.document`, `fcntl`, `os`, `pathlib`, `studio_manual_ui.service`, `threading`, `types`, `uuid`, `visual_poster_studio.brand_application`, `visual_poster_studio.project_bindings`, `visual_poster_studio.session`

- `snapshot(s)` at line 15
- `comparable(s, floor)` at line 16
- `Unified` at line 20
  - `Unified.__init__(self, root, library, decoder, *, base=None, binding=None, acknowledge=False, fault=None)` at line 21
  - `Unified._component(self, s, part)` at line 40
  - `Unified._validate(self, s)` at line 44
  - `Unified.current(self)` at line 69
  - `Unified._record(self, s, before, kind, operation)` at line 87
  - `Unified._transaction(self, s, target, kind)` at line 89
  - `Unified.action(self, kind, expected, identity=None, g=None)` at line 91
  - `Unified.edit(self, request, expected)` at line 98
  - `Unified.view(self)` at line 137
  - `Unified.scene(self, *, export_svg=False)` at line 143
  - `Unified.recover_copy(self, name, destination, *, acknowledge=False)` at line 145

### `studio_png_sandbox/workflow.py`

Explicit media-workflow@2 fork: frozen creative@1 base + editable PNG overlays.  No media records are inserted into the accepted manual document/history. The distinct envelope is authoritative; older readers must refuse it. Drafts only.

SHA-256 `93c81b65561a938490959032a79b43c00d0464d941cd1d228d4d7a5c58c656ae`; bytes 22240. Imports: `.controller`, `base64`, `contextlib`, `copy`, `creative_core`, `creative_core.document`, `fcntl`, `html`, `json`, `math`, `os`, `pathlib`, `re`, `struct`, `studio_manual_ui.service`, `threading`, `time`, `types`, `uuid`, `visual_poster_studio.binding_workflow`, `visual_poster_studio.brand_application`, `visual_poster_studio.fonts`, `visual_poster_studio.project_bindings`, `visual_poster_studio.scene`, `visual_poster_studio.session`, `zlib`

- `require(ok, detail)` at line 22
- `packet(tag, data)` at line 24
- `normalized_png(pixels)` at line 25. Fixed unfiltered RGBA container over qualified bytes; zlib supplies DEFLATE. No source-image parsing, profiles, metadata, external references or codec options.
- `geometry(v)` at line 33
- `Workflow` at line 38
  - `Workflow.__init__(self, root, library, decoder, *, base=None, binding=None, acknowledge=False, fault=None)` at line 39
  - `Workflow.close(self)` at line 59
  - `Workflow._brand(self, binding)` at line 61
  - `Workflow._live_locked(self, c, s)` at line 63
  - `Workflow._asset(self, binding, identity, *, export_svg=False)` at line 75
  - `Workflow._usage(self)` at line 86
  - `Workflow._reserve(self, n)` at line 93
  - `Workflow.head(self)` at line 94
  - `Workflow.token(self)` at line 96
  - `Workflow._receipt(self, identity)` at line 97
  - `Workflow._validate(self, s)` at line 102
  - `Workflow._load(self, name)` at line 126
  - `Workflow.current(self)` at line 128
  - `Workflow.candidates(self)` at line 141
  - `Workflow.recover_copy(self, name, destination, *, acknowledge=False)` at line 148
  - `Workflow._publish(self, s, expected)` at line 173
  - `Workflow._next(self, s, expected)` at line 186
  - `Workflow.place(self, identity, g, expected, *, cancel=None)` at line 188
  - `Workflow._constraints(self, s, items)` at line 205
  - `Workflow._transaction(self, s, target, kind)` at line 210
  - `Workflow.action(self, kind, expected, identity=None, g=None)` at line 212
  - `Workflow.scene(self, *, export_svg=False)` at line 225
  - `Workflow.export(self, head, png, svg_sha256, *, cancel=None, expires=None)` at line 232

### `tools/studio_local.py`

Local manual-Studio entry point and bounded internal source recovery kit. No acquisition.

SHA-256 `6ec2e140c30d8a5dad2ad6a4d8886130b07c00dce9b5255007df5f7f6579a996`; bytes 10996. Imports: `argparse`, `hashlib`, `json`, `os`, `pathlib`, `platform`, `re`, `sqlite3`, `sys`, `visual_poster_studio.__main__`, `visual_poster_studio.fonts`, `visual_poster_studio.server`, `visual_poster_studio.session`, `zipfile`

- `regular(path)` at line 18
- `inventory(root=ROOT)` at line 25
- `source_paths(root=ROOT)` at line 58
- `sessions(root=ROOT)` at line 72
- `build_kit(name, root=ROOT, parent=None)` at line 88
- `main(argv=None)` at line 122

### `visual_poster_studio/ai_adapter.py`

Text-only qualification boundary. No subprocess, network, project writes or model loading.

SHA-256 `a09021b20862b79358ee7d45a8954460996dbd366a8cca38e951588745e22bd7`; bytes 6493. Imports: `.project_bindings`, `copy`, `creative_core.document`, `re`, `studio_manual_ui.service`

- `require(ok, message)` at line 10
- `text(value, maximum=300)` at line 12
- `prepare(fields, brand, identity, settings)` at line 18. Caller supplies a live-revalidated pin. Never opens stores or interprets instructions as tools.
- `completion_json(raw)` at line 46. Remove only llama-completion's documented observed terminal marker, not arbitrary prose.
- `validate(raw, request)` at line 54
- `outcome(raw, request, *, failure=None)` at line 68. No automatic retry. Deterministic fallback is an explicit caller/UI choice.

### `visual_poster_studio/ai_capabilities.py`

Read-only capabilities from the accepted renderer/editor, with source identity checks.

SHA-256 `56b9a34f942882ddd93868e7adfa8d922749b70550dedf45bc7df65c50f49c9a`; bytes 2335. Imports: `.fonts`, `.project_bindings`, `.scene`, `creative_core.document`, `pathlib`, `studio_manual_ui.service`

- `manifest()` at line 11

### `visual_poster_studio/ai_constrained.py`

Capability-constrained proposal qualification v2. No inference, UI or publication.

SHA-256 `71337ca62673507090378ac8529a8d653f2526d6ef2a37543daeca5bc3dc14c5`; bytes 12203. Imports: `.`, `.ai_adapter`, `.ai_capabilities`, `.project_bindings`, `.scene`, `copy`, `creative_core`, `creative_core.document`, `math`, `re`, `studio_manual_ui.service`, `uuid`

- `block_schema(roles, low, high)` at line 12
- `prepare(studio, source, identity, settings)` at line 16
- `norm(s)` at line 39
- `similarity(a, b)` at line 40
- `center(e)` at line 42
- `distance(a, b)` at line 43
- `differentiation(plans)` at line 44
- `validate(studio, raw, request)` at line 57
- `reject_or_validate(studio, raw, request, *, failure=None)` at line 100

### `visual_poster_studio/ai_hybrid.py`

Hybrid editorial intent and factual application rationales; no inference or publication.

SHA-256 `6b77b047a709d5be571a8c9f609ec3fa4bfb27031a138dcaff965db14ca25f51`; bytes 7332. Imports: `.`, `.ai_adapter`, `.brand_application`, `.project_bindings`, `.scene`, `copy`, `creative_core`, `creative_core.document`, `studio_manual_ui.service`, `uuid`

- `prepare(studio, source, identity, settings)` at line 15
- `intent(raw)` at line 26
- `rationale(plan, interpretation, response_hash)` at line 33
- `compile(studio, raw, request, measurements)` at line 43
- `reject_or_compile(studio, raw, request, measurements, *, failure=None)` at line 64

### `visual_poster_studio/ai_semantic.py`

Versioned semantic directions and general measured-box packing. No model/UI/project writes.

SHA-256 `c99f4e6bb3db33bbbdb9aab559b5ecd869c5ea121b9bfde10c1f7ae8b3a0cfd2`; bytes 10021. Imports: `.`, `.ai_adapter`, `.fonts`, `.project_bindings`, `.scene`, `copy`, `creative_core`, `creative_core.document`, `math`, `studio_manual_ui.service`, `uuid`

- `prepare(studio, source, identity, settings)` at line 15
- `Measurements` at line 22
  - `Measurements.__init__(self, record)` at line 24
  - `Measurements.get(self, copytext, size)` at line 28
- `palette(binding, mode)` at line 32
- `pack(concept, fields, binding, measure)` at line 35. Generic two-role packer; content-dependent metrics, no catalog or preassigned directions.
- `compile(studio, raw, request, measurements)` at line 59
- `reject_or_compile(studio, raw, request, measurements, *, failure=None)` at line 72

### `visual_poster_studio/app.js`

Local DOM/form UI only. No renderer, media inputs, external assets or agent launches.

SHA-256 `e228c14b1f7d27ab3d6b9586b6a42eb22aae6cbd53e07c794b7c6b5ee535b567`; bytes 50263. Imports: `/brands.mjs`, `/browser_acceptance.js`, `/canvas.mjs`, `/director.mjs`, `/editing.mjs`, `/geometry.mjs`, `/home.mjs`, `/layout.mjs`, `/media.mjs`, `/product.mjs`, `/text_layout.mjs`

- `notice` at line 27
- `request` at line 32
- `element` at line 50
- `content` at line 51
- `pendingText` at line 52
- `render` at line 57
- `refreshProjects` at line 133
- `action` at line 145
- `flushText` at line 150
- `run` at line 154
- `commit` at line 180
- `reopenSaved` at line 200
- `refreshAnalysis` at line 225
- `initializeFonts` at line 258
- `exportButtons` at line 267
- `updatePreview` at line 271
- `b64` at line 294
- `exportDraft` at line 295
- `commitReorder` at line 328
- `reorderLayer` at line 337
- `updateTextStatus` at line 358
- `showWorkflow` at line 383
- `cancelWorkflow` at line 394
- `finishWorkflow` at line 397
- `selectLayer` at line 420
- `placeBox` at line 424
- `updateSelection` at line 428
- `showReceipt` at line 451
- `refreshNavigation` at line 455
- `requestGeometry` at line 489
- `textMeasure` at line 512
- `briefFields` at line 560
- `createContext` at line 561
- `refreshWorkflowVersions` at line 566
- `showCreateBrand` at line 570
- `renderBinding` at line 571

### `visual_poster_studio/binding_recover.py`

Explicit verified pair recovery to a fresh session; never repairs a source project.

SHA-256 `538cc46926ddba38c4ddc725e0240768b694cf412ee7c94454629f9bb8ce7fdf`; bytes 2982. Imports: `.__main__`, `.project_bindings`, `.service`, `.session`, `argparse`, `copy`, `creative_core.document`, `pathlib`, `studio_manual_ui.service`

- `recover(source, identity, commit, destination, acknowledge=False)` at line 11
- `main()` at line 41

### `visual_poster_studio/binding_workflow.py`

Application-owned binding/brief orchestration; no media, model or creative schema changes.

SHA-256 `6c201ce782603e934bad4896509c09f1f58beb9b23fa952b532b485123794e1a`; bytes 7643. Imports: `.brand_application`, `.brands`, `.project_bindings`, `copy`, `creative_core`, `creative_core.document`, `html`, `json`, `studio_manual_ui.service`

- `library(studio)` at line 9
- `pin(studio, value)` at line 10
- `eligible_versions(studio)` at line 23
- `binding_state(studio, identity)` at line 36
- `mark_saved(studio, identity, doc)` at line 45
- `save(studio, request)` at line 46
- `create(studio, request)` at line 50
- `proposal(studio, request)` at line 58
- `change(studio, request)` at line 68
- `bound_scene(studio, identity, scene)` at line 74

### `visual_poster_studio/brand_application.mjs`

Pinned metadata only. No asset/font file loading or user-defined code.

SHA-256 `ba5e680d84987007369da3d7c01840874717bc53179ba277ae506a6085173104`; bytes 2014. Imports: None statically recorded.

- `installBrandApplication` at line 2

### `visual_poster_studio/brand_application.py`

Derived Brand A policy only; existing pins/records remain authoritative. No asset I/O.

SHA-256 `9a8947ac3732e3e5565479c1fc4c8d25ff1eee5e38b66f4ae9c2f58a79cec81d`; bytes 10098. Imports: `.binding_workflow`, `.director`, `copy`, `creative_core`, `re`, `studio_manual_ui.service`, `uuid`

- `policy(binding)` at line 20
- `supported(p)` at line 48
- `overlaps(a, b)` at line 50
- `covers(a, b)` at line 51
- `issues(doc, binding, p)` at line 52
- `validate(doc, binding)` at line 84
- `live(studio, identity)` at line 89
- `status(studio, identity)` at line 96
- `action(studio, request, perform)` at line 104. Guard one existing user transaction; save/history travel never silently repairs records.

### `visual_poster_studio/brand_portability.py`

Bounded logical ZIP_STORED backup; no extraction, SQL import or media decoding.

SHA-256 `663fa1e6f5b1e6f965195cc1f32b93463d9ca33257738b37219379a0b95ffe2f`; bytes 16320. Imports: `.brands`, `.session`, `base64`, `hashlib`, `io`, `json`, `os`, `pathlib`, `re`, `stat`, `struct`, `studio_manual_ui.service`, `uuid`, `zipfile`

- `digest(raw)` at line 11
- `empty()` at line 12
- `snapshot(store, c)` at line 13
- `validate_state(s, omissions)` at line 23
- `fingerprint(s)` at line 67
- `build_package(store)` at line 70
- `_parse(raw)` at line 93
- `parse(raw)` at line 133
- `ancestor(a, b, records, parent)` at line 138
- `plan(parsed, local)` at line 146
- `preview(store, raw)` at line 165
- `restore(store, raw, expected_destination, expected_package, acknowledge, fault=None)` at line 172
- `save_backup(store)` at line 191
- `upload(value)` at line 202

### `visual_poster_studio/brands.mjs`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `e64384123fe0e200d494a6c9f34571ac7efef520769e7013d4ad2de5f3e32827`; bytes 11300. Imports: None statically recorded.

- `installBrands` at line 1
- `status` at line 7
- `fill` at line 8
- `history` at line 14
- `refresh` at line 15
- `run` at line 19
- `data` at line 27

### `visual_poster_studio/brands.py`

Separate metadata-only library. Opaque asset bytes never enter a renderer/decoder.

SHA-256 `044a6e4a591fbc05f559460739dda99eec6c543b45f383d39a053331195822c6`; bytes 16303. Imports: `base64`, `contextlib`, `datetime`, `fcntl`, `hashlib`, `json`, `os`, `pathlib`, `re`, `sqlite3`, `studio_manual_ui.service`, `uuid`

- `check(ok, message)` at line 13
- `string(value, maximum=256, empty=False)` at line 15
- `identity(value)` at line 20
- `canonical(v)` at line 25
- `now()` at line 26
- `timestamp(v)` at line 27
- `payload(v)` at line 33
- `rights(v)` at line 47
- `validate_record(v)` at line 57
- `Store` at line 80
  - `Store.__init__(self, root=ROOT)` at line 81
  - `Store.transaction(self, create=False)` at line 84
  - `Store.put(self, c, v)` at line 117
  - `Store.get(self, c, h)` at line 120
  - `Store.asset(self, c, i)` at line 125
  - `Store.eligibility(self, c, i, scope, destination)` at line 127
  - `Store.describe(self, c, h)` at line 133
  - `Store.list(self)` at line 138
  - `Store.command(self, request)` at line 146

### `visual_poster_studio/canvas.mjs`

Native Pointer Events controller; source edits use the existing one-layer move transaction.

SHA-256 `7bad1c41a2f822a479b0968e5496fdca6a3399f2e5605cb48ff1b8ab433007bf`; bytes 6063. Imports: `./geometry.mjs`, `./layout.mjs`

- `selectionBounds` at line 4
- `toggleSelection` at line 8
- `snappedMove` at line 9
- `sameGesture` at line 34
- `installDrag` at line 35

### `visual_poster_studio/checkpoint_restore.py`

Explicit checkpoint restore to a fresh Visual session; never repairs the source.

SHA-256 `4d318065199bb305956972dc7693a53c1d06e5cc7f3b6bf3814d4ef86df9a0d2`; bytes 2861. Imports: `.__main__`, `.service`, `.session`, `argparse`, `contextlib`, `creative_core`, `hashlib`, `json`, `pathlib`, `re`, `studio_manual_ui.service`

- `restore(source, identity, digest, destination, acknowledge=False)` at line 12
- `_opened(root)` at line 37
- `main()` at line 42

### `visual_poster_studio/director.mjs`

First-party deterministic concept comparison. No provider, model or external asset calls.

SHA-256 `e54367768091d36630f5e5f00de842263325547d298d531f67c791fe4b6f3ae3`; bytes 4299. Imports: `/brand_application.mjs`, `/hybrid.mjs`

- `installDirector` at line 4
- `update` at line 9
- `draw` at line 18

### `visual_poster_studio/director.py`

Reproducible text/vector proposals. No model execution, media or protected formats.

SHA-256 `43099c85b845446eaac672820284c1e7d80abb0c47b5c5d198a01497ff2b8b26`; bytes 11924. Imports: `.`, `.brand_application`, `.project_bindings`, `.scene`, `.session`, `copy`, `creative_core`, `creative_core.document`, `re`, `studio_manual_ui.service`, `uuid`

- `require(value, message)` at line 14
- `source(studio, request)` at line 17
- `wrap(text, columns)` at line 38
- `fitted(text, width, height, preferred)` at line 47
- `luminance(value)` at line 57
- `palette(binding)` at line 60
- `document(identity, plan, binding)` at line 67
- `directions(binding, seed)` at line 79
- `generate(studio, request)` at line 106
- `retain(studio, bundle)` at line 125. Immutable provenance only, never project truth. Orphans remain evidence after failure.
- `select(studio, request)` at line 137

### `visual_poster_studio/editing.mjs`

Pure editing policy. Browser/OS retain shaping, grapheme segmentation and IME ownership.

SHA-256 `64de7a8dbcd66fbcf0d63bf785887e769ded4dd761cd4591ac523b56715ecd94`; bytes 1698. Imports: None statically recorded.

- `compositionActive` at line 2
- `shortcut` at line 3
- `textStats` at line 12
- `nextLayerIndex` at line 13
- `zoomWidth` at line 20
- `dialogStillCurrent` at line 26
- `nudge` at line 27

### `visual_poster_studio/exports.py`

Bounded, explicit draft export handshake; no image decoder, approval or overwrite.

SHA-256 `aa669b6b16692297d48adc82dd648480db8979bed8cb3c0e9d4743d6e050306a`; bytes 7232. Imports: `base64`, `binascii`, `creative_core.document`, `hashlib`, `html`, `json`, `os`, `re`, `secrets`, `studio_manual_ui.service`, `time`

- `Exports` at line 14
  - `Exports.__init__(self, root, *, resume=False)` at line 15
  - `Exports.audit(self)` at line 21
  - `Exports.cancel(self)` at line 55
  - `Exports.begin(self, identity, scene)` at line 56
  - `Exports.finish(self, token, revision, png, qa, current_revision)` at line 64

### `visual_poster_studio/fonts.py`

Pinned local fonts and cmap coverage; shaping belongs to the browser.

SHA-256 `ee30559eea01bcf0193d69f2b8b81fdb85e006965e9f1560af840b0b3707724d`; bytes 3633. Imports: `base64`, `hashlib`, `pathlib`, `struct`, `studio_manual_ui.service`

- `coverage(data)` at line 13. Read cmap formats 4/12 only from hash-qualified, bounded local sfnt bytes.
- `Fonts` at line 39
  - `Fonts.__init__(self)` at line 40
  - `Fonts.css(self)` at line 53
  - `Fonts.public(self)` at line 55
  - `Fonts.runs(self, text)` at line 57

### `visual_poster_studio/geometry.mjs`

UI geometry only; authority is the atomic core transaction validator.

SHA-256 `a12398ca9cbbcab329d9ce8ab5d50d5bb787b47130e252729826e69cf847a525`; bytes 3297. Imports: None statically recorded.

- `targetsFor` at line 2
- `translate` at line 3
- `resizeBox` at line 4
- `installResize` at line 14

### `visual_poster_studio/home.mjs`

Same-document navigation: editor drafts remain in their existing DOM/state.

SHA-256 `745c39c886de5862b2cc1db48c05acc52f8cb75bf138e1a2e2042155e17fef7b`; bytes 5600. Imports: None statically recorded.

- `installHome` at line 2
- `route` at line 6
- `refresh` at line 16

### `visual_poster_studio/home.py`

Ephemeral session catalogue and explicit locked handover; no new persisted format.

SHA-256 `80ceb5064bb224915b019fbe92bd2d22e9e5b239d6d5aa608f715a051afcd8a4`; bytes 2695. Imports: `.service`, `.session`, `pathlib`, `secrets`, `studio_manual_ui.service`

- `catalogue(parent=RUNTIME)` at line 8
- `switch(server, request)` at line 22

### `visual_poster_studio/hybrid.mjs`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `95a385a6e4b1484085d68c14a41b8de138b0426571ce069af79eeab9a8a7104a`; bytes 8207. Imports: `/browser_acceptance.js`, `/text_layout.mjs`

- `measurements` at line 4
- `installHybrid` at line 17
- `clear` at line 21
- `controls` at line 22
- `report` at line 23
- `draw` at line 24
- `refresh` at line 39

### `visual_poster_studio/hybrid_jobs.py`

Explicit, single-flight local-text planning. No HTTP, media backend or source-project mutation.

SHA-256 `213964a3722f0ef5d9594e8abba7234630a49d7e2dd2e124d9eae94749db4ac2`; bytes 12130. Imports: `.`, `.ai_adapter`, `.session`, `copy`, `creative_core`, `creative_core.document`, `hashlib`, `json`, `os`, `pathlib`, `signal`, `studio_manual_ui.service`, `subprocess`, `sys`, `threading`, `time`, `uuid`

- `Cancelled` at line 21
- `Native` at line 23
  - `Native.available(self)` at line 25
  - `Native.execute(self, path, request, cancel, stage)` at line 27
- `Jobs` at line 75
  - `Jobs.__init__(self, studio, executor=None)` at line 76
  - `Jobs.active(self)` at line 79
  - `Jobs._public(self)` at line 80
  - `Jobs.status(self)` at line 86
  - `Jobs.start(self, request)` at line 88
  - `Jobs._stage(self, j, state)` at line 107
  - `Jobs._work(self, j)` at line 110
  - `Jobs.cancel(self, request)` at line 132
  - `Jobs.select(self, request)` at line 139
  - `Jobs.close(self)` at line 152

### `visual_poster_studio/index.html`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `dfa9bab30a206d342b780f8e04257b43d1df320b37d57f6389cf34237586ac6d`; bytes 26718. Imports: None statically recorded.


### `visual_poster_studio/layout.mjs`

Scene interpretation only. No rendering, shaping, schema mutation or drag engine.

SHA-256 `6fbcbc23dccfdf5fb699b748378c4ef58963423d32a797faec30ab7bb065fd75`; bytes 2189. Imports: None statically recorded.

- `sourcePoint` at line 2
- `hitLayers` at line 7
- `nextHit` at line 15
- `clippedBox` at line 16
- `alignPosition` at line 21
- `shellQuote` at line 32

### `visual_poster_studio/media.mjs`

Main Studio integration; legacy requests retain their existing contracts.

SHA-256 `604d783cd68dd87f8976638eb1b37c25b195aff7a18b9418d23287af04186ec4`; bytes 9713. Imports: `/media_gestures.mjs`

- `installMedia` at line 3
- `catalogue` at line 8
- `open` at line 9
- `refreshAssets` at line 10
- `select` at line 11
- `geometry` at line 12
- `overlay` at line 13
- `update` at line 20

### `visual_poster_studio/media_bridge.py`

Fixed-ID main Studio bridge. No paths or format-upgrade shortcuts from HTTP.

SHA-256 `f2b7e337bc79296c66cbe70cce827dbaaf528495581fe5457d1457da9625651c`; bytes 7956. Imports: `.brand_application`, `.brands`, `base64`, `copy`, `creative_core.document`, `json`, `pathlib`, `re`, `secrets`, `studio_manual_ui.service`, `studio_png_sandbox.controller`, `studio_png_sandbox.unified`, `time`, `uuid`, `visual_poster_studio.session`

- `Media` at line 10
  - `Media.__init__(self, server)` at line 11
  - `Media.close(self)` at line 12
  - `Media.library(self)` at line 15
  - `Media.decoder(self)` at line 16
  - `Media.get(self, identity)` at line 17
  - `Media.listing(self)` at line 21
  - `Media.fork(self, v)` at line 31
  - `Media.check(self, v, fields)` at line 40
  - `Media.open(self, v)` at line 44
  - `Media.action(self, v)` at line 45
  - `Media.scene(self, v)` at line 46
  - `Media.overlay(self, v)` at line 50
  - `Media.begin(self, v)` at line 56
  - `Media.finish(self, v)` at line 60
  - `Media.navigation(self, v)` at line 83
  - `Media.assets(self, v)` at line 91
  - `Media.recovery(self, v)` at line 98
  - `Media.recover(self, v)` at line 100
- `require_id(value)` at line 103

### `visual_poster_studio/media_gestures.mjs`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `cd9bef884e50196313e5ae1740f79b3331cbbda19d909e6c437ebd12a7ab09a2`; bytes 5467. Imports: `/canvas.mjs`, `/geometry.mjs`

- `hitPNG` at line 3
- `installPNGGestures` at line 4
- `current` at line 9
- `layer` at line 10
- `show` at line 11
- `render` at line 12
- `choose` at line 13
- `finish` at line 14
- `cancel` at line 15
- `begin` at line 16
- `move` at line 20
- `up` at line 21

### `visual_poster_studio/product.mjs`

Connected Create and progressive experience levels; no alternate document model.

SHA-256 `e08394bba2b386c649da794ce4bd0d2e0fbd61c88ab4f4f26e4edba1820fd9b8`; bytes 7520. Imports: None statically recorded.

- `installProduct` at line 2
- `apply` at line 11
- `brands` at line 14
- `info` at line 15

### `visual_poster_studio/product.py`

Connected product entry points. Protected documents/bindings remain authoritative.

SHA-256 `a40550d155dda986d7a499981d99fa2b2d62c6954f743e40265ac3976ba59a3a`; bytes 5149. Imports: `.`, `.brands`, `.hybrid_jobs`, `studio_manual_ui.service`

- `create(server, value)` at line 4
- `history(server, value)` at line 20
- `capabilities(server)` at line 29

### `visual_poster_studio/project_bindings.py`

Immutable document/context pairs with one publication pointer; legacy primaries untouched.

SHA-256 `190bbe1160fa6e63db84400e8398c012e2409b701e95097459276580c9efd6e3`; bytes 12390. Imports: `.brands`, `.session`, `copy`, `creative_core`, `creative_core.document`, `hashlib`, `json`, `os`, `re`, `studio_manual_ui.service`, `uuid`

- `check(ok, message)` at line 9
- `sha(raw)` at line 11
- `brief(value)` at line 12
- `validate(value, session_id, identity)` at line 20
- `valid_commit(value)` at line 31
- `Pairs` at line 33
  - `Pairs.__init__(self, session, journal)` at line 34
  - `Pairs.usage(self)` at line 36
  - `Pairs.directory(self, identity)` at line 43
  - `Pairs.owns(self, identity)` at line 44
  - `Pairs.head(self, identity)` at line 45
  - `Pairs.pair(self, identity, commit)` at line 49
  - `Pairs.chain(self, identity, commit)` at line 63
  - `Pairs.load(self, identity)` at line 75
  - `Pairs.scan(self, manual)` at line 78
  - `Pairs.compatible(self, before, after)` at line 84
  - `Pairs.install(self, manual, identity, doc)` at line 88
  - `Pairs.new(self, identity, pin, fields, origin=None)` at line 90
  - `Pairs.commit(self, identity, doc, binding, expected_head, publish=True, origin_raw=None)` at line 92
  - `Pairs.candidates(self, identity)` at line 126

### `visual_poster_studio/recovery.py`

Append-only bounded save intents/checkpoints. Never repairs primary or previous files.

SHA-256 `47782647dcfb49076bd9532b2aed62f2e9dce0644590e3adf597dbb03ecd2101`; bytes 8017. Imports: `.session`, `creative_core.document`, `hashlib`, `pathlib`, `studio_manual_ui.service`, `uuid`

- `sha(raw)` at line 11
- `Journal` at line 13
  - `Journal.__init__(self, root, *, resume=False)` at line 14
  - `Journal.usage(self)` at line 20
  - `Journal.reserve(self, n)` at line 37
  - `Journal.checkpoint(self, identity, doc)` at line 39
  - `Journal._directories(self, identity)` at line 51
  - `Journal.inspect(self, identity)` at line 60
  - `Journal.save(self, manual, request)` at line 89
  - `Journal.candidate(self, identity, which)` at line 117

### `visual_poster_studio/scene.py`

Single deterministic manual creative@1 to SVG mapping. No renderer or I/O.

SHA-256 `181f104eb0380f2b915340fa16b74a52172062d51a2e11997380ab027271b256`; bytes 3076. Imports: `creative_core`, `hashlib`, `html`, `studio_manual_ui.service`

- `build_scene(doc, fonts)` at line 10

### `visual_poster_studio/service.py`

Composition over accepted manual APIs; separate fresh session and derived scenes.

SHA-256 `65d98b35fd8ed656e3f9e6e571c44dfb36cbb9d0902b3bbf7b327aa769251298`; bytes 14096. Imports: `.binding_workflow`, `.brand_application`, `.exports`, `.fonts`, `.project_bindings`, `.recovery`, `.scene`, `.session`, `creative_core`, `studio_manual_ui.service`

- `VisualStudio` at line 11
  - `VisualStudio.__init__(self, root, *, resume=False)` at line 12
  - `VisualStudio.close(self)` at line 43
  - `VisualStudio.status(self)` at line 44
  - `VisualStudio.analysis(self)` at line 47
  - `VisualStudio._ready(self, identity)` at line 49
  - `VisualStudio.list_projects(self)` at line 53
  - `VisualStudio._decorate(self, value)` at line 61
  - `VisualStudio.view(self, identity)` at line 68
  - `VisualStudio.create(self, request)` at line 70
  - `VisualStudio.action(self, request)` at line 73
  - `VisualStudio._action(self, request)` at line 77
  - `VisualStudio.context_checkpoint(self, identity, doc)` at line 152
  - `VisualStudio.reopen(self, identity, expected_revision=None)` at line 156
  - `VisualStudio.scene(self, identity, revision)` at line 164
  - `VisualStudio.begin(self, request)` at line 172
  - `VisualStudio.navigation(self)` at line 176
  - `VisualStudio.finish(self, request)` at line 193

### `visual_poster_studio/session.py`

Explicit Visual-owned session identity; legacy adoption is deliberately refused.

SHA-256 `51e121b9baea2d64346fee1d0d3e80979e8151a52938372e46ac12766a774596`; bytes 2439. Imports: `.fonts`, `.scene`, `hashlib`, `os`, `pathlib`, `studio_manual_ui.service`

- `sync_directory(path)` at line 11
- `exclusive(path, data, mode=384)` at line 17
- `root_path(root)` at line 22
- `marker(root)` at line 27
- `initialize(root)` at line 40

### `visual_poster_studio/styles.css`

apply-text, #apply-position { margin-top: 8px; }

SHA-256 `b7ee819df9f1df9f6b1cb60f513d076f0878a010342cc2316e24e42121955fa7`; bytes 13077. Imports: None statically recorded.


### `visual_poster_studio/text_layout.mjs`

Explicit text edits only. No new persisted layout fields or font-shaping implementation.

SHA-256 `9dd993c0ec93c89145a1999f381660a59fb84549c48de7a6de464bbb47a39de0`; bytes 2432. Imports: None statically recorded.

- `wrapText` at line 2
- `fitTextBox` at line 24
- `keyboardGeometry` at line 29
- `fontRuns` at line 33

### `poster_render/isolation.sb`

UI/static/runner source; inspect the named module card and source for behavior.

SHA-256 `7c00e6a23c447357e14154658cefde47bfc99995e493c7d217fd39233f34d00f`; bytes 400. Imports: None statically recorded.


## E. Protected interfaces and compatibility


- `creative_core/document.py`: exact format `ai-reel-studio/creative@1`, schema_version1. Core keys include format/schema/id/project/languages/brand/views/assets/content/elements; approvals, versions, history/revision are validated envelopes. Broad core permits more types/styles than strict manual/render subsets; schema permission is NOT renderer/security capability.
- `creative_core/operations.py` and `validation.py`: history1 base operations; history2 reorder requires a complete same-view permutation, expected revision, no duplicate/foreign/missing/no-op IDs; first upgrade needs acknowledged immutable verified legacy checkpoint. History3 `geometry` receives nonempty unique complete x/y/width/height targets, validates all before one commit. Every change creates one revision and full before/after pair. Persisted operations reject unauthorized non-order/non-geometry changes. Version floors stay sticky across Undo/Redo; unknown versions fail; older source readers reject instead of silently dropping fields. A downgrade is not rollback.
- Current approvals clear on appearance-affecting changes, including context; history travel does not restore approval. Historical approved snapshots and exports are never rewritten. Recovery is a new explicit copy, not resurrection of an old approval. Reviewer labels/hash equality do not establish legal/factual truth.
- `studio_manual_ui/service.py:manual_subset` is narrower than the core schema:editable text/rectangle/ellipse with fixed supported style fields, no arbitrary referenced assets. Do not add media fields to legacy creative documents to bypass it.
- `project_bindings.py:validate/brief/Pairs`:binding@1 exact fields format, version, binding_id, session_id, project_id, revision, parent, brand, brief, origin. Brief exact purpose/topic/audience/format poster/instructions. Pin exact brand_id/revision/hash/record. Fields up to2000 codepoints,64 KiB binding; new revision links prior hash. Whole creative.json+binding.json+manifest.json(+origin-binding.json where declared) fsync/readback precede one HEAD replacement. No independent publication or legacy primary mirror. Expected revision/head/impact/hash prevent stale writes;200pair candidates; session recovery128 MiB includes pairs. Benign later brands do not migrate pins; adverse hard rules/current rights can block pinned use. Creative Undo cannot rewind binding.
- `brands.py`:SQLite application_id plus user_version1; records(hash, payload), blobs(hash, data), heads, assets, rights_heads. Record shapes are exact brand/asset/rights types; record/blob UPDATE/DELETE triggers reject mutation. Approved brand binds every asset SHA and rights-event hash. Rights exact status, authority, evidence, scopes, destinations, expires; non-grants carry no permissions; grants require explicit authority/evidence/scope/destination/valid UTCexpiry. Live current event/scope/expiry and approved pins must pass. Later grants cannot silently rescue historical stale approval bindings.
- `brand_portability.py`:studio-brand-backup@1 ZIP_STORED fixed paths/manifest. All entries, hashes, lineage, counts and destination fingerprint verified before restore. Immutable conflicts refuse; incoming advancing grants quarantine to unknown clearance; revocations/expiry never rewound. No project gets approval merely by restoring a blob.
- `studio_media_workflow`:v1 namespace is quarantined metadata only; requires its own marker and refuses active media/processing. Do not promote by JSON flags.
- `studio_png_sandbox/workflow.py`:studio-media-workflow@2 and studio-png-session@1 hold frozen base/binding plus qualified placements. `unified.py:Unified` adds workflow@3/studio-png-session@2, explicit source checkpoint, combined base/PNG timeline and history_floor. v2 reader rejects v3; manual/Visual readers reject foreign markers/no primary. v3 base uses accepted core operations; PNG transactions remain only place/geometry/remove. No reorder or media/base interleaving. v3 logical validation checks full ancestry and rejects forged mutations;100combined transactions/200 generations/64 layers.
- PNG immutable receipts and normalized pixels are hash/profile-bound;`studio-png-export@1` pins head, scene/svg/png/rgba identities. One15s export handshake; one in flight;4MiBSVG/8MiBPNG/20 sets and128 MiB whole media-root retention. Old/incomplete outputs count and are not deleted. Nativebrowser exported PNG goes back through the qualified decoder before publication.
- `VisualStudio`,`Journal`,`Pairs`,`Workflow`:writer lock before reading projects/recovery; immutable files +same-filesystem pointer replacement+directory sync; unsupported sync refuses/blocks or reports degraded status. Injected ENOSPC/interruption is not physical power-loss proof. Missing/corrupt pointers are not silently reconstructed. Explicit selected recovery copies exclude later changes/old exports and preserve source evidence.
- New media reorder, arbitrary font/style fields, conversational multi-operation/provenance, shared content unlink, broader profiles, final approval axes or R2 operational bridges require explicit separately reviewed versioned contracts/authorization. Never rewrite accepted records or invent a migration to make a feature appear supported.


## F. Security, dependencies and licensing
# M5 security, rights, dependencies and licensing

Status: trusted-local development product and narrow separately approved PNG capability profile. Broader GateA remains BLOCKED. No production security acceptance, hostile local user defense or complete offline rebuild closure.

PNG stack:Wasmtime50.0.1 Apache-2.0 WITH LLVM-exception; LodePNG20261102 commit7b2893e35891c0c85bee5595caafaf3c2044b409 Zlib; WASI SDK34.0/LLVM build-time terms and incorporated wasi-libc notices retained by original records. Exact artifacts, hashes, expected absolute paths, commands and missing inputs: `M5_DEPENDENCIES.json` plus `source/docs/PNG_SANDBOX_DEPENDENCIES.json`. Runtime helper/Wasm identities verified read-only for this checkpoint; not executed.

The guest has no WASI/host imports/filesystem/network/process/thread API. Only one application-pinned Wasm module is accepted. Guest hard64 MiB memory;512 KiB Wasm stack/threshold plus8 MiB helper OS stack; one memory/instance/table≤64; threads/shared memory/memory64/GC/components disabled; one compute thread, parallel compilation/Mach service thread disabled and thread count checked. Guest cannot select paths/modules or create workers. Native helper/runtime retains OS privileges and is trusted code:Chrome/Sharp alone is not containment and the helper is not a native kernel FS/network sandbox.

Input≤8 MiB;1..2048 dimensions; RGBA≤16 MiB; PNG control header<256B/stderr≤4096. Entire64 MiB guest plus module/native input10 MiB, input8 MiB, stdout16 MiB, finalRGBA16 MiB and pipe allowance form conservative~114.13 MiB controlled scratch bound, below128 MiB. No guest scratch filesystem. Normalization follows confirmed helper exit. Whole helper RSS and controller measured peak RSS each refuse above128 MiB; measurement overcounts pages. **Total host memory is NOT kernel-enforced.** The1 GiB overall target is not a proven kernel aggregate quota. Native-runtime exploit, host/kernel failure, malicious local actor and underestimated trusted allocations remain residual risks.

Five-billionfuel, helperCPU/wall15s, supervisor≤15s and complete main media operation60s. Singleton OS PNG job lock admits one helper; no auto-retry/restart. Cancellation kills private helper group and reaps it; unconfirmed termination faults supervisor. Final main editor still uses sequential media routes; do not introduce thread/signal changes casually. Trusted local AI is a separate CPU text workload:~13 GiB measured child RSS historically,240s deadline, one job/controller. It is NOT claimed to meet the1 GiB untrusted media quota. Multiple independently started Studios have no machine-wide AI quota.

Supported:static8-bitRGB/RGBA noninterlaced PNG with strict IHDR/contiguousIDAT/IEND and CRC/trailing/decompressed-size validation. Refused:ancillary/metadata chunks, palette, grayscale,16bit, APNG, interlaced, unknownchunks, corrupt/truncated/bomb inputs, SVG, TTF, OTF, JPEG, WebP, video/OCR/reference files. Browser consumes only normalized qualified RGBA-derived PNG, never raw registered bytes. Common ordinary PNGs may therefore refuse; do not silently use a native fallback.

Live rights and approved-brand asset membership/hash/pin/expiry checks occur before decode, after decode and inside publication transaction. SVG export needs redistribute/poster clearance because embedded image bytes are extractable. Removal of revoked placements and historical recovery can remain available without granting render/export. No hash or restored asset equals permission. Brand rules are independent simultaneous constraints:unknown hard prose rules refuse rather than model-interpret; preferences never override rights/protection.

Latest integration defect:full23,518,480-byte Wasmtime identity reads caused long-lived Studio measured RSS refusal after AI. `controller.file_sha` now streams64 KiB, checking the same hashes and leaving all limits untouched.4 focused decoder checks and actual affected AI-to-PNG smoke passed after correction. Historical records saying controller byte-identical apply only before this sprint.

Known vulnerability records are retained evidence, not a new current advisory audit:Wasmtime86 advisory records reviewed at adoption; LodePNG repository reported0 but CVE-2026-112020 concerned utility getFilterTypesInterlaced in lodepng_util.cpp, which was not compiled/linked and interlace refuses. Absence of repository advisories is not absence of vulnerabilities. Review current upstream advisories under future acquisition/release authorization; no network fetch was performed for packaging.

License obligations:keep font OFL copyrights/notice, do not sell fonts alone, reserved-name/modification terms; MIT copyright/permission for runtime/ggml; Apache2 licenses/applicable NOTICE/modification/patent/trademark terms for Qwen/OpenSSL/Wasmtime with relevant exceptions; Zlib origin/notice/altered-source marking; LLVM exceptions/incorporated wasi-libc terms; PythonPSF/historical/native notices; SQLite deliverable public domain does not close all Python/build components; browser/Apple SDK terms separate. First-party project distribution license was not selected. Model/tokenizer/conversion provenance is not completed by an Apache label. Brand-media legal rights remain separate from software licenses.

This internal source checkpoint includes only pre-retained OFL fonts/notices and selected license records; no native runtime, model weights, SDK binaries or user assets. Such artifacts remain explicit external dependencies. Actual wrapper/helper offline rebuild had matched hashes historically; full Wasmtime/RustCargo/LLVM/Python/browser/model-source clean provisioning and transitive distribution audit remain OPEN. Copying into Complete Modules is neither integration nor permission to distribute.

## G. Working journey and evidence scope

Launch → Quick/Guided/Professional → exact brief → optional approved pinned brand → actual local AI → three distinct concepts → review/selection → unified editor → explicit media-v3 PNG copy → qualified PNG edit → committed-edit autosave/Undo/Redo → full restart/reopen → draft SVG/PNG export. Source and latest retained smoke agree for this bounded journey. Full product acceptance, unknown historical source identities and missing modules are not inferred. See section K for the exact evidence, failures and limitations.

## H. Outstanding requirements and acceptance work

Every original requirement remains in section B and the machine inventory. The following records are not complete; their exact source, prerequisite, contract limit and acceptance criterion are preserved.

### M5-001 — Authoritative editable creative documents

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Schema1 remains;37 original tests predate later additive history2/3. Do not claim the old run verifies current code in full.

Acceptance: Validate old and current histories without content reinterpretation; retain source-associated targeted evidence.

### M5-005 — Guided Create

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Same brief contract and additional instructions; not every proposed taxonomy control is implemented.

Acceptance: All guided fields round-trip; switching retains pending text; no mode-driven source migration.

### M5-006 — Professional Studio mode

**IMPLEMENTED BUT NOT FULLY VERIFIED**. UI-density mode exposes existing controls, not the full proposed inspector taxonomy.

Acceptance: Same underlying project/history; keyboard and pointer access; preserve unapplied fields on mode changes.

### M5-011 — Meaningful traceable rationales and creative critique

**PARTIALLY IMPLEMENTED**. Rationales are application-authored layout facts linked to AI response. Broader originality/editorial/visual critique is human-review work.

Acceptance: Complete fact-derived explanation; no fabricated AI authorship or universal quality score; human creative approval.

### M5-012 — Progress, cancel, timeout, error and explicit fallback

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Latest smoke exercised progress/success; prior2G cancellation/timeout checks belong to historical identities. No machine-wide model concurrency quota.

Acceptance: TERM/KILL/reap/group absence; unconfirmed termination faults; no auto-retry; failed job publishes no project.

### M5-013 — Multiple saved brand profiles and immutable approved versions

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Trusted-local reviewer labels; not authenticated legal ownership. No private library is packaged.

Acceptance: Append-only records, explicit revisions, approval pins assets/rights; restart and deny missing clearance.

### M5-014 — Asset identity, provenance, rights scope and expiry

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Registration/hash is never permission; claims remain user assertions. Unknown/expired/revoked/insufficient scope deny.

Acceptance: Live checks before/after decode and under publication transaction; no permission resurrection after restore.

### M5-015 — Brand-library backup, restore and portability

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Separate trusted metadata package; not arbitrary hostile ZIP sandbox. Missing legal blob clearance yields explicit omission; imports may quarantine grants.

Acceptance: Whole-package integrity/lineage preview, stale-plan refusal, one SQLite transaction, immutable history retained.

### M5-017 — Explicit brand-version switching and adverse invalidation

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Benign later versions do not migrate pins; mandatory-rule changes and current rights can block old use. Media-v3 binding is frozen/read-only.

Acceptance: Impact preview/confirmation, new paired revision, current approval clearing; historical records untouched.

### M5-018 — Brand Application A colors, supported typography, rules

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Exact supported rule vocabulary only; unknown hard declarations refuse. Only InterBold/NotoTeluguBlack, no uploaded fonts.

Acceptance: Independent checks before generation/edit/render/export; palette constraints; no AI rule override.

### M5-022 — PNG stacking and base/media interleaving

**BLOCKED BY SECURITY OR CONTRACT**. v3 allows place/geometry/remove, not reorder. PNG overlays are above base. Do not fake reorder by identity replacement.

Acceptance: Explicit approved new envelope/transaction; complete permutation; one Undo; strict replay/old-reader rejection.

### M5-023 — Core layer ordering and atomic geometry

**IMPLEMENTED BUT NOT FULLY VERIFIED**. History2/3 sticky; first upgrade needs explicit acknowledgement and verified checkpoint. Full older suites not rerun for package.

Acceptance: Complete same-view permutations/targets, current revision, atomic one-step undo/redo, no unauthorized deltas.

### M5-024 — Text alignment, wrapping, leading and fitting

**PARTIALLY IMPLEMENTED**. Current text is left aligned,1.65× spacing; wrap inserts explicit newlines for review. Arbitrary leading/alignment/tracking not implemented.

Acceptance: Any future extension needs persisted/render-parity contract; current fit never silently changes approved copy.

### M5-025 — English/Telugu exact Unicode editing and shaping

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Exact text and browser font probes pass; native speaker semantic/typographic acceptance is open.

Acceptance: Exact combining marks/script runs; no normalization/fallback; native visual approval and input-method checks.

### M5-026 — Native Telugu IME acceptance

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Composition safeguards exist; no native Telugu OS IME acceptance was performed.

Acceptance: Real input method composition/candidate selection; no interim mutation/navigation shortcuts; save/reopen exact result.

### M5-027 — Keyboard editing and full accessibility

**PARTIALLY IMPLEMENTED**. Core keyboard paths and labels exist; new PNG keyboard and full screen-reader/focus/contrast acceptance incomplete.

Acceptance: Keyboard-only complete journey, IME-safe shortcuts, focus restoration, assistive-technology review.

### M5-029 — Explicit session resume and crash-safe recovery

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Writer locks, validated pointers and recovery copies; physical power loss, hostile concurrent filesystem and arbitrary filesystems unproven.

Acceptance: Full stop/resume exact state; ENOSPC/sync failures fail closed; explicit recovery never overwrites source or revives approval.

### M5-030 — Named variants, historical approvals and export records

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Core snapshots supported; not a full campaign branching/multi-output management UI. Reviewer strings not authentication.

Acceptance: Immutable snapshots/old exports; new edits clear current approval; history travel never resurrects it.

### M5-031 — Conversational editing with atomic diff/provenance

**BLOCKED BY SECURITY OR CONTRACT**. No implemented selection-scoped AI diff/apply transaction. Imperative manual edits are not this feature.

Acceptance: Separate approved atomic multi-operation/provenance version; explicit Apply/Discard; one reversible action; protected facts unchanged.

### M5-032 — Advanced inspector lock/visibility/opacity/duplicate/unlink/crop

**PARTIALLY IMPLEMENTED**. Some fields exist in broad core schema but strict manual/render subset does not expose/accept all. Crop/masks and persistent locks/visibility not complete.

Acceptance: Capability/contract matrix before enabling; persisted identities and shared-content semantics; undo/export parity.

### M5-033 — Reference Style manual R1

**UNKNOWN / REQUIRES CONFIRMATION**. Previously conditionally accepted per task context; source/evidence deliberately not opened or copied. This checkpoint cannot recover that protected module.

Acceptance: Owner-authorized separate R1 preservation and independent evidence review; do not infer approval from this package.

### M5-034 — R2 synthetic report-contract conformance

**NOT IMPLEMENTED**. Planning contracts exist; no separate r2 contract implementation package found in scoped source. Not implemented by media-agent protocol.

Acceptance: Explicit authorized frozen allowlist/API preflight; synthetic-only tests; no sixth format/real decoding.

### M5-035 — Bounded reference image/poster analysis and English/Telugu OCR

**BLOCKED BY SECURITY OR CONTRACT**. Independent optional agent/defaultOFF; no qualified real backend/OCR/language models. PNG logo decoder does not qualify R2.

Acceptance: Separate R2 authorization; GateA/B/C/D; real fixtures, resource/isolation/security and OCR language acceptance.

### M5-036 — Selective reference application, multi-reference mixing, video style

**BLOCKED BY SECURITY OR CONTRACT**. R2–R6 separately gated; requirements retained, not current implementation or authorization.

Acceptance: Each phase prerequisites/review/rights/contracts/fixtures; reversible protected-asset-safe adaptation.

### M5-037 — Independent optional media agent lifecycle

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Synthetic lifecycle/replaceable package foundation only; ordinary Studio showsOFF/ABSENT. Not broad resource-containment certification.

Acceptance: Explicit enable/start/cancel/stop; no auto retry; confirmed exit/fault; strict validated communication; UI independent.

### M5-038 — Local AI image generation

**NOT IMPLEMENTED**. No adopted qualified image model/runtime/weights/rights package. Listed as future optional in taxonomy but remains an eventual product requirement, not silently removed.

Acceptance: Separate authorized stack selection/rights/security/resource gate and editable integration; do not substitute PNG decoding or templates.

### M5-039 — Cinematic reel creation and poster/reel adaptation

**BLOCKED BY SECURITY OR CONTRACT**. No authorized accepted cross-milestone adapter; M4/M6 workspaces untouched. Still required eventual coordination.

Acceptance: Accepted identified engine baseline, separate adapter authorization, poster/reel content/rights mapping and independent approvals.

### M5-040 — Expanded outputs, dimensions, carousel/campaign/custom

**PARTIALLY IMPLEMENTED**. Current editor fixed1080×1350; legacy prototype larger stills do not qualify editable multi-output product.

Acceptance: Versioned supported profiles/pixel budgets, linked-view semantics, export parity and explicit acceptance per output.

### M5-041 — Final content/fact/brand/legal approval workflow

**PARTIALLY IMPLEMENTED**. Core fingerprint approval/helper exists; current UI exports drafts only. No integrated final factual/legal/brand release authority.

Acceptance: Separate review axes, current immutable inputs, QA/rights evidence and authorized approval; drafts never relabeled final.

### M5-042 — Offline/local independence and no mandatory subscription

**PARTIALLY IMPLEMENTED**. Existing runtime works locally; exact runtime/model/source/SDK/transitive closure and clean offline provisioning NOT proved.

Acceptance: Retain legal source/build inputs/notices; clean no-network provision/build/recover on target; no hidden paid fallback.

### M5-043 — Open-source/licensing/commercial distribution closure

**PARTIALLY IMPLEMENTED**. MIT/Apache/Zlib/OFL research recorded; first-party release license not selected; transitive/native/model-conversion notice gaps remain.

Acceptance: Independent exact artifact/transitive/notice audit; rights to media separate; no release until closure.

### M5-044 — Production integration, engine modification and release

**OUTSIDE M5 SCOPE**. Outside this isolated M5 development/checkpoint authorization, not removed from overall product release process.

Acceptance: Explicit owner authorization, accepted interfaces, recovery/regression/rollback and release signoff before action.

### M5-046 — Deterministic fallback when AI absent

**IMPLEMENTED BUT NOT FULLY VERIFIED**. Explicit separate user selection only. No model means no claim of AI interpretation.

Acceptance: Visible deterministic label; manual remains usable; AI failure never silently publishes templates.

### M5-047 — Brand Kit Wizard and automatic extraction

**NOT IMPLEMENTED**. Manual profile foundation exists; automatic extraction is explicitly future in the design and no prerequisite for entering a kit.

Acceptance: Separate bounded extraction evidence/uncertainty/rights/review gate; human approval before publication.

### M5-048 — Source facts/claims, identity, logo and hard-rule protection

**PARTIALLY IMPLEMENTED**. Claims/quotes lack general automatic verification; PNG aspect/text protection applies, not full identity/face editing or all prose rules.

Acceptance: Preserve approved exact content/identities; unknown hard rules block; no stylistic override or invented factual claims.

### M5-050 — Voice/URL input, advanced effects, motion/audio and print

**NOT IMPLEMENTED**. Proposed/later optional capabilities, not currently enabled or silently declared complete. Commitment priority requires owner confirmation where design labels future.

Acceptance: Separate accepted runtime/persistence/profile/security/rights gates; do not treat design taxonomy as installed capability.

## I. Known issues and technical debt
# Known issues and dependency-ordered remaining work

## Functional blockers

ISS-01:PNG stacking/interleaving absent. `Workflow._transaction` and `Unified._validate` only accept place/geometry/remove PNG deltas. Define a separately approved new workflow/history version, complete ID permutation/same-universe validation, one atomic before/after transaction, sticky compatibility, explicit reader rejection and one-stepUndo/Redo. Preserve receipts, rights, IDs, base paint order and old exports. Numeric/delete-readd tricks are prohibited.

ISS-02:Conversational atomic editing absent. Universal§8 explicitly calls multi-operation/provenance a future contract. Need selection/ambiguous-target handling, before/after diff, protected-text review, explicitApply/Discard and one atomic reversible action. Current independent geometry/style/text transactions are not an implementation. Shared-content unlink, duplicate, visibility/lock/opacity/crop/mask and broad type styling also need supported transaction/render semantics rather than client-only flags.

## Security/rights blockers

ISS-05:BrandB complete-format scope remains partial. Narrow PNG is live; SVG/otherimages/uploadedfonts remain disabled. Each future format requires its own allowlist/decoder/resource/active-reference/font-shaping/rights/profile qualification. Metadata registration is not use permission. Unknown hard brand rules refuse. R2 image/OCR/video boundary remains unqualified; do not generalize PNG approval or old Phase2 sandbox probes.

## Integration blockers

ISS-07:Current optional inference and PNG helper use fixed absolute runtime/model/rpath/build locations. Portable source is not independently runnable without these artifacts; relocation requires reviewed loader/profile/identity compatibility and qualification. Old Phase2 requires external private HyperFrames dependencies. No M4/M6 adapter or authorized engine access; G5 and separately gated Reference/R2 remain open.

ISS-08:Historical docs conflict:rootREADME describes early core, no UI/models; early handoffs say no editor/media; LOCAL_STUDIO_START says registered assets not applied; PROJECT_BINDING_CONTRACT says no automatic colors/fonts and hard rules only displayed; PNG dependency/build records retain live_placement_enabled=false; quarantine v1 alwaysNO-GO;2A–2E AI integrationNO-GO; old unified handoff says controller unchanged. Current source +2F/2G +BrandA +qualifiedPNGv2/v3 +functional sprint supersede only their scopes. Do not rewrite historical records or infer all gates closed.

## Acceptance-only gaps

ISS-03:Native Telugu speaker review/OSIME composition and complete accessibility are unverified. ExactUnicode copying is not Telugu comprehension; browser font probes are not editorial language approval. New PNG keyboard paths are implemented but latest pointer smoke is not a keyboard-only/screen-reader audit.

ISS-04:AI current hybrid uses two text roles and three generic top/middle/bottom relationships. Model supplies editorial interpretation, not all geometry/rationale wording. Avoid claiming unlimited creative novelty, arbitrary instruction satisfaction or human originality approval. SlowCPU≈1–3minutes; earlier14B peaks≈12–14 GiB. No approved Metal fix or source-bundle closure. Existing Qwen8B/semantic14B failures stay failures; hybrid is a separate labelled contract, not changed thresholds.

Recovery:application crash/ENOSPC/sync simulations and restart pass only documented conditions. No physical power-loss certification, hostile filesystem race-proofing, general atomic-replacement proof or authenticated reviewer identity. Missing/corruptHEAD requires explicit selected recovery copy; never auto-overwrite primaries/.previous/history/exports. Quota exhaustion refuses with retained evidence; no cleanup policy.

## Offline/distribution blockers

ISS-06:Retained wrapper/runtime/source metadata is not clean independent rebuild. RustCargo, LLVMbootstrap, SDK/Python/browser/native dependencies, matching model-tokenizer/conversion provenance, complete notices, sourceoffers where applicable and owner first-party license/release signoff remain open. The9.276 GB model cannot fit a256 MiB media deployment target; those are separate product components/requirements, not interchangeable claims.

ISS-09:Checkpoint intentionally excludes protected R1 and privatebrand/project data, all nonselected runtime state/nativebinaries/models/caches. Preserve them separately with owner authorization and exact identities. This package cannot restore user sessions or protected R1 or cold-provision the whole machine. Requirement inventory marks that unknown/exclusion rather than complete.

ISS-10:Complete Modules not found/confirmed from project docs, parent structure and available exact-nameSpotlight lookup. No protected directory was entered, no location guessed, no external copy made. Owner must identify the destination; never overwrite an existing module or conflate archive placement with release.

## Deferred cosmetic/performance work

Improve responsive density, inspector/navigation ergonomics, full poster screenshot framing and noncritical polish only after main functional gaps. Performance profiling/acceleration is separate from re-running random model samples. Keep targeted checks per changed boundary and one focused final journey; avoid repeated broad regressions.

## Recommended execution order

1. Verify package and restore exact authorized source into a fresh approved isolated copy; confirm external dependencies/no other writer. Read master, status, security and source-associated evidence before edits.
2. Resolve narrow PNG-order contract authorization; implement/validate complete versioned reorder without touching protected content; preserve unified editing/export.
3. Resolve essential conversational/advanced-inspector contract decisions without pretending fields exist; implement safe approved transactions with one-stepundo/context/rights checks.
4. Complete native TeluguIME, keyboard/accessibility and broader creative-quality acceptance; ordinary defects within approved boundaries can be fixed autonomously, not repeated design reviews.
5. Seek separate qualified-format/Reference/R2/image-model/reel-engine authorization where required. Keep requirements visible; do not bridge M4/M6 or process unqualified media as a shortcut.
6. Close offline/legal/build provisioning, then run consolidated final functional/security/rights/compatibility acceptance against exact source and artifacts.
7. Only declareM5 complete when every essential committed requirement is implemented and the full authorized end-to-end workflow works; owner approves integration/release separately. No percentage-complete claim.

## J. Development history and decisions


-2026-11-10 Phase1:independent creative@1 core,37 tests; kept FFmpeg/HyperFrames engine intact and integration gated. No Git/worktree initialization or production swap implied.
-Phase2:renderer-neutral SVG +Chrome/Puppeteer and Sharp comparison. Retained font hashes and outputs; Sharp differed and was not accepted as a drop-in. Legacy isolation is not arbitrary import security.
-ManualUI →VisualPoster:new independent plainHTML/CSS/JS/stdlib loopback service, shared SVG/browser-native export; no Fabric/Konva installation. Two pinned weights, transparent fixed profile, fail-closed fonts/glyphs/overflow. Provisional editor research is not a hidden dependency.
-Reorder/history2 and geometry/history3 were explicitly bounded additive envelopes, not a new creative schema. Explicit immutable upgrade checkpoints/sticky reader compatibility and recovery-copy restrictions are protected.
-BrandLibrary/backup and project-binding@1 remain separate stores/envelopes; whole-pair atomic publication avoids partial document/context changes. BrandA adds derived runtime rules without changing pinned record structure.
-2A/2B/2C Qwen8B struggled with geometry/semantics;2D existing14B improved structure but incomplete English rationale;2E bounded correction stillNO-GO.2F deliberately switched to independently labelled AIeditorial/deterministic composition/factual application rationale boundary;2G integrated that foundation after separate authorization. No threshold weakening or indefinite prompt tuning is asserted.
-NativeXPC/VM resource-accounting candidates were unqualified; R2 gates remained blocked. Independent agent was separated to prevent blocking manual product. Quarantine media@1 is metadata-only.
-User later approved narrow PNG Wasmtime/LodePNG capability model with measured trusted overhead and explicit lack of kernel total-host quota. This did not qualify broaderR2 GateA. PNG v2 standalone →explicit v3 combined editor; preserved manual schema and source copy.
-Latest functional sprint connected modes/Create, history/autosave and PNG gestures. Whole-runtime hashing allocation caused controllerRSS refusal, then bounded streaming hash fixed it with unchanged hashes/security limits and focused verification.

These are recorded design/implementation decisions, not future authorization. Exact original chat approval transcripts are not all retained in the project; future protected-contract/release changes require owner approval rather than inferring it from a handoff. No untouched historical record is rewritten by this package.


## K. Tests and verification evidence
# Test evidence and verification boundaries

Packaging does not run product tests, inference, decoding, browser acceptance or a broad regression. Existing records below are retained statements with exact source association where available. A matching subset does not certify all current files. Counts from overlapping historical reruns are NOT summed into a global number.

## core

Original: `.runtime/test-results.txt`; present=True; packaged: `evidence/retained/test-results.txt`.

Historical Phase1 37 cases; later core extensions were not present.

No machine-readable whole-current-source test association inferred.

## phase2

Original: `output/phase2/acceptance.json`; present=True; packaged: `evidence/retained/phase2/acceptance.json`.

Historical prototype4drafts/comparisons/repeats; NOT current hostile-media qualification.

Source association: 0matching and 0different scoped files; see JSON exact lists.

## manual

Original: `docs/STUDIO_UI_HANDOFF.md`; present=True; packaged: `source/docs/STUDIO_UI_HANDOFF.md`.

Historical28 manual UI tests; not rerun.

No machine-readable whole-current-source test association inferred.

## visual

Original: `docs/VISUAL_POSTER_HANDOFF.md`; present=True; packaged: `source/docs/VISUAL_POSTER_HANDOFF.md`.

Historical43 automated/14browser checks; not a current whole-suite rerun.

No machine-readable whole-current-source test association inferred.

## resume

Original: `docs/VISUAL_REORDER_RESUME_CONTRACT.md`; present=True; packaged: `source/docs/VISUAL_REORDER_RESUME_CONTRACT.md`.

Read actual contracts and individual retained evidence references; not fresh power-loss testing.

No machine-readable whole-current-source test association inferred.

## geometry

Original: `docs/VISUAL_GEOMETRY_HANDOFF.md`; present=True; packaged: `source/docs/VISUAL_GEOMETRY_HANDOFF.md`.

Historical targeted history-v3/geometry evidence; not rerun.

No machine-readable whole-current-source test association inferred.

## text

Original: `docs/VISUAL_TEXT_COMPLETION_HANDOFF.md`; present=True; packaged: `source/docs/VISUAL_TEXT_COMPLETION_HANDOFF.md`.

Composition guards/keyboard checks; not native IME/human language signoff.

No machine-readable whole-current-source test association inferred.

## home

Original: `docs/M5_HOME_PROJECTS_HANDOFF.md`; present=True; packaged: `source/docs/M5_HOME_PROJECTS_HANDOFF.md`.

Historical Home/Projects focused checks.

No machine-readable whole-current-source test association inferred.

## brand

Original: `docs/BRAND_ASSET_FOUNDATION_HANDOFF.md`; present=True; packaged: `source/docs/BRAND_ASSET_FOUNDATION_HANDOFF.md`.

Historical SQLite/record/rights tests, not private-library legal audit.

No machine-readable whole-current-source test association inferred.

## brand-portability

Original: `docs/BRAND_LIBRARY_PORTABILITY_HANDOFF.md`; present=True; packaged: `source/docs/BRAND_LIBRARY_PORTABILITY_HANDOFF.md`.

Historical package-preview/restore rights and atomicity evidence.

No machine-readable whole-current-source test association inferred.

## binding

Original: `docs/PROJECT_BINDING_HANDOFF.md`; present=True; packaged: `source/docs/PROJECT_BINDING_HANDOFF.md`.

Historical pair publication/recovery/identity tests; not physical power-loss proof.

No machine-readable whole-current-source test association inferred.

## brand-a

Original: `docs/BRAND_APPLICATION_A.md`; present=True; packaged: `source/docs/BRAND_APPLICATION_A.md`.

Historical exact-rule/palette/font/refusal and integration checks.

No machine-readable whole-current-source test association inferred.

## director

Original: `docs/CREATIVE_DIRECTOR_PHASE1.md`; present=True; packaged: `source/docs/CREATIVE_DIRECTOR_PHASE1.md`.

Historical deterministic planning, not AI.

No machine-readable whole-current-source test association inferred.

## hybrid-f

Original: `docs/CREATIVE_DIRECTOR_PHASE2F.md`; present=True; packaged: `source/docs/CREATIVE_DIRECTOR_PHASE2F.md`.

12 focused tests,2actual language runs; source and measurements bound to historical identities.

No machine-readable whole-current-source test association inferred.

## hybrid-g

Original: `.runtime/studio-ui/visual-director-2g-01/completion-final.json`; present=True; packaged: `evidence/retained/studio-ui/visual-director-2g-01/completion-final.json`.

Final36 targeted Python/34 browser-export checks as recorded; not rerun or added to current25.

Source association: 0matching and 0different scoped files; see JSON exact lists.

## png-security

Original: `.runtime/png-first-001/security-02/results.json`; present=True; packaged: `evidence/retained/png-first-001/security-02/results.json`.

22 distinct base decoder/security checks,0failures; older controller source identity.

Source association: 4matching and 3different scoped files; see JSON exact lists.

## png-lifecycle

Original: `.runtime/png-first-001/lifecycle-final/results.json`; present=True; packaged: `evidence/retained/png-first-001/lifecycle-final/results.json`.

4 additional lifecycle/accounting checks; do not double-count reruns.

Source association: 8matching and 6different scoped files; see JSON exact lists.

## png-workflow

Original: `.runtime/studio-ui/visual-png-workflow-tests-final/results.json`; present=True; packaged: `evidence/retained/studio-ui/visual-png-workflow-tests-final/results.json`.

18 workflow checks.22+4+18=44 historical distinct tests only.

Source association: 8matching and 6different scoped files; see JSON exact lists.

## png-unified

Original: `.runtime/png-unified-001/completion.json`; present=True; packaged: `evidence/retained/png-unified-001/completion.json`.

12 targeted Python+9HTTP and browser/export/restart records; historical pre-sprint UI identities.

Source association: 0matching and 0different scoped files; see JSON exact lists.

## sprint

Original: `.runtime/m5-functional-sprint-01/completion.json`; present=True; packaged: `evidence/retained/m5-functional-sprint-01/completion.json`.

11product/hash+4decoder+6JS+4HTTP=25 targeted;5JS+5Python=10syntax; actualAI103.9s/96.7s;19retained files unchanged.

Source association: 247matching and 0different scoped files; see JSON exact lists.

## agent

Original: `docs/MEDIA_AGENT_COMPLETION_HANDOFF.md`; present=True; packaged: `source/docs/MEDIA_AGENT_COMPLETION_HANDOFF.md`.

Synthetic lifecycle/protocol/package tests; never general media qualification.

No machine-readable whole-current-source test association inferred.

## media-foundation

Original: `docs/MEDIA_WORKFLOW_FOUNDATION.md`; present=True; packaged: `source/docs/MEDIA_WORKFLOW_FOUNDATION.md`.

22 quarantine/admission checks; live processing unconditionally disabled.

No machine-readable whole-current-source test association inferred.

## r2-design

Original: `docs/R2_ARCHITECTURE_DECISION_RECORD.md`; present=True; packaged: `source/docs/R2_ARCHITECTURE_DECISION_RECORD.md`.

GateA BLOCKED, GateB contracts provisional, GateC dependencies, GateD evaluation; no actualR2accepted.

No machine-readable whole-current-source test association inferred.

## local

Original: `docs/M5_LOCAL_PRODUCT_HANDOFF.md`; present=True; packaged: `source/docs/M5_LOCAL_PRODUCT_HANDOFF.md`.

Historical9 startup checks, not offline rebuild closure.

No machine-readable whole-current-source test association inferred.

## dependency

Original: `docs/PNG_SANDBOX_DEPENDENCIES.json`; present=True; packaged: `source/docs/PNG_SANDBOX_DEPENDENCIES.json`.

Recorded exact licensing/security/build inputs; not a new current-upstream audit.

Source association: 0matching and 0different scoped files; see JSON exact lists.

## excluded-r1

Original: `None`; present=False; packaged: `not copied / this checkpoint verification`.

Protected R1 content/tests/handoffs not read or copied; acceptance claims not independently reviewed here.

No machine-readable whole-current-source test association inferred.

## checkpoint

Original: `None`; present=False; packaged: `not copied / this checkpoint verification`.

This task verifies copy/hash/ZIP/extraction/document paths/source preservation only; no product tests executed.

No machine-readable whole-current-source test association inferred.

## Latest working journey

Source confirms product.create uses binding_workflow.create; product.mjs opens existing hybrid controls; hybrid_jobs verifies pinned artifacts and publishes selected paired drafts; media_bridge forks explicit Unified; media.mjs routes accepted edits/scenes/export to existing envelope; media_gestures commits one captured-head geometry delta; app.run autosaves canonical edits; scene/QA/export/reopen use existing sources. Latest evidence records actual model103.9s then96.7s after a technicalRSS integration fix, three differentiated concepts, PNGplace/drag/resize/Undo/Redo, textedit/Undo/Redo, draftSVG+PNG and full service stop/resume.19 retained files/state unchanged; SVG6adcdc1304752d600650dba4ea6cfd9e6bd6171d585d9c356649300973a4f8ff; PNGc3432468a11d8a4624d0216d0f8d85a26b53dc4443c6b8b8e4c2f8015576b62c. Browser parity is a trusted client measurement, not independent server raster.

Initial failures remain visible:first fixture library wrongruntime-root refusal; initial PNG controller RSS refusal, no publication; one restartport8778address-in-use then8779resume; stale temporarytabs/locator retargeting. A raw SVG substring assertion initially failed because text was split across script tspans; parsed concatenated textnodes matched exactEnglish/Telugu andno product defect was inferred. These attempts are not passing tests. The second AI execution was an affected integration recheck, not retry-to-manufacture language validity.

22basePNG+4additional lifecycle+18workflow=44 historical distinct tests;12unified+9HTTP are separate integration evidence.2G's36Python+34browser/export=70 are historical categories, not70new currenttests. Latest25targeted+10syntax are not added to historical reruns. Fault injections are not actualOScrash, diskexhaustion or physical power loss. No latest native Telugu IME, full accessibility, broad creative quality, malicious native host or cleanoffline provisioning acceptance.

## L. Restart and recovery
# Restart, source restoration and recovery

## Understand scope first

Exact recovery means the listed source bytes/modes are preserved. It does not mean private projects/brandlibraries/protected R1 or externalPython/browser/model/Wasmtime/SDKs are included. Keep existing original runtime/project data untouched; this package is on the same disk until owner copies it to independent media. SHA256 detects corruption, not malicious replacement of both data and manifests. Archive receipt is an external trust anchor to retain separately; not a digital signature.

## Verify without writes

```sh
python3 -I -B '/ABSOLUTE/PACKAGE/tools/verify_package.py' --root '/ABSOLUTE/PACKAGE'
```

This checks structure, every payload digest/size/mode, missing/unexpected files and documented status schema; it prints external dependencies without opening outside paths, installing or launching anything. It excludes only the authoritative root manifest itself from self-hashing; archive receipt records its hash and full archive hash. Preserve .zip.sha256 receipt separately. `manifests/CAPTURED_SOURCE.json` binds the original source, not generateddocs.

## Restore into a fresh isolated directory

```sh
python3 -I -B '/ABSOLUTE/PACKAGE/tools/restore_source.py' --root '/ABSOLUTE/PACKAGE' --authorized-root '/ABSOLUTE/OWNER_APPROVED/ISOLATED/WORKAREA' --destination '/ABSOLUTE/OWNER_APPROVED/ISOLATED/WORKAREA/NEW_UNUSED_M5'
```

It first verifies the full package, requires an existing real approvedroot and nonexistent strict child destination, rejects traversal/symlinks/aliases and exclusively creates/copies only source-relative paths with recordedmodes. It never executes product code or writes external dependencies. For exactpre-handoverbytes use recovery artifact; portable source adds master/status documentation. Do not use a production/M4/M6/frozen/R1 directory as either parameter. No restoration into an existing working copy/merge/overwrite is supported. Missing dependencies remain missing, not auto-downloaded. Wrong destination/sourcealias refuses; incomplete failure output is retained, not silently deleted.

## Check and launch

Original workspace:
`/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`

```sh
cd '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio'
python3 -I -B tools/studio_local.py check
python3 -B -m visual_poster_studio --port 8766
```

Open `http://127.0.0.1:8766`. Alternative `'/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/Start Studio.command' start --port 8766` starts from anycwd. `--port 0` selects a free port without evicting anotherprocess. No package manager/install/AI/backend is automatically launched. Check verifies local font source/SQLite presence, not browser/modelexecution, advisories or offline distribution. Original model/PNG artifact paths and native rpath must match or remain disabled; relocation needs separately authorized qualification, not editing immutable manifests. Tests may contain original workspace anchors; inspect before running restored tests.

Fresh launch creates a new Visual-owned session. For existing normal owned data:

```sh
python3 -B -m visual_poster_studio --resume --root '/ABSOLUTE/EXISTING/OWNED/VISUAL_SESSION' --port 8766
```

OSwriterlock/Visual and manual identity/fontprofile/document/history/context/exports validate before projectaccess. Resume is explicit; never adopt a legacy or acceptance-evidence root. Mainservice currently uses default brandlibrary under workspace/.runtime/studio-ui/brand-library; the synthetic sprintsmoke injected its own fixture library and is not realbrandpermission or recommendedproductiondata. Source-onlyrestore does not recreateprivate projects. Owner must make a separately authorizedconsistent privatebackup; do not copy independentlyselectedcreative/bindingfiles or use a testsuite as a restoretool.

Stop with Ctrl+C in the terminal that owns the service and wait for controller shutdown/writerlockrelease. Do not kill arbitrary ports/processes. Inferencecancel/close confirms childtermination; faults requireexplicitdiagnosis, no auto-restart. Server printsstartup errors; UI displaysapplicationfailures. Inspect owned session/hybrid-jobs/<id>/{status, termination, command}.json andstdout/stderr, pendingjournal/pair/mediaHEAD throughread-onlytools. Do not publish diagnostic/privatebriefs outside authorizedchannels.

## Explicit recovery commands

Unbound Visual journal:stopservice;`python3 -B -m visual_poster_studio --resume --root '<ownedsession>' --recover-copy '<projectUUID>' --candidate after`. This creates a new session; selectedlaterchangesexcluded. Immutablecheckpoint:read `python3 -B -m visual_poster_studio.checkpoint_restore --help`; explicit source/checkpoint/acknowledgeloss required; boundprojects refuse rawlegacyrestore. Pairedbindings:read `python3 -B -m visual_poster_studio.binding_recover --help`; select one validatedpaircommit and freshdestination, not separatebinding/document generations. PNG:mainUI listsvalidatedcandidates and recoversselectedcopy withacknowledgement; CLI/library recover_copy retains source and excludeslaterchanges/oldexports. Do not mutateprimary/.previous/HEAD or overwritecurrentapprovedhistory to repair.

Commandhelps here are instructions, not executedthispackagingtask. Always inspect captured CLI's argparse before a destructive/recoverycommand. Unknownversions/corruptHEAD/unsupportedfsyncfailclosed. Recoverybudget128 MiB, mediawhole-root128 MiB, exportquotas and orphanedartifacts remaincounted; exhaustiondoesnotauthorizecleanup. Physicalpowerloss unverified.

## Minimal verification after resuming development

Do not run tests solely to unpack/read handover. After owner-authorized changes, use source-relevantfresh evidence only. Existing exact targetedcommand (writesprojects, not read-only):`python3 -I -B tools/run_m5_sprint_checks.py --evidence '<workspace>/.runtime/studio-ui/NEW_UNUSED_CHECK_ROOT'`. AI generation/PNGdecoder/browser checks require their acceptedruntime and deliberate test scope; do not run oldbroad orfixed-output scripts blindly. Never useacceptancefixturelegalgrants as real asset permissions.

## M. Next development plan



1. Verify package and restore exact authorized source into a fresh approved isolated copy; confirm external dependencies/no other writer. Read master, status, security and source-associated evidence before edits.
2. Resolve narrow PNG-order contract authorization; implement/validate complete versioned reorder without touching protected content; preserve unified editing/export.
3. Resolve essential conversational/advanced-inspector contract decisions without pretending fields exist; implement safe approved transactions with one-stepundo/context/rights checks.
4. Complete native TeluguIME, keyboard/accessibility and broader creative-quality acceptance; ordinary defects within approved boundaries can be fixed autonomously, not repeated design reviews.
5. Seek separate qualified-format/Reference/R2/image-model/reel-engine authorization where required. Keep requirements visible; do not bridge M4/M6 or process unqualified media as a shortcut.
6. Close offline/legal/build provisioning, then run consolidated final functional/security/rights/compatibility acceptance against exact source and artifacts.
7. Only declareM5 complete when every essential committed requirement is implemented and the full authorized end-to-end workflow works; owner approves integration/release separately. No percentage-complete claim.


**STOP. Handover and preservation do not authorize further feature work or release. M5 remains IN_PROGRESS.**
