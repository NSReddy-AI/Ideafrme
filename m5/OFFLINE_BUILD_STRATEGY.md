# AI Reel Studio — independent offline build and recovery strategy

Policy: PROJECT_ENGINEERING_POLICY.md. Status: proposed strategy, 2026-11-10.
No source acquisition, vendoring, install, toolchain change or offline build is authorized
by this document. No reproducible offline-build completion is claimed.

Phase 2 status update: the user subsequently authorized the bounded installed-tool
prototype and listed font copies. Its runtime uses an OS-denied IP network policy;
this is offline runtime evidence only. The full offline install/rebuild/recovery gates
below remain open. The later phase status supersedes the historical research-only
status recorded at the end of this strategy.

## Objective and boundaries

Essential workflows must survive loss of GitHub, upstream servers/accounts, free tiers
and network access. Distinguish:
- Offline runtime: installed components can perform the essential task disconnected.
- Offline installation: an empty environment can be provisioned from retained artifacts.
- Offline rebuild: source plus retained tools/dependencies can rebuild working artifacts.
- Reproducibility: repeated builds meet declared byte/pixel/behavior comparisons.

Passing one does not establish the others. macOS/Apple Silicon hardware, compatible OS,
SDK/toolchain availability, and any signing/notarization requirements are external
constraints to record honestly. Core local use must not require a cloud signing service.

## 1. Define the release closure before acquisition

Freeze first-party source and an accepted legacy engine baseline; identify exact
runtime/build dependencies, OS/SDK/compiler/runtime versions, build flags and outputs.
Inventory optional vs essential components. Keep M5 formats/orchestration independent
of a specific editor, browser distribution, model runtime or app's private packages.
Do not change released engines to simplify the archive without regression approval.

## 2. Obtain scoped authorization and check rights

Present a source/artifact manifest, sources, sizes, licenses, checksums and destination
before copying/downloading/installing/vendoring. Confirm code, weights, tokenizers,
fonts/assets and build inputs can legally be retained and redistributed separately.
Retention permission does not automatically imply redistribution permission.
If essential inputs cannot legally be retained or rebuilt, classify the gap and approve
a replacement before claiming independence. Never remove notices or bypass restrictions.

## 3. Retain enough to build, not just repository HEAD

Proposed archive layout (not created):
- release manifest: versions, commits, file hashes, configuration and provenance.
- source snapshots: original archives, patches and exact submodule/LFS content.
- language artifacts: Python sdists/wheels with platform/interpreter tags; Node package
  tarballs and lockfiles; Rust crates/toolchains/lockfiles if adopted.
- native sources: FFmpeg/codecs, libvips/librsvg, shaping libraries and selected features.
- build tools: authorized compiler/runtime/SDK inputs and documented host prerequisites.
- models: immutable weights, tokenizer, configs, conversion tools and checksums.
- fonts/assets: immutable bytes plus licenses, rights and provenance records.
- compliance: notices, licenses, modified-file records and applicable source obligations.
- recipes/tests: explicit offline commands, fixture manifests and acceptance results.

Lockfiles alone do not contain packages. Wheels alone do not establish source rebuilds.
A browser/model runtime may download resources on first use; retain and configure those
resources explicitly. Never let an offline build silently fall back to remote fetching.

## 4. Separate development convenience from product dependency ownership

Installed Chrome and HyperFrames-nested Puppeteer/Sharp may be temporary prototype
inputs only after authorization. Record exact resolved identities and fail on mismatch.
Do not publish a product requiring /opt/homebrew/lib/node_modules/hyperframes/node_modules.
Before product adoption, approve independently provisioned dependency artifacts and
the matching source/notice closure. Compare resvg/Chromium or another accepted renderer
if Chrome's executable terms or rebuild limits prevent the required independence.

## 5. Build without touching shared environments

All M5 work, profiles, writable caches, temporary files, logs and outputs stay in the
isolated AI Studio workspace (or a separately authorized build environment).
Production, Reel Studio_dev, existing venvs, global tools and model caches remain
read-only. No default shared cache mutations; no model pulls/unloads or automatic updates.
Use explicit tool paths and versions. An environment-variable override is not proof
that a native child process cannot write elsewhere; verify isolation before execution.

## 6. Offline acceptance experiment (future, separately authorized)

1. Prepare a clean isolated environment with declared OS/toolchain prerequisites.
2. Mount the retained archive read-only; verify every archive/input hash.
3. Deny external network and detect attempted requests (including first-run downloads).
4. Provision solely from retained inputs; record all installation/build steps and outputs.
5. Rebuild first-party and selected third-party binaries where source rebuild is claimed.
6. Exercise manual/template workflows and essential local AI with paid providers off.
7. Verify project open/save, approvals, poster exports and accepted reel regressions.
8. Repeat in a fresh environment; compare outputs using declared criteria.
9. Recover from a verified backup with the original working environment unavailable.
10. Record failures, missing inputs and replacements; never relabel gaps as completed.

Acceptance: no external account/payment/network dependency; no unauthorized writes;
all declared runtime resources present; rebuild/install succeeds; required regressions
pass. Separate bit-for-bit build reproducibility from pixel/behavior equivalence.
Record nondeterministic timestamps/signatures and any exceptions explicitly.

## 7. Backup, maintenance and upstream-loss recovery

Keep verified independent backups of source closure, immutable project assets and
release artifacts on an authorized second medium if available. Same-disk duplication
does not cover disk loss. Retain manifests/checksums and practice restore verification.
Never treat creative.json.previous or shared tool caches as independent backups.

If upstream disappears, continue the last accepted local version, assess security,
maintain an authorized internal patch set and test replacements behind owned adapters.
New upstream versions require license/security checks and golden tests; no silent updates.
Fallbacks: deterministic/manual planning without AI; approved alternative SVG backend;
accepted compatible video build; manual crop/mask instead of optional vision features.

## Current evidence and gates

M5 Phase 1: historical 37-test log exists; standard-library core requires no installed
third-party package. This proves neither a full application build nor offline recovery.
Phase 2: bounded installed-tool prototype and listed font copies subsequently authorized;
see its handoff for runtime isolation evidence. Full source closure/offline build are NOT verified.

Next approvals: scoped inventory/audit -> acquisition manifest -> isolated provisioning
and test plan -> recorded offline installation/rebuild/recovery -> distribution review.
No M4 modification, merge or production release is included in any implicit gate.
