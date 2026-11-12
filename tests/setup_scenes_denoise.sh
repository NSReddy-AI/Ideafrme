#!/bin/bash
# Installs the two candidates into TEST places only, then runs the comparison (about 15 minutes, mostly the Telugu transcription).
#  - PySceneDetect 0.7.3 (BSD-3) into ~/.venvs/rs_asr
#  - DeepFilterNet's deep-filter program (MIT/Apache-2.0, latest GitHub release for Apple Silicon) into ~/.cache/rs_tools
set -e
cd "$(dirname "$0")/.."
echo "== 1. PySceneDetect"
"$HOME/.venvs/rs_asr/bin/pip" install -q --only-binary=:all: "scenedetect==0.7.3"
"$HOME/.venvs/rs_asr/bin/pip" list 2>/dev/null | grep -iE "^scenedetect |^opencv"
echo "== 2. DeepFilterNet (deep-filter)"
mkdir -p "$HOME/.cache/rs_tools"; B="$HOME/.cache/rs_tools/deep-filter"
if [ ! -x "$B" ]; then
  URL=$(curl -fsSL https://api.github.com/repos/Rikorose/DeepFilterNet/releases/latest | grep -o '"browser_download_url": *"[^"]*aarch64-apple-darwin[^"]*"' | grep -v '\.sha' | head -1 | sed 's/.*"\(http[^"]*\)"/\1/')
  echo "downloading $URL"; curl -fL -o "$B" "$URL"; chmod +x "$B"
fi
"$B" --version || true
echo "== 3. comparison"
set +e
"$HOME/.venvs/reelstudio/bin/python" tests/test_scenes_denoise.py
