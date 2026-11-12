# AI Reel Studio — project-wide third-party inventory and audit backlog

R1 update, 2026-11-10: manual authoring reuses installed Python 3.15.2 standard library;
cross-language tests additionally reuse installed Node 26.13.0 (Homebrew 26.13.0_2).
Zero new packages, model weights, fonts, services or runtime bundles. Full decision,
official license references, redistribution obligations, native-closure/security gaps
and source-retention limitations: [R1 dependency decisions](docs/R1_DEPENDENCY_DECISIONS.md).
Exact local executable/notice identities: [.runtime/r1/runtime-identity.json](.runtime/r1/runtime-identity.json).
PSF license stack and Node MIT/bundled notices require a release audit before shipping
runtimes. The local offline test pass is not G7 independent rebuild/distribution proof.

Policy: PROJECT_ENGINEERING_POLICY.md. Recorded: 2026-11-10.
This is a seed inventory, NOT a completed SBOM or redistribution approval.
No third-party files were copied, downloaded, installed, vendored or modified to create it.

Phase 2 update: subsequent user authorization permits temporary installed Chrome,
Puppeteer and Sharp reuse and the TWO font copies listed in
docs/FONT_SOURCE_MANIFEST.json. These now exist in examples/posters/assets/fonts with
OFL notices. Embedded font metadata identifies Noto 2.005 and Inter 4.000/git-a52131595.
No packages/models/source repositories were acquired, and no independent rebuild is
verified. Phase 2 toolchain reuse remains temporary; internal HyperFrames package paths
must not become the permanent product dependency mechanism. See M5_PHASE2_HANDOFF.md.

## Evidence and status conventions

M5 Phase 1 uses Python's standard library only; no third-party packages are bundled.
Existing inventory evidence was previously read from:
- Reel Studio_dev/docs/DEPENDENCY_INVENTORY.md
- Reel Studio_dev/docs/LICENSE_COMPLIANCE.md
- Reel Studio_dev/docs/SBOM.json (available; not newly regenerated/validated here)
- Local runtime/package metadata inspected during Phase 2 research.

Those legacy registers remain untouched and must be reconciled by component/version
before release. Historical inventory reports do not prove current byte identity.
"Observed" below means prior read-only metadata/file evidence; "reported" means the
legacy documentation. No runtime or offline-build checks were executed for this policy.
All missing commits/checksums/source snapshots are explicitly unresolved, not waived.

## Required complete record for every adopted component

- Name, purpose, owning milestone and essential/optional status.
- Official repository/source URL and release/artifact provenance.
- Exact version, source commit, artifact SHA-256 and transitive lockfile identity.
- Code license and separate weight/font/data/native licenses where applicable.
- Intended commercial-use assessment and unresolved conditions.
- Redistribution obligations: notices, attribution, source, modifications, relinking,
  installation information and patent/asset considerations as applicable.
- Direct/transitive dependencies and feature/build configuration.
- Local source, binary, weight/tokenizer/font and notice locations; archive hashes.
- Offline installation/build inputs and verified availability (yes/no/partial).
- Runtime/OS/architecture, memory/storage and optional network requirements.
- Security advisories, affected-version assessment, maintenance and review date.
- Upstream-loss maintenance owner, replacement and recovery strategy.

## Existing components requiring audit

### Python and Python packages (M2/M3/M4 and M5 core)

Source: https://github.com/python/cpython ; PSF-2.0 plus bundled notices.
M5's recorded test interpreter: 3.15.2; legacy environment reported Python 3.12.16.
Locations: Homebrew runtime; ~/.venvs/reelstudio; ~/.venvs/rs_asr.
No interpreter source snapshot, toolchain archive or offline rebuild is established.
Audit interpreter distributions independently; do not copy Python 3.12 native modules
into Python 3.15. Recover from a compatible retained distribution/build recipe.

Existing package audit scope includes Pillow, NumPy, SciPy, OpenCV and OpenCV-contrib,
ONNX Runtime, MediaPipe, torch, transformers and their full resolved transitive trees.
Inspect wheel contents/native libraries, exact environment versions and package sources;
do not rely only on package metadata. Legacy OpenCV duplication is documentation debt,
not permission to uninstall either package. Optional matplotlib/sounddevice dependencies
must be classified by actual usage before future packaging.

Pillow: https://github.com/python-pillow/Pillow ; observed 13.0.0, MIT-CMU.
Location: ~/.venvs/reelstudio/lib/python3.12/site-packages/PIL.
Commercial use permitted under license terms; preserve notices and assess codecs,
FreeType, RAQM, HarfBuzz, FriBidi and color-management dependencies separately.
Security evidence reviewed in Phase 2 includes advisories patched in 13.0.0, not a full
native audit. Replacement: controlled Sharp/browser processing. Source/build archive,
exact local artifact hash and runtime feature checks remain pending.

### FFmpeg and video/audio stack

Sources: https://ffmpeg.org/ ; https://code.videolan.org/videolan/x264 ;
https://bitbucket.org/multicoreware/x265_git/ . Legacy register reports FFmpeg 9.0.2,
GPL-3.0-or-later build with GPL/version3 options and x264/x265.
Audit exact binary hash, configure flags, full linked libraries, matching source and
build scripts. Codec patent rights are separate. Preserve baseline behavior; no swap
to a different FFmpeg build without authorized regression and rollback evidence.
Local source/toolchain closure and offline rebuild are NOT established.
Replacement: a separately accepted compatible build/codec path, not a silent change.

DeepFilterNet: https://github.com/Rikorose/DeepFilterNet ; legacy report 0.5.6,
MIT OR Apache-2.0, binary under ~/.cache/rs_tools. Audit binary/weight provenance,
hashes, native libraries and matching source. Optional fallback: disable cleaning.

### Node, HyperFrames and browser stack

Node: https://github.com/nodejs/node ; observed Homebrew Node 26.13.0; MIT core with
bundled third-party notices. Audit npm, native libraries, exact build and artifact hash.
HyperFrames: https://github.com/heygen-com/hyperframes ; observed global 0.9.9,
Apache-2.0 core; newer upstream releases exist. Location:
/opt/homebrew/lib/node_modules/hyperframes. Audit complete runtime lock and behavior,
browser provisioning, caches, optional features and matching source. No shared upgrade.
Replacement strategy: retain our scene/render interface and accepted motion contract.

Puppeteer Core: https://github.com/puppeteer/puppeteer ; observed 25.16.0,
Apache-2.0, nested under HyperFrames/node_modules. Not an owned M5 dependency.
Sharp: https://github.com/lovell/sharp ; observed 0.35.5, Apache-2.0, likewise nested.
Observed native bundle @img/sharp-libvips-darwin-arm64 1.3.4 declares LGPL-3.0-or-later;
includes libvips 8.18.7, librsvg 2.63.2, Pango 1.58.2 and HarfBuzz 14.5.0, among others.
Bundle README lists additional licenses, including MPL/FTL/BSD-like terms.
Audit the entire bundle and each native feature before distribution. The reviewed Sharp
librsvg advisory is patched by the observed versions; this is not comprehensive clearance.
Do not make nested HyperFrames package paths permanent. A prototype may use them only
with explicit authorization, pinned identity and a later independent provisioning gate.

Google Chrome: https://www.google.com/chrome/terms/ ; observed 157.0.8103.39,
universal arm64/x86_64, /Applications/Google Chrome.app. Proprietary executable terms
plus third-party notices; not a permissive open-source distribution. No source/offline
rebuild for that exact executable is established. Temporary external-tool use does not
approve redistribution or permanent dependence. Future replacement: separately approved
Chromium or a compatible standalone renderer. No standalone Chromium was established.

### Models, inference and speech

Ollama: https://github.com/ollama/ollama ; MIT code, executable observed; exact version,
source commit, artifact hash and build recipe remain pending. Model source/weights are
separate records. A local service is not proof of independent offline provisioning.
Qwen3: https://huggingface.co/Qwen/Qwen3-14B and
https://huggingface.co/Qwen/Qwen3-8B ; Apache-2.0 official weights; local Ollama manifests
observed under ~/.ollama/models. Audit quantized blob provenance/hash, exact tokenizer,
configuration and runtime conversion chain. No model modifications authorized.
Replacement: approved smaller local model, then deterministic/manual planning.

Telugu STT: https://huggingface.co/vasista22/whisper-telugu-large-v2 ; legacy report
Apache-2.0 weights. English: https://github.com/ggml-org/whisper.cpp and turbo weights,
reported MIT. Audit weight/tokenizer/config hashes, speech-runtime environment,
Hugging Face cache closure and first-run downloads. No new model downloads authorized.

MediaPipe: https://github.com/google-ai-edge/mediapipe ; reported Apache-2.0 code and
Google model artifacts; inspect each face/pose model's own provenance and terms.
Matting: https://github.com/PeterL1n/RobustVideoMatting ; legacy register reports GPL-3.0
model; audit code AND weights and intended combined distribution, not process layout alone.
Upscaling: https://github.com/xinntao/Real-ESRGAN ; legacy report BSD-3-Clause x4plus
weights; independently confirm artifact terms/provenance before adoption or bundling.
Replacement for optional vision/matting/upscaling: manual crop/mask/native-resolution
workflow. Do not silently remove accepted integrations.

### Fonts, brand and other assets

Noto Telugu: https://github.com/notofonts/telugu ; OFL-1.1 upstream.
Observed local NotoSansTelugu-Black.ttf in production engine/fonts:
SHA-256 42a3167fc2d8ca089b03dcbfcdfe673ecaa176545944ea9c50377144947ae383.
Inter: https://github.com/rsms/inter ; OFL-1.1 upstream; local Inter-Bold.otf:
SHA-256 00fd6f4691ee8884a33b46bf45851b341927c37c30064f558e1befb242971c49.
Local file versions/provenance and matching copyright/license bundles remain pending.
Also inventory Anton, Six Caps and DejaVu separately; do not generalize OFL to all fonts.
Preserve notices, font licensing and reserved-name conditions. Snapshot exact bytes for
approved designs; font substitution requires visual regression and approval.

Brand logos, photographs, footage, music and sound assets require their own ownership,
commercial-use, likeness and redistribution records. A software license does not grant
those rights. No private assets were imported into M5; synthetic fixtures are first-party.

## Future candidates — not adopted or installed by M5

- Fabric.js (https://github.com/fabricjs/fabric.js), MIT: provisional editor; retain
  exact release/source/dependencies after approval; Telugu editing gate first.
- Konva (https://github.com/konvajs/konva), MIT: fallback, not an automatic second dependency.
- resvg (https://github.com/linebender/resvg), MIT OR Apache-2.0: standalone renderer
  candidate; retain binary/source, Cargo.lock/vendor closure and font dependencies.
- Chromium: open-source browser candidate; exact distribution/build/license inventory
  needed; a source checkout alone is insufficient to rebuild offline.
- Image/vision models: optional only; code/weight/tokenizer/encoder/VAE/quantization
  records required independently. No candidate is approved merely by a model-card label.
- FastAPI/frontend stack: deferred; retain resolved sources, locks and build tools if adopted.

## Priority audit queue

1. Before Phase 2 adoption: renderer dependency ownership, browser exception/replacement,
   font copy manifest/notices, child-process write/network confinement.
2. Before M4/M5 integration: identify accepted M4 baseline; reconcile runtime versions,
   asset/model hashes and compatibility evidence without changing protected workspaces.
3. Before any redistribution: complete every shipped transitive/native/weight/font
   record, license compliance bundle and source availability review.
4. Before independence claims: archive complete authorized build closure and execute
   clean offline installation/build/recovery tests. None is verified yet.

## M5 Brand & Asset metadata library — 2026-11-11

Adopted existing Python sqlite3/SQLite for the newly authorized separate metadata library. Locally observed Python 3.15.2 and SQLite 3.54.1; no package, source, model or runtime installation/acquisition. Python bindings/runtime carry PSF and incorporated-software obligations. Upstream SQLite deliverable code/documentation are public domain with commercial use permitted; upstream build/configure scripts may have separate terms. Official sources: https://docs.python.org/3/library/sqlite3.html ; https://www.sqlite.org/copyright.html ; https://www.sqlite.org/atomiccommit.html .

SQLite is an optional native Python component and now required for Brand Studio, not the independent manual editor. Main local doctor reports its availability/version separately. No exact SQLite matching-source/build-tool/native transitive archive or fresh offline runtime rebuild is retained/verified. No complete advisory audit, public-domain jurisdiction legal review or distribution closure claim. New first-party code and its contract are retained by the existing internal source-kit mechanism. No SQLAlchemy/TinyDB/package installed: existing SQLite supplies transactions and avoids a new persistence engine/dependency. Opaque asset bytes are quarantined BLOBs; no codec/OCR/model library adopted. Brand store is excluded from source kits along with all other runtime/project data. See docs/BRAND_ASSET_FOUNDATION_CONTRACT.md and docs/BRAND_ASSET_FOUNDATION_HANDOFF.md.
