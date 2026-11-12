"""Speech to text with word timings, picking the engine by language (engine/asr.json):
  Telugu  -> Telugu-trained Whisper (IIT Madras, Apache-2.0) in its own Python (~/.venvs/rs_asr), raw audio
  English -> whisper.cpp turbo (MIT), fast on the Mac GPU
Audio is split at its quietest moments into 8-15 s pieces (long audio makes models stop early or repeat).
Usage:
  python transcribe.py --project <project> [--source video] [--ss S --t T] [--lang te|en] [--out build/transcript.json] [--words-out]
  python transcribe.py --audio file.wav --lang te --out transcript.json
Writes {"lang","engine","model","source","words":[{"w","s","e","hl","review":[reasons]}]} on the SOURCE timeline.
--words-out also writes build/words.json (captions format) when the source is used without cuts.
'review' lists the tool's own doubts (repeats, wrong script, odd timing). Every caption is still approved by the user."""
import os, sys, json, re, time, argparse, subprocess, tempfile, unicodedata
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ENGINE, job, load, save, fail, progress, emit, tmpdir, probe

CFG = load(os.path.join(ENGINE, "asr.json"))

def to_wav(src, out, ss=None, t=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-y"] + (["-ss", str(ss)] if ss else []) + ["-i", src] + (["-t", str(t)] if t else []) + ["-map", "0:a:0", "-ac", "1", "-ar", "16000", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: fail("AUDIO_FAILED", f"could not read the audio of {src}: {r.stderr[-400:]}")
    return out

def pieces(wav, lo=8.0, hi=15.0):
    """Cut points at the quietest 0.2 s between lo and hi seconds into each piece."""
    import wave
    with wave.open(wav) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    dur = len(x) / 16000; hop = 800
    rms = np.sqrt(np.convolve((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).mean(1), np.ones(4) / 4, "same"))
    out, start = [], 0.0
    while dur - start > hi:
        a, b = int((start + lo) / 0.05), int((start + hi) / 0.05)
        end = (a + int(np.argmin(rms[a:b]))) * 0.05; out.append([round(start, 3), round(end, 3)]); start = end
    out.append([round(start, 3), round(dur, 3)]); return out, dur

def hf(cfg, wav, parts, lang):
    py = os.path.expanduser(cfg["python"])
    if not os.path.exists(py): fail("ASR_ENV_MISSING", f"the speech-to-text environment is missing: {py} (see SETUP: Telugu speech-to-text)")
    p = subprocess.Popen([py, os.path.join(ENGINE, "asr_worker.py"), "--model", cfg["model"], "--audio", wav, "--pieces", json.dumps(parts), "--lang", lang] + (["--beams", str(cfg["num_beams"])] if cfg.get("num_beams") else [])
                         + (["--revision", cfg["model_revision"]] if cfg.get("model_revision") else []) + (["--base-revision", cfg["base_config_revision"]] if cfg.get("base_config_revision") else []),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    last = None; limit = float(cfg.get("memory_limit_gb", 0) or 0); stop = {}
    if limit:   # M4: watch the worker's physical footprint (includes Mac GPU memory, which ps RSS misses); stop it above the limit
        import threading, re as _re
        def watch():
            while p.poll() is None:
                L = subprocess.run(["top", "-l", "1", "-pid", str(p.pid), "-stats", "mem"], capture_output=True, text=True).stdout.splitlines()
                k = next((i for i, x in enumerate(L) if x.strip() == "MEM"), None)   # only the value row under the MEM header counts
                m = _re.fullmatch(r"([\d.]+)([KMG])[+-]?", L[k + 1].strip()) if k is not None and k + 1 < len(L) else None
                gb = float(m.group(1)) * {"K": 1e-6, "M": 1e-3, "G": 1}[m.group(2)] if m else 0; stop["peak"] = max(stop.get("peak", 0), gb)
                if gb > limit: stop["gb"] = gb; p.kill(); return
                time.sleep(2)
        threading.Thread(target=watch, daemon=True).start()
    for line in p.stdout:
        line = line.strip()
        if not line.startswith("{"): continue
        d = json.loads(line)
        if "progress" in d: progress(5 + d["progress"] * 90, "transcribing")
        else: last = d
    err = p.stderr.read(); p.wait()
    if stop.get("gb"): fail("ASR_MEMORY_LIMIT", f"stopped speech-to-text at {stop['gb']:.1f} GB (limit {limit:.0f} GB) so the Mac does not run out of memory")
    if p.returncode or last is None: fail("ASR_FAILED", f"speech-to-text failed: {err[-800:]}")
    return last["words"], f"{cfg['model']} ({last.get('device')})"

def whisper_cpp(cfg, wav, parts, lang):
    exe = subprocess.run(["which", "whisper-cli"], capture_output=True, text=True).stdout.strip()
    model = os.path.expanduser(cfg["model"])
    if not exe: fail("ASR_MISSING", "whisper-cli not found (brew install whisper-cpp)")
    if not os.path.exists(model): fail("MODEL_MISSING", f"missing model file {model}")
    T = tmpdir(); words = []
    for k, (a, b) in enumerate(parts):
        f = os.path.join(T, f"piece{k}.wav")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-ss", f"{a:.3f}", "-to", f"{b:.3f}", f], check=True)
        base = os.path.join(T, f"piece{k}")
        r = subprocess.run([exe, "-m", model, "-l", lang, "-f", f, "-ml", "1", "-sow", "-oj", "-of", base, "-np"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode: fail("ASR_FAILED", f"whisper.cpp failed: {r.stderr[-600:]}")
        for seg in json.load(open(base + ".json", encoding="utf-8", errors="replace")).get("transcription", []):
            w = seg.get("text", "").strip(); o = seg.get("offsets", {})
            if w: words.append(dict(w=w, s=round(a + o.get("from", 0) / 1000, 3), e=round(a + o.get("to", 0) / 1000, 3)))
        progress(5 + (k + 1) / len(parts) * 90, "transcribing")
    return words, os.path.basename(model)

def norm(w): return re.sub(r"[\"'“”‘’.,!?;:()\[\]{}…\-–—|।‌‍]", "", unicodedata.normalize("NFC", w)).lower()
def mark(words, lang):
    """The tool's own doubts. Numbers get hl=true (highlighted in captions)."""
    for i, x in enumerate(words):
        r, n = [], norm(x["w"])
        if i and n and n == norm(words[i - 1]["w"]): r.append("repeated word")
        if i >= 3 and n and (n, norm(words[i - 1]["w"])) == (norm(words[i - 2]["w"]), norm(words[i - 3]["w"])): r.append("repeated phrase")
        letters = [c for c in x["w"] if c.isalpha()]
        if lang == "te" and letters and not any('ఀ' <= c <= '౿' for c in letters): r.append("not in Telugu script")
        d = x["e"] - x["s"]
        if d < 0.05 or d > 2.0: r.append("odd timing")
        x["hl"] = bool(re.search(r"\d", x["w"])); x["review"] = r
    return words

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--project"); ap.add_argument("--source"); ap.add_argument("--audio")
    ap.add_argument("--ss", type=float); ap.add_argument("--t", type=float); ap.add_argument("--lang"); ap.add_argument("--out")
    ap.add_argument("--words-out", action="store_true"); A = ap.parse_args(); t0 = time.time()
    j = c = None
    if A.project:
        j, c = job(A.project); b = os.path.join(j["_dir"], "build")
        src = A.audio or A.source or (os.path.join(j["_dir"], j["video"]) if j.get("video") else None)
        if not src: fail("NO_SOURCE", "no source: set project.json video or pass --source")
        lang = A.lang or c.get("language", "en"); out = A.out or os.path.join(b, "transcript.json")
    else:
        if not A.audio: fail("NO_SOURCE", "pass --project or --audio")
        src, lang, out = A.audio, A.lang or CFG.get("default", "en"), A.out or os.path.splitext(A.audio)[0] + "_transcript.json"
    if not os.path.exists(src): fail("FILE_NOT_FOUND", f"not found: {src}")
    cfg = CFG.get(lang) or CFG["en"]
    wav = to_wav(src, os.path.join(tmpdir(), "speech16k.wav"), A.ss, A.t); progress(3, "audio ready")
    parts, dur = pieces(wav, *cfg.get("piece_seconds", [8, 15]))
    words, model = (hf if cfg["engine"] == "hf" else whisper_cpp)(cfg, wav, parts, lang)
    if A.ss: words = [dict(x, s=round(x["s"] + A.ss, 3), e=round(x["e"] + A.ss, 3)) for x in words]
    words = mark(words, lang)
    res = dict(lang=lang, engine=cfg["engine"], model=model, source=src, ss=A.ss or 0, seconds=round(dur, 2), pieces=parts,
               words=words, review_count=sum(bool(x["review"]) for x in words), time_s=round(time.time() - t0, 1))
    save(res, out)
    if A.words_out and j:
        save([dict(w=x["w"], s=x["s"], e=x["e"], hl=x["hl"]) for x in words], os.path.join(j["_dir"], "build", "words.json"))
    progress(100); emit("output", path=out)
    print(f"transcribe -> {out} | {lang} | {model} | {len(words)} words, {res['review_count']} marked for review | {res['time_s']} s for {dur:.1f} s of audio")

if __name__ == "__main__":
    main()
