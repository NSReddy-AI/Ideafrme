# Brand Application B — separate quarantine foundation

Decision: compatibility/admission foundation implemented; **NO-GO for live asset placement, decoding or export**. No media format qualified. Work stops at a concrete missing enforcement mechanism, not a pending permission to run the already authorized qualification.

## Implemented boundary

New explicit CLI/library package studio_media_workflow. It is not imported by ordinary Studio and does not alter its HTTP routes, renderer, validators, stores or startup. A separate media-workflow-* root inside .runtime/studio-ui has media-workflow-session.json (studio-media-session@1), its own lifetime nonblocking OS writer lock, HEAD.json (studio-media-head@1) and immutable commits/<sequence8>-<uuidhex>/workflow.json. No manual/Visual marker, legacy creative.json mirror, automatic adoption or migration. Older readers fail on missing own ownership/version and reject the distinct envelope instead of coercing it into a manual project.

Envelope studio-media-workflow@1/version1 contains session_id,generation,parent,document,binding,admissions,state,recovered_from. Embedded creative remains ai-reel-studio/creative@1/schema_version1; original core validator is reused. Embedded binding remains studio-project-binding@1, validated by its existing validator. New foundation state is strictly quarantined; active assets (including historical states) and qualified-state assertions are refused. Admissions are separate quarantined metadata, NOT enabled layers or an asset-bearing document disguised as metadata-only Studio. Future activation needs a separately qualified processing/promotion implementation and an explicit compatible workflow-version decision; no latent force-enable switch exists.

The initial creative is a new pending project, not silently imported or migrated user data. There is no operational media editor yet. Existing metadata-only Studio remains fully separate; old creative/history/binding/Brand Library contracts and approved data were not changed. No new core asset-registration operation was invented: the current add operation only adds a layer, and adding references to an existing project's asset inventory requires a future explicit compatibility design. Media placement/edit/Undo/export remains intentionally unavailable.

## Rights, identity and quarantine

Explicitly selected Brand Library and approved brand hash are required for asset admission. Reuses the live pin checks, approved asset membership, exact rights-event binding, internal_preview/library_metadata, commercial_design/poster and (for font candidates) font_embed/poster. Current rights, expiry and adverse brand restrictions are rechecked on every processing request. Registration, a hash or a historical grant never enables use. Trusted-local reviewer/provenance labels are not authenticated legal clearance.

Admission checks registered record identity/hash, actual BLOB length and SHA-256 (maximum8MiB existing library bound) before creating a metadata receipt. It does not copy opaque input bytes into the workflow, render a preview, parse a font/image, follow references or run a processor. Candidate declarations png/svg/ttf/otf are constrained by the registered kind; unknown declarations/paths/templates refuse. A declaration is explicitly not format validation. Even an SVG containing active content can only remain opaque in the existing library with a quarantined-unparsed receipt; processing always refuses. No sanitizer or safe-SVG claim is made. All candidate file types remain disabled for live use.

## Atomic metadata persistence and recovery

Expected-head hash plus lifetime nonblocking flock and thread RLock reject stale/concurrent writers. File/directory synchronization, exclusive immutable files, canonical JSON/hash readback and one HEAD replacement publish a whole metadata generation. Document/binding cannot change across admission generations; admissions append one record. Earlier records/heads' referenced generations remain intact. Max64 admissions,200 generations/candidates,1024 entries,10MiB envelope,8MiB creative payload and128MiB application metadata/recovery budget. Unknown versions, corrupted hashes, links, special paths, missing/invalid HEAD and incomplete initialization refuse rather than repair/delete.

The128MiB limit here is a trusted metadata-history budget, NOT a worker scratch quota and NOT evidence of Gate A enforcement. Code/path checks are trusted-local-actor application controls, not a kernel sandbox against a compromised process.

Injected failures before publication preserve the old HEAD. After publication, a whole new generation can be reopened and validated; the failed instance blocks further writes. Unsupported synchronization fails and blocks publication in that instance; no durability success is claimed. Missing/tampered HEAD is not automatically reconstructed. candidates lists validated candidates; recover-copy requires explicit selected commit, a new root and acknowledgement that later changes are excluded. It preserves immediate selected source bytes in immutable recovery-source.json, carries admissions in quarantine, assigns new session/binding identity, advances creative revision and clears current approvals. Revoked historical metadata remains recoverable, but processing revalidates live rights and refuses. This is immediate-source recovery, not a complete portable historical dependency/library backup or physical power-loss proof. Partial failed initialization/candidates are retained for diagnosis.

## Local enforcement inventory and real blocker

Observed without installing/launching tools: Darwin25.6.0/arm64, CPython3.15.2. sandbox-exec,swift,clang found in PATH. qemu-system-aarch64,limactl,colima,docker,wasmtime,bwrap,prlimit not found in PATH; this is not a claim about every application elsewhere on the machine. PIL,png,wasmtime absent from the active interpreter's import search. Linux cgroup filesystem absent. Existing project inventory documents the global legacy HyperFrames/Puppeteer/Sharp/libvips stack and unqualified native/VM candidates. No new evidence justified repeating those rejected investigations, compiling them or launching a VM.

The missing enforceable boundary must cover all of:
- Hard1GiB aggregate worker job memory including descendants/shared allocations and attributable host buffers.
-128MiB across every worker-controlled writable sink, including temporary/memory-backed/open-deleted storage and output.
- Process/thread admission, cancellation and descendant termination against a compromised worker, not merely cooperative children in one process group.
- Complete filesystem/network isolation and supervisor death/crash handling, within the unchanged15s worker/60s job timing and remaining limits.

No new installed facility was identified that proves this combination. This does not prove no solution can ever exist on macOS. A configured compute thread, per-file limit, RSS poller, existing Python audit hook, browser sandbox or Sharp decoder is not equivalent to these requirements. No such shortcut was implemented or represented as qualification.

containment.status reports the unchanged limits, inspected local facilities and missing proofs. require_qualified unconditionally rejects; there is no JSON attestation, user-provided backend claim or force flag that can turn live processing on. This is fail-closed admission, NOT an implemented containment sandbox. Zero workers launched; no claim that cancellation, worker memory/scratch quotas, network denial or unsafe-media decode were experimentally qualified. Ordinary Studio receives no media output.

## Dependencies/licensing/offline status

New functionality uses installed Python standard library, existing core/canonical validators, file-sync/path helpers and existing sqlite3-backed Brand Library. No third-party source copied or new library/runtime adopted; no decoder replacement/codec/sandbox invented. Existing installed-stack notices and source/build gaps remain in THIRD_PARTY_INVENTORY.md and the current handoffs. Python carries PSF/incorporated obligations, SQLite deliverable public-domain status does not close native/build provenance, and installed legacy Puppeteer/Sharp/native license declarations do not make their processing boundary safe. Those packages were not executed/adopted by this batch. Matching runtime/transitive source, full notices, toolchains and clean offline reproduction remain unverified; no distribution claim. No downloads or acquisition.

## Targeted evidence

Final command: python3 -I -B tools/run_media_workflow_tests.py --run-id visual-media-foundation-targeted-final —exit0,22passed,0failures/errors,~1.63s, no source drift/rejected writes/child commands. All test writes inside that fresh runtime root;30s test deadline. Earlier22/22 development run retained, not added to total. No broad regressions or repeated media experiments.

Checks cover new namespace/older-reader rejection, explicit future-version refusal, exact English/Telugu/combining-mark metadata, approved brand membership, BLOB hash/length/provenance, stale-head and duplicate refusal, missing permissions/font-embedding scope/revocation, disabled processing before Popen, active-content isolation, unknown-format/path rejection, writer contention, simulated ENOSPC before publication, interrupted response after publication, metadata budget refusal, sync failure, explicit recovery with revoked rights, corrupt HEAD/no repair, symlink refusal, rejection of active/qualified flags, and unchanged original Studio create/save/reopen. Synthetic bytes are intentionally not decoded. No actual disk exhaustion, power-loss or OS crash.

CLI inventory: python3 -B -m studio_media_workflow status —exit2 intentionally reports unqualified/disabled, not a test failure. Output retained in .runtime/studio-ui/visual-media-foundation-01/local-containment-status.json.

Other explicit commands:
- python3 -B -m studio_media_workflow new --root '<workspace>/.runtime/studio-ui/media-workflow-NEW' --topic 'Pending media'
- ... inspect --root '<owned media root>'
- ... admit --root '<owned media root>' --library '<explicit in-workspace library>' --asset '<UUID>' --format png --expected-head '<current token>'
- ... process --root '<owned media root>' --library '<explicit library>' --asset '<UUID>' —always refuses until a qualified backend is implemented separately.
- ... candidates --root '<owned media root>'
- ... recover-copy --root '<owned media root>' --commit '<validated candidate>' --destination '<new media-workflow-* root>' --acknowledge

The command examples are usage guidance, not additional executed workflows. Tests exercise the same library paths; no actual private Brand Library or protected workspace was selected. No test server/UI or model started.

## Files and preservation

Eight created; zero existing files changed:
- studio_media_workflow/__init__.py
- studio_media_workflow/contracts.py
- studio_media_workflow/containment.py
- studio_media_workflow/store.py
- studio_media_workflow/__main__.py
- media_workflow_tests/test_boundary.py
- tools/run_media_workflow_tests.py
- docs/MEDIA_WORKFLOW_FOUNDATION.md

New evidence only under .runtime/studio-ui/visual-media-foundation-01 and fresh targeted run roots. Exact hashes/source preservation: completion.json in the foundation evidence root. Brand A and all existing application source remain unchanged. No M4/M6/production/R1 or frozen-checkpoint access/modification. Existing M5 security documents were read for the binding requirements; Gate A decisions/implementation were not changed. Frozen checkpoint was not opened for a new hash audit because this authorization forbids accessing it; preservation is no-touch, not newly independently hash-verified in this batch.

## Completion and next boundary

Implemented: separate versioned quarantine/admission/persistence/recovery foundation. Containment mechanisms implemented: none beyond trusted metadata controls and fail-closed processing refusal. Actual enforcement evidence: application denial before any worker/render path, metadata rights/hash/path/lock/commit/budget checks. This must not be called worker containment.

New formats supported for live placement: NONE. PNG/SVG/TTF/OTF remain disabled; other formats are not admitted even as declarations. Existing metadata-only Studio and its already pinned fonts remain untouched. No media placement/edit/export workflow or processor was enabled.

NO-GO for live Brand Application B. The smallest necessary external change is availability and explicit qualification of a concrete mechanism meeting the aggregate memory/sink/process/network contract. If that requires new artifacts, acquisition/provisioning needs its separate permission; installing a VM by itself is not proof, and no generic VM/XPC/Wasm cycle is recommended. Alternatively the resource-accounting requirements need an explicit product decision; no change was assumed. No protected contract modification is necessary for the implemented quarantine foundation. Live media activation will still need an explicit reader/profile/promotion design and assets-before-layer/history policy; this batch does not smuggle such changes into existing contracts.

STOP at this technical enforcement boundary. No further decoding, asset placement or gated work proceeds automatically.
