# M5 Phase 2 — poster renderer prototype handoff

Date: 2026-11-10. Workspace: /Users/Nadish/projects/AI Video Editor./Codex/AI Studio.
Status: IMPLEMENTED; automated acceptance passed; human visual/Telugu acceptance PENDING.
Stop boundary reached. No editor, model integration, M4 integration or release follows.

## What changed

An independent renderer-neutral creative@1-to-SVG mapper with strict renderer policy,
script-specific pinned fonts, fixed baselines/explicit newlines, safe-area and brand
palette/required-layer checks. Shape, path, safe SVG/logo and PNG layers are supported.
Editable source retains layers; rendering never flattens or rewrites creative.json.

Chrome/Puppeteer exports actual draft PNGs; Sharp provides a separate comparison path.
Final-export checking requires creative approval plus a render receipt bound to source,
policy, profile, engine and renderer implementation hashes. All supplied outputs remain
unapproved DRAFTS; no human approval records were invented for the examples.

No creative_core files or creative@1 schema changes. No production/M4 modifications,
shared tool/model/venv changes, package installation, Git setup, repository clone or
model download. Only the TWO previously manifested fonts were copied; their hashes and
embedded metadata were checked, and OFL notices were retained. The rest is new source
and synthetic text/geometry. No private brand assets or production media were imported.

## Actual deliverables

- output/phase2/editorial.draft.png — 1080x1350 English editorial poster.
- output/phase2/telugu.draft.png — 1080x1920 Telugu poster.
- output/phase2/cinematic.draft.png — 2160x3840 cinematic STILL, not video.
- output/phase2/calibration.draft.png — 1080x1350 Telugu conjuncts/numerals,
  mixed-language and English samples, synthetic SVG logo and transparent PNG fixture.
- Matching .svg, .scene.json, .manifest.json and .metrics.json files.
- Matching .sharp.png comparisons and .repeat.png repeatability evidence.
- output/phase2/acceptance.json — exact final automated result and measurements.
- examples/posters/creative.json and render-policies.json — editable synthetic source.
- docs/FONT_SOURCE_MANIFEST.json and local font notices.
- poster_render/ modules, tools/prepare_phase2.py, tools/run_phase2.py,
  tests/test_render_policy.py and docs/PHASE2_RENDER_CONTRACT.md.
- FILE_MANIFEST.md lists additions; README and inventory/build-strategy notes updated.

## Exact commands and final results

Run from the workspace above. No install/build step.

Fixture preparation (only when intentionally regenerating synthetic examples; do not
run over user-edited versions):

```sh
python3 -B tools/prepare_phase2.py
```

Pure acceptance suite, with original Phase 1 tests preserved:

```sh
TMPDIR="$PWD/.runtime" TMP="$PWD/.runtime" TEMP="$PWD/.runtime" XDG_CACHE_HOME="$PWD/.runtime" PYTHONDONTWRITEBYTECODE=1 python3 -B tests/run_isolated.py > .runtime/phase2-unit-results.txt 2>&1
```

Result: exit 0; **55 tests passed, 0 failures/errors, 2.011 seconds**.
37 original tests plus 18 new renderer-policy tests. Audit log: 0 rejected external
write/process/network attempts during the pure suite. Original Phase 1 log is preserved.

Renderer acceptance (host GUI/subprocess approval was obtained; the script applies the
mandatory additional OS sandbox to each backend process and all its children):

```sh
python3 -B tools/run_phase2.py > .runtime/phase2-render-results.txt 2>&1
```

Result: exit 0; four Chrome drafts and four Sharp comparisons; four independent fresh
Chrome repeats. Exact decoded-pixel equality for all repeat pairs. No detected glyph
ink overflow or line overlap; all inspected glyph fonts are custom pinned faces.
Intentional overlong text was rejected before PNG output. Source document and Phase 1
source hashes remained unchanged across rendering. Filesystem/IP-denial probes passed.

Final smoke measurements (wall time includes process startup; not warm rendering):
- Editorial: Chrome 1.322 s; Sharp 0.203 s; sampled tree RSS 704,368 KiB.
- Telugu: Chrome 0.557 s; Sharp 0.208 s; sampled tree RSS 730,352 KiB.
- Cinematic still: Chrome 0.633 s; Sharp 0.272 s; sampled tree RSS 806,224 KiB.
- Calibration: Chrome 0.477 s; Sharp 0.202 s; sampled tree RSS 726,592 KiB.

All are below the 15 s / 3 GiB smoke limits. Sampling can miss transient peaks. This is
two fresh Chrome renders per fixture, not a warm statistical/stress benchmark. Automated
results do not certify arbitrary fonts/media, every Unicode sequence or high-layer loads.

Visual inspection found usable poster layouts and no clipped text in the final four
images. Calibration review prompted increased Telugu line spacing and explicit Latin
font runs. Native Telugu editorial/typographic approval remains the user's gate.

## Security and isolation evidence

The user approved the OS-isolated execution commands. sandbox-exec policy denies writes
outside AI Studio and IP network activity for every backend descendant. /dev/null is a
discard-device exception, and local Unix IPC is allowed for Chromium's singleton.
CDP is pipe-based; no web server, account, billing or external network is required.
Read access is not fully confined; this is not a hostile-import service.

Initial failures were handled without granting writes to shared directories: macOS
temp locations needed MAC_CHROMIUM_TMPDIR; crash paths were redirected; default writes
were denied by the OS. Chrome's own nested Seatbelt sandbox cannot initialize under the
outer policy, so --no-sandbox is used ONLY inside that mandatory OS restriction. This
loses Chromium internal per-process isolation and is documented prototype debt.
Do not run backend.mjs directly. Do not relax the OS policy to make a render pass.

The pure test runner remains unchanged and continues rejecting subprocesses. Renderer
tests use the separate OS-isolated runner. Native child-process safety is not inferred
from Python's audit hook. Logs/profiles/fontconfig caches remain inside .runtime.
No forensic whole-disk monitoring claim is made; task mutations and child writes are
constrained by the described commands and OS policy.

## Dependency independence and comparison

Observed prototype stack: Python 3.15.2, Node 26.13.0, Chrome 157.0.8103.39,
HyperFrames installation 0.9.9 containing Puppeteer Core 25.16.0 and Sharp 0.35.5.
Sharp's arm64 native bundle is @img/sharp-libvips-darwin-arm64 1.3.4 (libvips 8.18.7,
librsvg 2.63.2, Pango 1.58.2, HarfBuzz 14.5.0). Native metadata retained in metrics.
Noto font metadata: 2.005; Inter: 4.000/git-a52131595. No new dependency installed.

Temporary use of HyperFrames's private package tree is explicit, not the product's
permanent dependency plan. Chrome is not a permissive open-source browser executable.
Full source snapshots, independent dependency provisioning, offline installation,
rebuild and recovery have NOT been verified. Runtime with denied IP networking is
evidence of local rendering only. Source acquisition/vendor approval is still separate.

Sharp comparison completed, but typography visibly differs from Chrome; it is NOT
accepted as a drop-in renderer. Mean absolute channel differences and affected fractions
are preserved in manifests. A later resvg/Chromium or independently provisioned backend
must pass reviewed golden fixtures before replacement. No renderer switch occurred.

## Deliberate limits and remaining gates

- No automatic wrapping, fitting, arbitrary SVG/text asset import, gradients, filters,
  rotated-layer bounds, video, print color workflows or editor UI.
- Bounds/style/glyph and asset limits are intentionally narrow; unsupported data fails.
- Fixed Noto Black/Inter Bold fonts demonstrate a subset, not a complete typography kit.
- Brand policy currently covers synthetic palette, mandatory layers and safe margins.
- SVG text stays editable in source; output PNG is flattened. Future engine integration
  is deferred and no 4K reel capability is claimed.
- Final approval helper is implemented/tested; no production final-export UI/CLI exists.
- Prototype filesystem checks have ordinary trusted-local-process race limitations;
  no multiwriter or hostile-document security guarantee.
- Phase 2 automated acceptance is not user acceptance. Review Telugu wording/shaping,
  professional appearance, Sharp differences and the documented sandbox tradeoff.

STOP. Next action is user review, not implementation. Any interactive editor,
independent backend acquisition, M4 integration, Git setup or release requires separate
authorization. No continuation is implied by the completion of these tests.
