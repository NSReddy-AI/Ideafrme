# M4 planner hook review (Qwen3, local) - grading sheet

Prepared 11 Nov 2026 for Gate D. **Status: OWNER DECISION 11 Nov 2026 - accepted for M4 as a human-supervised editorial assistant only** (see the end). Not a quality pass. The "pre-review" column is an AI assessment to speed up your
review; it is not a grade. Human editorial approval stays mandatory for every reel (the engine refuses to build/render without it).
Sources: `tests/out/planner_qwen3_14b.md`, `tests/out/planner_qwen3_8b.md` (reel_002 news speech, approved hook held out),
`projects/demo_speaker_said/build/plan.md`, `projects/2026-11-11_speaker_said/build/plan.md` ("What jagan said" rally speech).

Criteria: N = natural Telugu · G = grounded in the speech (no new claim) · H = headline relevant to the reel · Q = quotes complete and verbatim.

## A. reel_002 news speech - Qwen3 14B (approved model)
| Opt | Hook (line1 / line2 / line3) · headline | Pre-review | Owner grade |
|---|---|---|---|
| A | జగన్ ఏం చేశాడు? / “24 గంటలు సరిపోవు” / ఇదీ అభివృద్ధి! · ప్రభుత్వ బడులు పెరిగాయి / ఇప్పుడు ప్రభుత్వ బడులు ఉన్నాయి | Hook N✓ G✓ Q✓ (close to the approved November direction). Headline G✗: "schools increased / now there are government schools" is not said (speech: ₹17,805 crore for schools, Nadu-Nedu); H weak (one claim of nine). | |
| B | అసలు ఏం జరిగింది? / “24 గంటలు సరిపోవు” / ఇది నిజం అయ్యేది! · నాడు నేడు ప్రభుత్వ బడులు / ప్రభుత్వ బడులు పెరిగాయి | Line3 N✗ ("this would have become true!"). Headline G✗ ("increased"). | |
| C | ఇది అభివృద్ధి అయ్యేది? / “24 గంటలు సరిపోవు” / ఇదీ సాక్ష్యం! · ప్రభుత్వ బడులు పెట్టుబడులతో / ఇలా సాకారం అయ్యేది | Line1 N✗. Headline G✗: joins the schools claim with "investments realised" from the projects claim. | |
| D | (owner's own, held-out November wording) | Reference. | |
Tag 17,805 కోట్లు — ప్రభుత్వ బడులు: G✓. ❓ beat 10 (750 కోట్లతో label) correctly raised for the editor.

## B. reel_002 - Qwen3 8B (backup only, never for automatic use)
| Opt | Hook · headline | Pre-review | Owner grade |
|---|---|---|---|
| A | అసలు ఏం చేశాడు? / “24 గంటలు సరిపోవు” / ఇదీ అభివృద్ధి! · ఇది మార్పు అయింది / ఇది నిజం అయింది | Hook acceptable; headline generic, N weak. | |
| B | ఏం కారణం అయింది? / … / ఇది నిజం అయింది! · ఇది అభివృద్ధి అయింది / ఇది సాక్ష్యం అయింది | N✗ throughout. | |
| C | ఇదీ నిజం అంటే ఏం? / … / ఇది మార్పు అయింది! · ఇది చూడండి / ఇది లెక్కలు అయింది | N✗ ("ఇది లెక్కలు అయింది" ungrammatical). | |

## C. "What jagan said" rally speech (political) - Qwen3 14B, two real plans
| Plan / Opt | Hook · headline | Pre-review | Owner grade |
|---|---|---|---|
| demo A | మనకు ఏం కావాలి? / “ఇరవై స్థానాల్లోనే మనల్ని” / ఇదీ పోటీ! · పోటీ ఎందుకు అవసరం? / ఇదీ పోటీ పెట్టిన స్థానం! | **Q✗** quote cut before the verb (speech: "…ఇరవై స్థానాల్లోనే మనల్ని పోటీ చేయనిస్తా ఉన్నారు" = they let us contest only 20 seats) - meaning lost; G✗ "why is a contest needed?" is not his point; H✗. | |
| demo B | పోటీలో ఏం జరుగుతుంది? / (same quote) / ఇది స్థానాలు! · స్థానాలు ఎక్కడున్నాయి? / … | Q✗; line3 N✗; headline irrelevant. | |
| demo C | ఎందుకు పోటీ పెట్టారు? / (same quote) / ఇదీ స్పష్టత! · … / ఇదీ పోటీ కావాలి! | Q✗; N✗ ("ఇదీ పోటీ కావాలి!"). | |
| app A | అసలు ఎందుకు పోటీ పెట్టారు? / (same quote) / ఇదీ అభివృద్ధి! · పోటీ పెట్టినందుకు కారణం ఏంటి? / ఇది సాక్ష్యం! | Q✗; G✗ "ఇదీ అభివృద్ధి!" (development) is unrelated to this speech (brand phrase from another reel). | |
| app B/C | (same pattern: "ఇదీ సత్యం!", "ఇదీ స్పష్టత!") | Q✗; generic. | |
Hashtags (both plans): built from speech-to-text errors (#గూగుల్అనిపిస్తే, #స్మోగాలసౌండ్, #కొడితేక్షంప) - all ❓-flagged, so the gate works; unusable.
Tag 40 — స్థానాలు: number spoken, but the point of the speech is "only 20 of 40" - editor's call.

## Findings for the release decision
1. **Quality (genuine):** local hooks are drafts, not publishable text. reel_002 option A's hook is usable; headlines invent or merge claims;
   the political speaker plans are not usable without the editor rewriting them (option D).
2. **Safety-check gap (genuine, non-technical blocker for any auto-approval):** the quote-completeness check accepted
   "“ఇరవై స్థానాల్లోనే మనల్ని”" (ends before the verb) although it rejects similar fragments ("ends on చాలానే"). With mandatory human
   approval it is caught by the editor; it should be fixed before any reduced-supervision use. Recorded in the backlog (#25).
3. **Safeguards that work:** every invented word is listed as ❓ "words not from the speech"; approval needs "checked" while ❓ are open;
   option D keeps the editor's exact wording; nothing renders without approval.

## Owner decision (11 Nov 2026)
- [x] **Accepted for M4 as a human-supervised editorial assistant only.** Every suggested hook, headline, quotation, number and factual
  claim requires human review and approval. No automatic publishing (Reel Studio never publishes; rendering refuses unapproved plans).
- [ ] Quote-completeness fix and Telugu quality → consolidated improvement backlog (#25, #26, #27).
