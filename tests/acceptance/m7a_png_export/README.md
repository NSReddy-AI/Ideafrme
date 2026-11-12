# M7-A: targeted PNG export check — PASS (12 Nov 2026)

## How it was run

- **Browser:** your own Chrome 157 (Claude in Chrome), window focused, against the throwaway check server on port 8776.
  That server has its own session; M6's real session and Brand Library were not used.
- **Test poster:** six text layers, at 56–72 px. Five are pure Telugu, covering conjuncts, vowel signs, ZWNJ, visarga
  and Telugu digits. One is mixed Telugu and English, with curly quotes and "é". One block sits exactly on the 64 px
  margin (x = 64), and one is near the bottom-right.
- **Export:** through the editor's normal "Export PNG" button. That runs M5's font probe, overflow check and exact
  pixel comparison.
- **Evidence in this folder:** the exported files (`poster.draft.png`, `poster.draft.svg`, `manifest.json`), the
  comparison script (`png_check.py`, re-runs from this folder) and its output (`results.json`).

## Results

| Check | Result |
|---|---|
| M5 export checks (manifest) | fonts loaded, overflow none, embedded fonts true, **pixel parity true** |
| Same image as the preview | SVG SHA-256 593bf058… equals the preview scene at revision 19; PNG SHA-256 matches the manifest |
| Format | RGBA, 1080 × 1350 |
| Clipping at poster edges | 0 ink pixels on any edge row or column; no stray ink outside the six text bands |
| Text positioning | for all 6 layers, the PNG ink lies inside the browser's measured text box (within 2 px); left edge 0–2 px from the measured x (4 px for the line starting with a curly quote, which is that glyph's side bearing) |
| Margin case | block at x = 64: ink starts at x = 65, inside the poster and the safe area |
| Telugu shaping (11 words, 5 lines) | compared with the engine (Pillow + RAQM, same font file, same size), word by word: 10 words 0.9986–1.000. బ్రహ్మ scored 0.9625 at first because its window included part of the neighbouring word. Measured each way: every engine stroke is in the PNG (1.000), and 99.7% of the PNG's own ink matches the engine word |
| Mixed Telugu/English line | checked by eye: curly quotes, Latin digits and "é" drawn in Inter, Telugu in Noto Sans Telugu, correctly placed |
| Protected assets | **not applicable**: M5 posters cannot place logo or image layers yet, so no protected asset can appear in a PNG. Not a pass |

## Found during the check: PNG export depends on window focus (for Codex)

In the in-app Browser pane, PNG export was unavailable ("Browser operation timed out") while the window was not focused.
The cause is that the browser defers `HTMLImageElement.decode()` for full-size 1080 × 1350 images while unfocused: it
had not finished after 9–12 s. The same image loads in 4 ms through `onload` and in 10 ms through `createImageBitmap`.

M5's `visual_poster_tests/browser_acceptance.js` uses `decode()`, with a 5 s limit, in its font probe and its pixel
comparison. So a person exporting while the window is behind another one sees PNG export turned off for no visible
reason. Suggested M5 fix, for Codex within M5 scope: use `onload` or `createImageBitmap` for these decodes. No M6
change was made.
