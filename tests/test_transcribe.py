"""Checks engine/transcribe.py against the approved Telugu captions of 'What jagan said' (spelling AND word timing).
Run: ~/.venvs/reelstudio/bin/python tests/test_transcribe.py      (about 3 minutes)
Pass rules: Telugu character errors <= 25%; matched words start within 0.4 s of the approved time for >= 80% of them."""
import os, sys, json, subprocess, difflib, time, unicodedata, re
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PY = sys.executable; OUT = os.path.join(ROOT, "tests", "out"); os.makedirs(OUT, exist_ok=True)
REF = json.load(open(os.path.join(ROOT, "tests", "asr_reference_what_jagan_said.json")))
def say(*a): print(*a, flush=True)
def norm(t): return " ".join(re.sub(r"[\"'“”‘’.,!?;:()\[\]{}…\-–—|।‌‍]", " ", unicodedata.normalize("NFC", t)).split())
def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]
# reference audio: approved segments in order (same as tests/test_asr.py)
wav = os.path.join(OUT, "asr", "ref_raw16k.wav")
if not os.path.exists(wav):
    os.makedirs(os.path.dirname(wav), exist_ok=True); src = os.path.normpath(os.path.join(ROOT, REF["source"])); S = REF["segments_in_order"]
    parts = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(S))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", parts + "".join(f"[a{i}]" for i in range(len(S))) + f"concat=n={len(S)}:v=0:a=1[o]",
                    "-map", "[o]", "-ac", "1", "-ar", "16000", wav], check=True)
R = {}
for lang in ("te", "en"):
    out = os.path.join(OUT, f"transcribe_{lang}.json"); t = time.time()
    r = subprocess.run([PY, os.path.join(ROOT, "engine", "transcribe.py"), "--audio", wav, "--lang", lang, "--out", out], capture_output=True, text=True, encoding="utf-8", errors="replace")
    say(f"== {lang}:", (r.stdout.strip().splitlines() or [""])[-1] or r.stderr[-600:])
    if r.returncode: R[lang] = dict(error=(r.stderr or r.stdout)[-600:]); continue
    T = json.load(open(out)); hyp = T["words"]
    if lang == "en": R[lang] = dict(runs=True, words=len(hyp), seconds=round(time.time() - t, 1), model=T["model"]); continue
    rt, ht = norm(REF["text"]).replace(" ", ""), norm(" ".join(x["w"] for x in hyp)).replace(" ", "")
    cer = lev(rt, ht) / len(rt)
    rw, hw = [norm(x["w"]) for x in REF["words"]], [norm(x["w"]) for x in hyp]
    sm = difflib.SequenceMatcher(a=rw, b=hw, autojunk=False); ds, de = [], []
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            a, b = REF["words"][blk.a + k], hyp[blk.b + k]; ds.append(abs(a["s"] - b["s"])); de.append(abs(a["e"] - b["e"]))
    ds, de = np.array(ds), np.array(de)
    R[lang] = dict(model=T["model"], seconds=round(time.time() - t, 1), cer=round(cer, 3), words=len(hyp), review=T["review_count"],
                   matched_words=f"{len(ds)} of {len(rw)}", start_median_s=round(float(np.median(ds)), 3) if len(ds) else None,
                   start_within_0_4s=round(float(np.mean(ds <= 0.4)), 3) if len(ds) else None, end_median_s=round(float(np.median(de)), 3) if len(de) else None,
                   marked=[(x["w"], x["review"]) for x in hyp if x["review"]][:12])
    say("  ", {k: v for k, v in R[lang].items() if k != "marked"}); say("   marked for review:", R[lang]["marked"])
json.dump(R, open(os.path.join(OUT, "transcribe_report.json"), "w"), ensure_ascii=False, indent=1)
te = R.get("te", {})
ok = te.get("cer") is not None and te["cer"] <= 0.25 and (te.get("start_within_0_4s") or 0) >= 0.8 and R.get("en", {}).get("runs")
say("\nTRANSCRIBE TEST", "PASSED" if ok else "NEEDS REVIEW", "-> tests/out/transcribe_report.json")
