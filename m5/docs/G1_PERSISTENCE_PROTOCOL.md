# G1 — Local persistence and recovery protocol

Draft 2, 2026-11-10. DOCUMENTATION ONLY — VERIFICATION DOES NOT AUTHORIZE IMPLEMENTATION.
Describes future R1 storage, not implemented behavior. No directory, lock, fixture,
record or project association is created by this document. R1/R2–R6 remain unauthorized.
Companions: G1_STYLE_RECORD_CONTRACTS.md and G1_CANONICAL_TEST_VECTORS.md.

## 1. Supported boundary and proposed layout

One local user, one writer per store, explicit user confirmation of review actions.
Initial target is a tested local macOS filesystem with exclusive advisory file locking,
exclusive creation, file/directory flush and same-directory atomic replacement. Do not
assume filesystem name alone proves these guarantees. Removable/network/cloud-synced
stores and multi-host editing are read-only until separately qualified. Files lacking
reliable atomic replacement OR locking OR durable directory sync are read-only: no
in-place overwrite, time-based lock stealing or best-effort save fallback.

Proposed store (names fixed, not user-controlled paths):

```text
records/<payload-sha256>.json    immutable canonical envelopes (including commits)
HEAD                           canonical commit Ref, newline-free, <=1024 bytes
PREVIOUS                       previous committed HEAD Ref, same encoding/bound
.writer.lock                   stable lock inode, never replaced/unlinked by app
.writer.info.json              advisory diagnostics, never lock authority
staging/<transaction-uuid>/     writer-owned bounded scratch only
```

No indexes needed for R1; mutable caches can never establish approval or overwrite
records. HEAD is the only publication point. PREVIOUS is a recovery aid, not an automatic
alternative HEAD. All traversed refs resolve within records by derived hash filename;
no path/URL from record data. Approved and draft records are application write-once,
not filesystem WORM or protection from a malicious local owner.

Opening/import: validate regular files, reject symlinks/hard-linked external inputs,
devices/FIFOs, traversal and path races using store-root directory handles and no-follow
operations. Root must not change during use. External input is bounded JSON bytes only;
never enumerate its containing folder or decode media. R1 does not claim the later
automated-media sandbox. Store writers hold user-granted access only to selected store.
Store resource cap for each transaction: 64 MiB new record bytes, 4096 records, bounded
graph per contracts; preflight free space is advisory, not protection against disk-full.

## 2. Commit and visibility contract

Commit is another immutable envelope with exact payload:

```text
{
 format:"ai-reel-studio/style-commit@1", record_id:ID,
 created_at:Time, created_by:ID,
 previous:Ref?, sequence:Int,
 action:"save"|"review"|"associate"|"dependency-event"|"rights-decision"|"recover",
 additions:[Ref], roots:[Ref],
 recovery_from:{head_present:boolean,head_bytes_sha256:Hash,previous:Ref}?
}
```

Same canonical/schema/bounds rules apply. previous is the exact preceding Commit or
null for first commit; sequence is 1 initially then previous.sequence+1, reject overflow.
Additions are all newly introduced records (excluding this commit), unique sorted by
record_id. Roots are the complete current logical root set after this transaction,
unique sorted by record_id, pointing to Recipe/Association/DependencyEvent/Review/Brand/
Finding/Dependency/RightsDecision records, not commits. Retain at most 32 roots; adding beyond that
fails rather than pruning history. Old roots can leave the active set only through an
explicit user-visible transaction; all prior committed records remain reachable in
commit ancestry. Latest event for a subject is determined by commit sequence, at most
one event per subject/scope per commit; reference order never picks a winner.

Each addition must reference only earlier committed records or earlier DAG nodes of
this addition set; no absent targets or cycles. Referenced snapshots are present locally
before publishing associations. A Ref plus matching payload does not prove current
eligibility: follow committed review/dependency events as well. Uncommitted/orphan
records and events are NEVER treated as approval, even if well-formed and hash-valid.
Readers take one HEAD snapshot, validate its full bounded chain/closure, and read only
that view. If HEAD changes during reading, finish the old immutable view or retry;
never combine unrelated heads. Refuse approval/apply if closure cannot be validated.
Commit ancestry itself uses max 4096 records/64 MiB/depth 64 closure bounds; when reached,
stop new writes pending a separately approved archival/checkpoint contract.

`action=review` must include its Review and subject prerequisites in closure; `associate`
includes Association/snapshot; `dependency-event` includes its event; `rights-decision`
includes its RightsDecision. `save` cannot hide a new Review/DependencyEvent/Association/
RightsDecision. `recover` cannot introduce an approve event.
Review/association/dependency-event/rights-decision actions introduce exactly one corresponding
event or association; they may also include prerequisite non-event records. They cannot
hide another action's event type. Recover introduces no new review/association/dependency/rights
event; it only selects the validated historical snapshot plus its recovery commit.
Actions are not operation permission: R1 still cannot write existing creative projects.
recovery_from is null except recover, where it records the observed recovery generation:
HEAD presence and SHA-256 of exact observed bytes (empty bytes when absent), plus the
verified PREVIOUS Ref selected for recovery. It must match preserved recovery evidence
and commit.previous. A damaged record/HEAD is never overwritten silently.

## 3. Writer ownership and conflicts

1. Open the existing stable .writer.lock inode (exclusive-create only for first setup),
   obtain nonblocking exclusive OS advisory lock. Verify directory/lock identity through
   held handles. If locked, report busy and make no transaction writes. Readers do not
   need the writer lock. No unlink/recreate of a lock that another process might hold.
2. Optional diagnostics: actor, PID, process start identity, transaction UUID. PID/age/
   timeout/metadata are NOT lock authority. A crashed process's OS lock releases on
   descriptor/process exit; stale metadata alone is harmless and replaced only after
   successful lock acquisition. Never break a held lock because the PID seems old.
3. NORMAL WRITES ONLY: user/editor supplies expected HEAD Ref (null only for empty new store), plus expected
   parent recipe/association pins. Under lock, reread and validate HEAD, compare exact
   refs and parent pins. A mismatch returns conflict; no overwrite, auto-merge or implicit
   fork. User may explicitly create a new draft revision after reviewing current state.
4. If lock semantics cannot be established or root changed, stop all writes. Corrupt
   HEAD stops NORMAL writes and requires the distinct recovery state machine below.
   Competing normal commits claiming one predecessor require investigation; a verified
   recovery branch is explicit and does not automatically activate abandoned branches.
   No timestamp last-writer-wins. External noncooperating writers invalidate guarantees.

## 4. Normal-commit state machine and durable ordering

Before first save, qualify filesystem support in an authorized isolated fixture store,
not production. Initial store creation is future setup requiring implementation scope;
HEAD/PREVIOUS absent is valid only with no prior committed store history, never an excuse
to silently initialize a damaged populated store.

States: N0 read-only/open -> N1 locked generation validated -> N2 records durable ->
N3 commit durable -> N4 recovery pointer durable -> N5 HEAD published -> N6 directory
sync confirmed/success. Any error before N5 leaves old HEAD active; after publication
without confirmed sync is UNCERTAIN, never reported success. No transition to recovery
implicitly. Normal generation = exact HEAD Ref including hash/record_id plus its sequence;
null generation is allowed only for an explicitly new empty store. Hold the same OS lock
and store-root handle throughout. Recheck generation immediately before replacing each
pointer; a changed/malformed generation aborts and blocks further writes.

While holding lock and after NORMAL expected-head checks:

1. Validate all new payloads, entire reference graph, review authority/eligibility and
   current dependencies. Create transaction staging with exclusive creation. Serialize
   canonical envelopes, flush each file, reopen and revalidate bytes/hash. No original
   payload or approved record is edited. Staging is not visible committed state.
   Eligibility is action-specific: draft saves and adverse events may commit while use
   is blocked; only an approve action requires its subject's approval prerequisites.
   Do not reject a valid deny/revoke because it makes a dependency ineligible. Approval
   evaluates prerequisites without requiring an existing approval of the same subject.
2. Publish each immutable record to records/<hash>.json using exclusive creation (never
   replacement), bounded copy from validated staging, file flush, reopen hash/shape check.
   If a file exists, reuse ONLY if canonical envelope bytes match exactly. Corrupt or
   partially written existing file is a storage error; no automatic overwrite. This
   exclusive-create step can leave a partial orphan on interruption; readers cannot
   reach it before HEAD publication. Flush records directory after completed records.
3. Construct Commit using exact old HEAD/next sequence and complete additions/roots;
   validate; persist using the same immutable procedure, flush file and records directory.
   Referenced subject payloads precede their Review event and commit durability. Validate commit
   closure again before publication. A durable commit file alone does NOT activate it.
4. For noninitial commit, write old HEAD bytes to unique sibling temporary PREVIOUS file,
   flush/reopen/validate; atomically replace PREVIOUS and flush store directory. This
   retains a known-good recovery pointer before touching HEAD. Initial commit has no
   PREVIOUS. Failure here aborts publication; old HEAD remains active.
   Replace PREVIOUS only with this validated current HEAD and only after its closure
   passes again; never copy malformed HEAD bytes. Existing invalid PREVIOUS requires
   preservation/explicit repair, not silent overwrite. This step is NOT used by recovery.
5. Write new canonical Commit Ref to unique sibling temporary HEAD file; flush/reopen/
   validate. Atomically replace HEAD and flush store directory. Only now report committed
   success. If replacement occurred but directory flush fails, report UNCERTAIN COMMIT,
   retain lock while inspecting, block further actions and require explicit reopen/
   recovery. Do not claim rollback or delete the possibly committed event.
6. Cleanup only this transaction's staging, report retained bytes on failure, then release
   OS lock. Cleanup failure never changes commit truth. No automatic record/history
   garbage collection in R1. Never touch source media, M4, production or unrelated files.

File flush means OS durable-sync mechanism accepted during filesystem qualification;
buffer flush alone is insufficient. Full power-loss guarantees depend on actual storage
and retained fault evidence; do not claim them from API calls alone. An OS/drive that
cannot supply the required durability leaves writes disabled. No two-file atomicity
claim is made: immutable records/events become visible together through the single HEAD.

## 5. Review, invalidation and recovery outcomes

Approval intent may be shown before commit, but UI must not show saved approval until
the durable HEAD step succeeds. An interrupted recipe save leaves previous committed
state or an orphan draft; interrupted review leaves prior review state unless its entire
commit became reachable. A committed adverse dependency event blocks affected current
use even if historical approve event remains intact. Restoration requires fresh review.

On reopen, never choose the highest sequence/timestamp or scan for a convenient approve
event. Validate HEAD, its ancestry and every active reference. If valid, expose that
snapshot; orphan newer commits remain inert. If invalid/missing on a populated store,
open read-only, list bounded safe diagnostics, preserve original bytes. Do not initialize
HEAD or promote PREVIOUS automatically. A partial new store similarly requires recovery.

### 5.1 Recovery-only state machine (never the normal pointer algorithm)

States: Q0 damaged/missing HEAD, read-only -> Q1 locked observed generation verified ->
Q2 quarantine durable and valid PREVIOUS selected/user confirmed -> Q3 recover commit
durable -> Q4 recovery HEAD published -> Q5 directory sync confirmed/success.
Recovery does NOT require damaged HEAD to parse or validate and does NOT perform normal
step 4 (PREVIOUS replacement). It shares only immutable-record writing and HEAD's
flush/atomic-replace/directory-sync primitives with normal commits.

1. Before asking for a recovery choice, capture HEAD presence/raw byte hash, PREVIOUS
   exact Ref and root identity. Under the stable OS lock compare those observations
   again. Any mismatch means stale recovery consent: stay read-only and show the new
   state. Bound pointer reads at 1024 bytes; oversized/malformed paths require separate
   manual forensic handling, not unrestricted reads or automatic recovery.
2. Preserve exact damaged HEAD bytes and relevant observations in user-approved,
   store-local quarantine using exclusive create, file sync and directory sync; record
   absence explicitly. Validate PREVIOUS and its complete closure. Show abandoned
   transactions, missing resources and approval invalidation. User must confirm this
   exact captured generation and selected Ref, while lock remains held; no reply means
   no publication. If PREVIOUS invalid, no in-place recovery: remain read-only and offer
   only separately approved salvage to a qualified store, with no transferred approval.
3. Build recover Commit with previous=selected PREVIOUS, sequence=that commit.sequence+1,
   roots exactly that commit.roots, additions=[], recovery_from=captured generation.
   Persist/flush/validate commit and records directory. Its branch sequence is not a
   global high-water mark; exact commit Ref distinguishes branches of equal sequence.
   Preserved damaged bytes are evidence, never imported as reachable approval events.
4. Immediately before publication recheck HEAD presence/raw hash, root/lock identity
   and PREVIOUS Ref/closure against captured generation. Any change aborts; never adopt
   a newly appeared HEAD or use time-based ordering. Prepare/flush/reopen a sibling HEAD
   temporary containing recover Commit Ref; atomically replace HEAD and sync directory.
   PREVIOUS MUST remain byte-for-byte unchanged throughout recovery and afterward; it
   may advance only in a subsequent successful NORMAL commit with a valid current HEAD.
5. Before Q4 failure leaves original damaged/missing HEAD and valid PREVIOUS unchanged,
   plus inert quarantine/orphans. Q4 without confirmed directory sync is UNCERTAIN;
   no success/rollback claim, no PREVIOUS rotation. Reopen exposes either valid recovery
   HEAD (approvals still invalidated) or explicit recovery-needed state; orphan recovery
   commits are never selected automatically. Q5 reports recovered, review-required.

No guessing a root from orphan files. The valid recovery pointer survives interruption
at every Q state. A retry captures a new generation/consent and can reuse only identical
validated immutable records. No protocol claims atomicity of multiple mutable pointers.

A recover commit makes all prior approvals in that branch historical-only for current
eligibility until fresh reviews after recovery; approved payloads/events remain intact.
Damaged hash-path records require separate user-reviewed quarantine/byte-identical
restore from verified retained originals; never substitute equivalent/new dependencies.
No recovery can infer rights, recreate missing resource bytes from hashes or authorize R1.

## 6. Required future fault evidence (R1-C)

Future tests use synthetic stores wholly inside AI Studio, with commands, fixture hashes,
fault positions, old/new HEAD hashes and actual reachable review state retained:

- Interrupt before/during each staging/record/commit write and each flush; prior HEAD
  remains valid, or explicit recoverable orphan; no orphan approval becomes active.
- Interrupt before/after PREVIOUS and HEAD replacement; reopening shows old or new
  complete snapshot, otherwise explicit read-only recovery. No mixed snapshot/false pass.
- Disk-full/permission failure at every write/flush and cleanup: never report success
  early; original bytes retained; uncertain publication distinctly reported.
- Two writers with same expected HEAD: only lock holder commits; other receives busy
  then stale conflict. Stale metadata/PID reuse cannot steal held lock; crash releases it.
- Corrupt HEAD, PREVIOUS, referenced payload/event, missing snapshot/dependency and
  duplicate identity: detect, refuse approval, preserve bytes and require recovery choice.
- Simulated non-atomic replace, failed directory sync, unsupported locking and root/link
  races: writes disabled; no fallback to overwriting. Real target qualification required
  in addition to mocks; process termination is not proof of power-loss durability.
- Unicode/canonical hash vectors, old snapshot after library update and repeated reopen:
  exact pins preserved; recipe/application/output approvals remain separate.
- Dependency revocation/restoration and recovery: historical events preserved, current
  use blocked until revalidation/fresh approval, never silently reactivated.
- Every N/Q transition: retain observed generation, expected Ref/raw hash, pointer bytes
  and reopen outcome. During Q, assert PREVIOUS unchanged at every injected fault; stale
  recovery consent must refuse publication. Recovery retry must not activate orphan reviews.

Read-only design verification checks ordering and failure cases; it does not execute
these tests or establish filesystem qualification. A accepts the contract and later
R1 evidence separately; B/C decide relevant rights/content issues. G1 is still pending
review, R1 remains NOT AUTHORIZED, and G7 independent offline rebuild remains open.
