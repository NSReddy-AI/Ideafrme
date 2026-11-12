"""Mix voice + music (ducked ~14 dB under voice) + sfx -> -14 LUFS, true peak safely under -1 dB after AAC encoding.
Usage: python mix.py <job> <voice.wav|none> <duration_s> [out.wav]
Voice cleaning (project.json "voice_clean"): "deepfilter" (default: DeepFilterNet, MIT/Apache-2.0, ~/.cache/rs_tools/deep-filter
or $RS_DEEPFILTER; falls back to "basic" with a warning if missing), "basic" (FFmpeg noise filter), "none".
AI narration (project narration = "ai", M4 B1) is not cleaned unless voice_clean says so: it is already clean.
Only the SOUNDTRACK is cleaned - transcription always uses the raw audio (cleaning doubled Telugu errors in the M3 test)."""
import sys, os, json, subprocess
from common import *
j, c = job(sys.argv[1]); b = os.path.join(j["_dir"], "build"); v = sys.argv[2]; D = float(sys.argv[3])
out = sys.argv[4] if len(sys.argv) > 4 else os.path.join(b, "edit_audio.wav")
mus, sfx = os.path.join(b, "music.wav"), os.path.join(b, "sfx.wav")
if v != "none":
    if not os.path.exists(v): fail("FILE_NOT_FOUND", f"voice file not found: {v}")
    mode = j.get("voice_clean", "none" if j.get("narration") == "ai" else "deepfilter"); DF = os.environ.get("RS_DEEPFILTER") or os.path.expanduser("~/.cache/rs_tools/deep-filter")
    if mode == "deepfilter" and not os.path.exists(DF):
        emit("warning", code="DEEPFILTER_MISSING", message=f"{DF} not found - using the basic noise filter"); print("WARNING: deep-filter not found, using basic filter"); mode = "basic"
    src, nr = v, ("afftdn=nf=-28," if mode == "basic" else "")
    if mode == "deepfilter":
        T = tmpdir(); v48 = os.path.join(T, "voice48k.wav"); outdir = os.path.join(T, "df"); os.makedirs(outdir, exist_ok=True)
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", v, "-ac", "1", "-ar", "48000", v48]); progress(3, "cleaning the voice")
        run([DF, "--compensate-delay", "-o", outdir, v48], code="DEEPFILTER_FAILED"); src = os.path.join(outdir, "voice48k.wav")
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", f"highpass=f=90,{nr}acompressor=threshold=-22dB:ratio=3:attack=10:release=150,aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={D}", f"{b}/voice_clean.wav"])
    print("voice cleaning:", mode)
    fc = "[0]volume=6dB,asplit[v1][key];[1]aformat=channel_layouts=stereo,volume=2.6dB[m1];[m1][key]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=250[md];[2]aformat=channel_layouts=stereo,volume=-8dB[s1];[v1][md][s1]amix=inputs=3:normalize=0[mix]"
    ins = ["-i", f"{b}/voice_clean.wav", "-i", mus, "-i", sfx]
else:
    fc = "[0]aformat=channel_layouts=stereo[m1];[1]aformat=channel_layouts=stereo,volume=-4dB[s1];[m1][s1]amix=inputs=2:normalize=0[mix]"
    ins = ["-i", mus, "-i", sfx]
progress(10, "premix"); run(["ffmpeg", "-loglevel", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[mix]", "-t", f"{D}", f"{b}/premix.wav"])
progress(40, "measuring loudness")
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{b}/premix.wav", "-af", "loudnorm=I=-14:TP=-2:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
d = json.loads(r[r.rindex("{"):r.rindex("}")+1])
mi = f"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}"
progress(70, "normalising"); run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{b}/premix.wav", "-af", f"loudnorm=I=-14:TP=-2:LRA=11:{mi}:linear=true,aresample=48000,alimiter=limit=0.79:level=false", out])   # 0.79 = -2 dBFS; was 0.84
progress(100)
print("mix ->", out)
