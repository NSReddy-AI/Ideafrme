"""Shared helpers for Reel Studio.
App hooks (Milestone 2): with RS_EVENTS=1 every script prints one JSON object per line on stdout
  {"event":"progress","step":"assemble","pct":42}   {"event":"error","step":"cut","code":"FFMPEG_FAILED","message":"..."}
Without RS_EVENTS the scripts behave exactly as before (plain text, exit code 1 on failure).
RS_PLATFORM=<name> renders for that platform without changing project.json.
RS_TMP=<folder> is this job's private temp folder (the adapter makes one per render)."""
import json, os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "engine")
FONT_TE = os.path.join(ENGINE, "fonts", "NotoSansTelugu-Black.ttf")
FONT_UI = os.path.join(ENGINE, "fonts", "Inter-Bold.otf")
FONT_MARK = os.path.join(ENGINE, "fonts", "DejaVuSans-Bold.ttf")
W, H, FPS = 1080, 1920, 30
STEP = os.path.splitext(os.path.basename(sys.argv[0]))[0] if sys.argv and sys.argv[0] else "engine"
EVENTS = os.environ.get("RS_EVENTS") == "1"

def emit(event, **kw):
    """One machine-readable line for the app (only when RS_EVENTS=1)."""
    if EVENTS:
        sys.stdout.write(json.dumps(dict(event=event, step=kw.pop("step", STEP), **kw), ensure_ascii=False) + "\n"); sys.stdout.flush()
def progress(pct, note=""):
    emit("progress", pct=max(0, min(100, int(pct))), **({"note": note} if note else {}))
def fail(code, message):
    """Stop this step with an error the app can show. CLI: same text + exit 1 as before."""
    emit("error", code=code, message=message)
    if EVENTS: sys.exit(1)
    sys.exit(message)
def _hook(t, e, tb):
    """Any unexpected crash still reaches the app as one readable error event."""
    if EVENTS and t is not KeyboardInterrupt:
        code = "FILE_NOT_FOUND" if t is FileNotFoundError else "UNEXPECTED"
        emit("error", code=code, message=f"{t.__name__}: {e}")
    sys.__excepthook__(t, e, tb)
sys.excepthook = _hook
def tmpdir():
    """This job's own temp folder (never a shared fixed path)."""
    d = os.environ.get("RS_TMP")
    if d: os.makedirs(d, exist_ok=True); return d
    return tempfile.mkdtemp(prefix="rs_")

def load(path):
    with open(path, encoding="utf-8") as f: return json.load(f)
def save(obj, path):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=2)
def job_dir(job): return job if os.path.isabs(job) else os.path.join(ROOT, "projects", job)
def job(jobname):
    """Load a project -> (project, brand). project["_platform"] / ["_style"] hold the platform and style settings.
    RS_PLATFORM overrides the platform for this run only (project.json is not changed)."""
    d = job_dir(jobname)
    if not os.path.exists(os.path.join(d, "project.json")): fail("PROJECT_NOT_FOUND", f"project not found: {d}")
    j = load(os.path.join(d, "project.json")); j["_dir"] = d
    bd = os.path.join(ROOT, "brands", j["brand"])
    c = load(os.path.join(bd, "brand.json")); c["_dir"] = bd
    pf = os.environ.get("RS_PLATFORM") or j["platform"]
    if not os.path.exists(os.path.join(ROOT, "platforms", pf + ".json")): fail("UNKNOWN_PLATFORM", f"unknown platform '{pf}'")
    j["platform"] = pf
    j["_platform"] = load(os.path.join(ROOT, "platforms", pf + ".json"))
    j["_style"] = load(os.path.join(ROOT, "styles", j["style"] + ".json"))
    os.makedirs(os.path.join(d, "build"), exist_ok=True)
    return j, c
def asset(c, key):
    p = c["assets"].get(key)
    return os.path.join(c["_dir"], p) if p else None
def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def run(cmd, total_s=None, code="FFMPEG_FAILED", pct_range=(0, 99)):
    """Run a command given as a LIST of arguments (no shell, so any file name is safe).
    ffmpeg commands with total_s report live progress. Old-style strings still work (shell) for compatibility."""
    shell = isinstance(cmd, str)
    if total_s and not shell and os.path.basename(cmd[0]) == "ffmpeg":
        cmd = [cmd[0], "-progress", "pipe:1", "-nostats"] + cmd[1:]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        err = []; import threading
        t = threading.Thread(target=lambda: err.extend(p.stderr.readlines()), daemon=True); t.start()
        last = -1
        for line in p.stdout:
            m = re.match(r"out_time_us=(\d+)", line.strip())
            if m:
                lo, hi = pct_range; pct = int(lo + (hi - lo) * min(1, int(m.group(1)) / 1e6 / total_s))
                if pct >= last + 2: progress(pct); last = pct
        p.wait(); t.join(2)
        if p.returncode: fail(code, f"command failed: {' '.join(cmd[:3])}...\n{''.join(err)[-1500:]}")
        return ""
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if r.returncode: fail(code, f"command failed: {cmd if shell else ' '.join(cmd)}\n{r.stderr[-1500:]}")
    return r.stdout
def probe(path):
    if not os.path.exists(path): fail("FILE_NOT_FOUND", f"file not found: {path}")
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_type", "-of", "json", path], code="PROBE_FAILED")
    d = json.loads(out); v = [s for s in d["streams"] if s["codec_type"] == "video"]
    return dict(duration=float(d["format"].get("duration", 0)), w=v[0]["width"] if v else 0, h=v[0]["height"] if v else 0,
                audio=any(s["codec_type"] == "audio" for s in d["streams"]))

def font_for(text):
    """Telugu font if the text has Telugu letters, else the Latin UI font."""
    return FONT_TE if any('ఀ' <= ch <= '౿' for ch in text) else FONT_UI

def safe_area(j):
    """The platform's safe area as (left, top, right, bottom) in 1080x1920 pixels."""
    s = j["_platform"].get("safe_area") or {}
    return s.get("left", 0), s.get("top", 0), s.get("right", W), s.get("bottom", H)
def safe_check(j, boxes):
    """boxes = {name: (l, t, r, b)} -> list of 'name: outside safe area (side by Npx)'."""
    L, T, R, B = safe_area(j); out = []
    for n, (l, t, r, b) in boxes.items():
        for side, over in (("top", T - t), ("bottom", b - B), ("left", L - l), ("right", r - R)):
            if over > 0: out.append(dict(element=n, side=side, px=int(over)))
    return out

# M4 B1: one heavy model at a time (voice model / speech-to-text started by the narration steps). Added; nothing above changed.
import contextlib
HEAVY_LOCK = os.environ.get("RS_HEAVY_LOCK") or os.path.join(ROOT, ".heavy_model.lock")   # RS_HEAVY_LOCK: tests only
@contextlib.contextmanager
def heavy_lock(name):
    """Refuse to start a second heavy model while one runs (lock file with the owner's pid; a crashed owner's lock is taken over)."""
    if os.path.exists(HEAVY_LOCK):
        try:
            pid, owner = open(HEAVY_LOCK).read().split()[:2]; os.kill(int(pid), 0)
            if int(pid) != os.getpid(): fail("BUSY_HEAVY_MODEL", f"another heavy model is running ({owner}, pid {pid}) - wait for it to finish")
        except (ProcessLookupError, PermissionError, ValueError, IndexError): pass   # owner gone (or not ours): stale lock, take it over
    with open(HEAVY_LOCK, "w") as f: f.write(f"{os.getpid()} {name}")
    try: yield
    finally:
        try:
            if open(HEAVY_LOCK).read().split()[0] == str(os.getpid()): os.remove(HEAVY_LOCK)
        except (OSError, IndexError): pass
