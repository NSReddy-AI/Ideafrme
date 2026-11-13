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
