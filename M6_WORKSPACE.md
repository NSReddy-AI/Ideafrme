# M6 workspace provenance

Created 12 Nov 2026 (step 1 of the M6 plan, approved by the owner).

## M4 source
- **Copied from:** `Reel Studio_dev`. Its live source was identical to production `Reel Studio` at copy time
  (a static `diff -rq` showed differences only in backup-suffixed files, `.claude` and `CHECKSUMS.sha256`).
- **Included:** `app/` (including `web/node_modules` and `web/dist`, so the UI builds offline), `engine/` (including models and fonts),
  `brands/`, `platforms/`, `styles/`, `examples/`, `docs/`, `tools/`, `tests/` (scripts, baselines, truth files, clips),
  the launcher and scripts, `providers.json`, and the reel_002 project folder.
- **Excluded:**
  - backup and scratch files (`*.pre*`, `*.new`, `*.vN`, `*.tmp`, `CLAUDE.md.*`)
  - `__pycache__`, `.DS_Store`, dev's `.claude/`
  - `exports/` contents (4.9 GB) and every project except reel_002 (test and demo projects stay in dev)
  - `tests/acceptance/` (gate evidence stays in dev) and `tests/out/`
- `docs/M4_CLAUDE_REFERENCE.md` = the M4 `CLAUDE.md`, unchanged. The new `CLAUDE.md` holds the M6 rules.

## M5 source
- **Copied into `m5/` on 12 Nov 2026** from Codex's frozen checkpoint
  `Codex/AI Studio_M5_checkpoint_2026-11-12_064759` (read-only, prepared 06:48 UTC).
- **Verified twice:** all 238 payload files against the checkpoint's own `SHA256SUMS`, once in the
  checkpoint and once in the copy (0 failures, no unlisted files). `m5/SHA256SUMS` is the M5 baseline.
- The checkpoint contains no `.runtime/`. M5 computes its storage root from its own folder
  (`studio_manual_ui/service.py:14`), so `m5/.runtime/` is M6's own session and Brand Library storage,
  separate from Codex's. It is git-ignored.
- Codex's handoff and interface documents are in `m5/checkpoint/` (start with `M5_INTEGRATION_HANDOFF.md`).
- Known hard-coded references to the Codex folder in the copy:
  - `tests/run_isolated.py:13` refuses to run outside the Codex folder.
  - `visual_poster_studio/app.js:453` shows a resume command that points at the Codex folder.
  - `poster_render/backend.mjs`, `isolation.sb` and `tools/run_phase2.py` (the legacy renderer) are hard-coded too.
  Never run these from M6. The app.js screen gets replaced by React in step 4.

## Checksum baseline
`M6_BASELINE.sha256` covers every file in the initial copy except `app/web/node_modules/`.
Check it with `shasum -a 256 -c M6_BASELINE.sha256`. Git holds the same initial state as its first commit.
