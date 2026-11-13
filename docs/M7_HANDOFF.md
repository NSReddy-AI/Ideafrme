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
