# Manual Style Recipe authoring — R1

Implementation is a structured local CLI and Python library, not a canvas/editor UI.
It creates style records only; creative.json remains authoritative and unchanged.
Use commands from /Users/Nadish/projects/AI Video Editor./Codex/AI Studio.
All store writes are confined to r1_data or .runtime/r1 under that workspace.
The commands below are instructions, not a pre-created or approved real brand/project.

## Create and edit

Choose a stable local actor UUID; it is an audit label, not authenticated identity.
Use a new store directory; init refuses existing directories, including damaged stores.

```sh
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 init
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 new --name 'తెలుగు / English' --property palette.primary --value-json '{"kind":"color","rgba":"#3366ffff"}'
```

Output identifies the Finding and Recipe payload hashes. Use the exact hashes returned.
Typed decimal properties use strings plus units, for example
`{"kind":"decimal","value":"0.1","unit":"ratio"}` for layout.margin.
Noncanonical decimals, unknown properties, nonmanual origins and unsupported outputs fail.

```sh
python3 -B -m style_recipes --store r1_data/manual-demo list
python3 -B -m style_recipes --store r1_data/manual-demo show RECIPE_HASH
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 edit RECIPE_HASH --name 'New draft name'
```

Editing creates a new revision/hash with a parent Ref; it cannot overwrite old payloads.
Property edits also require --property, --value-json and --reason, create a correction
Finding, and invalidate current use of superseded finding pins. No approval carries over.

## Explicit reviews

For a resource-free manual color Finding, explicitly confirm availability, then review
the Finding, then review the Recipe. Each command names an exact committed hash:

```sh
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 availability FINDING_HASH --state available --reason 'Verified manual entry' --confirm
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 review FINDING_HASH --decision approve --authority A --reason 'Reviewed manual value' --confirm
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 review RECIPE_HASH --decision approve --authority A --reason 'Reviewed transferable recipe definition' --confirm
python3 -B -m style_recipes --store r1_data/manual-demo eligibility RECIPE_HASH
```

Decisions reject/revoke (and exclude for Findings) append events. Restoring availability
does not restore approval; re-review affected leaves, then the Recipe. These are recipe
definition reviews only, never application/publication approval. CLI exit 2 reports
invalid input, blocked eligibility or storage conflict; success is not returned before
HEAD directory sync. UNCERTAIN COMMIT/RECOVERY means inspect/reopen, not assume rollback.

`write FILE` imports one record or an array of closed, bounded JSON records from within
AI Studio. It defaults to draft save; it cannot smuggle reviews/availability/associations.
`--action rights-decision --confirm` permits structured manual rights decisions. A B
review additionally needs --verified-evidence with the exact evidence hash, explicit
confirmation and actual human evidence/authority verification. This flag is an
attestation, not automated evidence retrieval or legal clearance. Obligations whose
fulfillment is not implemented remain blocked. No remote references are resolved.

Initial Brand snapshots and Dependency pins use the G1 closed shapes. Brand revisions
require explicit --brand-classification benign/adverse and --confirm; adverse applicable
pins must already have committed stale/revoked dependency events. Classification evidence
is retained in store-local quarantine; it does not itself grant Recipe approval.

`associate RECIPE_HASH --project-id UUID --synthetic-creative-json FILE` validates an
existing synthetic creative@1 document read-only and writes only a style association.
The creative id must start with synthetic-. This tests dependency snapshots; real
project integration, layer binding and creative+sidecar transactions remain out of scope.

## Recovery

`recovery-status` returns HEAD presence/raw hash and verified PREVIOUS Ref. Preserve that
exact JSON, inspect the selected history/lost work, then use:

```sh
python3 -B -m style_recipes --store r1_data/manual-demo --actor 00000000-0000-4000-8000-000000000002 recover --generation-json 'EXACT_JSON_FROM_RECOVERY_STATUS' --confirm
```

Recovery preserves damaged bytes as synced quarantine evidence, publishes a recovery
commit from PREVIOUS, never rotates PREVIOUS, and invalidates historical approvals for
current use. Stale generation or absent/invalid PREVIOUS refuses recovery. No automatic
repair, orphan approval promotion, migration, garbage collection or dependency download.
Resource closure must be revalidated and fresh ordered reviews supplied after recovery.

## Reproduce acceptance

```sh
/usr/bin/sandbox-exec -f docs/R1_TEST_ISOLATION.sb python3 -B tools/run_r1.py
python3 -B tests/run_isolated.py
```

The desktop sandbox may require permission to apply the dedicated nested OS sandbox.
Do not weaken it or run the OS denial probe suite without it. The R1 policy denies
networking and all writes except R1 data/evidence. Existing regression tests use their
unchanged original isolation runner. See ../M5_R1_HANDOFF.md for results and limitations.
