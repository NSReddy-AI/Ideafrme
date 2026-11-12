#!/bin/bash
# Installs Ollama (MIT) with Homebrew, starts it as a background service (it also starts at login - stop any time with
# 'brew services stop ollama'), downloads Qwen3 14B (9.3 GB) and 8B (5.2 GB) (Apache-2.0), then runs the planner test.
set -e
cd "$(dirname "$0")/.."
echo "== 1. Ollama"; command -v ollama >/dev/null || brew install ollama
brew services start ollama >/dev/null; sleep 3; ollama --version
echo "== 2. Qwen3 models"; ollama pull qwen3:14b; ollama pull qwen3:8b; ollama list
echo "== 3. planner test"; set +e
"$HOME/.venvs/reelstudio/bin/python" engine/rs.py providers
"$HOME/.venvs/reelstudio/bin/python" tests/test_planner.py
