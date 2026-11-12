# AI Creative Director Phase 1 — decision and implementation record

## Open-source-first decision before implementation

Official sources inspected 2026-11-11:
- [llama.cpp MIT licence](https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE): local inference candidate; MIT permits commercial reuse/distribution with copyright and licence notice retention. Native runtime/transitive and exact model/tokenizer/quantization licences still require separate qualification.
- [Ollama MIT licence](https://raw.githubusercontent.com/ollama/ollama/main/LICENSE) and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs): schema-constrained local output is a suitable future adapter. Installed executable located, not launched. Model weights are separately licensed; installed executable is not proof of qualified, offline redistributable inference.
- [Outlines Apache-2.0 licence](https://raw.githubusercontent.com/dottxt-ai/outlines/main/LICENSE): structured model generation alternative, not adopted. Redistribution requires licence/NOTICE preservation where applicable and marking modifications; inference/tokenizer/native dependencies add closure work. No package installed or source copied.

Existing inventory already identifies unresolved local model provenance and retained-source/build gaps. No qualified model/weight/tokenizer/runtime manifest exists for this feature in the workspace. Actual model execution is blocked on exact artifact/licence, resource/execution and offline qualification. No model process, service, download or model store access is required by this phase.

Decision: reuse Python standard library canonical JSON/SHA, existing core schema/validation, paired project publisher, pinned-font SVG renderer and browser export. Build our own application-specific brief interpretation, generic compositional alternatives, selection and editing handoff. Not rebuilding inference, shaping or codecs. Existing installed dependencies remain unchanged; no vendoring/acquisition. First-party implementation/source retained in workspace; full independent distribution rebuild remains open. Replacement model adapter must yield validated plans; no runtime dependency on a repository or provider introduced.

## Phase boundary

This is deterministic local concept planning, explicitly labelled as such. It does not invent or paraphrase factual copy, translate, execute free-text instructions or guarantee originality/IP clearance. Three composition strategies are generic and topic-independent, not industry templates. Purpose, topic, audience and instructions are retained in the plan; topic/purpose/audience are user-supplied display copy. Instructions and arbitrary mandatory brand rules are presented for human review, not falsely claimed to be semantically enforced. No assets, registered fonts or templates are applied. Existing pinned Inter/Noto Telugu renderer fonts are the only typefaces; preference mismatch is disclosed.

Plans are derived reproducible objects, not a new authoritative binding format. Selected bundles are retained immutably under concept-proposals/<digest>.json (maximum20 receipts,128 KiB each,4 MiB aggregate). Receipts contain exact inputs, rationale and layers; publication failure may leave a receipt as evidence, never a published project. Only the existing paired HEAD is project truth. Source project must have an explicitly reviewed saved binding/brief and no unsaved document changes. Generation and selection revalidate source revision, exact document hash, binding hash/HEAD and live brand eligibility. Selection recomputes the complete plan bundle, requires its exact digest plus explicit review of instructions/rules, and creates ONE separate paired project. Source document/history/approvals/exports are untouched. The new document starts unapproved at revision0/history v1. Subsequent normal edits/upgrades use existing APIs. Re-selecting the same plan/seed in the same session refuses rather than overwriting; choose another seed for a fresh variant.

No new fields in creative@1, history or binding; generated project uses a fresh binding with the same approved pin and exact brief. Deterministic concept identity derives from source snapshot, seed, planner version/profile/font hashes and concept ID. Exact plan inputs and document are returned for reproducibility. Layout wrapping inserts only explicit newline breaks at whitespace boundaries, retaining original characters and combining sequences; source brief never changes. Oversized/unrenderable copy is refused, never truncated. Browser typography/overflow checks remain authoritative before export. Default limits: source brief limits unchanged, visible topic <=180 codepoints, purpose/audience <=120 each, seed 0..2147483647, plan bundle <=128 KiB; three proposals and one selected project per request.

## Remaining conditions

Arbitrary prose rules require human review; selection acknowledgement is not brand/project approval. No autonomous final compliance claim. Model-powered copy/concept ideation remains unavailable pending exact local artifact qualification. Offline rebuild/distribution closure, native IME/full accessibility and physical power-loss durability remain open. Gate A and media-analysis OFF state unchanged. No R1/M4/production integration.

## Completion evidence

Created:
- visual_poster_studio/director.py — pure deterministic plans, live eligibility, stale-source checks, editable-document mapping and selected-bundle provenance.
- visual_poster_studio/director.mjs — comparison, review and selection UI.
- visual_poster_tests/test_director.py — targeted integration tests.
- tools/run_director_tests.py — fresh-runtime write/process/network guard and source association.
- docs/CREATIVE_DIRECTOR_PHASE1.md — research, boundary and handoff.

Modified:
- visual_poster_studio/server.py — two guarded fixed POST routes and one fixed module asset route; existing Host/Origin/CSRF enforcement retained.
- visual_poster_studio/index.html — local Director panel.
- visual_poster_studio/app.js — editor state and busy-state integration.
- tools/studio_local.py — retain this decision/contract document in future internal source kits; new source modules are already discovered automatically. No source kit built or dependencies copied in this batch.

Commands/evidence:
- python3 -I -B tools/run_director_tests.py --run-id visual-director-targeted-final — results.json/test transcript contains final targeted count, exit status and source hashes; 23 tests expected.
- python3 -I -B tools/run_binding_tests.py --run-id visual-director-binding-regression-001 — 24/24, exit0; no source drift/rejected writes/children.
- node --input-type=module --check < visual_poster_studio/app.js; node --check visual_poster_studio/director.mjs — both exit0.
- Python ast.parse on five Python files — exit0, no bytecode.
- Isolated browser server: python3 -I -B .runtime/studio-ui/visual-director-browser-01/start_server.py, then --resume; loopback8781; both explicitly stopped cleanly (exit0).

Earlier failed runs remain retained: -001 exposed a candidate validation root bug (fixed by pure validation against existing asset-free source root before target directory creation); -002 lacked sandbox loopback binding permission; -003 exposed test-only CSRF-token lookup (fixed to server.csrf). -004 passed18 tests; -005 passed21 tests after adding provenance and palette readability. Counts are not aggregated. These were targeted iterations on observed failures and new functionality, not repeated full regressions.

Browser evidence: .runtime/studio-ui/visual-director-browser-01/browser-results.json, concept-comparison.png and final-editor.png. Observed three different comparison cards, explicit review, new draft in editor, position change, Undo, save and successful SVG/PNG export. Existing browser qualification reported pinned fonts loaded, no overflow and exact decoded PNG parity. Source brief remained revision0 with original text; selected draft became revision2 after movement/Undo. Media Analysis remained OFF/ABSENT. This verifies one English/Telugu workflow, not comprehensive native typography approval or every input length.

Final browser SVG: 70d2cdbc1c437291504f2042cd277d3250808fa81974aa5c38f3154ebf8d92bb
PNG: 2f24988816192c0a109e1dd04be9ca95861daf91ef84c8e25b931a6a19e43c20
Bundle: f5423eabfce355f9ebd6d299e5d4c337a4763ee868ec641e2774fffa27f223a5

Default unbranded concepts include an editable background rectangle for legibility. Brand palettes use their available approved colors; single-color palettes retain transparent negative space and warn. Low-contrast palettes warn and require human review. Preview/export still use the unchanged single SVG scene mapper. Comparison shows rationale/hierarchy/layer data; full typography preview appears when opened in the editor, not a separate comparison renderer.

Limitations: three compositional families with copy-responsive sizing and seeded offsets, not open-ended semantic ideation. Free-text instructions/rules/preferences are retained and surfaced, not automatically interpreted or certified. No new model adapter is falsely advertised as working. Future algorithm changes must increment planner version; retain matching source hash/build evidence when reproducing a receipt. New bindings contain normal fresh UUIDs; scene/layout reproduction is exact for retained documents/inputs, not byte-identical independent sessions with different ownership identities. Session backup must retain concept-proposals as well as bound-projects to preserve rationale; existing recovery-copy tools preserve documents/context but do not promise proposal-receipt transfer. Prior generations/exports/receipts are never deleted automatically. Project limit100 and receipt limit20 bound selection writes.

A next separately authorized step is exact local model/runtime/tokenizer/source/licence qualification and bounded structured-output adapter execution, followed by quality evaluation for original copy and instruction-following. No acquisition or qualification of shared model stores occurred here. Scope complete for safe deterministic planning; model-powered generation remains explicitly blocked. No release/integration authorization inferred. STOP.
