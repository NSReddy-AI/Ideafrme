# M5 Phase 1 file manifest

All files are new, authored independently, and confined to this workspace.
No production/development code, assets, or project data are copied.

- `creative_core/__init__.py`: public API.
- `creative_core/document.py`: versioned format, fingerprints and synthetic document factory.
- `creative_core/validation.py`: structural, semantic and filesystem validation.
- `creative_core/operations.py`: allowlisted transactions, undo/redo, approvals and named snapshots.
- `creative_core/persistence.py`: validated load/save, atomic replacement and explicit recovery.
- `tests/test_core.py`: isolated standard-library acceptance tests.
- `tests/run_isolated.py`: workspace/path checks and Python write/process/network audit guard.
- `examples/creative.json`, `examples/assets/sample.svg`: synthetic editable project and asset.
- `README.md`: usage, format and scope.
- `docs/ARCHITECTURE.md`: invariants and limitations.
- `docs/COMPATIBILITY.md`: deferred legacy integration contract.
- `docs/DEPENDENCIES.md`: dependency/license notes.
- `M5_HANDOFF.md`: results, exact commands, limitations and next gate.
- `.runtime/test-results.txt`: retained test evidence; case data removed by teardown.

No packaging/build configuration, dependency install, Git setup or engine integration is needed.

## Phase 2 additions

- `poster_render/{__init__.py,scene.py,approval.py,backend.mjs,isolation.sb}`:
  neutral SVG mapping, render/approval policy, isolated Chrome/Sharp adapters.
- `tools/{prepare_phase2.py,run_phase2.py}`: synthetic fixture preparation and isolated acceptance.
- `tests/test_render_policy.py`: 18 new pure acceptance tests (55 total with Phase 1).
- `examples/posters/creative.json`, `render-policies.json`: editable synthetic views/policies.
- `examples/posters/assets/{alpha.png,symbol.svg}`: newly authored test assets.
- `examples/posters/assets/fonts/`: TWO approved pinned font copies and OFL notices.
- `docs/FONT_SOURCE_MANIFEST.json`: font source/destination/hash/license metadata.
- `docs/PHASE2_RENDER_CONTRACT.md`, `M5_PHASE2_HANDOFF.md`: behavior/evidence/limitations.
- `.runtime/phase2-unit-results.txt`, `phase2-render-results.txt`, `phase2/`:
  retained test/probe logs, fontconfig caches; `.runtime/chrome-*` are task-local profiles.
- `output/phase2/`: three draft posters and a typography/asset calibration sheet,
  SVG/scene sources, Sharp comparisons, repeat PNGs, metrics, manifests and acceptance JSON.

Phase 1 core/schema, original examples and original test-result log remain unchanged.
