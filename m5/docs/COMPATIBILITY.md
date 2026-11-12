# Deferred integration contract — no M4 integration performed

## Expected interface

A future adapter receives a validated creative document, an explicitly selected approved
snapshot, a frozen accepted M4 baseline identifier, and a NEW isolated output-job root.
It emits a legacy `project.json`, required build/media inputs and a conversion manifest.
It must never overwrite the originating creative project or a released legacy project.

The adapter must validate current asset hashes and approval fingerprints immediately
before use. Only approved supported creative features can be converted. Poster-only
projects and unsupported features are refused clearly. Merely adding a `requires` key
does not establish that an unchanged legacy engine will refuse a new format safely.

## Field ownership

M5 owns creative document identity/revision, views, editable elements/layout/style,
bound editorial content, source references, brand snapshot references, approvals,
named snapshots and reversible history. M5 will own the conversion manifest linking
creative version/hash to a separately generated reel job and its export hashes.

The existing engine owns its legacy project field interpretation, platform/brand/style
configuration interpretation, plan approval fingerprint rules, cut/words/audio/motion
inputs, build processing, export versioning, progress events and QA results.
M5 must not claim that its document-level approval replaces the M4 approval gate.

Legacy-origin fields remain engine-owned and preserved unless an explicitly approved
mapping delegates one to the adapter. Shared facts/quotes need source ID/time mappings,
not merely text copying. Any engine writeback must go through an explicit reviewed
import transaction; no automatic bidirectional synchronization.

## Adapter outline (future)

1. Verify full M4 acceptance and exact baseline manifest.
2. Freeze the approved M5 snapshot, content bindings, assets and font/brand bytes.
3. Map approved content and supported layout/motion into job-local legacy inputs.
4. Preserve unknown legacy fields; refuse ambiguous ownership or changed baseline.
5. Call the unchanged engine only in the isolated generated job after path auditing.
6. Run existing reel_002 regression using approved copied fixtures and new compatibility
   tests; never regenerate golden baselines to hide output changes.
7. Record conversion, QA, source/target hashes and any supported-feature limitations.

## Questions blocked on M4 closure / later approval

- Exact released project/plan schema, required fields and approval fingerprint inputs.
- Final voice, safe-area and Jagan template decisions; Create-flow interface.
- Whether the adapter accepts absolute job paths safely and which jobs mutate history.
- Full set of required build files, caption time bases and supported motion presets.
- Mapping creative approvals to engine approval without bypassing either gate.
- Brand snapshot semantics and asset pinning; output naming and rollback policy.
- Pixel/audio tolerance and fixture manifests for the released regression contract.

No 4K reel support is claimed. The production 1080×1920 reel baseline stays protected.
No source manifest has been approved for copying M4 code/assets, and none was copied.
