# M5 Phase 2 renderer contract

This prototype follows PROJECT_ENGINEERING_POLICY.md. No core/schema changes, installs,
engine calls or milestone integration are included. Source remains creative@1.

## Decision record

Existing research compared Fabric/Konva (editor interaction), Chrome/HTML/SVG, resvg,
Pillow and Sharp. Reuse installed Chrome/Puppeteer for the first controlled renderer;
use installed Sharp/librsvg for comparison. Do not implement font shaping, raster
decoding, PNG encoding or canvas interaction ourselves. Build only scene interpretation,
policy/layout checks, approval integration, manifests and orchestration.

Chrome is an externally installed prototype tool, not an approved redistributable
open-source browser. Puppeteer/Sharp are temporarily resolved from HyperFrames's private
package tree with user authorization; they must be independently provisioned before
product adoption. No local source/build closure was acquired or verified. resvg remains
the standalone candidate, not installed. Backend replacement must rerun these fixtures.

## Authoritative inputs and derived outputs

- examples/posters/creative.json: one synthetic creative project with four views.
- examples/posters/render-policies.json: explicit per-view render policy sidecar.
- Pinned font/media asset paths resolve beneath that project root.
- output/phase2/*.scene.json and *.svg: derived scenes, retaining layer IDs.
- *.draft.png: Chrome previews; *.sharp.png: comparison outputs; *.repeat.png:
  independent repeat-render evidence; per-output metrics and manifests are retained.
- acceptance.json: automated acceptance summary; not a human approval or release.

Element array order is paint order. Shapes use canvas-space geometry. SVG/logo/PNG
assets preserve aspect ratio with xMidYMid meet; vector paths use a nested local viewBox.
Text uses explicit newlines, pinned script-specific fonts, fixed baselines and line
spacing. Telugu cluster runs are never split into characters. Latin and punctuation
use Inter, Telugu uses Noto. Line overlap and glyph ink outside boxes fail at runtime.
No automatic wrapping/shrinking or content rewriting. Rotation is explicitly refused
until rotated-ink bounds are implemented. Video is deferred. Background can be none.

## Security and resource policy

Core validation runs first; renderer policy then requires integer output dimensions,
maximum 2160x3840 / 8,294,400 pixels, at most 150 layers, at most 10 MiB per asset,
explicit pinned font/hash/size, allowlisted paints, glyph repertoire and safe margins.
Policy requires mandatory layer IDs and an approved palette. This is a small synthetic
brand contract, not a complete Brand Studio rule system. Asset colors are approved by
asset hash; layer palette checks do not recolor a logo's internal artwork.

Imported SVG is limited to basic geometric elements/attributes. No script, events,
external resources, foreignObject, style imports, entities, declarations or asset text.
Raster input is PNG only; decoded dimensions are bounded and browser decoding must
succeed. Font inputs are local sfnt TTF/OTF and pinned by hash. Arbitrary user-supplied
fonts and hostile media are not approved for an untrusted service.

SVG is constructed from escaped text and allowlisted values, never arbitrary HTML.
Browser CSP blocks all default resources except embedded data images/fonts and generated
styles. Resource interception rejects non-data requests. CDP font inspection checks for
system fallback. All fixtures use custom pinned font faces.

## OS isolation

tools/run_phase2.py executes backend.mjs under macOS sandbox-exec with isolation.sb.
The inherited OS policy denies persistent writes outside AI Studio and denies IP network
activity. Local Unix IPC is allowed for Chromium's process singleton; CDP uses pipes,
not a network server. /dev/null writes are allowed as a discard device, not stored output.
Profiles, crash directories, fontconfig cache, temp files and logs are inside AI Studio.
macOS-specific MAC_CHROMIUM_TMPDIR is required; TMPDIR alone was insufficient.

macOS rejects Chromium's nested Seatbelt sandbox in this arrangement. Therefore the
prototype uses --no-sandbox ONLY under the mandatory inherited OS sandbox. Every child
inherits the workspace/IP restrictions, but Chromium's internal per-process isolation
is not retained. This is a documented prototype limitation, not a production security
architecture. Do not launch backend.mjs directly or remove the outer sandbox. A simple
environment sentinel is a usage guard, not a security boundary.

Before browser work, negative probes require filesystem and IP connection denial.
Early browser retries attempted default cache/temp/crash locations; the OS denied them.
No relaxation to production/shared directories was made. Native processes may still
attempt denied system paths; zero attempted writes is not claimed.

The sandbox restricts writes to the whole AI Studio workspace, not a single job, and
does not prevent a compromised process reading all user-readable files. This is a
trusted synthetic-input prototype, not a hostile-document isolation service. Stronger
read confinement and job-only write scope are required before arbitrary user imports.

## Approval and manifests

All supplied examples are DRAFTS and create no human approvals. Final export checking
requires a current creative approval AND an explicit render receipt binding document,
policy, profile, engine and renderer implementation hashes. Reviewer labels are not
authentication. A future user-facing export entry point must enforce this gate; the
low-level backend is private machinery and is not a production export command.

The prototype runner only emits draft manifests, including source/scene/PNG hashes,
render identity, policy/profile, engine, font/load/overflow QA, comparison and timing.
Original creative source and core files are checked for unintended changes. Document
hash approval does not mean external factual verification or native Telugu approval.

## Repeatability and performance

Software rendering (--disable-gpu) removes tiny GPU rounding differences encountered
in early retries. Two fresh Chrome processes per fixture produce identical decoded
pixels. Byte-identical PNG encoding across versions is not promised. No cross-engine
pixel identity is expected: Sharp's typography differs and is NOT accepted as a drop-in
replacement. Golden visuals must be reviewed before any backend switch.

Performance reports include sampled descendant-tree RSS, not just Node RSS. Sampling
can miss short-lived peaks. The test run is a small cold-process smoke benchmark, not
a 10-run warm benchmark, high-layer stress certification or full app memory analysis.
The cold prototype is below the 15-second / 3-GiB smoke limits on tested fixtures.
Final human typography/appearance approval and independent offline rebuild remain open.
