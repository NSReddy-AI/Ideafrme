"""Gate A2.1 - METADATA-ONLY inspection of Indic Parler-TTS and its second (description) tokenizer (authorised 10 Nov 2026).

Run on the Mac AFTER you accepted the model's terms and saved a read token in the Keychain as AI_REEL_STUDIO_HF_READ:
  cd "/Users/Nadish/projects/AI Video Editor./Reel Studio_dev"
  HF_TOKEN="$(security find-generic-password -a "$USER" -s AI_REEL_STUDIO_HF_READ -w)" ~/.venvs/reelstudio/bin/python tools/gate_a2_1_tokenizer.py

Safety rules (static review, 10 Nov):
  1. Metadata only: the Hugging Face model API (file lists, sizes, revisions, licence tags), small TEXT files
     (config.json, tokenizer_config.json, README.md header, LICENSE) and the HEADER of model.safetensors (its list of tensor
     names, read with byte ranges) - every read is refused above 300 kB. No tensor data, weights or vocab files are read.
  2. Uses only the Python standard library (urllib, json). It never imports transformers / huggingface_hub, never runs
     repository code, never sets trust_remote_code, never installs anything.
  3. The token is sent only to huggingface.co, only in a request header. It is never printed or written. Redirects are
     followed only within huggingface.co; for the model-file header only, a redirect to Hugging Face's own storage host is
     followed WITHOUT the token (signed link). Any other redirect is refused. Errors are short reasons, never raw exceptions.
  4. Every file is read at the exact commit (revision) recorded in the evidence.
  5. Evidence goes to a NEW folder tests/acceptance/M4_gateA2_1/<date_time>/ - an existing folder is never overwritten.
  6. Fails closed: a missing or unapproved licence, a missing description-tokenizer reference, an unreadable referenced
     repository, custom code (auto_map), a gated tokenizer source, a network error or a file over the limit -> FINAL: STOP.
  7. Writes nothing else: no environments, no project files, no production files.
Metadata cannot prove offline operation; that is a runtime test at A2.2."""
import json, os, sys, time, struct, http.client, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "ai4bharat/indic-parler-tts"
HOST = "huggingface.co"
TEXT_MAX = 300_000
ALLOWED = ("mit", "bsd", "apache", "isc", "psf", "mpl-2.0", "unlicense", "cc0", "gpl", "lgpl", "agpl")
TOKENIZER_FILES = ("tokenizer_config.json", "tokenizer.json", "spiece.model", "sentencepiece.bpe.model", "special_tokens_map.json",
                   "vocab.json", "merges.txt", "vocab.txt", "added_tokens.json")
TOKEN = os.environ.get("HF_TOKEN", "").strip()

def _storage(host):
    """Hugging Face's own download servers (used for large files). The token is NEVER sent there."""
    return host == "hf.co" or host.endswith(".hf.co") or host.endswith(".huggingface.co")

def fetch(url, rng=None, allow_storage=False, max_bytes=TEXT_MAX, hops=3):
    """GET with a hard size cap. Redirects: followed only to huggingface.co (token kept) or, when allow_storage, to
    Hugging Face's storage hosts (token dropped). Anything else is refused (fail closed). Returns (bytes, None) or (None, reason)."""
    u = urllib.parse.urlparse(url); host = u.hostname or ""
    if host == HOST: send_token = True
    elif allow_storage and _storage(host): send_token = False
    else: return None, f"redirect to {host} refused"
    h = {"User-Agent": "reel-studio-gateA2.1"}
    if send_token and TOKEN: h["Authorization"] = "Bearer " + TOKEN
    if rng: h["Range"] = rng
    try:
        c = http.client.HTTPSConnection(host, timeout=60)
        c.request("GET", u.path + (("?" + u.query) if u.query else ""), headers=h); r = c.getresponse()
        if 300 <= r.status < 400:
            loc = r.getheader("Location") or ""; r.read(0); c.close()
            if hops == 0 or not loc: return None, f"HTTP {r.status} (too many or empty redirects)"
            return fetch(urllib.parse.urljoin(url, loc), rng, allow_storage, max_bytes, hops - 1)
        if r.status not in (200, 206): c.close(); return None, f"HTTP {r.status}"
        n = r.getheader("Content-Length")
        if n and int(n) > max_bytes: c.close(); return None, f"refused: {int(n)} bytes is over the {max_bytes // 1000} kB metadata limit"
        data = r.read(max_bytes + 1); c.close()
        if len(data) > max_bytes: return None, f"refused: over the {max_bytes // 1000} kB metadata limit"
        return data, None
    except Exception as e: return None, f"network error ({type(e).__name__})"

def _get(path, accept_json):
    data, err = fetch(f"https://{HOST}{path}")
    if err: return None, err
    try: return (json.loads(data) if accept_json else data.decode("utf-8", "replace")), None
    except Exception: return None, "unreadable response"

def api(repo): return _get(f"/api/models/{repo}?blobs=true", True)
def text(repo, rev, name): return _get(f"/{repo}/resolve/{rev}/{name}", False)

def safetensors_prefixes(repo, rev, name="model.safetensors"):
    """Read ONLY the safetensors header (tensor names) with byte ranges: 8 bytes for its length, then the header itself
    (refused above 300 kB). No tensor data is read. Returns ({prefix: count}, None) or (None, reason)."""
    url = f"https://{HOST}/{repo}/resolve/{rev}/{name}"
    head, err = fetch(url, rng="bytes=0-7", allow_storage=True, max_bytes=8)
    if err or len(head or b"") != 8: return None, err or "could not read the header length"
    n = struct.unpack("<Q", head)[0]
    if n > TEXT_MAX: return None, f"header is {n} bytes, over the 300 kB limit"
    hdr, err = fetch(url, rng=f"bytes=8-{7 + n}", allow_storage=True, max_bytes=n)
    if err: return None, err
    try: names = [k for k in json.loads(hdr) if k != "__metadata__"]
    except Exception: return None, "header is not valid JSON"
    out = {}
    for k in names: p = k.split(".")[0]; out[p] = out.get(p, 0) + 1
    return out, None

def licence_tag(info):
    card = (info or {}).get("cardData") or {}
    tags = [t.split(":", 1)[1] for t in (info or {}).get("tags", []) if t.startswith("license:")]
    lic = card.get("license") or (tags[0] if tags else None)
    return lic if isinstance(lic, str) else (json.dumps(lic) if lic else None)

def approved(l): return bool(l) and any(a in l.lower() for a in ALLOWED) and not any(b in l.lower() for b in ("-nc", "noncommercial", "non-commercial", "research"))

def refs(cfg, path=""):
    out = []
    if isinstance(cfg, dict):
        for k, v in cfg.items():
            if k == "_name_or_path" and isinstance(v, str) and "/" in v and not v.startswith(("/", ".")): out.append((path or "(root)", v))
            else: out += refs(v, f"{path}.{k}" if path else k)
    return out

def main():
    stops, L, E = [], [], dict(when=time.strftime("%Y-%m-%d %H:%M:%S"), model=MODEL)
    out = os.path.join(ROOT, "tests", "acceptance", "M4_gateA2_1", time.strftime("%Y%m%d_%H%M%S"))
    if os.path.exists(out): print("Evidence folder already exists - refusing to overwrite. Wait a second and run again."); sys.exit(2)
    if not TOKEN: print("No token found (Keychain item AI_REEL_STUDIO_HF_READ). Nothing was done."); sys.exit(2)
    L += ["# Gate A2.1 - tokenizer provenance (metadata only)", "", f"Run {E['when']}. Metadata and small text files only; nothing installed.", ""]
    info, err = api(MODEL)
    if err: print(f"Model API: {err}. If HTTP 401/403: accept the terms on the model page with the account that owns the token, "
                  "or give the fine-grained token read access to this repository. Nothing was written."); sys.exit(2)
    rev = info.get("sha"); files = {s["rfilename"]: s.get("size") for s in info.get("siblings", [])}
    E.update(model_revision=rev, model_licence_tag=licence_tag(info), gated=info.get("gated"), model_files=files)
    if not approved(E["model_licence_tag"]): stops.append(f"model licence tag is '{E['model_licence_tag']}'")
    L += ["## Model repository", "", f"- revision (commit): `{rev}`", f"- licence TAG (repository metadata): {E['model_licence_tag']} | gated: {info.get('gated')}",
          f"- files ({len(files)}), total {round(sum(v or 0 for v in files.values()) / 1e9, 3)} GB:"] + [f"  - {k}: {round((v or 0) / 1e6, 2)} MB" for k, v in sorted(files.items())]
    cfg_txt, err = text(MODEL, rev, "config.json")
    if err: stops.append(f"model config.json unreadable ({err})"); cfg = {}
    else: cfg = json.loads(cfg_txt)
    ext = refs(cfg); te = (cfg.get("text_encoder") or {}).get("_name_or_path")
    E.update(auto_map=cfg.get("auto_map"), external_refs=ext, description_tokenizer_source=te, sampling_rate=cfg.get("sampling_rate"))
    if cfg.get("auto_map"): stops.append("model config requires custom code (auto_map)")
    pre, perr = safetensors_prefixes(MODEL, rev) if files.get("model.safetensors") else (None, "no model.safetensors")
    E.update(weight_groups=pre, weight_header_error=perr)
    inside = set(pre or {})
    if perr: stops.append(f"model file header unreadable ({perr}) - cannot tell which weights are inside")
    L += ["", "## What is inside model.safetensors (header only, no weights read)", ""] + \
         ([f"- `{k}.*`: {v} tensors" for k, v in sorted((pre or {}).items())] or [f"- {perr}"])
    if cfg and not te: stops.append("config.json names no text_encoder source - description tokenizer unknown")
    L += ["", "## What the model's config.json points to", "", f"- custom code (auto_map): {'YES' if cfg.get('auto_map') else 'no'}"] + \
         [f"- `{p}` -> **{r}**" for p, r in ext] + [f"- sampling rate: {cfg.get('sampling_rate')}"]
    for path, repo in ext:
        i2, e2 = api(repo); is_tok = repo == te
        L += ["", f"## Referenced repository: {repo}  (from `{path}`{'; DESCRIPTION TOKENIZER' if is_tok else ''})", ""]
        if e2: stops.append(f"{repo} unreadable ({e2})"); L.append(f"- API: {e2} -> STOP"); continue
        sha2 = i2.get("sha"); tag2 = licence_tag(i2); f2 = {s["rfilename"]: s.get("size") for s in i2.get("siblings", [])}
        lic_file = next((n for n in ("LICENSE", "LICENSE.txt", "LICENSE.md") if n in f2), None)
        lic_txt, lic_err = text(repo, sha2, lic_file) if lic_file else (None, "no LICENSE file in the repository")
        rd, rd_err = text(repo, sha2, "README.md")
        L += [f"- revision (commit): `{sha2}` | author: {i2.get('author')} | last modified: {i2.get('lastModified')} | gated: {i2.get('gated')}",
              f"- licence TAG (repository metadata): **{tag2}**",
              f"- LICENSE file (independent evidence): " + (f"{lic_file}, first lines below" if lic_txt else lic_err)]
        if lic_txt: L += ["```", "\n".join(lic_txt.strip().splitlines()[:6]), "```"]
        L += ["- model card header (for the licence record):", "```", "\n".join((rd or rd_err or "").splitlines()[:20]), "```"]
        part = path.split(".")[0]; weights_inside = part in inside
        if not is_tok and weights_inside:
            L.append(f"- its weights are INSIDE the model file (`{part}.*`): this repository is only a name in the config; nothing is downloaded from it. "
                     "Licence of those weights = the model's release (Apache-2.0); origin to review below")
            if not approved(tag2): L.append(f"- note: this repository itself states no approved licence ('{tag2}'); recorded for review, not a stop")
        elif not approved(tag2): stops.append(f"{repo}: licence tag '{tag2}' is not on the approved list (and its weights are not inside the model file)")
        if i2.get("gated"): stops.append(f"{repo} is gated - needs its own terms review")
        if is_tok:
            need = {k: v for k, v in f2.items() if k in TOKENIZER_FILES}
            tk_txt, tk_err = text(repo, sha2, "tokenizer_config.json")
            if tk_err: stops.append(f"{repo}: tokenizer_config.json unreadable ({tk_err})"); tk = {}
            else: tk = json.loads(tk_txt)
            if tk.get("auto_map"): stops.append(f"{repo}: tokenizer needs custom code (auto_map)")
            if not need: stops.append(f"{repo}: no tokenizer files found")
            L += [f"- tokenizer class: {tk.get('tokenizer_class')} | custom code: {'YES' if tk.get('auto_map') else 'no'}",
                  "- files the tokenizer needs (cached once at A2.2, at this revision): " + ", ".join(f"{k} ({round((v or 0) / 1e6, 2)} MB)" for k, v in need.items())]
            E.update(tokenizer_revision=sha2, tokenizer_licence_tag=tag2, tokenizer_licence_file=bool(lic_txt), tokenizer_files=need,
                     tokenizer_class=tk.get("tokenizer_class"))
        else:
            if not weights_inside: stops.append(f"{repo}: weights are not inside the model file, so they would be downloaded from this repository")
            L.append("- the A2.2 offline load (network off) is the final proof that nothing is fetched from here")
        if is_tok:
            L.append(f"- the text-encoder weights are {'INSIDE the model file - only the tokenizer files come from this repository' if 'text_encoder' in inside else 'NOT inside the model file -> they would be downloaded'}")
            if "text_encoder" not in inside and not perr: stops.append(f"{repo}: text-encoder weights would be downloaded from this repository")
    total = sum(v or 0 for v in files.values()) + sum(v or 0 for v in (E.get("tokenizer_files") or {}).values()) + 223_000_000
    E["download_total_bytes_incl_lock_B"] = total
    if total > 4.5e9: stops.append(f"total download {round(total / 1e9, 2)} GB is over the 4.5 GB ceiling")
    E["stops"] = stops; E["final"] = "STOP" if stops else "PASS"
    L += ["", "## Verdict", "", f"- total download with Lock B: {round(total / 1e9, 3)} GB (ceiling 4.5 GB)",
          "- licence TAGS are repository metadata; the LICENSE file and model card lines above are the independent evidence for your review",
          "- offline operation is NOT proven by metadata; it is a runtime test at A2.2"] + [f"- STOP: {s}" for s in stops] + ["", f"FINAL: {E['final']}"]
    os.makedirs(out)
    open(os.path.join(out, "tokenizer_evidence.md"), "w").write("\n".join(L) + "\n")
    json.dump(E, open(os.path.join(out, "tokenizer_evidence.json"), "w"), indent=1)
    if cfg: open(os.path.join(out, "model_config.json"), "w").write(cfg_txt)
    print("\n".join(L[L.index("## Verdict"):])); print(f"\nEvidence: {os.path.relpath(out, ROOT)}/tokenizer_evidence.md")
    sys.exit(0 if not stops else 2)

if __name__ == "__main__":
    main()
