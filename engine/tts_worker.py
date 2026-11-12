"""Text-to-speech worker for Indic Parler-TTS (M4 B1). Runs ONLY in the separate voice Python (~/.venvs/rs_tts, Lock B.1),
started by engine/narrate.py - never imported by Reel Studio's own Python. Works offline: Hugging Face offline mode is on and
every outside network connection is blocked inside this process. Loads the model ONCE, then speaks the sentences one after
another (never in parallel). Each finished sentence is written to its own file at once (temp file + rename), so a stop
part-way keeps the finished ones.
Usage: python tts_worker.py --config tts.json --jobs jobs.json
  jobs.json = [{"id": "...", "say": "spoken Telugu", "description": "Prakash speaks ...", "out": "/abs/path.wav"}, ...]
Prints one JSON object per line: {"event":"loaded"...} {"event":"sentence"...} ... {"event":"result"...}
or {"event":"error","code":"TTS_MODEL_MISSING|TTS_NETWORK_BLOCKED|TTS_FAILED","message":...} with exit code 3."""
import os, sys, json, time, argparse, socket, resource, platform

os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1"); os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1"); os.environ.pop("HF_TOKEN", None)
_real_connect = socket.socket.connect
def _guard(self, addr):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in ("127.0.0.1", "::1", "localhost"): raise ConnectionRefusedError(f"BLOCKED network attempt to {host} (narration is offline)")
    return _real_connect(self, addr)
socket.socket.connect = _guard

def say(**kw): sys.stdout.write(json.dumps(kw, ensure_ascii=False) + "\n"); sys.stdout.flush()
def peak_bytes():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r if platform.system() == "Darwin" else r * 1024   # macOS reports bytes, Linux kilobytes
def stop(code, message): say(event="error", code=code, message=message[-1500:]); sys.exit(3)

ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--jobs", required=True); A = ap.parse_args()
cfg = json.load(open(A.config, encoding="utf-8")); jobs = json.load(open(A.jobs, encoding="utf-8"))
os.environ["HF_HOME"] = os.path.expanduser(cfg["hf_home"])
t0 = time.time()
try:
    import torch, soundfile
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
    torch.set_grad_enabled(False)
    model = ParlerTTSForConditionalGeneration.from_pretrained(cfg["model"], revision=cfg["model_revision"]).to(cfg.get("device", "cpu")).eval()
    tok = AutoTokenizer.from_pretrained(cfg["model"], revision=cfg["model_revision"])
    dtok = AutoTokenizer.from_pretrained(cfg["description_tokenizer"], revision=cfg["description_tokenizer_revision"])
except OSError as e:
    stop("TTS_MODEL_MISSING", f"voice model files not found in {cfg['hf_home']} at the pinned revision: {type(e).__name__}: {str(e)[:400]}")
except Exception as e:
    stop("TTS_NETWORK_BLOCKED" if "BLOCKED network" in str(e) else "TTS_FAILED", f"loading the voice model failed: {type(e).__name__}: {str(e)[:600]}")
sr = model.config.sampling_rate
say(event="loaded", load_s=round(time.time() - t0, 1), sampling_rate=sr, rss_peak_bytes=peak_bytes(), device=cfg.get("device", "cpu"))
for k, jb in enumerate(jobs):
    t1 = time.time()
    try:
        torch.manual_seed(int(cfg.get("seed", 1234)))
        d = dtok(jb["description"], return_tensors="pt"); p = tok(jb["say"], return_tensors="pt")
        g = model.generate(input_ids=d.input_ids, attention_mask=d.attention_mask, prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
        a = g.cpu().numpy().squeeze()
        tmp = jb["out"] + ".part.wav"; soundfile.write(tmp, a, sr, subtype="PCM_16"); os.replace(tmp, jb["out"])
    except Exception as e:
        stop("TTS_NETWORK_BLOCKED" if "BLOCKED network" in str(e) else "TTS_FAILED", f"sentence {jb['id']}: {type(e).__name__}: {str(e)[:600]}")
    say(event="sentence", id=jb["id"], n=k + 1, of=len(jobs), audio_s=round(len(a) / sr, 2), synth_s=round(time.time() - t1, 1), rss_peak_bytes=peak_bytes())
say(event="result", sentences=len(jobs), sampling_rate=sr, peak_rss_bytes=peak_bytes(), total_s=round(time.time() - t0, 1))
