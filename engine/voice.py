"""Voiceover for a project.
Usage: python voice.py <job> [script.txt] [out.mp3]
M4 B1 - project.json "narration" decides (set with: rs.py narration <project> ai|recorded|none ...):
  "ai"       -> engine/narrate.py: local Indic Parler-TTS (Prakash / Lalitha, News / Documentary), offline, approved script only
  "recorded" -> engine/narrate.py: the user's own recording (narration_file)
  "none"     -> no voice: the reel is made as text + music
  not set    -> exactly the behaviour before M4 (ElevenLabs below). It runs only for a project WITHOUT a narration setting
               AND with ELEVENLABS_API_KEY set; ElevenLabs is an excluded provider and is never chosen by default.
ElevenLabs (unchanged): needs env ELEVENLABS_API_KEY (and optional ELEVENLABS_VOICE_ID). Never write the key into a file.
If no key is set, exits with a message so the reel is made as text + music instead."""
import sys, os, json, urllib.request, subprocess
from common import *
_P = load(os.path.join(job_dir(sys.argv[1]), "project.json")) if len(sys.argv) > 1 and os.path.exists(os.path.join(job_dir(sys.argv[1]), "project.json")) else {}
if "narration" in _P:
    _m = _P["narration"]
    if _m == "none": print("narration: none -> text + music"); emit("output", path=None, narration="none"); sys.exit(0)
    if _m not in ("ai", "recorded"): fail("NARRATION_MODE_INVALID", f"narration must be ai, recorded or none (is '{_m}')")
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):   # a script file given here must be the approved one, word for word
        import narration_script as _NS
        _given = [x.strip() for x in open(sys.argv[2], encoding="utf-8").read().splitlines() if x.strip()]
        _ok, _code, _msg, _N = _NS.verify(dict(_P, _dir=job_dir(sys.argv[1])))
        if _ok and _given != [l["text"] for l in _N["lines"]]:
            fail("NARRATION_TEXT_CHANGED", f"{sys.argv[2]} differs from the approved narration script - approve the new text first")
    sys.exit(subprocess.call([sys.executable, os.path.join(ENGINE, "narrate.py"), sys.argv[1]]))
key = os.environ.get("ELEVENLABS_API_KEY")
if not key: fail("NO_VOICE", "NO_VOICE: ELEVENLABS_API_KEY not set -> make this reel as text + music.")
j, c = job(sys.argv[1]); txt = open(sys.argv[2], encoding="utf-8").read().strip()
vid = os.environ.get("ELEVENLABS_VOICE_ID") or c.get("voice", {}).get("voice_id")
if not vid:
    if c.get("language", "en") != "en":   # never fall back to an English voice for a Telugu (or other) brand
        fail("VOICE_NOT_SET", f"brand '{c['name']}' ({c['language']}) has no voice: add voice.voice_id to brand.json or set ELEVENLABS_VOICE_ID")
    vid = "21m00Tcm4TlvDq8ikWAM"   # ElevenLabs default English voice, English brands only
out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(j["_dir"], "build", "voice.mp3")
req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
    data=json.dumps({"text": txt, "model_id": "eleven_multilingual_v2"}).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
try: data = urllib.request.urlopen(req, timeout=180).read()
except Exception as e: fail("VOICE_API_FAILED", f"ElevenLabs request failed: {e}")
open(out, "wb").write(data); print("voice ->", out)
