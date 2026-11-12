# Reel Style Sheet (default for all edits)

Source: the 4 reels in `reference /` (analyzed 3 Nov 2026).
- R1 `oHhZPHvfgTo` – 29.6 s, 1080x1920, 25 fps – political promo, fire background, gold Devanagari titles
- R2 `jqrpw9lGSzI` – 20.1 s, 1080x1920, 30 fps – birthday poster edit, red/black/yellow, text-mask type
- R3 `s-YiTAFlQ_Y` – 13.8 s, 720x1280, 30 fps – one-word kinetic type over a red-tinted single shot
- R4 `HYkaLaU8_cQ` – 16.8 s, 1080x1920, 30 fps – title reveal with letters filled by images

What they share: **big condensed all-caps type as the main visual, bold cinematic contrast, subjects cut out and layered with text, one idea on screen at a time, and music-driven timing.** The original references contain red-based treatments, but the default look for new edits is now a **premium cinematic DSLR aesthetic**: teal/charcoal shadows, warm golden highlights, natural skin tones, and deep blacks. None of the references has a talking head with standard subtitles, so the caption rules below adapt R3's one-word type treatment to speech.

Values marked *(measured)* come straight from the files. Values marked *(est.)* are read from frames and rounded.

---

## 1. Output
| Setting | Value |
|---|---|
| Resolution | 1080x1920 (9:16) |
| Frame rate | 30 fps |
| Safe area | keep text inside x 90–990, y 250–1600 (avoids the app UI at top and bottom) |
| Length | 15–30 s is the reference sweet spot (13.8–29.6 s) *(measured)* |

## 2. Colors – Cinematic DSLR Palette

The colours below are the **default creative palette for new edits**, not measurements from the four source reels.

| Role | Hex | Application |
|---|---|---|
| Deep charcoal | `#101820` | Backgrounds and overall cinematic base |
| Cinematic teal | `#17434A` | Controlled shadow tint and background accents |
| Dark teal | `#102D35` | Background depth |
| Warm gold | `#D6A45B` | Highlights and selected title accents |
| Golden amber | `#C58B4A` | Warm light accents |
| Natural white | `#F5F3EE` | Main typography |
| Deep black | `#080B0D` | Contrast and title-card backgrounds |
| Champagne | `#E8D2A6` | Premium title and script accents |

The original red, yellow and fire colours remain documented in the reference reels above; use them only when a specific project calls for that original poster treatment.

Rules: keep the frame to 3 dominant colours at a time. Teal/charcoal form the base, warm gold is the accent, and white is used for readable typography. Preserve natural skin tones. Do not apply a red wash or force teal into faces.

## 3. Grading – Cinematic DSLR Default

**Default look:** premium cinematic DSLR colour, with natural skin tones, controlled teal/charcoal shadows, warm golden highlights, and rich but detailed blacks. This replaces the red-monochrome treatment as the default for new edits.

Recommended workflow:
1. Correct exposure and white balance before applying a creative grade.
2. Protect natural skin tones; do not tint faces teal.
3. Add a restrained teal bias to darker background areas and shadows.
4. Warm highlights gently toward gold while retaining highlight detail.
5. Add moderate contrast without crushing shadow information.
6. Apply a subtle vignette only when it helps direct attention.
7. Add very subtle film grain; avoid heavy grunge on faces.

**FFmpeg starting-point filter** (adjust for each source clip):

```text
eq=contrast=1.08:brightness=0.01:saturation=1.05,
colorbalance=rs=-0.04:gs=0.02:bs=0.06:
rm=0.01:gm=0.00:bm=-0.02:
rh=0.06:gh=0.02:bh=-0.04,
vignette=PI/5,
unsharp=5:5:0.4
```

This is a starting point, not a universal LUT. Check the image after grading and reduce the colour-balance values if skin, neutral whites, or highlights shift unnaturally. Apply sharpening lightly and only after resizing.

**Poster look (optional project-specific treatment):** a black-and-white subject (`hue=s=0`, contrast adjusted to the footage) on a deliberate solid colour field. Red, yellow or fire treatments may still be used when the brief specifically requests the original reference aesthetic.

**Finishing:** retain shadow detail; avoid clipped highlights; use subtle grain (approximately 2–4% visual strength) and a restrained vignette. If the subject needs separation, use a soft, local exposure lift rather than brightening the entire face unnaturally.

## 4. Fonts
| Use | Font (free) | Weight | Size @1080x1920 | Tracking | Color |
|---|---|---|---|---|---|
| Captions (word-by-word) | **Anton** (Google Fonts) | 400 (it's already heavy) | 150 px; 130 px if 2 words | 0 | `#F5F3EE`, highlight word `#D6A45B` |
| Hero / one-word punch (R3 style) | **Six Caps** (ultra-condensed) | 400 | 420–500 px tall, word fills 80–92 % of width | 0.02 em | `#F5F3EE` |
| Title cards / posters (R2) | **Anton** or **Bebas Neue** | 400 | 220–300 px, stacked lines, 0.9 line-height | 0 | champagne `#E8D2A6`, warm gold `#D6A45B`, or white; image-filled (text-mask) on charcoal/black |
| Small subline (R2 "PAWANKALYAN") | **Bebas Neue** | 400 | 40–48 px | 0.5 em (very wide) | white |
| Non-Latin scripts (Telugu) | **Noto Sans Telugu** Black / **Ramabhadra** | 900 / 400 | 120–140 px | 0 | `#F5F3EE` or `#D6A45B` |
| Non-Latin scripts (Devanagari, R1) | **Noto Sans Devanagari** Black | 900 | 140–180 px | 0 | champagne `#E8D2A6` → warm gold `#D6A45B` gradient |

All caps for Latin text. No outlines. Use a soft shadow only when the background is busy: `0 6px 24px rgba(0,0,0,.55)`.

## 5. Captions
- **Words per screen:** 1 by default (R3). 2 only when both words are under 4 letters each (e.g. "I KNOW", "FOR THAT" in R3). Never more than 2.
- **Position:** caption block centered at **y = 1150 px** (lower-middle, under the face). Hero words sit at y 630–1130 (33–59 % of height) *(measured R3)*, and the subject's head overlaps the word (subject in front of the text) when a person cutout is available.
- **How words appear (R3):** each new word builds in over **0.10–0.20 s** (letters drop/stagger in from +40 px, 1-frame stagger per letter, ease `power3.out`), holds, and disappears on a hard cut to the next word. No fade-out.
- **On-screen time per word:** 0.6–0.7 s in R3 *(measured: words change at ≈0.4, 1.2, 2.2, 2.9 s…)*. For speech, follow Whisper word timing: show a word at its start time minus 0.05 s and keep it until the next word starts; minimum 0.20 s on screen.
- **Highlight words:** 1 per sentence, the key noun/number/claim → warm gold `#D6A45B`, 1.15x scale, with a 0.12 s scale-pop (1.0 → 1.15 → 1.08). Numbers always highlighted.
- **Background:** none (no boxes/pills).

## 6. Layout
- **Full-bleed single subject**, centered, cropped at chest/waist. Head at roughly y 500–800.
- **Text-behind-subject layering** (R2, R3): background → big type → person cutout → captions.
- **Text-mask** (R2 "02", "PK"; R4 "PARADISE"): footage or photos visible only inside giant letters on black. Use for openers and title cards.
- **Split stacks** (R2 at 5–7 s): the frame cut into 3 horizontal panels (each ≈ 1080x560 with 40 px black gaps), each panel with its own image and word.
- **Letterbox reveal** (R4): a 1080x~560 strip on black, centered vertically, used for logo/title reveals.
- **B-roll:** full-frame, graded with the cinematic DSLR treatment (natural skin, teal/charcoal shadows, warm highlights), max 2.0 s per clip. Use shallow depth of field only when present in the footage or created with a clean subject mask. The speaker's voice continues over it.
- **Zooms:** slow push-in 100 % → 108 % over the length of a shot (ease `sine.inOut`). Punch-in 100 % → 115 % in 1 frame on highlight words / beat hits.

## 7. Motion
| Element | Duration | Easing |
|---|---|---|
| Opener fade from black (R3) | 0.40 s | linear |
| Word / letter build-in | 0.10–0.20 s, 1 frame (0.033 s) stagger per letter | `power3.out` |
| Title card slam-in | 0.25 s from 130 % scale + blur 12 px → 100 % | `expo.out` |
| White flash/bloom transition (R2 at 4.2 s) | 3 frames (0.10 s) up to white, 3 frames back | linear |
| Hard cut | 0 frames, on the beat | – |
| Motion-blur whip (R2 at 15 s) | 0.20 s, 60 px directional blur | `power2.in` |
| Shake on hits | 4 frames, ±12 px | random |

How often something changes: **every 0.6–1.0 s** (a new word, panel or cut). Never let the frame sit unchanged for more than 1.5 s.
Transitions to use: hard cut (≈80 %), white flash (≈10 %), whip/blur (≈10 %). No dissolves, no slides, no 3D flips.

## 8. Sound design
| Item | Spec |
|---|---|
| Music style | Cinematic "mass"/trailer BGM: big low drums, brass/synth stabs, risers, 120–140 BPM |
| Reference loudness | −14.6, −8.7, −15.2, −14.8 LUFS integrated *(measured)*; these reels are music only, with no voiceover |
| Voice reels: final mix | −14 LUFS integrated, true peak ≤ −1.0 dBTP |
| Voice level | −16 to −14 LUFS short-term |
| Music under voice | −28 LUFS (≈ 14 dB under the voice), sidechain duck: 8 dB reduction, attack 20 ms, release 250 ms |
| Music with no speech (intro / gaps > 0.5 s / outro) | up to −18 LUFS |
| Impact hit | on the first frame of every title card, flash, and the hook word; −6 dB under the voice peak |
| Whoosh | starts 0.25 s **before** a whip/flash/B-roll cut and peaks on the cut |
| Pop/click | on each highlighted (yellow) caption word, very quiet (−20 dB relative to voice) |
| Riser | 1.0–2.0 s into the final reveal / CTA |
| Rule | Cuts land on the beat: R2's 4.23 s cut lines up with an audio hit at 4.25 s *(measured)*. Max 1 SFX every 0.5 s |

## 9. Pacing
| Measure | Value |
|---|---|
| Average shot length | R1 ≈ 5.9 s, R2 ≈ 1.0 s, R3 single 13.8 s shot (word changes ≈ 0.65 s), R4 ≈ 4.2 s *(measured from cut detection)* |
| **Default for talking reels** | Cut or B-roll every **1.5–2.5 s**; on-screen change every **0.6–1.0 s** |
| Fast sections | Bursts of 0.13–0.3 s cuts (R2 14.5–15.9 s: 7 cuts in 1.4 s) *(measured)*, 1 burst per reel, before the payoff |
| Pauses | Cut all silences > 0.25 s; keep 0.08 s of air before each sentence |

### The hook (first 3 s)
1. **Frame 0–0.4 s:** start on black or a strong color (all 4 references do). Fade up 0.4 s (R3), or slam in a giant text-mask word by 0.13 s (R2).
2. **By 0.5 s:** the biggest, most provocative word of the opening line is on screen at hero size (Six Caps/Anton, 420+ px), with an impact hit.
3. **0.5–3.0 s:** 3–5 word changes, at least one punch-in, and the main claim (in warm gold) before 3.0 s. The first hard cut or flash comes by 3.0–4.2 s (R2 4.23 s, R4 3.8 s *(measured)*).
4. No logos, intros or "hey guys" in the first 3 s. Lead with the payoff line, even if it means moving it from later in the take.

## 10. Ending
Last 1.5–3 s: a full-screen title card (text-mask or stacked Anton/Bebas Neue on deep charcoal or black), with champagne or warm-gold accents, music up to −18 LUFS, a final impact hit, then a hard cut to black. Retain a project-specific red title card only when the brief explicitly calls for the original reference look.

## 11. Title page, hooks and tags (read by the planner)

The planner sends only this section to the model. The user approves every line before rendering.

### Facts vs creative
- The hook may be creative, but it must not add facts. No new numbers, achievements, schemes, places or claims.
  Only what the speaker says in this reel or what the brief says.
- Captions are the speaker's exact words. They are never rewritten. Quotes on the title page (in “ ”) must be
  the speaker's exact words, word for word.

### Hook (title page, 3 lines, at most 4 words each)
- Line 1: a short question or challenge that makes people stop (e.g. "what did he actually do?" style).
- Line 2: the strongest short phrase the speaker says, as a quote in “ ”.
- Line 3: a short payoff or call ("this is development!" style). Natural spoken Telugu, not a copied sentence.
- Do not copy three pieces of the speech as the hook. Do not repeat the headline.
- Write three different options (different angles: question, number, emotion), so the user can pick one.

### Headline (2 lines above the video)
- Says the same idea as the hook in different words. Never a copy of a hook line.

### Tags (the sign on the title page)
- Format: number — label, the number with its unit exactly as spoken and the label = what that number is about.
  Examples of the format: "31 లక్షలు — ఇళ్ల పట్టాలు", "17,000 — జగనన్న కాలనీలు", "15,000 — సచివాలయాలు".
- Use the most striking number of the reel. Never a number from a different claim.

### Number cards
- One card per spoken number, shown while that number is spoken, with the same unit (లక్షలు, కోట్లు, వేలు)
  and a label that names the same thing the speaker names.

### Framing words allowed on the title page (not facts)
అసలు, ఏం, చేశాడు, ఇదీ, ఇది, అభివృద్ధి, నిజం, చూడండి, వినండి, లెక్క, లెక్కలు, సాక్ష్యం, మార్పు, చేసి, చూపించాడు, జగనన్న, జగన్
