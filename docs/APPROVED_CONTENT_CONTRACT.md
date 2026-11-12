# approved-content@1 — approved reel words reused on posters (M6 step 6)

Status: implemented in M6 (`app/approved_content.py`, `app/content_links.py`, routes in `app/creative.py`).
Neither the M4 engine nor M5's formats were changed to build it.

## Why

M4 never renders words a human has not approved: plan approval for speaker reels, script approval for narrated reels.
Posters must keep the same promise. When a poster reuses a hook, a verbatim quote or a number card, these must hold:
- it shows exactly the approved words;
- anyone can check later that they are still approved.

## Where the approval comes from (read-only)

| Approval | Required, or no content is given | Items |
|---|---|---|
| `plan` | `plan.approved`; `plan_hash(plan) == plan.approved_hash == project.plan_hash`; project.json hook lines and headline equal the chosen hook (the render gate in `engine/adapter.py`) | `hook.line1-3` (kind `quote` and `verbatim: true` when wrapped in “ ”), `headline.N`, `tag`, `card.N` (number — label, from the speaker's own words), `post.intro` |
| `narration` | `narration.approved`; `fingerprint(lines) == approved_hash == project.narration_hash` | `script.N` |
| `project` | project.json `approved: true` with a hook and no plan (hand-approved baseline, e.g. reel_002). This approval has no fingerprint; the document says so. | hook lines, headline, tag |

If an approval is missing, stale or was edited after approval, derivation fails (`ApprovalError`) instead of guessing.

## Document

```json
{"format": "ideaframe-approved-content@1",
 "source": {"kind": "m4-reel", "project": "<folder>", "brand": "<id>", "style": "<id>"},
 "approvals": [{"type": "plan", "hash": "<approved_hash>", "hook_choice": "A", "approved_at": "...", "checked": true}],
 "items": [{"id": "hook.line2", "kind": "quote", "text": "“…”", "language": "te", "verbatim": true,
            "origin": {"approval": "plan", "field": "hook.line2"}, "sha256": "<sha256 of text>"}],
 "fingerprint": "<sha256 of the canonical document above>"}
```

## Placing approved words on a poster

`POST /api/creative/approved/insert {project_id, expected_revision, reel, item_id, expected_fingerprint}`:
1. derives the reel's content again and refuses a stale fingerprint;
2. adds a text layer through M5's own actions and sets its text to exactly the approved words;
3. places it under the existing text when it fits;
4. records a link in M6's own store, outside M5's session: `m5/.runtime/studio-ui/m6-content-links/<poster>.json`.

The link records the layer, the M5 content id, the reel, the item id, the item SHA-256, the source fingerprint and the approval types.

M5 posters keep these words as `editorial` content. M5's manual Studio does not yet accept `claim`/`quote` content.
Provenance therefore lives in the M6 link, not in the creative@1 document.

## Checking

Poster QA (`POST /api/creative/qa`) adds an `approved_text` error for a linked layer in three cases:
- its text differs from the approved words;
- the item changed or disappeared in the reel;
- the reel's approval is no longer valid.

`GET /api/creative/approved/links/<poster>` lists the same statuses.

## Open for Codex / the owner

- If M5 later accepts `claim`/`quote` content with a `source_ref`, the link can move into the document. That needs Codex's decision.
- Export does not block on an `approved_text` error. Like all poster QA it reports; the owner may decide to make it blocking.
