# M6 step 7: reel_002 parity through an isolated engine job root (12 Nov 2026)

Command: `~/.venvs/reelstudio/bin/python -B tools/m6_render_job.py 2026-11-03_reel_002_development --platform instagram --baseline tests/baseline_reel_002.json`
Job root: `jobs/20261112-022442-2026-11-03_reel_002_development-7629c8` (git-ignored). Its manifest is copied here as JOB_MANIFEST.json.

| Check | M6 job render | Dev v25 (release preparation) |
|---|---|---|
| Engine code | byte-identical copy of M6 engine/ (manifest `engine_unchanged: true`) | same engine as production |
| QA | PASS: size, fps, codecs, loudness, true peak, black frames, baseline_frames, baseline_file_size | PASS |
| Frames / size | 1849 frames, 1080x1920 30 fps, 70,563,248 bytes | 1849, 70,424,990 bytes |
| Loudness / peak | -14.1 LUFS / -1.4 dB | -14.1 LUFS / -1.4 dB |
| Audio stream (decoded MD5) | 4bcf522afd0de16b33df6ac4829210de | identical |
| Video vs v25 | PSNR 49.73 dB average (min 47.14) | dev v24 vs v25: PSNR 49.76 dB (min 46.96) |
| Time | 19.6 s | |

Video frames are not bit-identical: 1820 of 1849 decoded frames differ from v25. Dev's own two consecutive renders (v24, v25)
also differ in 1818 frames at the same PSNR, so this is the encoder's normal run-to-run variation. It is not caused by
the job root. Sound is bit-identical. The M6 reel_002 project folder was hashed before and after: unchanged.
