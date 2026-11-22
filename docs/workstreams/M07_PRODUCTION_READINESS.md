# M7 production-readiness continuation

## Current base

The latest M7 implementation is included on `develop`: professional navigation and editor flows, brand-rights gating, measured poster QA, durable tasks, capability reporting, combined poster-to-reel work, accessibility improvements and reliability fixes.

## Remaining work

- Perform screen-reader testing, full physical-keyboard navigation and native Telugu IME validation.
- Run complete real-project regression across poster-only, reel-only and combined workflows.
- Validate restart and recovery behavior for long-running engine jobs and retained task records.
- Define task and local-data retention policies with backup and restoration tests.
- Complete security review of local HTTP boundaries, imported archives and file-system confinement.
- Recheck Windows/portable-launcher behavior against the final dependency set.
- Produce a clean installation test on a machine without development caches.
- Close production branding, approved logo and owner-controlled content/rights decisions.

## Release boundary

Passing engineering checks produces a release candidate. Promotion to `main` requires a versioned release record and explicit product approval; development commits are never silently treated as production.
