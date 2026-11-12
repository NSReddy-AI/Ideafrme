# R2 -> manual R1 bridge — compatibility proposal

Draft 1, 2026-11-10. PROPOSED, not implemented/approved. Preserve accepted R1 code,
schemas, stores, evidence, creative@1 and conditional acceptance. References:
[new report contract](R2_REPORT_CONTRACT_PROPOSAL.md), [vectors](R2_CANONICAL_VECTOR_SPEC.md),
[readiness roadmap](R2_IMPLEMENTATION_READINESS_ROADMAP.md), existing G1 contracts.

## 1. Honest boundary

R2 measures/infers; the user deliberately chooses a new abstract style intention in R1.
Its R1 origin is user-entered, source/method/region remain null, and original automated
origin/region/confidence/correction history remain available in the pinned report.
No direct measured/inferred import, validators patched at runtime, hidden creative
layers, copied OCR text, brand assets or automatic Apply. R2 approval never grants R1
Finding/Recipe approval. This bridge creates a manual Recipe/library revision only;
R1 project associations remain synthetic-only. Real project integration is not R2.

## 2. Exact user request and preconditions

Proposed ephemeral request (not an added accepted R1 format):

```text
{
 bridge_id:ID, actor:ID, confirmed:boolean,
 job_head:CRef, index_ref:CRef,
 expected_r1_head:G1Ref?, parent_recipe:G1Ref?,
 selections:[{observation_id:H, r1_property:Key, chosen_value:G1Value, reason:Text}],
 name:Text
}
```

Closed fields; <=8 selections, unique r1_property, ascending property order. Each
observation must exist in the exact Index, be currently available and approved after
its last correction/adverse event, and belong to a complete, currently approved report.
job_head must equal current generation. Word IDs, excluded/rejected/revoked subjects,
partial results and unsupported schemas cannot be selected. Every chosen_value is
manually confirmed and validated against the UNCHANGED R1 catalog. Reason1..256 scalars;
name1..256. Actor confirmation is explicit, not inferred from selection or report review.
The request is a human decision, not worker output; workers cannot construct it as authority.

Current source/profile/normalized hashes, report pages/review lineage and relevant
rights/brand constraints must be available and valid. Missing or project-restricted
clearance that R1 cannot evaluate without context blocks approval; never widen rights.
If expected_r1_head or parent pins changed, refuse and regenerate a draft selection;
no auto-merge or repointing. Parent is an exact existing Recipe Ref, never latest.

## 3. Mapping catalogue

| Approved R2 evidence | Permitted manual R1 intention | Mandatory interpretation |
|---|---|---|
| palette.swatch | palette.primary/secondary/accent/background color | User chooses semantic role and confirms RGBA; no inference of brand authority |
| text.height or text.size_ratio | heading/body size or line_height | User enters accepted px/ratio; raster glyph height is NOT nominal font size |
| measured line gap/layout margin | accepted line_height/layout.margin | User chooses units/value within R1 limits; geometry is evidence, not direct conversion |
| layout alignment/hierarchy observations | layout.alignment | Explicit start/center/end choice; no hidden grid or protected-layer changes |
| lighting/texture interpretation | description.lighting/texture text | User-written paraphrase, uncertainty visible, no reconstructed editing process claim |

All other metrics remain report-only in this profile. Exact font choice must pin an
independently approved local font dependency; OCR cannot identify it. No automatic font,
tracking, logo/content/portrait replacement or OCR wording transfer. New R1 properties
would require a separately authorized schema proposal and are not invented by bridge code.

## 4. Provenance using accepted structures

For each bridge retain immutable resource bytes: original PNG, exact analysis Index
and its page closure, profile, and a canonical human-choice receipt containing the
request, prior generation, selected review refs, effective corrected values and resulting
R1 record refs. Receipt is a supervisor-owned audit resource, not a new accepted R1
schema or a hidden scene. Its own hash is never embedded in itself.

Use accepted Dependency records with kind reference for source, Index and choice receipt;
kind extractor for profile. content_sha256 pins canonical resource bytes, not a new-format
Ref. parameters are sorted G1 key/value entries naming analysis-index/profile/source/
observation hashes and effective reviewed choice; every string obeys G1 bounds.
No XML/JSON scene or executable data hidden in parameters. Per-selection provenance
Dependency can pin a precommit choice receipt with no resulting R1 refs; a separate
postcommit outcome receipt links returned refs, avoiding a self-hash cycle.

The precommit receipt includes exact job head and selected observation/review refs,
chosen property/value and actor confirmation. Each new Finding's evidence lists that
selection's receipt, report/source/profile Dependency refs. At most4+8=12 resource
dependencies per request, below R1's32 limit, but the global500-member and1MiB bounds
can be tighter: compute aggregate shape/size BEFORE commit and split/refuse explicitly.
One resource's RightsDecision pins that resource's exact hash; source rights do not
automatically clear a derived OCR/report/receipt. B must assess the permitted use.
Unknown/expired/revoked/unsupported obligations block affected R1 approval.

## 5. Public API capability check

Read accepted `style_recipes/manual.py`, `schema.py`, `state.py`, `store.py`:

- `finding()` can create user-entered values and accepted evidence refs; no measured
  Finding import. `recipe()` creates a new Recipe from chosen Findings and Dependencies.
- `edited()` now preserves unselected properties, creates explicit corrections and a
  new revision. For complex multi-property selection, construct one closed new Recipe
  with accepted public factories/validation rather than sequential edits that lose pins.
- `review()` and `availability()` create accepted append-only events; `Store.commit()`
  takes expected HEAD and actor confirmation. Every availability/review/rights-decision
  action admits exactly one such event per commit: do not batch them as one atomic action.
- Draft save can commit new accepted Findings/Recipe together. Existing Ref and catalogue
  validation prevents embedding new R2 types. Generic `write` can express exact new
  revisions/removal; no dedicated property-removal convenience API is assumed.
- `association()` is synthetic-only and NOT used to attach this analysis to real projects.

Concrete compatibility gaps, not silently repaired:

1. R1 rights evaluation hardcodes manual-style-authoring. It does not authorize the
   separate reference-analysis use. R2 must validate that permission in its own gate;
   a licence permitting only manual use does not permit automated decoding/OCR.
2. R1 reads only its own committed dependency events. It does NOT follow R2 review
   revocations or poll an analysis authority. A raw R1 CLI may still show historical
   Recipe eligibility until explicit stale/revoked events are committed there.
3. Project-limited resource grants cannot be approved by generic Finding/Recipe commands
   without context; leave blocked, do not substitute project_ids=null.
4. There is no cross-store transaction, automatic analysis subscription or authenticated
   multi-user approval. Those guarantees cannot be promised without separate changes.

Therefore current-R2 validity must always be checked by the R2 bridge supervisor AND
R1 validity separately. Any later consumer claiming R2-backed current eligibility needs
both authorities. The accepted standalone R1 CLI is not redefined as that consumer.
Global automatic revocation enforcement through unchanged R1 alone is UNSUPPORTED.
If that is mandatory, Gate B remains BLOCKED pending a separately reviewed extension
or scope decision. No R1 extension is authorized here.

## 6. Publication, failures and revocation

1. Read/validate R2 job/report/reviews/resources and requested selection, freeze expected
   R1 HEAD. Write precommit choice resources into a new authorized staging location.
2. Explicit user/B confirmations create necessary rights and availability events through
   their individual R1 commits. They are preparatory metadata, not a cleared Recipe.
   Refresh expected generation after each deliberate event; no stale-snapshot overwrite.
3. Recheck R2 generation/rights and R1 expected HEAD immediately before saving selected
   manual Findings/Recipe. R2 bridge serializes its own review/invalidation operations
   while preparing this save. It cannot lock remote rights/time itself; expiry is checked
   at use and no cross-store atomicity is claimed.
4. Commit one R1 draft save. Only return success after R1 durability succeeds, then
   write an outcome receipt. New Finding and Recipe approval require fresh explicit
   reviews, not bridge/report approval. No automatic approve call.

Before final R1 save failure: prior Recipe/HEAD persists except explicitly completed
preparatory dependency events. On uncertain R1 publication, inspect/reopen by exact
refs; do not blindly retry and duplicate revisions. An outcome-receipt write failure
does not roll back a durable draft: report incomplete handoff, preserve refs, withhold
bridge completion. Any source/report-generation mismatch aborts before save or blocks
the just-created draft pending revalidation; never return an approved/cleared result.

On R2 adverse review/resource event, immediately block bridge/analysis eligibility,
then enumerate known R1 receipt dependencies and commit explicit stale/revoked events.
If propagation fails, report it and keep R2 consumers blocked. Do not claim that an
unmodified standalone R1 consumer is synchronously invalidated. Fresh R1 reviews follow
successful propagation/restoration; no rewriting old Recipe payloads or review events.

## 7. Required proof and status

Contract-only future tests: explicit selection vs automatic output, wrong provenance,
stale generations, aggregate limits, multiple event commits, failed publication/receipt,
revocation between stores, context-restricted rights, unchanged R1 hashes and retained
original observations. Reproduce rejected native measured imports. No tests run here.
Status: compatible manual-draft route PROPOSED; automatic cross-store enforcement is
not expressible by existing APIs. Approval of this bounded limitation is required before
calling Gate B ready. No R1 code, schema, store or evidence has been changed.
