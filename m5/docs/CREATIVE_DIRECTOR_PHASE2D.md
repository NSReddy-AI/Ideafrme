# Creative Director Phase2D — controlled local model comparison

Decision: NO-GO for model-to-editor integration or selection as a fully qualified creative engine. Qwen3-14B is the stronger structural candidate, but English editorial completeness fails. No threshold, prompt, semantic contract, geometry compiler or existing source changed to accommodate it. Exactly one alternative and two inference executions; no retries.

## Local inventory, shortlist and selection

Read-only local inventory found llama.cpp0.9.0, Ollama0.40.16, cached qwen3:8b, qwen3:14b and gemma2:latest9.2B Q4_0. No daemon launched or model store modified. Selected existing Qwen3-14B Q4_K_M, a post-trained instruction/chat model (not Qwen3-14B-Base). Same family was deliberately preferred to a new acquisition because its cached publisher artifact, permissive licence, known runtime architecture and same chat/tokenizer format allow a tightly controlled comparison without install/download/conversion.

Small shortlist, not additional acquisitions:
- Cached Gemma2 9B offers a different family and smaller weight file5.443GB, but carries custom Gemma terms. Local licence snapshot dates February2024, while current terms page is April2026; pass-through use restrictions/notices and applicability need review. It is not treated as MIT/Apache or automatically commercially redistributable. Not executed.
- Microsoft Phi-4-mini-instruct: official MIT model; efficient128k instruction model, but its listed24 supported languages do not include Telugu. The inspected Unsloth GGUF derivative declares bug fixes and needs exact conversion/modified-artifact verification. Not selected or acquired.
- Ministral3 8B Instruct2512: official Apache-2.0, advertised JSON/system-prompt capability and edge memory suitability; new artifact/quantization/native compatibility and Telugu quality were not established. Includes vision architecture; no media feature adopted. Not selected or acquired.
- Cached Qwen3-14B:14.8B, official post-training/multilingual instruction-following claims,32,768 native context reported in upstream card; cached GGUF advertises40,960. Comparison uses only2048. Larger/slower than8B, but available and architecture-compatible. Vendor language/creative benchmarks are not local acceptance evidence.

Sources inspected:
https://huggingface.co/Qwen/Qwen3-14B/blob/main/README.md
https://huggingface.co/Qwen/Qwen3-14B/blob/main/LICENSE
https://ollama.com/library/qwen3:14b
https://ollama.com/library/qwen3:14b/blobs/a8cc1361f314
https://ollama.com/library/qwen3:14b/blobs/d18a5cc71b84
https://ai.google.dev/gemma/terms
https://huggingface.co/microsoft/Phi-4-mini-instruct/blob/main/README.md
https://huggingface.co/unsloth/Phi-4-mini-instruct-GGUF/blob/main/README.md
https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512/blob/main/README.md

## Exact artifact/licence verification and retention

Selected registry repository registry.ollama.ai/library/qwen3, tag14b, pinned publisher manifest revision bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8. Weight SHA256 a8cc1361f3145dc01f6d77c6c82c9116b9ffe3c97b34716fe20418455876c40e;9,276,184,896 bytes (~8.64GiB). Official publisher page independently identifies the same a8cc1361f314 artifact as Q4_K_M, qwen3,14.8B and9.3GB. All6 local config/model/template/licence/params/nested-manifest records were streamed and matched declared content hashes and sizes. GGUFv3,443 tensors, architecture qwen3, quantization file_type15; embedded tokenizer vocabulary151,936 and Qwen2 pretokenizer. Known qwen3 architecture is already supported by the installed runtime; actual two successful native executions confirm compatibility.

Selected GGUF lacks general.license; this was recorded, not invented. Licence basis is the independently hashed publisher-manifest licence layer d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12 and official upstream/publisher Apache-2.0 records. Initial metadata inspection assumed an embedded licence key and stopped with KeyError; corrected the inspection to use the actual separate licence record before inference. No model mutation or inference retry occurred.

Apache-2.0 permits commercial use and redistribution subject to preserving licence and applicable notices, marking changes, and its patent/trademark provisions. Quantization is a derivative transformation; notices/provenance still matter. Exact publisher artifact revision is pinned; original upstream base-model git revision and conversion/tokenizer recipe were NOT mapped. Those remain redistribution/rebuild closure gaps. No claim of complete commercially distributable package or standalone-tokenizer provenance. Existing installed runtime/ggml MIT, OpenSSL Apache-2.0 and LLVM/OpenMP notice obligations remain as2A; no runtime/source/dependency acquisition.

Acquisition gate did not require a weight download: existing suitable bytes reused,0 model bytes downloaded/copied. Expected full weight acquisition would be9.276GB plus metadata; none requested. Small verified metadata/config/template/licence/params/manifest copies and checksums retained under .runtime/studio-ui/visual-director-2d-01/artifact-records and inventory.json. Weights remain referenced in the existing external cache, not an independently owned distribution bundle. No Gemma terms accepted and no other candidate downloaded. Retention is evidence, not offline-distribution closure.

## Fairness and frozen controls

Frozen source hashes include ai_semantic.py, ai_constrained.py, ai_capabilities.py, ai_adapter.py, director.py and original qualify_ai_semantic.py. New compare_ai_semantic.py changes only selected model/artifact loading and verifies every frozen hash before each execution. Existing Phase2C source and acceptance criteria remain byte-identical.

For BOTH languages, actual prompt.txt and schema.json matched Phase2C baseline byte-for-byte (fairness.json). Same original brief/rules/preferences, chat framing/non-thinking prefill, measurement record, renderer/fonts, strict enum/differentiation/completeness criteria. New session/project IDs are not sent to the model. Same installed llama-completion0.9.0 commit cd959bae99ff4bed22bef2604f45241c09bbb8c8; exact binary hash verified. CPU-only,1 compute/batch thread,context2048,output768,temp0,seed19,offline/local path,no warmup,240s deadline,1MiB per-file child guard. No Metal changes or hardware-acceleration advantage. Observations are single runs, not thermally/cache-controlled benchmark statistics. Greedy seed/repeatability limitations remain.

Complete editorial descriptions were required by the user and Phase2C review BEFORE this comparison. Technical compile status is not an overall acceptance result. Human editorial review was not replaced by model self-assessment or weakened to accept clipped text.

## Results against Qwen3-8B

English14B: exit0,168.663s,11,764,318,208-byte peak child RSS (~10.96GiB),2.66 generation tokens/s,4.04 prompt tokens/s. Frozen compiler passed. Focal/hierarchy choices are unique; pair structural dimension counts[3,3,3], versus8B[3,1,3] and rejected. Three distinct titles: Narrative journey, Shared moment, Quiet invitation. Public required copy exact; fonts/palette/rights remain independently enforced. BUT first rationale ends 'creatinga' and second 'that feels'; both incomplete. First also refers to a child's gaze and parent's smile, imagery not supplied by the text/vector compiler; flagged for scope/intent review rather than silently adding faces/assets. Third rationale is complete. English editorial gate FAIL.

Telugu14B: exit0,217.424s,12,855,459,840-byte peak child RSS (~11.97GiB),2.50 generation tokens/s,3.96 prompt tokens/s. Compiler passed; pair counts[3,2,3], versus8B[3,1,3] and rejected. Directions family gathering, book celebration, quiet learning have concise coherent rationales. Intent reflects family togetherness, shared reading and calm learning from original Telugu input; exact source text is compiler mapping, not copying/comprehension proof. Narrow indicative intent/editorial result positive; broad/native-speaker Telugu qualification still unverified.

Baseline8B English88.147s/~8.63GiB/4.82 generation tokens/s; Telugu115.337s/~8.72GiB/4.66 tokens/s. Alternative roughly1.91x/1.89x wall time and higher RSS, without acceleration differences. Larger model improves structural instruction following at a real CPU cost. Both runs fit the frozen240s diagnostic budget; this is not an accepted interactive/product performance contract or hard aggregate/unified/descendant memory quota. Host target24GiB verified by memory_pressure -Q, which reported72% free before the workload. No stress experiment. Gate A media limits unchanged and NOT qualified by these trusted-text runs.

## Documents, renderer and rights evidence

Six staged unapproved creative@1 documents were produced in fresh runtime roots (not registered in Studio projects). All6 independently loaded byte/value-exact through existing core persistence and supported a core move+Undo without approval resurrection. Existing renderer browser check found pinned fonts loaded and zero overflow for all6. This is geometry/compatibility evidence only, not editorial or production approval. No PNG/media generation, actual product UI integration or asset application. Existing live source/binding/brand eligibility checks executed before preparation and compilation; model cannot grant rights/change pins. Frozen source preserved; current typed checks unchanged; subjective brand compliance still human review.

No repeated full or legacy tests: architecture/validators were frozen. New runner AST syntax passed; actual output verification comprised6 document reload/edit/Undo checks and6 browser bounds checks. Existing20 Phase2C targeted tests are historical evidence, not claimed as rerun here. No technical execution retries; exactly one14B execution per language. Temporary isolated loopback harness stopped cleanly; no model process left running.

Commands:
python3 -I -B tools/compare_ai_semantic.py --case en --run-id visual-director-2d-en-001 --measurements <workspace>/.runtime/studio-ui/visual-director-2c-01/measure-session/browser-evidence-873568072427a6c3.json
Same --case te --run-id visual-director-2d-te-001.
Measurement/bounds harness: python3 -I -B .runtime/studio-ui/visual-director-2d-01/measure_server.py (loopback8783; stopped exit0).

Full argv, model identity and actual response hashes are in each language results.json. Wrapper/runtime exit0 indicate collection/inference success; neither overrides the editorial FAIL. No rationales stripped, completed, paraphrased or regenerated.

## Files, closure and selection decision

Created only tools/compare_ai_semantic.py and docs/CREATIVE_DIRECTOR_PHASE2D.md, plus fresh runtime evidence. No accepted source file changed. Baseline/new-source hashes and post-execution weight verification in .runtime/studio-ui/visual-director-2d-01/completion.json. No R1/M4/production access, creative/history/binding format change, Gate A change, dependency installation, UI/media/reel integration or release.

Evidence root contains inventory.json, fairness.json, comparison.json, artifact-records, scenes.json and geometry-checks.png. Browser evidence is measure-session/browser-evidence-46776c9476b4d860.json:6 passes, bundle_accepted=false. Individual roots visual-director-2d-en-001 and visual-director-2d-te-001 retain prompts/schema/outputs/logs/metrics and unapproved concept JSON documents. Prior evidence untouched.

Offline independence remains OPEN: external cached weights are not an independently retained app bundle; matching runtime/native sources, build tools/SDK closure, original tokenizer/config/conversion provenance, applicable notices/advisory closure and clean offline build/install/recovery remain missing/unverified. Publisher digest/Apache local-use verification does not close every redistribution obligation. No cloud/paid service or new model acquisition.

Model-selection recommendation: retain14B as a better TECHNICAL candidate than8B, but NO-GO for integration as a fully qualified English/Telugu creative engine. It fails the unchanged English complete-editorial-description requirement, even though all6 documents satisfy technical/structural checks. Do not promote it merely because compilation passes or silently repair its prose.

Smallest next action, requiring separate bounded authorization: address concise, complete English rationale generation/admission under the SAME40/80-character contract (and text/vector-only intent), using this14B candidate; do not acquire more models or widen limits to manufacture a pass. Preserve these comparison results as the frozen baseline. Any changed prompt is a new experiment, not a retrospective pass of2D. No more runs in this phase. STOP after reporting; no broader integration or release authorization inferred.
