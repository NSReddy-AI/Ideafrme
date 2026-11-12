# Dependencies, licensing and cost — Phase 1

Runtime dependencies: Python standard library only (`json`, `pathlib`, `hashlib`,
`copy`, `math`, `uuid`, `os`, `tempfile`). Tests add standard-library unittest/mock.
No package installation or packaging build was used. Python 3.10+ is required by
`Path.is_relative_to`; the tested interpreter version is recorded in the handoff.

Python is PSF-licensed with third-party notices applicable to its distribution. This
workspace does not redistribute a Python interpreter. No new third-party source, model
weights, brand assets, media, fonts or binaries are vendored. The example SVG and text
are newly authored synthetic fixtures. No repository license was selected on the user's
behalf; the new package's distribution license remains a user decision before publishing.

Core operation is local and offline. No accounts, keys, billing, external services or
hosted free tiers are needed. There are no paid provider paths in this package.

Future reviewed directions (NOT dependencies of this package):
- Fabric.js: MIT, provisional; Telugu typography/editing gate still required.
- Konva: MIT fallback; do not install both without a reason.
- HTML/SVG browser poster rendering: browser/font and media licenses reviewed separately.
- Existing FFmpeg/HyperFrames: preserve, integrate only after approved M4 baseline review.
- No tldraw or Remotion dependency; no model installation or runtime calls.

Exact versions, bundled transitive licenses, notices, commercial rights and weight
licenses must be reverified before any future install/distribution. This document does
not approve previously installed components or make a blanket codec/asset rights claim.
