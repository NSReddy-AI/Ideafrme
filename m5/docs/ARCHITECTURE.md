# Architecture and invariants

## Ownership

`creative.json` is the authoritative creative document. It has no Fabric.js or engine
objects. Fabric is provisional, Konva is the fallback, HTML/SVG is the later poster
direction, and FFmpeg/HyperFrames remain the later reel engine. None is installed here.

Pure document/operation code is separated from filesystem validation and persistence.
Validation checks structural types, exact field allowlists, finite/ranged geometry,
typed references, duplicate IDs, history continuity, snapshots and approval hashes.
No arbitrary Python, shell, HTML, SVG script or model operations execute.

## Reversibility and approvals

Each operation stores complete before/after core states. This favors correctness and
inspectability for a small foundation over history size/performance. Undo/redo changes
the cursor, increments revision and clears current approval. An edit after undo discards
the redo branch. Empty/no-effect/invalid operations are rejected without input mutation.
History is limited to 200 transactions; named versions to 100; record lists to 1000.

The fingerprint covers format, identity, project settings, brand reference, languages,
views, assets, content and elements. It excludes revision, history, approval records and
named versions. Asset hashes are checked during validation. All assets must have hashes
before approval. Relevant changes clear approval; undo does not resurrect it.
Approvals describe caller-confirmed review, not authentication, authorization or proof
of factual truth. There is no UI in which a user can approve in this phase.

Named snapshots are deep copies, hash-checked, and append-only across saves. The API
does not edit them. Files are ordinary JSON, not tamper-proof storage: an external editor
can rewrite both a snapshot and its hash. Authentic signatures are outside scope.

## Persistence and recovery

Loading is read-only. Duplicate keys, malformed UTF-8/JSON, nonstandard numeric constants,
unknown versions and invalid documents fail explicitly. No migration/repair occurs.
Input/output JSON is capped at 16 MiB. Parsing still requires bounded local memory;
this is not an internet-facing hostile-input service.

Saving validates the candidate and any existing primary first, checks identity/revision,
and preserves saved named versions. Unchanged saves do not rotate recovery data.
The previous valid primary is flushed into `.previous` with atomic replacement, then
the new primary is flushed and atomically replaced. Temporary siblings are cleaned up
after ordinary exceptions. Directory fsync is best effort where supported.

Recovery is explicit: `recover_previous(root)` returns a validated document without
writing. Save it under a NEW filename, inspect it, and only later decide replacement.
A corrupt primary is never automatically overwritten. Missing/mutated historical assets
can prevent strict validation/recovery; restore those bytes from backup first.

Simulated flush/replace interruptions are tested; power loss, filesystem corruption and
actual process termination are not. A hard kill can leave an unused temporary sibling.
The `.previous` file is one revision of recovery, not an independent backup.

## Filesystem safety

Paths must be normalized project-relative POSIX paths. Absolute paths, `..`, backslashes,
drive/URL notation and symlinks are rejected. Root/ancestor symlinks are also rejected.
No directories are implicitly created by persistence. Test data and audit logs stay in
AI Studio. No subprocess, shared model/venv/cache access or network is required.

This is not a race-proof filesystem sandbox: path checks and subsequent opens are
separate operations. Concurrent hostile symlink replacement, hard-link aliases and
cross-process save races are not fully prevented. `expected_digest` detects an observed
stale file but is not locking. Use a single trusted local writer. Before a future server
or untrusted import feature, add appropriate OS isolation, stronger file-descriptor based
confinement/locking and archive/media import checks.

## Deliberate limits

- Custom standard-library validator for a documented subset, not a general JSON Schema
  implementation. No formal JSON Schema compatibility is claimed.
- Telugu/English Unicode preservation is tested; shaping, IME, caret behavior, line
  breaking, font availability, originality and visual typography are not tested.
- Geometry permits intentional off-canvas positioning; poster safe-area/overflow QA is
  deferred. No SVG path syntax, color syntax or media decoder validation yet.
- No layers panel, grouping, animation timeline, print color management, renderer or
  export pipeline. Video elements are references only.
- No automatic migrations, editor integration, legacy conversion, fact verification,
  identity editing, model integration or paid providers.
- Asset reads/hashing scale with history/snapshot validation; optimize only with tests
  when larger real projects are approved. Do not bypass content integrity for speed.
