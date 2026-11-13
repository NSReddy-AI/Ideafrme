# M7 handoff notes (B4B-4 onward)

One short note per stage: what changed, what was checked, what is still open. Development build only; nothing here is a release.

## B4B-4 - responsive and accessibility

Changed
- Poster editor: below about 42rem of editor width the layer list moves into the right-hand tabs (Layers, Properties, Quality, Reel) and the canvas comes first. Three columns start at 56rem of editor width, so they appear in a 1280 px window.
- The selected layer's box sits above the others, so its resize handle can always be grabbed (it could be covered by another layer's box before).
- Reel inputs: file pickers no longer push the page wider at tablet width. Home: reel names no longer collapse to "20..." on phones; the prompt box is three lines.

Checked in the browser (throwaway server, port 8776)
- 360, 390, 768, 1024, 1280, 1680 px: no sideways page scroll and no clipped controls on Home, Advanced Create, Projects, Brand Studio, Exports, Settings, poster editor, reel steps, #/posters, #/design.
- Editor at 360 px: canvas first, all four tabs reachable, Export reachable, 100% zoom scrolls inside the canvas only.
- Real mouse drag moves a layer; real mouse drag on the handle resizes it (after the existing "upgrade history format" confirmation).
- 200% browser zoom equals half the window width in CSS pixels; covered by the 360-768 px checks.
- Reduced motion: durations come from tokens that the reduced-motion rule sets to zero. Skip link present.

Open
- The stray ellipse layer seen once in B4B-3 did not reappear in 5 further scripted rounds of the same sequence. Cause unknown; treated as not reproducible.
- Not done by hand: a real screen reader pass, a real Telugu keyboard (IME was simulated), Tab order on a physical keyboard.

## B4C-1 - durable local tasks

Changed
- New `app/tasks.py`: one JSON record per task under `jobs/tasks/` (local data, not in Git). Kinds: poster, reel, both. States: pending, running, waiting, completed, failed, cancelled, retrying; a task's state is always derived from its steps.
- Routes: `GET /api/tasks`, `GET /api/tasks/{id}`, `POST /api/tasks`, `POST /api/tasks/{id}/step`, `/cancel`, `/retry`. Seven lines added to `app/server.py` to install them; the job queue itself is unchanged.
- Poster steps are reported by the screen when the existing M5 call really succeeds or fails. Reel steps mirror the existing engine jobs and the reel's own approval state; the screen cannot set them.
- Same `key` twice gives the same task. Approvals and hand-written hooks are never retried automatically.

Checked (`tests/test_tasks.py`, 9 tests, no engine job run)
- Create, real progress, failure, retry, cancel, invalid requests, concurrent writes, damaged files reported and kept.
- Restart: through the real server, a running step comes back as failed "interrupted by a restart", waiting-for-you survives, the prompt is kept.

Open
- Engine jobs still live in server memory; after a restart their step is reported as interrupted and can be queued again. That is honest, not seamless.
- No clean-up of old task files yet.

## B4C-2 - real orchestration interface

Changed
- `app/web/src/tasks.ts` (client and pure helpers), `use-task.ts` (keeps a task fresh), `TaskTracker.tsx` (step list, one-line strip, and the dark progress page at `#/task/<id>`).
- The brief form creates one task per creation and reports interpret and brief. Concepts reports concepts, choose and poster. The editor reports review, QA numbers and export, and shows a one-line strip while the task is open. A reel page shows the reel's task; its steps come from the server's mirror of engine jobs.
- Percentages appear only when the engine reported one. The ring on the progress page turns only while a step is running, and not at all with reduced motion.

Checked
- `tests/web/test_tasks_logic.mjs` (41 checks).
- Browser, real poster operations: steps moved brief -> concepts -> waiting for your choice -> poster -> review -> QA -> export -> completed. A forced failure of the concept call showed "Make three concepts: Failed" with the error; a page reload showed the same failed state; doing the step again for real cleared it.

Open
- Reel steps were not exercised with a live engine job in this stage (the mirror is covered by `tests/test_tasks.py`); a real build and render is part of B4C-4/B5.
- Posters made before this stage have no task and show no strip.

## B4C-3 - capability and provider health

Changed
- New `app/capabilities.py` and `GET /api/capabilities`: for each capability, separate answers for installed, configured, available, qualified, running, failed, unsupported (and switched off). Facts are read on this Mac only: `providers.json`, the local model server's own model list and in-memory list, whether a key exists in the environment (never its value), whether the local speech and voice environments exist.
- `app/web/src/capabilities.ts` turns those answers into one headline (a reason it cannot be used always wins). `CapabilityList.tsx` shows the list on Home (short) and in Settings (every answer, with what it is based on). The old Planner pills in Settings are replaced by this list.
- "Qualified" is per use: the local model is marked as used by the M4 reel planner, and as not qualified for poster concepts (Codex's NO-GO record).

Checked
- `tests/test_capabilities.py` (7 tests, made-up facts, nothing contacted) and `tests/web/test_capabilities_logic.mjs` (27 checks).
- Browser, this Mac: local model server answering with qwen3:8b and qwen3:14b; reel planning Available; AI poster concepts Not qualified although the model is installed; Claude, Gemini and ChatGPT Switched off (two have a key in the environment and still show as off); translation, generated pictures and Web Bridge Unsupported.

Open
- Speech and voice environments are only checked for presence; they are not started to prove they work.
- No paid provider was called, so "configured" for them means only that a key exists.

## B4C-4 - poster-first "Both" as one tracked chain

Changed
- A creation started as Both gets one task with 14 steps: the eight poster steps, "Make a reel from the poster", then the five reel steps. "Make a reel" in the editor reports the handoff with the real reel name; from then on the reel's engine jobs and its approval state fill the same task.
- The editor's Reel tab reads "Reel · next" and explains the handoff when it is the waiting step. The reel page and Concepts show the same progress list, with the original request. The brief form's Both note now describes the real order.
- The original Omnibar prompt is kept in the task record (`meta.prompt`), which is local data beside the projects. No poster or reel schema changed.
- Fixed in `app/tasks.py`: a finished engine job could start a second, empty task for the same reel on the next look. Finished jobs are now remembered; test added.

Checked
- `tests/test_tasks.py` (10 tests): the chain stops at the concept choice, poster review, handoff and script approval; a failed export does not open the handoff; the screen cannot mark approval, build or render; a failed render leaves the task failed; the prompt survives to the end.
- End to end with the real engine (throwaway reel `2026-11-12_zz_b4c4_check`, deleted afterwards with its exports): prompt "Poster and reel for Reading Day..." -> Both detected -> brief -> three concepts -> choice -> poster -> SVG+PNG export -> handoff -> reel created with its script not approved -> Build and Render disabled until approval and title page -> build 5/31/63/95% from the engine -> render 0/18/85% -> task Completed. Reel QA passed.

Open
- PNG export, which the handoff needs, did not work in the app's unfocused preview pane (the known M5 decode stall: "PNG export unavailable: Browser operation timed out"). It worked in focused Chrome, where this check was finished. The button was correctly disabled; nothing was faked.
- The title page words are one more thing the reel needs before Build; they are not a tracked step.

## B5 - consolidated acceptance and polish

Changed
- One quiet entrance animation when a screen or a step of a flow appears (zero with reduced motion). Home lists unfinished creations under "Pick up where you left off" when there are any. The Home brand selector stays compact when draft brands have long names. The capability list explains that the app must be restarted if it was updated while running.

Checked
- All suites, once: Python 49 tests in 8 files (tasks 10, capabilities 7, creative 10, poster QA 8, approved content 6, brand bridge 3, engine jobs 2, token audit 3); web 237 checks in 8 files; token audit 0 findings; contrast check 0 failures; type-check clean; lint at its 10 earlier warnings.
- Real data (dev server on 8775, read only): the three brands are still drafts, none is eligible, and Home shows them as not available. Capability list matches this Mac. Projects shows the real poster-reel link.
- Timings on this Mac: server answering 0.3 s after start; page load about 90 ms; Projects list 50 ms; poster editor open 131 ms; task and capability routes about 1-10 ms; the older system check route 0.7 s.
- Resource use: engine jobs still run one at a time and the engine's heavy-model lock is unchanged, so planning with the local model and rendering do not run together. The task watcher looks at the in-memory job list twice a second and writes a file only when something changed.

Issues by class
- Critical: none open.
- High: none open. (Fixed in this run: resize handle could be covered by another layer; a finished engine job could create a second empty task.)
- Medium: PNG export stalls when the browser window is not focused (M5, with Codex); poster overflow gate trusts the browser's measurement (M5 design); engine jobs do not survive a restart (reported as interrupted, retry offered); task files are never cleaned up; title page words are not a tracked step.
- Cosmetic: Home lists "Recent reels" only; poster rows have no dates; two posters per brief appear in Projects (the brief's and the chosen concept's).
- Deferred capability: AI poster concepts, model-read prompts, translation, generated pictures, Reference Style Studio, layout repair, reel timeline editor, image and logo layers, Web Bridge, paid providers.

Not done
- No screen-reader pass, no physical-keyboard Tab pass, no real Telugu keyboard. No accessibility certification is claimed.
- Brand rights, the logo master and a production release remain the owner's decisions.

# M7-C (final M7 stages, 13 Nov 2026)

## C1 - tasks, title page, stale server, launcher
- Task records are now `ideaframe-task@2`: reel and both tasks have a "Set the title page words" step, read from the reel project (a speaker reel skips it). `@1` records are upgraded when read.
- `POST /api/tasks/cleanup` and a Settings button remove finished records older than 30 days; at start, older than 90 days. Unfinished, failed and damaged records are always kept.
- `GET /api/version` says whether the running server is older than the code on disk, and whether the built screens are older than their source. The app shows "Restart needed" when so (also when the route is missing, i.e. a very old server).
- Launcher: refuses with a plain message when Python or the built screens are missing or the port belongs to something else; reuses a current copy; replaces a stale copy of this workspace, but never while it has a job queued or running.
- Checked: `tests/test_tasks.py` 12 tests; launcher exercised on a spare port against a fresh and a stale copy (old process stopped, new one current).
