#!/bin/bash
# One go: record current Whisper, install the two test engines + models, then run the Telugu comparison.
# Installs only: ~/.venvs/rs_asr (faster-whisper 1.2.1, MIT), Homebrew whisper-cpp (MIT), model files in ~/.cache/rs_asr (MIT).
set -e
cd "$(dirname "$0")/.."
echo "== 1. current Whisper version"
"$HOME/Library/Application Support/pipx/venvs/openai-whisper/bin/python" -m pip list 2>/dev/null | grep -iE "whisper|torch" || echo "(could not read)"
echo "== 2. faster-whisper test environment"
[ -x "$HOME/.venvs/rs_asr/bin/python" ] || /opt/homebrew/bin/python3.12 -m venv "$HOME/.venvs/rs_asr"
"$HOME/.venvs/rs_asr/bin/pip" install -q --only-binary=:all: "faster-whisper==1.2.1"
"$HOME/.venvs/rs_asr/bin/pip" list 2>/dev/null | grep -iE "faster-whisper|ctranslate2"
echo "== 3. whisper.cpp"
command -v whisper-cli >/dev/null || brew install whisper-cpp
echo "whisper-cli: $(command -v whisper-cli)"
echo "== 4. whisper.cpp models"
mkdir -p "$HOME/.cache/rs_asr"
for m in large-v3-turbo large-v3; do
  f="$HOME/.cache/rs_asr/ggml-$m.bin"
  [ -s "$f" ] || curl -fL -o "$f" "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-$m.bin"
  ls -lh "$f" | awk '{print $5, $9}'
done
echo "== 5. Telugu comparison (10-20 min)"
set +e
"$HOME/.venvs/reelstudio/bin/python" tests/test_asr.py "$@"
