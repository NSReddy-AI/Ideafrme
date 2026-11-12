# Independent manual Studio UI — implementation handoff

Date: 2026-11-10 (America/Toronto). Authority: user's explicit 11-file manual-UI
implementation and bounded-test authorization. **Manual source-editing foundation
implemented; browser-level visual/IME acceptance remains pending.** This is not a
complete Studio release, a production integration or a qualified media-analysis backend.

Workspace: `/Users/Nadish/projects/AI Video Editor./Codex/AI Studio`.

## Exact authored files and protected baseline

Every target was verified unused and its ancestors checked for symlinks before writing.
Only these 11 new source/document/test files were authored:

1. `studio_manual_ui/__init__.py`
2. `studio_manual_ui/__main__.py`
3. `studio_manual_ui/service.py`
4. `studio_manual_ui/server.py`
5. `studio_manual_ui/index.html`
6. `studio_manual_ui/app.js`
7. `studio_manual_ui/styles.css`
8. `studio_ui_tests/test_service.py`
9. `studio_ui_tests/test_http.py`
10. `tools/run_studio_ui_tests.py`
11. `docs/STUDIO_UI_HANDOFF.md`

Generated projects, saved/previous JSON, locks, session markers and evidence exist only
under NEW `.runtime/studio-ui/manual-ui-20261110-01` through `-04` and
`.runtime/studio-ui/startup-20261110-01`. Existing evidence was not overwritten.
143 pre-existing non-runtime files stayed hash-identical, including creative_core,
accepted R1, both independent agent revisions, frozen R2 documents and prior handoffs.
The final completion manifest rechecks the original preimplementation baseline as well.
No M4/production workspace was accessed, no shared configuration or environment changed,
and no dependency, model, font, decoder or OCR component was installed or acquired.

## Start and use

From the workspace above:

```sh
python3 -B -m studio_manual_ui --port 8765
```

After startup open **http://127.0.0.1:8765**. The service prints its actual URL and newly
created runtime root. It does not open a browser automatically. Use `--port 0` to request
a free local port and read the printed URL. There is no bind-host option: only 127.0.0.1.
The host environment must permit loopback sockets. No server is left running by this task.

An explicit root is optional, must be unused, and must be a named directory beneath
`.runtime/studio-ui/`. New startup never overwrites an existing root. To resume a saved
session after stopping the service, use its exact previously printed absolute root:

```text
python3 -B -m studio_manual_ui --resume --root <absolute-UI-owned-session-root> --port 8765
```

Create a named English/Telugu project; choose a layer; edit text with Apply text; apply
position, font size or fill changes; add text/rectangle/ellipse layers; undo/redo committed
operations; Save project. Save also commits unapplied text. Reopen saved version explicitly
discards unsaved changes after the browser asks for confirmation. Project switching keeps
working drafts in the current service's memory. Saved projects remain available on resume.
Stop the service with Ctrl-C. **Unsaved drafts are memory-only and are lost on service
exit; save before stopping.** No automatic recovery, migration or approval is performed.

## Supported behavior and compatibility

- Existing creative@1 source and public creative_core factory/validation/apply/undo/redo/
  save APIs are reused unchanged. Files remain ordinary accepted creative documents.
- Manual editable text and rectangle/ellipse geometry, integer X/Y position, text size
  1–512 and six-digit hexadecimal fill. One 1080x1350 source view, no rendered preview.
- Independent text bindings: new projects initialize 32 supported editorial content
  records (16 per language), with one initially visible. Add text binds an unused record
  through the existing add-element operation. It does not insert content through an
  invented edit operation. The initial pool is part of newly created creative@1 content,
  not a hidden sidecar scene or a change to accepted code/contracts.
- Maximum 64 active layers, 100 project directories/session, 8 MiB stored UI documents,
  and existing 200-transaction core history. The document limit includes core.save's
  terminal newline. Capacity/remaining text slots are visible. Unsupported/exhausted
  operations fail without silently extending the schema or discarding history.
- Unicode strings received by the service are preserved without trimming, normalization,
  translation, spelling correction or rewriting. Tests distinguish composed/decomposed
  English and preserve Telugu marks, whitespace and newlines. Browser IME/paste behavior
  and shaping are not established by those service tests.
- Every mutation checks the expected in-memory revision. Save additionally checks the
  previously read file digest; external saved changes are not overwritten. Edits and
  undo/redo clear current approvals through the accepted core. The UI has no approval API.
- Saved original/previous files retain the accepted core's persistence behavior; no
  stronger filesystem, power-loss, concurrency or backup guarantee is claimed.

The UI returns a projection for its inspector; the complete authoritative creative@1
document, including history and inactive content slots, is saved in each owned project's
`creative.json`. It cannot import arbitrary legacy/user-supplied project locations.
Schema-valid features outside this manual subset are refused rather than silently lost.

## Analysis and security

Analysis shows OFF, independent availability/state and bounded safe error codes. Default
status is ABSENT / agent-not-connected. Test-only cached-status providers exercise disabled,
faulted, incompatible and reported-ready states; none can enable controls or media. No live
agent polling, process launch, decoder import or R1/brand-store integration is included.
All analysis enable/start/stop controls remain operationally disabled. No automatic retry.

UI requests are loopback-only. Exact Host checks prevent alternate-host/rebinding access;
Origin is validated when supplied and required for POST; mutations also require a per-server
CSRF token. Duplicate Host/Origin/token headers, unknown routes, arbitrary filesystem paths,
unsupported methods, encoded bodies, malformed/duplicate-key JSON and requests over 64 KiB
are refused. No CORS permission is emitted. Static files use a fixed route allowlist.
CSP restricts scripts/styles/connections to self and denies images, fonts, frames, objects,
base changes and native form submission. No CDN, remote asset, external fetch or package.
Frontend uses DOM textContent/textarea values, never innerHTML/eval for project content.

Runtime paths reject symlinks, special files and hard-linked JSON. All current/historical
manual states are checked for forbidden media/asset references before core validation could
open asset files. The session has a single OS writer lock and serialized request operations.
This is a trusted-local-user manual tool, **not** a hostile-native-code sandbox or authenticated
multi-user service. Concurrent malicious local filesystem races are not fully defended.
A local process that can access loopback/session data is not excluded by browser CSRF controls.

The proposed revised resource-accounting contract was NOT adopted. No Gate A limit,
agent security profile, frozen R2 format or accepted milestone was modified. Actual uploaded
image/poster analysis, English/Telugu OCR and reel/video reference analysis remain mandatory
eventual capabilities, disabled until separately qualified and authorized.

## Commands, exits and evidence

New UI suites only; no legacy project suite or package manager was run:

```sh
python3 -I -B tools/run_studio_ui_tests.py --run-id manual-ui-20261110-01
python3 -I -B tools/run_studio_ui_tests.py --run-id manual-ui-20261110-02
python3 -I -B tools/run_studio_ui_tests.py --run-id manual-ui-20261110-03
python3 -I -B tools/run_studio_ui_tests.py --run-id manual-ui-20261110-04
env -u NODE_COMPILE_CACHE node --check studio_manual_ui/app.js
```

- Run 01 exited 1: 27 tests, zero assertion failures, nine HTTP setup errors because the
  host sandbox denied local socket binding. Service tests completed. No unexpected writes,
  rejected audit attempts or protected changes occurred. This failed evidence is preserved.
- Runs 02/03, with permission for the already-authorized loopback tests, exited 0:
  27 tests each, no failures/errors. Write/network/process audit checks remained active.
- Final run 04 exited 0: **28 tests, zero failures/errors**, after adding the saved-file
  terminal-newline size-boundary regression. Runner elapsed 1.047 seconds; unittest 0.444
  seconds as recorded in its transcript. All 143 baseline hashes unchanged; zero rejected
  audit attempts. Before final report, run files totaled 152,344 bytes.
- JavaScript syntax check ran twice, both exit 0, using existing Node only as a check tool.
  It does not constitute browser behavior or visual verification.

[Final results/source and baseline hashes](../.runtime/studio-ui/manual-ui-20261110-04/results.json),
[per-test transcript](../.runtime/studio-ui/manual-ui-20261110-04/tests.txt),
[preserved sandbox-denied run](../.runtime/studio-ui/manual-ui-20261110-01/results.json).

The runner restricts writes to its fresh root, permits only loopback IPv4 test traffic,
denies process launches and uses a 60-second suite alarm. Request/socket waits are bounded.
Intentional symlink/hard-link negative fixtures are wholly inside the new test root;
they are not unexpected aliases into protected data. This audit is scoped evidence, not
whole-disk forensic monitoring or a replacement for Gate A.

The standalone CLI startup smoke test exited 0. Its actual absolute command and local
requests are recorded in [startup-smoke.json](../.runtime/studio-ui/startup-20261110-01/startup-smoke.json).
It started at http://127.0.0.1:62465, created/saved/reopened synthetic Telugu/English/NFD
text over HTTP, confirmed analysis controls disabled, and stopped normally with SIGINT.
That temporary URL is now inactive. [stderr](../.runtime/studio-ui/startup-20261110-01/stderr.txt)
was empty. The normal reusable startup command/URL is given above.

## Remaining acceptance and rollback

No browser was launched. Remaining browser-level checks: initial/layout/mobile appearance,
keyboard navigation and focus, full create/add/edit/undo/redo/save/reopen DOM interaction,
unsaved-change confirmations, English/Telugu IME/paste/caret behavior, native typography
and accessibility. Service/HTTP tests and JS syntax do not establish those results or
professional poster rendering. Existing browser tooling could perform these checks later
without new runtime dependencies, within a separately controlled verification session.

Unsupported: image/video/font imports; real analysis/OCR; poster or reel rendering; raster,
SVG or video exports; approval creation; R1 bridging; brand assets/rules editing; real
production projects; canvas dragging/resizing/rotation; rich typography or automatic fitting.
The browser shows source-editing controls and layer text, not a render-engine preview.

Rollback: stop this standalone service and do not invoke the new UI package. Retain owned
saved projects, prior revisions and test evidence. No deletion, schema migration, agent
rollback, M4 change or production swap is required. Python/macOS/browser provision and
full independent offline distribution/licensing closure remain open product gates.

**STOP: authorized minimal manual UI and bounded verification completed. No full Studio
completion, browser acceptance, resource-contract revision or real-media activation claimed.**
