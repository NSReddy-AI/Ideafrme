"""Narration audio for a project (M4 B1): AI voice (Indic Parler-TTS, offline) or the user's own recording.
Usage: python narrate.py <project>
project.json: narration = "ai" | "recorded" | "none"; narrator = "prakash" | "lalitha" (ai); narrator_style = "news" | "documentary";
              narration_speed = 1.0 .. 1.2 (ai only; default from engine/tts.json, 1.0); narration_file = "inputs/....wav" (recorded)
Needs an APPROVED narration script (narration_script.py approve). Writes:
  build/narration.wav            the narration (44.1 kHz mono, 16-bit) on the EDIT timeline (starts at 0)
  build/narration_timeline.json  where each sentence starts/ends + fingerprints (approved text, audio) + memory + timings
  build/narration_cache/         one file per spoken sentence (AI); a re-run only speaks sentences that changed
AI path: one heavy model at a time (common.heavy_lock) and any model the local Ollama server holds is unloaded first; the voice
model runs in its own Python (tts.json "python"), sentences one after another, in a fresh process every memory.restart_every
sentences (default 5, B1.2) so memory does not build up over a long script; its memory is watched: warning at warn_gb, stopped
at limit_gb (TTS_MEMORY_LIMIT). Speed changes the speech only (pitch kept, FFmpeg rubberband); pauses between sentences are added
afterwards at the style's fixed length, so they are the same at every speed. Errors are clear codes, never a crash."""
import sys, os, json, time, hashlib, subprocess, threading, queue, wave, urllib.request, shutil
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import narration_script as NS

CFG_PATH = os.environ.get("RS_TTS_CONFIG") or os.path.join(ENGINE, "tts.json")

def read_wav(p):
    with wave.open(p) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes(); b = w.readframes(n)
    if sw != 2: fail("NARRATION_AUDIO_FORMAT", f"{p}: expected 16-bit wav")
    x = np.frombuffer(b, np.int16).astype(np.float32) / 32768
    return (x.reshape(-1, ch).mean(axis=1) if ch > 1 else x), sr

def write_wav(p, x, sr):
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def trim(x, sr, db, margin=0.03):
    """Cut the silence the model leaves before and after a sentence (so pauses are set by us, not by chance)."""
    idx = np.where(np.abs(x) > 10 ** (db / 20))[0]
    if not len(idx): return x[:0]
    m = int(margin * sr); return x[max(0, idx[0] - m): min(len(x), idx[-1] + m + 1)]

_FILTERS = {}
def filter_available(name):
    """Is this FFmpeg filter built into the FFmpeg on this machine? (Homebrew's ffmpeg may not include rubberband.)"""
    if name not in _FILTERS:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        _FILTERS[name] = any(len(l.split()) > 1 and l.split()[1] == name for l in out.splitlines())
    return _FILTERS[name]

def stretch(x, sr, speed, method, T, tag):
    """Faster speech with the same pitch (rubberband) - or atempo for comparison. 1.0 = untouched."""
    if abs(speed - 1.0) < 1e-6: return x
    a, b = os.path.join(T, f"{tag}_in.wav"), os.path.join(T, f"{tag}_out.wav"); write_wav(a, x, sr)
    af = f"rubberband=tempo={speed}:pitchq=quality" if method == "rubberband" else f"atempo={speed}"
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af", af, "-ar", str(sr), "-ac", "1", "-c:a", "pcm_s16le", b], code="NARRATION_SPEED_FAILED")
    return read_wav(b)[0]

def rss_bytes(pid):
    """Return live worker RSS; raise if a running process cannot be measured."""
    if sys.platform == "darwin":
        import ctypes
        import ctypes.util

        class ProcTaskInfo(ctypes.Structure):
            _fields_ = [
                ("virtual", ctypes.c_uint64),
                ("resident", ctypes.c_uint64),
                ("total_user", ctypes.c_uint64),
                ("total_system", ctypes.c_uint64),
                ("threads_user", ctypes.c_uint64),
                ("threads_system", ctypes.c_uint64),
            ] + [(f"field_{i}", ctypes.c_int32) for i in range(12)]

        libpath = ctypes.util.find_library("proc")
        if not libpath:
            raise RuntimeError("macOS libproc unavailable")
        lib = ctypes.CDLL(libpath, use_errno=True)
        lib.proc_pidinfo.argtypes = [
            ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
            ctypes.c_void_p, ctypes.c_int
        ]
        lib.proc_pidinfo.restype = ctypes.c_int
        info = ProcTaskInfo()
        result = lib.proc_pidinfo(
            pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info)
        )
        if result != ctypes.sizeof(info):
            raise RuntimeError(
                f"proc_pidinfo returned {result}/{ctypes.sizeof(info)} bytes"
            )
        return info.resident

    result = subprocess.run(
        ["ps", "-o", "rss=", "-p", str(pid)],
        capture_output=True, text=True, timeout=5, check=True
    )
    value = result.stdout.strip()
    if not value:
        raise RuntimeError("ps returned no RSS measurement")
    return int(value) * 1024

def worker_rss(p):
    """Allow a just-exited worker to be reaped before declaring monitor failure.

    macOS can remove proc_pidinfo before waitpid observes exit. A live worker
    still fails closed after this bounded grace period; no zero-RSS fallback.
    """
    try:
        return rss_bytes(p.pid)
    except (OSError, RuntimeError, ValueError):
        try:
            p.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            raise RuntimeError("cannot measure live voice worker memory")
        return 0


def unload_ollama():
    """Free the memory a local Ollama model may still hold (local server only). Not running = nothing to do."""
    url = "http://localhost:11434"
    try: url = load(os.path.join(ROOT, "providers.json"))["providers"]["local"].get("url", url)
    except Exception: pass
    if not url.startswith(("http://localhost", "http://127.0.0.1")): return dict(status="skipped (not a local server)")
    try: models = [m["name"] for m in json.loads(urllib.request.urlopen(url + "/api/ps", timeout=3).read()).get("models", [])]
    except Exception: return dict(status="not running")
    done = []
    for m in models:
        try:
            urllib.request.urlopen(urllib.request.Request(url + "/api/generate", data=json.dumps(dict(model=m, keep_alive=0)).encode(),
                                                          headers={"Content-Type": "application/json"}), timeout=30).read(); done.append(m)
        except Exception as e: emit("warning", code="OLLAMA_UNLOAD_FAILED", message=f"could not unload {m}: {e}")
    return dict(status="ok", unloaded=done)

def model_present(C):
    hub = os.path.join(os.path.expanduser(C["hf_home"]), "hub")
    need = C.get("model_check") or [
        os.path.join(hub, "models--" + C["model"].replace("/", "--"), "snapshots", C["model_revision"], "model.safetensors"),
        os.path.join(hub, "models--" + C["description_tokenizer"].replace("/", "--"), "snapshots", C["description_tokenizer_revision"], "spiece.model")]
    return [p for p in need if not os.path.exists(os.path.expanduser(p))]

def description(C, voice, style): return f"{C['voices'][voice]} {C['styles'][style]['description']}{C.get('quality', '')}"

def cache_key(C, desc, text):
    return hashlib.sha256(json.dumps([C["engine"], C["model"], C["model_revision"], C["description_tokenizer_revision"], desc,
                                      int(C.get("seed", 1234)), C.get("device", "cpu"), text], ensure_ascii=False).encode()).hexdigest()[:24]

def synthesize(C, lines, voice, style, cache, T):
    """Speak every sentence that is not cached yet; return (paths, stats)."""
    desc = description(C, voice, style); os.makedirs(cache, exist_ok=True)
    paths = [os.path.join(cache, cache_key(C, desc, l["say"]) + ".wav") for l in lines]
    need = [i for i, p in enumerate(paths) if not os.path.exists(p)]
    st = dict(spoken=len(need), cached=len(lines) - len(need), peak_rss_bytes=0, warned=False, load_s=None, sentences=[], description=desc)
    if not need: progress(80, "all sentences cached"); return paths, st
    py = os.path.expanduser(C["python"])
    if not os.path.exists(py): fail("TTS_ENV_MISSING", f"voice Python not found: {C['python']} (Gate A2.2 environment)")
    miss = model_present(C)
    if miss: fail("TTS_MODEL_MISSING", "voice model files missing: " + ", ".join(miss))
    worker = C.get("worker", "engine/tts_worker.py"); worker = worker if os.path.isabs(worker) else os.path.join(ROOT, worker)
    env = {k: v for k, v in os.environ.items() if k not in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "PYTHONPATH", "PYTHONHOME", "RS_EVENTS")}
    env.update(HF_HOME=os.path.expanduser(C["hf_home"]), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
               HF_HUB_DISABLE_TELEMETRY="1", PYTHONNOUSERSITE="1")
    M = C.get("memory", {}); warn, limit, poll = M.get("warn_gb", 7.5) * 1e9, M.get("limit_gb", 8.0) * 1e9, M.get("poll_s", 0.5)
    every = int(M.get("restart_every", 0) or 0) or len(need)   # B1.2: a fresh voice process every N sentences keeps memory from building up
    st.update(restart_every=every, batches=[]); done = 0
    for bi in range(0, len(need), every):
        chunk = need[bi: bi + every]; jf = os.path.join(T, f"tts_jobs_{bi}.json"); bpeak = 0
        save([dict(id=str(i), say=lines[i]["say"], description=desc, out=paths[i]) for i in chunk], jf)
        p = subprocess.Popen([py, worker, "--config", CFG_PATH, "--jobs", jf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=ROOT)
        q, errbuf = queue.Queue(), []
        threading.Thread(target=lambda p=p, q=q: [q.put(l) for l in p.stdout] + [q.put(None)], daemon=True).start()
        threading.Thread(target=lambda p=p, e=errbuf: e.extend(p.stderr.readlines()), daemon=True).start()
        err, killed, load_s = None, None, None
        while True:
            try:
                r = worker_rss(p)
            except (OSError, RuntimeError, ValueError) as exc:
                if p.poll() is None:
                    p.kill()
                    p.wait()
                    fail("TTS_MEMORY_MONITOR_FAILED", f"cannot monitor voice worker memory: {exc}")
                r = 0
            bpeak = max(bpeak, r)
            if r > warn and not st["warned"]:
                st["warned"] = True; emit("warning", code="TTS_MEMORY_HIGH", message=f"voice model is using {r / 1e9:.2f} GB (warning level {warn / 1e9:.1f} GB)")
            if r > limit and killed is None:
                p.kill(); killed = r
            try: line = q.get(timeout=poll)
            except queue.Empty:
                if p.poll() is not None and q.empty(): break
                continue
            if line is None: break
            line = line.strip()
            if not line.startswith("{"): continue
            try: ev = json.loads(line)
            except ValueError: continue
            if ev.get("event") == "error": err = ev
            elif ev.get("event") == "loaded":
                load_s = ev.get("load_s"); st["load_s"] = st["load_s"] or load_s; progress(15, "voice model loaded" + (f" (batch {bi // every + 1})" if every < len(need) else ""))
            elif ev.get("event") == "sentence":
                done += 1; st["sentences"].append(ev); progress(15 + 65 * done / len(need), f"sentence {done}/{len(need)}")
            bpeak = max(bpeak, int(ev.get("rss_peak_bytes") or ev.get("peak_rss_bytes") or 0))
        p.wait(); time.sleep(0.05)
        st["peak_rss_bytes"] = max(st["peak_rss_bytes"], bpeak)
        st["batches"].append(dict(sentences=len(chunk), peak_rss_gb=round(bpeak / 1e9, 3), load_s=load_s))
        if killed: fail("TTS_MEMORY_LIMIT", f"stopped the voice model at {killed / 1e9:.2f} GB (limit {limit / 1e9:.1f} GB); "
                                            f"{done} of {len(need)} sentences were finished and are kept in the cache")
        if err: fail(err.get("code", "TTS_FAILED"), err.get("message", "voice model failed"))
        if p.returncode: fail("TTS_FAILED", f"voice worker stopped (exit {p.returncode}): {''.join(errbuf)[-1200:]}")
    missing = [i for i in need if not os.path.exists(paths[i])]
    if missing: fail("TTS_FAILED", f"voice worker finished but sentences {missing} have no audio")
    return paths, st

def main(project):
    t0 = time.time(); j, c = job(project); b = os.path.join(j["_dir"], "build"); mode = j.get("narration")
    if mode in (None, "none"):
        print("narration: none -> text + music (nothing to do)"); emit("output", path=None, narration="none"); return
    if mode not in ("ai", "recorded"): fail("NARRATION_MODE_INVALID", f"narration must be ai, recorded or none (is '{mode}')")
    C = load(CFG_PATH); style = j.get("narrator_style")
    if style not in C["styles"]: fail("NARRATION_STYLE_INVALID", f"narrator_style must be one of {sorted(C['styles'])} (is '{style}')")
    ok, code, msg, N = NS.verify(j)
    if not ok: fail(code, msg)
    lines = N["lines"]; sr = int(C.get("sample_rate", 44100)); T = tmpdir()
    out, tl_path = os.path.join(b, "narration.wav"), os.path.join(b, "narration_timeline.json")
    TL = dict(mode=mode, style=style, approved_hash=N["approved_hash"], sample_rate=sr, created=time.strftime("%Y-%m-%d %H:%M:%S"))
    if mode == "recorded":
        f = j.get("narration_file"); fp = f and (f if os.path.isabs(f) else os.path.join(j["_dir"], f))
        if not fp or not os.path.exists(fp): fail("NARRATION_FILE_MISSING", f"recorded narration file not found: {f}")
        if float(j.get("narration_speed", 1.0)) != 1.0: emit("warning", code="SPEED_IGNORED", message="speed applies to AI narration only; the recording is used as it is")
        progress(10, "reading the recording")
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", fp, "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", out], code="NARRATION_FILE_UNREADABLE")
        x, _ = read_wav(out)
        TL.update(voice="recorded", speed=1.0, source=os.path.relpath(fp, j["_dir"]), source_sha256=sha_file(fp), duration=round(len(x) / sr, 3),
                  aligned=False, sentences=[dict(i=i, text=l["text"], say=l["say"], s=None, e=None) for i, l in enumerate(lines)],
                  note="sentence times come from narration_align.py (speech-to-text on the recording)")
    else:
        voice = j.get("narrator")
        if voice not in C["voices"]: fail("NARRATION_VOICE_INVALID", f"narrator must be one of {sorted(C['voices'])} (is '{voice}')")
        S = C["speed"]; speed = float(j.get("narration_speed", S["default"]))
        if not (S["min"] - 1e-9 <= speed <= S["max"] + 1e-9): fail("NARRATION_SPEED_INVALID", f"narration_speed must be {S['min']}..{S['max']} (is {speed})")
        method = j.get("narration_speed_method", S.get("method", "rubberband"))
        if method not in ("rubberband", "atempo"): fail("NARRATION_SPEED_INVALID", f"speed method must be rubberband or atempo (is '{method}')")
        if abs(speed - 1.0) > 1e-9 and not filter_available(method):
            fail("SPEED_METHOD_UNAVAILABLE", f"FFmpeg on this computer has no '{method}' filter, so speed {speed}x cannot be made with it. "
                                             f"Use speed 1.0, or choose another method (narration_speed_method), or add the filter (a new install - needs approval). Nothing was changed.")
        with heavy_lock("narration"):
            ol = unload_ollama() if not os.environ.get("RS_NO_OLLAMA_UNLOAD") else dict(status="skipped (test)")
            progress(5, "voice model starting")
            paths, st = synthesize(C, lines, voice, style, os.path.join(b, "narration_cache"), T)
        pause, lead, tail = C["styles"][style]["pause_s"], C.get("lead_s", 0.25), C.get("tail_s", 0.45)
        fade_n = int(round(float(C.get("edge_fade_ms", 0) or 0) * sr / 1000)); maxs = (C.get("sentence_limit") or {}).get("max_speech_s")
        parts, sents, t = [np.zeros(int(round(lead * sr)), np.float32)], [], lead; pos = len(parts[0])   # pos = exact sample position
        for i, (l, pth) in enumerate(zip(lines, paths)):
            x, r = read_wav(pth)
            if r != sr: fail("NARRATION_AUDIO_FORMAT", f"sentence {i + 1}: {r} Hz, expected {sr} Hz")
            raw_s = len(x) / sr; x = trim(x, sr, C.get("trim_db", -45))
            if not len(x): fail("TTS_SILENT", f"sentence {i + 1} came out silent - check its text")
            x = stretch(x, sr, speed, method, T, f"s{i}")
            if fade_n and len(x) > 4 * fade_n:   # raised-cosine fade inside the trim margin (the margin is 30 ms, the fade 10 ms)
                ramp = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade_n))).astype(np.float32); x = x.copy(); x[:fade_n] *= ramp; x[-fade_n:] *= ramp[::-1]
            sents.append(dict(i=i, text=l["text"], say=l["say"], s=round(t, 3), e=round(t + len(x) / sr, 3), s_sample=pos, e_sample=pos + len(x),
                              raw_audio_s=round(raw_s, 3), speech_s=round(len(x) / sr, 3)))
            if maxs and len(x) / sr > maxs:
                sents[-1]["long"] = True; emit("warning", code="LONG_SENTENCE", message=f"sentence {i + 1} is {len(x) / sr:.1f} s of speech (limit {maxs} s) - longer sentences need more memory")
            parts.append(x); t += len(x) / sr; pos += len(x)
            gap = pause if i + 1 < len(lines) else tail
            g = np.zeros(int(round(gap * sr)), np.float32); parts.append(g); t += len(g) / sr; pos += len(g)
        x = np.concatenate(parts)
        if np.max(np.abs(x)) > 0.98: x = x * (0.98 / np.max(np.abs(x)))   # never clip; loudness is set later by mix.py
        write_wav(out, x, sr)
        TL.update(voice=voice, speed=speed, speed_method=method, pause_s=pause, lead_s=lead, tail_s=tail, edge_fade_ms=C.get("edge_fade_ms", 0), samples=len(x),
                  duration=round(len(x) / sr, 3), aligned=True,
                  sentences=sents, model=C["model"], model_revision=C["model_revision"], description=st["description"],
                  generated=dict(spoken=st["spoken"], cached=st["cached"], load_s=st["load_s"], per_sentence=st["sentences"],
                                 restart_every=st.get("restart_every"), batches=st.get("batches", [])),
                  memory=dict(model_loaded=st["spoken"] > 0, peak_rss_gb=round(st["peak_rss_bytes"] / 1e9, 3) if st["spoken"] else None,
                              note=None if st["spoken"] else "model not loaded (every sentence came from the cache)",
                              warn_gb=C["memory"]["warn_gb"], limit_gb=C["memory"]["limit_gb"], warned=st["warned"]),
                  offline="HF_HUB_OFFLINE=1 + outside network blocked inside the voice process", ollama=ol)
    TL.update(audio_sha256=sha_file(out), time_s=round(time.time() - t0, 1)); save(TL, tl_path)
    import rs; rs.log(j, f"narration ({mode}{', ' + TL['voice'] + ' ' + style + ' ' + str(TL['speed']) + 'x' if mode == 'ai' else ''}) -> build/narration.wav {TL['duration']} s")
    progress(100); emit("output", path=out, timeline=tl_path, duration=TL["duration"])
    print(f"narration -> {out} | {mode} | {TL['duration']} s | " + (f"{TL['generated']['spoken']} spoken, {TL['generated']['cached']} cached, " + (f"peak {TL['memory']['peak_rss_gb']} GB" if TL['memory']['model_loaded'] else "model not loaded") if mode == "ai" else "recording"))

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1])
