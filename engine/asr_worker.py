"""Speech-to-text worker for Hugging Face Whisper models (e.g. the Telugu model). Runs in the separate ASR Python
(~/.venvs/rs_asr: transformers Apache-2.0 + torch BSD-3), started by engine/transcribe.py - never imported by Reel Studio's
own Python. Reads a 16 kHz mono wav and a list of [start, end] pieces; prints progress lines and finally one JSON line:
  {"words": [{"w": ..., "s": ..., "e": ...}, ...], "device": "mps"|"cpu", "model": ...}
Usage: python asr_worker.py --model vasista22/whisper-telugu-large-v2 --audio x.wav --pieces '[[0,12.9],...]' --lang te
M4 memory fix (11 Nov): the words come from the same decoding as before (5 beams, the transformers pipeline default the M3
accuracy test used), but word TIMES are measured afterwards in one pass over the chosen words ("forced", the method OpenAI's
Whisper uses: cross-attention of the alignment heads -> median filter -> DTW). Asking transformers for word times during a
5-beam search kept every attention map of every beam at every step: 18+ GB on a 24 GB Mac. --timing pipeline = the old way."""
import os, sys, json, wave, argparse, string, socket
# Offline, like the voice worker (Gate C, 11 Nov): use the local model cache only and refuse any outside connection.
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1"); os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1"); os.environ.pop("HF_TOKEN", None)
_real_connect = socket.socket.connect
def _guard(self, addr):
    host = addr[0] if isinstance(addr, tuple) else str(addr)
    if host not in ("127.0.0.1", "::1", "localhost"): raise ConnectionRefusedError(f"BLOCKED network attempt to {host} (speech-to-text is offline)")
    return _real_connect(self, addr)
socket.socket.connect = _guard
import numpy as np, torch
from transformers import pipeline, GenerationConfig

ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--audio", required=True)
ap.add_argument("--pieces", required=True); ap.add_argument("--lang", default="te"); ap.add_argument("--device", default="auto")
ap.add_argument("--beams", type=int, default=0)        # 0 = the pipeline default (5 beams); asr.json "num_beams" sets it
ap.add_argument("--timing", default="forced", choices=["forced", "pipeline"])
ap.add_argument("--revision", default=None)         # pinned model snapshot (asr.json model_revision) - reproducible results
ap.add_argument("--base-revision", default=None)    # pinned openai/whisper-* generation config (asr.json base_config_revision)
A = ap.parse_args(); pieces = json.loads(A.pieces)
with wave.open(A.audio) as w:
    sr = w.getframerate(); audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
if sr != 16000: sys.exit("audio must be 16 kHz mono")

def base_config(model_id):
    """Fine-tuned models often ship an old generation config (no language table, no alignment heads for word times):
    borrow the matching base Whisper config (MIT)."""
    size = next((s for s in ("large-v3", "large-v2", "large", "medium", "small", "base", "tiny") if s in model_id), "large-v2")
    return GenerationConfig.from_pretrained(f"openai/whisper-{size}", revision=A.base_revision)

def make(dev):
    p = pipeline("automatic-speech-recognition", model=A.model, revision=A.revision, device=dev)
    gc = p.model.generation_config
    if not getattr(gc, "alignment_heads", None) or not getattr(gc, "lang_to_id", None): p.model.generation_config = base_config(A.model)
    # The fine-tuned model ships use_cache=False (a training setting); the cache only skips repeated work.
    p.model.config.use_cache = True; p.model.generation_config.use_cache = True
    # Word times only need the decoder's cross-attention: never keep the encoder's attention maps (about 5.8 GB).
    enc = p.model.get_encoder(); fwd = enc.forward
    def enc_forward(*a, **k): k["output_attentions"] = False; return fwd(*a, **k)
    enc.forward = enc_forward
    return p

# CPU by default: on the Mac GPU the word-time step grew past 20 GB. "--device mps" still works when asked for explicitly.
dev = "cpu" if A.device == "auto" else A.device
try: P = make(dev)
except Exception: dev = "cpu"; P = make(dev)
TOK = P.tokenizer; EOT = TOK.convert_tokens_to_ids("<|endoftext|>")
# Telugu needs about 3 byte-tokens per letter: the pipeline's 256-token default cut 13 s pieces off mid-word. Use the model's own
# limit (448 positions minus the 4 start tokens).
MAXTOK = int(getattr(P.model.config, "max_target_positions", 448)) - 4

def pipeline_words(seg):
    gk = {"language": A.lang, "task": "transcribe"}
    if A.beams: gk["num_beams"] = A.beams
    out = P({"raw": seg, "sampling_rate": 16000}, return_timestamps="word", generate_kwargs=gk); res = []
    for c in out.get("chunks") or []:
        a, b = c.get("timestamp") or (None, None)
        res.append(((c.get("text") or ""), 0.0 if a is None else float(a), None if b is None else float(b)))
    return res

def dtw(x):
    """Cheapest monotonic path through the cost matrix (tokens x audio frames), as in OpenAI Whisper (MIT)."""
    N, M = x.shape; cost = np.full((N + 1, M + 1), np.inf, np.float32); cost[0, 0] = 0; trace = -np.ones((N + 1, M + 1), np.int8)
    for j in range(1, M + 1):
        c0, c1 = cost[:-1, j - 1], cost[:-1, j]
        for i in range(1, N + 1):
            a, b, c = c0[i - 1], c1[i - 1], cost[i, j - 1]
            if a <= b and a <= c: cost[i, j] = x[i - 1, j - 1] + a; trace[i, j] = 0
            elif b <= c: cost[i, j] = x[i - 1, j - 1] + b; trace[i, j] = 1
            else: cost[i, j] = x[i - 1, j - 1] + c; trace[i, j] = 2
    trace[0, :] = 2; trace[:, 0] = 1; i, j = N, M; path = []
    while i > 0 or j > 0:
        path.append((i - 1, j - 1)); t = trace[i, j]
        if t == 0: i -= 1; j -= 1
        elif t == 1: i -= 1
        else: j -= 1
    path = np.array(path[::-1]); return path[:, 0], path[:, 1]

def split_words(tokens):
    """Group text tokens into words: complete Unicode pieces first, then a new word at every leading space or punctuation."""
    units, cur = [], []
    for t in tokens:
        cur.append(t); d = TOK.decode(cur)
        if "�" not in d: units.append((d, cur)); cur = []
    if cur: units.append((TOK.decode(cur), cur))
    words = []
    for d, ts in units:
        if not words or d.startswith(" ") or d.strip() in string.punctuation: words.append([d, list(ts)])
        else: words[-1][0] += d; words[-1][1] += ts
    return [(w, len(ts)) for w, ts in words]

def forced_words(seg):
    M = P.model; gc = M.generation_config
    feats = P.feature_extractor(seg, sampling_rate=16000, return_tensors="pt").input_features.to(dev, M.dtype)
    with torch.inference_mode():
        ids = M.generate(feats, language=A.lang, task="transcribe", num_beams=A.beams or 5, max_new_tokens=MAXTOK)[0].tolist()
    text = [t for t in ids if t < EOT][:MAXTOK - 1]                      # the words only (special tokens are >= <|endoftext|>); room for the end
    if not text: return []
    sot = [gc.decoder_start_token_id, gc.lang_to_id[f"<|{A.lang}|>"], gc.task_to_id["transcribe"], gc.no_timestamps_token_id]
    dec = torch.tensor([sot + text + [EOT]], device=dev)
    impl = getattr(M.config, "_attn_implementation", None)
    try:
        if impl != "eager": M.set_attn_implementation("eager")           # attention weights need the plain implementation
        with torch.inference_mode(): out = M(input_features=feats, decoder_input_ids=dec, output_attentions=True, use_cache=False)
    finally:
        if impl and impl != "eager": M.set_attn_implementation(impl)
    nf = len(seg) // 320                                                 # 20 ms per audio position
    W = torch.stack([out.cross_attentions[l][0, h] for l, h in gc.alignment_heads]).float()[:, :, :nf]   # heads x tokens x frames
    W = (W - W.mean(dim=-2, keepdim=True)) / W.std(dim=-2, keepdim=True).clamp_min(1e-6)
    W = torch.nn.functional.pad(W, (3, 3), mode="reflect").unfold(-1, 7, 1).median(-1).values           # median filter, width 7
    Mx = W.mean(0)[len(sot) - 1:-1].numpy()                             # rows that predict each text token (+ end)
    ti, fi = dtw(-Mx.astype(np.float64))
    jumps = np.pad(np.diff(ti), (1, 0), constant_values=1).astype(bool); jt = fi[jumps] / 50.0
    res, k = [], 0
    for w, n in split_words(text):
        a = float(jt[min(k, len(jt) - 1)]); b = float(jt[min(k + n, len(jt) - 1)]); res.append((w, a, b)); k += n
    return res

words = []
for k, (s, e) in enumerate(pieces):
    seg = audio[int(s * 16000):int(e * 16000)]
    run = forced_words if A.timing == "forced" else pipeline_words
    try: out = run(seg)
    except Exception:
        if dev == "cpu": raise
        dev = "cpu"; del P; torch.mps.empty_cache(); P = make(dev); out = run(seg)   # free the GPU copy before loading the CPU one
    for w, a, b in out:
        w = w.replace("\ufffd", "").strip()                         # drop a broken byte-token the model may leave inside a word
        if not w: continue
        b = a + 0.3 if b is None else b
        words.append(dict(w=w, s=round(s + min(a, e - s), 3), e=round(s + min(max(b, a + 0.02), e - s), 3)))
    print(json.dumps({"progress": round((k + 1) / len(pieces), 3)}), flush=True)
print(json.dumps({"words": words, "device": dev, "model": A.model, "revision": A.revision, "timing": A.timing, "beams": A.beams or 5}, ensure_ascii=False), flush=True)
