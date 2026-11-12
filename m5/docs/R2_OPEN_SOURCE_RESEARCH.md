# R2 — open-source research and build-versus-reuse

2026-11-10, planning only. Official upstream pages were inspected through browsing;
no source archives, packages, binaries, models or data were downloaded to the workspace.
Versioned review anchors below are NOT install/adoption approvals or claims of newest
patch status. Recheck exact artifacts and advisories before any future acquisition.
See [licence matrix](R2_DEPENDENCY_AND_LICENCE_MATRIX.md) for obligations and unresolved closure.

## Existing capabilities and local evidence

Read-only project evidence is ../THIRD_PARTY_INVENTORY.md, ../M5_PHASE2_HANDOFF.md,
the accepted R1 source and [acceptance record](M5_R1_ACCEPTANCE_RECORD.md). Inventory
reports Pillow 13.0.0 in a separate Python 3.12 venv; NumPy/OpenCV also appear in legacy
scope without a reconciled exact version. Sharp 0.35.5/libvips 8.18.7 and Puppeteer
25.16.0 are recorded under HyperFrames's private Node tree, Chrome 157 is external.
These are recorded local observations, not revalidated feature inventories in this task.
Do not inspect/alter M4 to resolve them. No compatible decoder is established inside R1's
Python 3.15 environment. Tesseract, eng/tel data, Color Thief and scikit-image local
availability is UNVERIFIED; absence of a project record does not prove not installed.

Chrome/Puppeteer already render synthetic posters but are not an analysis engine or an
accepted arbitrary-media boundary. Chrome's proprietary executable and broad process/
profile surface conflict with a small independent decoder. Preserve that reel/poster
engine; do not route R2 through it. Sharp's existing native operations are useful for a
comparison, subject to its private-path and LGPL native-bundle constraints.

## Candidate assessments

### Pillow 13.0.0 — conditional shortlist

Reviewed [release](https://github.com/python-pillow/Pillow/releases/tag/13.0.0),
[versioned MIT-CMU licence](https://github.com/python-pillow/Pillow/blob/13.0.0/LICENSE),
[installation](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html),
[native build requirements](https://pillow.readthedocs.io/en/stable/installation/building-from-source.html)
and [Image API](https://pillow.readthedocs.io/en/stable/reference/Image.html).
Reuse PNG decoding, orientation, resizing, quantization, histograms and native filters.
Works offline once its runtime/native closure exists; arm64 macOS distributions/build
support are documented. A wheel must match interpreter ABI; old venv modules cannot be
loaded into R1's interpreter. A separate pinned worker interpreter is a valid design.
RGBA at the maximum input pixel count is 64 MiB before scratch/copies, so memory is
not estimated from output size alone. Bound source decode and native scratch explicitly.

Maintenance: quarterly releases and fixes; [13.0.0 security notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
include mode-transition storage, MSP unbounded decode and empty-palette quantization
issues. These illustrate why format allowlists and a patched exact build matter; they
are not evidence of complete security clearance. Current [advisories](https://github.com/python-pillow/Pillow/security/advisories)
must be reassessed for the selected build and native libraries. No sample images decoded.

### OpenCV 5.0.0 — benchmark only if Pillow primitives are insufficient

Reviewed [release](https://github.com/opencv/opencv/releases/tag/5.0.0),
[versioned Apache-2.0 licence](https://github.com/opencv/opencv/blob/5.0.0/LICENSE),
[official project](https://github.com/opencv/opencv) and
[Python binary third-party notice inventory](https://github.com/opencv/opencv-python/blob/4.x/LICENSE-3RD-PARTY.txt).
Mature morphology, thresholding, connected regions and image statistics could help
composition/text-region work. It does not itself identify Telugu fonts or guarantee OCR.
Python/native arrays and possible NumPy, codecs, thread pools and optional video/UI
libraries add closure and peak-memory complexity. A selected 5.0.0 binary needs its OWN
notices; a 4.x wheel notice file is only a warning/example, not its actual SBOM.
macOS arm64 source builds are feasible, but exact wheel/ABI provenance and minimal
headless build must be verified. No GUI/video/DNN/contrib/nonfree components needed.
Maintained project; [security tracker](https://github.com/opencv/opencv/security/advisories)
is an audit input, not a no-vulnerability claim. Do not reuse ambiguous duplicate legacy
opencv installations or upgrade their environment. Reject full framework adoption for
the first bounded slice unless a frozen benchmark demonstrates a material quality benefit.

### scikit-image 0.26.0 — reject baseline dependency, retain as comparator

Reviewed [release](https://github.com/scikit-image/scikit-image/releases/tag/v0.26.0),
[versioned licence inventory](https://github.com/scikit-image/scikit-image/blob/v0.26.0/LICENSE.txt)
and [dependency/build declarations](https://github.com/scikit-image/scikit-image/blob/v0.26.0/pyproject.toml).
Useful tested region/edge/segmentation/measurement routines, with a BSD-led per-file
licence collection. Its runtime includes NumPy, SciPy, NetworkX, Pillow, imageio,
tifffile, packaging and lazy-loader; build adds Meson/Cython/Pythran/toolchain inputs.
This is more closure than the baseline requires. Array float conversions and temporary
representations can multiply memory. macOS arm64 support is distribution/build specific;
offline use works only after all requirements are retained. Disable sample-data fetching;
pooch/data extras are not permitted runtime network dependencies. Maintained project,
[security information](https://github.com/scikit-image/scikit-image/security) reviewed;
no complete native vulnerability audit established. Use if a specific benchmark proves
substantial value, not just because it offers many algorithms.

### Tesseract 5.5.4 — benchmark first, separate language-data gate

Reviewed [5.5.4 release](https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.4),
[Apache-2.0 code licence](https://github.com/tesseract-ocr/tesseract/blob/5.5.4/LICENSE),
[dependencies](https://github.com/tesseract-ocr/tesseract),
[build guide](https://tesseract-ocr.github.io/tessdoc/Compiling.html) and
[security policy](https://github.com/tesseract-ocr/tesseract/security).
Offline CPU OCR is suitable for comparison; it does not require a hosted service.
macOS builds are documented, but a specific arm64 executable/library closure is not
presently proven locally. Leptonica is required; codecs and threading depend on build.
Prefer minimal CLI/native closure and normalized PGM, no Python OCR wrapper package.
Output word/line boxes, raw text and raw scores are useful; scores are not probabilities
and stylized Telugu/English posters are not covered by general OCR claims.

Audit models independently: official [data-set comparison](https://tesseract-ocr.github.io/tessdoc/Data-Files),
[fast language inventory](https://tesseract-ocr.github.io/tessdoc/Data-Files-in-tessdata_fast.html),
[fast 4.1.0 release](https://github.com/tesseract-ocr/tessdata_fast/releases/tag/4.1.0),
[fast licence](https://github.com/tesseract-ocr/tessdata_fast/blob/main/LICENSE),
[best licence](https://github.com/tesseract-ocr/tessdata_best/blob/main/LICENSE).
Both official repositories publish Apache-2.0 terms; this is independent of the engine's
code licence. eng and tel exist; only LSTM/OEM1 is supported by fast/best. Compare pinned
fast eng/tel against pinned best only if fast misses frozen quality gates. Exact model
commit/blob hashes, packaged licences and compatibility with the selected engine must
be recorded before adoption. Do not call a moving main branch a reproducible version.
Training corpus provenance is distinct from the distributed traineddata licence; no
training data is acquired, retraining proposed or legal clearance for user content inferred.

### Color Thief Python 0.2.1 — reject additional dependency

Reviewed [official repository](https://github.com/fengsp/color-thief-py),
[0.2.1 package declaration](https://github.com/fengsp/color-thief-py/blob/master/setup.py)
and [licence text](https://github.com/fengsp/color-thief-py/blob/master/LICENSE).
This Python candidate is BSD-3-Clause by repository text, NOT the licence of another
similarly named JavaScript project. It already depends on Pillow and supplies palette
quantization rather than typography/layout intelligence. Legacy Python classifiers and
0.2.1 metadata provide weak current maintenance/Apple Silicon assurance; no new security
coverage is inferred from its small size. Pure Python iteration can dominate processing.
Its actual release artifact/licence correspondence remains unverified without acquisition.
Pillow's existing quantizer plus our explicit alpha/sampling/semantic-role rules is
simpler. Do not vendor or copy its algorithm to evade the dependency decision.

### Sharp 0.35.5 — substantial performance alternative, not baseline adoption

Reviewed [Apache-2.0 licence](https://github.com/lovell/sharp/blob/v0.35.5/LICENSE) and
[platform/runtime installation requirements](https://sharp.pixelplumbing.com/install/).
Native libvips offers low-copy/statistics/resampling potential and arm64 support; that
is a meaningful alternative if Pillow cannot meet the measured envelope. Decode caches,
native concurrency and other loaders still need enforcement. The recorded installed
bundle includes LGPL-3.0-or-later libvips components and other licences; Apache-2.0 Sharp
alone is not clearance. Source-retention/relinking obligations require separate review.
Private HyperFrames node_modules are not the product's dependency strategy. No automatic
second decoder, native addon rebuild, package acquisition or Sharp adoption authorized.

## Build-versus-reuse decision

Reuse: patched PNG/CMS decoding, resampling, quantization, OCR and image primitives.
Build small application-specific components: bounded job protocol, geometry/profile
orchestration, alpha-weighted coverage, explainable feature rules, uncertainty/review,
rights/brand constraints, immutable report/provenance and the manual R1 bridge.
Do not rebuild OCR, shaping, codecs, generic canvas interaction or a vision framework.

Defer/reject: exact font recovery, semantic subject identification, hidden-layer recovery,
editing-process reconstruction, learned aesthetic rankings, video/mixing and automatic
style application. Those claims cannot be justified by this deterministic R2 proposal.
Full R2 still includes benchmarked OCR; early color-only progress is not full R2 acceptance.

No benchmark, install or source retention was performed. Proposed dependencies are not
adopted. Security, language accuracy, source/build closure and R1 sidecar compatibility
must pass their explicit gates before any future enabling decision.
