# M7-A slice 2: Telugu shaping, large-text threshold, measured poster QA (12 Nov 2026)

## 1. Telugu shaping: posters (browser) = reels (engine) — PASS

Reels draw Telugu with Pillow and RAQM (HarfBuzz 14.5). Posters let the browser shape M5's SVG. Both use the same font
file: NotoSansTelugu-Black.ttf, SHA-256 42a3167f…, byte-identical in engine/fonts and M5's pinned fonts.

- **How to repeat:**
  1. Run `~/.venvs/reelstudio/bin/python -B tools/m6_telugu_shaping.py`. It writes `engine/*.png`, `words.json` and `compare.html` here.
  2. Serve this folder on loopback and open `compare.html`. Results land in `window.__shaping`; this run is `results.json`.
- **Words:** 28, in `tests/fixtures/telugu_shaping_words.json`. They cover conjuncts, stacked and repeated consonants,
  vowel signs on every side, ర్ forms, ZWNJ, visarga, Telugu digits, mixed Latin/Telugu and curly quotes.
- **Rule:** both drawn at 96 px, cropped to their ink and compared at native size. They match when at least 97% of the
  ink lies within 1 px in both directions, and width and height differ by no more than 3 px.
- **Result:** 28 of 28 match. Lowest ink match is 0.974 (క్ష), and the largest size difference is 2 px.
- **Negative controls, all caught:** the browser deliberately drew a wrong form.

  | Engine word | Browser drew | Fault | Ink match | Size change |
  |---|---|---|---|---|
  | క్ష | క్‌ష | conjunct broken by ZWNJ | 0.38 | +77 px wide |
  | తెలుగు | తేలుగు | wrong vowel sign | 0.64 | +11 px high |
  | ఇళ్ల | ఇల్ల | different consonant | 0.57 | -23 px high |

- **Metric note:** a first version of the check scaled both crops to 64 px high. That turned 1 px anti-aliasing
  differences into false flags (5 words). The native-size rule above replaced it, and the controls show it still catches real faults.

## 2. The 52 px "large text" threshold (poster canvas coordinates) — measurements

The fonts were measured with Pillow at a 1000 px em (the pinned Inter Bold and Noto Sans Telugu Black):

| Poster font_size | Size on a 390 px-wide phone | Inter lowercase height | Inter capital height | Telugu letter body |
|---|---|---|---|---|
| 40 | 14.4 CSS px | 8.2 px | 10.5 px | 10.8 px |
| **52** | **18.8 CSS px** | 10.6 px | 13.7 px | 14.1 px |
| 64 | 23.1 CSS px | 13.1 px | 16.8 px | 17.3 px |

- WCAG "large" bold text is 14 pt, which is 18.66 CSS px. On a 390 px phone that is poster font_size **51.7**, so 52 is the WCAG boundary.
- Telugu letter bodies are 0.75 em: 1.33 times Inter's lowercase height and slightly taller than its capitals. At the
  same font size, Telugu looks larger than English, so 52 px is conservative for Telugu and exact for English.
- **Owner decision (12 Nov 2026, corrected):** the approved large-text threshold is **52 px in poster canvas
  coordinates** (font_size on the 1080 × 1350 poster), the same for every preview size, including 360 px and 390 px phones.
  No 56 px threshold was approved. The phone-width figures above are background measurements only, not part of the rule.
- Correction note: an earlier version of this file said a 56 px boundary for 360 px phones was "recorded and accepted".
  That was wrong and has been removed.
- The 64 px poster safe margin is unchanged.

## 3. Measured-text QA in the poster editor

- **What changed:** the editor now measures each text layer as actually drawn (`app/web/src/measure.ts`, same off-screen
  method as M5's `inspectScene`).
  - Drawn text outside the poster is an **error**.
  - Drawn text within 64 px of an edge is a **warning** that gives the real distance.
  - With a current preview this replaces the declared-box safe-area check, because the box is usually larger than the text.
- **Unit test:** `node tests/web/test_measure.mjs` — 9 checks.
- **Browser check:** text at x = 10 gave "drawn text is 10 px from the left edge (keep 64 px)". Text at x = -40 gave
  "measured canvas" error, QA FAIL and both exports disabled, together with M5's own overflow block.
- **Not verified in this run:** the PNG export probe. The Browser pane was hidden, and a hidden page never finishes
  decoding PNG images: 12 s+ timed, against M5's 5 s limit. Every other step of the probe took 1 s or less.
  PNG export qualified normally in earlier visible-pane checks (steps 4, 6 and 7).
