"""Narration script: the approved text, the spoken form of every number, and the approval fingerprint (M4 B1).
  python narration_script.py prepare <project> <script.txt>   one sentence per line -> build/narration.json (not approved)
  python narration_script.py show <project>                   print the script for review (written text and spoken form)
  python narration_script.py approve <project> [--checked]    approve exactly this text; --checked = numbers marked ❓ were checked
  python narration_script.py check <project>                  is the approved text unchanged? (exit 0 yes / 1 no)
build/narration.json = {"lines": [{"text": written (captions), "say": spoken (voice), "tokens": [...], "numbers": [...]}],
                        "approved": bool, "approved_hash": sha256 of every text + say}
The written text is kept exactly as given (only the line break and outer spaces are removed). Nothing is ever corrected
automatically: a change after approval refuses narration and rendering until the script is approved again. The user may
edit a line's "say" by hand before approving (for example a decimal); approval then covers the edited form."""
import sys, os, json, hashlib, datetime, unicodedata, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import te_numbers

def path(j): return os.path.join(j["_dir"], "build", "narration.json")

def fingerprint(lines):
    return hashlib.sha256(json.dumps([[l["text"], l["say"]] for l in lines], ensure_ascii=False).encode("utf-8")).hexdigest()

def spoken_chars(say): return len(re.sub(r"[\s.,!?;:।\"'“”‘’()\[\]\-–—…]", "", say))

def length_check(j, say):
    """B1.2: (estimated speech seconds, spoken characters, too_long). Uses the project's voice/style rate, else the slowest measured."""
    L = load(os.path.join(ENGINE, "tts.json")).get("sentence_limit") or {}
    if not L: return None, spoken_chars(say), False
    rates = L["speech_s_per_char"]; v, st = j.get("narrator"), j.get("narrator_style")
    rate = rates.get(v, {}).get(st) or max(r for vv in rates.values() for r in vv.values())
    n = spoken_chars(say); est = round(n * rate * 1.0 / float(j.get("narration_speed", 1.0) or 1.0), 2)
    return est, n, est > L["max_speech_s"] or n > L["max_spoken_chars"]

def prepare(j, script_file):
    if not os.path.exists(script_file): fail("FILE_NOT_FOUND", f"script not found: {script_file}")
    raw = open(script_file, encoding="utf-8").read().splitlines()
    lines = []
    for t in (x.strip() for x in raw):
        if not t: continue
        say, tokens, numbers = te_numbers.spoken(t)
        est, n, long_ = length_check(j, say)
        lines.append(dict(text=t, say=say, tokens=tokens, numbers=numbers, nfc=unicodedata.normalize("NFC", t) == t,
                          length=dict(est_speech_s=est, spoken_chars=n, too_long=long_)))
    if not lines: fail("NARRATION_SCRIPT_EMPTY", f"{script_file} has no sentences")
    N = dict(version=1, source=os.path.relpath(script_file, j["_dir"]) if os.path.isabs(script_file) else script_file,
             prepared=f"{datetime.datetime.now():%Y-%m-%d %H:%M}", lines=lines, approved=False, approved_hash=None)
    save(N, path(j)); return N

def show(N):
    out = []
    for i, l in enumerate(N["lines"], 1):
        flag = "❓ " if any(n["check"] != "ok" for n in l["numbers"]) or re.search(r"\d", l["say"]) or (l.get("length") or {}).get("too_long") else ""
        out.append(f"{i}. {flag}{l['text']}")
        if l["say"] != l["text"]: out.append(f"   spoken: {l['say']}")
        for n in l["numbers"]:
            if n["check"] != "ok": out.append(f"   ❓ {n['text']} -> {n['say']}: {n['why']}")
        if not l.get("nfc", True): out.append("   note: this line is not in standard Unicode form (NFC); it is kept exactly as written")
        Lg = l.get("length") or {}
        if Lg.get("too_long"): out.append(f"   ❓ long sentence: about {Lg['est_speech_s']} s of speech, {Lg['spoken_chars']} spoken characters "
                                           f"(limit 5.5 s / about 70) - consider splitting it into two lines; nothing is changed automatically")
    out.append(f"status: {'APPROVED ' + N['approved_hash'][:12] if N.get('approved') else 'not approved'}")
    return "\n".join(out)

def approve(j, checked=False):
    p = path(j)
    if not os.path.exists(p): fail("NARRATION_SCRIPT_MISSING", "no build/narration.json - run: narration_script.py prepare <project> <script.txt>")
    N = load(p); problems = []
    for i, l in enumerate(N["lines"], 1):
        if not l.get("say", "").strip(): problems.append(f"line {i}: empty spoken form")
        if re.search(r"\d", l["say"]): problems.append(f"line {i}: the spoken form still has digits ({l['say']}) - write them as words")
        if any(n["check"] != "ok" for n in l["numbers"]) and not checked: problems.append(f"line {i}: number marked ❓ - check it, then approve with --checked")
        if (l.get("length") or {}).get("too_long") and not checked:
            problems.append(f"line {i}: long sentence (about {l['length']['est_speech_s']} s) - review it (split it if you wish), then approve with --checked")
    for l in N["lines"]:   # 'say' edited by hand -> the word-by-word map no longer fits; timing then falls back to proportions
        if l.get("tokens") and " ".join(w for t in l["tokens"] for w in t["say"]) != l["say"]: l["tokens"] = None
    if problems: fail("NARRATION_SCRIPT_PROBLEMS", "not approved:\n  " + "\n  ".join(problems))
    N.update(approved=True, approved_hash=fingerprint(N["lines"]), approved_at=f"{datetime.datetime.now():%Y-%m-%d %H:%M}", checked=bool(checked))
    save(N, p)
    pj = os.path.join(j["_dir"], "project.json"); P = load(pj); P["narration_hash"] = N["approved_hash"]; save(P, pj)
    import rs; rs.log(j, f"narration script approved ({len(N['lines'])} sentences, {N['approved_hash'][:12]})")
    return N

def verify(j):
    """(ok, code, message, N). Used by narrate.py and the render gate in adapter.py."""
    p = path(j)
    if not os.path.exists(p): return False, "NARRATION_NOT_APPROVED", "no narration script yet (build/narration.json)", None
    N = load(p)
    if not N.get("approved"): return False, "NARRATION_NOT_APPROVED", "the narration script is not approved yet", N
    if fingerprint(N["lines"]) != N.get("approved_hash") or j.get("narration_hash") != N.get("approved_hash"):
        return False, "NARRATION_TEXT_CHANGED", "the narration text changed after approval - approve it again", N
    return True, None, "approved", N

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("prepare", "show", "approve", "check"): sys.exit(__doc__)
    j, c = job(a[1])
    if a[0] == "prepare":
        if len(a) < 3: sys.exit(__doc__)
        print(show(prepare(j, a[2] if os.path.isabs(a[2]) or os.path.exists(a[2]) else os.path.join(j["_dir"], a[2]))))
    elif a[0] == "show":
        if not os.path.exists(path(j)): fail("NARRATION_SCRIPT_MISSING", "no build/narration.json yet")
        print(show(load(path(j))))
    elif a[0] == "approve": print(show(approve(j, "--checked" in a)))
    else:
        ok, code, msg, _ = verify(j); print(("OK: " if ok else f"{code}: ") + msg); emit("check", ok=ok, code=code); sys.exit(0 if ok else 1)
