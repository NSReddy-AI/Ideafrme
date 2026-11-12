#!/bin/bash
# Double-click to start the IDEAFRAME M6 development copy. Local only - nothing is published. Close this window to stop it.
# Port 8775, not production's 8765, so this copy can never open (or be mistaken for) production.
cd "$(dirname "$0")"
export RS_PORT=${RS_PORT:-8775}; PORT=$RS_PORT; URL="http://127.0.0.1:$PORT"
if curl -s -o /dev/null "$URL/api/catalog"; then echo "IDEAFRAME (M6 dev) is already running: $URL"; open "$URL"; exit 0; fi
if curl -s -o /dev/null http://127.0.0.1:8765/api/catalog; then echo "Note: production Reel Studio is running on 8765. Do not run heavy jobs in both at once."; fi
if ! curl -s -o /dev/null http://127.0.0.1:11434/api/tags; then echo "Note: Ollama is not running - start it before planning a speaker reel."; fi
( for i in $(seq 1 30); do curl -s -o /dev/null "$URL/api/catalog" && { open "$URL"; break; }; sleep 1; done ) &
echo "Starting IDEAFRAME (M6 dev) at $URL  (close this window or press Ctrl+C to stop)"
exec "$HOME/.venvs/reelstudio/bin/python" app/server.py
