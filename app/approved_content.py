"""M6 step 6: approved-content@1, the human-approved words of an M4 reel in a form posters can reuse.

Derived READ-ONLY from what the owner already approved in M4. Nothing in the engine changes and nothing is written:
  - plan       speaker reels: build/plan.json approved, and the SAME checks the render gate makes (adapter.py):
               plan_hash(plan) == plan.approved_hash == project.plan_hash, and project.json's hook lines / headline are the
               chosen hook. Items: hook lines, verbatim quotes (“ ” = the speaker's own words), headline lines, the
               title-page tag, every number card (number — label, from the speaker's words) and the checked post intro.
  - narration  narrated / slides reels: build/narration.json approved, fingerprint(lines) == approved_hash == project.narration_hash
               (narration_script.verify). Items: each approved sentence.
  - project    a hand-approved baseline with no plan (reel_002): project.json "approved": true. Items: hook lines, tag, headline.
               Weaker evidence (no fingerprint exists for it), so it is labelled as such.
If an approval is missing, stale or edited after approval, there is NO approved content (ApprovalError) - never a guess.
Every item carries the SHA-256 of its exact text, and the document a fingerprint over source + approvals + items, so a
poster that reuses an item can later prove the words are unchanged and still approved."""
import hashlib, json, os, re

FORMAT = "ideaframe-approved-content@1"
TE = re.compile(r"[ఀ-౿]")


class ApprovalError(ValueError):
    def __init__(self, code, message): super().__init__(message); self.code = code


def sha(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()
def canonical(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def language(text): return "te" if TE.search(text) else "en"


def _load(path):
    with open(path, encoding="utf-8") as f: return json.load(f)


def _item(items, ident, kind, text, origin, verbatim=False):
    if isinstance(text, str) and text.strip():
        items.append(dict(id=ident, kind=kind, text=text, language=language(text), verbatim=verbatim, origin=origin, sha256=sha(text)))


def _hook_items(items, hook, headline, approval, tag=None):
    for k in ("line1", "line2", "line3"):
        t = hook.get(k, "")
        quoted = t.startswith("“") and t.endswith("”")
        _item(items, f"hook.{k}", "quote" if quoted else "hook", t, dict(approval=approval, field=f"hook.{k}"), verbatim=quoted)
    for i, t in enumerate(headline or [], 1): _item(items, f"headline.{i}", "headline", t, dict(approval=approval, field=f"headline[{i - 1}]"))
    if tag: _item(items, "tag", "tag", tag, dict(approval=approval, field="tag"))


def derive(project_dir, engine_dir):
    """approved-content@1 for one M4 project folder, or ApprovalError."""
    import sys
    if engine_dir not in sys.path: sys.path.insert(0, engine_dir)
    d = str(project_dir); name = os.path.basename(os.path.normpath(d))
    pj = os.path.join(d, "project.json")
    if not os.path.isfile(pj): raise ApprovalError("NOT_FOUND", f"no project {name}")
    J = _load(pj); items, approvals = [], []
    plan_p, narr_p = os.path.join(d, "build", "plan.json"), os.path.join(d, "build", "narration.json")

    if os.path.isfile(plan_p):
        from planner import plan_hash
        P = _load(plan_p)
        if not P.get("approved"): raise ApprovalError("PLAN_NOT_APPROVED", "the plan is not approved yet")
        ch = P.get("hook_choice"); hooks = P.get("creative", {}).get("hooks", [])
        idx = "ABCDEFG".index(ch) if ch and ch in "ABCDEFG" else -1
        if not 0 <= idx < len(hooks): raise ApprovalError("PLAN_STALE", "the approved hook choice is missing")
        hook = hooks[idx]; pjh = J.get("hook", {})
        same_page = [pjh.get(k) for k in ("line1", "line2", "line3")] == [hook.get(k) for k in ("line1", "line2", "line3")] and list(J.get("title", [])) == list(hook.get("headline", []))
        if P.get("approved_hash") != plan_hash(P) or J.get("plan_hash") != P.get("approved_hash") or not same_page:
            raise ApprovalError("PLAN_STALE", "the plan or the title page changed after approval - approve it again")
        approvals.append(dict(type="plan", hash=P["approved_hash"], hook_choice=ch, approved_at=P.get("approved_at"), checked=bool(P.get("checked"))))
        F = P.get("facts", {}); tag = (F.get("tag") or {}).get("text")
        _hook_items(items, hook, hook.get("headline"), "plan", tag)
        for b in F.get("beats", []):
            g = b.get("graphic", {})
            if g.get("type") == "number" and g.get("number"):
                _item(items, f"card.{b.get('claim', len(items))}", "number", f"{g['number']} — {g.get('label', '')}".strip(" —"),
                      dict(approval="plan", field="facts.beats", words=g.get("spoken", {}).get("words"), spoken=g.get("spoken", {}).get("text")))
        caption = (F.get("post") or {}).get("caption", "")
        if caption: _item(items, "post.intro", "post", caption.split("\n")[0], dict(approval="plan", field="facts.post.caption[0]"))

    if os.path.isfile(narr_p) and J.get("narration") in ("ai", "recorded", "none"):
        from narration_script import fingerprint
        N = _load(narr_p)
        if N.get("approved"):
            if fingerprint(N["lines"]) != N.get("approved_hash") or J.get("narration_hash") != N.get("approved_hash"):
                raise ApprovalError("SCRIPT_STALE", "the narration script changed after approval - approve it again")
            approvals.append(dict(type="narration", hash=N["approved_hash"], approved_at=N.get("approved_at"), checked=bool(N.get("checked"))))
            for i, line in enumerate(N["lines"], 1): _item(items, f"script.{i}", "script", line["text"], dict(approval="narration", field=f"lines[{i - 1}].text"))

    if not approvals and J.get("approved") is True and J.get("hook"):
        approvals.append(dict(type="project", hash=None, note="hand-approved project without a plan (project.json approved: true); no fingerprint exists"))
        hk = J["hook"]; tag = " ".join(x for x in (hk.get("tag_top"), hk.get("tag_bottom")) if x) or None
        _hook_items(items, hk, J.get("title"), "project", tag)

    if not approvals: raise ApprovalError("NOT_APPROVED", "nothing in this project is approved yet")
    seen = set()
    for it in items:                                    # stable, unique ids
        base, n = it["id"], 2
        while it["id"] in seen: it["id"] = f"{base}.{n}"; n += 1
        seen.add(it["id"])
    source = dict(kind="m4-reel", project=name, brand=J.get("brand"), style=J.get("style"))
    doc = dict(format=FORMAT, source=source, approvals=approvals, items=items)
    doc["fingerprint"] = sha(canonical(doc))
    return doc


def item_status(doc_or_error, item_id, item_sha256, current_text):
    """Is a reused item still the approved words? -> (ok, detail). doc_or_error: a fresh derive() result or its ApprovalError."""
    if isinstance(doc_or_error, Exception): return False, f"the reel's approval is no longer valid: {doc_or_error}"
    it = next((x for x in doc_or_error["items"] if x["id"] == item_id), None)
    if it is None or it["sha256"] != item_sha256: return False, "the approved line changed or was removed in the reel - insert it again"
    if current_text != it["text"]: return False, "the text was edited after insertion; approved words must stay exactly as approved"
    return True, "exactly as approved"
