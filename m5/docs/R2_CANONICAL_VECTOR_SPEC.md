# R2 canonical vector specification

2026-11-10. PROPOSED CONTRACT VECTORS, not executable schemas, worker fixtures or
implementation acceptance. Read [report contract](R2_REPORT_CONTRACT_PROPOSAL.md) and
[bridge](R2_R1_BRIDGE_CONTRACT_PROPOSAL.md). Accepted R1 vectors/code/evidence unchanged.

## 1. Authorized calculation and meaning

Ten canonical payloads below were calculated in memory using existing Python
standard-library JSON/SHA-256, then independently serialized/hashed by existing
`node tools/r1_canonical.mjs` using stdin/stdout only. All ten digests and byte counts
agreed, exit0; no file, image, dependency or test evidence was created/modified.
This establishes canonical arithmetic/literal consistency, NOT R2 schema validation,
an actual decoded image, security, model identity, rights clearance or persistence.

Canonical fences contain exact UTF-8 text, NO terminal newline in digest. A stored
envelope adds payload/sha256 and its own bounded encoding; hashes below exclude it.
Resource hashes of repeated0/1/2 are SYNTHETIC placeholders, not acquired artifacts.
V01/V03 are ID-preimage primitive vectors; V02/V04 are well-shaped content pages;
V05 is an illustrative partial index conforming to the proposed shape (never approval/bridge eligible); V06 is an initial
unknown-availability Job. Validation of resource availability/closure remains blocked.
V07–10 are canonical primitive cases, not standalone R2 records.

The exact field grammar, slot, page ordering and pixel-only Region proposal must first
be accepted. Never feed these examples into accepted R1 as new formats.

## 2. Positive vectors

### V01

Observation identity preimage; its digest is the V02 observation_id.

```json
{"metric":"palette.swatch","profile_sha256":"1111111111111111111111111111111111111111111111111111111111111111","region":{"height":8,"width":8,"x":0,"y":0},"slot":0,"source_sha256":"0000000000000000000000000000000000000000000000000000000000000000"}
```

UTF-8 bytes: 247. SHA-256: `4f2672c06114ea5c3f3a1298de217b6afd9d698c6005596f175e6bd1c343a96d`.

### V02

One measured palette observation; evidence/source/profile hashes are synthetic.

```json
{"format":"ai-reel-studio/image-observation-page@1","observations":[{"confidence":"not-assessed","confidence_reason":"Synthetic contract vector; no analysis or clearance claimed.","evidence_refs":[{"kind":"normalized","sha256":"2222222222222222222222222222222222222222222222222222222222222222"},{"kind":"profile","sha256":"1111111111111111111111111111111111111111111111111111111111111111"},{"kind":"source","sha256":"0000000000000000000000000000000000000000000000000000000000000000"}],"limitations":[],"method_sha256":"1111111111111111111111111111111111111111111111111111111111111111","metric":"palette.swatch","observation_id":"4f2672c06114ea5c3f3a1298de217b6afd9d698c6005596f175e6bd1c343a96d","origin":"measured","region":{"height":8,"width":8,"x":0,"y":0},"slot":0,"value":{"kind":"color","rgba":"#3366ffff"}}],"page_no":1,"profile_sha256":"1111111111111111111111111111111111111111111111111111111111111111","source_sha256":"0000000000000000000000000000000000000000000000000000000000000000"}
```

UTF-8 bytes: 993. SHA-256: `c58e429249547c711ff7cfd8cbba0dcab4471239dfac6e7d4ebf0322a595373d`.

### V03

Word identity preimage, reading_order1; digest is the V04 word observation_id.

```json
{"metric":"ocr.word","profile_sha256":"1111111111111111111111111111111111111111111111111111111111111111","reading_order":1,"region":{"height":8,"width":8,"x":0,"y":0},"slot":0,"source_sha256":"0000000000000000000000000000000000000000000000000000000000000000"}
```

UTF-8 bytes: 259. SHA-256: `c7c63edbd9783406a53e1f0a603cd25eca8f3248ce5a6721e3bac8b6f3cfd35d`.

### V04

Telugu recognized text; raw confidence is a string score, not approval/probability.

```json
{"format":"ai-reel-studio/image-ocr-page@1","language_profile":"tel","page_no":1,"profile_sha256":"1111111111111111111111111111111111111111111111111111111111111111","source_sha256":"0000000000000000000000000000000000000000000000000000000000000000","words":[{"observation_id":"c7c63edbd9783406a53e1f0a603cd25eca8f3248ce5a6721e3bac8b6f3cfd35d","raw_confidence":"87.5","reading_order":1,"region":{"height":8,"width":8,"x":0,"y":0},"status":"recognized","text":"తెలుగు"}]}
```

UTF-8 bytes: 480. SHA-256: `9d7da1b191c7bb9ef5d2622a9d69c8641add5099d7fd24c476b5c86977cd3cee`.

### V05

Partial Index linking V02/V04 in separate ordered page lists; covered scalar count exact.

```json
{"analysis":{"height":8,"width":8},"color_policy":"assumed-srgb","coverage":{"observations":1,"ocr_scalars":6,"status":"partial","words":1},"display":{"alpha_present":true,"height":8,"orientation":1,"width":8},"format":"ai-reel-studio/image-analysis-index@1","limitations":["Synthetic partial result; no source bytes acquired."],"normalized_sha256":"2222222222222222222222222222222222222222222222222222222222222222","observation_pages":[{"format":"ai-reel-studio/image-observation-page@1","sha256":"c58e429249547c711ff7cfd8cbba0dcab4471239dfac6e7d4ebf0322a595373d"}],"ocr_pages":[{"format":"ai-reel-studio/image-ocr-page@1","sha256":"9d7da1b191c7bb9ef5d2622a9d69c8641add5099d7fd24c476b5c86977cd3cee"}],"profile_sha256":"1111111111111111111111111111111111111111111111111111111111111111","raw":{"bit_depth":8,"color_type":6,"height":8,"width":8},"source_sha256":"0000000000000000000000000000000000000000000000000000000000000000"}
```

UTF-8 bytes: 927. SHA-256: `a4e1c33032c2fec151e173c39572ec703ed241b2122c3d149e0dc61c1f847715`.

### V06

Selected Job revision1; no result/review/resource evidence, unknown availability.

```json
{"availability":"unknown","created_at":"2026-11-10T00:00:00Z","created_by":"00000000-0000-4000-8000-000000000003","failure":null,"format":"ai-reel-studio/image-analysis-job@1","job_id":"00000000-0000-4000-8000-000000000002","operation":"progress","previous_job":null,"profile_sha256":"1111111111111111111111111111111111111111111111111111111111111111","record_id":"00000000-0000-4000-8000-000000000001","recovery_from":null,"resource_evidence_sha256":null,"result_ref":null,"review_ref":null,"revision":1,"source_sha256":"0000000000000000000000000000000000000000000000000000000000000000","state":"selected"}
```

UTF-8 bytes: 606. SHA-256: `7f292addf9bdd62e637afb10abc5ab09681effead5e7c9e1fa78312c31c8a785`.

### V07

Decoded keys U+E000 and U+10000; Unicode-scalar ordering, not UTF-16 ordering.

```json
{"":1,"𐀀":2}
```

UTF-8 bytes: 18. SHA-256: `8706b5798a29d65739b3d1bbb1d009f87d005c71c8130c5353c4990c15ddfec8`.

### V08

Precomposed U+00E9; do not normalize into another string before hashing.

```json
{"text":"é"}
```

UTF-8 bytes: 13. SHA-256: `42d3cbf59fdccced04e5dff14433fb52d34d58e385e9770ffd896ff517d63b92`.

### V09

U+0065 U+0301; intentionally different from V08.

```json
{"text":"é"}
```

UTF-8 bytes: 14. SHA-256: `9b53287cd41955684903378d2b1b4a3ddea9d80d67dcd026319a7c5a9a8a8b42`.

### V10

Exact signed64 endpoints; JavaScript verifier preserves BigInt values.

```json
{"max":9223372036854775807,"min":-9223372036854775808}
```

UTF-8 bytes: 54. SHA-256: `161a1dcda7bae00f28f0ba32675f218fd4977065d2aa0439cf451c6d066dbbfb`.

## 3. Equivalence and rounding vectors

- Reorder keys/allow JSON whitespace/alternate valid escapes: canonical bytes unchanged.
- Arrays are ordered: page order, reading_order or evidence order changes are NOT
  normalized away; malformed semantic order is rejected before accepting a report.
- Observation slot0 versus1 changes ID even if Region/RGB coincide. Nonpalette slot1
  is schema-invalid; two palette records sharing the same metric/region/slot are rejected.
- Change source/profile/region/slot or word reading_order: new deterministic ID required.
  Reusing an old ID fails semantic validation. Re-paginating identical ordered contents
  changes page/index hashes but not observation/word IDs; no approval transfer implied.
- Compute1.2345665 -> "1.234566";1.2345675 -> "1.234568";0.0000005 -> "0";
  -0.0000005 -> "0". These are declared half-even extraction rounding outcomes, not
  input-loader normalization. Noncanonical raw "-0", "1.0", "01", exponent decimals
  are rejected for typed D. Text "1.0" remains literal text where text is permitted.
- Quote/backslash/C0 escape behavior, invalid Unicode, no BOM, number grammar and
  recursive key ordering remain G1-compatible. No NFC/NFD conversion in stored words.
  Evaluation may normalize copies only under the independently frozen scoring policy.

## 4. Negative/semantic vectors and expected outcomes

Each rejection has no accepted record/approval. Diagnostic hashing of invalid bytes
does not make them valid. An absent resource may leave well-shaped content inspectable
but unavailable; do not confuse eligibility failure with malformed JSON.

| Case | Mutation/input | Expected validation behavior |
|---|---|---|
| N01 | Duplicate "metric" key, or key and equivalent Unicode escape | Reject duplicate decoded key before object interpretation |
| N02 | Lone surrogate, malformed UTF-8, BOM, raw nonfinite/fraction/exponent/-0 number | Reject encoding/syntax/numeric grammar; no normalization |
| N03 | Unknown format/field, omitted nullable field, bool where Int expected | Reject exact shape/type/version |
| N04 | Region negative/empty/outside display; redundant normalized fields added | Reject bounds/unknown fields |
| N05 | V02 ID unchanged after changing slot/profile/Region | Reject ID/preimage mismatch |
| N06 | Duplicate observation identity/key or word reading_order/ID | Reject ambiguity, never choose latest by sorting |
| N07 | V05 pages swapped/noncontiguous/page source mismatch/count mismatch | Reject page closure/order/count binding |
| N08 |33 pages,513 words,65 observations, oversized strings/member depth/byte cap | Reject before publication; no successful truncation |
| N09 | OCR raw score101, unsupported language/status; guessed text called recognized | Reject score/enums; fabricated provenance fails review |
| N10 | Corrected Review with null value, approval with nonnull correction, Word corrected to color | Reject decision/value contract |
| N11 | Two Reviews use same base generation/previous event; wrong job/page/observation | Reject stale generation/subject mismatch; no timestamp/UUID arbitration |
| N12 | Worker supplies approved status or Review/store authority | Reject unknown content field/untrusted event producer |
| N13 | Partial Index or revoked/unreviewed subject chosen for bridge | Block eligibility; retain draft bytes, no R1 save/approval |
| N14 | Missing/expired/revoked/out-of-scope rights, changed source/profile | Block affected availability/eligibility; record invalidation without rewriting history |
| N15 | New-format CRef placed into an R1 Ref field | R1 rejects; bridge uses accepted Dependency content hashes |
| N16 | Interrupted publication, orphan Review or unknown Job HEAD | No approval visibility; explicit recovery, no orphan promotion |
| N17 | Revalidated resources after adverse event/recovery | Prior approval stays historical; fresh subject then whole-report reviews required |
| N18 | Native measured Finding automatically imported into R1 | Reject unchanged R1 manual-only validator; no relabeling |
| N19 | Corrected value approved, later excluded/revoked then reapproved | Effective correction retained; new review required, original evidence unchanged |
| N20 | Reviewed source absent but report hashes available | Inspect historical identity only; no resource reconstruction/rights inference from hash |

## 5. Future conformance proof

After separate approval, two independent readers must implement exact schema/ID/
pagination/review-chain semantics and these valid/invalid cases in fresh isolated
evidence. Freeze complete Review/Job transition fixtures, resource/rights stubs and all
new metric/profile vectors BEFORE evaluating them. Hash arithmetic here is not that
proof. Canonical record-level rejection, stale reviews, restart/recovery and bridge
failure tests remain UNVERIFIED and must not inherit R1's prior test pass.

