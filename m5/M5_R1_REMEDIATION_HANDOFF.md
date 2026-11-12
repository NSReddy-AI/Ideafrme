# M5 R1 — targeted acceptance-defect remediation

2026-11-10. Scope: only the two independently reproduced R1 audit defects.
Remediation implemented and tested; R1 acceptance remains a separate user decision.
No R2–R6 work or authorization is implied.

## Changes

Changed `style_recipes/state.py`: transaction validation maintains a local current head
for each Finding identity while processing the proposed DAG. Duplicate initial identities,
sibling corrections and stale-parent corrections are rejected rather than arbitrated by
record IDs. Valid linear chains, including chains supplied in reverse input/UUID order,
are checked by ancestry. Snapshot reconstruction uses the same validation and appends
Finding events in validated topological order, so reopening cannot select a conflicting
revision by UUID ordering. Canonical commit-reference sorting is unchanged; it does not
decide the logical Finding head. Invalid legacy forks fail closed; no history is migrated
or rewritten. Other logical record types and their existing branching rules are unchanged.

Changed `style_recipes/manual.py`: edits deep-copy the existing Recipe rather than
rebuilding active properties from all retained Findings. A rename changes only the name
and required new-revision metadata. A targeted property edit changes only that property
and its chosen Finding revision, preserving other active properties and inactive/excluded
observations, including other observations of the same property. It selects the active
Finding when editing an active property. No review/approval is inherited by the new hash.

Created `r1_tests/test_targeted_remediation.py`: 17 targeted regressions covering duplicate
initial IDs, competing corrections, stale ancestry, branched chains, valid linear chains,
independent chains, reversed ordering, disk reopen validation, failed transaction
preservation, inactive/excluded selection, targeted edits, deep-copy behavior and immutable
original records. The malformed legacy-fork fixture exists only in the new synthetic run.

Created `tools/run_r1_remediation.py`: a scoped test harness using a fresh evidence
directory. It redirects the four legacy report destinations and supplies new synthetic
store factories at runtime without editing old tests or runners. The original CLI test
is excluded because its destination is hardcoded; the original 55-test runner is not rerun.
No schema, creative@1 format, compatibility contract, dependencies or unrelated features
were changed. This handoff is the only new project documentation.

## Executed tests and evidence

Fresh evidence directory:
`.runtime/r1/remediation-20261110T210532971307Z/`

Exact successful command, from AI Studio:

```sh
/usr/bin/sandbox-exec -f .runtime/r1/remediation-20261110T210532971307Z/isolation.sb python3 -B tools/run_r1_remediation.py --evidence .runtime/r1/remediation-20261110T210532971307Z
```

Exit 0. **59 tests passed: 17 new targeted tests and 42 existing contract/persistence
tests.** No failures or errors. Approximately 39.6 seconds. The kernel sandbox denied
networking and limited ALL test writes to this fresh directory, narrower than the original
R1 fence. The desktop sandbox initially rejected nested sandbox application; the command
then ran with the scoped sandbox permission. The policy was not weakened.

The existing canonicalization test reproduced **46 Python/JavaScript cases** with equal
bytes/hashes or equal rejection outcomes, writing its results only into the fresh run.
The existing persistence tests reproduced **148 fault scenarios**: 42 normal process exits,
32 recovery process exits, 42 normal injected-ENOSPC cases and 32 recovery injected-ENOSPC
cases. SIGKILL, competing writers, local sync/lock/replace probes and OS isolation tests
also passed. These remain process/fault-injection tests, not OS-crash or physical power-loss
proof; the disk was not exhausted. No new offline rebuild claim is made.

Evidence in that directory:
- `before.json`: previous evidence hashes, prior source manifest and protected baseline.
- `tests.txt`: complete 59-test transcript.
- `results.json`: result, command, changed-source hashes and preservation checks.
- `cross-language-results.json`: fresh canonicalization case results.
- `persistence-fault-results.json`: fresh 148-row fault evidence.
- `filesystem-qualification.json`, `isolation-results.json`: fresh probe evidence.
- `isolation.sb`: exact restricted OS policy used for this run.
- `stores/`, `legacy-test-stores/`: new synthetic stores only.

The runner refuses to overwrite a run containing tests.txt. To reproduce again, create
another new remediation-* directory with its own before.json and policy; do not rerun
into this completed directory or use the original evidence-writing runner.

## Preservation and stopping boundary

All previously recorded top-level R1 evidence files match their pre-remediation hashes.
The OS test fence also excluded previous test-store directories. The original acceptance
manifest intentionally remains unchanged: its two implementation hashes now describe
the pre-fix source, not this remediation. `results.json` supplies the new source hashes.
Only state.py and manual.py changed among its 17 previously recorded source/fixture files.

All **25 protected baseline files** match. No creative_core, poster_render, existing
test/fixture/runner, M4 or production file was modified. No previous acceptance evidence
was removed or overwritten. No package, model, font or dependency was installed; no
Git setup, integration, production swap or paid service was performed.

The broader R1 acceptance audit is not replaced by this targeted regression run. The
earlier 55-regression pass remains historical evidence, not newly executed evidence.
Request user review of the two fixes and fresh results. Stop here; do not begin R2.
