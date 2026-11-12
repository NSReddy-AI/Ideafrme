# G1 — Canonical bytes and hash vectors

Draft 2, 2026-11-10. DOCUMENTATION ONLY — VERIFICATION DOES NOT AUTHORIZE IMPLEMENTATION.
These are frozen proposed acceptance inputs, not executed R1 tests. Expected SHA-256
values were calculated with existing Python standard-library JSON/SHA-256, in memory,
without creating fixtures or running project tests. Independent implementation agreement
and R1 save/reopen evidence remain required. Applies only to style records, not creative@1.

## 1. Canonicalization contract

First strictly validate the input under G1_STYLE_RECORD_CONTRACTS.md. For canonicalizer
unit vectors below only, any bounded JSON object is accepted; these small objects are
not complete style records. Production never bypasses record-schema validation this way.

Serialize the validated payload only: UTF-8 without BOM or terminal newline; object keys
sorted by Unicode scalar sequence, recursively; array order retained; no whitespace
outside strings. No NFC/NFD normalization, trimming, locale collation or case folding.
Quote/backslash use `\"`/`\\`; U+0008/0009/000A/000C/000D use `\b\t\n\f\r` respectively;
other U+0000–001F use lowercase four-digit `\u` escapes. Solidus and other Unicode scalars
remain literal, including U+2028/U+2029. Compare decoded keys before detecting duplicates.
Booleans/null use JSON lowercase tokens. Integers use shortest ordinary base-10 lexical
form; no -0 or float tokens are accepted. Fractional parameters are canonical decimal
STRINGS; never interpret an arbitrary text string as a number. Reject noncanonical typed
decimals rather than normalizing them silently. Interactive formatting is an explicit
new draft edit before review. SHA-256 result is lowercase hex of canonical payload bytes.
This is a recipe-specific contract, not RFC 8785 compliance. Changes require new format.

## 2. Positive primitive vectors

Every fenced line below is exact canonical text, with NO newline included in the hash.
Input key ordering/outer whitespace may differ unless otherwise stated. Byte counts are
UTF-8, not character counts. Each digest is unprefixed lowercase hex.

C01 — empty object, 2 bytes:
```json
{}
```
SHA-256: `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`

C02 — input `{ "b": 2, "a": 1 }`, 13 bytes:
```json
{"a":1,"b":2}
```
SHA-256: `43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777`

C03 — Telugu and typed decimal text, input b before a, 37 bytes:
```json
{"a":"0.65","b":"తెలుగు"}
```
SHA-256: `a7993d689a43dc142323436f173c240c22adf5936a8c9e50949033fff69a4741`

C04 — U+00E9 precomposed, 13 bytes:
```json
{"text":"é"}
```
SHA-256: `42d3cbf59fdccced04e5dff14433fb52d34d58e385e9770ffd896ff517d63b92`

C05 — decoded string U+0065 U+0301, 14 bytes. Input escapes below decode first;
canonical text contains literal e followed by the combining acute, not escape syntax:
```json
{"text":"é"}
```
SHA-256: `9b53287cd41955684903378d2b1b4a3ddea9d80d67dcd026319a7c5a9a8a8b42`
Canonical hex: `7b2274657874223a2265cc81227d`. MUST differ from C04.

C06 — controls, quote, solidus and backslash, 53 bytes:
```json
{"text":"quote\" slash/ backslash\\\b\t\n\f\r\u0001"}
```
SHA-256: `e27bd3fe3f043b360d9c3fe3c1520876f2e3a8a2b6094f39947c3c85a8c66781`
Canonical hex:
`7b2274657874223a2271756f74655c2220736c6173682f206261636b736c6173685c5c5c625c745c6e5c665c725c7530303031227d`
Alternate input escapes such as `\u000a` or `\/` produce the same decoded value/hash.

C07 — input `{"\ud800\udc00":2,"\ue000":1}`. Decoded keys U+E000 then U+10000,
18 bytes; scalar ordering deliberately differs from UTF-16 code-unit sorting.
Canonical hex: `7b22ee8080223a312c22f0908080223a327d`.
SHA-256: `8706b5798a29d65739b3d1bbb1d009f87d005c71c8130c5353c4990c15ddfec8`

C08 — array order preserved and JSON literals, 43 bytes:
```json
{"array":[3,1,2],"flags":[true,false,null]}
```
SHA-256: `10299df0cbf679bbfb89d73f91b996a4dd80f6498d9580e72f64856b4bbe5f5e`

C09 — signed 64-bit endpoints, 54 bytes:
```json
{"max":9223372036854775807,"min":-9223372036854775808}
```
SHA-256: `161a1dcda7bae00f28f0ba32675f218fd4977065d2aa0439cf451c6d066dbbfb`
Readers whose native number type loses these integers must use an exact parser or refuse.

C10 — canonical typed decimal fragment, 31 bytes:
```json
{"unit":"ratio","value":"0.65"}
```
SHA-256: `235bc7e06d2b22310a32a8068068304506cf569d4a34ea35820d900b94ef62de`

C11 — canonical negative decimal fragment, 28 bytes (primitive only; property range
validation remains separate):
```json
{"unit":"px","value":"-1.5"}
```
SHA-256: `98acada3eee348f381eead75b59fe9cda14f0790f890b316c0ffaf6880655567`

C12 — recursive keys and English/Telugu, 53 bytes:
```json
{"a":[],"z":{"a":"తెలుగు","b":"English"}}
```
SHA-256: `7b499418b904ed01ae79b075f0c3eb71b91f26c1cf149681f847631ca8bbe665`

## 3. Complete record vector

C13 — complete Dependency payload, exact canonical line below, 480 bytes. This is a
synthetic schema-valid pin to empty bytes, NOT a valid installed font or cleared license.
Draft schema/hash validation passes; availability/rights/resource-use eligibility does
not. No actual font is created, read or loaded. Null license/rights remains unknown.

```json
{"content_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","created_at":"2026-11-10T00:00:00Z","created_by":"00000000-0000-4000-8000-000000000002","dependency_id":"00000000-0000-4000-8000-000000000003","format":"ai-reel-studio/style-dependency@1","kind":"font","license_expression":null,"name":"Synthetic font pin","notice_sha256":null,"parameters":[],"record_id":"00000000-0000-4000-8000-000000000001","required":true,"rights_record":null,"version":"1"}
```

SHA-256: `9ebc1f671105fecd2260f9510c4e592eeda94ebb1ec3e84f795e18b2ee3dad5d`.
Envelope is exactly `{payload:<above object>,sha256:<above digest>}` with quoted JSON
keys/strings; envelope field ordering cannot affect payload identity. Changing version
or content_sha256 under the old envelope digest MUST fail hash validation. The payload
hash is distinct from content_sha256: record metadata versus pinned resource bytes.

## 4. Rejection and equivalence vectors

Each invalid case has expected outcome REJECT with NO accepted digest/record/approval.
Hashing invalid raw bytes for diagnostics is not a valid record fingerprint.

- N01 `{"a":1,"a":2}` and `{"a":1,"\u0061":2}`: syntax, duplicate decoded key.
- N02 `{"x":"\ud800"}` / lone low surrogate / malformed UTF-8: encoding/syntax.
  Proper surrogate pair in C07 is accepted and becomes one scalar.
- N03 `{"x":NaN}`, Infinity, -Infinity: syntax; never strings converted to numbers.
- N04 numeric tokens `1.0`, `1e0`, `-0`, `01`, `+1`: syntax/schema, no coercion.
- N05 integers 9223372036854775808 or -9223372036854775809: schema range.
- N06 typed Decimal strings `"00"`, `"01"`, `"-0"`, `"-0.0"`, `"1.0"`, `"0.650"`,
  `"+1"`, `"1e-2"`, `".5"`, `"1."`, `" 0.65"`: schema; no rounding/normalizing.
  The same strings in unrestricted Text are text, not rejected as numbers.
- N07 BOM, trailing garbage, raw unescaped C0 control, executable serialization: syntax.
  Ordinary leading/trailing JSON whitespace is allowed but excluded from canonical bytes.
- N08 envelope >1 MiB, nesting 33, 501 total members or 4097 total array items: limit.
- N09 unknown format/field, missing nullable field, unit mismatch, duplicate properties,
  out-of-range layout margin `"0.46"`: schema. Retain original, no partial interpretation.
- N10 mismatched hash/record_id/format, missing Ref, cycle, excessive graph closure:
  hash/reference/limit; no approval. Unknown required capability blocks eligibility.
- N11 wrong snapshot pin/library substitution or stale expected HEAD: reference/conflict.
- N12 unreviewed active finding/rights unknown/revoked dependency: record may remain a
  valid draft; approval/application blocked as dependency/authority/protection. Do not
  misreport every eligibility failure as malformed JSON.

E01: key reorder, allowed whitespace, alternate valid escapes and input terminal newline
must not change canonical hash. E02: array reorder, NFC versus NFD, changed typed value,
changed dependency hash or format MUST change payload identity; no approval carries over.
E03: adding a separate review event must not change recipe payload/hash. Changing its
payload under an old envelope hash must fail. E04: decimal `"0"` canonical; negative
fraction `"-0.5"` canonical where property range allows. Text wording is never normalized.

## 5. Review and future test evidence

Read-only review must check every literal/hex/digest and distinguish primitive vectors
from complete-record fixtures. Once separately authorized, R1-A builds complete valid
Recipe/Brand/Finding/Review/Association/Dependency fixtures from the closed grammar,
records their full payloads and frozen hashes BEFORE save/reopen testing, then exercises
all rejection/equivalence cases. No implementation may claim record conformance solely
from these primitive hashes. R1-C additionally consumes all persistence fault cases.
Approval authority A; B/C where brand/rights/content semantics apply. No tests executed
or R1 approval implied by this document.

### Explicit implementation acceptance requirements

R1-A must demonstrate byte/hash agreement in TWO independently written serializers in
different languages (for example Python and existing JavaScript, with exact integer
handling). Both must consume the same frozen vectors, including C07 scalar key ordering,
C09 signed-64 endpoints and N01 duplicate decoded keys. Raw SHA-256 agreement alone is
not serializer/parser agreement. No new installation is authorized by this requirement.
The existing 13 vector checks and the later independent serializer check were Python
documentation checks only; cross-language portability remains NOT VERIFIED.

Add synthetic lifecycle fixtures to R1-B/C after implementation authorization: manual
Finding approval/revocation/reapproval; missing->available; correction invalidating old
recipe; rights grant/deny/revoke/expiry/out-of-scope/unknown authority; fresh rights review
after recovery; and stale recovery generation/PREVIOUS preservation at every Q state.
Expected outcomes follow record-contract section 6.1 and persistence sections 4–6.
All failures block affected current eligibility; historical payloads remain unchanged.
These scenarios are specified, not executed. No real persistence fault, concurrent
writer, filesystem durability or power-loss behavior has been verified by drafting.
