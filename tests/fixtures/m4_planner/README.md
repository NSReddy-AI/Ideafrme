# M4 planner regression transcript

Byte-identical copy of the historical M4 transcript from
`Reel Studio_dev/projects/2026-11-03_reel_002_development/build/words.json`.
Copied on 2026-11-22 for the planner safety regression; the historical source was read only.

- SHA-256: `94fb7a37a64a82cbd6156715ce5034738ffdf1bdb883d9a692ba22dd8e7ccd7e`
- Structure: 102 timed word records, with 16 spoken quantities.
- Preserve wording, ordering and timings: the regression asserts exact indices and claims.
- This is test input, not an approved project or production acceptance evidence.

Run from the repository root:
`~/.venvs/reelstudio/bin/python -B tests/test_plan_checks.py`
No historical project folder is required. The test reads this fixture, provider configuration,
and brand reference files; it does not invoke planner CLI release or rendering operations.
