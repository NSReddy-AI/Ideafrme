"""Spoken numbers -> values, for checking plan numbers against what was actually said (Telugu + English).
  quantities(words)  -> every number the speaker says: value, unit, word span, times, subject words after it
  value_of(text)     -> the value of a number written in a card / hook / tag ("31 లక్షలు", "2.5 లక్షలు", "నాలుగు", "17,000")
  same(a, b)         -> two values are equal (tolerant to float rounding)
Units multiply: 31 లక్షల = 3,100,000; 750 కోట్లతో = 7,500,000,000; లక్ష కోట్లకు = 10^12; రెండు లక్షల యాభై వేలు = 250,000.
Telugu case endings are understood on unit words (లక్షల, లక్షలు, కోట్లతో, కోట్లకు, వేల, వేలు, వందల ...)."""
import re, unicodedata

ONES = {"సున్నా": 0, "ఒకటి": 1, "ఒక": 1, "ఒక్క": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5, "అయిదు": 5, "ఆరు": 6, "ఏడు": 7,
        "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10, "పదకొండు": 11, "పన్నెండు": 12, "పదమూడు": 13, "పద్నాలుగు": 14, "పదిహేను": 15,
        "పదహారు": 16, "పదిహేడు": 17, "పద్దెనిమిది": 18, "పంతొమ్మిది": 19, "ఇరవై": 20, "ముప్పై": 30, "ముప్ఫై": 30, "నలభై": 40,
        "యాభై": 50, "ఏభై": 50, "అరవై": 60, "డెబ్బై": 70, "ఎనభై": 80, "తొంభై": 90, "అర": 0.5, "సగం": 0.5,
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
# unit stems: (stem, value, display name). Longest stems first so "వేల" does not swallow other words.
UNITS = [("కోట్ల", 10**7, "కోట్లు"), ("కోటి", 10**7, "కోటి"), ("కోట్లు", 10**7, "కోట్లు"),
         ("లక్షల", 10**5, "లక్షలు"), ("లక్షలు", 10**5, "లక్షలు"), ("లక్ష", 10**5, "లక్ష"),
         ("వేల", 1000, "వేలు"), ("వేలు", 1000, "వేలు"), ("వెయ్యి", 1000, "వెయ్యి"), ("వేయి", 1000, "వెయ్యి"),
         ("వందల", 100, "వందలు"), ("వందలు", 100, "వందలు"), ("వంద", 100, "వంద"),
         ("crore", 10**7, "crore"), ("crores", 10**7, "crore"), ("lakh", 10**5, "lakh"), ("lakhs", 10**5, "lakh"),
         ("billion", 10**9, "billion"), ("million", 10**6, "million"), ("thousand", 1000, "thousand"), ("hundred", 100, "hundred")]
ENDINGS = ("తో", "కు", "కి", "లో", "ని", "ను", "గా", "పైగా", "వరకు", "మంది", "")   # case endings allowed after a unit / number word
PUNCT = r"[\"'“”‘’.,!?;:()\[\]{}…\-–—|।‌‍]"

def clean(w): return re.sub(PUNCT, "", unicodedata.normalize("NFC", w)).strip().lower()

def _digits(w):
    """'17,805' -> 17805, '2.5' -> 2.5 (and digits glued to Telugu: '31లక్షల' -> (31, 'లక్షల'))."""
    m = re.match(r"^(\d[\d,]*(?:\.\d+)?)(.*)$", unicodedata.normalize("NFC", w).strip().strip("\"'“”‘’"))
    if not m: return None, None
    v = float(m.group(1).replace(",", "")); return (int(v) if v == int(v) else v), m.group(2)

def _unit(w):
    c = clean(w)
    if not c: return None
    for stem, val, name in UNITS:
        if c.startswith(stem) and c[len(stem):] in ENDINGS: return val, name
    return None

def _ones(w):
    c = clean(w)
    for e in ENDINGS:
        if e and c.endswith(e) and c[: -len(e)] in ONES: return ONES[c[: -len(e)]]
    return ONES.get(c)

def _kind(w):
    """('num', value, rest) | ('unit', value, name) | None"""
    v, rest = _digits(w)
    if v is not None: return ("num", v, rest)
    u = _unit(w)
    if u: return ("unit",) + u
    o = _ones(w)
    if o is not None: return ("num", o, "")
    return None

def _combine(tokens):
    """[('num',v)|('unit',v,name)] -> (value, display unit). Indian/English place value:
    'రెండు లక్షల యాభై వేలు' = 2*10^5 + 50*1000; 'లక్ష కోట్లు' = 10^5 * 10^7 (a bigger unit multiplies everything before it)."""
    total, cur, last_big, name = 0, 0, None, None
    for t in tokens:
        if t[0] == "num": cur += t[1]; continue
        mult = t[1]
        if mult < 1000: cur = (cur or 1) * mult; name = name or t[2]
        elif last_big is not None and mult > last_big: total = (total + cur) * mult; cur = 0; last_big = mult; name = t[2]
        else:
            total += (cur or 1) * mult; cur = 0
            if last_big is None: last_big = mult; name = t[2]
    v = total + cur
    return (int(v) if float(v).is_integer() else round(v, 6)), name

def quantities(words, subject_words=4):
    """Every spoken number in a word list ([{w,s,e}] or [str]). A number = digits / number words followed by unit words.
    'ఒక'/'ఒక్క'/'అర' alone (= 'a', 'half') only count when a unit follows ('ఒక లక్ష')."""
    W = [x["w"] if isinstance(x, dict) else x for x in words]; out, i = [], 0
    while i < len(W):
        k = _kind(W[i])
        if not k: i += 1; continue
        toks, j = [], i
        while j < len(W):
            k = _kind(W[j])
            if not k: break
            if k[0] == "num" and toks and toks[-1][0] == "num" and not (toks[-1][1] >= 20 and k[1] < 10):   # 'పది 10' = two numbers
                break
            toks.append(k[:2] if k[0] == "num" else k)
            if k[0] == "num" and k[2]:                          # digits glued to a unit: '31లక్షల'
                u = _unit(k[2])
                if u: toks.append(("unit",) + u)
            j += 1
        if len(toks) == 1 and toks[0][0] == "num" and clean(W[i]) in ("ఒక", "ఒక్క", "అర", "సగం", "one"):
            i += 1; continue
        v, unit = _combine(toks)
        q = dict(value=v, unit=unit, a=i, b=j - 1, text=" ".join(W[i:j]))
        if isinstance(words[0], dict): q.update(s=words[i].get("s"), e=words[j - 1].get("e"))
        out.append(q); i = j
    # the claim around each number: words after it up to the next number, and words before it back to the previous one
    for k, q in enumerate(out):
        nxt = out[k + 1]["a"] if k + 1 < len(out) else len(W); prv = out[k - 1]["b"] + 1 if k else 0
        q["subject"] = W[q["b"] + 1: min(nxt, q["b"] + 1 + subject_words)]
        q["before"] = W[max(prv, q["a"] - 6): q["a"]]
    return out

def value_of(text):
    """The value of the FIRST number written in a short text, or None."""
    q = quantities(re.split(r"\s+", (text or "").replace("—", " ").replace("-", " ").strip()) if text and text.strip() else [])
    return q[0]["value"] if q else None

def all_values(text):
    toks = [t for t in re.split(r"\s+", (text or "").replace("—", " ").strip()) if t]
    return quantities(toks) if toks else []

def same(a, b):
    return a is not None and b is not None and abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(a)))

def display(q):
    """How a spoken quantity is written on a card / tag: digits as said + the unit in its plain form ('31 లక్షలు')."""
    v = q["value"]; unit = q.get("unit"); mult = {"కోట్లు": 10**7, "కోటి": 10**7, "లక్షలు": 10**5, "లక్ష": 10**5, "crore": 10**7, "lakh": 10**5,
                                                 "million": 10**6, "billion": 10**9}.get(unit)
    if mult and v >= mult:
        n = v / mult; n = int(n) if float(n).is_integer() else round(n, 2)
        if n >= 1000 and unit in ("కోట్లు", "కోటి") and (n / 10**5).is_integer(): return f"{int(n / 10**5)} లక్షల కోట్లు" if n > 10**5 else "లక్ష కోట్లు"
        if n == 1 and unit in ("లక్ష", "లక్షలు"): return "లక్ష"
        if n == 1 and unit in ("కోటి", "కోట్లు"): return "కోటి"
        return f"{n:,} {'లక్షలు' if unit == 'లక్ష' else unit}" if isinstance(n, int) and n >= 1000 else f"{n} {'లక్షలు' if unit == 'లక్ష' else unit}"
    return f"{v:,}" if isinstance(v, int) and v >= 1000 else f"{v}"

def stem(w, n=4):
    c = clean(w); return c[:n] if len(c) >= n else c

def related(label, words, n=4):
    """True if any content word of the label shares its start with any of the given words (Telugu inflects at the end)."""
    L = [stem(x, n) for x in re.split(r"\s+", label or "") if len(clean(x)) >= 2 and not _kind(x)]
    S = {stem(x, n) for x in words if len(clean(x)) >= 2}
    return any(l in S or any(s.startswith(l) or l.startswith(s) for s in S if len(s) >= 3) for l in L if len(l) >= 3)

# ---------------------------------------------------------------------------------------------------------------------------
# Numbers -> spoken Telugu words (added in M4 B1 for narration). Everything above is unchanged.
# The narration voice reads words, not digits: "31 లక్షల" is spoken as "ముప్పై ఒక్క లక్షల". Every conversion is read back
# with value_of() above; anything that does not read back exactly is marked "review" and must be checked by the user.
_UNDER20 = ["సున్నా", "ఒక్క", "రెండు", "మూడు", "నాలుగు", "ఐదు", "ఆరు", "ఏడు", "ఎనిమిది", "తొమ్మిది", "పది", "పదకొండు", "పన్నెండు",
            "పదమూడు", "పద్నాలుగు", "పదిహేను", "పదహారు", "పదిహేడు", "పద్దెనిమిది", "పంతొమ్మిది"]
_TENS = {2: "ఇరవై", 3: "ముప్పై", 4: "నలభై", 5: "యాభై", 6: "అరవై", 7: "డెబ్బై", 8: "ఎనభై", 9: "తొంభై"}

def _w99(n):
    if n < 20: return _UNDER20[n]
    t, r = divmod(n, 10); return _TENS[t] + (" " + _UNDER20[r] if r else "")

def _w999(n):
    h, r = divmod(n, 100)
    if not h: return _w99(r)
    if h == 1: return "వంద" if not r else "నూట " + _w99(r)          # 100 = వంద, 105 = నూట ఐదు
    return _w99(h) + " వందల" + (" " + _w99(r) if r else "")         # 200 = రెండు వందల (before a noun)

def to_words(n):
    """Whole number -> Telugu words in the form used BEFORE a noun or unit (ఒక్క, వందల, వేల, లక్షల, కోట్ల).
    Indian place values: 3,10,00,000 = మూడు కోట్ల పది లక్షల. 1 lakh / 1 crore are said 'ఒక లక్ష' / 'ఒక కోటి'."""
    n = int(n)
    if n < 0: return "మైనస్ " + to_words(-n)
    if n == 0: return _UNDER20[0]
    parts = []
    cr, n = divmod(n, 10**7)
    if cr: parts.append("ఒక కోటి" if cr == 1 else to_words(cr) + " కోట్ల")
    lk, n = divmod(n, 10**5)
    if lk: parts.append("ఒక లక్ష" if lk == 1 else _w99(lk) + " లక్షల")
    th, n = divmod(n, 1000)
    if th: parts.append("వెయ్యి" if th == 1 else _w99(th) + " వేల")
    if n: parts.append(_w999(n))
    return " ".join(parts)

def _final(words):
    """The same number standing alone at the end of a phrase: ...ఒక్క -> ...ఒకటి, ...వేల -> ...వేలు, లక్షల -> లక్షలు, కోట్ల -> కోట్లు."""
    for a, b in ((" ఒక్క", " ఒకటి"), (" వందల", " వందలు"), (" వేల", " వేలు"), (" లక్షల", " లక్షలు"), (" కోట్ల", " కోట్లు")):
        if (" " + words).endswith(a): return (" " + words)[: -len(a)].strip() + b if words != a.strip() else b.strip()
    return "ఒకటి" if words == "ఒక్క" else words

def _reads_back(words, value):
    """True if value_of() above reads the words back as exactly this value ('నూట' = 'వంద' for the reader)."""
    if value == 1 and words in ("ఒక్క", "ఒకటి"): return True       # the reader skips a lone 'one' on purpose (it also means 'a')
    w = words.replace("నూట", "వంద").replace("న్నర", "")
    v = value_of(w)
    return v is not None and same(v, value)

_NUM = re.compile(r"^(\d[\d,]*(?:\.\d+)?)(%?)(.*)$")

def spoken(text):
    """A narration sentence -> (say, tokens, numbers).
    say     = the sentence as it is spoken (digits replaced by Telugu words; every other character kept exactly)
    tokens  = [{"t": written word, "say": [spoken words]}] (used to time each written caption word)
    numbers = [{"text": "31", "say": "ముప్పై ఒక్క", "value": 31, "check": "ok"|"review", "why": ...}]"""
    toks = text.split()
    out, nums = [], []
    for k, t in enumerate(toks):
        lead = re.match(r"^[\"'“”‘’(\[]*", t).group(0); core = t[len(lead):]
        m = _NUM.match(core)
        if not m: out.append(dict(t=t, say=[t])); continue
        raw, pct, rest = m.groups(); v = float(raw.replace(",", ""))
        if "," in raw and not re.fullmatch(r"\d{1,3}(,\d{2})*,\d{3}|\d{1,3}(,\d{3})+", raw): why = "unusual digit grouping"
        else: why = None
        nxt = toks[k + 1] if k + 1 < len(toks) else ""
        ends = not nxt or bool(re.search(r"[.!?।]$", core)) or bool(rest and re.fullmatch(r"[.,!?;:।\"'”’)\]]+", rest))
        if v == int(v):
            w = to_words(int(v)); w = _final(w) if (ends and not pct and not rest.strip(".,!?;:।\"'”’)]")) else w
        elif round(v % 1, 6) == 0.5:
            base = to_words(int(v)) if int(v) else ""
            w = ("ఒకటిన్నర" if int(v) == 1 else (base + "న్నర" if base else "అర")); why = why or "half (న్నర): check the spoken form"
        else:
            w = raw; why = "decimal: write the spoken form by hand"
        if pct: w += " శాతం"
        unit = _unit(rest) or (_unit(nxt) if nxt else None)
        ok = why is None and _reads_back(w if not pct else w[: -len(" శాతం")], int(v) if v == int(v) else v)
        tail = re.sub(r"[.,!?;:।\"'”’)\]]+$", "", rest)
        if not rest or not tail: joined = lead + w + rest                          # nothing or only punctuation after the digits
        elif _unit(rest): joined = lead + w + " " + rest                           # '31లక్షల' -> 'ముప్పై ఒక్క లక్షల'
        else:                                                                       # a case ending glued on: '2024లో' -> '...నాలుగులో'
            joined = lead + w + rest; why = why or "case ending joined to the number: check the spoken form"; ok = False
        say = joined.split()
        out.append(dict(t=t, say=say))
        nums.append(dict(text=t, say=" ".join(say), value=int(v) if v == int(v) else v, unit=unit[1] if unit else None,
                         check="ok" if ok else "review", why=why or (None if ok else "does not read back as the same number")))
    return " ".join(w for o in out for w in o["say"]), out, nums
