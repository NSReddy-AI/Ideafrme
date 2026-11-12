#!/bin/bash
# Milestone 2 baseline: re-render reel_002 with the current engine (dev copy only).
set -e
cd "$(dirname "$0")"
PY="$HOME/.venvs/reelstudio/bin/python"
P=2026-11-03_reel_002_development
echo "Rendering reel_002 baseline..."; START=$(date +%s)
"$PY" engine/rs.py render "$P"
echo "Render time: $(( $(date +%s) - START )) s"
"$PY" engine/qa.py "exports/${P}_jagan_for_andhra_instagram.mp4"
ls -l "exports/${P}_jagan_for_andhra_instagram.mp4"
echo "BASELINE DONE"
