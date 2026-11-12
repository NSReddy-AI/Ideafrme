# Visual Poster Studio — preview selection, alignment and navigation

Date: 2026-11-11, America/Toronto. Authorized manual-editor batch completed; not full product acceptance or release. R1, M4, production and Gate A remain protected. No real-media/R2–R6 execution, engine integration or dependency acquisition occurred.

## Implemented

- Direct preview-to-layer selection using the existing source geometry and reverse paint order. Rectangle/ellipse tests respect shape geometry; text uses its declared editable layout box. Alt-click cycles overlapping hits; the layer list remains available for covered layers. Pointer coordinates are mapped from the current image rectangle into the fixed source view, so zoom/scroll positioning does not mutate source coordinates.
- A clipped, preview-only selection outline, plus optional margin guides. Neither is inserted into the SVG or PNG. Selection does not create history/revisions. Valid unchanged scenes are reused when only selection changes.
- Six alignment controls: left, horizontal centre, right, top, vertical centre and bottom. Configurable integer canvas margin; unsupported/out-of-range margins and layers that do not fit the requested axis are refused. Centres round to integer coordinates. Alignment commits the existing move transaction and supports ordinary undo/redo/save/reopen.
- Clearer project/session/export navigation: short project IDs distinguish duplicate names; refresh workspace updates the project inventory; expandable session details show the owned runtime root and a shell-quoted resume command. Retained export receipts show state, revision, hashes and local directory. Partial and invalid receipts remain retained and are labelled for review. Read-only navigation never repairs or migrates files.

## Exact files

Modified:

```text
visual_poster_studio/service.py
visual_poster_studio/server.py
visual_poster_studio/app.js
visual_poster_studio/index.html
visual_poster_studio/styles.css
tools/run_visual_resume_tests.py
```

Created:

```text
visual_poster_studio/layout.mjs
visual_poster_tests/test_layout.mjs
visual_poster_tests/test_layout_navigation.py
visual_poster_tests/layout_browser.mjs
docs/VISUAL_LAYOUT_BATCH_HANDOFF.md
```

All paths/ancestors were checked before writing. A 161-file in-scope SHA-256 baseline was captured in `.runtime/studio-ui/visual-layout-batch-20261111-01/baseline.json`. Completion metadata records exact before/after and new-file hashes and test associations. R1 source/tests and R1/G1 records were excluded from content reads. Earlier evidence was not overwritten.

## Compatibility and reuse

No core, creative@1 content/history contract, renderer, pinned font, approval, export manifest, journal or ownership-marker change. Old projects continue using the same fields and existing move operations; this batch introduces no new persisted version boundary. History v2 is still required only by the previously implemented reorder capability. Margin/zoom/selection are transient UI state, not persisted brand rules or export policy.

The application reuses native browser image/pointer events, DOM focus, the existing SVG scene and core transactions. `layout.mjs` implements application-specific hit mapping, clipping and alignment arithmetic; it is not a canvas interaction framework, shaper or renderer. No third-party library, package or mandatory service was added. Dragging, resizing, rotation and multi-selection are not included.

The new GET `/api/navigation` has no path arguments and reuses exact Host/Origin validation. It audits owned exports and returns bounded local inventory. Fixed module routes serve only the new local helper/test files. Text is inserted through textContent/value; arbitrary paths, remote assets, downloads outside the owned runtime and automatic filesystem repair are not added. Resume commands use POSIX single-quote escaping, including quote/command-substitution test cases.

## Targeted tests — no repeated full regression

```sh
env -u NODE_COMPILE_CACHE node visual_poster_tests/test_layout.mjs
env -u NODE_COMPILE_CACHE node --check visual_poster_studio/app.js
env -u NODE_COMPILE_CACHE node --check visual_poster_tests/layout_browser.mjs
python3 -I -B tools/run_visual_resume_tests.py --track layout --run-id visual-layout-targeted-001
python3 -I -B tools/run_visual_resume_tests.py --track layout --run-id visual-layout-targeted-002
```

Initial targeted run: 9 Python tests passed, zero failures/errors/rejected operations. Pure JS layout policy: 29 assertions passed. Tests cover zoom coordinates, overlap/ellipse hit testing, clipping, alignment/margin refusal, shell quoting, source immutability, move/undo restoring exact SVG, fixed module routes and Host/Origin/path-argument rejection.

Final targeted run adds invalid receipt-revision coverage: ten tests, with actual results authoritative in `.runtime/studio-ui/visual-layout-targeted-002/results.json` and `tests.txt`. No full 126-test suite was rerun. The runner retains fresh-root write restrictions and loopback-only socket checks. New target selection does not execute legacy suites or child servers. Final JS command exits/output and source hashes are retained with completion metadata.

## Single meaningful browser fixture

One fresh project in `.runtime/studio-ui/visual-layout-browser-20261111-01/` verifies overlapping text/rectangle/ellipse selection, alignment, history and export navigation. Initial server on 8771, followed by explicit resume of the same saved root on 8772. No second sample project was created. Both processes were stopped with SIGINT, exit 0.

The `#layout-checks` test-only harness passed all ten checks:

1. Exact alignment coordinates.
2. Single-step alignment undo.
3. Preview selects the topmost ellipse.
4. Alt-click cycles to the covered rectangle.
5. Selection does not increment revision.
6. Selection outline appears.
7. Guides do not change rendered source.
8. Export receipt navigation populates.
9. Session root/resume navigation is available.
10. Save/reopen retains deterministic preview identity.

Evidence: `browser-evidence-caf9f170106374b6.json`. The final-source normal UI was then tested using real pointer clicks at 25% zoom, not only synthetic event dispatch: centre click selected the ellipse, Alt-click selected the rectangle, and revision remained 8. Session/export details were opened and the same project was exported again. `browser-proof.json` records the final UI, receipt and console inspection; `layout-workspace.jpg` is the screenshot. Final browser console errors were empty.

Both exports retain the same identities despite changed selection, guides, zoom and a full process restart:

```text
SVG 4ccb7df68c12dae740abd9fc8046b6a781e27d965e89537f40c8b819b5d671f3
PNG 72cb57a1741bd5f0e8f32de7898c5ae52843d9195a3b911041b11a8673f87fb9
```

The final export is `exports/draft-e541cd8a1d2bfb70/` inside that browser root. Its browser QA reports exact decoded RGBA parity. Earlier output was not replaced. New navigation metadata validation marks an incomplete revision receipt for review instead of failing the entire inventory. No known failing targeted test remains.

## Remaining work and boundaries

No genuine blocker remains for this batch. Text hit testing deliberately selects layout boxes rather than individual glyph outlines. Resize/rotate, drag manipulation, multi-layer alignment/distribution and persistent editor preferences remain future work; geometry changes unsupported by current core contracts must not be smuggled into existing operations.

Native Telugu IME/candidate-window and visual approval, full accessibility/VoiceOver, independent offline distribution/build closure, and separately qualified real image/OCR/video analysis remain product completion requirements. This batch does not claim those gates passed, or authorize M4/production integration.

Startup remains `python3 -B -m visual_poster_studio --port 8766`, with explicit `--resume --root <Visual-owned-root> --port 0` for saved sessions. Session details now expose the exact safe resume command. No legacy-session adoption or silent migration was introduced.
