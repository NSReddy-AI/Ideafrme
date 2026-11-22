# Local manual AI Reel Studio

No installation, package manager, account or cloud service is required for the existing manual Studio when a compatible local Python and browser are already installed. This is not a standalone runtime distribution or proof of clean offline installation.

## Start from any directory

Double-click `Start Studio.command` in Finder, or invoke its absolute path in Terminal. No browser or media backend starts automatically. Open the printed loopback URL. Stop with Ctrl+C. Default port 8766; choose `start --port 0` for a free port. Every fresh start creates a new Visual-owned session. Save before stopping.

From Terminal, with the full workspace path:

```sh
'/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/Start Studio.command' check
'/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/Start Studio.command' start --port 8766
'/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/Start Studio.command' sessions
'/Users/Nadish/projects/AI Video Editor./Codex/AI Studio/Start Studio.command' start --resume --root '<absolute Visual session root>' --port 8766
```

Python-only equivalent from any directory:

`python3 -I -B '<workspace>/tools/studio_local.py' check`

Replace `check` with `start`, `sessions`, or `kit --name <new-name>`. Resume is explicit; the launcher never guesses a project, migrates legacy sessions or repairs evidence. Existing writer-lock, font/profile, journal, quota and ownership validation remain authoritative. Listing reads ownership markers only; project access occurs through the locked service on explicit start/resume.

## Local dependency status

Manual runtime: Python standard library with POSIX fcntl, existing local HTML/CSS/ES modules and a browser supporting embedded FontFace, SVG, Canvas, PNG and Intl.Segmenter. Only the recorded local macOS/Python combination has been exercised; version floor is not blanket platform qualification. Node is used by developer tests, not by this launcher or manual UI. FFmpeg, HyperFrames, Pillow, OCR/model libraries and the Media Analysis Agent are not needed for manual startup.

Pinned Inter Bold and Noto Sans Telugu Black plus their existing OFL notices must be present. `check` verifies their byte hashes and notices and inspects bounded local source files. Browser font/shaping/origin-clean-canvas/PNG parity qualification still occurs in the running UI. A successful check cannot prove browser capability or absence of external network activity by Python/browser/OS.

## Internal source recovery kit

`Start Studio.command kit --name <fresh-name>` creates a fixed-file, hash-manifested ZIP and receipt under `.runtime/studio-ui/local-kits/<fresh-name>`. It retains first-party manual source, local browser acceptance assets needed by fixed routes, launcher instructions and the already retained pinned fonts with notices. No source/runtime is fetched. No R1, M4, production, projects, sessions, exports, models, Python executable or browser binary is bundled. Output is bounded to 200 source files, 4 MiB per source file and 32 MiB total/uncompressed and compressed. Existing directories are refused, not overwritten. Symlinks, multihardlinked files and source changes during capture are refused. ZIP bytes use fixed ordering/timestamps; repeated kits are compared in tests.

This is an internal source backup, NOT an approved release, installer, complete offline build archive or independent second-medium backup. It does not bundle Python's native dependencies, its source/build tools, a browser source/toolchain, or font build sources. Do not redistribute until first-party distribution terms and all shipped notices/dependencies are reviewed. Preserve every font copyright/OFL notice. No runtime copying, acquisition or installation is performed.

## Licensing and remaining gates

Python is PSF-2.0 with historical/bundled terms; commercial use is permitted under those terms, but a shipped runtime requires its complete notice/native dependency audit. [Official Python license](https://docs.python.org/3/license.html).

Unmodified fonts are OFL-1.1; retain copyright/license notices, do not sell fonts alone, and observe reserved-name/modified-font conditions. Existing notices travel with font bytes in the internal kit. [Official OFL text](https://openfontlicense.org/open-font-license-official-text/).

A user-provided browser's executable rights and matching source/rebuild closure are separate; Chrome is not automatically a distributable open-source runtime. No browser binary is copied. Full Python/browser/native toolchain/source closure, font rebuild inputs, clean offline provisioning/rebuild, security qualification, maintenance/advisory audit, independent backup/restore and distribution approval remain open. No M4 inventory or engine change is attempted.

## Brand & Asset foundation update

Brand Studio is now an independently stored, metadata-only feature. Python's optional sqlite3 module and its existing native SQLite are required for that feature; check reports availability/version without acquiring anything. The original studio_manual_ui is a separate dependency-light workflow. The current Visual Studio imports binding modules that require sqlite3, so the Visual launcher now refuses readiness when SQLite is missing; it does not promise an unimplemented degraded Visual startup. Brand data lives separately under .runtime/studio-ui/brand-library and is NOT included in source kits. Future kits retain the first-party library code and BRAND_ASSET_FOUNDATION_CONTRACT.md. No opaque asset is decoded or applied to projects. Brand approval covers reviewed library metadata only. SQLite matching source/native/build closure and runtime distribution review remain open; existing kits are historical and are never rewritten.

## Current product readiness reporting

The local check now reports implemented explicit project bindings, supported history envelopes1/2/3 and the separate binding format. Registered assets are still not applied. Deterministic concept planning is implemented; model-to-editor integration now has a tested Phase2G UI pilot, with human acceptance still pending. The check does not execute or qualify a model, browser, decoder or legacy renderer. Legacy Puppeteer/Sharp is still required only by the old Phase2 renderer, not current Visual startup. Existing frozen checkpoints and historical source kits are unchanged. Runtime/library roots remain package-local; this update does not add external-root support or integration.
