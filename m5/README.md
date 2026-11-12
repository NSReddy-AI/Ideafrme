# M5 Creative Document Core — Phase 1

Phase 2 now adds an isolated poster prototype. See `M5_PHASE2_HANDOFF.md` and
`docs/PHASE2_RENDER_CONTRACT.md`; the Phase 1 core and schema remain unchanged.
Use `tools/run_phase2.py` only through the documented mandatory OS-isolated workflow.
Examples under `output/phase2/` are drafts awaiting human review.

An independent Python standard-library package. No installation/build step, renderer,
browser UI, model calls, paid services, legacy integration or Git setup is included.
All source is newly authored. The example uses synthetic content and artwork only.

## Tests

From `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`:

```sh
TMPDIR="$PWD/.runtime" TMP="$PWD/.runtime" TEMP="$PWD/.runtime" XDG_CACHE_HOME="$PWD/.runtime" PYTHONDONTWRITEBYTECODE=1 python3 -B tests/run_isolated.py > .runtime/test-results.txt 2>&1
```

`.runtime` must already exist as a real directory. The runner refuses a different or
symlinked workspace, uses only local temporary directories, disables bytecode writes,
and audits Python write/process/network events. Test teardown removes synthetic case
directories. The retained results log stays in `.runtime`.

## API (illustrative; no production paths)

```python
from creative_core import new_document, validate, apply, undo, redo, approve, snapshot, save, load

doc = new_document("my-project")
validate(doc, project_root)
doc = apply(doc, {"op": "move", "element_id": "title", "x": 100, "y": 120}, project_root)
doc = undo(doc, project_root)
doc = redo(doc, project_root)
# Only after a human has actually reviewed the document:
doc = approve(doc, "reviewer-name", project_root)
doc = snapshot(doc, "Reviewed layout", project_root)
save(doc, project_root)
assert load(project_root) == doc
```

The API returns deep-copied documents for changes; it never silently mutates its input.
The caller must supply an existing trusted project root and store the returned document.
Do not point this package at production or M4 development during this phase.

## Format v1

`format = ai-reel-studio/creative@1`, integer `schema_version = 1`; no migration.
The exact executable format contract is in `creative_core/validation.py`.
Unknown fields and versions are rejected, including unknown extension fields.

- `id`, monotonic `revision`, `project` name/output kinds and `languages` (te/en).
- `views`: unique IDs, width/height and language.
- `assets`: unique IDs, normalized relative path, kind and optional SHA-256.
- `brand`: null or ID plus a local brand-asset reference.
- `content`: unique IDs, text, language, editorial/claim/quote kind; source asset
  mandatory for claims/quotes. Source fidelity is not factual verification.
- `elements`: unique IDs, text/shape/vector/image/logo/video type, view reference,
  geometry, allowlisted style, content or asset binding as appropriate.
- `approvals`: reviewer label, ID and whole-core fingerprint; assets must be pinned.
- `versions`: named immutable core snapshots, fingerprints and approval copies.
- `history`: reversible before/after core transactions and an undo/redo cursor.

IDs are unique within their typed namespace; references identify that namespace.
All five operations are allowlisted: add, move, restyle, edit_text, remove.
Text edits update the shared bound editorial content; claims/quotes cannot be edited
through the Phase 1 API. Removing an element leaves shared content/assets intact.
Styles currently support fill, stroke, stroke_width, font_size, opacity, rotation,
font_asset_id, shape and vector path. No renderer interprets them in this phase.

See `docs/ARCHITECTURE.md`, `docs/COMPATIBILITY.md`, `docs/DEPENDENCIES.md`, and
`M5_HANDOFF.md` for guarantees, limits and approval gates.
