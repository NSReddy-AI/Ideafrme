"""AI providers for the planner: local (Ollama + Qwen3, default, free) and optional Claude, Gemini, ChatGPT.
Keys are read from environment variables only (never from files):
  ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY
Models and the default provider are in providers.json (repo root)."""
import os, json, urllib.request, urllib.error
from common import ROOT, load
CFG = load(os.path.join(ROOT, "providers.json"))
def status():
    """Which providers can be used right now (local = Ollama answering on this Mac; others = key present)."""
    out = {}
    for p, c in CFG["providers"].items():
        if p == "local":
            try: urllib.request.urlopen(c.get("url", "http://localhost:11434") + "/api/tags", timeout=3); out[p] = True
            except Exception: out[p] = False
        else: out[p] = c.get("enabled") is not False and bool(os.environ.get(c["key_env"]))
    return out
def local_models():
    c = CFG["providers"]["local"]
    try: return [m["name"] for m in json.loads(urllib.request.urlopen(c.get("url", "http://localhost:11434") + "/api/tags", timeout=5).read())["models"]]
    except Exception: return []
def ask(prompt, system="", provider=None, images=None, max_tokens=4000, model=None, json_schema=None, temperature=0.4):
    """Send a text prompt (optionally with image file paths) and return the reply text.
    provider 'local' = Ollama on this Mac (default, free); json_schema makes the local model answer in that exact JSON shape."""
    p = provider or CFG["default"]; c = CFG["providers"][p]
    if c.get("enabled") is False: raise RuntimeError(f"{p} is switched off in providers.json (enabled: false) - no paid models are used")
    if p == "local":
        body = {"model": model or c["model"], "stream": False, "think": False, "options": {"temperature": temperature, "num_predict": max_tokens},
                "messages": ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]}
        if json_schema: body["format"] = json_schema
        r = _post(c.get("url", "http://localhost:11434") + "/api/chat", body, {}, timeout=900)
        return r["message"]["content"]
    key = os.environ.get(c["key_env"])
    if not key: raise RuntimeError(f"{p}: set {c['key_env']} in your shell (not in a file)")
    import base64, mimetypes
    imgs = [(mimetypes.guess_type(f)[0] or "image/png", base64.b64encode(open(f, "rb").read()).decode()) for f in (images or [])]
    if p == "claude":
        content = [{"type": "image", "source": {"type": "base64", "media_type": m, "data": d}} for m, d in imgs] + [{"type": "text", "text": prompt}]
        body = {"model": model or c["model"], "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": content}]}
        r = _post("https://api.anthropic.com/v1/messages", body, {"x-api-key": key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r["content"])
    if p == "gemini":
        parts = [{"inline_data": {"mime_type": m, "data": d}} for m, d in imgs] + [{"text": prompt}]
        body = {"contents": [{"parts": parts}], "generationConfig": {"maxOutputTokens": max_tokens}}
        if system: body["system_instruction"] = {"parts": [{"text": system}]}
        r = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{(model or c['model'])}:generateContent", body, {"x-goog-api-key": key})
        cand = (r.get("candidates") or [{}])[0]; parts = cand.get("content", {}).get("parts") or []
        if not parts: raise RuntimeError(f"Gemini gave no text (finish: {cand.get('finishReason')}, block: {r.get('promptFeedback', {}).get('blockReason')})")
        return "".join(x.get("text", "") for x in parts if not x.get("thought"))
    if p == "openai":
        content = [{"type": "input_image", "image_url": f"data:{m};base64,{d}"} for m, d in imgs] + [{"type": "input_text", "text": prompt}]
        body = {"model": model or c["model"], "input": [{"role": "system", "content": system}] * bool(system) + [{"role": "user", "content": content}], "max_output_tokens": max_tokens}
        r = _post("https://api.openai.com/v1/responses", body, {"Authorization": f"Bearer {key}"})
        return r.get("output_text") or "".join(cc.get("text", "") for o in r.get("output", []) for cc in o.get("content", []) if isinstance(cc, dict))
    raise ValueError(f"unknown provider {p}")
def _post(url, body, headers, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:   # show the provider's own message (429 = free daily/minute limit reached)
        msg = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"HTTP {e.code}{' (limit reached - try again later)' if e.code == 429 else ''}: {msg}") from None
