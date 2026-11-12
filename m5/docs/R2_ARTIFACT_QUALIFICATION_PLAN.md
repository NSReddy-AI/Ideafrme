# R2 Gate C — artifact qualification and acquisition plan

2026-11-10. NO acquisition/adoption authorization. No sources, models, packages, fonts
or binaries downloaded/installed. Gate C **BLOCKED** for deployment; official-source
identity research is partially verified, not local artifact qualification.
Read [security decision](R2_SECURITY_GATE_DECISION.md), [prior comparison](R2_OPEN_SOURCE_RESEARCH.md)
and [licence matrix](R2_DEPENDENCY_AND_LICENCE_MATRIX.md). Do not alter existing inventory.

Status vocabulary: VERIFIED-OFFICIAL=primary upstream text/commit examined;
VERIFIED-LOCAL=read-only evidence in AI Studio, not an inspected external installation;
PROPOSED=choice requiring approval; UNVERIFIED=no artifact proof; BLOCKED=entry cannot pass.
A=user approves acquisition/phase, B=designated licence/rights reviewer, engineering
owner inventories/builds/verifies, C=language reviewer. No owner may self-grant A approval.

## 1. Immutable upstream anchors

| Candidate | Official source identity | Licence evidence | Local/binary/build status |
|---|---|---|---|
| Pillow13.0.0 | [293218ad059d994baf1777d882911bed6a49704a](https://github.com/python-pillow/Pillow/commit/293218ad059d994baf1777d882911bed6a49704a) | [Pinned MIT-CMU](https://github.com/python-pillow/Pillow/blob/293218ad059d994baf1777d882911bed6a49704a/LICENSE), VERIFIED-OFFICIAL | Existing inventory records a separate macOS Python3.12 installation, VERIFIED-LOCAL record only; actual artifacts/SHA/native features UNVERIFIED |
| Tesseract5.5.4 | [7e548e6eff172f38f97664afe7f7ce40db36c8d6](https://github.com/tesseract-ocr/tesseract/commit/7e548e6eff172f38f97664afe7f7ce40db36c8d6) | [Pinned Apache-2.0](https://github.com/tesseract-ocr/tesseract/blob/7e548e6eff172f38f97664afe7f7ce40db36c8d6/LICENSE), VERIFIED-OFFICIAL | No current AI Studio artifact identity; executable/lib closure and arm64 build UNVERIFIED |
| tessdata_fast4.1.0 eng.traineddata and tel.traineddata | [65727574dfcd264acbb0c3e07860e4e9e9b22185](https://github.com/tesseract-ocr/tessdata_fast/commit/65727574dfcd264acbb0c3e07860e4e9e9b22185) | [Separate pinned model Apache-2.0](https://github.com/tesseract-ocr/tessdata_fast/blob/65727574dfcd264acbb0c3e07860e4e9e9b22185/LICENSE), VERIFIED-OFFICIAL | Individual blob IDs/SHA256/bytes/model metadata and executable compatibility UNVERIFIED; no model inferred from engine licence |
| Worker CPython | [3.15.2 review tag](https://github.com/python/cpython/releases/tag/v3.15.2), full commit resolution not yet frozen | PSF licence stack; match chosen distribution's complete notices, not PSF label alone | Host3.15.2 identified in R1 evidence; new worker ABI/build unselected, BLOCKED |
| zlib / optional LittleCMS | Versions/builds UNSELECTED | [Zlib](https://github.com/madler/zlib/blob/master/LICENSE), [LittleCMS MIT](https://github.com/mm2/Little-CMS/blob/master/LICENSE); exact chosen versions need matching texts | Minimal PNG path needs zlib; ICC needs approved CMS closure. Existing wheel may contain more. UNVERIFIED |
| Leptonica | Exact version/build UNSELECTED | [BSD-2-Clause](https://github.com/DanBloomberg/leptonica/blob/master/leptonica-license.txt), match selected source | Native codec/archive/thread dependencies unresolved; BLOCKED |
| VM kernel/rootfs, if selected | Exact release/source/config UNSELECTED | [Kernel GPL-2.0-only + syscall exception](https://docs.kernel.org/process/license-rules.html); rootfs packages separately licensed | Linux arm64 guest independent of macOS native modules; no retained/provisioned closure, BLOCKED |
| Host helper/toolchain | macOS/SDK/Swift or C compiler/framework versions UNSELECTED for PoC | Apple SDK/framework/signing/distribution terms separately reviewed | Existing OS is not proof of SDK availability/entitlement validity or reproducible helper build; UNVERIFIED |

OpenCV/scikit-image/Sharp are NOT acquired or adopted: benchmark only if a documented
gap justifies their added native/licence closure. Never depend permanently on private
HyperFrames Sharp or Chrome. No new font or non-OCR model is needed by this plan.

## 2. Feature and security qualification

Minimal candidate: Pillow PNG decoder/resize/quantize and optionally CMS, no optional
libimagequant, delegate/remote/plugin/GUI path. Tesseract CLI uses normalized PGM plus
only eng/tel, OEM1, no OSD/training tools. Inspect actual linkage and enabled features,
not merely import flags. [Tesseract compilation documentation](https://tesseract-ocr.github.io/tessdoc/Compiling.html)
includes optional archive/curl/codecs: exclude unnecessary network/archive paths in a
controlled build and verify the result. Do not rebuild or upgrade any shared environment.

[Pillow13.0.0 security notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
and [Tesseract5.5.4 release](https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.4)
show active security fixes, not absence of vulnerabilities. Tesseract's release reports
17 fixed advisories. Before adoption, enumerate advisory IDs, affected/fixed versions,
reachability and native-library findings with reviewer/date/evidence. Do not rely on
a vulnerability count or an old no-network test as decoder security clearance.

## 3. Proposed acquisition manifest — all missing values block obtaining/use

Before A authorizes ANY acquisition, present one row per actual file, not this category
list: official immutable URL, owner/purpose, full commit/blob, bytes, SHA256 where
published, architecture/OS/libc/ABI, exact licence/NOTICE sources, intended redistribution,
native dependencies and proposed destination. If SHA is unavailable upstream, explain
how first acquisition will establish/independently verify identity before execution.
Never insert a guessed hash or treat Git SHA1 commit as a binary SHA256.

Proposed categories (no directory created):
- source archives for the pinned engines, CPython and exact native prerequisites;
- only eng/tel traineddata at the pinned source commit, plus matching licence/notices;
- independently provisioned host-helper and guest/runtime binaries with build manifests;
- selected immutable kernel/rootfs sources/config/package list if VM is approved;
- compiler/SDK/build dependencies and legally retainable provisioning materials;
- fixture rights/annotation manifests, contract vectors and first-party build recipes.

Destination proposal: a new approved `r2_materials/` under AI Studio, with per-artifact
sources/binaries/notices/build-info/hashes, no paths inside global tools or M4. No file
copy/vendoring is authorized by writing this manifest. Acquisition, provisioning and
execution are separate approvals; downloaded material is not run until validated.

Manifest status fields: official_identity_status, local_identity_status, licence_status,
source_binary_correspondence, advisory_status, ABI_status, build_status, retention_status,
owner, evidence_ref, unresolved_reason. Engineering records facts; B reviews licence/
rights; A accepts exact scope. Unknown/blocked rows cannot be omitted from a total.

## 4. ABI, storage and independence

Host macOS arm64 wheels/dylibs cannot satisfy Linux arm64 guest ABI. Select guest OS,
libc (glibc versus musl), CPython ABI, loader and full toolchain before picking wheels.
No Python3.12 native module copied into3.15; no macOS venv mounted in a guest. Node is
not a required worker runtime merely because it checked R1 hashes. Avoid package managers
and first-run data fetching in deployed runtime; frozen local closure only.

The earlier256MiB compressed deployment target must include ALL mandatory worker/kernel/
rootfs/model/runtime artifacts, not exclude the VM to appear small. Size is UNVERIFIED.
Retained build sources are separately budgeted. If no viable closure fits, present a
measured scope/budget revision to A; do not silently increase or waive the target. Worker
1GiB RAM and128MiB scratch limits remain unchanged regardless of archive size.

Retaining sources and notices is generally permitted under the inspected licences but
distribution duties differ. Preserve required notices/modification records; comply
with kernel/user-space copyleft source obligations where applicable. Source access is
not patent/asset/training-data provenance clearance. Runtime no-network operation can
be tested before release, but clean independent offline provisioning/rebuild/recovery
needs a separate G7 experiment and corresponding source/toolchain rights.

No mandatory subscription/hosted service/paid model or paid VM product is chosen.
Apple signing/notarization/deployment constraints require explicit commercial review;
no paid membership is silently made essential to local operation. Do not bypass OS
security if a local entitlement route cannot be proven. Rejection/fallback requires a
separate proposal. R1's open distribution and physical-durability conditions remain open.
