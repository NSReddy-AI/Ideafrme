# Architecture

IDEAFRAME is a local-first modular monolith. One local FastAPI process owns application state and serves one React application. Heavy media operations run through isolated jobs and external local tools.

## Application boundaries

- `app/server.py` installs the HTTP routes and serves the built web application.
- `app/web/` provides the IDEAFRAME interface and workflow state.
- `app/creative.py` is the controlled boundary to the Creative Studio library under `m5/`.
- `app/engine_jobs.py` isolates reel rendering jobs from the source engine and project baseline.
- `app/tasks.py` stores durable local workflow records and mirrors actual engine progress.
- `engine/` owns transcription, planning, editing, rendering, packaging and QA.
- `app/brand_bridge.py` connects versioned creative brands to engine-brand exports without silently changing either source.
- `app/approved_content.py` and `app/content_links.py` preserve the relationship between approved reel content and poster/reel derivatives.

## Data boundaries

Source code, reviewed configuration, tests and small approved fixtures belong in Git. Project sessions, brand libraries, job records, model files, caches and generated renders are local data by default. Selected evidence can enter Git only when its purpose, rights and size are recorded.

## Safety boundaries

- Human content and rights approval cannot be granted by code or migration tooling.
- Reel Studio production and all historical folders remain read-only during migration.
- The reel_002 baseline is a regression reference and is not edited as ordinary project data.
- Local provider availability is reported separately from installation, configuration and qualification.
- The application remains functional without paid or network providers for its supported offline paths.
