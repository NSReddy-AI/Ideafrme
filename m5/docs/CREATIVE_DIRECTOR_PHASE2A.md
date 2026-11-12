# Creative Director Phase 2A — local AI qualification and offline foundation

Decision: existing local inference demonstrated; creative-integration qualification NOT PASSED. No application integration or release. This record distinguishes actual model execution from adapter fixture tests and offline distribution closure.

## Chosen installed stack and shortlist

Recommended qualification baseline: llama.cpp 0.9.0, build12110, commit cd959bae99ff4bed22bef2604f45241c09bbb8c8, AppleClang21/Darwin arm64. Use the installed llama-completion binary for isolated one-shot text execution; llama-cli in this build starts an internal server and failed restricted free-port allocation. Do not require a shared Ollama daemon.

Existing selected model: Qwen3-8B, Q4_K_M, GGUFv3, 8.2B label,399 tensors. Exact weight SHA256 a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f, 5,225,374,496 bytes (4.87 GiB). Tokenizer embedded: GPT2/Qwen2 pretokenizer,151,936 vocabulary entries and151,387 merges, embedded chat template and EOS151645. Model file includes architecture qwen3 and apache-2.0 metadata. Platform labels amd64/linux in Ollama config are package metadata, not a requirement to execute this GGUF on x86/Linux; native arm64 execution actually completed.

Installed alternative: Ollama0.40.16, commit d63b702609c4300a2ca07be2bdb0adb9834725e5. MIT runtime; local qwen3:8b, qwen3:14b and gemma2 manifests observed. Ollama not launched or queried; no shared service/model-store mutation. More service lifecycle and conversion dependencies than direct completion. Its receipt also pins an internal llama.cpp resource and patches; not equivalent to the separate installed0.9.0 runtime.

Smaller candidate, NOT ACQUIRED: Qwen/Qwen3-4B-Instruct-2507, upstream revision cdbee75f17c01a7cc42f958dc650907174af0554, Apache-2.0. Non-thinking instruction model; lower theoretical weight/compute cost than8B, not measured here and not established as better for Telugu or creative quality. Exact GGUF quantization artifact would need selection/provenance/hash approval. Existing14B model is9,276,184,896 bytes of weights alone; not executed, not recommended before8B/4B qualification because of memory/latency cost. Existing gemma2 not adopted: separate model terms require a separate audit. No new runtime/model package acquired.

Official sources:
- https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE
- https://raw.githubusercontent.com/ggml-org/llama.cpp/master/docs/build.md
- https://github.com/ggml-org/llama.cpp/security
- https://raw.githubusercontent.com/ollama/ollama/main/LICENSE
- https://docs.ollama.com/capabilities/structured-outputs
- https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen3-8B-GGUF/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen3-8B/blob/main/tokenizer_config.json
- https://huggingface.co/Qwen/Qwen3-8B/blob/main/README.md
- https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/README.md
- https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507

Qwen3-8B official current reference revision b968826d9c46dd6066d109eabc6255188de91218 is NOT proven to be the conversion source of the cached Ollama quantization. Exact cached bytes are pinned; full upstream conversion/tokenizer provenance remains open. Model cards report broad multilingual instruction-following/creative capabilities; these are vendor claims, not our Telugu/creative acceptance evidence. llama.cpp documents Metal support; device discovery outside the restricted sandbox actually found MTL0 Apple M4 Pro. Qualification below is the evidence for this machine.

## Licence and redistribution status

Local llama.cpp/ggml LICENSE files and official llama.cpp MIT licence agree: commercial use/copy/modification/distribution permitted with copyright and permission notice retained. Ollama code also MIT; model terms remain separate. Local8B licence blob SHA d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12 contains Apache-2.0 and Alibaba Cloud copyright. Official base and GGUF Qwen repositories carry Apache-2.0; commercial use and redistribution subject to licence copy, applicable notices, modification notices and patent/trademark provisions. Registration/hash is not independent proof of media rights. Tokenizer/config files are covered by the official repository licence absent a contrary file notice; the local tokenizer is embedded in GGUF. Separate upstream files/conversion chain were not matched or retained: distribution closure remains OPEN, not a separately verified standalone-tokenizer provenance PASS.

Native dependencies identified from installed receipts/linkage: ggml0.29.0 MIT; OpenSSL4.1.0 Apache-2.0; libomp23.1.5 Apache-2.0 WITH LLVM exceptions. Their installed licence file hashes are recorded. Complete transitive NOTICE/source/build and advisories have NOT been closed. Apple Accelerate/Metal/OS frameworks require the user's licensed macOS; do not redistribute the Apple SDK/frameworks as permissively licensed dependencies. Runtime/stdlib Python carry their existing PSF/incorporated-software obligations. No third-party source copied, no packages installed and no model downloaded.

Upstream security page lists GGUF/tokenizer/server/RPC vulnerabilities. No RPC/backend server exposed and no untrusted downloaded GGUF used. Exact installed commit was not comprehensively matched against every advisory/transitive fix; do not claim security clearance. Proposals cannot call tools or alter files. Trusted local qualification is not a malicious-model/media sandbox qualification.

## Actual local artifact inventory and retention gaps

.runtime/studio-ui/visual-director-2a-01/inventory.json contains runtime versions, source commits from Homebrew receipts, CLI/completion binary hashes, native dependency/licence identities and every selected8B config/model/template/licence/params/nested-manifest size/digest. All selected8B declared digests were independently streamed and matched. No weight bytes copied. Existing blobs remain read-only referenced external materials, not an independent AI Studio distribution.

Present: selected5.225GB GGUF with tokenizer/template; licence blob; config/params; versioned runtimes/native libs; installed licence files; local clang; first-party adapter/tests and exact qualification prompts/schema/commands/results. CMake not found on PATH. A build-tool PATH miss does not prove no installation elsewhere.

Missing/unverified: retained exact runtime source at commit above; exact ggml/OpenSSL/OpenMP sources and build tools; CMake/toolchain/SDK closure; relevant notices; original model-weight revision/config/tokenizer files and conversion/quantization recipe; independent binary/weights bundle; verified compressed size; clean offline build/install/recovery. Existing Q4_K_M is already quantized: no claim that ZIP will reduce5.225GB to a small deployment. This optional text engine cannot be passed off as the R2 mandatory256MiB deployment or1GiB untrusted worker.

Prepared retention layout (NOT downloaded/copied): local-ai/runtime/<runtime-commit>/source+build-recipe+toolchain-manifest; local-ai/models/<model-digest>/weights.gguf+upstream-provenance+tokenizer/config+conversion-recipe; local-ai/notices/{MIT,Apache-2.0,LLVM-exception,applicable-NOTICE}; SHA256SUMS; platform/linkage manifest and offline-run/clean-build instructions. Obtain separate approval for missing source/tool/model acquisition; use only audited exact artifacts. Headless completion-only build should avoid UI/npm/TLS where the retained source supports it; do not assume current upstream options reproduce the installed Homebrew bottle. Homebrew recipe currently enables UI/npm acquisition/system ggml/OpenSSL, so receipt alone is not a network-free build recipe. Model retained at a fixed local path can run via --offline -m <exact verified blob>; no registry/daemon is required by the observed completion run. Full independent offline readiness: NOT READY.

## Executed qualification and resource measurements

All source/test/evidence writes in AI Studio; external model/runtime inventories read-only. Existing model and shared services not modified. Probe scripts, exact argv, JSON schema/prompt, stdout, stderr and resource/exit JSON retained under .runtime/studio-ui/visual-director-2a-01/. Configured one compute thread, one job,2048 context tokens,512 output tokens, temperature0, seed19, no model download/remote flags, explicit --offline. Default trusted synthetic text only; no user-sensitive inputs/media. GPU disabled on CPU runs. Recorded RSS is Darwin child maxrss, not aggregate unified/GPU/descendant accounting. No hard aggregate memory/thread/scratch isolation proven.

1. llama-cli --version: exit0, build12110/commit verified against receipt.
2. llama-cli prompt probe: exit1,0.145s, failed free-port allocation; no generation.
3. llama-completion CPU,60s deadline: SIGTERM exit-15 after60.13s; partial invalid JSON; maxRSS9,196,863,488 bytes (~8.57GiB); direct-child termination confirmed. Failure, not a working result.
4. Metal discovery: restricted sandbox did not expose Metal; native read-only device discovery found MTL0 Apple M4 Pro. Two native Metal text probes ended SIGXFSZ exit-25 with the probe's1MiB and16MiB per-file guards respectively. Peak RSS5.67/5.68GB. Exact offending writable sink is NOT established. No guard-free rerun; no assertion that Metal inference is qualified or that changing the guard would solve it. These diagnostic per-file caps are not Gate A aggregate scratch enforcement. Native probe network denial/write confinement was not independently traced; --offline and fixed local assets were used.
5. Final CPU diagnostic, explicit180s deadline: exit0;83.659s wall;9,098,854,400 bytes peak RSS (~8.47GiB);80.37s user CPU,1.82s system. Runtime reported301 generation runs at4.90tokens/s and143 prompt tokens at7.56tokens/s. Three complete JSON proposals returned. Output transport had a known literal '[end of text]' marker; only that exact marker is removed before strict JSON validation; arbitrary trailing prose still rejects. No token truncation/repair/salvage of incomplete JSON.

Result: startup/model execution and JSON decoding demonstrated. English request understanding partial; exact Telugu headline repeated under schema enum constraint, which is NOT evidence of Telugu semantic understanding. Three directions differ mainly in alignments; first/third emphasis repeated. Model suggested unsupported 'Inter Telugu' and light/regular/medium/semi-bold/thin weights. Lexical adapter screen rejects repeated emphasis; human capability/creative review FAIL. Brand-rule adherence is not established by model claims or lack of a forbidden price string. Creative integration: NO-GO.

Reproducibility: exact inputs/model/runtime/settings retained. Temperature0 uses greedy sampling; runtime log displays seed sentinel4294967295 despite argv seed19. No claim that seed19 independently controls greedy output, no same-input repetition performed, and no cross-platform/Metal bit-exact guarantee. Real retry was an explicit diagnostic action on observed failures, not an automatic product retry. No repeated quality-tuning sample loop.

Gate A remains unchanged: it applies to untrusted image/OCR/video jobs with1GiB aggregate untrusted memory,128MiB scratch,15s worker/60s job and existing process/thread restrictions. This separate trusted local text qualification consumed >1GiB and >60s; it DOES NOT qualify that media profile. It neither establishes nor adopts a production text-engine hard-limit contract. Deployment needs explicit text resource/execution policy and qualification; no limits silently revised.

## Adapter foundation (prepared, not integrated)

New visual_poster_studio/ai_adapter.py: structured brief/pin/capability input, exact model/runtime/tokenizer-container identity, bounded settings, request digest, JSON schema, duplicate-key/nonfinite/unknown-authority rejection, exactly3 bounded concept records, lexical composition/hierarchy/emphasis differentiation screen, unapproved/non-renderable output, explicit failure/retry/fallback reporting. No subprocess/network/project-store writes in adapter. Pin is caller supplied; future integration must use live existing binding eligibility immediately before execution AND before selection. A valid adapter envelope is NOT proof that a model ran or that rules are satisfied.

Prepared adapter request under prepared-request.json was NOT executed. Actual diagnostic uses its own exact recorded prompt/schema. Its completed external output was independently screened against the same bounded concept-field rules and rejected for repeated emphasis; assessment.json explicitly records the provenance distinction. No misleading request-to-source association or fabricated AI success.

No direct geometry/document application. A later bounded adapter must translate AI-selected layouts through deterministic schema/geometry/font checks and the existing new-project paired publisher, preserving source snapshots/approvals. No free-form SVG/code, arbitrary paths, URLs, assets, fonts, tool calls or approved status admitted. Deterministic fallback remains explicit and labelled via existing director.generate; no silent substitution and no automatic retries. Rejection leaves all existing projects unchanged. Actual concept selection needs independent live rights/rule/human review; semantic originality/compliance cannot be proved by lexical screening.

## Files, tests and next action

Created only4 source/docs files: visual_poster_studio/ai_adapter.py; visual_poster_tests/test_ai_adapter.py; tools/run_ai_adapter_tests.py; docs/CREATIVE_DIRECTOR_PHASE2A.md. Existing sources, creative@1, historyv3, bindings, R1, M4, production and Gate A unchanged. Qualification artifacts/probes live only in the fresh runtime evidence root; all earlier evidence preserved.

Targeted test command: python3 -I -B tools/run_ai_adapter_tests.py --run-id visual-director-2a-adapter-final.15 tests cover identity/seed, exact Unicode, input aliasing, request tampering, duplicate JSON keys, authority-field injection,3-concept count, superficial variation, bounds, explicit failure/fallback, prompt-as-data, brand declarations, exact transport-marker handling and observed repeated emphasis. No legacy/full suite or dependency manager run. Syntax parsed without bytecode. Model execution is evidenced separately from these synthetic fixtures. Baseline/completion hashes are retained in the qualification root.

Next exact step before model-powered concept integration: qualify a structured capability-constrained prompt/schema that can produce three genuinely different supported direction plans with this fixed8B model; perform English/Telugu semantic and creative review, bounded same-input repeat and explicit timeout/cancel checks under an approved text-runtime resource profile. Investigate Metal SIGXFSZ with a separately bounded writable-sink diagnostic, preserving Gate A. Do not simply remove guards. If8B remains too slow/weak, request acquisition of one exact approved4B quantization plus provenance/tokenizer/notices; currently not present. In parallel, obtain permission for exact missing source/tool retention and build closure, then actually test clean offline provisioning. These are prerequisites, not approvals inferred here. No broader integration or release. STOP after Phase2A.

Hardware suitability: target24GB unified memory is user-specified; device enumeration confirms Apple M4 Pro. Restricted sysctl memory query was denied. The8.47GiB measured child RSS is plausible for one job on that target, but total host/GPU/shared allocations and simultaneous Studio workload were not measured. No aggregate-hard-cap or guaranteed memory headroom claim.
