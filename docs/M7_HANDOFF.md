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
