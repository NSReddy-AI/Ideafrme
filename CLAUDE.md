# IDEAFRAME M6 development workspace: instructions for Claude Code

This folder is the isolated M6 workspace. Here M4 (Reel Studio) and M5 (Creative Studio) are integrated into one
offline-first app under the IDEAFRAME by AINRICH identity. The owner created it on 12 Nov 2026 as a new sibling folder.
For M6 work only, it replaces the M4 rule "work only in `Reel Studio_dev`".

## Where M6 may write
- **Only inside this folder.** Every other folder in `AI Video Editor./` is read-only for M6 work.
- **Protected (never modify, move, rename, delete or run release scripts against):**
  - `Reel Studio` (production M4) and its `CHECKSUMS.sha256`
  - `Reel Studio_dev` (M4 development) and its acceptance evidence
  - `Reel Studio_old_M3_2026-11-11` and its manifests, plus all other backups, checkpoints, RC1 and vendor folders
  - `Codex/AI Studio` (M5, owned by Codex; copy in only from a checkpoint Codex has named)
  - the reel_002 baseline. In this folder its copy (`projects/2026-11-03_reel_002_development`) is a reference.
    Never edit its inputs or `project.json` fields; render tests may only add history lines and exports, exactly as in M4.
- Gate and release tools in `tools/` (`gate_*.py`, `demo_product.py`, `make_register*.py`) and the procedures in
  `docs/GATE_D_READINESS.md` refer to other folders by absolute path. **Never run them from here.**

## Approval boundary
- Planning or architecture approval is not implementation approval. Each M6 step needs the owner's explicit go-ahead.
- Ask first for: new dependencies, network access, model downloads, destructive operations, or anything outside this folder.
- Nothing is published or uploaded automatically. Mandatory human approval of content (plan hash and fingerprints) must never be bypassed.

## Approved decisions (12 Nov 2026)
- **Single shell:** the M4 React 19 + TypeScript + Vite + Tailwind 4 frontend (`app/web`), with the FastAPI backend (`app/server.py`).
  M5's pure `.mjs` modules get imported; M5's screens get rewritten as React components.
- **Workspace:** this sibling folder, under Git.

## M5 code in `m5/`
- `m5/` is M6's mutable copy of Codex's frozen checkpoint `Codex/AI Studio_M5_checkpoint_2026-11-12_064759`.
  It may be changed here. Never write to the checkpoint or to `Codex/AI Studio`.
- M5 keeps its sessions and Brand Library under `m5/.runtime/`. This is M6 data, never Codex's.
  Never point M6 at Codex's `.runtime` or its accepted libraries.
- Never run the legacy renderer (`poster_render/backend.mjs`, `tools/run_phase2.py`) or `tests/run_isolated.py`
  from M6: they are hard-coded to the Codex folder.
- The M6 server reaches M5 only through `app/creative.py` (routes `/api/creative/*` and `/api/brands/*`). It calls M5 as a library,
  with one owner and one lock, and never runs M5's own HTTP server. M6's live session is `m5/.runtime/studio-ui/m6-studio`.
  Test with `~/.venvs/reelstudio/bin/python -B tests/test_m6_creative.py`: it uses throwaway folders and cleans up after itself.
- M5 AI integration is NO-GO (Codex Phase 2E). The Creative Director in M6 stays deterministic until the owner decides otherwise.

## Running side by side with production
- Production and this copy both default to port 8765, and each folder has its own `engine/.heavy_model.lock`.
  Never run both apps at once: they would share neither the port nor the heavy-model lock (24 GB RAM).
  If both must be open, start this copy with `RS_PORT=8775` and run no heavy jobs in parallel.
- Python: `~/.venvs/reelstudio` (shared with production; never install into it without approval).

## Standing project policy (carried over from M4)
Open-source first (permissive licences, recorded in `docs/THIRD_PARTY_NOTICES.md`), fully local/offline at run time,
zero mandatory cost, no GSAP. Never put words in a real person's mouth, never change approved Telugu, facts or brand identity silently.
Application branding (IDEAFRAME tokens and logo) is separate from content brands (`brands/`) and never appears on a reel or poster.

## M4 pipeline reference
The full M4 engine and pipeline instructions are in `docs/M4_CLAUDE_REFERENCE.md` (a copy of the M4 CLAUDE.md).
They still describe how the engine works here. Where they say "work only in Reel Studio_dev", read "work only in this folder".

## Provenance
See `M6_WORKSPACE.md` for what was copied, from where, what was excluded, and the checksum baseline.
