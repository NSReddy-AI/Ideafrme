#!/bin/bash
# Double-click to start Reel Studio (development copy). Local only - nothing is published. Close this window to stop it.
cd "$(dirname "$0")"
PORT=${RS_PORT:-8765}; URL="http://127.0.0.1:$PORT"
if curl -s -o /dev/null "$URL/api/catalog"; then echo "Reel Studio is already running: $URL"; open "$URL"; exit 0; fi
if ! curl -s -o /dev/null http://127.0.0.1:11434/api/tags; then echo "Note: Ollama is not running - start it before planning a speaker reel."; fi
( for i in $(seq 1 30); do curl -s -o /dev/null "$URL/api/catalog" && { open "$URL"; break; }; sleep 1; done ) &
echo "Starting Reel Studio at $URL  (close this window or press Ctrl+C to stop)"
exec "$HOME/.venvs/reelstudio/bin/python" app/server.py
