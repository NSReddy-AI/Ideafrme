# Reel Studio – instructions for Claude Code

You are the editor for this folder. The user drops inputs into a project and picks a brand + platform; you deliver a
finished, checked reel plus its cover and post copy. Work through the steps below in order. Talk to the
user in short, plain language; do not show code unless asked.

## Golden rules
1. **Stop once for approval** (step 3) before rendering. Never render unapproved Telugu/English text.
2. **Never put words in a real person's mouth.** Captions of speech are verbatim (spelling fixes only).
   Polished wording goes in titles, headlines and graphics, not in quote captions.
3. **No watermarks / broadcaster logos** in any shot (crop, blur or skip the shot).
4. **No downloaded photos of real people.** Use frames from the user's footage or photos the user provides.
5. **Verify facts** from links (date-stamp them); flag anything you could not confirm.
6. A reel = **Brand** (`brands/<id>/brand.json`, look + rules) + **Platform** (`platforms/<id>.json`, size/limits/post format)
   + **Style** (`styles/<id>.json`, pacing/structure/captions). Follow all three, plus the brand's `style-sheet.md` if present.
7. Keep every file inside this folder. Read secrets (API keys) from the environment only.

## Permanent project policy (owner's standing instruction, saved 11 Nov 2026)
- **Open-source first:** prefer commercially suitable open-source software (MIT, Apache-2.0, BSD and similar permissive licences);
  record every new component's licence in docs/THIRD_PARTY_NOTICES.md / LICENSE_COMPLIANCE.md. No GSAP or other non-open-source parts.
- **Locally self-sufficient / offline:** everything runs on this Mac; models, fonts and scripts are installed or vendored locally - never
  loaded from the internet at run time. Cloud services may only ever be optional.
- **Zero mandatory cost:** no required paid APIs, subscriptions or cloud services (Claude/Gemini/ChatGPT/ElevenLabs stay optional, key-gated).
- **Ask the owner first** for: new dependencies or costs, destructive operations, changes to protected production assets, publication,
  or major scope changes. Never publish or upload automatically.
- **Protected:** the original `Reel Studio` production folder (never modified), the locked reel_002 baseline, existing backups,
  checksums and acceptance evidence. Work only in `Reel Studio_dev`. Gate C needs separate authorisation; Gate D (production release)
  needs the owner's explicit approval.
- **Product first:** finish working functionality before cosmetic refinements; record refinements in docs/M4_IMPROVEMENT_BACKLOG.md.

## The pipeline
Commands are run from this folder: `python3 engine/<script>.py <project> ...`

### 1. Start the job
- `python3 engine/rs.py brands|platforms|styles` (show lists if the user didn't choose; default style = brand's default_style).
- `python3 engine/rs.py new <brand> <platform> <style> <short-topic>` -> `projects/<date>_<topic>/`.
  If the user gave files/links/text, put them in `inputs/` (links one per line in `inputs/urls.txt`,
  ideas/notes in `inputs/notes.txt`). Then `python3 engine/rs.py ingest <project>`.
- Mode from ingest: `speaker` (video with a person talking) or `slides` (links/images/idea -> voiceover or text+music).

### 2. Understand the inputs
- **Video:** `python3 engine/transcribe.py --project <project>` -> `build/transcript.json` (words with times on the source).
  Picks the engine by the brand language (engine/asr.json): Telugu = Telugu-trained Whisper (raw audio, never cleaned:
  cleaning made it worse), English = whisper.cpp turbo. Words marked `review` are the tool's doubts; show ALL captions to
  the user anyway (in the M3 test it still changed one phrase's meaning).
- **Links:** fetch and read them; take screenshots of the key parts (Chrome headless:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --screenshot=<file> --window-size=1080,1920 <url>`).
- **Images:** look at each; note what it shows.
- **Notes:** this is the brief.

### 3. Plan -> show the user -> wait for approval
Draft it with `python3 engine/planner.py <project>` (local Qwen3 14B by default; 8B is only a backup, never for automatic
publishing). Facts are built by CODE from the transcript (approved 10 Nov): one beat per spoken number cut at phrase edges,
cards = number + unit as spoken + the speaker's own 1-3 word label, card time = spoken time (`engine/te_numbers.py` reads
Telugu numbers). The model only CHOOSES by claim number (which cards, the tag, hashtags); if it can't, the program chooses.
Then 3 hook options from model candidates + the brand's `style-sheet.md` / `approved_hooks.json`, all checked; quotes verbatim.
Local models write weak Telugu hooks: the user (or you, in chat) can add an own option D, checked the same way:
`python3 engine/planner.py <project> --hook "line1 / line2 / line3 / headline 1 / headline 2"` (“ ” = the speaker's exact words,
no quotes = commentary). Cards in the wrong beat are moved only when exactly one spoken claim matches (audit table in plan.md).
Show `build/plan.md`; the user picks A-D -> `python3 engine/planner.py <project> --approve D [--checked]`
(writes hook/title/approved + a fingerprint into project.json). Rendering refuses an unapproved plan, open ❓ need --checked,
and any edit after approval needs a new approval. After hand edits: `--recheck`.
The plan shows:
- Title page: hook line1/line2/line3 (≤4 words each), sign tag_top/tag_bottom, 2-line headline.
- Beats: time | what is said / shown | on-screen graphic.
- Captions (verbatim) and every on-screen word in the channel language. Mark anything unsure with ❓.
- Length (speaker reels: cut silences >0.25 s; hook = strongest line first).
Apply the user's corrections, then save them into `project.json` (`hook`, `title`, `approved: true`) and continue.

### 3b. The product flow in one place (M4 B3; the app uses the same adapter actions)
- Speaker video: set project.json `video`, then `python3 engine/rs.py plan <project>` (transcribes if needed, then the planner) ->
  show build/plan.md -> optional `rs.py hook <project> "l1 / l2 / l3 / h1 / h2"` -> `rs.py approve <project> A|B|C|D [--checked]`.
- Narrated or text slides: `rs.py narration ...` + `rs.py script` + `rs.py script-approve` (+ `adapter.py narrate` for a voice).
- Then `python3 engine/rs.py build <project>` (engine/build.py: edit + audio from APPROVED material only - plan beats in source
  order with silences cut, verbatim captions, approved number cards; or one slide per approved sentence, captions = approved text)
  and `python3 engine/adapter.py render <project> --all-platforms`. Slide pictures: inputs/slide_01.png ... (the user's own).
- Adapter (JSON events): `adapter.py plan|approve|build|narrate|render <project> ...`. Nothing is ever published automatically.
- Safe areas (B2): layout.json lists every element as must-stay-visible or may-be-covered; QA enforces must-stay-visible for
  enforce-mode brands and warns for the approved Jagan template; platforms/*.json `safe_area_strict` = stricter published
  guidance, advisory warnings only. Sheets: `python3 tools/safe_area_sheets.py`.

### 3c. The app (M4, 11 Nov): `~/.venvs/reelstudio/bin/python app/server.py` -> http://127.0.0.1:8765
- FastAPI backend `app/server.py` + React/Vite/Tailwind screens `app/web` (built into app/web/dist; `npm run build` after UI changes,
  `npm run dev` for live editing with the API proxied). Local only; nothing is ever published.
- The app calls the SAME commands as above (rs.py new/narration/script/script-approve, adapter.py plan/approve/narrate/build/render),
  each as its own process; jobs run one at a time; every job logs its time + peak memory in the project history.
- After a render the app writes `exports/<reel>_post.md` (engine/post.py: approved text + checked hashtags only; draft for the user).
- reel_002 (the locked baseline) is read-only in the app. Test projects (zz_*) and archived projects are hidden unless "show test + archived" is ticked.
- Start: double-click `Start Reel Studio.command`. Jobs can be cancelled. A new/changed source video moves the old transcript/plan/edit to
  build/_superseded_*. Caption spelling fixes keep the heard word (w_asr) and withdraw the plan approval. AI narration = Telugu brands only.
- Feature status: docs/M4_COMPLETION_REPORT.md. Refinements: docs/M4_IMPROVEMENT_BACKLOG.md.

### 4. Build the edit (no channel frame yet)
**speaker mode**
- `build/keep.json` = ordered [[start,end],...] in the source (hook first, silences cut, crowd cheers ≤0.6 s).
  Set `project.json.video` to the source path, then `python3 engine/cut.py <project>`.
- Face tracking (optional, OFF by default): only if project.json `face_tracking` is true, reframe a wide shot with
  `python3 engine/facetrack.py build/cut.mov build/cut_tracked.mp4 --aspect 1:1 --project <project>` (MediaPipe; models in engine/models).
- Background blur: `python3 engine/matte.py <project>/build/cut.mov <project>/build/cut_dof.mp4 [face_x] [half_width]`.
- Shots: build the edit at **1080x1080** for framed brands, **1080x1920** for fullscreen, with FFmpeg
  (crop on the face, slow push-in 100→108 %, colour grade from the style sheet, B-roll / screenshots / cutaways
  for the beats).
- Words: `build/words.json` on the EDIT timeline (`{"w","s","e","hl"}`, numbers hl=true) ->
  `python3 engine/captions.py <project>` -> overlay at the caption band.
- Motion graphics (number cards, maps, bars, end line): build the HyperFrames composition with `engine/motion.py`
  (Web Animations API + fonts copied beside it; example: projects/2026-11-03_reel_002_development/source/gen_overlay_waapi.py).
  NEVER use GSAP (not open source) or fonts/scripts from the internet. Render from inside the composition folder:
  `npx hyperframes lint` (0 errors) then `npx hyperframes render --format webm --output ../overlay.webm`, overlay it.
**slides mode (voiceover or text + music)**
- `build/beats.json` (one beat per point; 2–4 s each; first beat = hook text) -> `python3 engine/slides.py <project>`.
- Narration (M4 B1, optional; chosen per project): `python3 engine/rs.py narration <project> ai --voice prakash|lalitha
  --style news|documentary [--speed 1.0]`, or `recorded --style ... --file inputs/<recording>.wav` (the user's own voice, never
  trained or cloned), or `none` (text + music). Speed stays 1.0 unless the user approves another value.
  Script: one sentence per line in `build/script.txt` -> `python3 engine/rs.py script <project> build/script.txt` shows the
  written text and the spoken form of every number (❓ = check) -> the user approves -> `python3 engine/rs.py script-approve
  <project> [--checked]`. Never change approved Telugu; any edit needs a new approval.
  Then `python3 engine/adapter.py narrate <project>` (offline voice model in ~/.venvs/rs_tts, one heavy model at a time,
  memory stop at 8 GB) -> `build/narration.wav`, `build/narration_timeline.json`, captions `build/narration_words.json`
  (approved text, timed by speech-to-text) and `build/narration_check.json` (show the user every sentence it lists).
  One slide per sentence: `slides.py` takes each slide's length from the narration. Mix with
  `python3 engine/mix.py <project> build/narration.wav <edit_seconds>`.
  AI narration puts the Telugu AI-voice disclosure on screen (frame.py) and QA checks it; switch on the platform's AI label
  when uploading. Recorded or no narration shows no disclosure.
  ElevenLabs (`voice.py`, excluded provider) only runs for a project with no narration setting and ELEVENLABS_API_KEY set.
**Audio (all modes)**
- `python3 engine/music.py <project> <edit_seconds> build/cues.json` (impacts on title/number cards, whooshes before cuts, pops on highlights).
- `python3 engine/mix.py <project> <voice.wav|none> <edit_seconds>` -> `build/edit_audio.wav` (-14 LUFS).

### 5. Brand packaging + export
- Save the edit as `build/edit.mp4` and audio as `build/edit_audio.wav`.
- `python3 engine/rs.py render <project>` = title page (4K cover) + brand frame + end card -> `exports/`.
  Title needs project.json hook + title_person (cut-out PNG, face centred) + title_bg.
- Another platform, same edit: `python3 engine/rs.py reexport <project> <platform>` (project.json keeps its platform).
- All platforms with versions, progress and QA in one go (what the app uses):
  `python3 engine/adapter.py render <project> --all-platforms` -> `exports/<project>_<brand>_<platform>_vN.mp4` + `_qa.json`.
- English version: make English words.json/graphics, rebuild the edit, then `python3 engine/assemble.py ... _EN`.

### 6. Check (always) and deliver
- `python3 engine/qa.py exports/<reel>.mp4 --platform <p> --layout build/layout.json` -> PASS/FAIL + `<reel>_qa.json`; look at the contact sheet yourself.
  Must pass: 1080x1920, 30 fps, no unplanned black frames, -14 LUFS ±1, captions on the right word at 10+ sample
  points, no watermark, nothing overlapping logos/ribbon, every text in the safe area.
- Write `exports/<reel>_post.md` following the platform's `post` settings (caption/title/description/hashtags), in the
  brand language (plus English if asked). The 4K cover is exported automatically.
- Tell the user in 2–3 sentences what was made and anything to check.

## Settings
- **Brand:** `brands/<id>/brand.json` + `assets/` – name, handle, language (te/en), assets, title colours, frame (framed|fullscreen),
  captions, music, rules, default_style, default_platforms.
- **Platform:** `platforms/<id>.json` – size, fps, bitrate, safe_area, max_seconds, post format.
- **Style:** `styles/<id>.json` – pacing, structure, captions mode, graphics, music, transitions.
- **AI providers:** `providers.json` (Claude / Gemini / ChatGPT, default + models). Keys only in the shell environment.
- Self-test after changing settings: `python3 tests/test_milestone2.py`. Engine changes: `bash checkpoint.sh` (must match tests/baseline_reel_002.json).
- Safe areas: platform `safe_area`; brand `frame.safe_area` = enforce (fullscreen default) or warn (framed default, approved template).
