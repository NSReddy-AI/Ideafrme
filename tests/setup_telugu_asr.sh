#!/bin/bash
# Telugu-trained speech models (all Apache-2.0, free and unrestricted), then the comparison against your approved captions.
# Adds: ggml-te-small.bin (181 MB, whisper.cpp, Apache-2.0) and transformers + torch inside the TEST environment ~/.venvs/rs_asr only.
# The Telugu large model (vasista22/whisper-telugu-large-v2, Apache-2.0, about 3 GB) downloads on first use to ~/.cache/huggingface.
set -e
cd "$(dirname "$0")/.."
echo "== 1. whisper.cpp Telugu model (ggml-te-small, Apache-2.0)"
f="$HOME/.cache/rs_asr/ggml-te-small.bin"
[ -s "$f" ] || curl -fL -o "$f" "https://huggingface.co/ukta-app/indic-whisper-ggml/resolve/main/ggml-te-small.bin"
ls -lh "$f" | awk '{print $5, $9}'
echo "== 2. transformers + torch in the test environment (not in Reel Studio's Python)"
"$HOME/.venvs/rs_asr/bin/pip" install -q --only-binary=:all: transformers torch
"$HOME/.venvs/rs_asr/bin/pip" list 2>/dev/null | grep -iE "^(transformers|torch) "
echo "== 3. Telugu comparison (about 10-15 min, first run downloads ~3 GB)"
set +e
"$HOME/.venvs/reelstudio/bin/python" tests/test_asr.py --only=whisper.cpp-te --only=hf-telugu "$@"
