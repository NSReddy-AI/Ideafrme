# Reel Studio

Give any input (video, link, screenshots/photos, or an idea) + choose **Brand × Platform × Style** → get a finished
1080x1920 reel, a 4K cover and ready-to-post text.

| Folder | What's inside |
|---|---|
| `brands/` | One folder per brand: look, logos, end card, language, rules |
| `platforms/` | Instagram, YouTube Shorts, Facebook: size, limits, post format |
| `styles/` | News speech, Listicle, Showcase, Cinematic, Documentary |
| `projects/` | One folder per reel: inputs, approved text, plan, build files, history |
| `exports/` | Finished reels + covers |
| `engine/` | The tools (the app screens will use these too) |
| `providers.json` | AI planner choice: Claude / Gemini / ChatGPT |

Useful commands: `python3 engine/rs.py brands | platforms | styles | providers | check`,
`python3 engine/rs.py render <project>`, `python3 engine/rs.py reexport <project> youtube`,
self-test: `python3 tests/test_milestone2.py`.

Status: milestone 2 (engine + settings) done. Next: milestone 3 (app screens), 4 (AI planner), 5 (voice/stock media), 6 (trials).
