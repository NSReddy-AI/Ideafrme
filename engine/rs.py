"""Reel Studio command line (the app screens will call the same functions).
  python3 engine/rs.py brands | platforms | styles | providers
  python3 engine/rs.py new <brand> <platform> <style> <slug>   create projects/<date>_<slug>/
  python3 engine/rs.py ingest <project>                       list inputs -> build/inputs.json
  python3 engine/rs.py render <project>                       title page + frame + final reel (needs build/edit.mp4 + build/edit_audio.wav)
  python3 engine/rs.py reexport <project> <platform>          same reel for another platform (no re-edit, project.json unchanged)
  python3 engine/rs.py check                                  verify tools and settings
M4 B1 narration (optional; a project without these settings works exactly as before):
  python3 engine/rs.py narration <project> ai --voice prakash|lalitha --style news|documentary [--speed 1.0] [--method rubberband|atempo]
  python3 engine/rs.py narration <project> recorded --style news|documentary --file inputs/my_voice.wav
  python3 engine/rs.py narration <project> none
  python3 engine/rs.py script <project> <script.txt>          one sentence per line -> build/narration.json, shown for approval
  python3 engine/rs.py script-approve <project> [--checked]   approve exactly that text (fingerprint into project.json)
M4 B3 - the whole flow (each step logged in project.json history; nothing is published):
  python3 engine/rs.py plan <project>                         speaker video: transcribe if needed, then the planner -> build/plan.md
  python3 engine/rs.py hook <project> "l1 / l2 / l3 / h1 / h2"    add your own hook as option D (checked like the others)
  python3 engine/rs.py approve <project> A|B|C|D [--checked]  approve the plan (fingerprint)
  python3 engine/rs.py build <project>                        build/edit.mp4 + edit_audio.wav from approved material only
  then: python3 engine/adapter.py render <project> --all-platforms
  python3 engine/rs.py next <project>                         what is done, and the next command to run"""
import sys, os, glob, datetime, shutil, subprocess, json
from common import *
def names(kind): return sorted(os.path.basename(p).replace(".json", "") for p in glob.glob(os.path.join(ROOT, kind, "*.json")))
def brands(): return sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "brands", "*", "brand.json")))
def validate():
    """Check every brand/platform/style file; return list of problems."""
    errs = []
    for b in brands():
        c = load(os.path.join(ROOT, "brands", b, "brand.json"))
        for k in ("name", "handle", "language", "assets", "title", "frame", "captions", "default_style"):
            if k not in c: errs.append(f"brand {b}: missing '{k}'")
        for k, v in c.get("assets", {}).items():
            if v and not os.path.exists(os.path.join(ROOT, "brands", b, v)): errs.append(f"brand {b}: asset {k} file not found ({v})")
        if c.get("default_style") not in names("styles"): errs.append(f"brand {b}: default_style '{c.get('default_style')}' not in styles/")
        if "YOUR_" in c.get("handle", ""): errs.append(f"brand {b}: handle not set yet ({c['handle']})")
    for p in names("platforms"):
        d = load(os.path.join(ROOT, "platforms", p+".json"))
        for k in ("name", "width", "height", "fps", "safe_area", "post"):
            if k not in d: errs.append(f"platform {p}: missing '{k}'")
    for s in names("styles"):
        d = load(os.path.join(ROOT, "styles", s+".json"))
        for k in ("name", "pacing", "structure", "captions"):
            if k not in d: errs.append(f"style {s}: missing '{k}'")
    return errs
def new(brand, platform, style, slug):
    if brand not in brands(): sys.exit(f"unknown brand '{brand}'. Brands: {brands()}")
    if platform not in names("platforms"): sys.exit(f"unknown platform '{platform}'. Platforms: {names('platforms')}")
    if style not in names("styles"): sys.exit(f"unknown style '{style}'. Styles: {names('styles')}")
    d = os.path.join(ROOT, "projects", f"{datetime.date.today()}_{slug}")
    for sub in ("inputs", "build"): os.makedirs(os.path.join(d, sub), exist_ok=True)
    save(dict(brand=brand, platform=platform, style=style, provider=None, brief="", video=None, title_seconds=2.0,
              hook=dict(line1="", line2="", line3="", tag_top="", tag_bottom=""), title=["", ""],
              title_person=None, title_bg=None, face_tracking=False, approved=False, status="new", history=[f"{datetime.datetime.now():%Y-%m-%d %H:%M} created"]),
         os.path.join(d, "project.json"))
    for f in ("notes.txt", "urls.txt"): open(os.path.join(d, "inputs", f), "a").close()
    return d
def narration(project, mode, voice=None, style=None, speed=None, file=None, method=None):
    """Set a project's narration (M4 B1). Validated against engine/tts.json; logged in the history."""
    C = load(os.path.join(ENGINE, "tts.json")); d = job_dir(project); p = os.path.join(d, "project.json")
    if not os.path.exists(p): fail("PROJECT_NOT_FOUND", f"project not found: {project}")
    P = load(p)
    if mode not in ("ai", "recorded", "none"): fail("NARRATION_MODE_INVALID", "narration must be ai, recorded or none")
    if mode in ("ai", "recorded") and style not in C["styles"]: fail("NARRATION_STYLE_INVALID", f"--style must be one of {sorted(C['styles'])}")
    if mode == "ai":
        if voice not in C["voices"]: fail("NARRATION_VOICE_INVALID", f"--voice must be one of {sorted(C['voices'])}")
        sp = float(speed if speed is not None else C["speed"]["default"])
        if not (C["speed"]["min"] <= sp <= C["speed"]["max"]): fail("NARRATION_SPEED_INVALID", f"--speed must be {C['speed']['min']}..{C['speed']['max']}")
        P.update(narration="ai", narrator=voice, narrator_style=style, narration_speed=sp); P.pop("narration_file", None)
        if method:
            if method not in ("rubberband", "atempo"): fail("NARRATION_SPEED_INVALID", "--method must be rubberband or atempo")
            P["narration_speed_method"] = method
    elif mode == "recorded":
        if not file or not os.path.exists(file if os.path.isabs(file) else os.path.join(d, file)): fail("NARRATION_FILE_MISSING", f"recording not found: {file}")
        P.update(narration="recorded", narrator_style=style, narration_file=file); [P.pop(k, None) for k in ("narrator", "narration_speed", "narration_speed_method")]
    else:
        P["narration"] = "none"; [P.pop(k, None) for k in ("narrator", "narration_speed", "narration_file", "narration_speed_method")]
    save(P, p); log(dict(_dir=d), f"narration set: {mode}" + (f" {voice} {style} {P.get('narration_speed')}x" if mode == "ai" else f" {style or ''}"))
    return P
def next_step(project):
    """The workflow at a glance: what is done and the one next command (used by people and by the app)."""
    d = job_dir(project); q = f'"{project}"' if " " in project else project; b = os.path.join(d, "build")
    if not os.path.exists(os.path.join(d, "project.json")): return [], f"python3 engine/rs.py new <brand> <platform> <style> <slug>"
    P = load(os.path.join(d, "project.json")); done = [f"project: {P['brand']} / {P['platform']} / {P['style']}"]; ex = os.path.exists
    exports = sorted(glob.glob(os.path.join(ROOT, "exports", os.path.basename(d) + "_*_v*.mp4")))
    if P.get("video"):
        if not (ex(os.path.join(b, "transcript.json")) or ex(os.path.join(b, "words.json"))): return done, f"python3 engine/rs.py plan {q}   (transcribes, then plans)"
        done.append("transcript")
        if not ex(os.path.join(b, "plan.json")): return done, f"python3 engine/rs.py plan {q}"
        pl = load(os.path.join(b, "plan.json"))
        if not pl.get("approved"): return done + ["plan drafted (build/plan.md)"], f"read build/plan.md, then: python3 engine/rs.py approve {q} A|B|C|D [--checked]   (own hook: rs.py hook {q} \"l1 / l2 / l3 / h1 / h2\")"
        done.append(f"plan approved (hook {pl.get('hook_choice')})")
    else:
        mode = P.get("narration")
        if mode is None: return done, f"python3 engine/rs.py narration {q} ai --voice prakash|lalitha --style news|documentary   (or recorded ... / none)"
        done.append(f"narration: {mode}" + (f" ({P.get('narrator')}, {P.get('narrator_style')}, {P.get('narration_speed', 1.0)}x)" if mode == "ai" else ""))
        nj = os.path.join(b, "narration.json")
        if not ex(nj): return done, f"write one sentence per line in inputs/script.txt, then: python3 engine/rs.py script {q} inputs/script.txt"
        if not load(nj).get("approved"): return done + ["script prepared (check the ❓ lines)"], f"python3 engine/rs.py script-approve {q} [--checked]"
        done.append("script approved")
        if mode in ("ai", "recorded"):
            import adapter
            bad = adapter.narration_ready(dict(P, _dir=d))
            if bad or not ex(os.path.join(b, "narration_words.json")): return done, f"python3 engine/adapter.py narrate {q}"
            done.append("narration made + checked (build/narration_check.json)")
    if not (ex(os.path.join(b, "edit.mp4")) and ex(os.path.join(b, "edit_layout.json"))): return done, f"python3 engine/rs.py build {q}"
    done.append("edit built")
    if not exports: return done, f"python3 engine/adapter.py render {q} --all-platforms"
    done.append(f"exported: {len(exports)} file(s), latest {os.path.basename(exports[-1])}")
    return done, "review the exports and their _qa.json / _qa.jpg; publishing is always done by you, by hand"

def log(j, msg):
    p = os.path.join(j["_dir"], "project.json"); d = load(p); d.setdefault("history", []).append(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {msg}"); save(d, p)
def render(project, suffix="", platform=None):
    """Title page + frame + final reel. platform (or RS_PLATFORM) renders for that platform WITHOUT changing project.json."""
    prev = os.environ.get("RS_PLATFORM")
    if platform: os.environ["RS_PLATFORM"] = platform
    try:
        j, c = job(project); b = os.path.join(j["_dir"], "build")
        for f in ("edit.mp4", "edit_audio.wav"):
            if not os.path.exists(os.path.join(b, f)): fail("EDIT_MISSING", f"missing build/{f} - build the edit first")
        py = sys.executable
        for step in (["title.py", project], ["frame.py", project], ["assemble.py", project, f"{b}/edit.mp4", f"{b}/edit_audio.wav", suffix]):
            r = subprocess.run([py, os.path.join(ENGINE, step[0])] + step[1:], capture_output=True, text=True)
            if r.stdout.strip(): print(r.stdout.strip(), flush=True)
            if r.returncode:
                if EVENTS: sys.exit(1)          # the step already sent its error event
                sys.exit(r.stderr[-1500:])
        out = os.path.join(ROOT, "exports", f"{os.path.basename(j['_dir'])}_{j['brand']}_{j['platform']}{suffix}.mp4")
        shutil.copy(os.path.join(b, "cover_4k.jpg"), out.replace(".mp4", "_cover_4k.jpg")); log(j, f"rendered {os.path.basename(out)}"); return out
    finally:
        if platform:
            if prev is None: os.environ.pop("RS_PLATFORM", None)
            else: os.environ["RS_PLATFORM"] = prev
if __name__ == "__main__":
    a = sys.argv[1:] or ["help"]; cmd = a[0]
    if cmd == "brands":
        for b in brands():
            c = load(os.path.join(ROOT, "brands", b, "brand.json")); print(f"- {b}: {c['name']} | {c['handle']} | {c['language']} | frame={c['frame']['type']} | style={c['default_style']}")
    elif cmd in ("platforms", "styles"):
        for n in names(cmd): print(f"- {n}: {load(os.path.join(ROOT, cmd, n+'.json'))['name']}")
    elif cmd == "providers":
        import providers; cfg = providers.CFG
        for p, ok in providers.status().items():
            how = ("running" if ok else "not running (start Ollama)") if p == "local" else ("key set" if ok else f"key NOT set ({cfg['providers'][p]['key_env']})")
            print(f"- {p}: {cfg['providers'][p]['name']} | {how}{' | default' if p == cfg['default'] else ''}")
    elif cmd == "new": print(new(*a[1:5]))
    elif cmd == "ingest":
        j, c = job(a[1]); i = os.path.join(j["_dir"], "inputs"); inv = dict(videos=[], images=[], audio=[], urls=[], notes="")
        for f in sorted(os.listdir(i)):
            p = os.path.join(i, f); e = f.lower().rsplit(".", 1)[-1]
            if e in ("mp4", "mov", "mkv", "webm", "m4v"): inv["videos"].append(dict(file=f"inputs/{f}", **probe(p)))
            elif e in ("jpg", "jpeg", "png", "webp", "heic"): inv["images"].append(f"inputs/{f}")
            elif e in ("mp3", "wav", "m4a"): inv["audio"].append(f"inputs/{f}")
        inv["urls"] = [u.strip() for u in open(os.path.join(i, "urls.txt"), encoding="utf-8") if u.strip()]
        inv["notes"] = open(os.path.join(i, "notes.txt"), encoding="utf-8").read()
        inv["mode"] = "speaker" if inv["videos"] and inv["videos"][0]["audio"] else "slides"
        save(inv, os.path.join(j["_dir"], "build", "inputs.json")); log(j, f"ingested ({inv['mode']})"); print(json.dumps(inv, ensure_ascii=False, indent=1))
    elif cmd == "narration":
        if len(a) < 3: sys.exit(__doc__)
        opt = lambda k: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None
        P = narration(a[1], a[2], opt("--voice"), opt("--style"), opt("--speed"), opt("--file"), opt("--method"))
        print(json.dumps({k: P.get(k) for k in ("narration", "narrator", "narrator_style", "narration_speed", "narration_speed_method", "narration_file") if k in P}, ensure_ascii=False))
    elif cmd in ("script", "script-approve"):
        import narration_script as NS
        j, c = job(a[1])
        if cmd == "script":
            if len(a) < 3: sys.exit(__doc__)
            f = a[2] if os.path.isabs(a[2]) or os.path.exists(a[2]) else os.path.join(j["_dir"], a[2])
            print(NS.show(NS.prepare(j, f))); log(j, f"narration script prepared from {a[2]}")
        else: print(NS.show(NS.approve(j, "--checked" in a)))
    elif cmd in ("plan", "hook", "approve", "build"):
        if len(a) < 2 or (cmd in ("hook", "approve") and len(a) < 3): sys.exit(__doc__)
        if cmd == "build": args = ["build.py", a[1]]
        elif cmd == "plan":
            d = job_dir(a[1]); P = load(os.path.join(d, "project.json"))
            if P.get("video") and not any(os.path.exists(os.path.join(d, "build", f)) for f in ("transcript.json", "words.json")):
                r = subprocess.run([sys.executable, os.path.join(ENGINE, "transcribe.py"), "--project", a[1]])
                if r.returncode: sys.exit(r.returncode)
            args = ["planner.py", a[1]]
        elif cmd == "hook": args = ["planner.py", a[1], "--hook", a[2]]
        else: args = ["planner.py", a[1], "--approve", a[2]] + (["--checked"] if "--checked" in a else [])
        r = subprocess.run([sys.executable, os.path.join(ENGINE, args[0])] + args[1:]); sys.exit(r.returncode)
    elif cmd == "next":
        done, nxt = next_step(a[1]); [print("  done:", x) for x in done]; print("  next:", nxt)
    elif cmd == "render": render(a[1])
    elif cmd == "reexport":
        if a[2] not in names("platforms"): fail("UNKNOWN_PLATFORM", f"unknown platform {a[2]}")
        render(a[1], platform=a[2])   # project.json keeps its own platform
    elif cmd == "check":
        for t in ("ffmpeg", "ffprobe", "node", "npx", "whisper"): print(f"{t:12}", shutil.which(t) or "MISSING")
        for m in ("PIL", "numpy", "scipy", "cv2", "onnxruntime"):
            try: __import__(m); print(f"{m:12} ok")
            except Exception: print(f"{m:12} MISSING  -> pip install --user pillow numpy scipy opencv-python onnxruntime")
        errs = validate(); print("settings    ", "ok" if not errs else ""); [print("  !", e) for e in errs]
    else: print(__doc__)
