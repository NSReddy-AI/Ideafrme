"""Final reel: title page (project.title_seconds, default 2 s) -> edit in the brand frame -> end card.
Usage: python assemble.py <job> <edit.mp4> <edit_audio.wav> [suffix]
edit.mp4 must already contain captions/graphics. Output: exports/<project>_<brand>_<platform><suffix>.mp4
(RS_PLATFORM picks the platform for this run without changing project.json.)"""
import sys, os
from common import *
j, c = job(sys.argv[1]); b = os.path.join(j["_dir"], "build"); edit, aud = sys.argv[2], sys.argv[3]; suf = sys.argv[4] if len(sys.argv) > 4 else ""
for f in (edit, aud, os.path.join(b, "layout.json"), os.path.join(b, "title_1080.png")):
    if not os.path.exists(f): fail("FILE_NOT_FOUND", f"missing {f}")
L = load(os.path.join(b, "layout.json")); D = probe(edit)["duration"]; TS = float(j.get("title_seconds", 2.0))
end = asset(c, "end_card"); ED = probe(end)["duration"] if end else 0
title = os.path.join(b, "title_1080.png"); progress(2, "title sound")
# title stinger: impact + whoosh into the cut (cached per title length, so a new length makes a new sound)
stg = os.path.join(b, f"title_sfx_{TS:.2f}s.wav")
if not os.path.exists(stg):
    import numpy as np; from scipy.io import wavfile; import music as M
    x = np.zeros(int(TS*M.SR)); M.place(x, M.impact(), 0.03, 0.9); M.place(x, M.stab(1.4), 0.03, 0.5); M.place(x, M.whoosh(0.5, 0.4), TS-0.45, 0.8)
    x = x/np.max(np.abs(x))*0.5; wavfile.write(stg, M.SR, (x*32767).astype(np.int16))
ins = ["-loop", "1", "-t", f"{TS}", "-i", title, "-loop", "1", "-t", f"{D}", "-i", os.path.join(b, "frame.png"), "-i", edit]
if L["type"] == "framed":
    w = L["window"]
    mainv = (f"[1:v]loop=loop=-1:size=1,trim=0:{D},setpts=PTS-STARTPTS,fps=30[bg];[2:v]trim=0:{D},setpts=PTS-STARTPTS,scale={w['size']}:{w['size']}:flags=lanczos,format=rgba[cv];"
             f"[3:v]format=gray[mk];[cv][mk]alphamerge[clip];[bg][clip]overlay={w['x']}:{w['y']}:format=auto,format=yuv420p[t2];")
    ins += ["-loop", "1", "-t", f"{D}", "-i", os.path.join(b, "window_mask.png")]
else:
    mainv = f"[2:v]trim=0:{D},setpts=PTS-STARTPTS,scale=1080:1920,fps=30[e];[1:v]loop=loop=-1:size=1,trim=0:{D},setpts=PTS-STARTPTS,format=rgba[ov];[e][ov]overlay=0:0:format=auto,format=yuv420p[t2];"
    ins += ["-f", "lavfi", "-t", "1", "-i", "color=black:s=2x2"]
fc = f"[0:v]loop=loop=-1:size=1,trim=0:{TS},setpts=PTS-STARTPTS,fps=30,format=yuv420p[t1];" + mainv
if end:
    ins += ["-i", end]; fc += f"[4:v]fps=30,scale=1080:1920,format=yuv420p,setpts=PTS-STARTPTS[t3];[t1][t2][t3]concat=n=3:v=1:a=0,setsar=1[v];"
else:
    fc += "[t1][t2]concat=n=2:v=1:a=0,setsar=1[v];"
ai = 5 if end else 4
ins += ["-i", stg, "-i", aud]
fc += f"[{ai}:a]aformat=channel_layouts=stereo,aresample=48000[ta];[{ai+1}:a]aformat=channel_layouts=stereo,aresample=48000,afade=t=out:st={max(0,D-0.3)}:d=0.3[ea];[ta][ea]concat=n=2:v=0:a=1,apad=whole_dur={TS+D+ED}[a]"
os.makedirs(os.path.join(ROOT, "exports"), exist_ok=True)
out = os.path.join(ROOT, "exports", f"{os.path.basename(j['_dir'])}_{j['brand']}_{j['platform']}{suf}.mp4")
PF = j["_platform"]; mx = PF.get("max_seconds"); VB = PF.get("video_kbps", 10000)
if mx and TS+D+ED > mx:
    print(f"WARNING: reel is {TS+D+ED:.1f}s, {PF['name']} limit is {mx}s"); emit("warning", code="TOO_LONG", message=f"{TS+D+ED:.1f}s > {PF['name']} limit {mx}s")
progress(5, "encoding")
run(["ffmpeg", "-loglevel", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-profile:v", "high", "-preset", "medium",
     "-b:v", f"{VB}k", "-maxrate", f"{int(VB*1.2)}k", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
     "-color_trc", "bt709", "-color_range", "tv", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out],
    total_s=TS+D+ED, pct_range=(5, 99))
progress(100); emit("output", path=out)
print("reel ->", out)
