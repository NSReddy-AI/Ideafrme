# Brand & Asset Studio foundation handoff

Implemented the bounded separate metadata library, not creative integration or media processing. Contract was defined before persistence in BRAND_ASSET_FOUNDATION_CONTRACT.md. Existing creative@1, history v3, accepted R1 and project stores are unchanged.

## Functionality

Multiple independently identified brands with names, hex colors, English/Telugu typography preferences, notes and distinct mandatory-rule/preference/inspiration declarations. Each Save creates a new immutable draft record, guarded by expected head hash. Approval requires explicit acknowledgement and reviewer label; creates an immutable approved revision with asset/rights bindings. An approved head is read-only in UI; Create revision produces a new draft. Historical versions remain separately viewable by hash. Rule declarations are metadata, not machine-enforced creative rules. Colors are approved only in approved records, not merely because entered in a draft.

Local file registration retains up to 8 MiB of explicitly selected opaque bytes. Declared logo/image/font/template kind, immutable UUID/hash/length and provenance (owner, source, license claim) are retained. Byte deduplication does not merge asset identities or rights. No decoding, thumbnailing, SVG parsing, font loading, template execution, direct asset download route or creative application. Preview is read-only metadata JSON. Claimed media type/license/authority is not independently verified. Unknown initial clearance allows registration but not rights-sensitive use or profile approval involving that asset.

Rights events carry explicit status, authority/evidence, permitted scopes/destinations and UTC expiry; missing/unknown/denied/expired/out-of-scope clearance blocks affected review. Decisions append with optimistic current-event hash, never rewrite historical records. Library approval requires internal_preview/library_metadata scope only; it never implies poster/reel/export permission. Any rights event hash change makes an older approval binding stale; revocation then regrant cannot resurrect it. New revision/review is needed. Creative use remains false on every response regardless of library approval. No operational bridge to R1 or protected projects.

Home and Projects now navigate to Brand & Assets. Form fields survive Home navigation and asset refresh. New/switch brand actions refuse discarding dirty fields without Save or explicit Discard. Approval refuses unsubmitted edits. Session switching is blocked for unsubmitted brand fields, and navigation is paused during a library operation. Editor keyboard shortcuts do not mutate a hidden project from Brand Studio; Ctrl/Cmd+S inside Brand Studio submits the brand draft. Unsubmitted fields remain browser memory and are not autosaved; native page-leave warning is installed. Cross-tab coordination is optimistic hash refusal, not collaborative editing.

## Persistence and security

Separate default root: .runtime/studio-ui/brand-library, SQLite application_id 0x42524131, user_version 1. Read of an absent library creates nothing. First explicit mutation initializes it. No migration, automatic repair/deletion, project pointer or marker change. Unknown versions, malformed/corrupt hashes and opaque byte mismatches refuse reads. SQLite rollback transactions, synchronous FULL, DELETE journal and memory-only temp storage; separate nonblocking OS flock. Records/blobs have no-update/no-delete triggers; heads are mutable pointers. Limits: 100 assets, 1000 records, 32 MiB distinct BLOB bytes, 64 MiB main DB cap. Journal/filesystem overhead is additional; these are metadata-library bounds, NOT Gate A resource qualification.

Reuses existing canonical-safe path checks and loopback Host/Origin/CSRF validation. Store roots are controlled by the application; HTTP requests cannot supply them. Symlink/hardlink/special-file aliases are refused. Native SQLite writes are configured to this database directory; Python audit-hook evidence is not kernel enforcement of all native writes. The trusted-local-actor model remains; filesystem administrators can bypass application triggers. Reviewer/authority labels are not authenticated identities and local OS time supplies expiry checks. No security-boundary qualification or physical power-loss test is claimed. Full interrupted initialization/disk-full/OS-crash fault coverage for this new store remains future acceptance work; failed transactions do not auto-repair data. An incomplete initialization remains blocked for explicit diagnosis.

## Open-source and licensing decision

Official sources researched before substantive implementation:
- https://docs.python.org/3/library/sqlite3.html — installed standard-library binding, optional module with native SQLite dependency.
- https://www.sqlite.org/copyright.html — SQLite deliverable code/documentation public domain and commercially reusable; upstream build/configure scripts can have separate terms.
- https://www.sqlite.org/atomiccommit.html — mature transactional commit model and its filesystem/hardware assumptions.

Reused installed Python 3.15.2 / SQLite 3.54.1. No new packages, binaries, sources, fonts or models downloaded/installed. Rejected adding a package/ORM/another file journal: existing SQLite already supplies the needed transactional storage. New code/contract are first-party local source and included by future internal source kits. Existing sqlite3/SQLite runtime source, native transitive/toolchain archive and full advisory/licensing distribution closure are NOT retained/verified. Python/PSF/incorporated-software obligations remain. No model-weight licence applies because no model is adopted. THIRD_PARTY_INVENTORY.md and the local doctor now record this dependency; absence of sqlite3 blocks Brand Studio with an unavailable response while the manual editor remains independent. No redistribution approval or clean offline rebuild claim.

## Exact files

Modified eight:
- visual_poster_studio/server.py — fixed library routes and bounded opaque-byte upload body.
- visual_poster_studio/index.html — separate Brand/Asset forms and navigation.
- visual_poster_studio/home.mjs — separate view, editor draft preservation, brand dirty-state session guard.
- visual_poster_studio/app.js — brand UI adapter and isolated shortcut/operation state.
- visual_poster_studio/styles.css — basic form/read-only preview layout.
- tools/studio_local.py — optional SQLite feature inventory and retention of the brand contract in future source kits.
- THIRD_PARTY_INVENTORY.md — appended SQLite adoption/closure record.
- docs/LOCAL_STUDIO_START.md — appended feature/dependency/retention update.

Created six:
- visual_poster_studio/brands.py
- visual_poster_studio/brands.mjs
- docs/BRAND_ASSET_FOUNDATION_CONTRACT.md
- docs/BRAND_ASSET_FOUNDATION_HANDOFF.md
- visual_poster_tests/test_brands.py
- tools/run_brand_tests.py

No core, renderer, pinned fonts, history or accepted manual UI files changed. R1 source/storage not read/modified; M4/production not accessed; Gate A unchanged. Default brand library remains uninitialized after testing, so no synthetic data is seeded into the user's real library.

## Commands and evidence

- python3 -I -B -c 'import sqlite3,sys; print(sys.version.split()[0]); print(sqlite3.sqlite_version)' — exit 0: 3.15.2 / 3.54.1.
- python3 -I -B tools/run_brand_tests.py --run-id visual-brand-targeted-001: exit 0, 16 tests.
- Same runner visual-brand-targeted-002: exit 0, 16 tests.
- Final run visual-brand-targeted-003: exit 0, 19 tests. Covers multiple brands/reopening, canonical identity, immutable versions/approvals, stale brand/rights writes, unknown/expired/insufficient rights, revocation/regrant without resurrection, all four opaque declared kinds/dedup, invalid base64/paths/rights, missing references, acknowledgement, DB immutability/unknown versions/record/BLOB corruption, transaction rollback, writer contention and symlink refusal. No source drift, rejected Python writes or child processes.
- python3 -I -B tools/run_home_tests.py --run-id visual-brand-home-regression-001: exit 0, 12 tests. No source drift/rejected writes. Final targeted Python total 31; previous smaller development runs are not added to that total.
- node --check visual_poster_studio/brands.mjs; node --input-type=module --check < visual_poster_studio/app.js: exit 0.
- python3 -I -B tools/studio_local.py check: exit 0; existing manual dependencies qualified as locally present; optional SQLite correctly recorded. Evidence local-check.json under visual-brand-baseline-01.
- python3 -I -B .runtime/studio-ui/visual-brand-browser-01/start_server.py: test-only loopback server with explicit isolated library root; stopped with Ctrl+C, exit 0. Test script is retained as runtime evidence, not a production entry point.

One synthetic opaque byte fixture registered through local API; it is intentionally not an image and never decoded. Missing Origin/CSRF refused with 403. Registration evidence records exact asset/record/rights hashes. Browser exercised Home/Projects navigation, read-only asset metadata, Unicode brand fields, unknown-rights approval refusal, scoped grant, immutable approved fields, explicit revision, dirty-field retention across Home, save, second brand, reopening and historical approved preview: 13 manually observed browser checks, not an automated browser suite. Evidence .runtime/studio-ui/visual-brand-browser-01/browser-evidence.json, registration-evidence.json and brand-library-proof.png. OS file chooser itself was not exercised; upload API and opaque retention were tested. Browser checks preceded final dirty-field session/shortcut guards; those guards were syntax checked without repeating the whole UI sequence. No poster/sample generation or full regression suite run.

Before source snapshots/hashes and final preservation report: .runtime/studio-ui/visual-brand-baseline-01/baseline.json, before/ and completion.json. All test databases, journals and BLOBs remain in fresh bounded runtime fixtures. No existing acceptance evidence overwritten.

## Remaining limitations and next batch

Foundation complete within metadata-only scope; not accepted as production-ready. No asset thumbnails/rendering, font application, template interpretation, project association, automatic brand compliance, asset export, authenticated rights proof or adverse-rule operational propagation. Direct creative integration remains separately authorized and must respect existing manual_subset (assets empty/brand null) and protected schema/history boundaries.

Next unblocked product batch: explicit library backup/restore and portability with integrity checks, followed by consolidated library/Studio acceptance. That should preserve all immutable approved records and never overwrite existing stores. Any Brand-to-project application requires a narrowly scoped compatibility proposal/approval first. Qualified real image/poster, English/Telugu OCR and reel/video analysis remain mandatory eventual capabilities under separate Gate A authorization. No R2–R6, M4 integration or release is authorized here.
