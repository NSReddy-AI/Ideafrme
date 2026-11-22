# Revision provenance

## Active base

The active migration base is the complete 30-commit history from `IDEAFRAME_M6_dev`, ending at `e6a592c0e609609253a95820566982d5799a0203`. A verified Git bundle records the complete history.

The current working changes were preserved separately and restored into the isolated migration checkout:

- `app/web/package-lock.json`
- `app/web/package.json`
- `app/web/src/App.tsx`
- `app/web/src/index.css`
- `app/web/src/ui.tsx`
- `tools/m6_a11y_audit.js`

`app/web/src/Create.tsx.bak` is retained in preservation but is not treated as active source. Two untracked projects are also retained in preservation and classified under `DATA_POLICY.md`.

## Earlier modules

M1–M4 are carried forward through the M6 seed. `M6_WORKSPACE.md` records that the M4 live source matched production at copy time apart from backup/control files. The M2, M3 and M4 folders and manifests remain independent evidence and are not modified.

## Module 5

Three M5 identities are retained:

1. The frozen checkpoint `AI Studio_M5_checkpoint_2026-11-12_064759`.
2. The byte-verified copy integrated under `m5/` during M6.
3. The later live `Codex/AI Studio` source, whose status manifest is dated 13 November 2026 and says `IN_PROGRESS`.

The live source was first overlaid in a disposable integration trial. Thirty M6/M7 compatibility tests, all eight web test files and 11 official M5 sprint checks passed. Its reviewed source was then overlaid into the isolated migration checkout while runtime data, generated output, handover packages and duplicate checkpoint packages remained outside the active source tree.

## Verification performed

- Git bundle verification: complete history.
- Preliminary secret-pattern screening: no findings in the M6/M7 history/current text or latest M5 source text.
- Frontend: TypeScript and Vite build passed.
- Web logic: eight test files passed.
- Combined M6/M7 validation: 49 tests passed with local-loopback access for route tests.
- Latest M5 validation: 11 official sprint checks passed.
