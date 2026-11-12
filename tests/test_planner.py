"""Planner acceptance test (M4): both local models draft the plan for reel_002's Telugu news speech.
Run: ~/.venvs/reelstudio/bin/python tests/test_planner.py [--models qwen3:14b,qwen3:8b] [--provider claude] [--creative-provider claude]
The November approved title page is HELD OUT (the model never sees it) and printed for comparison.
Automatic pass rules (code, not the model): every number card spoken inside its beat with the same value + unit + claim,
card times taken from the spoken words, no number that is not spoken, quotes verbatim, 3 hook options, Telugu script.
Human check (you): are the three hooks natural Telugu, and how do they compare with the November direction?
Writes tests/out/planner_<model>.md and tests/out/planner_report.json."""
import os, sys, json, shutil, subprocess, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "tests", "out"); os.makedirs(OUT, exist_ok=True)
E = os.path.join(ROOT, "engine"); PY = sys.executable; say = lambda *a: print(*a, flush=True)
ap = argparse.ArgumentParser(); ap.add_argument("--models", default="qwen3:14b,qwen3:8b"); ap.add_argument("--provider", default="local")
ap.add_argument("--creative-provider", help="optional: hooks by claude|gemini|openai (facts stay local)"); ap.add_argument("--creative-model")
ap.add_argument("--record", help="save the results as an acceptance record in tests/acceptance/<RECORD>/"); A = ap.parse_args()
BASE = os.path.join(ROOT, "projects", "2026-11-03_reel_002_development"); T = "zz_plan_te"; d = os.path.join(ROOT, "projects", T)
os.makedirs(os.path.join(d, "build"), exist_ok=True); os.makedirs(os.path.join(d, "inputs"), exist_ok=True)
pj = json.load(open(os.path.join(BASE, "project.json"), encoding="utf-8")); human = dict(hook=pj["hook"], title=pj["title"])
pj.update(status="test", history=[], approved=False, hook={}, title=[])
json.dump(pj, open(os.path.join(d, "project.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(os.path.join(BASE, "build", "words.json"), os.path.join(d, "build", "words.json"))
open(os.path.join(d, "inputs", "notes.txt"), "w", encoding="utf-8").write("Reel: what Jagan did for Andhra Pradesh - development works, told with the numbers he speaks. Telugu political news channel.")
import hashlib
md5 = lambda f: hashlib.md5(open(f, "rb").read()).hexdigest()
WJ = os.path.join(d, "build", "words.json"); words_md5 = md5(WJ)
HOOK_D = "అసలు జగన్ ఏం చేశాడు? / 24 గంటలు సరిపోవు! / ఇదీ అభివృద్ధి! / జగన్ చేసిన పనులపై చర్చ / 24 గంటలు సరిపోవంటున్న వక్త"
def pl(*a): return subprocess.run([PY, os.path.join(E, "planner.py"), T] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
def render_codes():
    r = subprocess.run([PY, os.path.join(E, "adapter.py"), "render", T], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [json.loads(x).get("code") for x in r.stdout.splitlines() if x.startswith("{") and '"error"' in x]
R = dict(human_approved=human, runs=[]); allok = True
# 1. the offline regression suite (no model): every earlier check + the new tag / quote checks
off = subprocess.run([PY, os.path.join(ROOT, "tests", "test_plan_checks.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
open(os.path.join(OUT, "offline_checks.txt"), "w", encoding="utf-8").write(off.stdout + off.stderr)
npass, nfail = off.stdout.count("\nPASS ") + off.stdout.startswith("PASS "), off.stdout.count("FAIL ")
say(f"== offline regression suite: {npass} passed, {nfail} failed -> tests/out/offline_checks.txt"); allok &= off.returncode == 0 and nfail == 0
R["offline"] = dict(passed=npass, failed=nfail)
models = A.models.split(",") if A.provider == "local" else [None]
for m in models:
    args = [PY, os.path.join(E, "planner.py"), T, "--provider", A.provider, "--holdout", "reel_002"] + (["--model", m] if m else []) + (["--creative-provider", A.creative_provider] if A.creative_provider else []) + (["--creative-model", A.creative_model] if A.creative_model else [])
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    say(f"\n== {A.provider} {m or ''}:", (r.stdout.strip().splitlines() or [""])[-1] or r.stderr[-500:])
    if r.returncode: R["runs"].append(dict(model=m, error=(r.stderr or r.stdout)[-500:])); allok = False; continue
    P = json.load(open(os.path.join(d, "build", "plan.json"), encoding="utf-8")); tag = (m or A.provider).replace(":", "_") + (f"+{A.creative_model or A.creative_provider}" if A.creative_provider else "")
    shutil.copy(os.path.join(d, "build", "plan.md"), os.path.join(OUT, f"planner_{tag}.md"))
    cards = [b["graphic"] for b in P["facts"].get("beats", []) if b.get("graphic", {}).get("type") == "number"]
    synced = [g for g in cards if g.get("spoken")]; backup = P["meta"]["backup"]; cor = P["facts"].get("corrections", [])
    labels = [g.get("label", "") for g in cards] + [P["facts"].get("tag", {}).get("label", "")]
    if not backup:
        checks = {"no problems left (numbers, units, claims, quotes, script)": not P["issues"],
                  f"number cards synced to the spoken words ({len(synced)}/{len(cards)})": bool(cards) and len(synced) == len(cards),
                  "3 hook options": len(P["creative"].get("hooks", [])) == 3,
                  "tag is 'number — label' from a spoken number": "—" in P["facts"].get("tag", {}).get("text", "")}
    else:   # backup: it may fail, but nothing wrong may get through silently
        nprob = sum("card" in x for x in P["issues"])
        checks = {f"no wrong card accepted: {len(synced)} cards checked and in place, {nprob} card problem(s) block approval": len(synced) == len(cards) or nprob > 0,
                  f"moved cards have an audit trail ({len(cor)} moved)": all(k in m for m in cor for k in ("from_beat", "to_beat", "reason", "original_error")),
                  "moved cards need --checked (marked ❓)": sum("was moved" in x for x in P["flags"]) == len(cor),
                  "marked as backup, not for automatic publishing": P["meta"].get("auto_publish_allowed") is False}
    tg = P["facts"].get("tag") or {}
    checks[f"tag is an achievement or left out ({tg.get('text') or 'none'})"] = not any(w.startswith(("గంట", "నిమిష", "రోజు", "సంవత్సర")) for w in (tg.get("label") or "").split())
    qs = [h["line2"] for h in P["creative"].get("hooks", []) if h.get("source") != "editorial"]
    checks["no quote is 'జగన్ ఏం చేశాడనే ప్రస్తావన' or another incomplete statement"] = not any("ప్రస్తావన" in x or x.strip("“”") in ("24 గంటలు", "నేడు 130 భారీ ప్రాజెక్టులు") for x in qs)
    checks[f"labels max 3 words, max 8 hashtags ({len(P['facts'].get('post', {}).get('hashtags', []))})"] = \
        (all(len(x.split()) <= 3 for x in labels) and len(P["facts"].get("post", {}).get("hashtags", [])) <= 8) or bool(P["issues"])
    if not backup and not P["issues"]:            # approval flow on the default model's plan, with your option D
        r = pl("--hook", HOOK_D); P = json.load(open(os.path.join(d, "build", "plan.json"), encoding="utf-8")); Dh = P["creative"]["hooks"][-1]
        checks["option D added with your exact wording"] = Dh.get("source") == "editorial" and " / ".join([Dh["line1"], Dh["line2"], Dh["line3"]] + Dh["headline"]) == HOOK_D
        checks["render refused before approval"] = "PLAN_NOT_APPROVED" in render_codes()
        r1 = pl("--approve", "D"); checks["approval without --checked refused while ❓ are open"] = (r1.returncode != 0 and "--checked" in r1.stdout + r1.stderr and json.load(open(os.path.join(d, "build", "plan.json"), encoding="utf-8")).get("approved") is False) if P["flags"] else True
        r2 = pl("--approve", "D", "--checked"); PJ = json.load(open(os.path.join(d, "project.json"), encoding="utf-8"))
        checks["approved D goes into project.json unchanged"] = r2.returncode == 0 and [PJ["hook"]["line1"], PJ["hook"]["line2"], PJ["hook"]["line3"]] + PJ["title"] == HOOK_D.split(" / ")
        codes = render_codes(); checks["render passes the approval gate after approval (stops later: no edit in this test)"] = "PLAN_NOT_APPROVED" not in codes and "EDIT_MISSING" in codes
        PJ["title"][1] = PJ["title"][1] + "!"; json.dump(PJ, open(os.path.join(d, "project.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        checks["title page edited after approval -> render refused again"] = "PLAN_NOT_APPROVED" in render_codes()
        checks["transcript unchanged"] = md5(WJ) == words_md5
        shutil.copy(os.path.join(d, "build", "plan.md"), os.path.join(OUT, f"planner_{tag}.md"))
    ok = all(checks.values()); allok &= ok
    R["runs"].append(dict(model=m or A.provider, ok=ok, checks=checks, seconds=P["meta"]["seconds"], tries=P["meta"]["tries"], backup=P["meta"]["backup"],
                          beats=len(P["facts"].get("beats", [])), cards=len(cards), problems=P["issues"], marked=P["flags"], corrections=P["facts"].get("corrections", []),
                          hooks=P["creative"].get("hooks"), tag=P["facts"].get("tag", {}).get("text")))
    for k, v in checks.items(): say(f"   {'PASS' if v else 'FAIL'} {k}")
    for i, h in enumerate(P["creative"].get("hooks", [])):
        say(f"   {'ABCD'[i]}: {h.get('line1')} / {h.get('line2')} / {h.get('line3')}  | headline: {' / '.join(h.get('headline', []))}")
    for m in P["facts"].get("corrections", []): say(f"   moved: {m['card']} beat {m['from_beat']} -> {m['to_beat']} (was: {m['original_error']})")
    say(f"   {len(P['creative'].get('rejected', []))} hook candidates rejected by the checks")
    for x in P["facts"].get("adjusted", []): say(f"   adjusted: {x}")
    say(f"   tag: {P['facts'].get('tag', {}).get('text')} | {len(P['issues'])} problems, {len(P['flags'])} marked ❓ -> tests/out/planner_{tag}.md")
say("\n== your approved title page (November, held out from the models):")
say("   hook:", " / ".join(human["hook"].get(k, "") for k in ("line1", "line2", "line3")), "| tag:", human["hook"].get("tag_top", ""), "—", human["hook"].get("tag_bottom", ""),
    "| headline:", " / ".join(human["title"]))
import platform, time as _t
R["when"] = _t.strftime("%Y-%m-%d %H:%M"); R["passed"] = bool(allok)
R["versions"] = {f: md5(os.path.join(ROOT, f)) for f in ("engine/planner.py", "engine/te_numbers.py", "engine/providers.py", "engine/adapter.py", "providers.json", "tests/test_plan_checks.py")}
R["note"] = "These tests check transcript fidelity (numbers, units, claims, quotes as spoken), not whether the political claims are true. Fact verification stays in the production workflow."
json.dump(R, open(os.path.join(OUT, "planner_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if A.record:
    rec = os.path.join(ROOT, "tests", "acceptance", A.record); os.makedirs(rec, exist_ok=True)
    for f in os.listdir(OUT):
        if f.startswith("planner_") or f == "offline_checks.txt": shutil.copy(os.path.join(OUT, f), os.path.join(rec, f))
    say(f"acceptance record saved -> tests/acceptance/{A.record}/")
shutil.rmtree(d, ignore_errors=True) if not os.environ.get("RS_KEEP_TEST") else None
say(f"\nPLANNER TEST {'PASSED (automatic checks)' if allok else 'FAILED'} - now read the planner_*.md files and grade the three hooks")
sys.exit(0 if allok else 1)
