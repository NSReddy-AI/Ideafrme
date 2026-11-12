# R2 — architecture, security and failure design

Draft 1, 2026-11-10. DESIGN ONLY; no worker, sandbox, format or test is implemented here.
Read with [technical spec](R2_IMAGE_ANALYSIS_SPEC.md), [acceptance](R2_ACCEPTANCE_MATRIX.md),
[licence gate](R2_DEPENDENCY_AND_LICENCE_MATRIX.md), Reference spec section 15 and
[accepted R1 boundary](M5_R1_ACCEPTANCE_RECORD.md). No M4/production reads/writes or
R1/creative@1 changes are needed. The existing poster engine stays unchanged.

## 1. Trust and pipeline

Trusted local supervisor -> selected immutable input handle -> isolated PNG worker ->
normalized bounded RGBA + feature pages -> optional serial OCR worker with normalized
PGM only -> strict supervisor validation -> immutable analysis index/pages -> user review
-> explicit manual R1 bridge. No renderer/project Apply service exists in R2.

Trust the locally confirming actor only within R1's documented model, not the image,
metadata, OCR text, worker result, filename or model suggestion. Assume native decoder
compromise. No worker gets shell/agent authority, project Store handles or approval keys.
The supervisor never imports the image decoder or executes metadata/text instructions.
The analysis namespace is separate; untrusted worker data cannot become R1 records directly.

Future locations (not created): `r2_data/inputs/<hash>`, immutable analysis records and
review events, and `.runtime/r2/jobs/<job-uuid>/` scratch/evidence. Initial imports must
already be inside AI Studio or arrive through a separately explicitly authorized copy;
no directory crawling or implicit access to protected workspaces. Input selection grants
one file, not its parent directory. Source names are display-only sanitized labels.

## 2. Secure import and normalized transfer

Supervisor obtains a no-follow regular-file handle under the authorized root, rejects
symlinks/hard-link aliases/devices/FIFOs/directories and enforces encoded size on the
handle while reading. Read/hash to an exclusive job-owned snapshot, verify size/hash
after copy, preserve original unchanged. Replacing the selected source path cannot
redirect the worker. Record original/source snapshot equality; no source mutation.

Bounded preflight reads PNG signature and declared IHDR only; no untrusted decompression
in the supervisor. Worker repeats checks, validates chunk lengths/CRCs/IEND, rejects
unknown critical chunks, trailing payloads, animation acTL/multiple frames, interlace,
unsupported 16-bit input and unsupported color/profile combinations. Maximum 4096
chunks and 256 KiB aggregate ancillary data; embedded text is never interpreted as
instructions. ICC compressed bytes <=64 KiB and decompressed <=64 KiB, enforced in the
worker before CMS use. Unsupported metadata yields a specific unsupported/error result,
not a parser exception used to activate unrestricted format fallback.

Decoder uses PNG-only loading, no registered external plugins, delegates, URLs, ImageShow,
shell utilities or optional remote data. Treat decompression warnings as rejection;
header limits are checked again against actual decoded dimensions/mode. No reuse of the
Phase2 browser's broad-readable sandbox or Chrome no-sandbox workaround.

Normalized transfer: supervisor checks declared width/height/stride and exact byte count
before accepting RGBA, plus profile/source hash. OCR receives a bounded derived PGM
only, with explicit dimensions and no arbitrary metadata. Derivation does not clear
source rights. Worker result records are checked for all schema/bound/reference/hash
rules; wrong job/source/profile, forged paths, duplicate fields or extra output refuse
the entire result. Only whitelisted output basenames are read through held directory
handles; reject links, aliases, special files and path/open races. Decode no thumbnails
in the supervisor as a hidden second image-import path.

## 3. Binding resource envelope

These retain or tighten existing Reference section 15 bounds, not new relaxed limits.

| Resource | Binding maximum | Required enforcement and failure |
|---|---|---|
| Input | one PNG; 10 MiB encoded | Handle-based bounded read; reject before full decode |
| Source dimensions | 8192 per edge; 16,777,216 pixels | Validate header and decoded result; checked multiplication |
| Analysis image | 2048 per edge | Pinned downscale; full decode remains subject to source memory cap |
| Memory | 1 GiB aggregate worker-process tree | OS-enforced allocation/containment limit; overshoot must be denied/killed, not merely observed |
| Worker wall time | 15 s total across decode/extract/OCR stages | Monotonic external supervisor deadline; descendants terminated on expiry |
| Job deadline | 60 s including setup, validation and cancellation | Supervisor deadline independent of worker cooperation; expiry blocks result publication |
| Scratch | 128 MiB aggregate job filesystem | Enforced quota/bounded storage facility plus capped stdout/stderr; no unbounded core dumps |
| Result | 1 MiB aggregate, <=32 pages | Bounded parse and strict per-page G1 canonical limits |
| OCR/result density | 512 words; 16,384 text scalars; 64 observations | Explicit overflow/incomplete outcome; never silent truncation |
| Concurrency | one job; serial decoding/OCR, <=4 processes | OS child-process policy, no uncontrolled fork/thread pool; one configured compute thread |

The 1 GiB cap excludes the trusted supervisor/OS but includes every untrusted decoder,
CMS and OCR descendant. The host application must not run optional local models during
R2 benchmarking. On 24 GB hardware these are requirements, not measured fit claims.
The 15 s aggregate budget includes both OCR languages; it is not 15 s per tool.

## 4. OS isolation gate — still unresolved

Require a deny-by-default child policy: read only immutable input/derived handles,
the exact pinned runtime/native libraries, selected eng/tel models and explicitly listed
OS resources; write only its unique job scratch. No home/other-job/project directories,
R1 evidence/stores, browser profiles, shared caches or M4/production access. Deny network,
unneeded local IPC, executable launches outside the declared tree and arbitrary plugins.
Inherited environment must not contain secrets or search paths pointing to user plugins.

The R1 sandbox allows broad reads and workspace R1 writes; it is NOT reused as the
automated-media boundary. The Phase2 synthetic renderer is also NOT proof. Python audit
hooks, environment settings, decoder warnings, RSS polling and soft thread limits are
defense-in-depth only. Check native allocation, mmap, children and hidden temporary files.

Native macOS worker confinement is the preferred low-dependency candidate, conditional
on proving every bound. No verified aggregate memory/quota facility has been selected.
Do not assume RLIMIT_AS/RSS/file-size limits cover all native allocations or cumulative
scratch. A filesystem write allowlist is not a storage quota, and per-file caps are not
an aggregate job cap. A process monitor may supplement but cannot replace hard enforcement.

If the platform cannot demonstrate the table, automated decode remains DISABLED. A
separately reviewed constrained VM/container backend may be proposed, with its own free/
open-source licences, arm64 kernel/runtime, hard cgroup/quota facilities, storage/build
closure and acquisition approval. None is selected or installed by this proposal.
No administrative privilege escalation or system configuration change is implicit.
Do not silently relax requirements to make a zero-install prototype pass.

Before arbitrary media exposure, R2-S acceptance must use synthetic hostile probes to
demonstrate external-read/write/network/IPC denial, hard OOM/quota handling, fork attempts,
timeouts, descendant cleanup and denial at exact boundary values. Sampling alone fails.

## 5. Job state, cancellation and publication

Proposed states: selected -> preflight -> isolated-decode -> extract -> optional-ocr ->
validate -> draft-complete. Terminal alternatives: unsupported, failed, canceled,
quarantined. Approval is a later append-only event, never a worker-produced state.
No partial success is automatically treated as a complete result; each unavailable
metric has a safe error code and reason. R1 manual operation remains available throughout.

Cancel/deadline/resource failure: stop entire process tree, confirm termination, close
handles; do not publish a completed index or R1 Recipe. Cleanup only that job's files.
Cleanup failure quarantines the job, reports retained bytes, disables reuse and never
deletes source/brand/project records. No automatic retry; explicit retry creates a new
job with the same immutable source/profile or a newly approved profile. At most one retry
per user request, no automatic fallback codec/model. Temporary results retained only on
explicit user choice, labeled incomplete/unreviewed and ineligible for bridge approval.

Supervisor publishes validated pages by exclusive content-hash creation, file sync,
reopen/hash verification and directory sync; then publishes the index and commits its
job-local result pointer atomically. Reviews/corrections are separate immutable records
with exact subject/previous refs and expected-head/single-writer checks. R2's new report
store contract must be reviewed separately: do not call R1 Store private methods or add
new formats to its closed validator. Reuse public canonical helpers and OS primitives;
the new namespace still requires its own crash/failure evidence, not inherited R1 results.
Keep last validated pointer, preserve corrupt bytes, never scan orphans for approval,
and use explicit recovery with no pointer rotation until a valid normal commit. Flush
failure after pointer publication is UNCERTAIN, not success or claimed rollback.

## 6. Provenance, revocation and manual bridge

Separate source identity, report identity, rights status, analysis review, R1 Recipe
definition approval and future application/output approval. Unknown or insufficient
rights permit no affected approved use; acquisition/redistribution permissions are
separate. Even a derived OCR transcript or thumbnail can have content/privacy rights.
Apply the immutable Brand-version benign/adverse rules in Reference section 14.

For a manual bridge, retain valid report index/pages first. Create only accepted R1
Dependency records with content_sha256 pinning opaque source/report/profile resources;
do NOT put a new-format Ref in an R1 Ref field. Existing rights decisions/events govern
each pin. User confirmation then creates new user-entered Finding/Recipe records with
explicit evidence refs and manual palette/layout choices. No automatic Apply, no scene
sidecar, no source/method field bypass. Bridge APIs and mapping fixtures require review.
Commit exact Recipe revision once; stale expected R1 HEAD fails without overwrite.
An orphan report is harmless and unapproved if the later R1 commit fails. No cross-store
atomicity claim: never show bridge success/approval until the relevant R1 commit succeeds.

Source/profile changes, missing resources, adverse brand restrictions and revoked rights
block affected current eligibility through recorded dependency events and fresh review;
history is immutable. Reanalysis cannot overwrite correction records or approved Recipes.
Imports of newer/unsupported report formats are refused for interpretation, not migrated.
Logs retain IDs/hashes/error stages/resource bounds, not private full OCR text or secrets.

## 7. Launch prerequisites and remaining risks

No worker launch until A accepts: exact report/bridge schema and vectors; enforceable
resource/isolation backend; artifact/source/licence manifest; frozen fixture/threshold
profile; reviewer assignments. These are explicit unresolved entries, not delegated
implementation guesses. No native decoder, OCR data or confinement mechanism was tested
in this documentation task. Physical power-loss durability, clean offline rebuild,
distribution audit and malicious-local-owner resistance remain unproven boundaries.
