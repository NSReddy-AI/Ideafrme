"""Draft the reel plan from the transcript + brief + brand + style (the 'plan' step of Create Reel). The user approves it.
Default provider: the local model (Ollama + Qwen3 14B, free, offline); 8B is the backup; Claude / Gemini / OpenAI optional.
Usage:
  python planner.py <project> [--provider local|claude|gemini|openai] [--model qwen3:14b] [--creative-provider claude] [--out build/plan.json] [--holdout <source>]
  python planner.py <project> --recheck            (re-run the checks after you edited build/plan.json by hand)
  python planner.py <project> --hook "line1 / line2 / line3 / headline 1 / headline 2"   (your own option D, same checks)
  python planner.py <project> --approve A|B|C|D [--checked]   (pick a hook; --checked = I have read every ❓ line)
Two separate model steps:
  1. FACTS    - built by CODE (build_claims): one beat per spoken number at phrase edges, cards and labels from the speaker's words.
               The model only chooses by claim number (cards, tag, hashtags); an unusable choice -> the program's default choice.
  2. CREATIVE - candidate openers / payoffs / headlines + quote word ranges, from the brand style sheet and the fact list only;
     code keeps the valid candidates and builds options A/B/C (--creative-provider can use Claude/Gemini/OpenAI for this step only).
  The post text = the checked intro + one line per number card (no free-written facts). Overlapping beat edges are moved (listed).
Safety rules enforced in CODE (te_numbers.py understands Telugu number words, units and compounds):
  - speech quotes are never written by the model: beats point at transcript word numbers; quotes on the title page must be verbatim;
  - every number card must be spoken INSIDE its beat, with the same value AND unit, and its label must name what the speaker names;
    the card's time is taken from the spoken words;
  - every number in hooks, headline, tag and post must be a value that is spoken (or in the brief), about the same thing;
  - hook lines at most 4 words; headline 2 lines and not a copy of the hook; text in the brand's language.
One automatic retry per step with the problems listed; what is still wrong is listed as a problem (blocks approval) or ❓.
The backup model (8B) passes the same checks and is never allowed for automatic publishing."""
import os, sys, re, json, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import job, load, save, fail, progress, emit, ROOT
import providers, te_numbers as N

S_STR = {"type": "string"}
CHOICE_SCHEMA = {"type": "object", "required": ["feature", "tag", "hashtags"], "properties": {
    "feature": {"type": "array", "items": {"type": "integer"}}, "tag": {"type": ["integer", "null"]}, "hashtags": {"type": "array", "items": {"type": "string"}}}}
FACTS_SCHEMA = {"type": "object", "required": ["beats", "tag", "post"], "properties": {   # (old shape, still accepted by --recheck for hand-made plans)
    "beats": {"type": "array", "items": {"type": "object", "required": ["from_word", "to_word", "graphic"], "properties": {
        "from_word": {"type": "integer"}, "to_word": {"type": "integer"},
        "graphic": {"type": "object", "required": ["type", "number_word", "number", "label"], "properties": {
            "type": {"type": "string", "enum": ["none", "number", "text", "place"]}, "number_word": {"type": "integer"}, "number": S_STR, "label": S_STR}}}}},
    "tag": {"type": "object", "required": ["number_word", "label"], "properties": {"number_word": {"type": "integer"}, "label": S_STR}},
    "post": {"type": "object", "required": ["hashtags"], "properties": {"hashtags": {"type": "array", "items": S_STR}}}}}
# Creative step: the model writes CANDIDATE lines; code keeps the valid ones and builds options A/B/C from them.
# The quote line is never typed by the model: it points at transcript words (like beats), the words come from the transcript.
S_LIST = {"type": "array", "items": S_STR}
CREATIVE_SCHEMA = {"type": "object", "required": ["openers", "quotes", "payoffs", "headlines", "post_intro"], "properties": {
    "openers": S_LIST, "payoffs": S_LIST, "post_intro": S_STR,
    "quotes": {"type": "array", "items": {"type": "object", "required": ["from_word", "to_word"], "properties": {"from_word": {"type": "integer"}, "to_word": {"type": "integer"}}}},
    "headlines": {"type": "array", "items": {"type": "object", "required": ["line1", "line2"], "properties": {"line1": S_STR, "line2": S_STR}}}}}
FILLER = {"మంది", "వరకు", "పైగా", "కోసం", "అదే", "ఇలా", "సార్", "మరియు", "కూడా", "అండ్", "ఉంది", "గా"}   # not a label on their own

TE = re.compile(r"[ఀ-౿]")
QUOTE = re.compile(r"[“\"‘']([^”\"’']+)[”\"’']")

def load_words(b):
    for f in ("transcript.json", "words.json"):
        p = os.path.join(b, f)
        if os.path.exists(p):
            d = load(p); return (d["words"] if isinstance(d, dict) else d), f
    fail("NO_TRANSCRIPT", "no build/transcript.json or build/words.json - run transcribe.py first")

def brand_guide(j, holdout=None):
    d = os.path.join(ROOT, "brands", j["brand"]); g = ""
    if os.path.exists(os.path.join(d, "style-sheet.md")):   # only the title-page section (the rest is the visual style)
        full = open(os.path.join(d, "style-sheet.md"), encoding="utf-8").read(); m = re.search(r"^## \d*\.?\s*Title page.*?(?=^## |\Z)", full, re.S | re.M)
        g = m.group(0) if m else ""
    ex = load(os.path.join(d, "approved_hooks.json")).get("examples", []) if os.path.exists(os.path.join(d, "approved_hooks.json")) else []
    ex = [e for e in ex if not (holdout and holdout in e.get("source", ""))]
    m = re.search(r"#+ Framing words[^\n]*\n(.+)", g); framing = set(re.split(r"[,\s]+", m.group(1).strip())) if m else set()
    return g, ex, framing

def lang_name(c): return "Telugu (Telugu script)" if c.get("language") == "te" else "English"

def numbers_list(Q):
    return "\n".join(f"- word [{q['a']}] \"{q['text']}\" = {N.display(q)} -> about: {' '.join(q['subject'])}  (before it: {' '.join(q['before'][-3:])})" for q in Q) or "(no numbers spoken)"

# ---------------------------------------------------------------- step 1: facts
def choose_prompt(j, c, words, C, brief, issues=None):
    S = j["_style"]
    system = (f"You are the fact editor of short vertical reels for '{c['name']}' ({c.get('category', '')}). The program has already cut the speech "
              "into claims, one per spoken number. You only CHOOSE, by claim number: which claims get a number card, which one goes on the title-page tag, "
              f"and up to {MAX_HASHTAGS} hashtags in {lang_name(c)} made only from the speaker's words. Never write numbers or labels. Answer with JSON only.")
    user = (f"STYLE: {S.get('name')} - structure: {'; '.join(S.get('structure', []))}\nBRIEF: {brief or '(none)'}\n\nCLAIMS:\n{claims_list(C, words)}\n\n"
            "Return: feature = the claim numbers that get a card (the strongest facts; skip talk that is not an achievement), "
            "tag = the single most striking ACHIEVEMENT claim number (never time talk like '24 గంటలు'; null if there is none), hashtags = 5-8 relevant hashtags.")
    if issues: user += "\n\nYOUR PREVIOUS ANSWER HAD THESE PROBLEMS - FIX THEM:\n- " + "\n- ".join(issues)
    return system, user

def find_q(Q, idx):
    for q in Q:
        if q["a"] <= idx <= q["b"]: return q

def label_ok(label, q):
    """The label names what the speaker names with this number. Amounts said with -తో ('750 కోట్లతో') can belong to the work before them."""
    amount = N.clean(q["text"].split()[-1]).endswith("తో") and bool(q["before"])   # 'X కోట్లతో': the work can be before or after it
    if N.related(label, q["subject"]): return True, amount
    if amount and N.related(label, q["before"]): return True, True
    return False, False

def check_text_numbers(t, Q, known_brief, where, flags, issues):
    """Numbers inside free text: the value must be spoken (or in the brief) and, when a subject follows, about the same thing."""
    for x in N.all_values(t):
        hits = [q for q in Q if N.same(q["value"], x["value"])]
        if not hits and not any(N.same(x["value"], v) for v in known_brief):
            spoken_digits = [q for q in Q if x["unit"] and N.same(q["value"], x["value"] / {"కోట్లు": 10**7, "కోటి": 10**7, "లక్షలు": 10**5, "లక్ష": 10**5, "వేలు": 1000}.get(x["unit"], 1))]
            hint = f" (the speaker says {spoken_digits[0]['text']} without that unit)" if spoken_digits else ""
            issues.append(f"{where}: '{x['text']}' ({N.display(x)}) is not a number the speaker says{hint}"); continue
        subj = x["subject"]
        if hits and subj and not any(label_ok(" ".join(subj), q)[0] for q in hits):
            flags.append(f"{where}: '{x['text']} {' '.join(subj)}' - the speaker says {hits[0]['text']} about '{' '.join(hits[0]['subject'])}'. Same claim?")

MAX_LABEL_WORDS, MAX_HASHTAGS = 3, 8
# A Telugu phrase cannot END on these: dative -కు/-కి, instrumental -తో, locative -లో, quotative -అనే, conditional -స్తే/-తే/-ంటే,
# purpose -ేలా, postpositions కోసం/వరకు/యొక్క, an adjectival participle -సిన, a genitive -ల్ల, or a number/unit (it needs what it counts).
OPEN_END = ("కు", "కి", "తో", "లో", "నే", "స్తే", "ంటే", "తే", "ేలా", "కోసం", "వరకు", "యొక్క", "సిన", "ల్ల")
COMPLETE_OK = {"ఎందుకు", "దేనికి", "ఇంకెందుకు", "ఎప్పుడో", "ఇంతే", "అంతే", "ఏంటే", "ఇదే", "అదే"}
ATTRIB = ("అంటున్న", "అన్నారు", "అన్నాడు", "అంటూ", "అంటున్నారు", "చెప్పారు", "చెప్పాడు", "అంటాడు", "అంటారు", "ంటున్న", "అన్న")

def incomplete(t, quote_part=False):
    """Why a Telugu line ends (or a speech fragment starts/ends) in the middle of a phrase, or None. Catches obvious cuts only."""
    toks = [x for x in t.split() if N.clean(x)]
    if not toks: return None
    last = N.clean(toks[-1])
    if N._kind(toks[-1]): return f"ends on the number/unit '{toks[-1]}' without what it counts"
    if last in COMPLETE_OK: return None
    for e in OPEN_END + (("గా",) if quote_part else ()):
        if last.endswith(e) and len(last) > len(e) + 1: return f"ends on '{toks[-1]}' - the phrase is not finished"
    return None

def fragment_cut(a, b, words, Q):
    """A speech fragment words[a..b]: must not start right after a number or a genitive (ఇళ్ల|పట్టాలు) and must not split a number from its subject."""
    if a > 0:
        prev = words[a - 1]["w"]; pc = N.clean(prev)
        if N._kind(prev) or pc.endswith("ల్ల") or pc.endswith("ళ్ల"): return f"starts in the middle of a phrase (the word before it is '{prev}')"
    for q in Q:
        if a <= q["b"] <= b and q["b"] == b: return f"ends on the number '{q['text']}' without what it counts"
        if q["a"] < a <= q["b"]: return "cuts a number in half"
    cut = incomplete(" ".join(w["w"] for w in words[a:b + 1]), quote_part=True)
    if cut: return cut
    return meaning_cut(a, b, words, Q)

PREDICATE_SKIP = {"సార్", "కదా"}   # address words are not part of the meaning

def meaning_cut(a, b, words, Q):
    """A quote must be a complete statement: it ends on the speaker's sentence end ('24 గంటలు సరిపోవు'), or it is a complete
    achievement claim - a number with what it counts ('31 లక్షల ఇళ్ల పట్టాలు'). It must not drop the verb that finishes
    the sentence ('24 గంటలు' without 'సరిపోవు'), and a noun phrase that is not a claim is not a statement
    ('జగన్ ఏం చేశాడనే ప్రస్తావన')."""
    W = [w["w"] for w in words]
    if Q:                                       # it must stay inside one claim: 'నేడు 130 భారీ ప్రాజెక్టులు' takes 'నేడు' from 'నాడు నేడు'
        C, _ = build_claims(words, [dict(q) for q in Q])
        where = lambda i: next((c["id"] for c in C if c["start"] <= i <= c["end"]), None)
        if where(a) != where(b): return f"joins words from two different claims ('{W[a]}' belongs to the claim before)"
    nxt = next((W[i] for i in range(b + 1, min(len(W), b + 3)) if N.clean(W[i]) not in PREDICATE_SKIP), None)
    if nxt is not None and _ender(nxt) and N.clean(nxt) not in PREDICATE_SKIP and not _ender(W[b]):
        return f"leaves out how the sentence ends ('{nxt}') - that changes the meaning"
    if _ender(W[b]): return None
    for q in Q:
        if a <= q["a"] <= b:
            lab, end = noun_phrase(q, W)
            if end == b and not is_time_talk(lab): return None
    return "is not a complete statement or a complete number claim"

# ---------------------------------------------------------------- code-first facts
ENDERS = {"సార్", "ఉంది", "ఉన్నాయి", "సరిపోవు", "చాలు", "కదా"}
FORWARD = ("కు", "కి", "గా", "ేలా", "కోసం", "లో", "స్తూ", "తూ")

def _ender(w):
    c = N.clean(w); raw = w.strip()
    return bool(c) and (c in ENDERS or raw.endswith((",", ".", "!", "?", "।")) or (len(c) >= 5 and c.endswith(("ారు", "ాడు", "ాయి", "ంది")) and not N._kind(w)))

def _forward(w):
    c = N.clean(w); return bool(c) and c not in COMPLETE_OK and (c in ("కోసం", "వరకు") or any(c.endswith(e) and len(c) > len(e) + 1 for e in FORWARD))

def noun_phrase(q, W):
    """The thing the speaker counts with this number: (label, last word index). Skips fillers / place words in front
    ('అదే ఉద్దానంలో రక్షిత మంచినీరు' -> 'రక్షిత మంచినీరు'), stops at the first plural noun (-లు) or after 3 words,
    and writes a case-marked plural plainly ('పెట్టుబడులతో' -> 'పెట్టుబడులు'). The words are the speaker's."""
    i, label, end = q["b"] + 1, [], q["b"]
    while i < len(W) and not label and (N.clean(W[i]) in FILLER or (_forward(W[i]) and not N.clean(W[i]).endswith(("లతో", "లకు")))) and i - q["b"] <= 2:
        i += 1
    while i < len(W) and len(label) < 3 and not N._kind(W[i]):
        c = N.clean(W[i])
        if c in FILLER: i += 1; continue
        head = c.endswith("లు") or c.endswith(("లతో", "లకు"))
        word = W[i].strip(" ,.!?")
        if c.endswith("లతో"): word = word[: word.rfind("లతో")] + "లు"
        elif c.endswith("లకు"): word = word[: word.rfind("లకు")] + "లు"
        label.append(word); end = i; i += 1
        if head or _ender(W[end]): break
        if len(label) == 2 and not any(N.clean(x).endswith("లు") for x in W[i:i + 1]): break
    return " ".join(label), end

def build_claims(words, Q):
    """Every spoken number as a claim with its own beat, cut at phrase edges. Telugu puts the purpose BEFORE the number
    ('అన్నదాతకు ఆసరాగా 10,500 ఆర్బీకేలు'), so words between two claims go to the next claim when they point forward
    (-కు, -గా, -ేలా, -కోసం, -లో ...), and stay with the previous claim up to its last sentence end ('సరిపోవు సార్')."""
    W = [w["w"] for w in words]; C = []
    for q in Q:
        label, np_end = noun_phrase(q, W)
        C.append(dict(q=q, label=label, np_end=np_end))
    for k, c in enumerate(C):
        nxt = C[k + 1]["q"]["a"] if k + 1 < len(C) else len(W)
        gap = list(range(c["np_end"] + 1, nxt)); last_end = max([i for i in gap if _ender(W[i])], default=None)
        if k + 1 == len(C):   # the last claim keeps one closing word ('సాకారం'); the rest is the closing beat
            c["end"] = c["np_end"] + 1 if gap and not _forward(W[gap[0]]) and N.clean(W[gap[0]]) not in FILLER else c["np_end"]
        elif last_end is not None: c["end"] = last_end
        elif any(_forward(W[i]) for i in gap): c["end"] = c["np_end"]
        else: c["end"] = gap[-1] if gap else c["np_end"]
    for k, c in enumerate(C):   # an amount ('X కోట్లతో') can only belong to words before it that are not already another claim
        c["q"]["before"] = W[(C[k - 1]["np_end"] + 1 if k else 0): c["q"]["a"]][-6:]
    for k, c in enumerate(C):
        c["start"] = 0 if k == 0 else C[k - 1]["end"] + 1
        q = c["q"]; c.update(id=k + 1, number=N.display(q), s=words[q["a"]]["s"], e=words[c["np_end"]]["e"])
    tail = (C[-1]["end"] + 1, len(W) - 1) if C and C[-1]["end"] < len(W) - 1 else None
    return C, tail

def claims_list(C, words):
    return "\n".join(f"[{c['id']}] {c['number']} — {c['label']}   (beat: \"{' '.join(w['w'] for w in words[c['start']:c['end'] + 1])}\")" for c in C)

def facts_from_choice(C, tail, choice, words):
    """Beats and cards built by code; the model's choice only says which claims get a card, the tag and hashtags."""
    feat = [x for x in dict.fromkeys(choice.get("feature") or []) if isinstance(x, int) and 1 <= x <= len(C)]
    beats = []
    for c in C:
        g = dict(type="number", number_word=c["q"]["a"], number=c["number"], label=c["label"]) if c["id"] in feat else {"type": "none"}
        beats.append(dict(from_word=c["start"], to_word=c["end"], graphic=g, claim=c["id"]))
    if tail: beats.append(dict(from_word=tail[0], to_word=tail[1], graphic={"type": "none"}))
    t = choice.get("tag"); tc = C[t - 1] if isinstance(t, int) and 1 <= t <= len(C) and not is_time_talk(C[t - 1]["label"]) else None
    return dict(beats=beats, tag=dict(number_word=tc["q"]["a"], label=tc["label"]) if tc else {}, post=dict(hashtags=list(choice.get("hashtags") or [])), feature=feat)

TIME_WORDS = ("గంట", "నిమిష", "సెకన", "రోజు", "రోజుల", "వారా", "నెల", "సంవత్సర", "ఏళ్ల", "ఏళ్లు", "hour", "minute", "second", "day", "week", "month", "year")

def is_time_talk(label):
    """'24 — గంటలు' is a way of speaking, not an achievement: never a title-page tag."""
    return any(N.clean(w).startswith(TIME_WORDS) for w in (label or "").split())

def check_choice(ch, C):
    issues = []
    f = ch.get("feature") or []
    bad = [x for x in f if not (isinstance(x, int) and 1 <= x <= len(C))]
    if bad: issues.append(f"feature: {bad} are not claim numbers (1-{len(C)})")
    if not [x for x in f if x not in bad]: issues.append("feature: choose at least one claim")
    t = ch.get("tag")
    if t is None and not [c for c in C if not is_time_talk(c["label"])]: pass
    elif not (isinstance(t, int) and 1 <= t <= len(C)): issues.append(f"tag: {t} is not a claim number (1-{len(C)})")
    elif is_time_talk(C[t - 1]["label"]):
        ok_ids = [c["id"] for c in C if not is_time_talk(c["label"])]
        issues.append(f"tag: claim {t} ({C[t - 1]['number']} — {C[t - 1]['label']}) is time talk, not an achievement - choose one of {ok_ids}" if ok_ids else "tag: no claim is an achievement - leave the tag out")
    if len(ch.get("hashtags") or []) > MAX_HASHTAGS: issues.append(f"{len(ch['hashtags'])} hashtags (max {MAX_HASHTAGS})")
    return issues, []

def default_choice(C):
    """If the model cannot choose: every claim except clock/time talk gets a card; the tag = the biggest count of people or homes said in lakhs, else the first claim."""
    feat = [c["id"] for c in C if not is_time_talk(c["label"])]
    big = [c for c in C if c["q"].get("unit") in ("లక్షలు", "లక్ష") and c["id"] in feat]
    tag = (big[0] if big else C[feat[0] - 1])["id"] if feat else None        # no achievement -> no tag (never invented)
    return dict(feature=feat or [c["id"] for c in C], tag=tag, hashtags=[])

def card_range(bt, Q):
    g = bt.get("graphic", {}); q = find_q(Q, g.get("number_word", -1)) if g.get("type") == "number" else None
    return (q["a"], q["b"]) if q else None

def repair_beats(F, Q):
    """Overlapping beat edges are moved, never the words: a beat inside the previous one is merged into it; otherwise the edge
    moves so both number cards stay inside their beats. Returns notes shown in plan.md. A beat that goes BACK in time is left (a problem)."""
    out, notes = [], []
    for bt in F.get("beats", []):
        a, b = bt.get("from_word", -1), bt.get("to_word", -1)
        if not out or not isinstance(a, int) or not isinstance(b, int): out.append(bt); continue
        pv = out[-1]; pa, pb = pv.get("from_word", -1), pv.get("to_word", -1)
        if not (isinstance(pa, int) and isinstance(pb, int)) or a > pb or a < pa: out.append(bt); continue
        c, pc = card_range(bt, Q), card_range(pv, Q)
        if b <= pb and not c:                                  # inside the previous beat, nothing of its own
            notes.append(f"beat at words {a}-{b} is inside the beat before it - merged"); continue
        if b <= pb and c and not pc:
            pv["graphic"] = bt["graphic"]; notes.append(f"beat at words {a}-{b} is inside the beat before it - merged, its card kept"); continue
        if a - 1 >= pa and (not pc or pc[1] <= a - 1):
            pv["to_word"] = a - 1; notes.append(f"beat ending at word {pb} now ends at {a - 1} (it overlapped the next beat)"); out.append(bt); continue
        if pb + 1 <= b and (not c or c[0] >= pb + 1):
            bt["from_word"] = pb + 1; notes.append(f"beat starting at word {a} now starts at {pb + 1} (it overlapped the beat before)"); out.append(bt); continue
        out.append(bt)
    F["beats"] = out; F["adjusted"] = F.get("adjusted", []) + notes
    return notes

def from_words(tag, words, extra=()):
    """A hashtag must be glued together from the speaker's words (each piece = a word, or the word minus its last 1-2 letters)."""
    W = {N.clean(w["w"]) for w in words if N.clean(w["w"])} | {N.clean(x) for x in extra if N.clean(x)}; t = N.clean(tag); ok = [True] + [False] * len(t)
    for i in range(len(t)):
        if ok[i]:
            for w in W:
                for cut in (0, 1, 2, 3):
                    piece = w[: len(w) - cut] if cut else w
                    if len(piece) >= 3 and t.startswith(piece, i): ok[i + len(piece)] = True
    return any(ok[len(t) - k] for k in (0, 1) if len(t) - k > 0)   # a vowel sign may differ at the very end

def beat_of(F, q):
    for k, bt in enumerate(F.get("beats", [])):
        if isinstance(bt.get("from_word"), int) and isinstance(bt.get("to_word"), int) and bt["from_word"] <= q["a"] and q["b"] <= bt["to_word"]: return k

def relocate_cards(F, Q):
    """A number card in the wrong beat is moved ONLY when its number + unit + subject match exactly one spoken claim and the beat
    that holds that claim has no other card. Everything else stays a problem for the user. Every move is recorded (original error kept).
    All misplaced cards are lifted out first, so a run of cards shifted by one beat (the 8B pattern) can be put back."""
    moved, problems, beats = [], [], F.get("beats", [])
    lifted = []
    for k, bt in enumerate(beats):
        g = bt.get("graphic", {})
        if g.get("type") != "number": continue
        a, b = bt.get("from_word", -1), bt.get("to_word", -1); q0 = find_q(Q, g.get("number_word", -1))
        if q0 and isinstance(a, int) and isinstance(b, int) and a <= q0["a"] and q0["b"] <= b: continue      # already in the right beat
        lifted.append((k, g, f"beat {k + 1} (words {a}-{b}): card '{g.get('number')} — {g.get('label', '')}' is not spoken in this beat")); bt["graphic"] = {"type": "none"}
    for k, g, original in lifted:
        v = N.value_of(g.get("number", "")); label = g.get("label", "")
        cands = [q for q in Q if N.same(q["value"], v) and label_ok(label, q)[0]]
        q = cands[0] if len(cands) == 1 else None; t = beat_of(F, q) if q else None; why = None
        if not cands: why = "no spoken claim has this number, unit and subject"
        elif len(cands) > 1: why = "it matches more than one spoken claim: " + ", ".join(f"'{x['text']} {' '.join(x['subject'][:2])}' at {x.get('s')} s" for x in cands)
        elif t is None: why = f"no beat contains '{q['text']}' (words {q['a']}-{q['b']})"
        else:
            tg = beats[t].get("graphic", {})
            if tg.get("type") == "number": why = f"beat {t + 1} (where it is spoken) already has the card '{tg.get('number')} — {tg.get('label')}'"
            elif tg.get("type") in ("text", "place") and (tg.get("label") or "").strip(): why = f"beat {t + 1} already has the graphic '{tg.get('label')}'"
        if why:
            problems.append(f"{original} - not corrected: {why}. Please review.")
            if beats[k].get("graphic", {}).get("type") in (None, "none"): beats[k]["graphic"] = g      # put it back so the error stays visible
            continue
        beats[t]["graphic"] = dict(g, number_word=q["a"])
        moved.append(dict(card=f"{g.get('number')} — {label}", from_beat=k + 1, to_beat=t + 1, original_error=original,
                          reason=f"its number, unit and subject match exactly one spoken claim: '{q['text']} {' '.join(q['subject'][:2])}' at {q.get('s')}-{q.get('e')} s"))
    F["corrections"] = F.get("corrections", []) + moved
    return moved, problems

def check_facts(F, words, Q, brief, lang, framing=()):
    issues, flags = [], []; kb = [q["value"] for q in N.quantities(brief.split())] if brief and brief.split() else []
    repair_beats(F, Q); moved, issues_moved = relocate_cards(F, Q); issues += issues_moved; last = -1
    for m in moved: flags.append(f"card {m['card']} was moved from beat {m['from_beat']} to beat {m['to_beat']} by the program ({m['reason']}) - please check")
    for bt in F.get("beats", []):            # an empty text card is no card
        g = bt.get("graphic", {})
        if g.get("type") in ("text", "place") and not (g.get("label") or "").strip(): bt["graphic"] = {"type": "none"}
    for i, bt in enumerate(F.get("beats", [])):
        a, b = bt.get("from_word", -1), bt.get("to_word", -1); n = f"beat {i + 1}"
        if not (0 <= a <= b < len(words)): issues.append(f"{n}: word numbers {a}-{b} are outside the transcript (0-{len(words) - 1})"); continue
        if i > 0 and a <= last: issues.append(f"{n}: overlaps or goes back in time (starts at word {a}, previous beat ended at {last})")
        last = max(last, b); g = bt.setdefault("graphic", {"type": "none"})
        if lang == "te" and g.get("label") and not TE.search(g["label"]): issues.append(f"{n}: label '{g['label']}' is not in Telugu script")
        if g.get("type") == "number":
            k = g.get("number_word", -1); q = find_q(Q, k)
            if q is None or not (a <= q["a"] and q["b"] <= b):
                inside = [x for x in Q if a <= x["a"] and x["b"] <= b]
                issues.append(f"{n}: the card number must be spoken inside the beat (words {a}-{b}); "
                              + (f"numbers spoken there: {', '.join(x['text'] + ' [' + str(x['a']) + ']' for x in inside)}" if inside else "no number is spoken in this beat - use type text or none"))
                continue
            v = N.value_of(g.get("number", ""))
            if not N.same(v, q["value"]):
                issues.append(f"{n}: card shows '{g.get('number')}' but the speaker says '{q['text']}' = {N.display(q)} (value and unit must match)"); continue
            ok, amb = label_ok(g.get("label", ""), q)
            if len((g.get("label") or "").split()) > MAX_LABEL_WORDS: issues.append(f"{n}: label '{g.get('label')}' has {len(g['label'].split())} words (max {MAX_LABEL_WORDS})")
            elif not [x for x in (g.get("label") or "").split() if N.clean(x) not in FILLER]: issues.append(f"{n}: label '{g.get('label')}' is only a filler word - name the thing (speaker: '{' '.join(q['subject'])}')")
            elif not ok: issues.append(f"{n}: label '{g.get('label')}' does not match what the speaker says with {q['text']}: '{' '.join(q['subject'])}'")
            elif amb: flags.append(f"{n}: {q['text']} - is it for '{' '.join(q['before'][-3:])}' (before) or '{' '.join(q['subject'])}' (after)? Please check the label '{g.get('label')}'")
            g.update(number=N.display(q), spoken=dict(words=[q["a"], q["b"]], s=q.get("s"), e=q.get("e"), text=q["text"] + " " + " ".join(q["subject"][:2])))
        else:
            check_text_numbers(g.get("label", "") + " " + g.get("number", ""), [x for x in Q if a <= x["a"] and x["b"] <= b] or Q, kb, f"{n} graphic", flags, issues)
    if not F.get("beats"): issues.append("no beats")
    t = F.get("tag") or {}; q = find_q(Q, t.get("number_word", -1))
    if not t and F.get("claims_by_code"): pass                         # no achievement number: the title page has no tag
    elif q is None: issues.append(f"tag: word {t.get('number_word')} is not a spoken number")
    elif is_time_talk(t.get("label")): issues.append(f"tag: '{q['text']} — {t.get('label')}' is time talk, not an achievement - choose another claim or no tag")
    else:
        ok, amb = label_ok(t.get("label", ""), q)
        if len((t.get("label") or "").split()) > MAX_LABEL_WORDS: issues.append(f"tag: label '{t.get('label')}' has {len(t['label'].split())} words (max {MAX_LABEL_WORDS})")
        elif not [x for x in (t.get("label") or "").split() if N.clean(x) not in FILLER]: issues.append(f"tag: label '{t.get('label')}' is only a filler word")
        elif not ok: issues.append(f"tag: label '{t.get('label')}' does not match what the speaker says with {q['text']}: '{' '.join(q['subject'])}'")
        elif amb: flags.append(f"tag: {q['text']} - is it about '{t.get('label')}'? Please check")
        t.update(number=N.display(q), text=f"{N.display(q)} — {t.get('label', '')}")
    tags = []
    for h in F.get("post", {}).get("hashtags", []):
        h = "#" + re.sub(r"[\s#]+", "", h)
        if len(h) > 1: tags.append(h)
        if TE.search(h) and not from_words(h[1:], words, list(framing) + (brief or "").split()): flags.append(f"hashtag {h} is not made from the speaker's words - check the name/spelling")
    tags = list(dict.fromkeys(tags))
    if F.get("claims_by_code"):   # hashtags are not facts: invalid ones are dropped (and listed), never a reason to block the plan
        keep = [h for h in tags if not (TE.search(h) and not from_words(h[1:], words, list(framing) + (brief or "").split())) and N.clean(h[1:]) not in FILLER][:MAX_HASHTAGS]
        dropped = [h for h in tags if h not in keep]
        if dropped: F["adjusted"] = F.get("adjusted", []) + [f"hashtags left out (not from the speaker's words, filler, or over {MAX_HASHTAGS}): {' '.join(dropped)}"]
        flags[:] = [x for x in flags if not any(x.startswith(f"hashtag {h} ") for h in dropped)]; tags = keep
    F.setdefault("post", {})["hashtags"] = tags
    if len(tags) > MAX_HASHTAGS: issues.append(f"{len(tags)} hashtags (max {MAX_HASHTAGS}) - keep the most relevant")
    about = [w for bt in F.get("beats", []) for w in (bt.get("graphic", {}).get("label") or "").split()] + (F.get("tag", {}).get("label") or "").split()
    for h in tags:
        if N.clean(h[1:]) in FILLER: issues.append(f"hashtag {h} is only a filler word")
        elif TE.search(h) and not any(N.clean(h[1:]).startswith(N.stem(w, 3)) or N.stem(w, 3) in N.clean(h[1:]) for w in about + list(framing) if len(N.clean(w)) >= 3):
            flags.append(f"hashtag {h} is not about any card, the tag or the brand - is it relevant?")
    return issues, flags

# ---------------------------------------------------------------- step 2: creative
def creative_prompt(j, c, words, Q, F, guide, examples, issues=None):
    numbered = " ".join(f"[{i}]{w['w']}" for i, w in enumerate(words))
    facts = "\n".join(f"- {N.display(q)} {' '.join(q['subject'])}" for q in Q)
    ex = "\n".join(f"- hook: {e['hook']['line1']} / {e['hook']['line2']} / {e['hook']['line3']} | tag: {e.get('tag', '')} | headline: {' / '.join(e.get('headline', []))}"
                   for e in examples) or "(none yet)"
    system = (f"You write the title page of short vertical reels for '{c['name']}' ({c.get('category', '')}), in natural spoken {lang_name(c)}. "
              "Be punchy, but add NO facts: no new numbers, achievements, schemes, places or claims - only the facts listed. "
              "COUNT THE WORDS: every opener and payoff is 2, 3 or 4 words, never more. "
              "Examples of length: 'అసలు ఏం చేశాడు?' = 3 words (good); 'ఇదీ అభివృద్ధి!' = 2 words (good); "
              "'జనగన్న కాలనీలు అంటే ఏం అర్థం?' = 5 words (TOO LONG). Answer with JSON only.")
    user = (f"BRAND STYLE SHEET:\n{guide or '(none)'}\n\nAPPROVED EXAMPLES FROM OTHER REELS (style only - their facts do NOT belong to this reel):\n{ex}\n\n"
            f"THIS REEL - WHAT THE SPEAKER SAYS (word numbers in brackets):\n{numbered}\n\nFACTS YOU MAY USE (nothing else):\n{facts}\n"
            f"TAG ALREADY CHOSEN: {F.get('tag', {}).get('text', '')}\n\nReturn:\n"
            "- openers: 10 different hook line 1 candidates, 2-4 words each: a short question or challenge (no quotes, no full sentence from the speech)\n"
            "- quotes: 3 different word ranges (from_word, to_word) of the speaker's strongest phrase, 2-4 words each - the program copies those exact words\n"
            "- payoffs: 10 different hook line 3 candidates, 2-4 words each: a short payoff or call, not a copy of the speech\n"
            "- headlines: 3 different 2-line headlines (line1, line2), 2-5 words per line, saying the idea in other words than the openers and payoffs\n"
            "- post_intro: one short sentence (max 15 words) to open the post, no new facts")
    if issues: user += "\n\nYOUR PREVIOUS ANSWER HAD THESE PROBLEMS - FIX THEM:\n- " + "\n- ".join(issues)
    return system, user

def code_quotes(words, Q, limit=4):
    """Complete verbatim fragments the program can offer itself: 2-4 words in the opening beat that end on a sentence end
    ('24 గంటలు సరిపోవు'), then 'number + what it counts' from the first claims ('31 లక్షల ఇళ్ల పట్టాలు')."""
    W = [w["w"] for w in words]; out = []
    first = Q[0]["a"] if Q else len(W)
    hook_end = next((i for i in range(first, min(len(W), first + 6)) if _ender(W[i])), None)
    if hook_end is not None:
        for n in (3, 4, 2):
            a = hook_end - n + 1
            if a >= 0 and not fragment_cut(a, hook_end, words, Q) and not _ender(W[a]): out.append((a, hook_end)); break
    for q in Q[1:4]:
        lab, end = noun_phrase(q, W)
        if end - q["a"] + 1 <= 4 and not fragment_cut(q["a"], end, words, Q): out.append((q["a"], end))
    return out[:limit]

def line_problems(t, maxw, lang, Q, kb, allow_quote=False, flags=None):
    t = (t or "").strip(); p = []
    if not t: return ["empty"]
    if len(t.split()) > maxw: p.append(f"{len(t.split())} words (max {maxw})")
    if lang == "te" and not TE.search(t): p.append("not in Telugu script")
    if not allow_quote and re.search(r"[“”\"]", t): p.append("quotes only come from the quote word ranges")
    if not allow_quote and maxw <= 4 and incomplete(t): p.append(incomplete(t))
    tmp = []; check_text_numbers(t, Q, kb, "x", flags if flags is not None else [], tmp); p += [x.split(": ", 1)[1] for x in tmp]
    return p

def assemble(C, words, Q, brief, lang, framing, tag_text=""):
    """Keep the valid candidates and build options A/B/C from them; then check the result like hand-written hooks."""
    kb = [q["value"] for q in N.quantities(brief.split())] if brief and brief.split() else []; rejected = []
    def keep(items, maxw, what):
        out = []
        for t in items or []:
            t = str(t).strip(); p = line_problems(t, maxw, lang, Q, kb)
            if p: rejected.append(f"{what} '{t}': {'; '.join(p)}")
            elif N.clean(t) not in {N.clean(x) for x in out}: out.append(t)
        return out
    ops, pays = keep(C.get("openers"), 4, "opener"), keep(C.get("payoffs"), 4, "payoff"); quotes = []
    for qd in C.get("quotes") or []:
        a, b = qd.get("from_word", -1), qd.get("to_word", -1)
        if not (isinstance(a, int) and isinstance(b, int) and 0 <= a <= b < len(words)): rejected.append(f"quote words {a}-{b}: outside the transcript"); continue
        if b - a + 1 > 4: rejected.append(f"quote words {a}-{b}: {b - a + 1} words (max 4)"); continue
        t = " ".join(w["w"] for w in words[a:b + 1]).strip(" ,.")
        if all(N._kind(x) for x in t.split()): rejected.append(f"quote '{t}': only a number"); continue
        cut = fragment_cut(a, b, words, Q)
        if cut: rejected.append(f"quote '{t}': {cut}"); continue
        if t not in quotes: quotes.append(t)
    for a, b in code_quotes(words, Q):           # the program's own complete speech fragments (verbatim) as extra quote candidates
        t = " ".join(w["w"] for w in words[a:b + 1]).strip(" ,.")
        if t not in quotes: quotes.append(t)
    hds = []
    for h in C.get("headlines") or []:
        l = [str(h.get("line1", "")).strip(), str(h.get("line2", "")).strip()] if isinstance(h, dict) else list(h)[:2]
        p = [f"line {k + 1}: {x}" for k, t in enumerate(l) for x in line_problems(t, 5, lang, Q, kb)] if len(l) == 2 else ["needs 2 lines"]
        if len(l) == 2 and l[1] and incomplete(l[1]): p.append(f"line 2: {incomplete(l[1])}")
        if p: rejected.append(f"headline '{' / '.join(map(str, l))}': {'; '.join(p)}")
        else: hds.append(l)
    issues = []
    for name, have, need in (("openers", ops, 1), ("payoffs", pays, 1), ("quotes", quotes, 1), ("headlines", hds, 1)):
        if len(have) < need: issues.append(f"only {len(have)} usable {name} (need {need}) - write more, each 2-4 words")
    if issues: issues += rejected[:12]
    norm = lambda t: " ".join(N.clean(x) for x in t.split())
    hooks, used, combos = [], set(), []
    if ops and pays and quotes and hds:          # different combinations of valid lines, the most different first
        import itertools
        combos = sorted(itertools.product(range(len(ops)), range(len(quotes)), range(len(pays))), key=lambda x: (max(x), sum(x)))
    seen1, seen3 = set(), set()
    for strict in (True, False):
        for i1, iq, i3 in combos:
            if len(hooks) == 3: break
            if strict and (i1 in seen1 or i3 in seen3): continue
            l1, l3 = ops[i1], pays[i3]; key = (l1, quotes[iq], l3)
            if any((h["line1"], h["line2"].strip("“”"), h["line3"]) == key for h in hooks): continue
            cand = [h for i, h in enumerate(hds) if i not in used and not any(norm(x) in (norm(l1), norm(l3)) for x in h)] or \
                   [h for h in hds if not any(norm(x) in (norm(l1), norm(l3)) for x in h)] or hds
            h = cand[0]; used.add(hds.index(h)); seen1.add(i1); seen3.add(i3)
            hooks.append(dict(line1=l1, line2=f"“{quotes[iq]}”", line3=l3, headline=h))
    C.update(hooks=hooks, rejected=rejected)
    i2, f2 = check_creative(C, words, Q, brief, lang, framing, tag_text)
    i3, f3 = check_intro(C, words, Q, brief, lang, framing)
    return issues + i2 + i3, f2 + f3

def check_intro(C, words, Q, brief, lang, framing):
    kb = [q["value"] for q in N.quantities(brief.split())] if brief and brief.split() else []; t = (C.get("post_intro") or "").strip()
    if not t: return [], []
    fl = []; p = line_problems(t, 15, lang, Q, kb, allow_quote=True, flags=fl); flags = [f"post intro: {x.split(': ', 1)[1]}" for x in fl]
    vocab = {N.stem(w["w"]) for w in words} | {N.stem(x) for x in (brief or "").split()} | {N.stem(x) for x in framing}
    new = sorted({w for w in t.split() if len(N.clean(w)) >= 4 and not N._kind(w) and N.stem(w) not in vocab})
    if new: flags.append(f"post intro: words not from the speech: {', '.join(new)} - check they add no new claim")
    return [f"post intro: {x}" for x in p], flags

def build_post(F, C):
    """The post text = the checked intro + one line per approved number card (number — label). No free-written facts."""
    cards = [b["graphic"] for b in F.get("beats", []) if b.get("graphic", {}).get("type") == "number" and b["graphic"].get("spoken")]
    lines = [(C.get("post_intro") or "").strip()] + [f"• {g['number']} — {g['label']}" for g in cards]
    F.setdefault("post", {})["caption"] = "\n".join(x for x in lines if x)

def verbatim_at(t, words):
    W = [N.clean(w["w"]) for w in words]; P = [N.clean(x) for x in t.split() if N.clean(x)]
    for i in range(len(W) - len(P) + 1):
        if P and W[i:i + len(P)] == P: return i, i + len(P) - 1
    return None

def closest(t, words, span=6):
    """The transcript window that shares the most word-starts with t (shown so the user can compare a paraphrase with the source)."""
    S = {N.stem(x) for x in t.split() if len(N.clean(x)) >= 2}; best, top = 0, -1
    for i in range(len(words)):
        sc = len(S & {N.stem(w["w"]) for w in words[i:i + span]})
        if sc > top: best, top = i, sc
    return " ".join(w["w"] for w in words[best:best + span])

def verbatim(t, words):
    W = [N.clean(w["w"]) for w in words]; P = [N.clean(x) for x in t.split() if N.clean(x)]
    return bool(P) and any(W[i:i + len(P)] == P for i in range(len(W) - len(P) + 1))

def check_creative(C, words, Q, brief, lang, framing, tag_text=""):
    issues, flags = [], []; kb = [q["value"] for q in N.quantities(brief.split())] if brief and brief.split() else []
    H = C.get("hooks", [])
    if len(H) < 3: issues.append(f"need 3 hook options, got {len(H)}")
    vocab = {N.stem(w["w"]) for w in words} | {N.stem(x) for x in (brief or "").split()} | {N.stem(x) for x in framing}
    seen = set()
    for i, h in enumerate(H):
        o = "ABCDEFG"[i] if i < 7 else str(i + 1); lines = [h.get(k, "").strip() for k in ("line1", "line2", "line3")]; hd = [x.strip() for x in h.get("headline", [])]
        for k, t in zip(("line1", "line2", "line3"), lines):
            if not t: issues.append(f"option {o} {k} is empty")
            elif len(t.split()) > 4: issues.append(f"option {o} {k} has {len(t.split())} words (max 4): {t}")
            elif incomplete(QUOTE.sub(lambda m: m.group(1), t)): issues.append(f"option {o} {k} '{t}': {incomplete(QUOTE.sub(lambda m: m.group(1), t))}")
        if len(hd) != 2 or not all(hd): issues.append(f"option {o}: headline must have exactly 2 lines")
        else:
            for x in hd:
                if len(x.split()) > 6: issues.append(f"option {o}: headline line '{x}' has {len(x.split())} words (max 6)")
            if incomplete(hd[1]): issues.append(f"option {o}: headline line 2 '{hd[1]}': {incomplete(hd[1])}")
        texts = lines + hd
        if lang == "te" and not all(TE.search(t) for t in texts if t): issues.append(f"option {o}: every line must be in Telugu script")
        norm = lambda t: " ".join(N.clean(x) for x in t.split())
        same_as = lambda x, l: norm(x) and norm(l) and (norm(x) == norm(l) or (norm(l) in norm(x) and len(norm(l)) > 0.8 * len(norm(x))))
        rep = [x for x in hd if any(same_as(x, l) for l in lines if not QUOTE.search(l))]   # repeating the speaker's quote is the approved pattern
        if len(rep) == 2: issues.append(f"option {o}: the headline repeats the hook - say it in different words")
        elif rep: flags.append(f"option {o}: headline line '{rep[0]}' repeats a hook line")
        if tag_text and any(norm(l) == norm(tag_text.split('—')[0]) for l in lines): flags.append(f"option {o}: a hook line repeats the tag")
        if len({norm(l) for l in lines if l}) < len([l for l in lines if l]): issues.append(f"option {o}: the same line is used twice")
        key = tuple(re.sub(r"\s+", " ", l) for l in lines)        # exact text: quote marks matter (speech vs commentary)
        if key in seen: issues.append(f"option {o} is the same as another option")
        seen.add(key)
        for t in texts:
            for qt in QUOTE.findall(t):
                pos = verbatim_at(qt, words)
                if pos is None: issues.append(f"option {o}: the quote “{qt}” is not the speaker's exact words")
                else:
                    cut = fragment_cut(pos[0], pos[1], words, Q)
                    if cut: issues.append(f"option {o}: the quote “{qt}” {cut}")
            plain = QUOTE.sub(" ", t).strip()
            if plain and not QUOTE.search(t) and len(plain.split()) >= 2 and verbatim(plain.rstrip("!?.…"), words):
                flags.append(f"option {o}: '{t}' is the speaker's words without quote marks - it will read as commentary; add “ ” if it is his quote")
            if any(N.clean(w).endswith(ATTRIB) or N.clean(w) in ATTRIB for w in plain.split()):
                best = closest(plain, words)
                flags.append(f"option {o}: '{t}' says what the speaker says - check it matches his words: “{best}”")
            check_text_numbers(QUOTE.sub(" ", t) if QUOTE.search(t) else t, Q, kb, f"option {o}", flags, issues)
        if all(l and verbatim(l, words) for l in lines): flags.append(f"option {o}: all three lines are copied from the speech - not much of a hook")
        new = sorted({w for t in texts for w in QUOTE.sub(" ", t).split() if len(N.clean(w)) >= 4 and not N._kind(w) and N.stem(w) not in vocab})
        if new: flags.append(f"option {o}: words not from the speech: {', '.join(new)} - check they add no new claim")
    return issues, sorted(set(flags), key=flags.index)

# ---------------------------------------------------------------- output
def plan_hash(P):
    """Fingerprint of what the user approves: all facts + the chosen hook. Rendering checks it, so a later edit needs a new approval."""
    import hashlib
    ch = P.get("hook_choice"); H = P.get("creative", {}).get("hooks", [])
    hook = H["ABCDEFG".index(ch)] if ch and "ABCDEFG".index(ch) < len(H) else None
    return hashlib.sha256(json.dumps([P.get("facts"), hook], ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def editorial_hook(text):
    """'line1 / line2 / line3 / headline1 / headline2' -> option dict, wording kept exactly as typed."""
    parts = [x.strip() for x in text.split(" / ")]
    if len(parts) != 5 or not all(parts): fail("HOOK_FORMAT", "--hook needs 5 parts: \"line1 / line2 / line3 / headline line 1 / headline line 2\" (each part non-empty, separated by ' / ')")
    return dict(line1=parts[0], line2=parts[1], line3=parts[2], headline=parts[3:5], source="editorial")

def to_md(P, words):
    meta, F, C = P["meta"], P["facts"], P["creative"]
    L = [f"# Plan for approval - {meta['project']}",
         f"Drafted by {meta['provider']} / {meta['model']} in {meta['seconds']} s ({meta['tries']} tries). Captions are the speaker's exact words (from the transcript)."]
    if meta.get("creative_provider"): L.append(f"Hooks written by {meta['creative_provider']} / {meta.get('creative_model')} (facts by the model above).")
    if meta.get("backup"): L.append("**⚠ Backup model: read every line. Not allowed for automatic publishing.**")
    L += ["", "## 1. Pick a hook (title page) - " + ", ".join("ABCDEFG"[:len(C.get("hooks", []))]), "", "| | Line 1 | Line 2 | Line 3 | Headline |", "| --- | --- | --- | --- | --- |"]
    for i, h in enumerate(C.get("hooks", [])):
        L.append(f"| **{'ABCDEFG'[i]}**{' (yours)' if h.get('source') == 'editorial' else ''} | {h.get('line1', '')} | {h.get('line2', '')} | {h.get('line3', '')} | {' / '.join(h.get('headline', []))} |")
    if any(h.get("source") == "editorial" for h in C.get("hooks", [])): L.append("\nLines in “ ” are the speaker's words (checked word for word); lines without quotes are the channel's commentary.")
    t = F.get("tag", {}); L += ["", f"**Tag (sign):** {t.get('text') or '(none - no achievement number in this speech)'}", "", "## 2. Beats", "", "| # | Time | What is said (exact) | Graphic | Card time (spoken) |", "| --- | --- | --- | --- | --- |"]
    for i, bt in enumerate(F.get("beats", [])):
        a, b = bt.get("from_word", 0), bt.get("to_word", 0)
        if 0 <= a <= b < len(words): said = " ".join(w["w"] for w in words[a:b + 1]); tm = f"{words[a]['s']:.1f}-{words[b]['e']:.1f}s"
        else: said, tm = "❓ invalid word numbers", "-"
        g = bt.get("graphic", {}); gt = "-" if g.get("type") in (None, "none") else (f"{g.get('number', '')} — {g.get('label', '')}" if g.get("type") == "number" else f"{g.get('type')}: {g.get('label', '')}")
        sp = g.get("spoken"); ct = f"{sp['s']:.2f}-{sp['e']:.2f}s \"{sp['text']}\"" if sp and sp.get("s") is not None else "-"
        L.append(f"| {i + 1} | {tm} | {said} | {gt} | {ct} |")
    cap = F.get("post", {}).get("caption", "").replace("\n", "<br>")
    L += ["", f"**Post caption:** {cap}", f"**Hashtags:** {' '.join(F.get('post', {}).get('hashtags', []))}", ""]
    if F.get("corrections"):
        L += ["## Cards moved by the program (original errors kept for the record)", "", "| Card | Original error | Moved | Why |", "| --- | --- | --- | --- |"]
        L += [f"| {m['card']} | {m['original_error']} | beat {m['from_beat']} → {m['to_beat']} | {m['reason']} |" for m in F["corrections"]] + [""]
    if F.get("adjusted"): L += ["## Adjusted automatically (beat edges only, never words)"] + [f"- {x}" for x in F["adjusted"]] + [""]
    if C.get("rejected"): L += [f"<details><summary>{len(C['rejected'])} hook candidates rejected by the checks</summary>", ""] + [f"- {x}" for x in C["rejected"]] + ["", "</details>", ""]
    if P["issues"]: L += ["## Problems (must be fixed before approval)"] + [f"- ✗ {x}" for x in P["issues"]] + [""]
    if P["flags"]: L += ["## ❓ Please check"] + [f"- ❓ {x}" for x in P["flags"]] + [""]
    if not P["issues"] and not P["flags"]: L.append("No automatic problems found - please still read every line.")
    if P.get("approved"): L += ["", f"**Approved: hook {P.get('hook_choice')} on {P.get('approved_at')}.**"]
    L += ["", "To approve: `python3 engine/planner.py <project> --approve A` (or " + " / ".join("ABCDEFG"[1:len(C.get("hooks", []))]) + ")" + (" `--checked` (after reading every ❓)" if P["flags"] else "")]
    return "\n".join(L) + "\n"

def write(P, out, words):
    save(P, out); open(out.replace(".json", ".md"), "w", encoding="utf-8").write(to_md(P, words))

def run_step(name, make_prompt, schema, checker, prov, model, temp, pct):
    issues, data, tries = None, None, 0
    for tries in (1, 2):
        progress(pct + 20 * (tries - 1), f"{name} (try {tries})")
        system, user = make_prompt(issues)
        try: raw = providers.ask(user, system=system, provider=prov, model=model, json_schema=schema if prov == "local" else None,
                                 max_tokens=4000 if prov == "local" else 12000, temperature=temp)   # cloud models spend part of it thinking
        except Exception as e: fail("PROVIDER_FAILED", f"{prov}: {e}")
        m = re.search(r"\{.*\}", raw, re.S)
        try: data = json.loads(m.group(0) if m else raw)
        except Exception: issues, data = ["the answer was not valid JSON"], None; continue
        issues, flags = checker(data)
        if not issues: break
    if data is None: fail("PLAN_INVALID", f"the model did not return a usable {name}")
    return data, issues, flags, tries

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--provider"); ap.add_argument("--model"); ap.add_argument("--out")
    ap.add_argument("--holdout", help="leave out approved examples from this source project (tests)"); ap.add_argument("--recheck", action="store_true")
    ap.add_argument("--approve", choices=list("ABCDEFG"))
    ap.add_argument("--hook", help="your own hook as option D: \"line1 / line2 / line3 / headline line 1 / headline line 2\""); ap.add_argument("--checked", action="store_true")
    ap.add_argument("--creative-provider", help="optional: write the hooks with another provider (claude|gemini|openai|local); facts stay with --provider")
    ap.add_argument("--creative-model"); A = ap.parse_args(); t0 = time.time()
    j, c = job(A.project); b = os.path.join(j["_dir"], "build"); words, src = load_words(b); out = A.out or os.path.join(b, "plan.json")
    notes = os.path.join(j["_dir"], "inputs", "notes.txt"); brief = (open(notes, encoding="utf-8").read().strip() if os.path.exists(notes) else "") or j.get("brief", "")
    lang = c.get("language", "en"); Q = N.quantities(words); guide, examples, framing = brand_guide(j, A.holdout)
    build_claims(words, Q)   # also tells each amount which words before it are free (not another claim)

    if A.approve or A.recheck or (A.hook and os.path.exists(out) and not A.provider and not A.model):
        if not os.path.exists(out): fail("NO_PLAN", "no plan yet - run planner.py first")
        P = load(out)
        if A.hook:
            H = [h for h in P["creative"].get("hooks", []) if h.get("source") != "editorial"][:3]; P["creative"]["hooks"] = H + [editorial_hook(A.hook)]
        if A.hook or A.recheck: P.update(approved=False, hook_choice=None, approved_hash=None)   # a changed plan needs a new approval
        i1, f1 = check_facts(P["facts"], words, Q, brief, lang, framing); i2, f2 = check_creative(P["creative"], words, Q, brief, lang, framing, P["facts"].get("tag", {}).get("text", ""))
        i3, f3 = check_intro(P["creative"], words, Q, brief, lang, framing); i2 += i3; f2 += f3; build_post(P["facts"], P["creative"])
        P["issues"], P["flags"] = i1 + i2, f1 + f2
        if A.recheck or (A.hook and not A.approve):
            write(P, out, words); print(f"{'hook D added' if A.hook else 'recheck'} -> {out} | {len(P['issues'])} problems, {len(P['flags'])} marked ❓"); return
        if P["issues"]: fail("PLAN_HAS_PROBLEMS", f"{len(P['issues'])} problems must be fixed first (see plan.md)")
        if P["flags"] and not A.checked: fail("PLAN_NOT_CHECKED", f"{len(P['flags'])} lines are marked ❓ - read them, then approve again with --checked")
        if "ABCDEFG".index(A.approve) >= len(P["creative"]["hooks"]): fail("NO_SUCH_HOOK", f"there is no option {A.approve}")
        h = P["creative"]["hooks"]["ABCDEFG".index(A.approve)]; t = P["facts"].get("tag") or {}
        pj = os.path.join(j["_dir"], "project.json"); PJ = load(pj)
        PJ["hook"] = dict(line1=h["line1"], line2=h["line2"], line3=h["line3"], tag_top=t.get("number", ""), tag_bottom=t.get("label", "")); PJ["title"] = h["headline"]
        PJ["approved"] = True; PJ.setdefault("history", []).append(f"{time.strftime('%Y-%m-%d %H:%M')} plan approved (hook {A.approve}, {P['meta']['model']})")
        P.update(approved=True, hook_choice=A.approve, approved_at=time.strftime("%Y-%m-%d %H:%M")); P["approved_hash"] = plan_hash(P)
        PJ["plan_hash"] = P["approved_hash"]; save(PJ, pj); write(P, out, words)
        print(f"approved hook {A.approve}: {h['line1']} / {h['line2']} / {h['line3']} | headline {' / '.join(h['headline'])} | tag {t.get('text') or '(none)'}"); return

    prov = A.provider or j.get("provider") or providers.CFG["default"]; cfg = providers.CFG["providers"][prov]
    if cfg.get("enabled") is False: fail("PROVIDER_OFF", f"{prov} is switched off in providers.json - only the free local model is used")
    model = A.model or cfg.get("model"); backup = False
    if prov == "local":
        if not providers.status().get("local"): fail("LOCAL_MODEL_OFF", "the local model is not running: start Ollama (brew services start ollama)")
        have = providers.local_models()
        if not A.model and model not in have and cfg.get("fallback_model") in have:
            emit("warning", code="BACKUP_MODEL", message=f"{model} not installed - using the backup {cfg['fallback_model']}"); model = cfg["fallback_model"]
        backup = model == cfg.get("fallback_model")
    C_, tail = build_claims(words, Q)
    if not C_: fail("NO_NUMBERS", "no spoken numbers found - nothing to put on number cards")
    try:
        ch, ci, _, t1 = run_step("choice", lambda iss: choose_prompt(j, c, words, C_, brief, iss), CHOICE_SCHEMA, lambda d: check_choice(d, C_), prov, model, 0.2, 5)
    except SystemExit: ch, ci, t1 = None, ["the model gave no usable choice"], 2
    notes, dc = [], default_choice(C_)
    if ch is None: ch = dict(dc); notes.append("the model gave no usable choice - the program chose the cards and the tag")
    elif ci:     # keep what the model chose well, replace only what is unusable
        feat = [x for x in (ch.get("feature") or []) if isinstance(x, int) and 1 <= x <= len(C_)]
        if not feat: ch["feature"] = dc["feature"]; notes.append("the model's card choice was unusable - every claim except time talk gets a card")
        t = ch.get("tag")
        if not (isinstance(t, int) and 1 <= t <= len(C_)) or is_time_talk(C_[t - 1]["label"]):
            ch["tag"] = dc["tag"]
            notes.append(f"the model's tag ({C_[t - 1]['number']} — {C_[t - 1]['label']} = time talk)" if isinstance(t, int) and 1 <= t <= len(C_) else "the model's tag was unusable")
            notes[-1] += " was replaced by the program's: " + (f"{C_[dc['tag'] - 1]['number']} — {C_[dc['tag'] - 1]['label']}" if dc["tag"] else "no tag (no achievement number)")
    F = facts_from_choice(C_, tail, ch, words); F["claims_by_code"] = True; F["adjusted"] = notes
    i1, f1 = check_facts(F, words, Q, brief, lang, framing)
    cp = A.creative_provider or prov; cm = A.creative_model or (model if cp == prov else providers.CFG["providers"][cp].get("model"))
    if providers.CFG["providers"][cp].get("enabled") is False: fail("PROVIDER_OFF", f"{cp} is switched off in providers.json - only the free local model is used")
    if cp != "local" and not providers.status().get(cp): fail("PROVIDER_KEY_MISSING", f"{cp}: set {providers.CFG['providers'][cp]['key_env']} in your shell")
    C, i2, f2, t2 = run_step("hooks", lambda iss: creative_prompt(j, c, words, Q, F, guide, examples, iss), CREATIVE_SCHEMA,
                             lambda d: assemble(d, words, Q, brief, lang, framing, F.get("tag", {}).get("text", "")), cp, cm, 0.7, 55)
    build_post(F, C)
    if A.hook:
        C["hooks"] = C.get("hooks", []) + [editorial_hook(A.hook)]
        i2, f2 = check_creative(C, words, Q, brief, lang, framing, F.get("tag", {}).get("text", "")); x, y = check_intro(C, words, Q, brief, lang, framing); i2 += x; f2 += y
    meta = dict(project=os.path.basename(j["_dir"]), provider=prov, model=model, backup=backup, auto_publish_allowed=False if backup else None,
                creative_provider=cp if cp != prov else None, creative_model=cm if cp != prov else None,
                seconds=round(time.time() - t0, 1), tries=t1 + t2, transcript=src, holdout=A.holdout)
    P = dict(meta=meta, facts=F, creative=C, issues=i1 + i2, flags=sorted(set(f1 + f2), key=(f1 + f2).index), approved=False, hook_choice=None)
    write(P, out, words); progress(100); emit("output", path=out)
    print(f"planner -> {out} | {prov}/{model}{' (backup)' if backup else ''} | {meta['seconds']} s, {meta['tries']} tries | {len(F.get('beats', []))} beats | "
          f"{len(P['issues'])} problems, {len(P['flags'])} marked ❓")

if __name__ == "__main__":
    main()
