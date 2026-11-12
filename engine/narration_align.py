"""Caption timing + listening check for the narration (M4 B1).
Usage: python narration_align.py <project>
Runs the Telugu speech-to-text (engine/transcribe.py -> its own Python, rs_asr) on build/narration.wav AFTER the voice model
has closed (one heavy model at a time), then:
  build/narration_words.json  caption words = the APPROVED written text, word by word, timed on the edit timeline
                              (speech-to-text only supplies the times; its words are never shown)
  build/narration_check.json  round-trip character error per sentence and overall, numbers heard vs approved, sentences to check
For a recording, the sentence start/end times are taken from the speech-to-text and written into narration_timeline.json.
A sentence above 20 % character error, or a number heard differently, is LISTED for the user - never changed or re-spoken.
The speech-to-text result is kept (build/narration_asr.json with the audio checksum) and re-used while the audio is unchanged.
Heard words are given to sentences through the word alignment (not by time windows, which drift with speech-to-text timing).
RS_ALIGN_ASR_JSON=<file> uses an existing speech-to-text result instead of running it (tests)."""
import sys, os, json, re, difflib, subprocess, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import narration_script as NS, te_numbers

LIMIT = 0.20
def norm(w): return te_numbers.clean(w)
def chars(s): return re.sub(r"\s+", "", "".join(norm(w) for w in s.split()))

def cer(ref, hyp):
    a, b = chars(ref), chars(hyp)
    if not a: return 0.0 if not b else 1.0
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for k, y in enumerate(b, 1): cur[k] = min(prev[k] + 1, cur[k - 1] + 1, prev[k - 1] + (x != y))
        prev = cur
    return prev[-1] / len(a)

def asr(j, wav, audio_sha):
    """Speech-to-text on the narration. Re-used when the audio is unchanged (no model is loaded again for nothing)."""
    if os.environ.get("RS_ALIGN_ASR_JSON"): return load(os.environ["RS_ALIGN_ASR_JSON"])
    out = os.path.join(j["_dir"], "build", "narration_asr.json")
    if os.path.exists(out):
        try:
            old = load(out)
            if old.get("audio_sha256") == audio_sha: old["reused"] = True; return old
        except ValueError: pass
    with heavy_lock("speech-to-text (narration check)"):
        r = subprocess.run([sys.executable, os.path.join(ENGINE, "transcribe.py"), "--audio", wav, "--lang", "te", "--out", out],
                           capture_output=True, text=True, cwd=ROOT, env={k: v for k, v in os.environ.items() if k != "RS_EVENTS"})
    if r.returncode or not os.path.exists(out): fail("ALIGN_ASR_FAILED", f"speech-to-text on the narration failed: {(r.stderr or r.stdout)[-1200:]}")
    R = load(out); R["audio_sha256"] = audio_sha; save(R, out); return R

def split_compounds(text):
    """'పదివేల' -> 'పది వేల' (speech-to-text often joins a number word and its unit; the number reader needs them apart)."""
    out = []
    for w in text.split():
        c = te_numbers.clean(w); done = False
        for k in sorted(te_numbers.ONES, key=len, reverse=True):
            if len(k) > 1 and c.startswith(k) and len(c) > len(k) and te_numbers._unit(c[len(k):]):
                out += [k, c[len(k):]]; done = True; break
        if not done: out.append(w)
    return " ".join(out)

def numbers(text): return [round(float(q["value"]), 6) for q in te_numbers.all_values(split_compounds(text.replace("నూట", "వంద")))]

def fill(times, lo, hi, weights):
    """Give every unmatched (None) slot a time between its matched neighbours, by character length."""
    n = len(times); idx = [i for i, t in enumerate(times) if t is not None]
    anchors = [(-1, (lo, lo))] + [(i, times[i]) for i in idx] + [(n, (hi, hi))]
    for (a, ta), (b2, tb) in zip(anchors, anchors[1:]):
        gap = list(range(a + 1, b2))
        if not gap: continue
        start, end = ta[1], tb[0]; tot = sum(weights[i] for i in gap) or 1; t = start
        for i in gap:
            d = (end - start) * weights[i] / tot; times[i] = (round(t, 3), round(t + d, 3)); t += d
    return times

def main(project):
    j, c = job(project); b = os.path.join(j["_dir"], "build")
    ok, code, msg, N = NS.verify(j)
    if not ok: fail(code, msg)
    tlp, wav = os.path.join(b, "narration_timeline.json"), os.path.join(b, "narration.wav")
    if not os.path.exists(tlp) or not os.path.exists(wav): fail("NARRATION_MISSING", "no build/narration.wav yet - run narrate.py first")
    TL = load(tlp)
    if TL.get("approved_hash") != N["approved_hash"]: fail("NARRATION_AUDIO_STALE", "the narration was made from an older script - run narrate.py again")
    progress(5, "speech-to-text on the narration"); R = asr(j, wav, TL["audio_sha256"]); heard = R["words"]
    # spoken-form tokens of the whole script, each linked to its line and its written word
    say_tok = []
    for li, l in enumerate(N["lines"]):
        if l.get("tokens"): toks = l["tokens"]
        elif l["say"] == l["text"]: toks = [dict(t=w, say=[w]) for w in l["text"].split()]
        else: toks = None
        if toks is None:   # 'say' edited by hand: spread written words over spoken words by position
            sw, tw = l["say"].split(), l["text"].split()
            for k, w in enumerate(sw): say_tok.append(dict(line=li, tw=min(len(tw) - 1, k * len(tw) // max(1, len(sw))), w=w))
        else:
            for ti, t in enumerate(toks):
                for w in t["say"]: say_tok.append(dict(line=li, tw=ti, w=w))
    A, Bw = [norm(t["w"]) for t in say_tok], [norm(h["w"]) for h in heard]
    times = [None] * len(say_tok)
    for blk in difflib.SequenceMatcher(None, A, Bw, autojunk=False).get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = (heard[blk.b + k]["s"], heard[blk.b + k]["e"])
    matched = sum(t is not None for t in times)
    owner = [None] * len(heard)   # which sentence each heard word belongs to: from the word it matched; unmatched words follow the previous one
    for blk in difflib.SequenceMatcher(None, A, Bw, autojunk=False).get_matching_blocks():
        for k in range(blk.size): owner[blk.b + k] = say_tok[blk.a + k]["line"]
    last = 0
    for i, o in enumerate(owner):
        if o is None: owner[i] = last
        else: last = o
    S = TL["sentences"]; dur = TL["duration"]
    if TL["mode"] == "recorded":   # sentence times from the matched words
        for li, s in enumerate(S):
            got = [times[k] for k, t in enumerate(say_tok) if t["line"] == li and times[k] is not None]
            s["s"], s["e"] = (round(got[0][0], 3), round(got[-1][1], 3)) if got else (None, None)
        known = [(i, s) for i, s in enumerate(S) if s["s"] is not None]
        if not known: fail("ALIGN_NO_MATCH", "the recording does not match the approved script at all - check the file")
        for i, s in enumerate(S):   # a sentence with no recognised word gets the gap between its neighbours (and is listed)
            if s["s"] is None:
                prv = max((x for x in known if x[0] < i), default=None, key=lambda x: x[0]); nxt = min((x for x in known if x[0] > i), default=None, key=lambda x: x[0])
                s["s"] = prv[1]["e"] if prv else 0.0; s["e"] = nxt[1]["s"] if nxt else dur; s["estimated"] = True
        TL["aligned"] = True; save(TL, tlp)
    # caption words inside each sentence's own window (exact for AI: we placed every sentence ourselves)
    words, check = [], []
    for li, (l, s) in enumerate(zip(N["lines"], S)):
        ks = [k for k, t in enumerate(say_tok) if t["line"] == li]
        tt = fill([times[k] if times[k] and s["s"] - 0.3 <= times[k][0] <= s["e"] + 0.3 else None for k in ks], s["s"], s["e"], [len(say_tok[k]["w"]) for k in ks])
        tt = [(max(s["s"], a), min(s["e"], max(a + 0.02, e2))) for a, e2 in tt]
        tw = l["text"].split()
        for wi, w in enumerate(tw):
            mine = [tt[n] for n, k in enumerate(ks) if say_tok[k]["tw"] == wi]
            if mine: words.append(dict(w=w, s=round(min(x[0] for x in mine), 3), e=round(max(x[1] for x in mine), 3), hl=bool(re.search(r"\d", w)), line=li))
        hw = [h["w"] for h, o in zip(heard, owner) if o == li]
        e = cer(l["say"], " ".join(hw)); nums_a, nums_h = numbers(l["say"]), numbers(" ".join(hw))
        issues = ([f"character error {e:.0%} (limit {LIMIT:.0%})"] if e > LIMIT else []) + ([f"numbers heard {nums_h} vs approved {nums_a}"] if nums_a != nums_h else []) \
            + (["sentence time estimated (no word recognised)"] if s.get("estimated") else [])
        check.append(dict(line=li + 1, text=l["text"], say=l["say"], heard=" ".join(hw), cer=round(e, 3), numbers_ok=nums_a == nums_h, issues=issues))
    for a, b2 in zip(words, words[1:]):   # keep captions in order and non-overlapping
        if b2["s"] < a["e"]: a["e"] = max(a["s"] + 0.02, b2["s"])
    save([{k: w[k] for k in ("w", "s", "e", "hl")} for w in words], os.path.join(b, "narration_words.json"))
    total = cer(" ".join(l["say"] for l in N["lines"]), " ".join(h["w"] for h in heard))
    sync = [round(next(w["s"] for w in words if w["line"] == i) - s["s"], 3) for i, s in enumerate(S) if any(w["line"] == i for w in words)]
    Rp = dict(mode=TL["mode"], approved_hash=N["approved_hash"], audio_sha256=TL["audio_sha256"], asr_model=R.get("model"), asr_reused=bool(R.get("reused")), words_heard=len(heard),
              spoken_tokens=len(say_tok), matched_tokens=matched, cer_total=round(total, 3), cer_limit=LIMIT,
              first_caption_vs_sentence_start_s=sync, max_sync_offset_s=max((abs(x) for x in sync), default=0.0),
              to_check=[x for x in check if x["issues"]], sentences=check)
    save(Rp, os.path.join(b, "narration_check.json"))
    progress(100); emit("output", path=os.path.join(b, "narration_words.json"), check=os.path.join(b, "narration_check.json"), cer=Rp["cer_total"], to_check=len(Rp["to_check"]))
    print(f"narration check: character error {total:.1%} overall | {len(Rp['to_check'])} sentence(s) to check | captions -> build/narration_words.json")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1])
