"""Original trailer-style music bed + sound effects (no licensing issues).
Usage: python music.py <job> <duration_s> [cues.json]
cues.json = {"impact":[t,...], "hit":[...], "whoosh":[...], "riser":[t_start,...], "pop":[...], "build":[start,end]}
Writes build/music.wav and build/sfx.wav (48 kHz)."""
import sys, os, json, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from common import *
SR = 48000; rng = np.random.default_rng(7)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b): return sosfilt(butter(2, [a, b], 'band', fs=SR, output='sos'), x)
def T(d): return np.arange(int(d*SR))/SR
def place(buf, x, t, g=1.0):
    i = int(t*SR); k = min(len(buf), i+len(x))
    if 0 <= i < len(buf): buf[i:k] += g*x[:k-i]
def saw(f, t): return 2*((f*t) % 1)-1
def kick():
    t = T(0.5); f = 45+120*np.exp(-t*30); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*7)+0.3*lp(rng.standard_normal(len(t)), 3000)*np.exp(-t*80)
def clap(): t = T(0.25); return bp(rng.standard_normal(len(t)), 900, 4000)*np.exp(-t*25)*0.6
def hat(): t = T(0.06); return hp(rng.standard_normal(len(t)), 7000)*np.exp(-t*70)*0.25
def stab(d=0.4, fr=(110, 130.81, 164.81)):
    t = T(d); x = sum(saw(f, t)+0.5*saw(f*1.005, t) for f in fr)/len(fr); return lp(x, 1400)*np.minimum(1, t*80)*np.exp(-t*4)
def impact():
    t = T(1.2); f = 80*np.exp(-t*2)+30
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*3)+lp(rng.standard_normal(len(t)), 2500)*np.exp(-t*25)*0.5+lp(rng.standard_normal(len(t)), 800)*np.exp(-t*4)*0.15
def hit(): t = T(0.5); f = 70*np.exp(-t*4)+35; return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*8)+0.3*lp(rng.standard_normal(len(t)), 3000)*np.exp(-t*40)
def whoosh(d=0.4, pk=0.25):
    t = T(d); n = rng.standard_normal(len(t)); o = np.zeros(len(t))
    for i in range(0, len(t), 480):
        fc = 300+2700*t[i]/d; o[i:i+480] = bp(n[i:i+480], fc*0.7, min(fc*1.4, 20000))[:len(o[i:i+480])]
    return lp(o, 6000)*np.where(t < pk, (t/pk)**2, np.exp(-(t-pk)*20))*1.6
def pop(): t = T(0.05); return np.sin(2*np.pi*1800*t)*np.exp(-t*120)*0.6
def riser(d=1.8):
    t = T(d); f = 200+1000*(t/d)**2; return (np.sin(2*np.pi*np.cumsum(f)/SR)*0.4+hp(rng.standard_normal(len(t)), 1500)*0.4*(t/d))*(t/d)**2
if __name__ == "__main__":
    j, c = job(sys.argv[1]); b = os.path.join(j["_dir"], "build"); D = float(sys.argv[2])
    cues = load(sys.argv[3]) if len(sys.argv) > 3 else {}; N = int(D*SR); bpm = c.get("music", {}).get("bpm", 128); bt = 60/bpm
    m = np.zeros(N); t = T(D)
    m += lp(saw(55, t)+saw(55.3, t)+0.5*np.sin(2*np.pi*27.5*t), 220)*0.35*np.minimum(1, t/1.5)
    k = 0; tt = 0.0; s0, s1 = cues.get("build", [D*0.7, D-1.5])
    while tt < D-0.5:
        heavy = s0 <= tt < s1
        if k % 4 in (0, 2) or heavy: place(m, kick(), tt, 0.9)
        if k % 4 in (1, 3): place(m, clap(), tt, 0.8)
        place(m, hat(), tt, 0.7); place(m, hat(), tt+bt/2, 0.5)
        if k % 8 == 0: place(m, stab(0.6), tt, 0.55)
        k += 1; tt = k*bt
    m[int((D-0.5)*SR):] *= np.exp(-np.arange(N-int((D-0.5)*SR))/SR*6)
    m = np.clip(m/np.max(np.abs(m))*0.9, -1, 1); wavfile.write(os.path.join(b, "music.wav"), SR, (m*32767).astype(np.int16))
    fx = np.zeros(N)
    for x in cues.get("impact", []): place(fx, impact(), x, 0.9)
    for x in cues.get("hit", []): place(fx, hit(), x, 0.7)
    for x in cues.get("whoosh", []): place(fx, whoosh(), x-0.25, 0.7)
    for x in cues.get("pop", []): place(fx, pop(), x, 0.4)
    for x in cues.get("riser", []): place(fx, riser(), x, 0.8)
    if np.max(np.abs(fx)) > 0: fx = fx/np.max(np.abs(fx))*0.9
    wavfile.write(os.path.join(b, "sfx.wav"), SR, (fx*32767).astype(np.int16)); print("music/sfx ->", b)
