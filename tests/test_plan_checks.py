"""Offline test of the planner's safety checks (no model needed): Telugu numbers, card-to-beat sync, units, labels, hooks.
Run: ~/.venvs/reelstudio/bin/python tests/test_plan_checks.py     (uses the tracked M4 planner fixture)"""
import os, sys, json, copy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "engine"))
import te_numbers as N, planner as PL
W = json.load(open(os.path.join(ROOT, "tests", "fixtures", "m4_planner", "words.json"), encoding="utf-8"))
Q = N.quantities(W); _, _, FR = PL.brand_guide({"brand": "jagan_for_andhra"}); fails = []
def ok(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else "")); cond or fails.append(name)

# 1. Telugu number normalisation (requirement B)
for t, v in [("నాలుగు", 4), ("ఆరు", 6), ("పది", 10), ("పదిహేడు", 17), ("లక్ష", 100000), ("31 లక్షలు", 3100000), ("31 లక్షల", 3100000),
             ("రెండు లక్షల యాభై వేలు", 250000), ("2.5 లక్షలు", 250000), ("750 కోట్లతో", 7.5e9), ("లక్ష కోట్లకు", 1e12), ("17,000", 17000),
             ("మూడు వేల ఐదు వందలు", 3500), ("ఇరవై ఐదు", 25), ("పది లక్షల కోట్లు", 1e13)]:
    ok(f"number '{t}' = {v:,}", N.same(N.value_of(t), v), N.value_of(t))
ok("'ఒక సారి' is not a number", N.value_of("ఒక సారి") is None)
ok("16 numbers found in the reel_002 speech", len(Q) == 16, len(Q))

def beat(a, b, num=None, label="", typ="number", nw=-1): return dict(from_word=a, to_word=b, graphic=dict(type=typ, number_word=nw, number=num or "", label=label))
GOOD = dict(beats=[beat(0, 11, "24", "గంటలు", nw=8), beat(12, 19, "31 లక్షలు", "ఇళ్ల పట్టాలు", nw=13), beat(20, 22, "17,000", "జగనన్న కాలనీలు", nw=20),
                   beat(31, 34, "2.5 లక్షలు", "వాలంటీర్లు", nw=31), beat(73, 74, "నాలుగు", "పోర్టులు", nw=73), beat(82, 87, "17,805 కోట్లు", "ప్రభుత్వ బడులు", nw=82)],
            tag=dict(number_word=13, label="ఇళ్ల పట్టాలు"), post=dict(hashtags=["#AP"]))
i, f = PL.check_facts(copy.deepcopy(GOOD), W, Q, "", "te"); ok("correct plan: no problems", not i, i)
G = copy.deepcopy(GOOD); PL.check_facts(G, W, Q, "", "te")
ok("card time comes from the spoken words (31 లక్షల at 6.87-7.71 s)", G["beats"][1]["graphic"]["spoken"]["s"] == 6.87 and G["beats"][1]["graphic"]["spoken"]["e"] == 7.71)
ok("tag written as 'number — label'", G["tag"]["text"] == "31 లక్షలు — ఇళ్ల పట్టాలు", G["tag"].get("text"))

def bad(name, mutate, expect):
    P = copy.deepcopy(GOOD); mutate(P); i, f = PL.check_facts(P, W, Q, "", "te"); ok(name, any(expect in x for x in i), i)
bad("card number not spoken inside its beat (8B misalignment)", lambda P: P["beats"][3].update(graphic=dict(type="number", number_word=37, number="10,500", label="ఆర్బీకేలు")), "inside the beat")
bad("card with wrong unit (31 instead of 31 లక్షలు)", lambda P: P["beats"][1]["graphic"].update(number="31"), "value and unit")
bad("card with wrong number in the right place", lambda P: P["beats"][2]["graphic"].update(number="15,000"), "value and unit")
bad("card label about a different claim", lambda P: P["beats"][2]["graphic"].update(label="సచివాలయాలు"), "does not match")
bad("tag label about a different claim", lambda P: P["tag"].update(label="మెడికల్ కాలేజీలు"), "tag: label")
def intro(name, text, expect, where="i"):
    i, f = PL.check_intro({"post_intro": text}, W, Q, "", "te", FR); ok(name, any(expect in x for x in (i if where == "i" else f)), (i, f))
intro("invented claim in post intro: '10,000 కోట్లతో మంచినీరు' (8B)", "10,000 కోట్లతో మంచినీరు అందించారు", "not a number the speaker says")
intro("invented number in post intro", "50 లక్షల ఉద్యోగాలు ఇచ్చారు", "not a number the speaker says")
intro("real number tied to the wrong claim is marked ❓", "10,000 మంచినీరు ప్రాజెక్టులు", "Same claim", "f")
G2 = copy.deepcopy(GOOD); PL.check_facts(G2, W, Q, "", "te"); PL.build_post(G2, {"post_intro": "జగన్ చేసిన అభివృద్ధి"})
ok("post text is built from the checked cards only", G2["post"]["caption"].split("\n")[2] == "• 31 లక్షలు — ఇళ్ల పట్టాలు", G2["post"]["caption"])
P = copy.deepcopy(GOOD); P["post"]["hashtags"] = ["జగన్నాథ్ కాలనీలు", "#ఇళ్లపట్టాలు"]; i, f = PL.check_facts(P, W, Q, "", "te")
ok("misspelt name in a hashtag (14B 'జగన్నాథ్') is marked ❓", any("జగన్నాథ్" in x for x in f) and not any("ఇళ్లపట్టాలు" in x for x in f), f)
ok("hashtags get # and no spaces", P["post"]["hashtags"][0] == "#జగన్నాథ్కాలనీలు", P["post"]["hashtags"])
bad("filler-only label (8B '2.5 లక్షలు — మంది')", lambda P: P["beats"][3]["graphic"].update(label="మంది"), "filler")
# overlapping beats are repaired by moving edges (14B / 8B test runs)
P = copy.deepcopy(GOOD); P["beats"] = [beat(0, 10, typ="none"), beat(6, 10, typ="none"), beat(73, 77, "నాలుగు", "పోర్టులు", nw=73), beat(75, 79, "10", "ఫిషింగ్ హార్బర్లు", nw=75),
                                      beat(78, 82, "6", "ఫిష్ ల్యాండింగ్ సెంటర్లు", nw=78), beat(82, 85, "17,805 కోట్లు", "ప్రభుత్వ బడులు", nw=82)]
i, f = PL.check_facts(P, W, Q, "", "te")
ok("overlapping beats repaired: no problems, every card still in its beat", not i and len(P["beats"]) == 5, (i, [(b["from_word"], b["to_word"]) for b in P["beats"]]))
ok("repairs are listed for the user", len(P.get("adjusted", [])) == 4, P.get("adjusted"))
P = copy.deepcopy(GOOD); P["beats"] = [beat(20, 22, "17,000", "జగనన్న కాలనీలు", nw=20), beat(12, 19, "31 లక్షలు", "ఇళ్ల పట్టాలు", nw=13)]
i, f = PL.check_facts(P, W, Q, "", "te"); ok("a beat going back in time is still a problem", any("back in time" in x for x in i), i)
P = copy.deepcopy(GOOD); P["beats"].insert(4, beat(60, 72, "750 కోట్లు", "రక్షిత మంచినీరు", nw=67)); i, f = PL.check_facts(P, W, Q, "", "te")
ok("750 కోట్లతో: before/after ambiguity is marked ❓", not i and any("750" in x for x in f), (i, f))

# 2. Hooks (requirements C, D)
NOV = dict(line1="అసలు జగన్ ఏం చేశాడు?", line2="“24 గంటలు సరిపోవు”", line3="ఇదీ అభివృద్ధి!", headline=["జగన్ చేసింది చెప్పాలంటే..", "24 గంటలు సరిపోవు!"])
H = dict(hooks=[NOV, dict(line1="31 లక్షల ఇళ్ల పట్టాలు", line2="17,000 జగనన్న కాలనీలు", line3="ఇదీ జగన్ లెక్క!", headline=["అక్కచెల్లెమ్మలకు సొంతింటి కల", "నెరవేర్చిన జగనన్న"]),
             dict(line1="ఆపకుండా చెప్పినా", line2="“24 గంటలు సరిపోవు”", line3="ఇదీ నిజం!", headline=["జగన్ చేసిన అభివృద్ధి", "ఒక్కసారి చూడండి"])])
i, f = PL.check_creative(copy.deepcopy(H), W, Q, "", "te", FR); ok("November hook + two good options: no problems", not i, i)
def badh(name, k, upd, expect):
    X = copy.deepcopy(H); X["hooks"][k].update(upd); i, f = PL.check_creative(X, W, Q, "", "te", FR); ok(name, any(expect in x for x in i + f), (i, f))
badh("quote that is not the speaker's words", 0, dict(line2="“48 గంటలు సరిపోవు”"), "exact words")
badh("hook line over 4 words", 0, dict(line1="అసలు జగన్ ఏం చేశాడు అంటే"), "max 4")
badh("headline repeating the hook (14B problem)", 1, dict(headline=["31 లక్షల ఇళ్ల పట్టాలు", "17,000 జగనన్న కాలనీలు"]), "repeats the hook")
badh("invented statistic in a hook", 1, dict(line2="50 లక్షల ఉద్యోగాలు"), "not a number the speaker says")
badh("unit changed in a hook (31 కోట్లు)", 1, dict(line1="31 కోట్ల ఇళ్ల పట్టాలు"), "not a number the speaker says")
badh("English line for a Telugu brand", 2, dict(line3="This is development"), "Telugu script")
X = copy.deepcopy(H); X["hooks"] = X["hooks"][:2]; i, f = PL.check_creative(X, W, Q, "", "te", FR); ok("fewer than 3 options is a problem", any("need 3 hook options" in x for x in i))
X = copy.deepcopy(H); X["hooks"][2].update(line3="ఉచిత విమాన ప్రయాణం"); i, f = PL.check_creative(X, W, Q, "", "te", FR)
ok("new words (possible new claim) are marked ❓", any("not from the speech" in x for x in f), f)

# candidate hooks -> options built by code
CAND = dict(openers=["అసలు జగన్ ఏం చేశాడు?", "జగన్ ఏం చేశాడు అని చెప్పాలంటే", "ఇదీ జగన్ లెక్క!", "ఎన్ని చెప్పాలి?", "50 లక్షల ఉద్యోగాలు"],
            quotes=[dict(from_word=8, to_word=10), dict(from_word=0, to_word=9)], payoffs=["ఇదీ అభివృద్ధి!", "ఇదీ నిజం!", "“48 గంటలు” అంతే", "చూడండి మార్పు!"],
            headlines=[dict(line1="జగన్ చేసింది చెప్పాలంటే..", line2="24 గంటలు సరిపోవు!"), dict(line1="అభివృద్ధి లెక్కలు", line2="ఒక్కసారి చూడండి"),
                       dict(line1="ఇదీ జగన్ లెక్క!", line2="జగనన్న అభివృద్ధి")], post_intro="జగన్ చేసిన అభివృద్ధి లెక్కలు చూడండి")
X = copy.deepcopy(CAND); i, f = PL.assemble(X, W, Q, "", "te", FR)
ok("candidates: valid ones build 3 options with no problems", not i and len(X["hooks"]) == 3, (i, X.get("hooks")))
ok("quote line is the transcript's exact words", X["hooks"][0]["line2"] == "“24 గంటలు సరిపోవు”", X["hooks"][0]["line2"])
ok("long, invented-number and fake-quote candidates are rejected", len(X["rejected"]) == 4, X["rejected"])
ok("a headline that repeats the opener is not paired with it", all(X["hooks"][k]["headline"][0] != X["hooks"][k]["line1"] for k in range(3)), X["hooks"])
X = copy.deepcopy(CAND); X["openers"] = X["openers"][1:2]; i, f = PL.assemble(X, W, Q, "", "te", FR)
ok("too few valid candidates is a problem (with reasons for the retry)", any("usable openers" in x for x in i) and any("max 4" in x for x in i), i)
X = dict(hooks=[dict(NOV, line2=NOV["line1"])] + H["hooks"][1:]); i, f = PL.check_creative(X, W, Q, "", "te", FR)
ok("the same line twice in one option is a problem (8B option A)", any("twice" in x for x in i), i)

# ---- fix 3: incomplete Telugu (quotes and lines)
for t in ["అక్కచెల్లెమ్మలకు 31 లక్షల", "15,000 సచివాలయాలు ప్రభుత్వానికి", "చేశాడనే ప్రస్తావన వస్తే", "పట్టాలు సొంతింటి కల నెరవేర్చేలా"]:
    X = copy.deepcopy(H); X["hooks"][0]["line2"] = f"“{t}”"; i, f = PL.check_creative(X, W, Q, "", "te", FR)
    ok(f"incomplete quote rejected: {t}", any("middle of a phrase" in x or "not finished" in x or "without what it counts" in x for x in i), i)
for t in ["“24 గంటలు సరిపోవు”", "“31 లక్షల ఇళ్ల పట్టాలు”", "“2.5 లక్షల మంది వాలంటీర్లు”"]:
    X = copy.deepcopy(H); X["hooks"][0]["line2"] = t; i, f = PL.check_creative(X, W, Q, "", "te", FR); ok(f"complete quote accepted: {t}", not i, i)
X = copy.deepcopy(H); X["hooks"][1]["line3"] = "ప్రజలకు వారధిగా"; i, f = PL.check_creative(X, W, Q, "", "te", FR)
ok("unfinished hook line rejected (ends on -గా is allowed only... ) / ends on 'జగన్ చేసిన'", PL.incomplete("జగన్ చేసిన") is not None)
X = copy.deepcopy(H); X["hooks"][1]["line1"] = "15,000 గ్రామ సచివాలయాలు"; i, f = PL.check_creative(X, W, Q, "", "te", FR)
ok("'15,000 గ్రామ సచివాలయాలు' (commentary line, complete) accepted", not i, i)
X = copy.deepcopy(CAND); X["quotes"] = [dict(from_word=12, to_word=14), dict(from_word=26, to_word=28), dict(from_word=8, to_word=10)]; i, f = PL.assemble(X, W, Q, "", "te", FR)
ok("model quote ranges cut mid-phrase are rejected, the complete one is used", not i and all(h["line2"] == "“24 గంటలు సరిపోవు”" for h in X["hooks"]), (i, X["rejected"]))

# ---- fix 2: label and hashtag limits
bad("card label over 3 words (8B)", lambda P: P["beats"][1]["graphic"].update(label="ఇళ్ల పట్టాలు సొంతింటి కల"), "max 3")
bad("tag label over 3 words (14B)", lambda P: P.update(tag=dict(number_word=82, label="ప్రభుత్వ బడులు నాడు నేడు")), "max 3")
bad("more than 8 hashtags (8B gave 32)", lambda P: P["post"].update(hashtags=[f"#ఇళ్లపట్టాలు{k}" for k in range(9)]), "max 8")
bad("filler hashtag (#సార్)", lambda P: P["post"].update(hashtags=["#సార్"]), "filler")

# ---- fix 4: guarded correction of misplaced cards
SHIFT = copy.deepcopy(GOOD)       # 8B pattern: every card sits one beat too early
SHIFT["beats"] = [beat(0, 11, "31 లక్షలు", "ఇళ్ల పట్టాలు", nw=13), beat(12, 19, "17,000", "జగనన్న కాలనీలు", nw=20), beat(20, 22, typ="none")]
i, f = PL.check_facts(SHIFT, W, Q, "", "te")
ok("misplaced cards with one exact matching claim are moved", not i and SHIFT["beats"][1]["graphic"]["number"] == "31 లక్షలు" and SHIFT["beats"][2]["graphic"]["number"] == "17,000", (i, [b["graphic"] for b in SHIFT["beats"]]))
ok("each move is recorded: original beat, new beat, reason, original error", len(SHIFT["corrections"]) == 2 and all(k in SHIFT["corrections"][0] for k in ("from_beat", "to_beat", "reason", "original_error")), SHIFT.get("corrections"))
ok("moved cards are marked ❓ (approval needs --checked)", sum("was moved" in x for x in f) == 2, f)
ok("moved card's time comes from the spoken words", SHIFT["beats"][1]["graphic"]["spoken"]["s"] == 6.87)
X = copy.deepcopy(GOOD); X["beats"] = [beat(0, 11, "31 లక్షలు", "ఉద్యోగాలు", nw=13), beat(12, 19, typ="none")]; i, f = PL.check_facts(X, W, Q, "", "te")
ok("label with a new claim is not moved - blocked for review", any("not corrected" in x for x in i) and not X.get("corrections"), i)
X = copy.deepcopy(GOOD); X["beats"] = [beat(0, 11, "31 లక్షలు", "ఇళ్ల పట్టాలు", nw=13), beat(12, 19, "31 లక్షలు", "ఇళ్ల పట్టాలు", nw=13)]
i, f = PL.check_facts(X, W, Q, "", "te"); ok("same card already in the right beat: duplicate not doubled", not X.get("corrections") or len(X["corrections"]) <= 1, X.get("corrections"))
X = copy.deepcopy(GOOD); X["beats"] = [beat(0, 11, "31 లక్షలు", "ఇళ్ల పట్టాలు", nw=13), beat(12, 19, typ="text", label="సొంతింటి కల")]
i, f = PL.check_facts(X, W, Q, "", "te"); ok("target beat has another graphic: not moved, blocked", any("already has the graphic" in x for x in i), i)
W2 = [dict(w=x, s=k * 0.5, e=k * 0.5 + 0.4) for k, x in enumerate("10,000 విలేజ్ క్లినిక్‌లు ఇక్కడ ఇంకా 10,000 విలేజ్ క్లినిక్‌లు అక్కడ".split())]; Q2 = N.quantities(W2)
X = dict(beats=[beat(3, 4, "10,000", "విలేజ్ క్లినిక్‌లు", typ="number", nw=-1)], tag=dict(number_word=0, label="విలేజ్ క్లినిక్‌లు"), post=dict(hashtags=[]))
i, f = PL.check_facts(X, W2, Q2, "", "te"); ok("number matching two spoken claims is not guessed - blocked", any("more than one spoken claim" in x for x in i), i)

# ---- fix 1: editorial hook D
D = PL.editorial_hook("అసలు జగన్ ఏం చేశాడు? / 24 గంటలు సరిపోవు! / ఇదీ అభివృద్ధి! / జగన్ చేసిన పనులపై చర్చ / 24 గంటలు సరిపోవంటున్న వక్త")
ok("option D keeps the wording exactly", [D["line1"], D["line2"], D["line3"]] + D["headline"] == ["అసలు జగన్ ఏం చేశాడు?", "24 గంటలు సరిపోవు!", "ఇదీ అభివృద్ధి!", "జగన్ చేసిన పనులపై చర్చ", "24 గంటలు సరిపోవంటున్న వక్త"])
X = copy.deepcopy(H); X["hooks"].append(D); i, f = PL.check_creative(X, W, Q, "", "te", FR)
ok("option D passes the checks", not i, i)
ok("option D: speaker's words without quotes are marked as commentary ❓", any("option D" in x and "commentary" in x for x in f), f)
ok("option D: headline that reports the speaker is compared with his words ❓", any("option D" in x and "check it matches his words" in x for x in f), f)
P1 = dict(facts=copy.deepcopy(G), creative=dict(hooks=X["hooks"]), hook_choice="D"); h1 = PL.plan_hash(P1); P1["facts"]["beats"][0]["graphic"]["label"] = "రోజులు"
ok("approval fingerprint changes when the plan is edited", PL.plan_hash(P1) != h1)

# ---- code-first facts (approved 10 Nov): beats, cards and labels come from the transcript
Qc = N.quantities(W); CL, TAIL = PL.build_claims(W, Qc)
EXP = ["24 — గంటలు", "31 లక్షలు — ఇళ్ల పట్టాలు", "17,000 — జగనన్న కాలనీలు", "15,000 — సచివాలయాలు", "2.5 లక్షలు — వాలంటీర్లు", "10,500 — ఆర్బీకేలు",
       "10,000 — విలేజ్ క్లినిక్‌లు", "25 లక్షలు — ఆరోగ్యశ్రీ పరిమితి", "17 — మెడికల్ కాలేజీలు", "750 కోట్లు — రక్షిత మంచినీరు", "4 — పోర్టులు",
       "10 — ఫిషింగ్ హార్బర్లు", "6 — ఫిష్ ల్యాండింగ్ సెంటర్లు", "17,805 కోట్లు — ప్రభుత్వ బడులు", "130 — భారీ ప్రాజెక్టులు", "లక్ష కోట్లు — పెట్టుబడులు"]
got = [f"{c['number']} — {c['label']}" for c in CL]
ok("16 claims with the speaker's own 1-3 word labels", got == EXP, [x for x in got if x not in EXP])
ok("beats cover the whole speech, in order, without gaps or overlaps", CL[0]["start"] == 0 and all(CL[k]["start"] == CL[k - 1]["end"] + 1 for k in range(1, len(CL))) and TAIL and TAIL[1] == len(W) - 1)
seg = lambda c: " ".join(w["w"] for w in W[c["start"]:c["end"] + 1])
ok("purpose phrase goes with its number ('అన్నదాతకు ఆసరాగా 10,500 ఆర్బీకేలు')", seg(CL[5]) == "అన్నదాతకు ఆసరాగా 10,500 ఆర్బీకేలు", seg(CL[5]))
ok("sentence end stays with its claim ('… 24 గంటలు సరిపోవు సార్')", seg(CL[0]).endswith("సరిపోవు సార్"), seg(CL[0]))
ok("'నాడు నేడు' stays with the schools", seg(CL[13]).endswith("నాడు నేడు"), seg(CL[13]))
DC = PL.default_choice(CL); F0 = PL.facts_from_choice(CL, TAIL, DC, W); F0["claims_by_code"] = True
ok("default choice: no card for '24 గంటలు', tag = 31 లక్షలు — ఇళ్ల పట్టాలు", 1 not in DC["feature"] and CL[DC["tag"] - 1]["label"] == "ఇళ్ల పట్టాలు")
i, f = PL.check_facts(F0, W, Qc, "", "te", FR)
ok("code-built facts pass every check; only the real 750 కోట్లతో ambiguity is ❓", not i and len(f) == 1 and "750" in f[0], (i, f))
ok("every card is timed to the spoken words", all(b["graphic"].get("spoken") for b in F0["beats"] if b["graphic"].get("type") == "number"))
F1 = PL.facts_from_choice(CL, TAIL, dict(feature=[2, 99, "x", 3], tag=42, hashtags=[]), W)
ok("model choice with invalid ids: only valid claims get cards, bad tag gives no tag", F1["feature"] == [2, 3] and not F1["tag"], (F1["feature"], F1["tag"]))
ok("choice check reports invalid ids for the retry", any("not claim numbers" in x for x in PL.check_choice(dict(feature=[99], tag=1, hashtags=[]), CL)[0]))
F2 = PL.facts_from_choice(CL, TAIL, dict(feature=[2, 3], tag=2, hashtags=["#ఇళ్లపట్టాలు", "#జగన్నాథ్", "#సార్"] + [f"#కాలనీలు{k}" for k in range(8)]), W); F2["claims_by_code"] = True
i, f = PL.check_facts(F2, W, Qc, "", "te", FR)
ok("bad hashtags are left out (listed), never block the plan", not i and "#జగన్నాథ్" not in F2["post"]["hashtags"] and len(F2["post"]["hashtags"]) <= 8 and any("left out" in x for x in F2["adjusted"]), (i, F2["post"]["hashtags"]))
CQ = [" ".join(w["w"] for w in W[a:b + 1]) for a, b in PL.code_quotes(W, Qc)]
ok("program's own quote candidates are complete phrases ('24 గంటలు సరిపోవు')", CQ[:2] == ["24 గంటలు సరిపోవు", "31 లక్షల ఇళ్ల పట్టాలు"], CQ)
X = dict(openers=["అసలు ఏం చేశాడు?"], quotes=[], payoffs=["ఇదీ అభివృద్ధి!", "ఇదీ నిజం!"], headlines=[dict(line1="జగన్ చేసింది చెప్పాలంటే..", line2="లెక్క చూడండి!")], post_intro="")
i, f = PL.assemble(X, W, Q, "", "te", FR)
ok("few valid candidates still give 3 different options (combinations)", not i and len(X["hooks"]) == 3 and len({(h["line1"], h["line2"], h["line3"]) for h in X["hooks"]}) == 3, (i, X.get("hooks")))

# ---- final fix 1: achievement-only tags (8B chose '24 — గంటలు')
i, _ = PL.check_choice(dict(feature=[2, 3], tag=1, hashtags=[]), CL)
ok("tag '24 — గంటలు' (time talk) is rejected for the retry, with the allowed claims listed", any("time talk" in x and "2" in x for x in i), i)
F3 = PL.facts_from_choice(CL, TAIL, dict(feature=[1, 2], tag=1, hashtags=[]), W)
ok("a time-talk tag never reaches the plan", not F3["tag"], F3["tag"])
X = copy.deepcopy(GOOD); X["tag"] = dict(number_word=8, label="గంటలు"); i, f = PL.check_facts(X, W, Qc, "", "te")
ok("a hand-edited time-talk tag is a problem (blocks approval)", any("time talk" in x for x in i), i)
Wt = [dict(w=x, s=k * 0.5, e=k * 0.5 + 0.4) for k, x in enumerate("24 గంటలు సరిపోవు సార్ మూడు రోజులు చాలు".split())]; Qt = N.quantities(Wt); Ct, Tt = PL.build_claims(Wt, Qt)
dc = PL.default_choice(Ct); Ft = PL.facts_from_choice(Ct, Tt, dc, Wt); Ft["claims_by_code"] = True; i, f = PL.check_facts(Ft, Wt, Qt, "", "te")
ok("no achievement in the speech -> no tag (not invented), and that is not a problem", dc["tag"] is None and not Ft["tag"] and not i, (dc, Ft["tag"], i))
ok("program's default tag is an achievement: 31 లక్షలు — ఇళ్ల పట్టాలు", CL[PL.default_choice(CL)["tag"] - 1]["label"] == "ఇళ్ల పట్టాలు")
# ---- final fix 2: complete, meaningful quotes
for t, good in [("జగన్ ఏం చేశాడనే ప్రస్తావన", False), ("24 గంటలు", False), ("అసలు జగన్", False), ("31 లక్షల ఇళ్ల పట్టాలు", True),
                ("24 గంటలు సరిపోవు", True), ("24 గంటలు సరిపోవు సార్", True), ("15,000 సచివాలయాలు", True)]:
    X = copy.deepcopy(H); X["hooks"][0]["line2"] = f"“{t}”"; i, f = PL.check_creative(X, W, Qc, "", "te", FR)
    ok(f"quote “{t}” {'accepted' if good else 'rejected'}", (not i) if good else any("option A" in x and "quote" in x for x in i), i)
X = copy.deepcopy(H); X["hooks"][0]["line2"] = "“24 గంటలు చాలవు”"; i, f = PL.check_creative(X, W, Qc, "", "te", FR)
ok("a quote that is not in the transcript is rejected (attribution must match the source)", any("not the speaker's exact words" in x for x in i), i)
X = dict(CAND); X = copy.deepcopy(X); X["quotes"] = [dict(from_word=1, to_word=4)]; i, f = PL.assemble(X, W, Qc, "", "te", FR)
ok("8B's quote range 'జగన్ ఏం చేశాడనే ప్రస్తావన' is rejected in drafting too", any("ప్రస్తావన" in x for x in X["rejected"]), X["rejected"])

# ---- found in the final acceptance run: a quote must stay inside one claim
X = copy.deepcopy(H); X["hooks"][0]["line2"] = "“నేడు 130 భారీ ప్రాజెక్టులు”"; i, f = PL.check_creative(X, W, Qc, "", "te", FR)
ok("quote 'నేడు 130 భారీ ప్రాజెక్టులు' (takes 'నేడు' from 'నాడు నేడు') is rejected", any("two different claims" in x for x in i), i)
X = copy.deepcopy(H); X["hooks"][0]["line2"] = "“130 భారీ ప్రాజెక్టులు”"; i, f = PL.check_creative(X, W, Qc, "", "te", FR)
ok("quote '130 భారీ ప్రాజెక్టులు' is accepted", not i, i)

print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)
