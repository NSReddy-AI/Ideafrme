# M5 local startup, source retention and Brand/Asset readiness

Implemented local-startup improvements only; existing editor/core/runtime contracts are unchanged. No release, installation or real-media backend activation.

## Completed functionality and decisions

New Start Studio.command resolves its own directory and invokes tools/studio_local.py with isolated Python (-I -B), so Terminal/Finder launch does not rely on the caller's working directory or installed project module. Default starts the existing Visual service on loopback port 8766. `start --port 0`, explicit `start --resume --root`, read-only `check`, ownership-only `sessions`, and bounded `kit --name` commands are available. Existing service handles writer locks, ownership, quotas, CSRF/Host/Origin, recovery, history and fonts. No alternative server or project format was introduced. No automatic browser launch, session selection, repair, dependency acquisition or agent restart.

Open-source-first decision: reuse installed Python standard-library argparse, pathlib, json, hashlib, zipfile/zlib and the accepted local HTTP service instead of adding Electron, a bundler, FastAPI, an installer or another package manager. Browser remains replaceable/user supplied and must pass existing font/PNG checks. These are local utilities around owned workflows, not rebuilt shaping/codec/canvas infrastructure. Existing fonts are unchanged, pinned and already locally retained. Font notices verified against actual retained files; official licensing references are in LOCAL_STUDIO_START.md. No source/code/model library was acquired, no shared runtime changed, and no M4 engine was inventoried or accessed.

Read-only dependency check records local Python 3.15.2, Darwin arm64, zero mandatory third-party Python packages, exact font hashes/notice hashes and required browser-route availability. Python 3.10+ is a feature floor only; no broad version/OS support claim. It reports all clean-install, runtime-rebuild, network-isolation and distribution gates as unverified. Missing files/fonts or changed font hashes refuse readiness. Node/FFmpeg/HyperFrames/Pillow/OCR/models are unnecessary for this manual slice, not unnecessary for the eventual product.

Internal kit uses fixed source categories, bounded file count/size, deterministic ZIP timestamps/order, exact SHA-256 manifest, source identity recheck and archive readback. New kit directory required; no overwriting/eviction. Symlinks, multi-hardlinked sources and out-of-runtime destinations are refused. It contains manual first-party source and required existing browser assets plus the two retained font binaries/notices. It excludes projects, sessions, exports, R1, M4, production and media backends. It does not bundle Python or a browser or claim redistribution approval. First-party distribution terms are unresolved, so this is internal retention only, not a public SDK/release. Zip readback and file fsync are not a physical power-loss durability claim.

## Brand & Asset Studio preparation

Read Universal specification §6 (identity/tokens/asset dimensions/rules/rights/history), proposed contracts around lines 282–291, and broader G1 around lines 356–367. The approved manual-R1 subset is not approval for this broader Brand/Asset data model. Versioned brand profiles, hard/soft rules, structured rights decisions, ownership/immutable persistence and approval/invalidation need explicit contracts before implementation. The specification marks those contracts proposed; current creative@1 accepts only a small brand reference, not a complete Brand Kit.

Reusable components: core asset records and confined relative paths/hash validation; existing UUID/canonical/hash utilities; versioned transaction and immutable snapshot patterns; Visual-owned session lock/journal/quota facilities; pinned font hash/coverage and deterministic scene mapping. These may be reused only behind an approved service boundary. Accepted manual_subset explicitly rejects nonempty assets and non-null brand values, including historical states; do not bypass it or mutate approved R1 behavior to make imports work.

Local libraries: Python standard library supplies metadata validation, hashing, safe paths, JSON and locking; no new dependency is needed for future manual metadata authoring. No image parser/thumbnailer, Pillow, SVG-file import, OCR, video or model backend is adopted. Actual assets would remain untrusted; a metadata-only catalogue is not permission to decode them. No new brand profile/store/sidecar, operational bridge, approval authority or asset import implementation was created in this batch. This is a scoped blocker, not a new review of already accepted editor work.

## Exact files

Created six files; zero existing source files modified:
- Start Studio.command (executable)
- tools/studio_local.py
- studio_ui_tests/test_local_tools.py
- tools/run_local_tools_tests.py
- docs/LOCAL_STUDIO_START.md
- docs/M5_LOCAL_PRODUCT_HANDOFF.md

All kit, test, relocation and startup data is under fresh .runtime/studio-ui roots. No Git/config/environment/model changes. Protected core, renderer, accepted manual UI, history/recovery and fonts remain byte-identical to this batch baseline. R1 not read/modified; M4/production not accessed; Media Analysis OFF and Gate A unchanged.

## Targeted verification and commands

From AI Studio:
- `python3 -I -B tools/run_local_tools_tests.py --run-id visual-local-targeted-001`: exit 0, 7 tests. No rejected writes/processes/network.
- Same command with visual-local-targeted-002 after adding fixed-route file checks: exit 0, 7 tests, no failures/errors or source drift. Covers dependency inventory, protected/runtime exclusions, changed-font refusal, invalid output names/locations, deterministic kits, archive manifest/license readback, duplicate-output refusal, symlink source/output refusal.
- Absolute `Start Studio.command check` from /private/tmp: exit 0; correct workspace/runtime/fonts reported without module installation.
- Absolute `Start Studio.command start --port 8776 --root '<workspace>/.runtime/studio-ui/visual-local-launch-01'` from /private/tmp: correct loopback service started; stopped with Ctrl+C, exit 0.
- Five startup assertions: GET /, /app.js, /text_layout.mjs, /api/session all 200; session reports enabled=false and real_media_enabled=false. An initial test used nonexistent /api/analysis and failed on its expected-200 assertion; actual session endpoint was then used. Unknown route correctly returned 404. route-attempt.json and successful launch-evidence.json are retained. No sample project created and no editor test suite repeated.
- Safely extracted known generated kit to visual-local-targeted-002/relocated; independently verified all 51 source/asset manifest hashes, then ran its absolute tools/studio_local.py check from /private/tmp: exit 0, detects relocated workspace and retained fonts. No installed runtime provisioned, full UI project workflow run or clean offline rebuild performed. Copied UI resume hint retains original development path; use the new launcher's explicit resume command for relocated kits. Finder double-click/Terminal permission UI and relocated-browser workflow remain unverified.

Deterministic kit pair: identical SHA-256 a1dd9f9d7c13d5cacd5ee9a2203ed0fbf523a049bebefa256db6c26f52afe8a9. ZIP 464,461 bytes; retained input 1,158,551 bytes; 51 input files plus one manifest. Receipt: .runtime/studio-ui/visual-local-targeted-002/kits/one/receipt.json. Includes full retained OFL notices. Same-disk kits do not constitute independent backup media.

## Offline/distribution status

Local source retention/readback and dependency-free manual startup improved. Python runtime source and matching native-library/build closure, browser provisioning/source/toolchains, font build sources, first-party distribution terms, complete redistribution notices, clean offline installation/rebuild, network-denied first-run testing, independent-medium backup and package signing/notarization decisions remain open. No browser binary/OS SDK/Python distribution is copied. PSF and OFL commercial-use terms do not waive redistribution obligations. A browser/OS may contact the network independently; this batch's localhost checks are not OS-level network isolation proof. Full eventual product includes separately gated reel/media dependencies; manual-kit size is not the full application deployment size.

## Next unblocked batch

Product-level Home/Projects startup and session/recovery navigation can reuse the existing launcher/read-only ownership listing and accepted project APIs, with explicit resume/lock semantics. This is preferable to optional canvas polishing. Broader Brand & Asset authoring requires approval of its minimal contract and authority rules; actual asset decoding stays separately gated. Clean offline distribution closure requires a separately scoped exact runtime/source acquisition and provisioning decision; no automatic install is recommended. No R2–R6, M4 integration or release is authorized.
