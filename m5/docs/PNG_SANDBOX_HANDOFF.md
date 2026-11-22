# PNG-first Brand Application B — implementation handoff

2026-11-12. **GO for the restricted PNG capability-sandbox workflow in isolated M5.** This is an implementation recommendation, not production acceptance, general media-security qualification, offline distribution closure or full Brand Application B completion. SVG/TTF/OTF inputs, other raster profiles, OCR/video/reference processing, R2–R6, M4/M6 integration and release remain disabled/out of scope.

## Completed functionality and compatibility

New standalone `studio_png_sandbox` CLI/library and loopback browser UI. Existing manual Studio launch, source and restrictions are unchanged. It uses a distinct **studio-media-workflow@2** envelope and **studio-png-session@1** owner, never a legacy Studio marker or creative.json mirror. Existing readers explicitly refuse the namespace; no migration/adoption. `creative@1`/schema1, history v3, project-binding@1, Brand Library and R1 contracts remain unchanged.

A version-2 fork contains a frozen text/geometry creative base and unchanged source binding snapshot, plus explicit PNG placement records and a separate version-1 media history. The envelope—not its embedded creative document—is the complete media project. Current approvals are cleared on the fork; historical snapshots remain intact. PNG media is not disguised inside a metadata-only document. Existing core paint order is preserved; PNG overlays paint above the base in their own declared order.

Approved pinned logo/image PNGs can be placed, moved, aspect-ratio resized, removed, undone/redone in one step, saved automatically and reopened after process restart. Base text is edited in its original manual project; later base edits do not silently synchronize into this explicit fork. The separate constructor can fork an existing validated document/binding; the CLI can create a fresh text base. No unified accepted-Studio media editing, cross-format font loading or layer interleaving is claimed.

Reuses existing Brand Library approval/pin/rights evaluation and Brand Application A rules, manual schema validation, renderer, pinned Inter/Noto Telugu fonts and the unchanged `visual_poster_tests/browser_acceptance.js` font/overflow/raster qualification functions. No external font file is loaded. Exact English/Telugu/decomposed Unicode is retained. Aspect ratio, source pixels, mandatory margins and text protection are enforced; a strict palette rule also checks source pixel colors. Unrecognized hard rules, no-assets rules, conflicting requirements, unauthorized assets and stale/revoked grants refuse use.

## Qualified processing boundary and precise limits

One pinned LodePNG WebAssembly module in a dedicated Wasmtime C-API helper. Production controller has one fixed decode command; diagnostic exports/modes are used only by the controlled test harness. No user-supplied module loading through Studio. Runtime/helper/module hashes checked before launch; dynamic-loader override environment removed. One global nonblocking OS job lock admits one application PNG helper. No automatic retries/restarts. Faulted termination requires explicit new supervisor instance.

- Guest: **64 MiB hard linear-memory maximum**, one memory, one instance, one table capped at64 entries. Guest memory growth fails synchronously. Memory64/shared memory/Wasm threads/components/GC disabled.
- Stacks: linked C/Wasm linear stack512 KiB; Wasmtime512 KiB native Wasm-stack threshold (upstream notes this threshold is not byte-perfect), plus hard helper OS stack limit8 MiB. Recursive-stack trap tested.
- Scratch: no WASI, host imports, temp paths, filesystem handles or worker scratch filesystem. Entire64 MiB guest charged as scratch, plus native input/module buffers10 MiB, input<=8 MiB, bounded stdout<=16 MiB+256 bytes, final RGBA copy<=16 MiB and131072-byte pipe allowance. Conservative controlled-buffer ceiling approximately114.13 MiB, below128 MiB. Normalization runs after helper exit; bounded4MP RGBA/container buffers remain below128 MiB. This is a capability/size proof, not a disk-exhaustion experiment.
- One compute thread. Parallel compilation, concurrency support and Mach exception service thread disabled using supported Wasmtime configuration. Mach thread count is checked before and after decode. Guest cannot create processes/threads because no imports or threading support exist. Trusted runtime is part of the TCB, not kernel-restricted against compromise.
- Five-billion fuel units, helper CPU hard limit15s, native wall alarm15s and supervisor deadline<=15s. Cancellation kills the process group and reaps the child; no result publication on cancellation. Unconfirmed termination faults the supervisor. Single-thread HTTP controller applies60s complete-operation alarm. No hard real-time scheduling guarantee is claimed.
- Input<=8 MiB; dimensions1..2048 each; decoded output<=16 MiB; control header<256 bytes; stderr<=4096; source hash required. Trusted runtime overhead uses a conservative **128 MiB whole-helper RSS refusal ceiling**, and the controller separately refuses above128 MiB measured peak RSS. These overcount guest/buffer pages deliberately; they are not exact deduplicated attribution.

**Total host memory is NOT kernel-enforced.** The1 GiB overall target has substantial numerical headroom under these conservative caps/ceilings, but native-runtime allocations are checked by measurement/refusal rather than a kernel quota. Engine escape, native runtime vulnerability, compromised trusted host, malicious local user or OS/kernel failure is not contained by the no-import guest boundary. The native helper can read its pinned module/runtime and retains normal OS privileges; do not describe it as a native filesystem/network sandbox. R2's broader Gate A remains blocked; this is the separately approved PNG-only capability profile.

Host filesystem/network/process/thread import requests are rejected before module instantiation. Guest cannot call a native decoder or choose paths. No raw uploaded/source PNG is fed into the normal renderer. Qualified RGBA bytes are normalized into a fixed IHDR/IDAT/IEND RGBA PNG using standard-library zlib for DEFLATE; this is fixed pixel serialization, not a replacement general image codec. Browser sees only this derived container.

## Supported and refused formats

Enabled: static, noninterlaced, 8-bit RGB/RGBA PNG, containing IHDR, contiguous IDAT chunks and final IEND only, with valid CRCs, dimensions and compressed/decompressed size. PNG logos/images preserve alpha and aspect ratio. Reject palette/grayscale/16-bit/interlaced/APNG and ancillary metadata, unknown chunks, trailing data, corrupt/truncated/bomb inputs, SVG, fonts, JPEG/WebP and every unsupported format. Common metadata-bearing PNGs may therefore need a future qualified normalization extension; no silent fallback is used.

Draft SVG embeds only the generated PNG bytes. SVG download/export additionally requires current `redistribute/poster` clearance because the embedded image can be extracted. Grant registration or a hash is never treated as legal permission. Live rights are rechecked before processing, after decoding and under the Brand Library OS/SQLite transaction across final placement/export publication. Removing revoked placements and historical recovery remain possible; rendering/export use stays blocked. Records and old export bytes are never rewritten on revocation.

## Persistence, exports and recovery

Own immutable hashed generation records; expected-head concurrency, lifetime OS writer lock, strict ancestry and operation validation, one atomic HEAD replacement after file/directory synchronization. Media history contains only placement/geometry/remove operations and exact before/after states; unauthorized field mutations/history rewrites refuse. Undo/Redo never resurrect approvals. Stale operations/exports refuse.

128 MiB total retained session budget, including orphaned/interrupted files and exports;200 generations,100 media history transactions,64 total layers,8 MiB metadata,4 MiB SVG,8 MiB PNG,20 retained export sets. All are stricter than or within the inherited bounds. No automatic deletion. Failed saves retain old HEAD or a fully validated new state and block uncertain writers. Explicit `candidates()` and `recover_copy(...,acknowledge=True)` restore a selected generation and ancestry to a fresh physical root, preserving source records and receipt bytes; later edits and previous exports are excluded, with an explicit recovery-origin record. Old roots/HEAD/exports are not repaired or overwritten. Same logical session identity is retained in this explicit recovery copy; no shared mutable files or hardlinks.

Exports have a15-second, one-use head/scene handshake; client refreshes its preview before export. Current PNG is validated through the qualified decoder, dimensions checked, rights checked and draft SVG/PNG/hash manifest published. A manifest is the completion marker; incomplete directories count toward retention and are not silently resumed or deleted. Same-source scene/PNG export identity includes frozen base/binding/brief, placements, qualified receipts/profile and pinned font hashes. Runtime identity is separately pinned in build/dependency evidence; future runtime/profile changes require requalification and an explicit compatibility decision.

Browser reuses existing font loading, embedded-font-vs-fallback probes and measured overflow refusal. It checks exact decoded RGBA equality of preview raster and encoded PNG. **This visual QA is browser-side, not independent server rerender verification**; API actors are trusted-local, outputs draft-only and no approvals are created. Rights provenance labels remain trusted-local legal assertions, not authenticated external clearance. Native Telugu human/IME/accessibility approval is not established by this batch.

## Evidence and commands

All commands executed from `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`. No existing source was edited. Acquisition used official HTTPS curl/API/codeload URLs; exact sources, sizes, SHA256, release metadata/licenses/advisories retained under `.runtime/png-first-001/downloads`, with digest manifest `retained-artifacts.json`. Wasmtime C API and SDK archive SHA256 match official release digests. Only workspace-local extraction/build; no global installation, Rust installation or package manager. Initial sandbox DNS/bind/sysctl refusals were resolved using separately reviewed authorized network/loopback/read-only host commands; no automatic-review rejection occurred.

Successful commands (exit0 unless noted):

```
python3 -I -B tools/build_png_sandbox.py --inputs '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/retained' --output '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/build-08'
python3 -I -B tools/run_png_sandbox_tests.py --build '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/build-08' --evidence '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/security-02'
python3 -I -B tools/run_png_sandbox_tests.py --track additional --build '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/build-08' --evidence '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/lifecycle-final'
python3 -I -B tools/run_png_sandbox_tests.py --track workflow --build '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/build-08' --evidence '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/studio-ui/visual-png-workflow-tests-final'
node --check studio_png_sandbox/app.js
```

-22 original security tests +4 additional lifecycle/accounting tests +18 workflow tests = **44 distinct targeted Python tests passed**. Four post-integration current-source checks also passed (`.runtime/studio-ui/visual-png-current-source-final/results.json`), not counted as new distinct tests. No broad legacy suite was intentionally run.
- Existing hash-limits, CRC, dimensions, decompression, forbidden imports, stack/fuel/memory traps, no paths, concurrency, timed process cleanup, actual native SIGALRM and simulated unconfirmed termination tested. ENOSPC/sync/interrupted publication are bounded injections, not real disk exhaustion, OS crash or physical power loss. Physical power-loss durability remains unverified.
- Initial helper refusals exposed a required bounded indirect-call table, default Mach service thread and insufficient fuel for the largest fixture. Corrected without changing numerical time/resource limits; all old build/probe evidence retained in build-01..07. A workflow-runner import collision initially selected an existing test_workflow module and caused21 setup errors (no tests ran and no protected data written); corrected by package-qualified imports. Failed evidence retained under visual-png-workflow-tests-01. Do not present those attempts as passing runs.
- Wrapper/decoder rebuilt locally without acquisition/network into build-09-offline; Wasm and native helper byte hashes match build-08 exactly. This proves wrapper rebuild from retained binaries/source, NOT rebuilding Wasmtime/LLVM/macOS toolchains from source or clean distribution independence.
- Actual host: Apple M4 Pro,25769803776 RAM bytes (24 GiB). Largest-case recorded helper peak RSS51658752 bytes, below128 MiB; maximum decode duration in security-02 metrics0.0685s. These controlled-fixture measurements are not a worst-case latency or total-host-memory proof. Other initial builds/fixtures recorded different timings; do not compare as a benchmark.
- English and Telugu browser placement/export: exact PNG decoded-RGBA parity passed. English move/resize/Undo/Redo and full process stop/restart passed;12 session file hashes unchanged across restart. Exact Telugu/decomposed copy tests and font probes passed, not native-language human approval. Browser uses the Codex in-app browser; other browsers require their own qualification.
-8 HTTP checks passed (loopback, Host, Origin, CSRF, malformed JSON/actions, path traversal), plus actual one-use/15.2-second expired-handshake refusals with no export writes. Final current-source embedded-font/bounds and PNG export passed after handshake/QA integration. Evidence: `.runtime/studio-ui/visual-png-browser-01/` (sessions.json, screenshots, final-font-qualified.txt, http-checks.json, handshake-final.json, English restart result and final-export-artifacts.json). All qualification servers stopped.

## Dependencies, licences and offline status

See `docs/PNG_SANDBOX_DEPENDENCIES.json` for exact hashes/paths/obligations and upstream links. Wasmtime50.0.1: Apache-2.0 WITH LLVM-exception; LodePNG20261102/commit7b2893e35891c0c85bee5595caafaf3c2044b409: Zlib. WASI SDK34/LLVM: Apache-2.0 with LLVM exceptions; wasi-libc includes MIT/musl and incorporated permissive notices retained with exact libc source. Do not strip notices or misrepresent upstream origin; no upstream source was altered. Runtime uses macOS system libSystem/libiconv; build compiler additionally uses SDK LLVM dylibs and macOS libc++/CLT. macOS/Apple SDK are platform dependencies, not newly redistributed FOSS components.

Official Wasmtime release/security metadata (86 advisories) retained and selected current stable50.0.1 fixes reviewed; disabled features reduce exposure but are not substitutes for patched code. LodePNG repository advisories returned0; a separate official CVE record, **CVE-2026-112020**, identifies utility getFilterTypesInterlaced in lodepng_util.cpp. That utility is not compiled/linked and interlaced input refuses. Do not describe zero repository advisories as absence of vulnerabilities. No claim of exhaustive vulnerability freedom or independent binary attestation.

Acquired compressed archives/metadata total224449682 bytes (~214 MiB); retained extraction approximately791 MiB plus220 MiB downloads. This is development retention, not qualified deployment size. Full Rust/Cargo transitive sources/toolchain, full LLVM/bootstrap/build dependencies, clean Wasmtime/SDK source rebuild, complete transitive redistribution notices and final256 MiB compressed deployment qualification remain open. No distribution/release is authorized. No mandatory subscription/network service is needed for the tested offline runtime or wrapper rebuild.

## Exact new files

```
studio_png_sandbox/__init__.py
studio_png_sandbox/__main__.py
studio_png_sandbox/controller.py
studio_png_sandbox/decoder.c
studio_png_sandbox/helper.c
studio_png_sandbox/workflow.py
studio_png_sandbox/server.py
studio_png_sandbox/index.html
studio_png_sandbox/app.js
studio_png_sandbox/style.css
png_sandbox_tests/test_security.py
png_sandbox_tests/test_workflow.py
tools/build_png_sandbox.py
tools/run_png_sandbox_tests.py
docs/PNG_SANDBOX_DEPENDENCIES.json
docs/PNG_SANDBOX_HANDOFF.md
```

Fresh generated evidence/dependencies under `.runtime/png-first-001`, `.runtime/studio-ui/visual-png-*` (test-created owned manual/library/png-workflow subdirectories), and the singleton `.runtime/png-sandbox-control/job.lock`. Existing evidence never removed/overwritten. No global caches/configuration/tool installation. Frozen checkpoint, M4, M6, production and R1 not accessed; their hashes were NOT re-audited. Existing scoped baseline258 files unchanged; final per-file hashes and exact new files in `.runtime/png-first-001/completion.json`. Hash helper excludes protected R1 paths/runtime/node_modules/git, so this is not an exhaustive protected-workspace hash proof.

## Startup, recovery and stopping boundary

Run from the project directory (running `-m` from home will not find this uninstalled module):

```
cd '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio'
python3 -B -m studio_png_sandbox --root '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/studio-ui/png-workflow-NEW-UNUSED-NAME' --library '/ABSOLUTE/OWNED/APPROVED/BRAND-LIBRARY' --build '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/.runtime/png-first-001/build-08' --create --brand APPROVED_BRAND_SHA256 --text 'Exact headline' --language en --acknowledge-version-2 --port 8776
```

Library must be an existing explicitly selected owned library inside `.runtime/studio-ui`, with current approved brand/rights and supported palette/fonts. Do not use synthetic acceptance libraries as legal permission for real assets. CLI fresh creation retains its own new png-source-* manual base. To resume, run the same command with root/library/build/port, omitting creation/brand/text/acknowledgement options. Loopback URL `http://127.0.0.1:8776`. Never adopt legacy/manual or acceptance-evidence roots automatically. CLI/library recovery is explicit; a polished recovery dashboard and unified editor integration are not included. Keep retained input/build/evidence roots; relocating/upgrading dependencies requires explicit hash/profile and loader-path requalification.

Rollback: stop the independent CLI/UI and return to the unchanged accepted Studio; do not delete history/evidence or downgrade media envelopes. Ordinary Studio never imports this package. No release/startup swap or broader integration performed.

**STOP. Restricted PNG-first implementation completed. GO only for this isolated capability profile and draft overlay workflow; full Brand Application B, other formats, native runtime OS sandboxing, source-rebuild/distribution closure and production acceptance are not established.**
