"""M4 release register (11 Nov 2026). Read-only inputs: tools/deps_m4.json (from tools/scan_licences_m4.py) + the existing docs/SBOM.json.
Writes docs/SBOM.json (CycloneDX 1.5, regenerated) and docs/M4_DEPENDENCY_TABLES.md (generated tables, linked from the inventory).
Licences come from the installed packages' own metadata/licence files; the few that metadata cannot settle are resolved below from
the licence file shipped inside the package (checked 11 Nov). Run:  ~/.venvs/reelstudio/bin/python tools/make_register_m4.py"""
import os, json, uuid, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOCS = os.path.join(ROOT, "docs")
D = json.load(open(os.path.join(ROOT, "tools", "deps_m4.json"))); OLD = json.load(open(os.path.join(DOCS, "SBOM.json")))
RESOLVED = {  # metadata blank or raw text -> licence file inside the installed package (read 11 Nov 2026)
    "parler_tts": "Apache-2.0", "ptyprocess": "ISC", "kiwisolver": "BSD-3-Clause", "matplotlib": "LicenseRef-Matplotlib (PSF-based)"}
USE = {"reelstudio": "Reel Studio engine + app backend (~/.venvs/reelstudio)", "rs_tts": "offline AI narration, Indic Parler-TTS (~/.venvs/rs_tts)",
       "rs_asr": "speech-to-text, Telugu Whisper (~/.venvs/rs_asr)"}
def lic(x):
    if " OR " in x or " AND " in x or " WITH " in x: return [{"expression": x}]
    return [{"license": ({"id": x} if " " not in x and not x.startswith("LicenseRef") else {"name": x})}]
comps, rows = {}, {}
for env, pk in D["python"].items():
    for p in pk:
        l = RESOLVED.get(p["name"].replace("-", "_").lower(), RESOLVED.get(p["name"], p["license"])) or "UNKNOWN"
        k = f'{p["name"].lower()}@{p["version"]}'
        c = comps.setdefault(k, dict(type="library", name=p["name"], version=p["version"], purl=f'pkg:pypi/{p["name"].lower()}@{p["version"]}', licenses=lic(l),
                                     properties=[]))
        c["properties"].append({"name": "reelstudio:environment", "value": env})
        rows.setdefault(env, []).append((p["name"], p["version"], l))
if "parler_tts@0.2.2" in comps: comps["parler_tts@0.2.2"]["purl"] = "pkg:github/huggingface/parler-tts@d108732cd57788ec86bc857d99a6cabd66663d68"
for p in D["npm"]["packages"]:
    shipped = p["name"] in D["npm"]["shipped"]
    comps[f'npm:{p["name"]}@{p["version"]}'] = dict(type="library", name=p["name"], version=p["version"], purl=f'pkg:npm/{p["name"]}@{p["version"]}', licenses=lic(p["license"]),
                                                   scope="required" if shipped else "excluded", properties=[{"name": "reelstudio:use", "value": "shipped in app/web/dist" if shipped else "web app build tool (not shipped)"}])
MODELS = [  # (name, version/revision, licence, use, licence evidence)
    ("ai4bharat/indic-parler-tts", "660bc53c64ae83150613264111708a0465211237", "Apache-2.0", "offline AI narration (Prakash, Lalitha)", "Hugging Face licence tag apache-2.0 recorded at install (Gate A2.1, tokenizer_evidence.json); gated download"),
    ("google/flan-t5-large (tokenizer only)", "0613663d0d48ea86ba8cb3d7a44f0f65dc596a2a", "Apache-2.0", "narration voice description tokenizer", "licence tag apache-2.0 recorded at install (Gate A2.1)"),
    ("vasista22/whisper-telugu-large-v2", "ba19a24bf6530de184860de2b8ba968595b9b18a", "Apache-2.0", "Telugu speech-to-text (weights sha256 1c3388d4…)", "recorded at M3 install (engine/asr.json licence); model card not cached - re-confirm online before any redistribution"),
    ("openai/whisper-large-v2 (generation config only)", "ae4642769ce2ad8fc292556ccea8e901f1530655", "Apache-2.0", "alignment heads + language table for Telugu Whisper", "OpenAI Whisper weights are MIT (code) / Apache-2.0 on Hugging Face; only a config file is used"),
    ("whisper.cpp ggml-large-v3-turbo", "local file", "MIT", "English speech-to-text", "OpenAI Whisper weights MIT"),
    ("Qwen3 14B (Ollama qwen3:14b)", "bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8", "Apache-2.0", "local AI planner (approved model)", "`ollama show qwen3:14b --license` = Apache License 2.0 (read locally 11 Nov)"),
    ("Qwen3 8B (Ollama qwen3:8b)", "500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41", "Apache-2.0", "planner backup only (never automatic)", "`ollama show qwen3:8b --license` = Apache License 2.0"),
]
for n, v, l, u, ev in MODELS:
    comps[f"model:{n}"] = dict(type="machine-learning-model", name=n, version=v, licenses=lic(l), properties=[{"name": "reelstudio:use", "value": u}, {"name": "reelstudio:licence-evidence", "value": ev}])
for c in OLD["components"]:          # keep tools, vendored models and fonts from the M2/M3 register (GSAP was removed on 10 Nov)
    if c.get("purl", "").startswith("pkg:pypi") or c["name"] == "gsap": continue
    comps[f'old:{c["name"]}'] = c
comps["app:ollama"] = dict(type="application", name="Ollama", version="0.40.16", purl="pkg:brew/ollama@0.40.16", licenses=lic("MIT"), properties=[{"name": "reelstudio:use", "value": "runs the local planner model"}])
ff = comps.get("old:FFmpeg")
if ff: ff["licenses"] = lic("GPL-3.0-or-later"); ff.setdefault("properties", []).append({"name": "reelstudio:build", "value": " ".join(D["tools"]["ffmpeg_configuration"][:12]) + " …"})
sbom = dict(bomFormat="CycloneDX", specVersion="1.5", serialNumber=f"urn:uuid:{uuid.uuid4()}", version=2,
            metadata=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(), component=dict(type="application", name="AI Reel Studio", version="M4 release candidate"),
                          properties=[{"name": "reelstudio:excluded", "value": "gemma2 (Ollama) - cached on this Mac, not used, Gemma Terms of Use are not an open-source licence; never part of a release"},
                                      {"name": "reelstudio:test-only-not-released", "value": "faster-whisper models, ggml-large-v3, ggml-te-small, openai-whisper (pipx), PySceneDetect"}]),
            components=sorted(comps.values(), key=lambda c: (c["type"], c["name"].lower())))
json.dump(sbom, open(os.path.join(DOCS, "SBOM.json"), "w"), ensure_ascii=False, indent=1)
# generated tables
L = ["# M4 dependency tables (generated)", "", f"Generated {D['generated']} by tools/make_register_m4.py from tools/deps_m4.json (installed metadata on this Mac).", ""]
for env in ("reelstudio", "rs_tts", "rs_asr"):
    L += [f"## Python - {USE[env]}", "", "| Package | Version | Licence |", "| --- | --- | --- |"] + [f"| {n} | {v} | {l} |" for n, v, l in sorted(rows[env], key=lambda r: r[0].lower())] + [""]
L += ["## npm - app/web (shipped: " + ", ".join(D["npm"]["shipped"]) + "; everything else is a build tool, not shipped)", "", "| Package | Version | Licence |", "| --- | --- | --- |"]
L += [f"| {p['name']} | {p['version']} | {p['license']} |" for p in D["npm"]["packages"]] + [""]
L += ["## Models", "", "| Model | Revision | Licence | Use | Evidence |", "| --- | --- | --- | --- | --- |"] + [f"| {n} | {v[:12]} | {l} | {u} | {ev} |" for n, v, l, u, ev in MODELS] + [""]
open(os.path.join(DOCS, "M4_DEPENDENCY_TABLES.md"), "w").write("\n".join(L) + "\n")
print("SBOM components:", len(comps), "| tables rows:", sum(len(r) for r in rows.values()) + len(D["npm"]["packages"]) + len(MODELS))
