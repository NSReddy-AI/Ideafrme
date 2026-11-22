# M5 functional sprint — implementation handoff

**M5 IN PROGRESS.** The connected supported poster journey passed this sprint's focused smoke. This is not full M5 acceptance, production readiness or a release. Exact feature states and preserved unmet requirements: `docs/M5_FUNCTIONAL_STATUS.json`.

## Completed connected functionality

Home/Create now offers Quick Create, Guided Create and Professional Studio over the same existing brief, binding and editor. Optional approved brand selection, exact English/Telugu headline, purpose, audience and instructions feed the existing real local Hybrid AI workflow. Missing purpose/audience resolve to generic, disclosed application defaults recorded in existing instructions; no schema field, factual claim or translation is invented. Mode preference is local; switching retains unapplied text and does not fork/migrate a document. Errors appear on Create; unavailable AI does not silently switch to deterministic generation.

Existing local Qwen3-14B interprets editorial intent; existing deterministic compiler guarantees three supported structurally distinct compositions with application-generated rationales. Review/selection opens a separate saved draft. Refinement is manual editing, not conversational AI editing. Existing brand rights, pinned colors/fonts/rules and approval invalidation remain independent of model output.

Committed canonical manual edits now autosave through the existing paired save/recovery API, including Undo/Redo. Raw typing and IME composition are not saved as transactions. Unsubmitted brand/brief fields are not silently committed. PNG workspaces retain existing immutable-generation autosave. New read-only committed history view shows base/media operations and recovery instructions.

Qualified PNG placement remains an explicit media-v3 copy in the same editor. New canvas hit selection, direct movement, aspect-protected corner resizing, arrow nudges, Ctrl+Alt resize and Escape cancellation use the existing geometry operation and captured head. One pointer gesture publishes one reversible transaction. Core/text layer controls and the combined history/export pipeline are reused. Pointer interaction focuses the image for keyboard follow-up; composing/input fields retain their native keys. PNG stacking/interleaving is visibly disabled: current v3 does not authorize a reorder delta, and identities are never recreated to fake it.

Startup checks/source-kit capture now include the already-integrated PNG source dependency. This does not bundle/rebuild the runtime, model, compiler or browser and does not establish offline distribution independence.

## Integration failure and correction

The first real AI-to-PNG run correctly refused PNG publication at the unchanged controller128 MiB measured peak-RSS ceiling. Runtime identity verification allocated the whole23,518,480-byte Wasmtime library in the long-lived Studio. `controller.py` now hashes fixed files in64 KiB chunks, checking the identical SHA256 values. No decoder, Wasm module/helper/runtime artifact, profile, numeric limit, rights validator or persisted contract was changed. A targeted reader test rejects unbounded hash reads. Four relevant decoder checks passed, including exact RGBA, maximum2048×2048 input, bad input/hash refusal and pre-cancel refusal.

The affected real AI-to-PNG path was repeated once after the fix and passed. The first refusal remains part of this report; no security limit was raised. Total host memory remains measured/refused rather than kernel-enforced, exactly as the separately approved PNG profile discloses. R2 Gate A stays unchanged.

## Verification and evidence

Fresh evidence: `.runtime/m5-functional-sprint-01/`; fresh UI checks under `.runtime/studio-ui/m5-sprint-final-checks-01/`; first-party synthetic cleared PNG library under `.runtime/studio-ui/m5-sprint-fixture-01/`; full smoke session `.runtime/studio-ui/visual-m5-sprint-smoke-01/`. No prior evidence overwritten. Synthetic rights are only for fixture bytes, not permission for real brand assets.

-11 final focused product/hash checks passed: exact mixed/decomposed Unicode, disclosed defaults, saved creation, read-only history, Guided/Professional contract compatibility, malformed-field/mode refusal, process restart document/history/text and bounded artifact hashing.
-4 relevant decoder tests passed, maximum helper peak RSS51,822,592 bytes in this run; no worst-case memory or power-loss proof is claimed.
-6 JavaScript hit selection, immutable input order, aspect resize, bounds and invalid-corner checks passed.
-4 focused HTTP checks passed for product status, Host/Origin/CSRF rejection. No rejected request published a project.
-5 JavaScript modules and3 changed Python modules passed syntax parsing; final module syntax is rechecked in completion evidence.
-One affected end-to-end workflow, with the technical correction above: Home → Quick Create → pinned first-party brand → actual local AI → three comparison previews → reviewed selection → Professional editor → explicit media v3 copy → PNG place → drag (800,1100→840,1060) → proportional80→120 resize → Undo80/Redo120 → exact mixed text edit/Undo/Redo → SVG+PNG export → full service stop → restart/explicit reopen. Mode changes preserved an unapplied draft, subsequently cancelled without source mutation. Read-only history reported the five committed place/geometry/geometry/restyle/edit_text operations.
-Actual model runs103.9s and96.7s, CPU-only existing configuration, no model/package download. Retained `hybrid-jobs/*/{request,prompt,command,stdout,stderr,compilation,status,termination}.json/txt` carry provenance. AI is still slow; this narrow mixed-language run does not establish general Telugu comprehension or creative-quality approval.
-Reopened complete media state identical;19 retained files unchanged. SVG preview before/after restart: `6adcdc1304752d600650dba4ea6cfd9e6bd6171d585d9c356649300973a4f8ff`. PNG SHA256: `c3432468a11d8a4624d0216d0f8d85a26b53dc4443c6b8b8e4c2f8015576b62c`. SVG1,174,228 bytes; PNG48,554 bytes. SVG text nodes concatenate to exact edited Unicode; script runs are separate tspans, so raw substring matching is inappropriate. Browser decoded-RGBA parity/font/overflow checks had to pass before publication; this is not independent server rerender QA.
-The test server's original port was temporarily unavailable on restart; it resumed the same root on8779. No port eviction, foreign process kill or session repair. Temporary tabs disappeared during the tool session; explicit Projects reopen recovered saved state. UI automation locator timeouts were not counted as passing checks.
-`studio-final.png`, `restart-export-verification.json`, `http-checks.json`, `hash-fix-checks/results.json`, `completion.json` record results and exact source hashes. Native Telugu IME/human shaping judgment and full accessibility remain open.

Useful exact commands (workspace cwd):

```sh
python3 -I -B tools/run_m5_sprint_checks.py --evidence '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/studio-ui/m5-sprint-final-checks-01'
python3 -I -B tools/studio_local.py check
node --check visual_poster_studio/product.mjs
node --check visual_poster_studio/media_gestures.mjs
```

The runner requires a fresh unused runtime root; use a new suffix to reproduce. The4 decoder and6 JS/4 HTTP focused checks used bounded inline Python/Node commands, summarized in completion evidence. No legacy broad suite, package manager or unrestricted probe was run. Initial test-fixture placement outside the library's required runtime subtree was refused before library creation, then corrected. First restart on8778 failed with address-in-use;8779 succeeded. These attempts are not reported as passes.

## Exact source changes

Modified: `visual_poster_studio/app.js`, `home.mjs`, `index.html`, `server.py`, `styles.css`, `media.mjs`; `studio_png_sandbox/controller.py` (streaming identity hash only); `tools/studio_local.py`.

Created: `visual_poster_studio/product.py`, `product.mjs`, `media_gestures.mjs`; `tools/run_m5_sprint_checks.py`; `docs/M5_FUNCTIONAL_STATUS.json`; this handoff. Before/after hashes and unchanged baseline count are in completion evidence. Generated projects, first-party fixtures, checkpoints, exports and test logs stay in fresh runtime roots. The singleton existing PNG job-lock file is reused for admission, not prior evidence.

No creative_core, accepted manual UI, history contracts, binding contract, Brand Library schema, R1 or frozen-checkpoint source changed. No M4/M6/production access or writes, dependencies, installs, downloads or release. Scoped source baseline verification excludes protected R1/runtime/git/node_modules; it is not an independent hash audit of external protected workspaces or frozen238-file checkpoint.

## Startup and rollback

```sh
cd '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio'
python3 -B -m visual_poster_studio --port 8766
```

Open `http://127.0.0.1:8766`. This creates a fresh owned session; create/approve real brand metadata and rights in Brand Studio before applying assets. Do not use acceptance fixture libraries as real permissions. AI/PNG depend on the existing pinned local artifacts; no automatic acquisition/fallback. `Start Studio.command` remains an alternative launcher. To resume a normal owned session, stop its writer and use:

```sh
python3 -B -m visual_poster_studio --resume --root '/ABSOLUTE/EXISTING/OWNED/VISUAL/SESSION' --port 8766
```

The smoke session used an explicitly injected first-party library and is evidence, not a recommended production session. No smoke service remains running after completion. Rollback means stopping the isolated service and returning to preserved accepted sessions; never downgrade media v3, rewrite historical records or delete evidence.

## Remaining product requirements

See the full feature status JSON. Immediate contract boundary: PNG reordering needs a separately versioned complete-permutation transaction, ancestry/undo validation and explicit old-reader rejection. Conversational atomic edits/provenance, protected shared-content unlinking, persisted advanced inspector features and broader render profiles are not present merely because imperative editing works. Native Telugu IME/human review, broad accessibility/creative quality and physical power-loss testing remain unverified.

Reference Style Studio/R2–R6 and real OCR/video analysis remain separately gated. AI image generation lacks an adopted qualified model/runtime/weights/rights stack. Poster/reel/cinematic workflows need accepted cross-milestone adapters and authorization; no M4/M6 access is allowed here. Extra formats/fonts remain disabled. Clean offline build/distribution/licensing closure is open. These requirements are preserved, not removed or reclassified as complete.

**STOP: connected supported poster workflow implemented and smoke-verified; M5 IN PROGRESS. No production release or further gated feature enabled.**
