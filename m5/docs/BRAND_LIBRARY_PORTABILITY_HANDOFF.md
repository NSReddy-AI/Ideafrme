# Brand library backup, restore and portability

Implemented separate brand-library portability. No creative@1/history-v3/R1 schema, brand-record schema or SQLite user-version changes. No project integration, real-media processing, package installation or release.

## Functionality and integrity

Brand Studio now offers explicit Create local backup package, local package selection, Verify and preview restore, acknowledgement and Restore previewed package. Backup returns an in-workspace path, package SHA-256, manifest SHA-256, byte count and declared omissions. No automatic browser download or external writes. Existing library records/rights/versions are captured from a locked consistent SQLite snapshot; logical entries use deterministic canonical JSON, fixed ZIP order/timestamps/modes and SHA-256 manifests under studio-brand-backup@1/version 1.

Uses only ZIP_STORED. No archive extraction, compression/decompression, media decoding, SQLite-database import, pickle, script execution or raw-asset rendering. Before ZipFile construction, EOCD entry count/directory/size limits are checked. Strict paths, local-header bounds/flags, member types/methods, duplicate names, complete manifest coverage, canonical record schemas/hashes, blob hashes/lengths, linear brand/rights ancestry and approval bindings are validated. Unsupported version, missing/unlisted members, corruption, traversal, symlinks, compressed archives, cycles/forks and bad references refuse. Bounds: 72 MiB package, 1101 members, 256 KiB central directory, 1 MiB manifest, 1000 records, 100 assets and 32 MiB blob aggregate; no decompression bomb path.

Asset bytes copied only when every registered identity sharing those bytes has a current grant for redistribute/library_metadata. A permissive alias cannot launder an unknown/denied alias. Otherwise bytes are omitted explicitly while metadata/rights/history remain intact. Such a package is not a complete standalone byte recovery: preview blocks restore unless matching verified bytes already exist locally. Missing/corrupt source BLOBs indicate store-integrity failure and refuse backup rather than claim a complete recovery copy. Rights are local-actor assertions, not independent legal verification.

Preview shows brand names/IDs, version/asset/rights counts, duplicates/new entries, lineage conflicts, missing dependencies/omissions, proposed heads, rights quarantines, package identity and current destination fingerprint. Preview of an absent store creates nothing. Restore requires acknowledgement and both preview identities; validates again under the target lock before insertion. Exact duplicates are explicit no-ops. New immutable rows insert without overwrite; pointers advance only on a common linear history. Newer local heads/revocations remain. Divergent histories block the whole restore, including a source revocation diverging from an already-restored quarantine; no UUID sorting or implicit fork merge.

Incoming new/advancing grants append unknown-clearance quarantine events. Original grant/approval/revocation record bytes remain intact; imported hash identity never activates permission. Existing exact local grants remain as existing state, not restored/recreated grants. Expiry is evaluated by existing eligibility logic; old approval bindings stay stale after quarantine/regrant. Asset/project creative_use_enabled remains false. Re-approval requires explicit subsequent local rights and brand revision workflows.

Restore uses one existing SQLite transaction for all new records/blobs/pointers/quarantines. Any precommit failure rolls back. Existing logical records remain exact; SQLite database physical page bytes are not required to be identical after rollback. If restoring into an absent destination, an interrupted transaction can leave an initialized empty database, not partial imported records. Retry is explicit. Existing size/count quotas include quarantine overhead; full-capacity imports can therefore be blocked. No deletion/eviction, force overwrite, automatic repair or silent migration.

Backups are SHA-named files in a separate sibling <library-name>-backups directory. Exclusive creation, byte readback and directory synchronization; exact duplicate backup reused without overwrite. 20-package/256 MiB retention cap refuses additional writes. Unexpected directory entries or damaged prior publication require explicit diagnosis, never deletion. Partial publication remains as evidence. Same-disk retention is not protection against disk loss, and physical power-loss durability is not verified.

## Source and licensing decisions

Reused existing Python zipfile/io/json/hashlib and SQLite; no new dependencies acquired. ZIP_STORED avoids adding a decompressor to this format. SQLite supplies the transaction rather than a new recovery engine. Research before implementation: https://docs.python.org/3/library/zipfile.html ; https://www.sqlite.org/lang_transaction.html . Existing Python PSF/incorporated-software and SQLite public-domain/build-tool caveats remain as documented in THIRD_PARTY_INVENTORY.md. New first-party code and portability contract are retained by future internal source kits; no Python/SQLite runtime/source acquisition or offline rebuild proof. No model/codec licence is introduced. Backups are unencrypted and unsigned: checksums detect inconsistency relative to the manifest, not publisher authenticity or maliciously rewritten but internally consistent provenance. Quarantine and explicit review prevent package claims from becoming operational rights.

## Exact changes

Modified five:
- visual_poster_studio/server.py — fixed backup/preview/restore routes, existing Host/Origin/CSRF gates, bounded package body.
- visual_poster_studio/index.html — explicit portability controls and read-only preview/results.
- visual_poster_studio/app.js — optional request timeout argument; existing calls retain 5 seconds, package calls use 30 seconds.
- visual_poster_studio/brands.mjs — bounded package file selection, preview binding, acknowledgement, stale-plan restore and backup results.
- tools/studio_local.py — retains portability contract in future internal source kits.

Created five:
- visual_poster_studio/brand_portability.py
- visual_poster_tests/test_brand_portability.py
- tools/run_brand_portability_tests.py
- docs/BRAND_LIBRARY_PORTABILITY_CONTRACT.md
- docs/BRAND_LIBRARY_PORTABILITY_HANDOFF.md

Core, accepted manual UI, renderer/fonts, history, R1 storage, M4, production and Gate A unchanged. Existing brand foundation record format and transaction code untouched. All package/test/library/evidence writes are in fresh isolated runtime roots. Default brand-library remains uninitialized; synthetic fixtures do not seed the user's real library.

## Targeted test evidence

Commands from workspace:
- python3 -I -B tools/run_brand_portability_tests.py --run-id visual-brand-portability-targeted-001: exit 1, 19 tests, one failure. Test wrongly expected an incoming revocation and independently appended restore quarantine (same parent, different descendants) to merge. Implementation correctly refused a fork. Corrected the existing-byte fixture and added an explicit divergent-rights refusal test. Failed evidence retained.
- visual-brand-portability-targeted-002: exit 0, 23 tests.
- visual-brand-portability-targeted-003: exit 0, final 25 tests, zero failures/errors/source drift/rejected Python writes/processes. Covers deterministic backup/manifests, preview without initialization, exact historic/BLOB retention, grant quarantine, duplicate no-op, local newer revocation preservation, expired/unknown rights omissions, verified local-byte dependency resolution, stale preview, divergent brand/rights history, acknowledgement/hash refusal, tampered/missing/unsupported/traversal/truncated/compressed/duplicate/symlink archive rejection, exclusive backup reuse/readback, rollback and quota failure.

Failure checks distinguish: injected OSError(ENOSPC) before commit; generic injected interruption after inserts; and actual SQLite SQLITE_FULL induced by lowering only the fixture connection's max_page_count (64 KiB synthetic opaque fixture), not filling the disk. All preserved original logical records. An absent destination remained empty and an explicit retry succeeded. No SIGKILL, OS-crash, destructive exhaustion or physical power-loss test in this batch.

- node --check visual_poster_studio/brands.mjs; node --input-type=module --check < visual_poster_studio/app.js: exit 0.
- python3 -I -B .runtime/studio-ui/visual-brand-portability-browser-01/start_server.py: loopback test server, isolated source/target libraries, stopped with Ctrl+C, exit 0. Script/fixture creation commands are retained in this chat and runtime evidence; no default library writes.

Browser used the native file-chooser flow to select the generated 4,942-byte source package. Eight observed checks (not an automated browser suite): local package selection, preview counts/hashes, acknowledgement requirement, restore commit, original record bytes preserved, opaque bytes identical, permission quarantine/stale approval, explicit backup with legal-copy omission. Source had four immutable records; destination retained all four exactly plus one new quarantine record. All 36 opaque bytes matched. UI showed approved historical brand as review stale/blocked and creative use disabled.

Source package SHA-256: b45cc88b601dd717f75e43bb59baa7321626fce1a2d4501009cd1ec615daabf5.
Source manifest SHA-256: e898ca90b1b0feda877e8e4b4928b19a71118cb8183b7a9f12594e70ab1c290a.
Post-restore backup SHA-256: 58f77b5a9c743768728bce3b592080da47fcf53cda77901b5df6831b3c8ff0a6 (5,446 bytes); its blob omission is expected because the restored grant was quarantined.

Evidence: .runtime/studio-ui/visual-brand-portability-browser-01/source-backup-evidence.json, browser-integrity-evidence.json, restore-backup-proof.png and http-evidence.json. Live HTTP missing Origin/CSRF backup request refused 403; malformed package preview refused 400; library state unchanged. Large maximum-size browser uploads were not stress tested; bounds were checked in implementation and small meaningful fixtures. Python audit hooks are not kernel enforcement of all native SQLite filesystem writes. No hostile-worker/Gate A qualification claim.

Before-source bytes/hashes and final protected-baseline verification: .runtime/studio-ui/visual-brand-portability-baseline-01/baseline.json, before/, completion.json. Prior evidence untouched.

## Remaining limitations / next product step

Unsigned, unencrypted packages; trusted local actor, local clock and explicit permission assertions remain. No automatic cross-device revocation discovery, conflict merge, authenticity proof, directory-wide backup browser, cloud storage, external-medium copy or runtime install. Divergent branches and quota/omission cases require explicit resolution; restored grants require local review. Recovery is application-transaction tested, not power-loss qualified. No full M5 or production-readiness claim.

Next unblocked development: a unified recovery dashboard and local backup catalogue combining the existing project journals, library packages and internal source-kit inventory, with explicit safe actions and no protected schema changes. Brand-to-project application and actual image/OCR/video analysis remain separately authorized/qualified. Offline runtime/build/licensing closure remains open; no R2–R6, M4 integration or production release is authorized.
