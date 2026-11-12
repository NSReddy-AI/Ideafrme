# R2 — dependency/licence review and proposed decisions

Draft 1, 2026-11-10. PLANNING ONLY. Licence review is of official upstream texts, not a
complete local binary/legal/security audit. No adoption or redistribution is approved.
Research context: [R2_OPEN_SOURCE_RESEARCH.md](R2_OPEN_SOURCE_RESEARCH.md).
Preserve existing THIRD_PARTY_INVENTORY.md; any future adoption updates need authorization.

## Decision matrix

| Candidate / exact review anchor | Core licence / commercial modification and redistribution | Native/transitive scope and obligations | Local / arm64 / offline status | Proposed decision |
|---|---|---|---|---|
| Pillow 13.0.0 | MIT-CMU; commercial use/modification/distribution permitted subject to notices and no unauthorized promotional use of author names | Python PSF stack; zlib for PNG; optional lcms2 for ICC; a wheel may bundle JPEG/TIFF/WebP/OpenJPEG/shaping libraries even if unused. Inspect actual build and notices | Inventory reports separate Python3.12 venv, not R1 ABI; macOS arm64 upstream support; installed offline runtime possible, closure unproven | Conditional adopt candidate for isolated worker; artifact/security/CMS gates first |
| OpenCV 5.0.0 | Apache-2.0 core; retain licence/notices, mark modified files; patent terms apply | Exact build may include NumPy, codecs, BLAS, UI/video/OpenMP and other third-party code. Core licence does not clear them | Legacy versions unresolved; exact arm64 build and offline native closure unverified | Benchmark first only if measurable gap; reject full framework baseline |
| scikit-image 0.26.0 | BSD-3-Clause-led file inventory; BSD-2-Clause/MIT exceptions; retain matching per-file notices and no endorsement | NumPy/SciPy/NetworkX/Pillow/imageio/tifffile/packaging/lazy-loader; native SciPy/BLAS/Fortran and build chain require exact independent licence audit | Local presence unverified; arm64 build feasible but exact artifacts unqualified; larger offline closure | Reject baseline; comparator only after separate approval |
| Tesseract 5.5.4 engine | Apache-2.0; commercial reuse/modification permitted with licence/notices/change notices and patent terms | Leptonica plus its selected codecs/native compiler/threads; no assumption that Python wrappers are needed or covered | Local executable/version unverified; macOS build documented, exact arm64 closure not verified; offline after engine/data retained | Benchmark first; full R2 OCR adoption conditional per language |
| tessdata_fast 4.1.0 review tag, eng/tel | Apache-2.0 repository licence separately inspected; preserve matching model licence/notice and exact artifact provenance | Model blobs separate from engine/code. Need full commit plus hashes of eng/tel, no other data implicitly included | Local data unverified; CPU architecture-independent model format, engine compatibility must be checked | Initial OCR benchmark candidate, no download authorized |
| tessdata_best eng/tel, moving-main research only | Apache-2.0 repository licence separately inspected | No immutable artifact pin chosen; larger/slower model claims require measured confirmation; no retraining/data acquisition | Unverified locally; no offline closure | Benchmark alternative only if fast fails; cannot adopt moving main |
| Color Thief Python 0.2.1 metadata | Repository BSD-3-Clause (not MIT); source/binary notices and no contributor endorsement; release-artifact reconciliation pending | Depends on Pillow and inherits its native/codec audit; no new capabilities beyond palette extraction justify extra closure | Local presence/current arm64 validation unverified; pure Python but old package metadata; offline if retained | Reject extra package, reuse Pillow quantizer |
| Sharp 0.35.5, recorded libvips 8.18.7 bundle | Sharp Apache-2.0; native bundle NOT uniformly Apache | Recorded bundle LGPL-3.0-or-later plus other terms. Source/relinking/install-information duties may depend on exact composition/distribution; audit separately | Recorded private HyperFrames copy, darwin-arm64 bundle; offline installed use possible; no independent provisioning | Benchmark alternative; reject permanent private-path dependency |
| Chrome/Puppeteer existing Phase2 | Chrome executable proprietary terms; Puppeteer Apache-2.0 is separate | Browser distribution and third-party resource closure; broad runtime/process surface | Existing recorded renderer, no standalone browser rebuild | Reject as R2 analyzer; preserve existing engine unchanged |
| Own bounded metrics/report/bridge | First-party application implementation, proposed only | Reuse stdlib/math/native primitives; no model or borrowed algorithm source copied | R1 Python canonical helpers available; new report contracts not accepted yet | Build only differentiating small components after approval |

Exact version anchors and source links are in the research companion. Exact local
artifact hashes/transitive versions remain UNVERIFIED; they cannot be fabricated from
upstream version labels. "Reject" means no R2 adoption, not uninstall existing tools.

## Mandatory shortlist closure

Minimal Pillow PNG worker can use its zlib decoder path; Pillow does not require libpng
merely to read PNG. If ICC is supported, [LittleCMS](https://github.com/mm2/Little-CMS/blob/master/LICENSE)
is MIT; preserve its notices and pin its build. [zlib](https://github.com/madler/zlib/blob/master/LICENSE)
uses the Zlib licence: preserve source notices, identify altered source and do not
misrepresent origin. The [Pillow build documentation](https://pillow.readthedocs.io/en/stable/installation/building-from-source.html)
identifies optional dependencies; omission is a verified build property, not an import flag.
Never assume an installed wheel contains only libraries exercised by the job.

[Leptonica](https://github.com/DanBloomberg/leptonica/blob/master/leptonica-license.txt)
uses BSD-2-Clause terms; retain notices/disclaimers. Tesseract can consume the normalized
PGM representation, avoiding giving a second decoder the original PNG. Actual builds
may still link libpng/zlib, libjpeg-turbo, libtiff, WebP, OpenJPEG and threading libraries.
Their exact versions, licence files and vulnerabilities must be enumerated before use.
Disable unneeded GUI/video/delegate/remote I/O, optional quantizers and OpenMP where a
controlled build is later approved. Environment thread limits alone are not hard limits.

For rejected/benchmark-only candidates, known top-level obligations are recorded above;
their entire transitive licence audit is intentionally NOT declared complete. Runtime
dependency counts, sizes and full commercial-distribution clearance remain unavailable
without a selected artifact. This uncertainty prevents adoption, not research comparison.

## Retention manifest required before acquisition/adoption

For EACH engine, language data, library and toolchain artifact record: official URL,
immutable commit/tag resolution, file SHA-256, bytes, architecture/ABI, source/binary
relationship, build flags, all direct/transitive versions, exact licence/NOTICE files,
modification record and legal retention/distribution decision. Record security advisory
review date, fixes/reachable codecs and known unresolved risks. No blank field means pass.

Retain legally permitted source archives, model files, dependency/build sources,
patches, compiler/SDK prerequisites and deterministic build instructions in an approved
AI Studio location. Proposed worker closure ceiling: 256 MiB compressed deployment
artifacts, excluding separately declared retained build sources; measure before approval,
do not claim that ceiling is met. Job memory/storage ceilings are separate hard limits.
No package-manager resolution, first-run model fetch or automatic update at runtime.
No mandatory external accounts, subscription, paid API or licence server.

Source access does not establish reproducible builds. Before an independence claim,
perform authorized clean offline provisioning/build/recovery from retained closure under
../OFFLINE_BUILD_STRATEGY.md/G7. R1's open conditions carry forward, not silently closed.

## Adoption gate

A (user) approves exact manifest and acquisition scope; B reviews licence/asset rights;
C approves language benchmarks. No Tesseract code licence is used as a substitute for
traineddata provenance/licence review. No content/brand/likeness permission is inferred
from software/model licences. If a candidate misses licence, security, hardware or bound
requirements, reject it or propose a separately reviewed replacement; never weaken limits.
