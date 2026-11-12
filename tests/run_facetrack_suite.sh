#!/bin/bash
# Re-runs every labelled face-tracking clip with the current code and prints one line per clip.
cd "$(dirname "$0")/.."
PY="$HOME/.venvs/reelstudio/bin/python"
for T in tests/facetrack_truth_*.json; do
  N=$(basename "$T" .json | sed 's/facetrack_truth_//')
  "$PY" tests/test_facetrack.py --truth "$T" 2>/dev/null | grep -E "ground truth|FACE TRACKING TEST" | sed "s/^/[$N] /"
done
echo "SUITE DONE"
