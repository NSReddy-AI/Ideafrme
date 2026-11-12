# Optional agent completion revision (synthetic only)

This revision closes controller/protocol/local-rollout gaps without editing the first
foundation, Track 1, R1, frozen R2 records, Studio source, M4 or production. It reuses
the existing first-party foundation and Python standard library; no new dependencies.

From the AI Studio workspace:

```sh
python3 -B -m media_analysis_agent_v2 serve --root "$PWD/.runtime/media-agent/my-v2-instance"
```

The CLI is explicitly started; it initially reports DISABLED. Commands are flat JSON
lines: enable, start, submit(value, optional scenario), wait, status, stop, cancel,
disable, recover, rollback, capabilities, quit. No shell, URL or media pathname command.
State/configuration behavior and real-media refusal remain as documented in the first
foundation README. No source package discovery or automatic agent startup is added to Studio.

## Communication, deadlines and revocation

Private inherited pipes only; protocol v1, session UUID and per-request UUID. Exactly
one response may be outstanding. Continuous reception rejects unsolicited, duplicate,
stale-job, old-session, unknown-version and malformed responses, including while idle.
There is no downgrade or retry. Faults revoke the current session, disable execution,
quarantine the last synthetic result and require explicit recovery/enable/start.
Rollback/stop/cancel revoke sessions and confirm process exit; failure remains FAULTED.

8 KiB frames, 1 KiB string fields, <=16 KiB cumulative TX+RX per synthetic job, <=1 MiB
per session, <=128 completed IDs per session. Counters include received rejected frames
and handshake traffic in session totals; per-job totals include both request and response.
Bytes/IDs cannot grow without limit across an idle/persistent session. Pending requests
are bounded; pipe drain supplies backpressure and bounded readers pause further buffering.
The continuous reader consumes no model/image content. Synthetic success never authorizes
R2 report publication or real use; operational_eligible is always false.

A separate monotonic watchdog starts at job submission and covers transport, validation
and publication of the synthetic result, independently of the <=15-second processing
wait. The <=60-second complete-job deadline may only be tightened. Startup separately
bounds spawn plus handshake to <=2 seconds. Expiry cancels the pending computation,
revokes the session, kills the child and waits for confirmation. No late result publishes.
These are trusted-controller safeguards, not hard real-time or hostile-worker proofs.

Original 1 GiB aggregate attributable memory, 128 MiB scratch, <=4 worker processes,
one configured compute thread/serial stages, CPU-only, PNG/geometry/density limits and
256 MiB full compressed deployment target remain unchanged. No real boundary is qualified.
The tiny synthetic child has no native decoder, GPU, writable-file or descendant-launch
path. Host IO threads are not silently classified as worker compute threads.

## Offline local installation and replacement

Package commands create only NEW first-party artifacts beneath `.runtime/media-agent/`:

```text
python3 -B -m media_analysis_agent_v2 build --output <new-runtime-zip> --version 0.2.0
python3 -B -m media_analysis_agent_v2 install --root <new-runtime-deployment> --bundle <zip> --sha256 <explicit-pin>
python3 -B -m media_analysis_agent_v2 activate --root <deployment> --version 0.2.0
python3 -B -m media_analysis_agent_v2 rollback --root <deployment>
```

The Python Deployment.command(instance) API returns the exact independently runnable
installed entry point after verifying its selected version and payload hashes. No process
starts from install/activate. Default OFF applies to new instances. No executable input
is taken from media or worker output. The operator must approve the explicit bundle hash.

Bundles contain first-party source, a strict file/hash manifest, retained local Python
notice and source-input/derivation provenance. ZIP contents and timestamps are deterministic.
Archive and expanded sizes are bounded, paths/names/aliases are allowlisted, and a version
is never overwritten. Interrupted installs are not auto-activated or repaired. Activation
verifies closure and atomically changes the local selection pointer. Updates always have
qualification=null and real_media_enabled=false; no previous certificate is inherited.

Only current local-workspace installation is supported. Bundled first-party policy is
explicitly derived to anchor writes to the authorized AI Studio workspace; the original
source remains unchanged. The existing foundation backend source inode is the stable
read-only admission coordinator across these versions. Do not replace/copy that anchor
while controllers run. This is not cross-machine or arbitrary-installation admission.

Activation/install/rollback are fenced while any foundation/v2 backend holds that shared
admission. Deployment.rollback(agent) first disables the supplied agent, revokes its
session and confirms exit; it then switches to an immutable prior version. Reports and
evidence are not deleted or migrated. A CLI rollback requires processing to be stopped
already and refuses otherwise. Explicit future start is always necessary.

This is a local first-party source package, **not the complete distribution closure**.
Existing Python/macOS remain declared prerequisites; the Python binary, full stdlib/native
closure and toolchain sources are not bundled or claimed independently rebuilt. Compressed
first-party size is reported, but meeting that size alone does not prove the full 256 MiB
target. Future runtime/models/codecs/notices must all count, without hiding components in
optional packages. Source access, a Python notice or a matching hash is not commercial
distribution clearance. First-party release licensing and full offline rebuild remain open.

## Eventual capabilities and actual next steps

Mandatory: uploaded image/poster measurements, style extraction, independently evaluated
English/Telugu OCR and editable confidence-aware Recipes; uploaded reel shot/scene/motion/
pacing/timing/style analysis; image-to-reel and reel-to-poster adaptation. They are not
implemented by synthetic echo. No thumbnails, decoding, OCR, FFmpeg, model downloads,
automatic R1 writes or project Apply are enabled here.

Next real-media steps: (1) separately qualify a specific supported resource/access/lifecycle
boundary with complete attributable-host-memory/sink accounting; (2) approve exact pinned
decoder/OCR/model/native artifacts and licensing/source closure; (3) implement the qualified
image profile and lawful English/Telugu evaluation under separate authorization; (4) review
a temporal video contract/codec allowlist and explicit resource profile, then separately
implement/evaluate reel analysis; (5) review cross-format mapping and dual R2/R1 eligibility
before any manual bridge/application. No larger historical video budget is inherited.

## Verification scope

The new suite reuses unchanged synthetic lifecycle cases against this controller and adds
budget/replay/watchdog/package/update/rollback tests. It exercises existing creative_core
public create/edit/save/reopen APIs only on fresh synthetic documents while analysis is
absent/disabled/hung/crashed/incompatible. This demonstrates current core independence,
not production-UI usability or full Studio feature acceptance. No legacy project suite runs.

New files only; original evidence retained. Test resource accounting and Python audit
guards do not qualify hostile native code, physical power-loss durability or filesystem
race resistance. Gate A remains BLOCKED and real-media interfaces refuse before handle IO.
