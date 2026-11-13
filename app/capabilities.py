"""M7-B B4C-3: what this build can really do right now, as facts.

Each capability gets seven separate answers instead of one "ready" light:
  installed, configured, available, qualified, running, failed, unsupported  (plus off = switched off by configuration)
Facts come from this Mac only: providers.json, whether the local model server answers on localhost and which models it
lists, whether a key is present in the environment (never its value), and whether the local tool environments exist.
Nothing is sent online, no paid provider is called, and no model is started by asking.

"Qualified" is per use, taken from the project's own records: the local model drives the M4 reel planner, and Codex's
qualification of the same model for poster concepts ended NO-GO (m5/docs/CREATIVE_DIRECTOR_PHASE2C.md). One never implies the other.
"""
import json, os, time, urllib.request
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
QUALIFIED = {   # use -> (answer, where that answer is recorded)
    "reel.plan.local": ("yes", "Used by the M4 reel workflow (docs/M4_COMPLETION_REPORT.md)"),
    "poster.concepts.ai": ("no", "Qualification ended NO-GO (m5/docs/CREATIVE_DIRECTOR_PHASE2C.md)"),
}


def probe(cfg, jobs=None, timeout=3):
    """Read-only look at this Mac. Local HTTP only (the model server's own address from providers.json)."""
    local = cfg["providers"].get("local", {}); url = local.get("url", "http://localhost:11434")
    out = dict(reachable=False, error=None, models=[], loaded=[])
    if not url.startswith(("http://localhost", "http://127.0.0.1")): out["error"] = "the local model address is not on this Mac; not contacted"
    else:
        try:
            out["models"] = [m["name"] for m in json.loads(urllib.request.urlopen(url + "/api/tags", timeout=timeout).read())["models"]]; out["reachable"] = True
            try: out["loaded"] = [m["name"] for m in json.loads(urllib.request.urlopen(url + "/api/ps", timeout=timeout).read()).get("models", [])]
            except Exception: out["loaded"] = []
        except Exception as e: out["error"] = f"the local model server did not answer ({type(e).__name__})"
    out["keys"] = {name: bool(os.environ.get(c["key_env"])) for name, c in cfg["providers"].items() if c.get("key_env")}
    out["asr_env"] = os.path.exists(os.path.expanduser("~/.venvs/rs_asr/bin/python")); out["tts_env"] = os.path.exists(os.path.expanduser("~/.venvs/rs_tts/bin/python"))
    out["planner_running"] = any(J.get("action") in ("plan", "hook") and J.get("status") == "running" for J in (jobs or {}).values())
    return out


def _cap(id, label, runner, detail, installed=None, configured=None, available=False, qualified="not-assessed", running=False, failed=False, unsupported=False, off=False, source=None):
    return dict(id=id, label=label, runner=runner, detail=detail, installed=installed, configured=configured, available=available, qualified=qualified,
                running=running, failed=failed, unsupported=unsupported, off=off, source=source)


def build(cfg, p):
    """Turn the facts into the capability list. Pure: the tests call it with made-up facts."""
    local = cfg["providers"].get("local", {}); want = [m for m in (local.get("model"), local.get("fallback_model")) if m]
    have = [m for m in want if m in p["models"]]; default_local = cfg.get("default") == "local"
    rules = dict(installed=True, configured=True, available=True, qualified="yes", source="Fixed rules in this build, covered by its tests")
    caps = [
        _cap("intent.rules", "Reading your prompt", "rules", "Fixed rules pick out what you typed. No AI model reads the prompt.", **rules),
        _cap("poster.concepts.rules", "Three poster concepts", "rules", "Arranged by layout rules on this Mac.", **rules),
        _cap("poster.edit-export", "Poster editing, QA and SVG/PNG export", "rules", "Telugu and English with pinned fonts.", **rules),
        _cap("reel.plan.local", "Reel planning with the local model", "local-model",
             (f"{have[0]} on this Mac" if have else f"needs {' or '.join(want)}" if p["reachable"] else p["error"] or "the local model server was not checked"),
             installed=bool(have) if p["reachable"] else None, configured=default_local, available=p["reachable"] and bool(have) and default_local,
             qualified=QUALIFIED["reel.plan.local"][0], source=QUALIFIED["reel.plan.local"][1],
             running=p["planner_running"] or any(m in p["loaded"] for m in want), failed=not p["reachable"]),
        _cap("reel.speech", "Speech to text for reels", "local-model", "Local speech environment (rs_asr)." if p["asr_env"] else "The local speech environment (rs_asr) is not set up.",
             installed=p["asr_env"], configured=p["asr_env"], available=p["asr_env"], source="Presence of the environment only; it is not started to check it"),
        _cap("reel.voice", "AI narration voice for reels", "local-model", "Local voice environment (rs_tts)." if p["tts_env"] else "The local voice environment (rs_tts) is not set up.",
             installed=p["tts_env"], configured=p["tts_env"], available=p["tts_env"], source="Presence of the environment only; it is not started to check it"),
        _cap("poster.concepts.ai", "AI poster concepts", "local-model", "The local model is not qualified for posters, even where it is installed for reels.",
             installed=bool(have) if p["reachable"] else None, configured=False, available=False, qualified=QUALIFIED["poster.concepts.ai"][0], source=QUALIFIED["poster.concepts.ai"][1]),
        _cap("language.translation", "Translation", "none", "Not in this build. Text is used exactly as you type it.", unsupported=True),
        _cap("media.generated-images", "Generated pictures", "none", "Not in this build. Posters are built from text and shapes.", unsupported=True),
        _cap("provider.web-bridge", "Web Bridge", "none", "Not built. Nothing is sent online.", unsupported=True),
    ]
    for name, c in cfg["providers"].items():
        if name == "local": continue
        enabled = c.get("enabled") is not False; key = p["keys"].get(name, False)
        caps.append(_cap(f"provider.{name}", c.get("name", name), "online",
                         "Switched off in providers.json. Never called." if not enabled else "Enabled, but no key in the environment." if not key else "Enabled with a key. Used only for reel planning, only when you choose it there.",
                         installed=None, configured=key, available=enabled and key, off=not enabled, source="providers.json and the environment; no request is sent to check it"))
    return dict(checked=time.strftime("%Y-%m-%d %H:%M:%S"), default=cfg.get("default"),
                local=dict(reachable=p["reachable"], error=p["error"], models=p["models"], loaded=p["loaded"], wanted=want), capabilities=caps)


def install(app, jobs):
    cfg_path = WORKSPACE / "providers.json"
    @app.get("/api/capabilities")
    def capabilities():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        return build(cfg, probe(cfg, jobs))
