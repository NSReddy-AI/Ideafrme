# IDEAFRAME

IDEAFRAME is a local-first creative production application for branded reels and posters. It combines the Reel Studio video pipeline with the Creative Studio poster workflow in one React, TypeScript and FastAPI application.

This repository is an integration workspace. Its current source contains the latest M6/M7 implementation preserved from the original 30-commit development history. Production release approval has not been granted.

## Current capabilities

- Create and manage poster and reel projects.
- Apply versioned brands, platform rules and visual styles.
- Transcribe Telugu and English media with local tools.
- Plan reels, review exact content and enforce explicit approvals.
- Build, render and quality-check multi-platform reels.
- Create, edit, review and export poster concepts.
- Track poster, reel and combined tasks through durable local records.
- Run offline with local providers where their individual capability gates pass.

## Repository map

| Path | Responsibility |
|---|---|
| `app/` | FastAPI server, integration services and React web application |
| `engine/` | Reel planning, transcription, editing, rendering and QA engine |
| `m5/` | Frozen Creative Studio integration baseline used by M6/M7 |
| `brands/` | Content-brand profiles and approved repository assets |
| `platforms/` | Platform dimensions, safe areas and output rules |
| `styles/` | Reel pacing and visual-style settings |
| `tests/` | Unit, integration, acceptance and regression evidence |
| `docs/` | Architecture, module, provenance, security and release records |
| `projects/` | Local project records and selected reviewed fixtures; builds are ignored |

Start with [the project documentation](docs/project/README.md). The seven modules are milestones in one evolving product; they are documented separately without duplicating the active source tree.

## Development status

The current integration build passes the frontend build, all eight web logic test files, 49 M6/M7 integration tests and 11 official M5 sprint checks. The latest Module 5 source is integrated locally, while its overall milestone status remains `IN_PROGRESS` and its incomplete capabilities remain labelled.

No branch should be described as production-ready until the release checklist and human approval are complete. `develop` is the intended integration branch and `main` is reserved for approved releases.
