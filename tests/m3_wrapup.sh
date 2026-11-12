#!/bin/bash
# Milestone 3 wrap-up: refresh the licence register from what is really installed, then the locked-baseline checkpoint.
cd "$(dirname "$0")/.."
PY="$HOME/.venvs/reelstudio/bin/python"
echo "== 1. dependency register"; "$PY" tools/dump_deps.py && "$PY" tools/make_register.py
grep -c "" docs/DEPENDENCY_INVENTORY.md | sed 's/^/   inventory lines: /'
echo "== 2. checkpoint (locked baseline)"; bash checkpoint.sh
echo "M3 WRAP-UP DONE"
