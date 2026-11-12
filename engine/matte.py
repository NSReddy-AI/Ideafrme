"""Shallow depth-of-field: keep the person sharp, blur the background (Robust Video Matting, CPU).
Usage: python matte.py <in.mov> <out.mp4> [center_x] [half_width]
Writes <out.mp4> and <out>_alpha.mp4 (the person matte, for text-behind-subject)."""
import sys, subprocess, numpy as np, onnxruntime as ort, cv2, os
from common import ENGINE, probe, progress, fail
src, dst = sys.argv[1], sys.argv[2]; p = probe(src); NT = max(1, round(p["duration"]*30)); Wd, Hd = p["w"], p["h"]
cx = float(sys.argv[3]) if len(sys.argv) > 3 else Wd/2; hw = float(sys.argv[4]) if len(sys.argv) > 4 else Wd
s = ort.InferenceSession(os.path.join(ENGINE, "models", "rvm.onnx")); rec = [np.zeros([1, 1, 1, 1], np.float32)]*4
dr = np.array([0.4 if max(Wd, Hd) <= 1920 else 0.25], np.float32)
dec = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
def enc(path, fmt): return subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', fmt, '-s', f'{Wd}x{Hd}', '-r', '30', '-i', '-', '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
e1, e2 = enc(dst, 'rgb24'), enc(dst.replace('.mp4', '_alpha.mp4'), 'gray')
xs = np.arange(Wd)[None, :].astype(np.float32); win = np.clip(1-(np.abs(xs-cx)-hw)/40, 0, 1); n = 0
while True:
    buf = dec.stdout.read(Wd*Hd*3)
    if len(buf) < Wd*Hd*3: break
    f = np.frombuffer(buf, np.uint8).reshape(Hd, Wd, 3)
    fgr, pha, *rec = s.run(None, {'src': (f.astype(np.float32)/255).transpose(2, 0, 1)[None], 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': dr})
    a = cv2.GaussianBlur(pha[0, 0]*win, (0, 0), 1.2)[..., None]; ff = f.astype(np.float32)
    bg = cv2.GaussianBlur(ff, (0, 0), 11); bg = np.clip(bg+0.12*np.maximum(bg-170, 0), 0, 255)
    e1.stdin.write((a*ff+(1-a)*bg).astype(np.uint8).tobytes()); e2.stdin.write((a[..., 0]*255).astype(np.uint8).tobytes()); n += 1
    if n % 30 == 0: progress(n/NT*99)
for e in (e1, e2): e.stdin.close(); e.wait()
if e1.returncode or e2.returncode: fail("ENCODE_FAILED", "matte: ffmpeg could not write the output")
progress(100)
print("matte ->", dst, n, "frames")
