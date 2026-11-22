# Branch and release policy

## Branches

- `main`: approved releases only. No current production-readiness claim is made.
- `develop`: latest integrated working source after tests and review.
- `feature/<scope>`: short-lived isolated work, such as `feature/m5-latest-integration`.
- `release/<version>`: optional stabilization branch when an actual release candidate exists.
- `hotfix/<scope>`: corrections based on an approved production tag.

## Promotion rules

Work moves from a feature branch to `develop` after relevant tests, documentation and provenance are current. It moves from `develop` to `main` only after the release checklist, security review, data inventory and human product approval pass.

Every release receives an immutable version tag and release notes identifying module status, supported platforms, known limitations, migration requirements and test evidence.

## Migration rule

The existing 30 commits remain intact. The professional documentation and current working changes will be added as new commits after review. History will not be rewritten merely to make the repository look cleaner.
