"""M4 B1 offline tests for narration (no voice model, no speech-to-text, no network, no full reel render).
Run from the dev folder with Reel Studio's Python:  ~/.venvs/reelstudio/bin/python tests/test_narration.py [--out <folder>]
A fake voice worker (a 220 Hz tone per sentence) stands in for Indic Parler-TTS, so every code path - cache, speed, pauses, memory
stop, error codes, approval fingerprint, caption timing, disclosure, QA, render gate - is tested in seconds. The real voice model is
tested separately (tools/gate_b1_1_run.sh). "Legacy" tests run the pre-B1 copies (*.preB1) and the new files on the same inputs and
require identical results: projects without narration settings must behave exactly as before.
Every test project lives in a temporary folder; nothing in projects/ or exports/ is touched."""
import os, sys, json, subprocess, tempfile, shutil, hashlib, wave, time, importlib.machinery, importlib.util, argparse
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ENG = os.path.join(ROOT, "engine"); sys.path.insert(0, ENG)
ap = argparse.ArgumentParser(); ap.add_argument("--out"); A = ap.parse_args()
TMP = tempfile.mkdtemp(prefix="rs_b1test_"); PY = sys.executable; RESULTS = []
os.environ["RS_HEAVY_LOCK"] = os.path.join(TMP, "heavy_model.lock")   # the tests never touch the real lock in the dev folder

def check(name, ok, detail=""):
    RESULTS.append(dict(test=name, passed=bool(ok), detail=str(detail)[:400])); print(("PASS " if ok else "FAIL ") + name + (f"  ({str(detail)[:160]})" if detail != "" else ""), flush=True)

def run(script, args, env=None, events=True):
    e = dict(os.environ, **(env or {}));
    if events: e["RS_EVENTS"] = "1"
    else: e.pop("RS_EVENTS", None)
    p = subprocess.run([PY, script if os.path.isabs(script) else os.path.join(ROOT, script)] + list(args), capture_output=True, text=True, env=e, cwd=ROOT, timeout=600)
    evs = []
    for l in p.stdout.splitlines():
        if l.startswith("{"):
            try: evs.append(json.loads(l))
            except ValueError: pass
    return p.returncode, evs, p.stdout, p.stderr

def codes(evs): return [e.get("code") for e in evs if e.get("event") == "error"]
def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
def load(p): return json.load(open(p, encoding="utf-8"))
def save(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def project(name, brand="jagan_for_andhra", platform="instagram", style="documentary", **kw):
    d = os.path.join(TMP, name); os.makedirs(os.path.join(d, "build"), exist_ok=True); os.makedirs(os.path.join(d, "inputs"), exist_ok=True)
    P = dict(brand=brand, platform=platform, style=style, provider=None, brief="b1 test", video=None, title_seconds=2.0,
             hook=dict(line1="పరీక్ష", line2="రెండు", line3="మూడు", tag_top="31 లక్షల", tag_bottom="ఇళ్ల పట్టాలు"), title=["పరీక్ష శీర్షిక", "రెండో లైన్"],
             title_person=None, title_bg=None, face_tracking=False, approved=False, status="test", history=[])
    P.update(kw); save(P, os.path.join(d, "project.json")); return d

def wav_write(p, x, sr=44100):
    with wave.open(p, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
def wav_read(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, w.getframerate()

FAKE = r'''
import sys, os, json, time, argparse, wave
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--config"); ap.add_argument("--jobs"); A = ap.parse_args()
jobs = json.load(open(A.jobs, encoding="utf-8")); mode = os.environ.get("FAKE_TTS", "ok"); cnt = os.environ.get("FAKE_TTS_COUNT")
def say(**k): print(json.dumps(k, ensure_ascii=False), flush=True)
if mode == "missing": say(event="error", code="TTS_MODEL_MISSING", message="fake: model files missing"); sys.exit(3)
if mode == "crash": raise RuntimeError("fake worker crash")
say(event="loaded", load_s=0.01)
hog = []
for k, jb in enumerate(jobs):
    if mode == "oom":
        for _ in range(120): hog.append(np.ones(2_500_000)); time.sleep(0.03)    # grows ~20 MB a step until the watchdog stops it
        say(event="error", code="TTS_FAILED", message="fake: watchdog did not stop me"); sys.exit(3)
    sr = 44100; dur = 0.4 + 0.05 * len(jb["say"]); t = np.arange(int(dur * sr)) / sr
    x = 0.3 * np.sin(2 * np.pi * 220 * t) * np.minimum(1, np.minimum(t, dur - t) * 20)
    x = np.concatenate([np.zeros(int(0.2 * sr)), x, np.zeros(int(0.3 * sr))])
    tmp = jb["out"] + ".part.wav"
    with wave.open(tmp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x * 32767).astype(np.int16).tobytes())
    os.replace(tmp, jb["out"])
    if cnt: open(cnt, "a").write(jb["id"] + "\n")
    say(event="sentence", id=jb["id"], n=k + 1, of=len(jobs), audio_s=round(len(x) / sr, 2), synth_s=0.0)
say(event="result", sentences=len(jobs), peak_rss_bytes=0)
'''
fake = os.path.join(TMP, "fake_tts_worker.py"); open(fake, "w").write(FAKE)
C = load(os.path.join(ENG, "tts.json")); dummy = os.path.join(TMP, "dummy_model.safetensors"); open(dummy, "w").write("x")
def cfg(name, **kw):
    c = dict(C, python=PY, worker=fake, model_check=[dummy]); c.update(kw); p = os.path.join(TMP, f"tts_{name}.json"); save(c, p); return p
CFG = cfg("ok", edge_fade_ms=0); COUNT = os.path.join(TMP, "count.txt")
ENV = dict(RS_TTS_CONFIG=CFG, RS_NO_OLLAMA_UNLOAD="1", FAKE_TTS_COUNT=COUNT)
SCRIPT = ["అక్కచెల్లెమ్మలకు 31 లక్షల ఇళ్ల పట్టాలు.", "సొంతింటి కల నెరవేర్చేలా 17,000 జగనన్న కాలనీలు.", "పేదవాడి ఆరోగ్యానికి 10,000 విలేజ్ క్లినిక్‌లు."]

def approve_script(d, lines=SCRIPT, checked=False):
    f = os.path.join(d, "inputs", "script.txt"); open(f, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    r1 = run("engine/rs.py", ["script", d, f], events=False); r2 = run("engine/rs.py", ["script-approve", d] + (["--checked"] if checked else []), events=False)
    return r1, r2

def oldmod(name):
    p = os.path.join(ENG, name + ".py.preB1"); l = importlib.machinery.SourceFileLoader(name + "_preB1", p)
    s = importlib.util.spec_from_loader(l.name, l); m = importlib.util.module_from_spec(s); l.exec_module(m); return m

# ----------------------------------------------------------------------------------------------------------------- A numbers
import te_numbers as T
cases = {31: "ముప్పై ఒక్క", 17805: "పదిహేడు వేల ఎనిమిది వందల ఐదు", 100000: "ఒక లక్ష", 3100000: "ముప్పై ఒక్క లక్షల", 105: "నూట ఐదు", 250000: "రెండు లక్షల యాభై వేల"}
check("numbers: known spoken forms", all(T.to_words(k) == v for k, v in cases.items()), {k: T.to_words(k) for k in cases})
rng = np.random.default_rng(7); sample = list(range(1, 3001)) + [int(x) for x in rng.integers(1, 10**12, 3000)]
bad = [n for n in sample if not T._reads_back(T.to_words(n), n)]
check("numbers: 6000 numbers read back exactly by the existing reader", not bad, bad[:5])
say, toks, nums = T.spoken(SCRIPT[0])
check("numbers: sentence spoken form", say == "అక్కచెల్లెమ్మలకు ముప్పై ఒక్క లక్షల ఇళ్ల పట్టాలు." and nums[0]["check"] == "ok", say)
check("numbers: decimals and joined endings are marked for review", T.spoken("2.5 లక్షల")[2][0]["check"] == "review" and T.spoken("2024లో")[2][0]["check"] == "review")
O = oldmod("te_numbers"); probe = ["31 లక్షలు", "2.5 లక్షలు", "రెండు లక్షల యాభై వేలు", "లక్ష కోట్లకు", "17,805 కోట్లు", "నాలుగు", "750 కోట్లతో", "ఒక లక్ష"]
same = all(O.value_of(x) == T.value_of(x) and O.all_values(x) == T.all_values(x) for x in probe) and \
       all(O.display(q) == T.display(q) for x in probe for q in T.all_values(x))
check("legacy: existing number reader gives identical results", same)

# ----------------------------------------------------------------------------------------------------------------- B script approval
d = project("script_test"); run("engine/rs.py", ["narration", d, "ai", "--voice", "prakash", "--style", "news"], events=False)
(r1, r2) = approve_script(d)
N = load(os.path.join(d, "build", "narration.json")); P = load(os.path.join(d, "project.json"))
check("script: written text kept exactly", [l["text"] for l in N["lines"]] == SCRIPT)
check("script: approval stores the fingerprint in narration.json and project.json", N["approved"] and P.get("narration_hash") == N["approved_hash"], N["approved_hash"][:12])
d2 = project("script_review"); run("engine/rs.py", ["narration", d2, "ai", "--voice", "lalitha", "--style", "documentary"], events=False)
(r1, r2) = approve_script(d2, ["మొత్తం 2.5 లక్షల మందికి లబ్ధి."])
check("script: a ❓ number is refused without --checked", r2[0] != 0 and "--checked" in (r2[3] + r2[2]), (r2[3] or r2[2])[-120:])
(r1, r2) = approve_script(d2, ["విలువ 3.7 శాతం."], checked=True)
check("script: digits left in the spoken form are refused even with --checked", r2[0] != 0 and "digits" in (r2[3] + r2[2]))
import narration_script as NS
def verify(dd): return NS.verify(dict(load(os.path.join(dd, "project.json")), _dir=dd))
check("script: verify OK after approval", verify(d)[0])
NJ = os.path.join(d, "build", "narration.json"); keep = open(NJ, encoding="utf-8").read()
N2 = load(NJ); N2["lines"][0]["text"] = N2["lines"][0]["text"].replace("31", "32"); save(N2, NJ)
check("script: an edit after approval -> NARRATION_TEXT_CHANGED", verify(d)[1] == "NARRATION_TEXT_CHANGED")
open(NJ, "w", encoding="utf-8").write(keep); check("script: restored text verifies again", verify(d)[0])

# ----------------------------------------------------------------------------------------------------------------- C narrate (fake worker)
rc, ev, out, err = run("engine/narrate.py", [project("not_approved", narration="ai", narrator="prakash", narrator_style="news")], ENV)
check("narrate: refuses an unapproved script (NARRATION_NOT_APPROVED)", rc != 0 and "NARRATION_NOT_APPROVED" in codes(ev), codes(ev))
if os.path.exists(COUNT): os.remove(COUNT)
rc, ev, out, err = run("engine/narrate.py", [d], ENV); TLp = os.path.join(d, "build", "narration_timeline.json")
check("narrate: AI narration made (fake voice)", rc == 0 and os.path.exists(os.path.join(d, "build", "narration.wav")), (codes(ev), err[-200:]))
TL = load(TLp); S = TL["sentences"]; pause = C["styles"]["news"]["pause_s"]
gaps = [round(b["s"] - a["e"], 3) for a, b in zip(S, S[1:])]
check("narrate: pauses between sentences = style pause (news 0.35 s)", all(abs(g - pause) <= 0.001 for g in gaps), gaps)
check("narrate: timeline carries the approval fingerprint and audio checksum", TL["approved_hash"] == N["approved_hash"] and len(TL["audio_sha256"]) == 64)
check("narrate: 3 sentences spoken, 0 from cache", TL["generated"]["spoken"] == 3 and TL["generated"]["cached"] == 0, TL["generated"])
rc, ev, out, err = run("engine/narrate.py", [d], ENV); TL2 = load(TLp)
check("cache: a re-run speaks nothing again", rc == 0 and TL2["generated"]["spoken"] == 0 and TL2["generated"]["cached"] == 3 and len(open(COUNT).read().split()) == 3)
check("cache: re-run audio is identical", TL2["audio_sha256"] == TL["audio_sha256"])
dR = project("restart", narration="ai", narrator="prakash", narrator_style="news"); approve_script(dR)
rc, ev, out, err = run("engine/narrate.py", [dR], dict(ENV, RS_TTS_CONFIG=cfg("restart2", memory=dict(C["memory"], restart_every=2)), FAKE_TTS_COUNT=os.path.join(TMP, "count_r.txt")))
TR_ = load(os.path.join(dR, "build", "narration_timeline.json")) if rc == 0 else {}
check("restart: a fresh voice process every N sentences (N=2, 3 sentences -> 2 loads)", rc == 0 and [b["sentences"] for b in TR_["generated"]["batches"]] == [2, 1], (codes(ev), TR_.get("generated", {}).get("batches")))
check("restart: same audio, text and timing as one long run", rc == 0 and TR_["audio_sha256"] == TL["audio_sha256"] and [(x["s"], x["e"], x["say"]) for x in TR_["sentences"]] == [(x["s"], x["e"], x["say"]) for x in TL["sentences"]])
# ---- B1.2 corrections: restart off by default, exact sample positions, optional edge fade, approved audio preserved
check("settings: 10 ms edge fade is the accepted default (tts.json)", C.get("edge_fade_ms") == 10)
check("restart: off by default (tts.json restart_every = 0)", C["memory"].get("restart_every") == 0 and TL["generated"].get("batches") and len(TL["generated"]["batches"]) == 1)
xw, srw = wav_read(os.path.join(d, "build", "narration.wav")); xi = (xw * 32768).round().astype(int)
gaps0 = [int(np.abs(xi[a["e_sample"]: c["s_sample"]]).max()) for a, c in zip(TL["sentences"], TL["sentences"][1:])]
check("continuity (exact samples): every pause is digital silence", all(g == 0 for g in gaps0) and all(isinstance(x.get("s_sample"), int) for x in TL["sentences"]), gaps0)
if os.path.exists(os.path.join(ENG, "narrate.py.preB12")):
    dO = project("old_narrate", narration="ai", narrator="prakash", narrator_style="news"); approve_script(dO)
    shutil.copytree(os.path.join(d, "build", "narration_cache"), os.path.join(dO, "build", "narration_cache"))
    rco, evo, _, erro = run("engine/narrate.py.preB12", [dO], ENV); TO = load(os.path.join(dO, "build", "narration_timeline.json")) if rco == 0 else {}
    check("approved audio preserved: with the fade off, the corrected code makes the same audio as before the corrections", rco == 0 and TO["audio_sha256"] == TL["audio_sha256"], (codes(evo), erro[-120:]))
dF = project("fade", narration="ai", narrator="prakash", narrator_style="news"); approve_script(dF)
shutil.copytree(os.path.join(d, "build", "narration_cache"), os.path.join(dF, "build", "narration_cache"))
rcf, evf, _, _ = run("engine/narrate.py", [dF], dict(ENV, RS_TTS_CONFIG=cfg("fade10", edge_fade_ms=10)))
TF = load(os.path.join(dF, "build", "narration_timeline.json")) if rcf == 0 else {}
if rcf == 0:
    xf, _ = wav_read(os.path.join(dF, "build", "narration.wav")); xf = (xf * 32768).round().astype(int); n10 = int(0.010 * srw)
    same_pos = [(a["s_sample"], a["e_sample"]) for a in TF["sentences"]] == [(a["s_sample"], a["e_sample"]) for a in TL["sentences"]]
    inner_same = all(np.array_equal(xf[a["s_sample"] + n10: a["e_sample"] - n10], xi[a["s_sample"] + n10: a["e_sample"] - n10]) for a in TF["sentences"])
    edge_quiet = max(int(np.abs(xi[a["s_sample"]: a["s_sample"] + n10]).max()) for a in TF["sentences"]) / 32768 <= 10 ** (C["trim_db"] / 20) + 1e-4
    check("fade 10 ms: sentence and pause positions unchanged (alignment and pauses identical)", same_pos and TF["samples"] == TL["samples"])
    check("fade 10 ms: every sample outside the 10 ms edges is identical (no speech cut, nothing else changed)", inner_same)
    check("fade 10 ms: the faded edges lie in the quiet trim margin (below the speech threshold)", edge_quiet)
    check("fade 10 ms: edges now start and end at silence", all(abs(xf[a["s_sample"]]) <= 1 and abs(xf[a["e_sample"] - 1]) <= 1 for a in TF["sentences"]))
else: check("fade 10 ms: narration made", False, codes(evf))
dL = project("long", narration="ai", narrator="lalitha", narrator_style="documentary")
longline = "పేదవాడికి కార్పొరేట్ వైద్యం 25 లక్షల వరకు ఆరోగ్యశ్రీ పరిమితి పెంచి రాష్ట్రంలో ప్రతి కుటుంబానికి భరోసా ఇచ్చిన పథకం ఇది."
(r1, r2) = approve_script(dL, [SCRIPT[0], longline]); NL = load(os.path.join(dL, "build", "narration.json"))
check("length: a long sentence is marked ❓ and refused without --checked", r2[0] != 0 and "long sentence" in (r2[3] + r2[2]) and NL["lines"][1]["length"]["too_long"]
      and not NL["lines"][0]["length"]["too_long"], NL["lines"][1]["length"])
(r1, r2) = approve_script(dL, [SCRIPT[0], longline], checked=True); NL = load(os.path.join(dL, "build", "narration.json"))
check("length: after review (--checked) it is approved exactly as written - never split or rewritten", r2[0] == 0 and [l["text"] for l in NL["lines"]] == [SCRIPT[0], longline])
check("length: 70-character rule", NS.length_check(dict(narrator="prakash", narrator_style="news"), "అ" * 71)[2] and not NS.length_check(dict(narrator="prakash", narrator_style="news"), "అ" * 40)[2])
check("memory label: a cached run says 'model not loaded' (no fake measurement)", TL2["memory"]["model_loaded"] is False and TL2["memory"]["peak_rss_gb"] is None
      and TL["memory"]["model_loaded"] is True, TL2["memory"].get("note"))

def pitch(x, sr):
    f = np.abs(np.fft.rfft(x * np.hanning(len(x)))); return np.argmax(f) * sr / len(x)
x0, sr = wav_read(os.path.join(d, "build", "narration.wav")); seg0 = x0[int(S[0]["s"] * sr) + 2000: int(S[0]["e"] * sr) - 2000]
speed_res = {}
import narrate as NR
for method in ("rubberband", "atempo"):
    have = NR.filter_available(method); speed_res[f"{method}_available"] = have
    for sp in (1.15, 1.2):
        run("engine/rs.py", ["narration", d, "ai", "--voice", "prakash", "--style", "news", "--speed", str(sp), "--method", method], events=False)
        before = open(TLp, "rb").read(); rc, ev, out, err = run("engine/narrate.py", [d], ENV)
        if not have:
            check(f"speed {sp}x {method}: not in this FFmpeg -> clear SPEED_METHOD_UNAVAILABLE, nothing changed",
                  rc != 0 and codes(ev) == ["SPEED_METHOD_UNAVAILABLE"] and open(TLp, "rb").read() == before, codes(ev)); continue
        T3 = load(TLp); S3 = T3["sentences"]
        x, _ = wav_read(os.path.join(d, "build", "narration.wav")); seg = x[int(S3[0]["s"] * sr) + 2000: int(S3[0]["e"] * sr) - 2000]
        ratio = [round(a["speech_s"] / b["speech_s"], 3) for a, b in zip(S, S3)]; g3 = [round(b["s"] - a["e"], 3) for a, b in zip(S3, S3[1:])]
        p0, p1 = pitch(seg0, sr), pitch(seg, sr); speed_res[f"{method}_{sp}"] = dict(ratio=ratio, gaps=g3, pitch=(round(p0, 1), round(p1, 1)), spoken=T3["generated"]["spoken"])
        check(f"speed {sp}x {method}: speech {sp}x shorter (±3%)", rc == 0 and all(abs(r - sp) / sp <= 0.03 for r in ratio), (ratio, codes(ev)))
        check(f"speed {sp}x {method}: pauses unchanged", all(abs(g - pause) <= 0.001 for g in g3), g3)
        check(f"speed {sp}x {method}: pitch kept (±3%)", abs(p1 - p0) / p0 <= 0.03, (round(p0, 1), round(p1, 1)))
        check(f"speed {sp}x {method}: uses the cache (no new speaking)", T3["generated"]["spoken"] == 0)
check("speed: FFmpeg filter check recognises a filter that does not exist", not NR.filter_available("no_such_filter_b1"))
P = load(os.path.join(d, "project.json")); P["narration_speed"] = 1.3; save(P, os.path.join(d, "project.json"))
rc, ev, out, err = run("engine/narrate.py", [d], ENV); check("speed: 1.3x refused (NARRATION_SPEED_INVALID)", "NARRATION_SPEED_INVALID" in codes(ev), codes(ev))
rc, ev, out, err = run("engine/rs.py", ["narration", d, "ai", "--voice", "prakash", "--style", "news", "--speed", "1.3"])
check("speed: rs.py refuses 1.3x too", rc != 0 and "NARRATION_SPEED_INVALID" in codes(ev))
run("engine/rs.py", ["narration", d, "ai", "--voice", "prakash", "--style", "news", "--speed", "1.0"], events=False); run("engine/narrate.py", [d], ENV)

def errcase(name, env_extra, want, mutate=None, lines=None):
    dd = project("err_" + name, narration="ai", narrator="lalitha", narrator_style="documentary"); approve_script(dd, lines or [SCRIPT[0] + " " + name])
    if mutate: mutate(dd)
    rc, ev, out, err = run("engine/narrate.py", [dd], dict(ENV, **env_extra)); cs = codes(ev)
    check(f"error: {want} ({name})", rc != 0 and want in cs and "UNEXPECTED" not in cs and "Traceback" not in err, (cs, err[-160:])); return dd, ev
dd, ev = errcase("memory", dict(RS_TTS_CONFIG=cfg("oom", memory=dict(warn_gb=0.15, limit_gb=0.3, poll_s=0.1)), FAKE_TTS="oom"), "TTS_MEMORY_LIMIT")
check("memory: warning sent before the stop", any(e.get("code") == "TTS_MEMORY_HIGH" for e in ev))
errcase("env", dict(RS_TTS_CONFIG=cfg("noenv", python="/nonexistent/rs_tts/bin/python")), "TTS_ENV_MISSING")
errcase("model", dict(RS_TTS_CONFIG=cfg("nomodel", model_check=["/nonexistent/model.safetensors"])), "TTS_MODEL_MISSING")
errcase("worker_missing", dict(FAKE_TTS="missing"), "TTS_MODEL_MISSING")
errcase("crash", dict(FAKE_TTS="crash"), "TTS_FAILED")
import common
def hold(dd): open(common.HEAVY_LOCK, "w").write(f"{os.getpid()} test-holder")
try: errcase("busy", {}, "BUSY_HEAVY_MODEL", mutate=hold)
finally:
    if os.path.exists(common.HEAVY_LOCK) and open(common.HEAVY_LOCK).read().split()[0] == str(os.getpid()): os.remove(common.HEAVY_LOCK)
def badvoice(dd): P = load(os.path.join(dd, "project.json")); P["narrator"] = "someone"; save(P, os.path.join(dd, "project.json"))
errcase("voice", {}, "NARRATION_VOICE_INVALID", mutate=badvoice)
check("lock: released after every run", not os.path.exists(common.HEAVY_LOCK))

# recorded
dr = project("recorded"); rec = os.path.join(dr, "inputs", "my_voice.wav")
rc, ev, out, err = run("engine/rs.py", ["narration", dr, "recorded", "--style", "news", "--file", "inputs/missing.wav"])
check("recorded: missing recording refused (NARRATION_FILE_MISSING)", rc != 0 and "NARRATION_FILE_MISSING" in codes(ev))
shutil.copy(os.path.join(d, "build", "narration.wav"), rec)   # stand-in recording (the fake voice), for the pipeline only
run("engine/rs.py", ["narration", dr, "recorded", "--style", "news", "--file", "inputs/my_voice.wav"], events=False); approve_script(dr)
rc, ev, out, err = run("engine/narrate.py", [dr], ENV); TR = load(os.path.join(dr, "build", "narration_timeline.json"))
check("recorded: recording read, sentence times left for alignment", rc == 0 and TR["mode"] == "recorded" and not TR["aligned"], codes(ev))

# ----------------------------------------------------------------------------------------------------------------- D alignment
def fake_asr(tl, path, drop=None, wrong=None, shift=0.0, join=None):
    words = []
    for s in tl["sentences"]:
        ws = s["say"].split(); step = (s["e"] - s["s"]) / len(ws)
        for k, w in enumerate(ws):
            if drop and (s["i"], k) == drop: continue
            if wrong and (s["i"], k) == wrong[0]: w = wrong[1]
            words.append(dict(w=w, s=round(s["s"] + k * step + shift, 3), e=round(s["s"] + (k + 1) * step + shift, 3)))
    if join:   # speech-to-text writes two words as one ('పది వేల' -> 'పదివేల')
        for i in range(len(words) - 1):
            if words[i]["w"] == join[0] and words[i + 1]["w"] == join[1]: words[i:i + 2] = [dict(w=join[0] + join[1], s=words[i]["s"], e=words[i + 1]["e"])]; break
    save(dict(words=words, model="fake-asr"), path); return path
TLd = load(TLp); asrj = fake_asr(TLd, os.path.join(TMP, "asr1.json"), drop=(1, 2))
rc, ev, out, err = run("engine/narration_align.py", [d], dict(ENV, RS_ALIGN_ASR_JSON=asrj)); CK = load(os.path.join(d, "build", "narration_check.json"))
W = load(os.path.join(d, "build", "narration_words.json"))
check("align: captions are the approved written words, in order", rc == 0 and [w["w"] for w in W] == " ".join(SCRIPT).split(), (len(W), codes(ev)))
check("align: numbers highlighted", [w["w"] for w in W if w["hl"]] == ["31", "17,000", "10,000"])
check("align: every sentence's first caption within 0.1 s of its speech", CK["max_sync_offset_s"] <= 0.1, CK["first_caption_vs_sentence_start_s"])
check("align: captions inside their sentence and never overlapping", all(a["e"] <= b["s"] + 1e-6 for a, b in zip(W, W[1:])) and all(w["e"] > w["s"] for w in W))
check("align: a missing word is listed for its own sentence only", CK["cer_total"] < 0.2 and [x["line"] for x in CK["to_check"]] == [2], (CK["cer_total"], [x["line"] for x in CK["to_check"]]))
asrj2 = fake_asr(TLd, os.path.join(TMP, "asr2.json"), wrong=((0, 1), "ముప్పై రెండు"))
rc, ev, out, err = run("engine/narration_align.py", [d], dict(ENV, RS_ALIGN_ASR_JSON=asrj2)); CK2 = load(os.path.join(d, "build", "narration_check.json"))
check("align: a number heard differently is listed for the user", any(not x["numbers_ok"] for x in CK2["to_check"]), [x["issues"] for x in CK2["to_check"]])
asrj3 = fake_asr(TLd, os.path.join(TMP, "asr_shift.json"), shift=0.6, join=("పది", "వేల"))
rc, ev, out, err = run("engine/narration_align.py", [d], dict(ENV, RS_ALIGN_ASR_JSON=asrj3)); CK3 = load(os.path.join(d, "build", "narration_check.json"))
check("align: speech-to-text times 0.6 s late do not move words to the wrong sentence", rc == 0 and not CK3["to_check"] and all(x["cer"] == 0 for x in CK3["sentences"]), [(x["line"], x["cer"], x["heard"][:30]) for x in CK3["sentences"]])
import narration_align as NA
check("align: joined number words read correctly ('పదివేల' = 10,000)", NA.numbers("పదివేల విలేజ్") == [10000.0] and NA.numbers("పది వేల") == [10000.0])
shutil.copy(asrj, os.path.join(d, "build", "narration_asr.json")); A0 = load(os.path.join(d, "build", "narration_asr.json")); A0["audio_sha256"] = load(TLp)["audio_sha256"]
save(A0, os.path.join(d, "build", "narration_asr.json")); e2 = {k: v for k, v in ENV.items()}
rc, ev, out, err = run("engine/narration_align.py", [d], e2); CK4 = load(os.path.join(d, "build", "narration_check.json"))
check("align: unchanged audio re-uses the earlier speech-to-text (no model loaded)", rc == 0 and CK4.get("asr_reused") is True, codes(ev))
check("align: approved script untouched after the check", verify(d)[0] and load(NJ)["lines"][0]["text"] == SCRIPT[0])
run("engine/narration_align.py", [d], dict(ENV, RS_ALIGN_ASR_JSON=asrj))
TRd = load(os.path.join(dr, "build", "narration_timeline.json"))
rc, ev, out, err = run("engine/narration_align.py", [dr], dict(ENV, RS_ALIGN_ASR_JSON=fake_asr(dict(TRd, sentences=TLd["sentences"]), os.path.join(TMP, "asr3.json"))))
TR2 = load(os.path.join(dr, "build", "narration_timeline.json"))
check("recorded: sentence times from speech-to-text", rc == 0 and TR2["aligned"] and all(abs(a["s"] - b["s"]) < 0.05 for a, b in zip(TR2["sentences"], TLd["sentences"])), codes(ev))

# ----------------------------------------------------------------------------------------------------------------- E slides
beats = [dict(img=None, text=f"స్లయిడ్ {i + 1}", dur=3.0) for i in range(3)]
save(beats, os.path.join(d, "build", "beats.json"))
rc, ev, out, err = run("engine/slides.py", [d], ENV)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(d, "build", "edit.mp4")], capture_output=True, text=True).stdout or 0)
check("slides: edit length follows the narration (±1 frame)", rc == 0 and abs(dur - TLd["duration"]) <= 1 / 30 + 0.01, (round(dur, 3), TLd["duration"], codes(ev)))
save(beats[:2], os.path.join(d, "build", "beats.json")); rc, ev, out, err = run("engine/slides.py", [d], ENV)
check("slides: slide/sentence count mismatch refused", "NARRATION_BEATS_MISMATCH" in codes(ev))
from PIL import Image as _I
orange = os.path.join(d, "inputs", "photo.png"); _I.new("RGB", (900, 1200), (255, 120, 0)).save(orange)
save([dict(img="inputs/photo.png", text=f"స్లయిడ్ {i + 1}", dur=3.0) for i in range(3)], os.path.join(d, "build", "beats.json"))
rc, ev, out, err = run("engine/slides.py", [d], ENV)
import frame as FRM; cJ = load(os.path.join(ROOT, "brands", "jagan_for_andhra", "brand.json")); cJ["_dir"] = os.path.join(ROOT, "brands", "jagan_for_andhra")
res_top = FRM.disclosure_reserve(cJ); worst = 0
for tt in (0.05, 1.0, round(S[1]["s"] - 0.05, 2)):
    fp = os.path.join(TMP, f"photo_{tt}.png"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(tt), "-i", os.path.join(d, "build", "edit.mp4"), "-frames:v", "1", fp])
    a = np.array(_I.open(fp).convert("RGB")).astype(int); band = a[: int(res_top * a.shape[0])]
    worst = max(worst, int(((band[..., 0] > 200) & (band[..., 1] > 80) & (band[..., 1] < 170) & (band[..., 2] < 60)).sum()))
check("slides (AI narration): photos stay below the disclosure band, also at full push-in", rc == 0 and worst == 0, dict(reserve=res_top, orange_pixels_in_band=worst, errors=codes(ev)))
def framemd5(p): return subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "framemd5", "-"], capture_output=True, text=True).stdout.splitlines()[-5:]
L1 = project("legacy_slides"); L2 = project("legacy_slides_new")
for x in (L1, L2): save([dict(img=None, text="ఒకటి", sub="పరీక్ష", dur=1.0), dict(img=None, text="రెండు", dur=1.0)], os.path.join(x, "build", "beats.json"))
ra = run("engine/slides.py.preB1", [L1], events=False); rb = run("engine/slides.py", [L2], events=False)
same = ra[0] == rb[0] == 0 and framemd5(os.path.join(L1, "build", "edit.mp4")) == framemd5(os.path.join(L2, "build", "edit.mp4")) and \
       load(os.path.join(L1, "build", "cues.json")) == load(os.path.join(L2, "build", "cues.json"))
check("legacy: slides without narration identical to pre-B1 (frames + cues)", same, (ra[3][-120:], rb[3][-120:]))

# ----------------------------------------------------------------------------------------------------------------- F frame + disclosure
FR = {}
for brand in ("jagan_for_andhra", "tech_ai_tools", "editing_freelance"):
    style = load(os.path.join(ROOT, "brands", brand, "brand.json"))["default_style"]
    for pf in ("instagram", "youtube", "facebook"):
        a, b = project(f"lf_{brand}_{pf}_old", brand, pf, style), project(f"lf_{brand}_{pf}_new", brand, pf, style)
        ra, rb = run("engine/frame.py.preB1", [a], events=False), run("engine/frame.py", [b], events=False)
        la_, lb_ = (load(os.path.join(x, "build", "layout.json")) if os.path.exists(os.path.join(x, "build", "layout.json")) else {} for x in (a, b)); lb_.pop("elements", None)   # B2 adds "elements"
        ok = ra[0] == rb[0] == 0 and md5(os.path.join(a, "build", "frame.png")) == md5(os.path.join(b, "build", "frame.png")) and la_ == lb_ and \
             (not os.path.exists(os.path.join(a, "build", "window_mask.png")) or md5(os.path.join(a, "build", "window_mask.png")) == md5(os.path.join(b, "build", "window_mask.png")))
        FR[(brand, pf)] = ok
check("legacy: frame.png and window_mask.png byte-identical to pre-B1, layout.json identical apart from the B2 'elements' list (3 brands x 3 platforms)", all(FR.values()), [k for k, v in FR.items() if not v])
DISC = {}
from PIL import Image
for brand, positions in (("jagan_for_andhra", ("window_top", "window_bottom")), ("tech_ai_tools", ("top", "bottom")), ("editing_freelance", ("top", "bottom"))):
    style = load(os.path.join(ROOT, "brands", brand, "brand.json"))["default_style"]
    for pf in ("instagram", "youtube", "facebook"):
        for pos in positions:
            x = project(f"disc_{brand}_{pf}_{pos}", brand, pf, style, narration="ai", narrator="prakash", narrator_style="news")
            r = run("engine/frame.py", [x], dict(RS_DISCLOSURE_POSITION=pos), events=False); LY = load(os.path.join(x, "build", "layout.json"))
            dz = LY.get("ai_disclosure"); iss = [i for i in LY["safe_area"]["issues"] if i["element"] == "ai_disclosure"]
            hole = True
            if dz and LY["type"] == "framed":
                mk = Image.open(os.path.join(x, "build", "window_mask.png")); w = LY["window"]; l, t, rr, bb = dz["box"]
                hole = mk.getpixel(((l + rr) // 2 - w["x"], (t + bb) // 2 - w["y"])) == 0 and mk.getpixel((w["size"] // 2, w["size"] // 2)) == 255
            two = bool(dz) and len(dz["lines"]) == 2 and dz["font_px"] >= 30 and " ".join(dz["lines"]) == dz["text"] == C["disclosure"]["te"]
            DISC[(brand, pf, pos)] = dict(ok=r[0] == 0 and bool(dz) and not iss and hole and two, box=dz and dz["box"], px=dz and dz["font_px"], lines=dz and dz["lines"], issues=iss,
                                          error=r[3][-160:] if r[0] else None)
check("disclosure: complete approved line on 2 lines at >= 30 px, inside the safe area, covering no logo/headline/social row, window hole correct (3 brands x 3 platforms x 2 positions)", all(v["ok"] for v in DISC.values()),
      [(k, v) for k, v in DISC.items() if not v["ok"]][:3])
for mode in ("recorded", "none"):
    x = project(f"nodisc_{mode}", narration=mode, narrator_style="news"); r = run("engine/frame.py", [x], events=False); LY = load(os.path.join(x, "build", "layout.json"))
    check(f"disclosure: absent for narration '{mode}'", r[0] == 0 and "ai_disclosure" not in LY and LY.get("narration") == mode)

# ----------------------------------------------------------------------------------------------------------------- G qa
def clip_from(proj, out, with_frame=True, loud=0.05):
    """A 4 s test clip (NOT a reel): 2 s title colour + 2 s of the frame composited like assemble.py does, quiet 220 Hz tone."""
    b = os.path.join(proj, "build"); LY = load(os.path.join(b, "layout.json")); W_, H_ = 1080, 1920
    vid = Image.new("RGB", (1080, 1080) if LY["type"] == "framed" else (W_, H_), (90, 110, 130))
    fr = Image.open(os.path.join(b, "frame.png")).convert("RGBA")
    if LY["type"] == "framed":
        w = LY["window"]; base = fr.copy() if with_frame else Image.new("RGBA", (W_, H_), (40, 40, 40, 255))
        v = vid.resize((w["size"], w["size"])).convert("RGBA"); m = Image.open(os.path.join(b, "window_mask.png")).convert("L") if with_frame else Image.new("L", (w["size"], w["size"]), 255)
        base.paste(v, (w["x"], w["y"]), m); comp = base
    else:
        comp = vid.convert("RGBA");
        if with_frame: comp.alpha_composite(fr)
    still = os.path.join(TMP, os.path.basename(out) + ".png"); comp.convert("RGB").save(still)
    a = os.path.join(TMP, os.path.basename(out) + ".wav"); sr = 48000; t = np.arange(4 * sr) / sr
    tone = np.sign(np.sin(2 * np.pi * 220 * t)) if loud >= 1 else loud * np.sin(2 * np.pi * 220 * t); wav_write(a, tone, sr)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-t", "2", "-i", "color=c=0x0459A8:s=1080x1920:r=30", "-loop", "1", "-t", "2", "-i", still, "-i", a,
                    "-filter_complex", "[1:v]fps=30,format=yuv420p[s];[0:v]format=yuv420p[t];[t][s]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-map", "2:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    return out, os.path.join(b, "layout.json")
def qa_checks(clip, layout, script="engine/qa.py"):
    j = os.path.join(TMP, os.path.basename(clip) + f"_{os.path.basename(script)}.json")
    run(script, [clip, "--platform", "instagram", "--layout", layout, "--json", j], events=False); return {c["name"]: c for c in load(j)["checks"]}
xa = project("qa_ai", narration="ai", narrator="prakash", narrator_style="news"); run("engine/frame.py", [xa], events=False)
c1 = qa_checks(*clip_from(xa, os.path.join(TMP, "qa_ai.mp4")))
check("qa: AI disclosure found readable on sampled frames (framed brand)", c1.get("ai_disclosure", {}).get("passed"), c1.get("ai_disclosure"))
check("qa: clipping check passes on clean audio", c1.get("clipping", {}).get("passed"), c1.get("clipping"))
c2 = qa_checks(*clip_from(xa, os.path.join(TMP, "qa_ai_nodisc.mp4"), with_frame=False))
check("qa: AI narration WITHOUT a visible disclosure fails", c2.get("ai_disclosure", {}).get("passed") is False, c2.get("ai_disclosure", {}).get("value"))
xf = project("qa_ai_full", "tech_ai_tools", "youtube", load(os.path.join(ROOT, "brands", "tech_ai_tools", "brand.json"))["default_style"], narration="ai", narrator="lalitha", narrator_style="documentary")
run("engine/frame.py", [xf], events=False); c3 = qa_checks(*clip_from(xf, os.path.join(TMP, "qa_ai_full.mp4")))
check("qa: AI disclosure found readable (fullscreen brand)", c3.get("ai_disclosure", {}).get("passed"), c3.get("ai_disclosure"))
xn = project("qa_none", narration="none"); run("engine/frame.py", [xn], events=False); c4 = qa_checks(*clip_from(xn, os.path.join(TMP, "qa_none.mp4"), loud=1.0))
check("qa: no disclosure for narration none passes", c4.get("ai_disclosure", {}).get("passed"), c4.get("ai_disclosure"))
check("qa: clipped audio is caught", c4.get("clipping", {}).get("passed") is False and c4["clipping"]["value"] > 0, c4.get("clipping", {}).get("value"))
xl = project("qa_legacy"); run("engine/frame.py", [xl], events=False); clipL, layL = clip_from(xl, os.path.join(TMP, "qa_legacy.mp4"))
o, n = qa_checks(clipL, layL, "engine/qa.py.preB1"), qa_checks(clipL, layL)
check("legacy: QA on a project without narration gives exactly the same checks as pre-B1", o == n and "ai_disclosure" not in n and "clipping" not in n, (list(o), list(n)))

# ----------------------------------------------------------------------------------------------------------------- H voice.py
xv = project("voice_legacy"); env0 = {k: "" for k in ()}
ea = dict(os.environ); ea.pop("ELEVENLABS_API_KEY", None)
pa = subprocess.run([PY, os.path.join(ENG, "voice.py.preB1"), xv, os.path.join(TMP, "s.txt")], capture_output=True, text=True, env=ea, cwd=ROOT)
pb = subprocess.run([PY, os.path.join(ENG, "voice.py"), xv, os.path.join(TMP, "s.txt")], capture_output=True, text=True, env=ea, cwd=ROOT)
check("legacy: voice.py without a narration setting behaves as before (no key -> NO_VOICE)", pa.returncode == pb.returncode != 0 and pa.stderr == pb.stderr and "NO_VOICE" in pb.stderr, pb.stderr[-120:])
rc, ev, out, err = run("engine/voice.py", [project("voice_none", narration="none")], ENV)
check("voice.py: narration none -> text + music, no error", rc == 0 and not codes(ev))
rc, ev, out, err = run("engine/voice.py", [d], ENV)
check("voice.py: narration ai -> local narration (not ElevenLabs)", rc == 0 and any(e.get("event") == "output" and e.get("path", "").endswith("narration.wav") for e in ev), codes(ev))
bad_script = os.path.join(TMP, "other.txt"); open(bad_script, "w", encoding="utf-8").write("వేరే వాక్యం.\n")
rc, ev, out, err = run("engine/voice.py", [d, bad_script], ENV)
check("voice.py: a script file that differs from the approved one is refused", rc != 0 and "NARRATION_TEXT_CHANGED" in codes(ev))

# ----------------------------------------------------------------------------------------------------------------- I adapter + rs + mix
import adapter
def gate(dd): return [e for e in adapter.render_reel(dd) if e.get("event") == "error"]
check("adapter: narrated project renders only when ready (fake narration ready -> next gate is the missing edit)",
      [e["code"] for e in gate(d)] == ["EDIT_MISSING"], [e["code"] for e in gate(d)])
check("adapter: unapproved narration blocks rendering", [e["code"] for e in gate(project("gate_na", narration="ai", narrator="prakash", narrator_style="news"))] == ["NARRATION_NOT_APPROVED"])
wv = os.path.join(d, "build", "narration.wav"); keepw = open(wv, "rb").read(); open(wv, "ab").write(b"\0\0")
check("adapter: narration audio changed after it was made -> blocked", [e["code"] for e in gate(d)] == ["NARRATION_AUDIO_CHANGED"]); open(wv, "wb").write(keepw)
P = load(os.path.join(d, "project.json")); P["narrator"] = "lalitha"; save(P, os.path.join(d, "project.json"))
check("adapter: voice changed since the audio was made -> blocked", [e["code"] for e in gate(d)] == ["NARRATION_AUDIO_STALE"]); P["narrator"] = "prakash"; save(P, os.path.join(d, "project.json"))
os.environ.update(ENV, RS_ALIGN_ASR_JSON=asrj); evs = list(adapter.narrate(d)); [os.environ.pop(k, None) for k in list(ENV) + ["RS_ALIGN_ASR_JSON"]]
dn = evs[-1]; check("adapter: narrate action -> events + done ok with memory, error rate and items to check", dn.get("ok") and "cer_total" in dn and "memory" in dn, {k: dn.get(k) for k in ("ok", "cer_total", "duration")})
lg = project("gate_legacy"); oA = oldmod("adapter")
ev_old = [{k: v for k, v in e.items() if k != "job_id"} for e in oA.render_reel(lg)]; ev_new = [{k: v for k, v in e.items() if k != "job_id"} for e in adapter.render_reel(lg)]
check("legacy: adapter render events for a project without narration identical to pre-B1", ev_old == ev_new, ev_new)
ca = run("engine/adapter.py.preB1", ["check"], events=False); cb = run("engine/adapter.py", ["check"], events=False)
check("legacy: adapter check output identical to pre-B1", ca[2] == cb[2] and ca[0] == cb[0])
import rs; oR = oldmod("rs")
check("legacy: rs.py settings validation identical", oR.validate() == rs.validate())
import inspect
check("legacy: rs.py 'new project' code identical (no narration fields added to new projects)", inspect.getsource(oR.new) == inspect.getsource(rs.new))
def mixcase(proj, voice, script):
    b = os.path.join(proj, "build"); sr = 48000; t = np.arange(6 * sr) / sr
    wav_write(os.path.join(b, "music.wav"), 0.1 * np.sin(2 * np.pi * 110 * t), sr); wav_write(os.path.join(b, "sfx.wav"), np.zeros(6 * sr), sr)
    r = run(script, [proj, voice, "5.0", os.path.join(b, f"out_{os.path.basename(script)}.wav")], events=False); return r, os.path.join(b, f"out_{os.path.basename(script)}.wav")
mx = project("mix_legacy", voice_clean="basic"); vf = os.path.join(TMP, "voice.wav"); wav_write(vf, 0.2 * np.sin(2 * np.pi * 300 * np.arange(5 * 44100) / 44100))
(ra, fa), (rb, fb) = mixcase(mx, vf, "engine/mix.py.preB1"), mixcase(mx, vf, "engine/mix.py")
(ra2, fa2), (rb2, fb2) = mixcase(mx, "none", "engine/mix.py.preB1"), mixcase(mx, "none", "engine/mix.py")
check("legacy: mix.py output identical to pre-B1 (voice + none)", ra[0] == rb[0] == 0 and md5(fa) == md5(fb) and md5(fa2) == md5(fb2), (ra[3][-120:], rb[3][-120:]))
ma = project("mix_ai", narration="ai"); (r_, f_) = mixcase(ma, vf, "engine/mix.py")
check("mix: AI narration is not cleaned again", r_[0] == 0 and "voice cleaning: none" in r_[2], r_[2][-80:])

# ----------------------------------------------------------------------------------------------------------------- summary
n_ok = sum(r["passed"] for r in RESULTS)
print(f"\n{n_ok}/{len(RESULTS)} passed" + ("  ALL PASSED" if n_ok == len(RESULTS) else "  SOME TESTS FAILED"))
if A.out:
    os.makedirs(A.out, exist_ok=True)
    save(dict(passed=n_ok, total=len(RESULTS), results=RESULTS, speed=speed_res, disclosure={"|".join(k): v for k, v in DISC.items()}), os.path.join(A.out, "test_narration.json"))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if n_ok == len(RESULTS) else 1)
