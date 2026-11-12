# Visual text layout and keyboard completion batch

Implemented within the existing content/history/renderer contracts. No new dependencies, source schema, style fields or renderer profile.

## Capabilities

- Explicit measured wrapping to the selected text-box width using already loaded pinned font families/weights, browser text measurement and native Intl.Segmenter grapheme boundaries. Preserves all original code points, spaces and existing newlines; inserts only newlines. Refuses over 20,000 code points, over 64 resulting lines, unsupported segmentation or an over-wide grapheme. Does not normalize or automatically rewrite text after resizing. The user reviews the draft and applies it through the existing edit_text transaction. Cancel text draft restores exact applied text without a transaction.
- Fit box to applied text computes measured width and fixed-profile line-height/baseline height, includes descent allowance and submits one history-v3 geometry transaction. Refuses pending text and boxes outside the canvas. Existing glyph/overflow checks remain authoritative; measurement is a convenience, not a substitute for export qualification.
- F2 focuses selected text; Escape returns to the primary layer. Layer arrows/Home/End retain navigation; Shift with these keys toggles keyboard multi-selection. Alt+arrows moves the selected layer or selected group, Shift uses ten pixels. Ctrl+Alt+arrows resizes one layer with existing aspect policy, Shift uses ten pixels. Editable fields and composition own their input; geometry shortcuts do not intercept normal typing. Numeric geometry fields remain the keyboard path instead of tabbing through pointer-only resize handles.
- Basic accessibility: text control descriptions, named layout section, live layout feedback, existing pressed-state layer semantics, predictable focus return and keyboard alternatives. No full screen-reader conformance claim.
- Composition start disables action buttons, composition/isComposing/keyCode229 guards suppress shortcuts, composition end preserves draft and caret. Native Telugu OS input-source/candidate-window behavior remains unverified.

## Contract limitations

The protected style vocabulary has no text-anchor/alignment, wrapping or line-spacing fields. The renderer remains left-aligned, explicit-newline-only, line_height 1.65 and baseline 1.02 under visual-poster-draft@1. Per-line centre/right alignment, adjustable line spacing and automatic reflow after resizing are NOT implemented: adding persisted semantics or changing rendering of historical projects would require a separately reviewed contract/profile extension. Existing whole-box canvas alignment and history-v3 sizing remain available. This batch therefore does not claim every requested typography capability is complete. No spaces are inserted as an alignment workaround; no blank-line spacing substitute or hidden sidecar is introduced.

Wrapping is a programmatic draft edit, not guaranteed to create a browser-native undo entry. Cancel draft restores applied text; after Apply, project Undo restores the complete preceding text. Browser-native typing undo remains under browser/IME control. Fitting and wrap measurement may differ by browser; applied explicit line breaks and geometry persist exactly, and renderer overflow refusal remains active.

## Exact source changes

Modified (4): visual_poster_studio/app.js, visual_poster_studio/index.html, visual_poster_studio/server.py, tools/run_visual_resume_tests.py.
Created (5): visual_poster_studio/text_layout.mjs, visual_poster_tests/test_text_layout.mjs, visual_poster_tests/test_text_completion.py, visual_poster_tests/text_completion_browser.mjs, docs/VISUAL_TEXT_COMPLETION_HANDOFF.md.

creative_core, accepted studio_manual_ui, scene mapper, font assets, geometry transaction implementation, recovery and export code remain unchanged. R1 was not read or modified. M4/production were not accessed. Gate A unchanged and Media Analysis OFF. All evidence stays in fresh .runtime/studio-ui roots.

## Commands and evidence

- python3 -I -B tools/run_visual_resume_tests.py --track text --run-id visual-text-targeted-001: exit 0, 5 tests.
- Final run with ID visual-text-targeted-002: exit 0, 5 tests; no source drift or rejected writes. Validates explicit Unicode/newline save/reopen, exact undo/redo, unchanged schema and renderer profile, accessible control references.
- node visual_poster_tests/test_text_layout.mjs: exit 0, 27 checks (graphemes/Unicode/spacing preservation, bounds, refusal, measurement, keyboard/composition policy).
- node visual_poster_tests/test_editing.mjs: existing lightweight editing checks; result recorded in final report.
- node --input-type=module --check < visual_poster_studio/app.js: exit 0.
- python3 -B -m visual_poster_studio --root '<workspace>/.runtime/studio-ui/visual-text-browser-01' --port 8775: loopback startup succeeded; stopped with SIGINT after verification.

Browser route /#text-completion-checks: final 14 checks pass: explicit wrapping, no draft transaction, cancel, exact Undo/Redo, synthetic composition command blocking and caret retention, F2/Escape focus, box fit and keyboard resize atomicity, saved text reopening and deterministic exports. Initial browser run timed out because programmatic wrapping had not notified the existing input-state handler, leaving Apply disabled. Fixed by dispatching the existing input event; failed evidence retained (browser-evidence-1d66663dbc233546.json). Final evidence: browser-evidence-892e04eea1e6e800.json. Native keyboard F2/Escape were independently exercised through browser input; focus moved to text then back to the layer. Native IME is explicitly false in evidence.

Repeated qualified exports: SVG d1d32d53ae32f958063f8d52485f56e38e65d04e6f4592f2df72fd9837713744; PNG 3f0c3314572e0683c507c1c48441f33a7d2eb919efa1737ae730073cb0ea5038. Existing decoded RGBA parity handshake remains mandatory. Screenshot: .runtime/studio-ui/visual-text-browser-01/text-keyboard-proof.png. It demonstrates layout, not native-language typography approval.

Before/after file hashes and preservation results: .runtime/studio-ui/visual-text-baseline-01/baseline.json and completion.json.

## Next product priorities

Stop optional editor refinements after this batch. Broader M5 work should prioritize consolidated manual-product acceptance, reliable local startup/distribution and offline dependency/licensing closure, then separately scoped remaining product workflows. Actual image/poster analysis, English/Telugu OCR and reel/video reference analysis remain mandatory eventual capabilities, requiring separate security qualification/authorization. No R2–R6, M4 integration or release is authorized here. Native Telugu IME/human typography review, full accessibility and fixed-profile typography limitations remain tracked follow-ups; no complete Studio or full M5 acceptance claim.
