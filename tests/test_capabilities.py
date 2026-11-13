"""M7-B B4C-3: capability facts (app/capabilities.py). build() is given made-up facts; nothing is contacted.
Run from the M6 folder:  ~/.venvs/reelstudio/bin/python -B tests/test_capabilities.py"""
import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import capabilities as C

CFG = json.loads((ROOT / "providers.json").read_text(encoding="utf-8"))
def facts(**k): return dict(dict(reachable=True, error=None, models=["qwen3:8b"], loaded=[], keys={"claude": False, "gemini": False, "openai": False}, asr_env=True, tts_env=True, planner_running=False), **k)
def cap(report, id): return next(c for c in report["capabilities"] if c["id"] == id)


class CapabilityTest(unittest.TestCase):
    def test_installed_model_is_not_qualified_for_posters(self):
        r = C.build(CFG, facts())
        plan, poster = cap(r, "reel.plan.local"), cap(r, "poster.concepts.ai")
        self.assertEqual((plan["installed"], plan["available"], plan["qualified"], plan["failed"]), (True, True, "yes", False))
        self.assertEqual((poster["installed"], poster["available"], poster["qualified"]), (True, False, "no"), "working for reels never makes it ready for posters")
        self.assertIn("NO-GO", poster["source"])

    def test_local_server_down_is_failed_not_ready(self):
        r = C.build(CFG, facts(reachable=False, models=[], error="the local model server did not answer (URLError)"))
        plan = cap(r, "reel.plan.local")
        self.assertEqual((plan["failed"], plan["available"], plan["installed"]), (True, False, None)); self.assertIn("did not answer", plan["detail"])
        self.assertTrue(cap(r, "intent.rules")["available"], "rule-based work does not depend on the model")

    def test_model_missing(self):
        plan = cap(C.build(CFG, facts(models=["gemma2:9b"])), "reel.plan.local")
        self.assertEqual((plan["installed"], plan["available"], plan["failed"]), (False, False, False)); self.assertIn("needs", plan["detail"])

    def test_running_is_separate(self):
        self.assertTrue(cap(C.build(CFG, facts(loaded=["qwen3:8b"])), "reel.plan.local")["running"])
        self.assertTrue(cap(C.build(CFG, facts(planner_running=True)), "reel.plan.local")["running"])
        self.assertFalse(cap(C.build(CFG, facts()), "reel.plan.local")["running"])

    def test_paid_providers_stay_off(self):
        r = C.build(CFG, facts(keys={"claude": True, "gemini": True, "openai": True}))
        for name in ("claude", "gemini", "openai"):
            c = cap(r, f"provider.{name}"); self.assertEqual((c["off"], c["available"], c["configured"]), (True, False, True), "a key alone never switches a paid provider on")
        on = json.loads(json.dumps(CFG)); on["providers"]["claude"]["enabled"] = True
        self.assertEqual([(c["off"], c["available"]) for c in [cap(C.build(on, facts()), "provider.claude")]], [(False, False)], "enabled without a key is not available")
        self.assertEqual(cap(C.build(on, facts(keys={"claude": True})), "provider.claude")["available"], True)

    def test_unsupported_and_tools(self):
        r = C.build(CFG, facts(asr_env=False))
        for id in ("language.translation", "media.generated-images", "provider.web-bridge"):
            c = cap(r, id); self.assertEqual((c["unsupported"], c["available"]), (True, False))
        self.assertEqual((cap(r, "reel.speech")["available"], cap(r, "reel.voice")["available"]), (False, True))
        self.assertEqual(r["default"], "local"); self.assertNotIn("key", json.dumps(r["local"]))

    def test_probe_refuses_a_remote_address_and_never_returns_a_key(self):
        cfg = json.loads(json.dumps(CFG)); cfg["providers"]["local"]["url"] = "http://example.invalid:11434"
        p = C.probe(cfg, {}, timeout=1); self.assertEqual((p["reachable"], p["models"]), (False, [])); self.assertIn("not on this Mac", p["error"])
        self.assertTrue(all(isinstance(v, bool) for v in p["keys"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=1)
