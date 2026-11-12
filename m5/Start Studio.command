#!/bin/zsh
# Local only; no installation, browser auto-launch, fetching or shell configuration.
set -eu
studio_dir="${0:A:h}"
exec python3 -I -B "$studio_dir/tools/studio_local.py" "$@"
