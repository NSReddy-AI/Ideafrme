# Optional Media Analysis Agent foundation

Implemented in isolation, 2026-11-10. Existing Studio/R1/M4/production are not connected
or modified. This is an independently runnable **trusted synthetic lifecycle service**,
not an approved media-processing boundary. It introduces no persisted R2 formats and
does not create, modify or expand the Track 1 package/test allowlist.

## Run locally

From `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`, using existing Python:

```sh
python3 -B -m media_analysis_agent --root "$PWD/.runtime/media-agent/manual-instance"
```

The CLI prints its initial status and capabilities, then accepts one flat JSON command
per line on stdin. It is not a network server. Start in a terminal to enter commands:

```json
{"op":"enable","backend":"synthetic"}
{"op":"start"}
{"op":"submit","value":"తెలుగు / English"}
{"op":"wait"}
{"op":"status"}
{"op":"disable"}
{"op":"quit"}
```

Other controls: `stop`, `cancel`, `recover`, `rollback`, `capabilities`. Start never
enables implicitly; enable never starts. A saved enable preference reopens STOPPED,
never running. A new instance is DISABLED. The CLI process itself is explicitly invoked;
Studio startup has no imports, package discovery or service dependency on this package.

`submit` returns immediately. `wait` explicitly waits for that job; a separate application
caller can continue other asyncio tasks while the service works. Avoid waiting on the UI
thread. Cancellation and deadlines continue while the CLI waits for its next input line.
Only one job is admitted. No media paths, URLs or source bytes are accepted by this CLI.

Lifecycle: DISABLED -> explicit enable -> STOPPED -> explicit start -> STARTING -> READY
-> submit -> BUSY -> validated result -> READY. Stop/cancel terminates the synthetic child
and returns STOPPED if still enabled. Disable and rollback terminate and leave DISABLED
unless a fault requires explicit acknowledgement or termination is unconfirmed.
Faults disable execution and retain FAULTED until explicit recover. Recover confirms
termination and leaves DISABLED; enable/start/new submit must each be explicit. No old job
is resumed, no automatic retry/restart occurs and no report/Recipe approval is issued.

The controller immediately kills on timeout/cancel; confirmation uses a bounded process
wait. Failure to verify exit retains FAULTED/termination-unconfirmed. It never reports
Stopped/Disabled as a successful runtime state while exit remains unconfirmed. Close
retains instance ownership on unconfirmed termination rather than claiming cleanup.

## Synthetic scenarios

For bounded failure demonstrations, run a new instance with `--timeout 0.2`, explicitly
enable/start, then submit a known scenario:

```json
{"op":"submit","value":"synthetic only","scenario":"hang"}
{"op":"wait"}
{"op":"recover"}
```

Allowed scenarios: echo, hang, crash, malformed, oversized, wrong-session, wrong-job,
extra-field and ignore-term. Hang/ignore-term are fixed two-second trusted waits, not
infinite loops or resource stress probes. Parent EOF interrupts these waits; an idle
child exits on EOF. Startup failure scenarios are library test controls, not arbitrary
executables or CLI commands. The worker contains no descendant-launch or thread code.
Its audit hook denies network, executable launches and writable-file opens after startup.
This is defense in depth for a trusted program, not confinement against compromised native code.

## Communication and real-media interface

Live controllers share an advisory admission lock on the read-only installed backend
source inode. The trusted child inherits that descriptor, retaining admission until exit
even if the controller dies. No source bytes or metadata are rewritten by the lock.
This applies to this single installed source tree, not independently copied installations;
never replace its files while running. Cross-version hostile-worker admission remains a
future qualification obligation. No dynamic package swap is implemented.

The backend registry is first-party and explicit; no dynamic plugin discovery or arbitrary
command/path execution. A frozen Backend descriptor provides capability metadata and a
launch interface. Only the fixed synthetic script can launch. Future replacement needs
separate approved code, identity pinning, protocol and boundary qualification.

Private stdin/stdout pipes carry flat version-1 control messages, not R2 record envelopes.
Frames include newline and are at most 8192 bytes; string fields at most 1024 UTF-8 bytes.
Only one request is outstanding. JSON nesting, arrays, duplicate keys, unknown result
fields and noninteger numeric values are refused. Result session/job identity must match
the current request. stderr is merged into the same bounded channel, so stray diagnostics
fail validation rather than enter a separate unbounded capture. Logs never copy inputs.
Canceled/faulted jobs cannot publish late results. Results are synthetic-only and always
`operational_eligible=false`; no report, image, project or R1 authority is minted.

`MediaRequest(capability, input_handle, source_sha256, profile_sha256)` and
`await Agent.submit_media(request)` establish the future handle-only ingress interface.
image, ocr-eng, ocr-tel and video are listed but unavailable. All refuse **before reading
the supplied handle or launching a process**. There is no fallback to Studio renderers,
M4, installed FFmpeg/Pillow/Tesseract, a browser or hosted provider.

## Independent files, configuration and rollback

Only named runtime instances beneath `.runtime/media-agent/` are writable by the service.
No writes on package import. Each instance uses a nonblocking OS controller lock, strict
bounded config.json and capped diagnostics.jsonl (64 KiB; further events counted/dropped).
Config replacement uses an exclusive pending file, file fsync, replace and directory sync.
Corrupt config or leftover config.pending is not automatically repaired/deleted. An
interrupted write may require separately reviewed recovery or a fresh instance; config
durability is not R2's publication protocol or physical power-loss certification.
Configuration persistence errors are reported or flagged, not hidden as successful writes.

Rollback means disable/terminate, retain diagnostics/config/evidence and avoid the new
entry point. It does not delete anything or switch production packages. Fault status is
in-memory with persistent diagnostic history; a newly invoked controller never resumes a
process/job. Saved enabled state, if any, means only STOPPED, not automatic restart.

Path/alias checks assume a trusted local actor; they are not race-proof against a
concurrent malicious filesystem actor. No automatic original/project edits, R1 store
access, brand writes, main-app integration or protected-workspace access exists.

## Resources and qualification status

Policy constants preserve 1 GiB aggregate untrusted memory (including attributable host
buffers), 128 MiB scratch, 15-second processing, 60-second job, <=4 worker processes,
one configured compute thread, serial work, 1 MiB result and 256 MiB compressed deployment.
Synthetic messages use stricter 8 KiB/1 KiB bounds. Actual synthetic topology is one
single-threaded backend child; asyncio may use trusted host IO/child-wait threads. No
parallel media stages, GPU, allocator stress, models or decoder are present. Startup
timeout is <=2 seconds, synthetic processing <=15 and kill confirmation <=1 second;
timeout arguments can tighten but cannot enlarge limits. Synthetic input is tiny and
all backend waits and allocations are deliberately bounded by authored code.

**These constants/observations do not enforce or qualify the full hostile-worker memory,
scratch, thread or host-allocation contract. Gate A remains BLOCKED.** A compromised
backend's descendant termination is not proven by waiting for this trusted single child.
Synthetic controller-death tests prove only the supplied child's EOF behavior. OS crash,
power loss and adversarial native execution remain unverified.

Actual image/poster analysis, independently evaluated English/Telugu OCR, and reel/video
reference analysis remain required eventual capabilities. They need supported containment,
complete resource accounting/lifecycle proof, exact artifact and model licensing/source
closure, qualified transport, lawful annotated fixtures and separate execution acceptance.
Video also needs a reviewed temporal contract/codec allowlist; no larger historical video
budget is inherited silently. Frozen R2 contracts, R1 and creative@1 are unchanged.

## Reproducible synthetic tests

```sh
python3 -I -B tools/run_media_agent_tests.py --run-id NEW-UNIQUE-ID
```

Every ID must be unused. Tests, logs, configs, locks and results remain in that fresh
runtime root. The runner audits parent writes, network operations and child command
prefixes; it does not claim an OS hostile-media sandbox. Explicit Python CLI/worker
children only, no shell or package manager. Suite alarm: 60 seconds. Child waits are
bounded; no power-loss/disk-exhaustion experiments. Fault injection includes unconfirmed
termination and diagnostic ENOSPC, clearly distinguished from real kills/crashes.
Evidence retains source/accepted-baseline hashes and exact outcomes; old evidence is
never overwritten. Resource usage is reported after the suite; its trusted small-write
design is not a hard filesystem quota. No old R1 or rendering runner is invoked.

No dependencies were installed/acquired. Python standard library only; no model, paid
service or online account. Full offline install/rebuild/distribution closure and this
project's first-party distribution licensing remain separate open gates.
