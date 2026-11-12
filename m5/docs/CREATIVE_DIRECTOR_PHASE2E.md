# Creative Director Phase 2E — NO-GO

## Finding and bounded correction

Phase 2D's first two English rationales ended mid-thought at exactly 80 Unicode code points. The response was complete JSON, ended normally and used 208 generation runs against a 768-token budget. This supports field-length pressure plus insufficiently precise brevity instructions, rather than global output truncation. The third rationale was coherent. The exact internal model cause cannot be established from logs alone.

One instruction-only attempt requested a complete short sentence, a terminal period and headroom below the unchanged 80-character ceiling. No schema, capability, compiler, rights, font or geometry thresholds were weakened. AST/schema invariants are retained in `.runtime/studio-ui/visual-director-2e-01/invariants.json`.

## Qualification

Exactly one English execution and one Telugu regression were performed because the instruction affected shared generation behavior. Both used existing llama.cpp 0.9.0 (cd959bae99ff4bed22bef2604f45241c09bbb8c8), Qwen3-14B Q4_K_M, CPU-only, one thread, context 2048, maximum 768 generated tokens, seed 19, temperature 0 and a 240-second deadline. Full argv, requests, schemas, outputs, stderr and source identities are retained per execution.

- English: exit 0, 80.609 seconds, child maximum RSS 12,504,416,256 bytes. Returned only an end-of-text marker, no JSON. Rejected; no concepts accepted. Neither timeout nor token-budget exhaustion explains this result. Early termination's underlying cause remains unknown. No useful generation throughput or speed improvement can be inferred.
- Telugu: exit 0, 234.194 seconds, child maximum RSS 12,748,881,920 bytes. Three structurally differentiated concepts compiled with exact required text, pinned fonts and approved colors. All three rationales passed the obvious-fragment screen; lengths 63/71/67 characters. Requested word counts/headroom were guidance, not relaxed acceptance requirements. Human semantic/native-language approval remains outstanding. One rationale says “centers text”; actual geometry centers boxes with left-aligned glyphs, so explanation accuracy remains a limitation.

RSS is a child-process measurement, not aggregate host-memory qualification. Existing 169–217-second latency remains a product limitation; the successful new Telugu run is slower and close to the deadline. No Metal changes were made.

## Targeted verification and evidence

Five editorial checks and 20 existing semantic tests passed (25 total). The fragment detector is a diagnostic screen, not a proof of meaningful editorial reasoning. Three Telugu documents reopened, accepted a move and undid it without changing original elements or resurrecting approvals. All three generated SVG strings are byte-for-byte identical to the corresponding previously browser-verified Phase 2D Telugu SVGs. Browser bounds evidence was reused on that exact-byte basis; no fresh browser or PNG acceptance is claimed.

The recorded execution commands in each results.json are authoritative for the two model runs. Existing semantic regression command: `python3 -I -B tools/run_ai_semantic_tests.py --run-id visual-director-2e-semantic-tests --measurements .runtime/studio-ui/visual-director-2c-01/measure-session/browser-evidence-873568072427a6c3.json` (exit 0). Editorial tests were executed by the bounded inline unittest harness retained as test output; five passed. No further inference runs were performed after these two qualifications.

Evidence roots:
- `.runtime/studio-ui/visual-director-2e-01/`: baseline, original and attempted source, invariants, root-cause analysis, test output, rollback/regression and final completion records.
- `.runtime/studio-ui/visual-director-2e-en-001/`: failed English qualification.
- `.runtime/studio-ui/visual-director-2e-te-001/`: Telugu qualification and standalone unapproved candidate documents.
- `.runtime/studio-ui/visual-director-2e-semantic-tests/`: semantic regression evidence.

## Rollback and files

The failed instruction edit was rolled back to the exact pre-Phase-2E bytes. Active Phase 2D behavior is preserved. Original and attempted source are retained in the fresh evidence root. No existing source changes remain.

New files only:
- `tools/qualify_ai_editorial.py`
- `visual_poster_tests/test_ai_editorial.py`
- `docs/CREATIVE_DIRECTOR_PHASE2E.md`

The experimental runner freezes the attempted source hash and therefore refuses execution against the restored source. This is deliberate fail-closed source association, not an operational inference entry point. Reproduction requires the retained attempted source in a separately authorized isolated environment; it must not automatically restore or modify active source.

## Decision and next step

NO-GO for model-to-editor integration. English did not produce proposals, so passing Telugu structural checks cannot qualify the shared correction. No retries, additional models or further prompt tuning are recommended in this batch.

Recommend a separately authorized hybrid: AI supplies editorial angles, intent and key phrases; the application guarantees three distinct supported composition relationships using the existing generic geometry system, and assembles complete, traceable explanations from validated intent and actual layout facts. Clearly label application-composed explanations separately from raw AI output; retain raw responses and human editing/approval. This requires an explicitly reviewed proposal/provenance boundary, not silent repair of the frozen contract or additional industry templates. It has not been implemented here.

No UI integration, R1/M4/production access, protected contract edits, Gate A changes, model downloads, dependency installations or media processing occurred. Deterministic fallback remains an explicit separate workflow; invalid AI output is never silently accepted. Full offline distribution remains open: matching runtime/transitive source, build toolchain/SDK, tokenizer/configuration and quantization/conversion provenance, notices, retained distribution materials and clean offline rebuild evidence are not closed by these local executions.

STOP: Phase 2E completed with NO-GO; no integration or further tuning authorized by this report.
