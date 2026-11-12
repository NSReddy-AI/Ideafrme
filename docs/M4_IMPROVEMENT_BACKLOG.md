# M4 consolidated improvement backlog

Non-blocking items found while completing M4 (started 11 Nov 2026). Revisit after the full product demo; nothing here blocks Gate C.
Blocking problems were fixed immediately and are listed at the end for the record.

## Visual / design (reels)
1. **Text + music slides with no pictures** show an empty blue-gradient video window on every slide. Expected (no `inputs/slide_NN.png`), but it looks unfinished. Option: brand-coloured panel or a large number treatment when there is no picture.
2. **Slide sub-labels are very small** (the Telugu label under each number) - hard to read on a phone.
3. **End card "LIKE"** renders in a plain serif fallback font, not the brand font.
4. **Jagan template safe-area warnings** (known, warn mode, approved template - unchanged by design): logos 103 px above the safe top, social row 30 px below, video window 50 px each side; stricter published guidance 122 px for logos.

4b. **Narrated slides: caption band sits directly under the slide's number + label**, so the spoken number shows twice (e.g. "17,000" on the slide and again as the highlighted caption) and the area looks crowded. Option: hide the caption while it repeats the slide number, or move the slide label up.
4c. Demo runner (`tools/demo_product.py`) renders through the adapter, not the app, so it does not write `_post.md`; run `engine/post.py` (done for the 11 Nov demo) or let the runner call it.

## Narration (B1)
5. **Long scripts can stop at the 8 GB voice-model limit** on the longest sentence (memory builds up across sentences in one process: 7.27 GB on 10 Nov, just over 8 GB on 11 Nov for the same 9 lines). Finished sentences are cached, so running narration again completes it (verified: second run 5.46 GB). Improve the message/UI: "N of M sentences kept - press Make narration again to finish", or approve an automatic single retry (automatic five-sentence restart stays OFF).
6. Sentence 9 of the demo script (≈5.7-5.8 s) is the one marked long; splitting it in two would lower the peak (user decision - text is never changed automatically).

## App (new in M4)
7. Job "peak memory" comes from `/usr/bin/time` (largest RSS in the job's process tree). It over-states model jobs (file-mapped weights count; ASR showed 17 GB RSS vs about 11 GB physical footprint). Show the engine's own figures (voice-model peak, ASR footprint) instead.
8. Progress for speech-to-text and the planner moves in big steps (the worker reports per piece). A time estimate would help.
9. Uploading a large video gives no progress bar (it just says "Uploading…").
10. Post copy for narrated / text reels has no hashtags (only the planner's checked hashtags are used) - an approved hashtag list per brand or per project would complete it.
11. No in-app editing of the speaker reel's title-page pictures (title_person / title_bg) beyond upload; no cut-out tool (needs a PNG with transparency).
12. Job history is kept in memory only (also logged in each project's history). Restarting the server forgets the job list.
13. reel_002 shows as a "slides" project (it predates the M4 workflow); it is read-only in the app.

## Engine
14. Speech-to-text (Telugu Whisper large-v2) now runs on the CPU: about 5.5 s per second of audio (41 s reference → 227 s; 63 s speaker video → about 5 min incl. planner). A Mac-GPU path that stays within memory (now possible with the one-pass word timing) would speed up planning and narration checks - needs its own accuracy check.
16. Speaker reel planner hooks from the local Qwen3 14B are weak Telugu (known since M4 planner work) - option D (own hook) is in the app.
17. Speaker reel title page has no person/background unless uploaded (plain gradient); the app has uploads but no cut-out tool.
18. The app does not yet show a caption-by-caption review list on the EDIT timeline (only the transcript words and plan.md).
15. Telugu speech-to-text and the planner are not covered by `heavy_lock`; the app runs one job at a time, but two CLI runs at once could overlap.

## Fixed during M4 completion (blocking)
- **Telugu speech-to-text ran out of memory** (narration check B1.3 and speaker transcription B3): 24 GB+ footprint and heavy swapping on the Mac GPU; 18 GB+ on the CPU, even on the M3 reference clip. Cause: transformers 5.22 decodes Whisper with 5 beams by default, and asking for word times kept every attention map of every beam at every step. Fixed in `engine/asr_worker.py`: same 5-beam decoding, then word times measured in ONE pass over the chosen words (OpenAI Whisper's method: alignment-head cross-attention → median filter → DTW); CPU by default; token limit raised to the model's own (Telugu needs ~3 byte-tokens per letter - the 256 default cut pieces off). Result on the M3 reference: **17.5% character errors (identical to M3)**, word starts within 0.11 s (median) of the approved captions, **peak 4.4 GB** (was 18-24 GB). `engine/transcribe.py`: physical-footprint watchdog (`ASR_MEMORY_LIMIT`, `asr.json` `memory_limit_gb` = 10). Backups `*.preASRmem`; checksums before/after in `tests/acceptance/M4_gateB/before_ASR_memory_fix.txt`.
- **No way to correct speech-to-text mistakes in speaker captions** (e.g. "గూగుల్"): the app's caption editor (spelling fixes only, original kept as `w_asr`); a fix after approval withdraws the plan approval (engine gate `PLAN_NOT_APPROVED`) until the user approves again.
- **No application layer existed** (no FastAPI backend, no React screens): built `app/server.py` + `app/web` on the existing adapter (approved 11 Nov; new dependencies fastapi + uvicorn in ~/.venvs/reelstudio, React/Vite/Tailwind in app/web).
- **Slides reels made from scratch could not render** (title page needs hook lines; `title.py` crashed on an empty line 3): title-page editor added to the app.
- **No post copy file** (CLAUDE.md step 6): `engine/post.py` writes `exports/<reel>_post.md` after each render (approved text + checked hashtags only).

## Added 11 Nov (audit)
19. English slides: the big number is pulled out of the sentence, so the label reads "Five AI tools that save hours a week" (the "10" shows above it).
20. English brands still have placeholder handles (@YOUR_TECH_HANDLE / @YOUR_EDITING_HANDLE) - brand data to fill in.
21. Changing a project's style/platform after creation is not in the app (create a new project; Render covers other platforms).

## Added by Gate C (11 Nov)
22. Pin the Telugu speech-to-text model revision in engine/asr.json (refs/main = ba19a24b… used; two snapshots cached), like engine/tts.json.
23. Planner hooks: human grading of tests/out/planner_qwen3_14b.md still to do.
24. `tslib` extraneous in app/web/node_modules (harmless, build-only).
25. Planner quote-completeness check accepted “ఇరవై స్థానాల్లోనే మనల్ని” (ends before the verb "…పోటీ చేయనిస్తా ఉన్నారు"); it should reject a quote that stops before its verb, as it already does for "…చాలానే". See docs/M4_PLANNER_HOOK_REVIEW.md.
26. Planner headlines invent or merge claims (e.g. "ప్రభుత్వ బడులు పెరిగాయి"); hashtags are built from speech-to-text errors - only from corrected captions would help.
27. Planner Telugu quality (owner decision 11 Nov: accepted for M4 as a human-supervised editorial assistant only): Qwen3 hooks/headlines are
    often unnatural or generic ("ఇది నిజం అయ్యేది!", "ఇది లెక్కలు అయింది", "ఇదీ పోటీ కావాలి!") and sometimes unrelated to the speech
    ("ఇదీ అభివృద్ధి!" on the rally speech). Every hook, headline, quotation, number and claim needs human review; never automatic publishing.
    Improvement options: better few-shot examples from approved_hooks.json, stricter naturalness checks, or an optional stronger planner.
