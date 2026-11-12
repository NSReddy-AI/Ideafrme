# R1 implementation dependency decisions

2026-11-10. User authorized manual R1 implementation; acceptance remains separate.
Policy: ../PROJECT_ENGINEERING_POLICY.md. No packages, models, sources or services
were installed, cloned, downloaded, vendored or activated. All new application code,
fixtures and evidence are retained in AI Studio. No third-party code was copied.

## Open source first and selected reuse

Research used official Python documentation for [JSON](https://docs.python.org/3/library/json.html),
[OS file operations](https://docs.python.org/3/library/os.html),
[fcntl/flock](https://docs.python.org/3/library/fcntl.html) and
[SQLite](https://docs.python.org/3/library/sqlite3.html), plus official license sources.
Reuse installed Python standard-library JSON decoding, SHA-256, exact Decimal,
UUID, argparse, unittest and OS locks/sync/replace primitives. Installed Node provides
its standard JSON/string engine, source-aware integer reviver and crypto hashing for
independent cross-language acceptance only. No npm/PyPI dependency is introduced.

SQLite is a suitable mature local transaction engine, but adopting it here would change
the explicitly reviewed immutable-record/HEAD persistence contract. It is not used.
JSON Schema libraries would add a package dependency while still requiring custom
graph, history, rights and eligibility checks. R1 owns its closed contract validator;
it does NOT replace the underlying JSON decoder. Bounded token preflight supplements
Python's decoder; the independent JS verifier checks grammar/duplicates before using
Node JSON parsing with exact BigInt integers. Neither verifier shapes text, decodes
images, implements a canvas or replaces existing renderers/codecs.

## Rights and redistribution

Python 3.15.2 is installed; upstream [history and license](https://docs.python.org/3/license.html)
contains PSF License Version 2 and the historical license stack. Commercial use is
permitted subject to those terms. Redistributing Python requires retaining applicable
copyright/license notices; modification summaries and component-specific obligations
must be assessed if distributing a modified runtime. Do not ship only a PSF label.

Node 26.13.0 is installed (Homebrew revision 26.13.0_2). Its
[exact upstream license file](https://github.com/nodejs/node/blob/v26.13.0/LICENSE)
contains MIT terms for Node-originated code and bundled third-party terms. Commercial
use does not remove notice obligations. No Node runtime is bundled by R1; it is a
test dependency, not a dependency of manual Python authoring. R1 uses no model code,
weights, fonts or new media assets, so no model-weight license is implied by code rights.

Local runtime executables and complete locally installed notice files are identified
by path, SHA-256 and size in ../.runtime/r1/runtime-identity.json. Both upstream and
local notice files were inspected; these identities are not a complete transitive SBOM.
Python's native framework/libpython and native hash backend, Node's dynamic libraries,
Homebrew build recipes, compiler/SDK and macOS are not fully captured by hashing launchers.
Distribution still requires the project's full dependency/source/notice audit and G7.

## Offline feasibility, storage and maintenance

R1 application runtime needs installed Python and macOS local APFS only. It uses no
network calls, accounts, model services, browsers or private HyperFrames node_modules.
Tests additionally need installed Node and macOS sandbox-exec. The acceptance suite
ran with kernel networking denied, and explicit network/write-denial probes passed.
Local Python stdlib source/notice path and Node notice path are retained as inventory
references; no independent clean offline installation/build closure has been provisioned.
No runtime sources/native dependencies are newly acquired without separate approval.

Own differentiating code: immutable Style Recipe interpretation, validation, typed
manual authoring, reference graph, brand constraints, rights/review eligibility,
versioned publication and recovery. Runtime/OS primitives remain replaceable behind
their modules. No FFmpeg/HyperFrames change or future R2–R6 capability is included.

Maintenance: record exact interpreter/test-runtime hashes for each acceptance run,
rerun strict vectors and crash/fault tests before upgrades, and audit advisories for
the exact runtime/native closure before distribution. Research confirms official
maintenance sources, not an absence of vulnerabilities. Local APFS, full-sync behavior,
single-user authority, conservative obligation handling and bounded history are material
limits. A future dependency/renderer/platform change needs its own scoped evidence.

If upstream disappears, the retained R1 source/fixtures remain available; the current
installed runtimes are usable locally. Rebuilding them on a clean machine is NOT yet
proven. Follow ../OFFLINE_BUILD_STRATEGY.md rather than claiming hashes prove independence.
