# Development workstreams

`develop` contains the complete latest integrated source for all seven modules. A feature branch does not replace or hide that source; it provides a clean continuation point and module-specific backlog for unfinished work.

| Module | Integrated status on `develop` | Continuation branch |
|---|---|---|
| M1 | Foundation carried forward into the current engine | No branch required |
| M2 | Structured reel pipeline carried forward and tested | No branch required |
| M3 | Transcription and media-processing features carried forward | No branch required |
| M4 | Latest implementation included; final release gates remain | `feature/module-04-release-gates` |
| M5 | Latest source integrated; milestone remains `IN_PROGRESS` | `feature/module-05-continuation` |
| M6 | Reel/poster integration implemented | No branch required |
| M7 | Latest development implementation included; production readiness remains | `feature/module-07-production-readiness` |

## Working rule

New module work begins on its continuation branch and is merged into `develop` only when its tests, documentation and provenance are current. `main` remains reserved for a future approved production release.

Historical folders are never copied back into feature branches wholesale. When older evidence reveals a missing capability, only the compatible latest implementation and its tests are brought forward.
