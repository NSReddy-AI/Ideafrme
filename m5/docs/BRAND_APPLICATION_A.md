# Brand Application A — implementation and evidence

Decision: GO for the bounded supported metadata-only profiles below. Human acceptance, arbitrary natural-language rule understanding and Brand Application B are not claimed. No external logo/image/font-file loading, media analysis, dependency/model acquisition, offline distribution, M4/M6 integration or release.

## Implemented

Pinned approved palettes apply to hybrid/deterministic concepts and editable layers. Brand-bound color edits must use an approved palette entry (hex case is equivalent); new layers use the approved palette rather than an unapproved default. New palette buttons apply one selected layer color through the existing restyle operation: one revision/history transaction, one-step Undo/Redo, current approvals cleared and historical named versions preserved. No bulk-restyle transaction or protected history extension invented.

Typography metadata is now checked against the existing actual renderer. Inter Bold and Noto Sans Telugu Black map exactly to already retained, hash-pinned faces. Family-only Inter/Noto Sans Telugu declarations resolve explicitly to their sole supported Bold/Black weight; the mapping is shown, not hidden. Empty preferences leave existing pinned defaults. Unsupported names/weights, including Inter Regular, refuse; no system lookup, substitution, registration byte read or external font load. Renderer chooses the same existing script runs, glyph coverage and browser shaping. No font fields added to creative@1.

Rules are evaluated independently of the AI. Known hard restrictions are checked before generation, after compilation, during editing and on bound scene/export begin/finish. Unknown hard rules or incompatible typography block brand application/generation/export with an explanation. Metadata saves, reopening, Undo/Redo and explicit existing context/version switching remain available to protect recovery. Preferences/inspiration stay advisory within hard rules; they cannot grant rights or override restrictions. Existing unbranded workflows are unchanged.

Existing live pin and rights checks are reused; later adverse brand versions/revocations remain authoritative. No changes to brand/project-binding storage or authority. Model assertions do not establish compliance. Approved records/historical documents/exports are never rewritten. Existing projects with previously advisory/unrecognized requirements may now be blocked for NEW application/export; this is an explicit new runtime restriction, not a schema migration or rewritten historical approval. A reviewed new brand revision/explicit binding switch is required to resolve unsupported requirements. Previously generated receipts remain historical, not recertified.

## Exact supported declarations

All brand-bound current documents must use approved colors and supported font metadata, even with no additional rule strings. Exact declarations recognized (case/punctuation intentional; no fuzzy/NLP matching):
- `Only approved palette and supported fonts.` / `Only the approved palette and supported fonts.` / `Use only approved colors.`
- `No additional display copy or invented claims.` — active displayed text must exactly match topic, purpose or audience from the pinned project brief. This prevents additional application/model copy; it does NOT prove the truth of user-provided claims. No rewriting/truncation/normalization. Wrapping that changes literal source text can be refused under this rule; explicitly revise the brief rather than silently reinterpret it.
- `No external assets.` / `No registered assets applied.` — current accepted manual subset already excludes external content/assets.
- `Preserve logo geometry` / `Preserve logo geometry.` — conditional non-mutation: Stage A has no logo instances and never loads/applies/transforms them. This does not satisfy a requirement to place a logo. Such a placement requirement remains unsupported/Stage B.
- `No text overlap.` — conservative layout-box non-overlap.
- `Allow layout variation.` — no extra restriction; ordinary validated layout/hierarchy/paint order remain editable.
- `Minimum safe margin: N px.` — integer0..256; all non-background layer boxes must satisfy it; an exact full-canvas rectangle is a background plate and exempt. No other string is silently treated as this declaration.
- `Minimum font size: N px.` / `Maximum font size: N px.` — integer1..512; contradictory bounds refuse.
- `Minimum text contrast: R:1.` — nominal sRGB fill contrast1..21, integer or one decimal place. Requires a verifiable fully covering prior opaque rectangle, refuses unknown/partial/covered backgrounds; not general compositing, image analysis or accessibility certification.

Unknown declarations remain blocked, including subjective style requests placed in mandatory_rules. Put nonbinding inspiration/preferences in their existing distinct fields or obtain a separate capability decision. No new fields/formats are persisted. The derived UI policy is labelled brand-application-a@1; approved metadata and bindings remain authoritative.

This is a validator, not a general constraint solver. Existing generic layout compilers are reused unchanged; if their actual three designs cannot satisfy a recognized margin/font/contrast requirement, generation refuses rather than weakening rules, shrinking undocumented bounds or fabricating measurements. Some feasible designs may require a future richer compiler; this batch does not promise arbitrary layouts. Branded editor repairs may improve pre-existing violations without introducing/worsening others; exports require complete compliance. Undo can return to an earlier invalid appearance, but cannot resurrect approval or make that state exportable. Unknown requirements cannot be bypassed by an unsupported renderer.

## Implementation boundaries

Created five:
- visual_poster_studio/brand_application.py
- visual_poster_studio/brand_application.mjs
- visual_poster_tests/test_brand_application.py
- tools/run_brand_application_tests.py
- docs/BRAND_APPLICATION_A.md

Modified eight:
- visual_poster_studio/service.py — derived brand status and guarded existing edit dispatch.
- visual_poster_studio/binding_workflow.py — validate current branded document on existing bound render/export path.
- visual_poster_studio/director.py — policy gate and deterministic output validation.
- visual_poster_studio/ai_hybrid.py — pre-generation requirement gate and per-document validation.
- visual_poster_studio/director.mjs — reuse new small metadata-only control adapter.
- visual_poster_studio/app.js — expose selected-layer and update callbacks; preserve selection after palette edits.
- visual_poster_studio/index.html — palette/status/typography mapping and restrictions.
- visual_poster_studio/server.py — one fixed same-origin module route.

creative@1/schema_version1, history1/2/3, core operations/validation/persistence, project-binding records/paired publication, Brand Library SQLite schema, R1, existing renderer/fonts and frozen checkpoint unchanged. No contracts extended. Current requests retain source/binding/capability stale checks; old pending proposals may require explicit regeneration after source/capability changes. Restart Studio after code updates; no hot migration/repair.

Edits validate under existing manual RLock, restore the entire original working document on a rejected edit, and never publish a failed candidate as current project truth. Existing filesystem/journal behavior is reused. A rejected first geometry upgrade may retain an original immutable checkpoint/unpublished recovery candidate created by the existing upgrade path; it does not activate the upgrade or change the document/history. Existing recovery quotas still apply, no evidence deleted. Saving a policy-invalid but schema-valid historical document remains allowed; rendering/export refuses it. Core structural validation is never skipped.

## Targeted tests

Final executed commands, exit0:
- `python3 -I -B tools/run_brand_application_tests.py --run-id visual-brand-application-a-targeted-final --measurements .runtime/studio-ui/visual-director-2c-01/measure-session/browser-evidence-873568072427a6c3.json` —16passed.
- `python3 -I -B tools/run_ai_hybrid_tests.py --run-id visual-brand-application-a-hybrid-regression --measurements <same path>` —12passed.
- `python3 -I -B tools/run_director_tests.py --run-id visual-brand-application-a-director-final` —23passed, including loopback HTTP.
- `python3 -I -B tools/run_local_tools_tests.py --run-id visual-brand-application-a-startup-regression` —9passed.
- Node syntax checks: brand_application.mjs, director.mjs and app.js (module input); Python AST checks passed.

60 final targeted Python tests; no full/legacy/R1 suite. Coverage: branded/unbranded and English/Telugu, three distinct compliant concepts, supported/family-only typography, unknown requirements/weights, atomic color/history/approval invalidation, preserved approved named snapshots, failed edit rollback, margins/non-overlap/font limits, infeasible generation rejection, save/reopen/resume, invalid-state export refusal, rights revocation, approved new-layer defaults and legacy violation Undo/save. No source drift or rejected test writes/child commands. First development run exposed an invalid test fixture that changed stored bytes without advancing revision; corrected to a real core transaction, preserving the contract rather than weakening it. Initial Director HTTP test was sandbox-bind denied; rerun with approved loopback passed. Earlier runs are retained, not added to totals.

Browser verification used a fresh owned session and isolated first-party approved metadata library, zero external assets. Existing actual Qwen3-14B English/Telugu outputs from Phase2G were recompiled under fresh current brand/request/rights/capabilities and exact browser measurements. This is explicitly replay qualification, not a new model inference or new brand-language-understanding claim. Every pair retained three measured structural differences. No new models or repeated latency demonstrations.

Observed actual UI workflows:
1. Branded English: select focal layer, apply approved gold, Undo/Redo, save/reopen and SVG+PNG export.
2. Branded Telugu: same with exact Telugu source text and supported pinned typography.
3. Unbranded English: existing font-size edit/Undo/save/reopen/SVG+PNG unaffected.
4. Unbranded Telugu: same unchanged workflow.

Additional English UI rejection: choose an approved but insufficient-contrast light color for dark headline on light background. Brand guard rejects, returns the original working revision3 and preserves dark headline. This verifies palette approval alone does not override another hard rule. All four successful exports ran the existing browser font/origin-clean/overflow/decoded PNG-RGBA parity gates and reported fonts_loaded=true,overflow=[],parity=true,embedded_fonts=true. This is browser-observed/reported evidence, not a newly independent hostile-client proof. No native IME or full accessibility certification.

Browser command: `python3 -I -B .runtime/studio-ui/visual-brand-application-a-browser-01/start.py` —loopback8786, stopped exit0. After stopping, explicit service resume through the library verified both branded documents/bindings/scenes and all saved states; source drafts remain revision0. Branded documents contain one color transaction, cursor1, revision3 after color+Undo+Redo, approvals empty, exact topic/purpose, unchanged pinned brand and gold focal. Four persisted SVG/PNG hashes independently read back; exactly two bound manifests and two legacy unbound manifests. Details in `.runtime/studio-ui/visual-brand-application-a-browser-01/verification.json` and fixture-proof.json. Browser screenshot: `.runtime/studio-ui/visual-brand-application-a-01/telugu-brand-export.jpg`.

Final source and checkpoint hashes, exact changes, export hashes and evidence links: `.runtime/studio-ui/visual-brand-application-a-01/completion.json`. All generated fixtures/evidence remain fresh isolated runtime data; no prior acceptance evidence overwritten. The test service is stopped.

## Reuse and remaining limits

Reused installed Python standard library, existing core transactions, immutable pin/rights validators, generic layout packer and SQLite. App-specific brand constraints are owned differentiating code; no new rules package/ORM/schema engine needed. Official primary references reviewed for whole-string matching and independent candidate copies: [Python re.fullmatch](https://docs.python.org/3/library/re.html#re.fullmatch), [Python deepcopy](https://docs.python.org/3/library/copy.html#copy.deepcopy). No third-party code copied/adopted. Existing Python/SQLite/font/runtime licence/notice and full offline-build/distribution gaps remain as previously documented; no new licensing closure or external redistribution approval claimed.

Remaining limits: supported exact rule vocabulary only, no arbitrary natural-language interpreter or general layout solver; one-layer color transactions rather than bulk palette swaps; only two pinned weights; literal-copy hard rule restricts additional text/wrapping; nominal contrast assumes solid supported shapes. Broader creative quality, native Telugu visual/IME, full accessibility and prior slow local inference remain open. No new latency/memory qualification was performed. Stage B logos/images/registered font application, real-media security, offline distribution, M6 integration and production release remain separately gated.

STOP after Brand Application A evidence. Recommendation: GO for these supported metadata-only profiles, pending user acceptance. Do not start Brand Application B or broaden rule interpretation automatically.
