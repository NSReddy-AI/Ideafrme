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
**Pending.** Codex was still editing `Codex/AI Studio` at creation time (last change about 01:00, 12 Nov).
Copy it into `m5/` only from a checkpoint Codex names (handoff file, test log and manifest).
Leave out `.runtime/` (browser profiles, test sessions, the local Brand Library).

## Checksum baseline
`M6_BASELINE.sha256` covers every file in the initial copy except `app/web/node_modules/`.
Check it with `shasum -a 256 -c M6_BASELINE.sha256`. Git holds the same initial state as its first commit.
