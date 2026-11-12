# AI Reel Studio — permanent project-wide engineering policy

Effective: 2026-11-10. Authority: the user's permanent project-wide engineering policy.
Scope: M1–M4, M5 and all future milestones; planning, generation, image/video/audio,
typography, editing, UI, models, dependencies, testing, deployment and distribution.
This is an adopted policy document, not implementation or procurement authorization.

## 1. Open source first

Before each substantial feature, research official open-source repositories and docs.
Compare functionality, performance, commercial rights, redistribution duties, transitive
dependencies, maintenance and security. Reuse proven components before building mature
infrastructure ourselves. Document a technical reason for any deliberate reinvention.
Build AI Reel Studio's differentiating behavior around suitable components; do not make
the product a dependent copy of another application.

## 2. Self-sufficiency and offline operation

Essential workflows must survive loss of internet, GitHub, upstream maintainers, hosted
free tiers and favorable third-party pricing. Where legally permitted, retain exact
source versions/commits, hashes, license/notice files, dependency sources, build tools,
fonts/assets, model weights/tokenizers and recovery instructions. A repository copy
alone is not a reproducible build. Verify the complete dependency/build closure.
Project creation/editing, storage, assets, approvals, poster/reel generation, exports
and locally supported AI must operate locally. Disclose hardware and model limits.
No unexpected network access; optional network services must be explicit opt-ins.

## 3. Licensing and commercial suitability

Check actual code, model-weight, font, dataset (where applicable), native-library and
transitive licenses independently. Assess the intended use and distribution model.
Preserve required copyrights, notices, attribution, source and replacement/relinking
rights. Never copy proprietary/restricted code without permission. Prefer permissive
licenses when suitable; reciprocal licenses are not automatically prohibited, but their
obligations require a documented compliance plan. Unknown rights remain unapproved.
Software licenses do not establish rights to trademarks, likenesses or source media.

## 4. Zero mandatory costs

No essential paid APIs, subscriptions, cloud-only processing, trials, licensing servers,
external accounts or hidden paid dependencies. Optional paid providers may remain
explicitly optional enhancements; essential operation must succeed with them disabled.
Never activate billing without separate authorization.

## 5. Own the application architecture

Own and maintain project formats/schema, workflow orchestration, brand rules, approvals,
revision logic, UX, creative planning interfaces, render orchestration, poster-to-reel
integration, exports and compatibility adapters. Reuse suitable renderers, codecs,
shapers, canvas systems, STT/inference/audio engines and standard infrastructure.
Do not make another application's internal package directories a permanent dependency.
Any externally installed tool used in a prototype needs an explicit temporary boundary,
version record and replacement/independent provisioning gate before product adoption.

## 6. Inventory and recovery obligations

Maintain THIRD_PARTY_INVENTORY.md from M1 onward, including FFmpeg, HyperFrames, Ollama,
Python/Node packages, fonts, models and native dependencies. For every component record
purpose, source, version/commit/hash, license, commercial status, redistribution duties,
transitives, source location, offline-build status, runtime requirements, security,
maintenance and replacement strategy. Audit existing components before redistribution.
Do not change functioning M1–M4 code or tools merely to complete documentation.

Follow OFFLINE_BUILD_STRATEGY.md for source retention, lockfiles, toolchains, notices,
model/font manifests, checksums, backups and recovery. Claim reproducibility only after
an actual recorded offline rebuild/recovery test on a clean isolated environment.

## 7. Parallel safety and authorization

M5 write boundary: /Users/Nadish/projects/AI Video Editor./Codex/AI Studio.
Production and Reel Studio_dev stay read-only for the M5 agent. Never modify shared
models, virtual environments, global tools/configuration, caches or browser profiles.
No copying, downloading, installing, vendoring or modifying third-party dependencies
without separate authorization. No milestone merge, production swap or release without
separate authorization, regression evidence and rollback plan.
The explicit M5 Phase 1 parallel-development exception does not close M4. Future engine
integration still requires an accepted, identified M4 baseline and separate approval.
Documentation permission does not authorize Phase 2 implementation. Already authorized
work may continue within its existing scope; this policy adds no blanket setup approval.

## 8. Required decision record before recommending implementation

For each significant feature, record:
1. Existing open-source solutions and official sources.
2. Best technical fit and alternatives considered.
3. Legal reuse/redistribution assessment, including transitive dependencies.
4. What can legally be retained locally and what is missing.
5. Offline runtime, installation and rebuild feasibility/evidence.
6. Application-specific work we must build.
7. Remaining security, maintenance, hardware, license and cost risks.
8. Maintenance, replacement and recovery if upstream disappears.

## 9. Enforcement gates

- Proposal: complete the eight-question decision record before substantial new work.
- Adoption: update the inventory, review rights/source retention and obtain required
  copy/install/vendor approval before changing dependencies.
- Implementation: keep formats and orchestration independent; apply scoped tests and
  document every network/runtime/resource dependency.
- Acceptance: verify offline essential workflows, regression protection and recovery;
  distinguish static inspection, historical evidence and newly executed checks.
- Distribution: audit all shipped components, notices/source offers and asset/model
  rights; verify an independently provisioned build before a release claim.
- Handoff: list versions, hashes, source gaps, test evidence and pending approvals.

This file is the durable project policy reference. It does not install an automatic
agent hook or propagate instructions into other chats/workspaces; future handoffs must
explicitly reference it. The other M4 agent has not been interrupted or messaged.
