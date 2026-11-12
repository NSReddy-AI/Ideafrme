# G1 — Style record contracts

Draft 2, 2026-11-10. DOCUMENTATION ONLY — VERIFICATION DOES NOT AUTHORIZE IMPLEMENTATION.
No G1 acceptance, R1 implementation, migration, media analysis or integration is authorized.
Scope: the manual R1 contract subset of universal G1, not completion of every G1
brand/asset/brief or later-phase contract. Companion authority: Reference Style Studio
spec sections 3–4 and 13–16, its acceptance matrix, and PROJECT_ENGINEERING_POLICY.md.
Draft 2 replaces the unimplemented draft-1 Finding/recovery/rights proposals. It is not
a migration or permission to rewrite stored files; no released format compatibility
claim follows from retaining provisional @1 names during documentation review.

## 1. Closed grammar and validation

The shapes below are normative typed grammar, not executable code. Every listed field
is required, including nullable fields; no unknown fields, coercion or implicit defaults.
`T?` means T or JSON null; `[T]` means an ordered array of T; `A|B` is a closed union.
Literal strings are exact. A record payload is one of the shapes in sections 3–8;
commit payloads are specified separately in G1_PERSISTENCE_PROTOCOL.md.

Shared scalars:

- `ID`: lowercase UUID in canonical 8-4-4-4-12 hexadecimal form, nonzero; opaque identity,
  never a filename/path or authority credential. New revisions receive new IDs.
- `Hash`: 64 lowercase hexadecimal digits, SHA-256. No prefix in these records.
- `Time`: valid Gregorian UTC `YYYY-MM-DDTHH:MM:SSZ`, year 0001–9999, no leap seconds.
  Time is descriptive, never conflict resolution or commit ordering.
- `Text`: valid Unicode scalar string, 0–4096 scalars; no normalization. Names/reasons
  require 1–256/1–4096 scalars respectively. No string is executed or treated as a path.
- `Int`: signed 64-bit JSON integer, lexical `0|-?[1-9][0-9]*`; no -0/fraction/exponent.
- `Decimal`: string matching `0|-?[1-9][0-9]*|-?(0|[1-9][0-9]*)\.[0-9]*[1-9]`,
  at most 32 characters. No -0, leading plus/zeros, exponent, or redundant trailing zeros.
  Exact decimal arithmetic/comparison; never binary float conversion or silent rounding.
- `Key`: ASCII `[a-z][a-z0-9_.-]{0,63}`. `Ref` =
  `{format:Text, record_id:ID, sha256:Hash}`; format must equal the target's supported
  format, record_id equal its record_id, and hash match its canonical payload.
- Every payload includes `format`, `record_id`, `created_at:Time`, `created_by:ID`.
  Their declarations below as `Common` expand these four fields in place.
- Stored envelope is exactly `{payload:Record, sha256:Hash}`. Hash canonical payload
  bytes only, never the envelope/self hash or separate events. Record format is included.

Before parsing, cap each envelope/input at 1,048,576 UTF-8 bytes. Strict UTF-8, no BOM;
JSON only, reject duplicate decoded keys, invalid escapes/surrogates, nonfinite/raw
floating numbers. Bound nesting to 32 (root container depth 1), total object member
occurrences to 500 across the envelope, total array items to 4096 across the envelope,
and strings as above. These are aggregate limits, not 500 per object. Validate bounded
tokens before building unrestricted structures. Reject over-limit input, not truncate.
An individual record with arrays below these maxima can still exceed aggregate limits.
No embedded media, URI resolution, filesystem path fields or executable serialization.

Validation order: bounds/encoding -> strict tokens -> exact shape/version -> field
constraints -> canonical hash -> reference graph -> eligibility. Failures retain input
unchanged and return a field path plus stable category: encoding, limit, syntax, schema,
hash, reference, conflict, protection, dependency, authority or storage. No partial load.
Opening an unsupported record permits raw read-only preservation, never interpretation.

## 2. Property vocabulary and protections

`Value` is exactly one of:

```text
{kind:"color", rgba:Text}                    # lowercase #rrggbbaa only
{kind:"decimal", value:Decimal, unit:Unit}   # ranges below
{kind:"text", value:Text}                   # descriptive, never executable
{kind:"choice", value:Text}                 # enumerations below
```

R1's closed transferable property catalog:

- `palette.primary`, `palette.secondary`, `palette.accent`, `palette.background`:
  color; literal sRGB RGBA, no automatic conversion or extraction.
- `typography.heading.font`, `typography.body.font`: choice equal to a pinned font
  dependency's dependency_id string. This names a proposal, not permission to load it.
- `typography.heading.size`, `typography.body.size`: decimal, unit `px`, 1–512 inclusive.
- `typography.heading.line_height`, `typography.body.line_height`: decimal, unit `ratio`,
  0.5–3 inclusive; `layout.margin`: decimal, unit `ratio`, 0–0.45 inclusive.
- `typography.heading.tracking`, `typography.body.tracking`: decimal, unit `em`, -0.2–1.
- `layout.alignment`: choice in `start|center|end`; `description.lighting` and
  `description.texture`: text, non-executable observations only.

`Unit` is `px|ratio|em`. R1 has no motion/audio, arbitrary CSS, SVG, font paths, layer
content or generic extension objects. Additional properties/units require a new accepted
catalog/schema and affected fixtures, not permissive fallback.

`Rule` = `{property:Key, allowed:[Value], minimum:Decimal?, maximum:Decimal?, unit:Unit?}`.
Property must be in the catalog; allowed values type-check and are unique. For decimal
properties, unit is the catalog unit and min/max may tighten its bounds; for other types,
min/max/unit must be null and allowed must be nonempty. Decimal empty allowed means any
value within the stated/catalog range. Nonempty allowed plus range is intersection.
Reject min > max, out-of-catalog range/value and an empty intersection.

`Protection` = `{target:ID?, mode:"locked"|"guided"|"free", protected_aspects:[Aspect]}`;
Aspect = `identity|content|logo|portrait|rights`. Null target means all potential targets.
No duplicate target. These aspects remain protected in every mode. Locked permits no
style changes; guided requires all pinned brand hard rules plus its guided rules;
free still requires hard rules/rights/content/identity protections. All constraints
are conjunctive; unsupported enforcement blocks future application. R1 only records
these rules; it cannot claim actual layer enforcement or override conflicts.

## 3. Dependency and minimal brand records

```text
Dependency = {
 Common(format="ai-reel-studio/style-dependency@1"),
 dependency_id:ID, kind:"brand"|"reference"|"font"|"extractor"|
                       "capability"|"render-profile"|"renderer"|"rights",
 name:Text, version:Text?, content_sha256:Hash,
 license_expression:Text?, notice_sha256:Hash?, rights_record:Ref?,
 parameters:[{key:Key, value:Value}], required: boolean
}
Brand = {
 Common(format="ai-reel-studio/style-brand@1"),
 brand_id:ID, parent:Ref?, name:Text,
 hard_rules:[Rule], guided_rules:[Rule], protections:[Protection]
}
```

Dependency parameters have unique keys in ascending Key order. Empty is valid for
manual dependencies; these are declared descriptive settings, no R2 extractor launch.
content_sha256 pins exact resource bytes (including exact brand/rights payload canonical
bytes where those are records); version labels alone never establish equality.
rights_record, if present, targets the RightsDecision below and its resource_sha256 must
equal content_sha256. A kind-rights Dependency is only a pin to supporting evidence,
not itself a clearance decision. A null license/notice/rights reference means unknown,
never permission to distribute or use restricted content. No resource is embedded here.
No remote fetching/search by name; acquisition remains separately authorized.
Brand parent must reference the same brand_id at an earlier revision. Rule properties
are unique within each rule list; same-property hard/guided constraints must intersect.
This is a minimal style-bound brand snapshot, not a replacement universal Brand Kit.
Pin existing fuller brand profiles as unsupported unless an accepted adapter exists.

### 3.1 Minimum structured rights decision

```text
RightsDecision = {
 Common(format="ai-reel-studio/style-rights-decision@1"),
 rights_id:ID, supersedes:Ref?, resource_sha256:Hash,
 decision:"grant"|"deny"|"revoke", grantor:Text,
 basis:"owned"|"license"|"permission", evidence_sha256:Hash,
 permitted_uses:["manual-style-authoring"|"reference-analysis"|"style-application"|
                 "publication"|"redistribution"],
 project_ids:[ID]?, outputs:["poster"|"reel"],
 valid_from:Time, expires_at:Time?,
 obligations:[{kind:"notice"|"attribution"|"no-redistribution", text:Text}]
}
```

grantor is nonempty and identifies the claimed rights holder/issuer, not reviewer authority.
evidence_sha256 pins the retained ownership/license/permission evidence; no evidence
retrieval or legal clearance is inferred from a hash. B explicitly verifies that evidence
and grantor authority before approving this decision using scope rights-decision. Unknown
authority, absent evidence, unsupported restrictions or uncertain interpretation deny use.
This is a record/validation design, not a legal determination or new resource acquisition.

One rights_id chain per resource hash in a store. Initial supersedes null; successors
pin the latest committed RightsDecision with same rights_id/resource hash. Competing
chains for that resource are a conflict, not a choice of the most permissive license.
Changed resource bytes require a separate chain and review. Arrays unique and sorted;
grant requires nonempty permitted_uses and outputs; deny/revoke require both arrays empty.
Null project_ids explicitly permits all project IDs; [] permits none. valid_from must
precede expires_at when nonnull. Time validity is half-open: valid_from <= evaluation
time < expires_at, with null expiry meaning no stated expiry. No wildcard implicit scopes.
Obligations have nonempty text, unique (kind,text), sorted by kind then scalar text.
No-redistribution conflicts with a redistribution grant. Unsupported/unfulfillable
obligations block that use; later phases must prove fulfillment, not just retain text.

Dependency rights_record must pin the currently approved grant, not a floating chain.
Any later deny/revoke decision in that chain blocks use immediately on commit, even if
that adverse decision has not yet received a review. Invalid input cannot become an event.
A later grant never reactivates an old pin: adopt its exact Ref in a new Dependency and
Recipe revision, obtain B review and fresh affected finding/recipe reviews. For a grant
to authorize a request, its latest Review must approve as B, it must remain the latest
decision in its chain, and requested use/project/output/time must all match. Missing,
expired, revoked, unreviewed or out-of-scope clearance fails closed. R1 requests only
manual-style-authoring; future uses remain disabled until their separate phase gates.
No application/output authority follows from approval of a rights-decision record.

## 4. Findings, corrections and independent axes

```text
Finding = {
 Common(format="ai-reel-studio/style-finding@1"),
 finding_id:ID, supersedes:Ref?, property:Key, value:Value,
 origin:"measured"|"inferred"|"user-entered",
 confidence:"high"|"medium"|"low"|"not-assessed",
 explanation:Text, evidence:[Ref], source:Ref?, method:Ref?,
 region:{x:Decimal,y:Decimal,width:Decimal,height:Decimal}?,
 interval:{start_tick:Int,end_tick:Int,timebase_num:Int,timebase_den:Int}?,
 correction_reason:Text?
}
```

property/value must match catalog. Evidence/source/method reference Dependency records;
source kind reference, method kind extractor. All must be pinned by consuming recipes.
Region uses normalized ratios, x/y>=0, width/height>0, x+width/y+height<=1. Interval
requires 0<=start<end, positive numerator/denominator; it is reserved and MUST be null
in R1. Region likewise null in manual R1; no media interpretation is enabled.
R1 origin must be user-entered, method/source null; evidence can cite manually pinned
resources without opening them. Measured/inferred are future supported shapes only:
reject R1 editing/import that claims these origins until the respective phase is accepted.

Review and availability are DERIVED independent axes, not Finding payload fields. Review
events point directly to the exact Finding they review; no back-reference or approval
revision is needed. Availability events likewise point to the exact Finding. Reviewing,
revoking or changing availability never rewrites a Finding or creates a changed copy.
Initial derived review is unreviewed, or corrected when supersedes is nonnull; initial
availability unknown until an explicit available event. Last review maps approve to
approved, exclude to excluded, reject to rejected, revoke to revoked. Origin/confidence
remain independent. Derived states are shown with the evaluation HEAD and event refs.

Corrections alone create a new Finding record_id with same finding_id/property, supersedes the
latest committed revision, nonempty correction_reason and preserved original origin/
evidence/source/method. Initial revision has null supersedes/correction_reason. Corrected
values receive no inherited approval. Reanalysis changes evidence/method and creates a
NEW finding_id. A newly committed correction makes older revisions superseded for current
use and transitively invalidates consuming recipes; explicit new recipe pins are required.
Original records and historical approvals remain identifiable. No review or availability
event changes original measured/user-entered provenance. See section 6.1 for eligibility.

## 5. Recipe revision

```text
Recipe = {
 Common(format="ai-reel-studio/style-recipe@1"),
 schema_version:1, recipe_id:ID, revision_id:ID, parent:Ref?, name:Text,
 dependencies:[Ref], brand:Ref?, findings:[Ref], protections:[Protection],
 properties:[{property:Key,value:Value,finding:Ref}],
 outputs:["poster"|"reel"], required_capabilities:[Key]
}
```

record_id MUST equal revision_id. Parent is null initially or an earlier Recipe of the
same recipe_id; no revision number inferred from clock/filename. Saved drafts are also
immutable revisions: changing anything produces a new revision_id/record_id, parent
link and hash. Approval is derived from events, never an editable status field.
Dependencies reference Dependency records, unique dependency_id, sorted by dependency_id;
brand is null or Brand and must have a matching kind-brand dependency whose content hash
equals that Brand payload hash. Findings unique by finding_id, sorted by finding_id;
only the selected revision is listed, with its superseded chain retained transitively.
Properties unique, sorted by property; each finding must be in findings and exactly
match property/value. Unavailable/unreviewed findings can be saved as draft intentions,
but recipe approval requires each active finding currently eligible under section 6.1.
Required capabilities are unique sorted
Keys and must each have a kind-capability dependency with matching name. Outputs unique
and sorted, nonempty; R1 permits only `["poster"]`; reel support is not implied.
At most 32 dependencies, 32 findings, 32 properties, 32 protections and 32 capabilities,
subject to stricter aggregate bounds. No scene graph or protected text in properties.
All hard/guided brand and recipe protections must be jointly satisfiable; rights or
unsupported required capabilities block approval. Optional missing dependencies must
not supply any active property/evidence needed to validate it; exclusion is a new revision.

## 6. Review events and current eligibility

```text
Review = {
 Common(format="ai-reel-studio/style-review@1"),
 subject:Ref, scope:"finding"|"recipe-definition"|"rights-decision",
 decision:"approve"|"exclude"|"reject"|"revoke",
 previous:Ref?, reason:Text, authority:"A"|"B"|"C",
 reviewed_dependencies:[Ref]
}
DependencyEvent = {
 Common(format="ai-reel-studio/style-dependency-event@1"),
 subject:Ref, previous:Ref?,
 state:"available"|"missing"|"stale"|"unsupported"|"failed"|"revoked"|"expired",
 reason:Text
}
```

Review subject type matches scope. Recipe-definition and rights-decision permit
approve/reject/revoke only. Rights-decision requires authority B (A may act as B under
the matrix's default delegation); reviewed_dependencies is [] for that scope.
previous references the latest committed Review for the same subject/scope, or null if
none; conflicting event chains fail expected-head validation. DependencyEvent subject
is Dependency or Finding and previous similarly pins its latest committed event. Commit ancestry
orders events; timestamps do not. reviewed_dependencies must equal the subject Recipe's
dependencies for recipe scope, or the Finding's unique evidence/source/method refs sorted
by record_id for finding scope. Exact hashes, no floating resource versions.
Actor identity/authority is explicitly confirmed by A (Nadish); B/C delegation must be
retained in review evidence, defaulting to A. Plain files are not authenticated signatures.
An approve event is valid only after validating subject, closures, protections and roles;
missing/unapproved rights never become cleared merely through a recipe approval.

### 6.1 Deterministic current eligibility and transitive invalidation

Evaluate at one validated committed HEAD H and explicit UTC time T. T must be trusted
current local time; unknown time or detected backward clock movement blocks clearance
until explicit user time verification. Re-evaluate at use time and expiry boundaries;
a previously computed result is not a durable permission. Append-only commit sequence,
not event timestamp or root membership, orders events throughout H's ancestry.

For each exact subject/scope take its last committed Review; for each availability
subject take its last DependencyEvent. A missing review is unreviewed; a missing
availability event is unknown. A revoke/exclude/reject never counts as approval.
Removing an event from active roots cannot remove its effect from ancestry.
For EVERY scope, including rights-decision, an approve event at or before the latest
recovery commit is historical-only; a fresh appropriately authorized Review is required.
Rights-decision latest approve must also follow any reject/revoke Review of that exact
decision. Approving a decision superseded by deny/revoke never restores the old pin.

Define adverse sequence for a subject's CURRENT dependency closure as the greatest
commit sequence of: any non-available availability event; any revoke/exclude/reject
review affecting it; a correction superseding its pinned Finding; a deny/revoke or
replacement of its pinned rights decision; and any recovery commit in its ancestry.
Use 0 if none. Include transitive resource/evidence/rights dependencies. This watermark
retains adverse events even after later available/approve events; histories never reset it.

Evaluate leaves first, then Findings, then Recipes (DAG order):

1. A Dependency must have latest state available and a currently valid pinned grant
   for the requested use under section 3.1. Required capabilities must also be supported.
   Evidence-only rights/brand record references do not recurse to their own grants;
   actual resources in Dependency lists do. No hash implies resource availability.
2. A Finding must be the latest revision of its finding_id, have latest availability
   available, eligible evidence/source/method dependencies, and latest Review approve
   whose commit sequence is STRICTLY GREATER than its adverse sequence. A manual finding
   with no resource evidence needs no artificial rights document. Its original origin
   stays user-entered even after approval.
3. A Recipe must pass hard rules/protections, have eligible active Findings and all
   required/actively used dependencies, and latest Review approve strictly after the
   transitive adverse sequence. That recipe review must also follow every active
   Finding's latest approval and every required rights grant's B approval. A fresh leaf
   approval alone therefore cannot resurrect an old recipe approval. Associations derive
   eligibility from their pinned Recipe, never from library latest or historical status.

At review commit validation, evaluate prerequisites against the preceding committed
HEAD and proposed commit sequence. An approve may follow an adverse watermark; it does
not require the subject to be already approved. Recipes require their leaf approvals
committed earlier. A required dependency's expired grant blocks immediately by T even
without a stored expiry event; extending/substituting it requires new rights/dependency/
recipe pins and review. Rights restoration, availability restoration or recovery never
silently reactivates approvals. Historical records/export bytes remain unchanged.
Specifically, rights-decision approval checks issuer/evidence/scope/time/obligations and
B authority, without requiring its own existing approve. Finding approval checks latest
revision, availability, dependency clearance and roles without its own existing approve.
Recipe approval checks eligible leaves/protections without its own existing approve.
After commit, current eligibility additionally requires that newly committed approve.

Example: F approved -> recipe approved -> F review revoked: F and recipe become blocked.
F reapproved: F eligible, recipe still blocked until a later recipe review. F availability
missing -> available has the same fresh F-then-recipe review requirement. Correction F2
supersedes F1: recipes pinning F1 stay blocked; approving F2 cannot repoint them silently.
Application and final-output approvals are deliberately outside these scope literals;
R1 cannot mint them. Rights decisions need B, content/language decisions C when relevant,
and A phase acceptance; no automated routine grants phase or legal approval.

## 7. Project association and snapshots

```text
Association = {
 Common(format="ai-reel-studio/style-project-association@1"),
 association_id:ID, parent:Ref?, project_id:ID,
 creative:{format:"ai-reel-studio/creative@1", id:Text, fingerprint:Text},
 recipe:Ref, recipe_id:ID, revision_id:ID,
 dependencies:[Ref], library_recipe:Ref?, snapshot:Ref
}
```

Fingerprint must match `sha256:` plus 64 lowercase hex; it is an opaque existing core
fingerprint, NOT this recipe canonicalizer. Creative id is nonempty, exact original ID.
Recipe and snapshot refs must be identical; referenced payload/dependency closure must
be present as an immutable project-local snapshot before association commit. dependencies
must exactly equal the recipe's list, and IDs must match its payload. Optional library
ref must identify the SAME recipe hash at creation, never “latest” or a path to follow.
Parent, if present, matches association_id/project_id and is prior immutable Association.
Library changes cannot alter snapshot. Updating pins creates a new association and
requires review; this record is dependency intent, not applied layer provenance.
R1 may exercise associations only against synthetic fixture project identities/local
stores. Writing any existing project, modifying creative@1, binding real layers, and
atomic creative+sidecar operations remain separately specified/authorized at R3.

## 8. Reference graph, compatibility and gate evidence

Every Ref resolves locally by hash to exact format/id; duplicate identity with different
bytes is a conflict, not last-writer-wins. All record references form an acyclic graph;
max transitive closure 4096 records/64 MiB, depth 64, including parent/event chains.
Exceeding bounds fails closed, never prunes approved history. Future archival extension
requires its own accepted contract. Validate the entire referenced closure before
commit/approval, with bounded traversal and hash equality. No implied dependency install.

Unknown format/version/required capability: preserve bytes read-only, no apply/approve.
No automatic migration. Explicit future migration creates a new revision, preserves old
bytes and records source/target format and migration tool hash in a separately accepted
migration contract; R1 includes no migration writer. Existing creative@1 schema and its
fingerprinting are unchanged. Hash identity alone never proves resource retention,
renderer parity, security, lawful use or independent offline rebuild (G7).

Read-only G1 verification must check these shapes against the canonical vectors and
persistence protocol, including DAG approval/correction sequencing, hard-rule conflicts,
synthetic snapshot equality and bounded parsing. R1-A/B/C remain NOT EXECUTED and NOT
AUTHORIZED. Acceptance requires A and relevant B/C evidence under the existing matrix.
This R1 subset does not finalize R2 media/results, R3 transactions, R4 mixing weights,
R5 timebase/codec or R6 model contracts. Finalize them before their own phase entry.
