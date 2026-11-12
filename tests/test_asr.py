"""Speech-to-text comparison on Telugu (dev copy only). Compares whatever engines are installed:
  openai-whisper (current, pipx), faster-whisper (test env ~/.venvs/rs_asr), whisper.cpp (Homebrew whisper-cli).
Reference: the approved, verbatim captions of 'What jagan said' (tests/asr_reference_what_jagan_said.json).
Measures character error rate (CER, best for Telugu), word error rate, Telugu-script share, time and speed.
Run:  ~/.venvs/reelstudio/bin/python tests/test_asr.py [--quick] [--only=faster-whisper --only=whisper.cpp]
      (--quick = turbo models, cleaned audio only; --only = run just these engines)
Writes tests/out/asr_report.json and asr_<engine>_<model>_<audio>.txt. Installs nothing, downloads nothing itself."""
import os, sys, json, time, shutil, subprocess, unicodedata, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "tests", "out", "asr"); os.makedirs(OUT, exist_ok=True)
REF = json.load(open(os.path.join(ROOT, "tests", "asr_reference_what_jagan_said.json")))
SRC = os.path.normpath(os.path.join(ROOT, REF["source"])); QUICK = "--quick" in sys.argv
HOME = os.path.expanduser("~")
OPENAI_PY = os.path.join(HOME, "Library/Application Support/pipx/venvs/openai-whisper/bin/python")
FW_PY = os.path.join(HOME, ".venvs/rs_asr/bin/python")
WCPP = shutil.which("whisper-cli"); GGML = os.path.join(HOME, ".cache/rs_asr")
def say(*a): print(*a, flush=True)
def norm(t):
    t = unicodedata.normalize("NFC", t); t = re.sub(r"[\"'“”‘’.,!?;:()\[\]{}…\-–—|।]", " ", t); return " ".join(t.split())
def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]
def score(hyp):
    r, h = norm(REF["text"]), norm(hyp)
    cer = lev(r.replace(" ", ""), h.replace(" ", "")) / max(1, len(r.replace(" ", "")))
    wer = lev(r.split(), h.split()) / max(1, len(r.split()))
    letters = [c for c in h if c.isalpha()]; te = sum('ఀ' <= c <= '౿' for c in letters) / max(1, len(letters))
    return round(cer, 3), round(wer, 3), round(te, 3)
# 1. reference audio: the approved segments, in order, 16 kHz mono; plus the cleaned version used for noisy Telugu
raw, clean = os.path.join(OUT, "ref_raw16k.wav"), os.path.join(OUT, "ref_clean16k.wav")
if not os.path.exists(raw):
    parts = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(REF["segments_in_order"]))
    cat = "".join(f"[a{i}]" for i in range(len(REF["segments_in_order"])))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", SRC, "-filter_complex", f"{parts}{cat}concat=n={len(REF['segments_in_order'])}:v=0:a=1[o]",
                    "-map", "[o]", "-ac", "1", "-ar", "16000", raw], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", "highpass=f=120,lowpass=f=6500,afftdn=nf=-25,dynaudnorm", "-ar", "16000", clean], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw], capture_output=True, text=True).stdout)
say(f"reference: {dur:.1f} s of Telugu speech, {len(REF['text'].split())} approved words")
for py, pk in ((OPENAI_PY, "openai-whisper torch"), (FW_PY, "faster-whisper ctranslate2")):
    if os.path.exists(py):
        v = subprocess.run([py, "-c", f"import importlib.metadata as m; print(', '.join(p + ' ' + m.version(p) for p in '{pk}'.split()))"], capture_output=True, text=True).stdout.strip()
        say("version:", v or "unknown")
if WCPP: say("version: whisper.cpp", subprocess.run(["brew", "list", "--versions", "whisper-cpp"], capture_output=True, text=True).stdout.strip() or "unknown")
ONLY = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")]
models = ["turbo"] if QUICK else ["turbo", "large-v3"]; audios = {"clean": clean} if QUICK else {"raw": raw, "clean": clean}
FW_CODE = r'''
import sys, json, time, wave
import numpy as np
from faster_whisper import WhisperModel
with wave.open(sys.argv[2]) as w:                     # read the 16 kHz wav ourselves (avoids a PyAV version clash)
    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8")
segs, info = m.transcribe(audio, language="te", word_timestamps=True, beam_size=5)
words = [w for s in segs for w in (s.words or [])]
print(json.dumps({"text": " ".join(w.word.strip() for w in words), "words": len(words)}, ensure_ascii=False))
'''
HF_CODE = r'''
import sys, json, wave
import numpy as np, torch
from transformers import pipeline
with wave.open(sys.argv[2]) as w:
    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
dev = "mps" if torch.backends.mps.is_available() else "cpu"
try: p = pipeline("automatic-speech-recognition", model=sys.argv[1], chunk_length_s=30, device=dev)
except Exception: dev = "cpu"; p = pipeline("automatic-speech-recognition", model=sys.argv[1], chunk_length_s=30, device=dev)
try: out = p({"raw": audio, "sampling_rate": 16000}, generate_kwargs={"language": "te", "task": "transcribe"})
except ValueError:   # older fine-tunes ship an outdated generation config: borrow the base Whisper one (MIT)
    from transformers import GenerationConfig
    base = "openai/whisper-large-v2" if "large-v2" in sys.argv[1] else "openai/whisper-small"
    p.model.generation_config = GenerationConfig.from_pretrained(base)
    out = p({"raw": audio, "sampling_rate": 16000}, generate_kwargs={"language": "te", "task": "transcribe"})
print(json.dumps({"text": out["text"], "device": dev}, ensure_ascii=False))
'''
TELUGU = {"whisper.cpp-te": ["ggml-te-small"], "hf-telugu": ["vasista22/whisper-telugu-large-v2"]}
def run_engine(engine, model, wav):
    t = time.time()
    if engine == "openai-whisper":
        d = os.path.join(OUT, "tmp_ow"); os.makedirs(d, exist_ok=True)
        r = subprocess.run([OPENAI_PY, "-m", "whisper", wav, "--model", model, "--language", "te", "--word_timestamps", "True", "--fp16", "False",
                            "--output_format", "json", "--output_dir", d], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        if r.returncode: return None, r.stderr[-400:], time.time() - t
        j = json.load(open(os.path.join(d, os.path.splitext(os.path.basename(wav))[0] + ".json")))
        return " ".join(w["word"].strip() for s in j["segments"] for w in s.get("words", [])), None, time.time() - t
    if engine == "faster-whisper":
        r = subprocess.run([FW_PY, "-c", FW_CODE, model, wav], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        if r.returncode: return None, r.stderr[-400:], time.time() - t
        return json.loads(r.stdout.strip().splitlines()[-1])["text"], None, time.time() - t
    if engine == "hf-telugu":
        r = subprocess.run([FW_PY, "-c", HF_CODE, model, wav], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
        if r.returncode: return None, r.stderr[-400:], time.time() - t
        return json.loads(r.stdout.strip().splitlines()[-1])["text"], None, time.time() - t
    if engine in ("whisper.cpp", "whisper.cpp-te"):
        mf = os.path.join(GGML, f"{model}.bin" if engine == "whisper.cpp-te" else f"ggml-{'large-v3-turbo' if model == 'turbo' else 'large-v3'}.bin")
        if not os.path.exists(mf): return None, f"model file missing: {mf}", 0
        base = os.path.join(OUT, "tmp_wcpp")
        r = subprocess.run([WCPP, "-m", mf, "-l", "te", "-f", wav, "-ojf", "-of", base, "-np"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        if r.returncode: return None, r.stderr[-400:], time.time() - t
        j = json.load(open(base + ".json", encoding="utf-8", errors="replace")); return " ".join(x["text"].strip() for x in j.get("transcription", [])), None, time.time() - t
def has_tf():
    return os.path.exists(FW_PY) and subprocess.run([FW_PY, "-c", "import transformers, torch"], capture_output=True).returncode == 0
CHUNK = "--chunk" in sys.argv
def chunks(wav, max_s=15.0, min_s=8.0):
    """Split at the quietest moment between min_s and max_s seconds (rally audio has no true silence);
    small models stop early on long audio."""
    import wave, numpy as np
    with wave.open(wav) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32); sr = w.getframerate()
    hop = int(0.05 * sr); rms = np.sqrt(np.convolve((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).mean(1), np.ones(4) / 4, "same"))
    cuts, start = [], 0.0
    while dur - start > max_s:
        a, b = int((start + min_s) / 0.05), int((start + max_s) / 0.05)
        end = (a + int(np.argmin(rms[a:b]))) * 0.05; cuts.append((start, end)); start = end
    cuts.append((start, dur)); files = []
    for k, (a, b) in enumerate(cuts):
        f = os.path.join(OUT, f"chunk_{os.path.basename(wav)[:-4]}_{k}.wav")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-ar", "16000", "-ac", "1", f], check=True); files.append(f)
    return files
def run_chunked(engine, model, wav):
    texts, t0 = [], time.time()
    for f in chunks(wav):
        txt, err, _ = run_engine(engine, model, f)
        if txt is None: return None, err, time.time() - t0
        texts.append(txt)
    return " ".join(texts), None, time.time() - t0
engines = [e for e, ok in (("openai-whisper", os.path.exists(OPENAI_PY)), ("faster-whisper", os.path.exists(FW_PY)), ("whisper.cpp", bool(WCPP)),
                           ("whisper.cpp-te", bool(WCPP) and os.path.exists(os.path.join(GGML, "ggml-te-small.bin"))), ("hf-telugu", has_tf())) if ok]
say("engines found:", engines or "none")
rows = []
for e in [e for e in engines if not ONLY or e in ONLY]:
    for m in TELUGU.get(e, models):
        for an, wav in audios.items():
            say(f"-- {e} / {m} / {an} audio ...")
            try: text, err, secs = (run_chunked if CHUNK else run_engine)(e, m, wav)
            except subprocess.TimeoutExpired: text, err, secs = None, "timed out (30 min)", 1800
            if text is None: say("   skipped:", err); rows.append(dict(engine=e, model=m, audio=an, error=err)); continue
            cer, wer, te = score(text); open(os.path.join(OUT, f"asr_{e}{'_chunked' if CHUNK else ''}_{m.replace('/', '_')}_{an}.txt"), "w").write(text)
            row = dict(engine=e + (" (chunked)" if CHUNK else ""), model=m, audio=an, cer=cer, wer=wer, telugu_script=te, seconds=round(secs, 1), speed_x=round(dur / max(secs, 0.01), 1))
            rows.append(row); say(f"   CER {cer:.1%}  WER {wer:.1%}  Telugu script {te:.0%}  {secs:.0f} s ({row['speed_x']}x real time)")
rp = os.path.join(ROOT, "tests", "out", "asr_report.json")
old = json.load(open(rp)).get("rows", []) if ONLY and os.path.exists(rp) else []
keep_old = [r for r in old if not any(r["engine"] == o + (" (chunked)" if CHUNK else "") for o in ONLY)]
json.dump(dict(reference_seconds=round(dur, 1), rows=keep_old + rows), open(rp, "w"), ensure_ascii=False, indent=1); rows = keep_old + rows
ok = [r for r in rows if "cer" in r]
if ok:
    best = min(ok, key=lambda r: (r["cer"], r["seconds"]))
    say(f"\nmost accurate: {best['engine']} / {best['model']} / {best['audio']} audio (CER {best['cer']:.1%}, {best['seconds']} s)")
say("report -> tests/out/asr_report.json | transcripts -> tests/out/asr/")
