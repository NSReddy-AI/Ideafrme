"""Post copy draft beside an export (M4 app): exports/<reel>_post.md, following the platform's `post` settings.
    python3 engine/post.py <project> exports/<reel>.mp4
Uses ONLY approved material: the approved hook + headline, the approved narration script (narrated/text reels) and the planner's
checked hashtags (speaker reels). Nothing new is written in Telugu; missing parts are left as clearly marked blanks for the user.
Nothing is ever posted: the user copies this by hand when they publish."""
import os, sys, json
from common import ROOT, load, job_dir

def draft(project, export):
    d = job_dir(project); P = load(os.path.join(d, "project.json")); b = os.path.join(d, "build")
    base = os.path.basename(export)[:-4]; pf = base.rsplit("_v", 1)[0].rsplit("_", 1)[-1]
    PF = load(os.path.join(ROOT, "platforms", pf + ".json")); post = PF.get("post", {}); B = load(os.path.join(ROOT, "brands", P["brand"], "brand.json"))
    hk = P.get("hook") or {}; hook = " ".join(x for x in (hk.get("line1"), hk.get("line2"), hk.get("line3")) if x)
    head = " ".join(x for x in (P.get("title") or []) if x)
    body = []
    nj = os.path.join(b, "narration.json")
    if os.path.exists(nj) and load(nj).get("approved"): body = [l["text"] for l in load(nj)["lines"]]
    tags = []
    pj = os.path.join(b, "plan.json")
    if os.path.exists(pj):
        PL = load(pj)
        if PL.get("approved"): tags = list((PL.get("facts", {}).get("post") or {}).get("hashtags") or [])
    lo, hi = (post.get("hashtags") or [0, 0])[:2]; tags = ["#" + t.lstrip("#") for t in tags][:hi]
    L = [f"# Post copy - {PF['name']} ({base})", "", "DRAFT for your review. Nothing is posted automatically; copy it by hand when you publish.",
         f"Platform rules: {post.get('note', '')}", ""]
    if P.get("narration") == "ai":
        L += ["**AI voice:** this reel uses a synthetic narrator. Switch ON the platform's AI-generated content label when uploading. "
              "The on-screen Telugu AI disclosure is already in the video.", ""]
    if "title" in post.get("fields", []):
        t = hook or head; L += ["## Title", "", t or "(write the title)", "", f"({len(t)}/{post.get('title_max_chars')} characters, aim for {post.get('title_target_chars')})", ""]
    first = hook or head
    text = "\n".join(x for x in [first, head if head and head != first else "", "", *body] if x is not None).strip()
    key = "description" if "description" in post.get("fields", []) else "caption"
    lim = post.get(f"{key}_max_chars")
    L += [f"## {key.capitalize()}", "", text or f"(write the {key})", "", f"({len(text)}/{lim} characters)", ""]
    L += ["## Hashtags", "", " ".join(tags) if tags else f"(add {lo}-{hi} hashtags - none were approved for this reel)", ""]
    if len(tags) < lo: L += [f"note: {lo}-{hi} hashtags recommended for {PF['name']}", ""]
    L += [f"Brand: {B['name']} {B.get('handle', '')}"]
    out = os.path.join(os.path.dirname(export), base + "_post.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n"); return out

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    print(draft(sys.argv[1], sys.argv[2]))
