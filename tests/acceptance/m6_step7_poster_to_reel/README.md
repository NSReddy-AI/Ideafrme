# M6 step 7: a poster taken all the way to a rendered reel (12 Nov 2026, throwaway project)

1. Poster "E2E both" (two English text layers) made through /api/creative, saved, exported. The PNG was a stand-in
   1080x1350 image made in Python, because the real PNG is made by the browser (checked separately in step 4).
2. POST /api/creative/to-reel -> M4 project 2026-11-12_zz_m6_e2e_both (tech_ai_tools, instagram, listicle):
   2 slides (the poster PNG), script = the two layers top to bottom, narration none, script NOT approved
   (conversion.json).
3. Owner steps done by the test, for this throwaway project only: title page words (PUT /api/projects/<p>/title)
   and script approval (POST .../script/approve).
4. `engine/adapter.py build` -> slides edit, 2 slides, 5.13 s.
5. `tools/m6_render_job.py` -> isolated job root, unchanged engine (engine_unchanged: true), QA PASS: 213 frames,
   -14.1 LUFS, -1.6 dB, 2.6 MB. Contact sheet: *_qa.jpg.
The project, job root and test session were deleted afterwards.
