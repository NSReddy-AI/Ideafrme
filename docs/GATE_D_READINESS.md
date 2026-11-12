# Gate D readiness - M4 release (updated 11 Nov 2026, isolated release preparation)

**Gate D is NOT started. Production has not been touched. Every command below is a procedure for the owner-approved release only.**
`P="/Users/Nadish/projects/AI Video Editor."`

## 1. Release artefacts (all beside production, isolated)
| Artefact | Location | Verified |
|---|---|---|
| Release candidate | `$P/Reel Studio_M4_RC1` (173 files, 386 MB; `CHECKSUMS.sha256`) | contents vs checkpoint, startup, reel_002 = production |
| M4 checkpoint (read-only) | `$P/Reel Studio_dev_M4_checkpoint_2026-11-11` | `CHECKPOINT.sha256` OK |
| Offline vendor | `$P/Reel Studio_M4_offline_vendor_2026-11-11` (Python env archives, Homebrew bottles + kegs, model manifest) | SHA256SUMS; archive entry counts = live envs |
| Gate C evidence (read-only) | `Reel Studio_dev/tests/acceptance/M4_gateC/20261111_143119` | `GATE_C_EVIDENCE.sha256` OK |
| Release-prep evidence | `Reel Studio_dev/tests/acceptance/M4_release_prep_2026-11-11` | STT pin check, RC1 verification |

**RC1 = M4 checkpoint + approved changes:** `engine/asr_worker.py` (Gate C offline guard + revision pin), `engine/transcribe.py` + `engine/asr.json`
(revision pin), licence records (SBOM.json, DEPENDENCY_INVENTORY.md, LICENSE_COMPLIANCE.md, THIRD_PARTY_NOTICES.md, new M4_DEPENDENCY_TABLES.md),
planner review, backlog, licence tools. **Left out:** 61 backup/version files (`*.v*`, `*.pre*`, `*.new`, `*.tmp`), all test/demo/check projects
and their exports, `tests/out`, `tests/acceptance` (stays in dev + checkpoint), `node_modules` (built app included), `.claude`.
**projects/** = production's own `2026-11-03_reel_002_development`, byte-identical copy (29 files). **exports/** empty (production has none).

## 2. Pre-flight (read-only, just before the release)
1. `cd "$P/Reel Studio" && shasum -a 256 -c CHECKSUMS.sha256 | grep -vc ': OK$'` → 0
2. `cd "$P/Reel Studio_M4_RC1" && shasum -a 256 -c CHECKSUMS.sha256 | grep -vc ': OK$'` → 0
3. No Reel Studio running: close every "Start Reel Studio" Terminal window; `lsof -ti tcp:8765` → empty (the dev instance started 14:25 counts).
4. No engine job running: `ls "$P/Reel Studio/.heavy_model.lock"` → absent, or the pid in it (first word) is not running.
5. Environments unchanged since the vendor archives: for e in reelstudio rs_tts rs_asr: `~/.venvs/$e/bin/python -m pip freeze | diff - "$P/Reel Studio_M4_offline_vendor_2026-11-11/python_envs/pip_freeze_$e.txt"` → no output.

## 3. Production backup (first step of Gate D - NOT done yet)
6. `mv "$P/Reel Studio" "$P/Reel Studio_old_M3_<date>"` - the untouched original IS the backup (same precedent as `Reel Studio_old_M2_2026-11-10`).
7. `cd "$P/Reel Studio_old_M3_<date>" && shasum -a 256 -c CHECKSUMS.sha256` → 0 failures; then `chmod -R a-w "$P/Reel Studio_old_M3_<date>"`.
8. Optional second copy (recommended): `cp -Rp "$P/Reel Studio_old_M3_<date>" <external disk>/` and re-run its checksum check.

## 4. Release (only with explicit owner approval)
9. `cp -Rp "$P/Reel Studio_M4_RC1" "$P/Reel Studio"` (RC1 stays as the pristine reference).
10. `cd "$P/Reel Studio" && shasum -a 256 -c CHECKSUMS.sha256` → 0 failures.
11. Smoke check in production: `~/.venvs/reelstudio/bin/python engine/adapter.py check`; `~/.venvs/reelstudio/bin/python tests/test_milestone2.py`;
    double-click `Start Reel Studio.command` → app opens, reel_002 shown read-only.
    **Do NOT run `checkpoint.sh` (or any other production-writing regression) after the release unless the owner approves it separately**
    (owner decision 11 Nov 2026).

## 5. Rollback (any time after step 9)
12. Close the app; `mv "$P/Reel Studio" "$P/Reel Studio_failed_M4_<date>"` (kept for diagnosis).
13. `chmod -R u+w "$P/Reel Studio_old_M3_<date>" && mv "$P/Reel Studio_old_M3_<date>" "$P/Reel Studio"`.
14. `cd "$P/Reel Studio" && shasum -a 256 -c CHECKSUMS.sha256` → 0 failures. Production is back to M3 exactly.
**Shared environments need no rollback.** M3 production uses `~/.venvs/reelstudio` and `~/.venvs/rs_asr`. M4 only ADDED packages to
`reelstudio` (fastapi, uvicorn + deps on 11 Nov; M3 does not import them; `pip check` clean) and added `rs_tts` (unused by M3); `rs_asr` is
unchanged. M3 has run alongside these environments all through Gate C (production checksums unchanged, M3 code untouched).

## 6. Recovery (damaged files or environments)
- Production M3: from `Reel Studio_old_M3_<date>` (step 7 verified) or the external copy (step 8).
- M4 source: `Reel Studio_M4_RC1` (CHECKSUMS.sha256) or the checkpoint archive (`RESTORE.md`).
- A Python environment (no network needed, same Mac): `mv ~/.venvs/<env> ~/.venvs/<env>_damaged`;
  `tar -xzf "$P/Reel Studio_M4_offline_vendor_2026-11-11/python_envs/venv_<env>.tar.gz" -C ~/.venvs`; check `pip freeze` = `pip_freeze_<env>.txt`.
  Requires Homebrew Python 3.12.16 at /opt/homebrew (its bottle is in the vendor folder).
- Tools: Homebrew bottles in `homebrew_bottles/` (60 bottles) + kegs in `homebrew_kegs/` for the 6 dependencies with no cached bottle
  (abseil, libvpx, mpdecimal, mpg123, uvwasi, x265).
- Models: stay in their caches (`model_manifest.json`; files are named by SHA-256, so each can be verified). **Not yet backed up elsewhere** (decision 3).

## 7. Status of the release requirements
| Requirement | Status | Evidence |
|---|---|---|
| Gate C evidence preserved | ✅ | read-only + manifest, unchanged |
| Telugu STT pinned | ✅ | revision ba19a24b (weights sha256 1c3388d4… verified); test_transcribe identical to Gate C (16.7 % CER, 0.11 s median, 83 % ≤0.4 s, 85/85 words identical); 0 outside connections without offline settings |
| Licence records | ✅ | SBOM 222 components (no unknown licences, Gemma absent); no GPL/AGPL Python or npm package; FFmpeg GPL-3.0 build + RVM GPL-3.0 obligations documented |
| Offline rebuild | ✅ with limits | web app: `npm ci --offline` → identical dist; Python: env archives (same Mac/path); tools: bottles + kegs; models: local caches only |
| Release candidate | ✅ | RC1 verified (content, startup, reel_002 identical) |
| Planner hook grading | ⬜ owner | docs/M4_PLANNER_HOOK_REVIEW.md - not passed |
| Backup / rollback procedure | ✅ written | sections 2-6 (nothing executed) |

## 8. Remaining risks
1. **Planner quality:** local hooks/headlines are drafts; the quote-completeness check let an incomplete political quote through
   (backlog #25). Mitigated by mandatory human approval + ❓ listing; not safe for reduced supervision.
2. **Models exist only in their caches** (20.8 GB required). Indic Parler-TTS is a gated download (needs a Hugging Face account to fetch again).
3. **Offline rebuild limits:** environment archives restore only on this Mac (same paths, Homebrew Python 3.12.16); a rebuild on another Mac
   needs PyPI wheels (incl. parler-tts from git d108732) - would need a one-time download.
4. Telugu Whisper licence (Apache-2.0) is from the M3 record; the model card is not cached - re-confirm online before distributing.
5. FFmpeg / RVM GPL obligations apply only if Reel Studio is ever given to someone else.

## 9. Owner decisions (11 Nov 2026)
1. Qwen3 planner: accepted for M4 as a **human-supervised editorial assistant only** - every hook, headline, quotation, number and claim
   needs human review and approval; no automatic publishing. Issues in the backlog (#25-#27). (docs/M4_PLANNER_HOOK_REVIEW.md)
2. Model backup: owner chose the internal disk for now. DONE: `$P/Reel Studio_M4_model_backup_2026-11-11` - physical copy (not a clone), 33 files,
   20.84 GB, all SHA-256 verified vs source and blob names, offline restore tested, RESTORE.md, read-only. **Interim:** same disk - copy to an
   external drive when available (remaining risk).
3. Production protection: M3 release, reel_002, configuration and recovery procedures preserved. Shared environments confirmed compatible
   (docs/M4_SHARED_ENV_COMPATIBILITY.txt: every M3 package at its M3 version; reelstudio only gained the 14 app packages; rs_asr identical).
4. No automatic `checkpoint.sh` / production-writing regression after release (step 11).

## 10. Recommendation: **GO for Gate D** on the owner's explicit production release approval. Remaining risks: interim same-disk model backup;
planner = supervised editorial assistant only; environment archives restore only on this Mac.
