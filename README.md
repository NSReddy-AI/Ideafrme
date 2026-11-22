# IDEAFRAME migration preservation

This branch stores recovery artifacts captured before the professional repository migration on 21 November 2026. It is separate from application source and must remain private.

## Contents

- `IDEAFRAME_M6_dev-history.bundle`: complete original 30-commit M6/M7 Git history.
- `IDEAFRAME_M6_dev-uncommitted.tgz`: five modified files and four untracked entries, including both untracked projects and their generated builds.
- `M5-frozen-checkpoint.tgz`: frozen Module 5 checkpoint.
- `M5-live-source.tgz`: later live Module 5 source, excluding runtime and generated output.
- `M5-live-runtime-studio-ui.tgz.part-aa` and `.part-ab`: complete compressed Module 5 Studio runtime/session data split for GitHub file-size compatibility.

## Restore the runtime archive

Run from the `archives` directory:

```sh
cat M5-live-runtime-studio-ui.tgz.part-aa M5-live-runtime-studio-ui.tgz.part-ab > M5-live-runtime-studio-ui.tgz
shasum -a 256 M5-live-runtime-studio-ui.tgz
```

The reconstructed archive must have SHA-256:

`dcc3f068bcd1ce5b1566950cedeae89756d7b6ef5ec81014901e778d4a1810f7`

## Restore the Git history

Verify and clone the bundle into a new directory. Never restore over production or an existing workspace.

```sh
git bundle verify archives/IDEAFRAME_M6_dev-history.bundle
git clone archives/IDEAFRAME_M6_dev-history.bundle IDEAFRAME_M6_dev_restored
```

Check every archive against `SHA256SUMS.txt` before extraction. Extract into a new empty directory and inspect the contents before deciding whether to copy anything into an active workspace.
