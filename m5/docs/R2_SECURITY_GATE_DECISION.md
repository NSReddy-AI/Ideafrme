# R2 Gate A — security/resource decision

2026-11-10. Read-only official-source research and proposed proof requirements only.
No process confinement, volume, VM, decoder or probe was created or run. **Gate A:
BLOCKED / enforcement UNVERIFIED.** A complete viable native combination has not been
established; this is not proof that every possible native solution is impossible.

Read [prior security proposal](R2_ARCHITECTURE_AND_SECURITY.md),
[artifact plan](R2_ARTIFACT_QUALIFICATION_PLAN.md), [roadmap](R2_IMPLEMENTATION_READINESS_ROADMAP.md).
The accepted R1 sandbox, interpreter audit hooks and Phase2 renderer are not this boundary.

## 1. Threat model and unchanged envelope

Assume malicious PNG/metadata, native decoder/CMS/OCR compromise, fork/thread storms,
allocation/mmap/output floods, symlink/path races, inherited descriptors and malicious
worker results. Trusted supervisor authorizes ONE immutable input, validates bounded
output and owns review/store authority. Worker has no R1/brand/project handles or keys.
No protected workspace access, source mutation, arbitrary shell, instruction execution,
network or unrelated filesystem enumeration. No model interprets metadata as commands.
Signed helpers identify code, not the truth of their outputs or safety after compromise.

Hard requirements remain: 10MiB encoded;16,777,216 source pixels;8192 source edge;
2048 analysis edge;1GiB aggregate untrusted memory;128MiB aggregate scratch;15s worker
processing;60s complete job;one concurrent job;four worker processes;1MiB result.
No technology may receive a larger budget merely to pass. Native allocations, descendants,
temporary/shared memory, open-deleted files and output sinks must be accounted for.
Trusted supervisor/host OS are outside the worker budget as previously defined, but
their actual footprint must still be measured on24GB hardware and cannot be hidden.

## 2. Candidate comparison — documented, not experimentally qualified

| Candidate | Mechanism and documented capability | Gaps / privilege / distribution | Decision |
|---|---|---|---|
| Separately sandboxed native XPC helper | Public App Sandbox entitlements/XPC privilege separation; omit network/file/app-group exceptions; broker bounded messages/handles | Does not establish aggregate descendant memory, job-specific PID admission or scratch quota. Runtime/system read allowances and inherited descriptors need audit. Packaging/signing entitlements required | Useful component; insufficient proven complete architecture |
| Inherited sandbox child | Inherits static sandbox rights with required entitlements | Inheriting a broad supervisor's rights is unsafe; cannot infer exact-file read isolation. New native code remains hostile after compromise | Reject as shortcut; separate least-privilege service preferred |
| sandbox-exec/SBPL custom policy | Existing test tooling can deny paths/network | Apple DTS says SBPL is undocumented for third-party products and advises against product dependence; no aggregate resource proof. Deprecation discussions are not a removal-date guarantee | Test aid only, reject permanent product boundary |
| setrlimit, process group, RSS monitor | Documented process/file/UID resource controls and timer/signal primitives | Per-file is not aggregate scratch; per-UID processes affect unrelated tasks; RSS is not a hard job RAM bound. Descendants may change groups/sessions. Polling is reactive | Defense-in-depth only, cannot close Gate A |
| Broker-only scratch/fixed-capacity storage | Supervisor can reject writes once its byte ledger is full if no other write sink exists | Must deny direct growth of writable FDs and every alternate sink; metadata/open-deleted data complicate accounting. Not memory/PID confinement | Feasible component proposal, UNVERIFIED |
| APFS dedicated quota volume | Apple documents volume quota | Host volume provisioning needs separate authorization, metadata/lifecycle accounting and proofs; solves neither memory nor descendant admission | Reject default R2 deployment complexity; possible separately approved experiment |
| Minimal Linux arm64 VM on Apple Virtualization.framework | Public Linux guest/configured RAM/device framework; guest cgroups, namespaces, bounded mounts | New kernel/rootfs/toolchain/signing closure, VM boot/host overhead, device attack surface. Not installed or performance-qualified | Preferred separately authorized PoC candidate if native full proof unavailable |

Sources: [Apple App Sandbox](https://developer.apple.com/documentation/security/app-sandbox),
[entitlements/inheritance](https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html),
[XPC](https://developer.apple.com/documentation/XPC),
[network entitlement semantics](https://developer.apple.com/documentation/BundleResources/Entitlements/com.apple.security.network.server),
[Apple DTS SBPL guidance](https://developer.apple.com/forums/thread/661939),
[setrlimit](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setrlimit.2.html),
[setsid](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/setsid.2.html),
[APFS quotas](https://support.apple.com/guide/disk-utility/add-delete-or-erase-apfs-volumes-dskua9e6a110/mac).
The DTS recommendation is staff guidance; user comments in that discussion are not OS API guarantees.

## 3. Preferred candidate design, not an enforcement pass

Use a small signed/restricted host launcher and an immutable Linux arm64 guest with
NO NIC, host directory sharing, clipboard, GUI/GPU or general host agent. Input delivered
as one immutable bounded byte resource/read-only device or narrow transport; no host
path from the worker. Output transport must validate length/types and stop at1MiB.
Keep virtualization helper separate from R1 supervisor/store authority. A fresh guest
job owns no secrets; process-tree escape inside guest must not grant host files/rights.

Apple documents [Linux VM support](https://developer.apple.com/documentation/virtualization/creating-and-running-a-linux-virtual-machine)
and [configuration](https://developer.apple.com/documentation/virtualization/vzvirtualmachineconfiguration).
The virtualization entitlement and code-signing/deployment path must be qualified;
local ad-hoc signing is a candidate, not a demonstrated entitlement outcome. No SIP,
system security changes, administrator entitlement workaround or paid service assumed.
Commercial distribution/notarization obligations are separate from local operation.

Inside guest, nondelegated per-job cgroup v2: proposed memory.max=1073741824,
memory.swap.max=0, memory.oom.group=1, pids.max=4, supervisor outside that group and
cgroup.kill for cleanup. Membership inherited by descendants; worker cannot migrate
itself/change limits. **pids counts tasks/threads**, so this is stricter than four processes
and must fit actual runtimes. The kernel documents possible temporary memory.max
overshoot: this configuration alone does NOT prove an instantaneous1GiB ceiling.
[Kernel cgroup documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html).

Configure guest physical RAM <=1GiB, no swap/ballooning or worker-accessible general host shared-memory
device/transport as a second
candidate bound. Virtualization still uses host-backed pages/device buffers; these
are not claimed absent. Guest RAM is not total host VM footprint. Whether this bounds the
required untrusted allocation metric, including kernel/device accounting, must be
proved and explicitly agreed; host helper overhead cannot be mislabeled as zero.
Do not silently reinterpret1GiB as merely an average RSS or relax it to allow overshoot.
If literal strict enforcement cannot be demonstrated, the gate remains blocked.

One job scratch mount, tmpfs size=134217728 with finite inode count; rootfs and input
read-only, no other writable mounts/swap/core dumps, bounded stdout/stderr and shm.
A tmpfs data cap is not automatically a cap on all metadata or host disk writes.
Count tmpfs in worker RAM as well as scratch; no double-budget assumption. Guest mount/
PID/IPC/network isolation, dropped capabilities, no_new_privs and syscall allowlists
are required defense layers, not substitutes for a complete sandbox.
[tmpfs](https://docs.kernel.org/filesystems/tmpfs.html),
[seccomp](https://docs.kernel.org/userspace-api/seccomp_filter.html).

## 4. Time, lifecycle and safe transfer

Host monotonic supervisor controls60s job deadline; guest trusted supervisor controls
aggregate15s worker processing and serial decode/OCR. No15s-per-stage interpretation.
Kill, not merely cooperative cancel, at budget expiry. Verify all descendants stopped;
existing2s termination-confirmation target must be reconciled with15s hard work bound:
it is confirmation latency, not permission for2s more processing. Scheduling latency
must be measured; no perfect real-time guarantee inferred from a timer API.
If supervisor dies, job must be killed/quarantined before new work is admitted. Never
resume an untrusted process on reopening a job. Kernel/VM crashes yield no valid result.

Do not simultaneously retain unbounded full source, RGBA copies, OCR arrays and report
buffers. Source max RGBA is64MiB; normalized RGBA <=16MiB, PGM <=4MiB. Budget additional
native scratch/model/runtime copies; reclaim stages serially. Transfer only validated
bounded buffers, no general shared host memory or filesystem. Store original hash and
coordinate/color transformations; revalidate even trusted-derived PGM at OCR boundary.

## 5. Exact future proof requirements and separate authorization

No media decoding in the proposed first PoC. Ask for separate permission to provision
the declared launcher/kernel/rootfs/toolchain artifacts and run synthetic allocation,
process and file probes ONLY in a new isolated AI Studio location. No shared venv/global
configuration changes. Later decoder/OCR trials need their own approved artifact/input scope.

Record actual OS/CPU/framework/kernel/runtime hashes, entitlements, mounts/cgroups,
syscall policies, guest RAM, no-NIC/no-share configuration, commands/exits, max observed
usage, exact denial conditions and retained failure evidence. Probes must include:

- Allocation/mmap/native children/thread storms, invalid group migration and limit changes.
- Single/many-file growth, metadata/inodes, sparse files, open-deleted files, alternate
  temp/shm locations, stdout floods, core dumps and all device output paths.
- Every boundary -1/exact/+1, attempted unrelated reads/writes/network/IPC/exec, inherited
  FDs, supervisor death, worker hang, cancel, VM failure and cleanup failure.
- Denial BEFORE unauthorized publication, no surviving descendants, no worker approval
  authority, unchanged accepted baselines and no protected-workspace access probes.
  Use synthetic denied destinations, not actual private/M4/production paths.

Configuration-only inspection, successful ordinary images or RSS sampling cannot pass.
Any gap stays UNVERIFIED; literal limit failure is BLOCKED. Acquisition budgets, signing,
host footprint, cold boot/OCR latency and native runtime licenses remain unresolved.
No mandatory paid VM product is chosen. Kernel/user-space redistribution duties require
separate source/notice closure, see artifact plan. No implementation is authorized.
