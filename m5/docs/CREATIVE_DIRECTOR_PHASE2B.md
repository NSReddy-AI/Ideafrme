# Creative Director Phase2B — capability-constrained local qualification

Verdict: NO-GO for AI integration. Boundary/qualification improvements implemented; zero AI bundles qualified. No UI integration, new model/runtime acquisition, media execution or release.

## Changes and exact capability boundary

Six new files only:
- visual_poster_studio/ai_capabilities.py — inspected renderer/editor capability manifest, actual PROFILE/MAX_SVG/MAX_DOCUMENT/MAX_ELEMENTS/SPECS constants, verified font loading and hashes of8 accepted implementation sources.
- visual_poster_studio/ai_constrained.py — v2 prepared request, compact constrained schema, source/rights rechecks, exact-copy mapping, technical/structural validation and explicit rejection/fallback.
- visual_poster_tests/test_ai_constrained.py —22 targeted tests.
- tools/run_ai_constrained_tests.py — isolated test runner with write/process/network audit hooks.
- tools/qualify_ai_constrained.py — one-case offline fixed-artifact CPU qualification; exact argv/input/output/resource evidence.
- docs/CREATIVE_DIRECTOR_PHASE2B.md — this handoff.

Existing ai_adapter.py reused for exact model/settings validation, strict completion JSON decoding and failure policy. Existing director.source/document, core validation, brand eligibility and SVG scene builder reused; none modified. No new inference implementation, fonts, packages or libraries introduced. Official upstream tuple generation implementation inspected for reuse: https://raw.githubusercontent.com/ggml-org/llama.cpp/master/common/json-schema-to-grammar.cpp . Installed runtime actually executed field-specific tuple schemas; no upstream code copied or new parser installed.

Exact machine-readable manifest: .runtime/studio-ui/visual-director-2b-01/capability-manifest.json. It contains current source identities, render/editor capabilities and final typed block schema/palette bounds. Supported subset:
-1080x1350 fixed draft poster; transparent surface or explicit filled rectangle.
- Text, rectangles, ellipses; flat6-digit hex palette fills; array paint order.
- Fixed automatic Unicode-run fonts only: Inter Bold700 (00fd6f4691ee8884a33b46bf45851b341927c37c30064f558e1befb242971c49), Noto Sans Telugu Black900 (42a3167fc2d8ca089b03dcbfcdfe673ecaa176545944ea9c50377144947ae383). No family/weight selections from model; actual cmap checked, no fallback.
- Left-aligned text, explicit source newlines,1.65 line-height and1.02 baseline. No automatic reflow/centering/right-alignment/rotation/effects.
- Editor bounds remain integer positions[-1000000,1000000], dimensions[1,4096], text sizes[1,512]; existing movement/resize/atomic geometry/reorder operations unchanged. Qualification admits a STRICTER explicit subset: every box inside canvas,10px coordinate units, text size16..96,2 exact text slots and1..3 shapes per concept. No new editor API invoked or promised.
- Final block format [role,left,top,right,bottom,size,palette_index]. Roles0=headline/topic,1=support/purpose,2=rectangle,3=ellipse. Typed tuple grammar constrains role, corners, sizes and pinned palette indices; independent arithmetic checks require positive extents and in-canvas placement. Shape size must0. Historical draft request@1 is explicitly rejected by final request@2 reader: no width/height-to-corner reinterpretation.
- Text role required exactly once each, no overlap, no later shape covering text. A backdrop intersecting text must fully contain its box, be rectangular and have>=4.5 contrast. Partial overlaps reject in this subset. Conservative copy-fit screen uses actual exact copy,1.2*size per codepoint and1.65*size per explicit line. It is a refusal screen, NOT a browser shaping/overflow proof. No automatic wrapping, truncation, resizing or paint-order repairs.
- Existing limits remain64 layers,32 text layers,20,000 active codepoints,64 lines/text,8MiB document,4MiB SVG,8MiB PNG. Final AI request/raw response bounded32KiB; generated direction records have bounded title/angle/reason and3..5 blocks. No SVG/code/media/paths/URLs/assets/fonts/approval fields from model. Glyph coverage and existing creative@1/manual-subset/SVG compatibility checked transiently; no poster persisted or rasterized. PNG still requires the existing qualified browser shaping/overflow/parity gate.

## Brand, identity and persistence protection

Prepare calls the existing saved-source and live pinned-brand eligibility checks. Only relevant authorized palette/rules/preferences/hash plus brief are sent, not asset IDs, bytes, rights evidence, provenance, raw library records or protected snapshots. Model output cannot replace a brand pin or grant rights. Validate rechecks current document revision/hash, binding/HEAD, eligibility, capability digest and exact prepared request. Even a rehashed palette override is rejected by reconstructing current trusted input. Revocation after preparation rejects the response. Reserved chat/tool control markers in input are refused explicitly rather than silently rewritten.

Palette indices, supported geometry/fonts, exact copy slots and no extra display copy are independently machine-enforced. Plain prose mandatory rules remain human-review items; no semantic compliance certification. Required headline/public purpose copy is preserved OUTSIDE the model by role references, so copying cannot count as comprehension. No generated public factual copy admitted; rationale remains untrusted and subject to claims/originality review. Never treat library metadata approval or asset registration as creative approval. All outputs unapproved; no published project/binding/export mutation. No change to creative@1/historyv3/R1.

## Differentiation gate

Each pair requires>=2 independent measured differences:
1. Headline-center displacement>=200px.
2. Headline/support font-size-ratio difference>=0.35 (unrounded comparison).
3. Headline-to-support spatial axis/sign changes.
4. Visible non-background focal shape changes type or location>=200px; admitted focal shapes must cover>=2% and<85% canvas, minimum side80px.

Editorial angle and rationale lexical Jaccard must each<0.75. This rejects superficial repeats, not proof of semantic originality or professional design. Separate qualitative review is required. Inputs/prompt ask for composition, hierarchy, emphasis and editorial variation without preassigning three layout families. Hand-authored positive fixtures validate compatibility/differentiation; they are NOT AI-generated success evidence.

## Frozen qualification and actual outcomes

Runtime unchanged: llama-completion from llama.cpp0.9.0, commit cd959bae99ff4bed22bef2604f45241c09bbb8c8; Qwen3-8B Q4_K_M weight a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f. Binary/model hashes verified before runs. No Ollama daemon or shared mutable configuration touched. One CPU job at a time, GPU inference disabled, one compute thread and batch thread, context2048, output768 tokens, temperature0, seed19, explicit offline/local model flags. No automatic retry. Trusted synthetic text only; not Gate A media qualification.

Each fresh run retains rubric.json BEFORE execution, exact prepared request/schema/chat prompt/argv, stdout/stderr, exit/resource results and source hashes. Prepared messages were actually the executed prompt; unlike2A, no synthetic request-to-execution association. Final v2 format used for Telugu; earlier local English draft requests retained as unsupported historical experiment artifacts.

Independent intent rubric: families/parent-child participation; reading/books together; calm and welcoming rather than competition; no prizes/prices/invented facts. Telugu brief uses original Telugu purpose/topic/audience/instructions; English expected meanings are not fed as translations. Diagnostic slow mode:240s maximum/request,768 output tokens,1MiB per-file write guard, no core dump, confirmed direct-child exit. This is disclosed qualification behavior, not an adopted production resource contract. It changes no Gate A memory/scratch/thread/time limit.

Executed small set:
- English first: exit0,144.636s,9,298,493,440-byte child RSS (~8.66GiB). Rejected out-of-canvas geometry. Pair structural counts[1,1,1], below2. Global scalar tuple bounds were insufficient.
- English one justified recheck: field-specific corner schema; exit0,136.030s,9,480,732,672-byte RSS (~8.83GiB). Rejected copy overflow:96px headline in900px box cannot fit the exact11-codepoint source under the conservative screen. Shape also follows/overlaps text. Pair headline distances[0,0,0], hierarchy differences[0,0,0], structural counts[1,0,1]. Not three different directions.
- Telugu: final v2 request; exit0,173.669s,9,863,495,680-byte RSS (~9.19GiB). Rejected zero-height boxes (e.g.[0,10,10,11,10,16,1]); pair structural counts[0,0,0]. No repair/render/export. This is a failed qualification, despite valid JSON/exit0.

English metadata reflects family reading/calm togetherness, but angles are closely related. Telugu English rationales include shared reading, family unity, calm/collective learning from original Telugu input: narrow indicative intent evidence BEYOND slot copying. Not a native-speaker review, comprehensive Telugu test or general supported-language pass. Exact Telugu headline retention is external slot mapping and is explicitly not used as comprehension evidence. Neither language produced3 technically valid, meaningfully distinct proposals.

Evidence: .runtime/studio-ui/visual-director-2b-01/{english-review.json,telugu-review.json,performance.json}; individual run directories visual-director-2b-en-001, visual-director-2b-en-002, visual-director-2b-te-001. Diagnostics on rejected raw geometry are labelled as such; never accepted documents. Two English attempts and one Telugu case only; no repeated large suite or endless tuning.

Latency: refinement136.03s was~6% faster than first144.64s, but both exceed2A's83.66s compact prose probe; not controlled same-input benchmarking. Added technical context increased prompt work; output quality did NOT meet the gate. Current138–174s-class CPU workflow is diagnostic/slow, not qualified interactive performance. Reproducibility inputs retained; greedy temperature0 log uses seed sentinel4294967295, no bit-exact/cross-platform guarantee or repeat trial claimed. Child RSS is not total host/unified/descendant accounting. No hard aggregate containment claim.

## Tests and commands

python3 -I -B tools/run_ai_constrained_tests.py --run-id visual-director-2b-tests-final —22/22, exit0, no source drift, rejected writes or child processes. Covers actual profile/fonts,3 compatible hand-authored layouts, exact Unicode/source preservation, unknown feature/approval injection, palette-only/repeated directions, invalid geometry/types/colors, overlap/coverage/contrast, no silent text wrapping, request tampering, rehashed palette override, stale source, current rights/revocation with metadata minimization, malformed JSON, failure behavior, reserved model markers and explicit invocation of existing deterministic fallback without source mutation. No AI result is substituted silently.

Earlier test runs are retained: tests-001 found hand-authored fixture copy-fit errors; tests-002 found partial backdrop overlap; corrected fixtures without weakening validator. tests-003 passed19 before3 further targeted protections. No full legacy regression or UI test suite run; accepted source implementations unchanged. Python files parsed without bytecode.

Actual model commands:
- python3 -I -B tools/qualify_ai_constrained.py --case en --run-id visual-director-2b-en-001
- same --case en --run-id visual-director-2b-en-002
- same --case te --run-id visual-director-2b-te-001

Wrapper execution exit0 means evidence collection completed; child runtime exit0 means inference completed; neither means acceptance. results.json records actual rejected status and full argv. All direct children exited; no model process left running. No browser/UI integration, native Telugu IME/accessibility or PNG parity acceptance newly claimed.

## Metal and offline closure

No Metal workloads in2B. Retained2A context: same runtime/model; MTL0 Apple M4 Pro discovered natively but absent in restricted enumeration; --device MTL0 --n-gpu-layers99, context2048, one compute thread, offline, no warmup. SIGXFSZ(-25) before meaningful generation at0.759/0.911s with1MiB/16MiB per-file guards. The offending fd/path is UNKNOWN; do not assert shader-cache/shared-memory cause. No guard removal, unrestricted environment change or acceleration claim.

Minimum next Metal diagnostic: one separately bounded process-scoped file/syscall trace of that unchanged guarded command, identifying fd/path/open/ftruncate/write/errno/signal. Existing OS tracing tooling only if required privileges are separately approved. Local bounded trace output; no global tracing, SIP weakening, new interposer/build/install, broader filesystem access or guard-free GPU run. Diagnose before considering any resource-profile change.

Offline/licensing gaps remain exactly open from Phase2A: MIT runtime and ggml, Apache-2.0 Qwen/OpenSSL, Apache-2.0 WITH LLVM-exceptions OpenMP notices; complete transitive/advisory review not closed. Cached GGUF tokenizer/config/conversion provenance not matched to upstream source revision; matching runtime/ggml/TLS/OpenMP source, CMake/toolchain/SDK closure, notices, original tokenizer/config/conversion recipe, independently retained bundle and clean offline build/install/recovery still missing. Existing external5.225GB cache is not independent distribution closure. No new dependencies, downloads, weights/tokenizer modifications or mandatory paid/cloud service. No new source vendoring or acquisition authorization inferred.

## Seven integration gates and next corrective action

1. Three technically valid proposals: FAIL for English and Telugu.
2. Meaningful structural differentiation: FAIL, measured above.
3. English intent: indicative positive metadata; end-to-end usable proposals FAIL.
4. Telugu supported scope: narrow family-reading signal characterized; native/general qualification OPEN; usable proposals FAIL.
5. Independent rights/brand enforcement: targeted tests PASS for typed checks/live revocation; subjective prose still needs human review.
6. Rejection and explicitly labelled deterministic fallback: targeted checks PASS. Existing deterministic workflow untouched.
7. Practical execution: finite slow CPU measurements documented; not yet an accepted product performance mode. Metal unqualified.

Overall NO-GO, no criteria weakened to pass. Smallest next corrective step: replace ambiguous corner tuples with named, role-specific box fields and generation-time text-size-dependent minimum extents/paint-order constraints; qualify ONE geometry case before re-running the two-language gate. Do not silently resize/reorder failed plans or swap to the three deterministic templates. If reliable arbitrary geometry remains unsuitable for this model, separately scope AI semantic direction plus a general constraint-based geometry stage, preserving model-led ideation and explicit rejection; not another fixed-layout expansion. No new model acquisition is required merely to test that correction. No UI/media/release work authorized by this report. STOP after Phase2B.
