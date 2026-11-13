#!/bin/bash
# Double-click to start the IDEAFRAME M6 development copy. Local only - nothing is published. Close this window to stop it.
# Port 8775, not production's 8765, so this copy can never open (or be mistaken for) production.
cd "$(dirname "$0")"
export RS_PORT=${RS_PORT:-8775}; PORT=$RS_PORT; URL="http://127.0.0.1:$PORT"; HERE="$(pwd -P)"
PY="$HOME/.venvs/reelstudio/bin/python"
if [ ! -x "$PY" ]; then echo "IDEAFRAME cannot start: its Python environment is missing ($PY). See SETUP.md."; read -r -p "Press Return to close." _; exit 1; fi
if [ ! -f app/web/dist/index.html ]; then echo "IDEAFRAME cannot start: the screens are not built (app/web/dist). In app/web run: npm run build"; read -r -p "Press Return to close." _; exit 1; fi

if curl -s -o /dev/null "$URL/api/catalog"; then
  # Something already answers on this port. Reuse it only if it is this copy and it is running the code that is on disk.
  PID=$(lsof -nP -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null | head -1)
  CWD=$(lsof -a -p "$PID" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)
  INFO=$(curl -s "$URL/api/version")
  STALE=$("$PY" -c 'import json,sys
try: v=json.loads(sys.argv[1])
except Exception: print("old"); raise SystemExit
print("busy" if v.get("jobs_active") else "stale" if v.get("stale") else "ok")' "$INFO" 2>/dev/null)
  if [ "$CWD" != "$HERE" ]; then echo "Port $PORT is in use by another program or another copy ($CWD). IDEAFRAME (M6 dev) was not started."; read -r -p "Press Return to close." _; exit 1; fi
  if [ "$STALE" = "ok" ]; then echo "IDEAFRAME (M6 dev) is already running: $URL"; open "$URL"; exit 0; fi
  if [ "$STALE" = "busy" ]; then echo "IDEAFRAME (M6 dev) is running a job. It was left alone; restart it after the job to load the latest update."; open "$URL"; exit 0; fi
  ACTIVE=$(curl -s "$URL/api/jobs" | "$PY" -c 'import json,sys
try: print(sum(1 for j in json.load(sys.stdin) if j.get("status") in ("queued","running")))
except Exception: print(0)')
  if [ "$ACTIVE" != "0" ]; then echo "IDEAFRAME (M6 dev) is running a job. It was left alone; restart it after the job to load the latest update."; open "$URL"; exit 0; fi
  echo "An older IDEAFRAME (M6 dev) was running (started before the latest update). Restarting it..."
  kill "$PID" 2>/dev/null; for i in $(seq 1 20); do curl -s -o /dev/null "$URL/api/catalog" || break; sleep 0.5; done
  if curl -s -o /dev/null "$URL/api/catalog"; then echo "The older copy did not stop. Close its Terminal window, then start again."; read -r -p "Press Return to close." _; exit 1; fi
fi
if curl -s -o /dev/null http://127.0.0.1:8765/api/catalog; then echo "Note: production Reel Studio is running on 8765. Do not run heavy jobs in both at once."; fi
if ! curl -s -o /dev/null http://127.0.0.1:11434/api/tags; then echo "Note: Ollama is not running - start it before planning a speaker reel."; fi
( for i in $(seq 1 30); do curl -s -o /dev/null "$URL/api/catalog" && { open "$URL"; break; }; sleep 1; done ) &
echo "Starting IDEAFRAME (M6 dev) at $URL  (close this window or press Ctrl+C to stop)"
exec "$PY" app/server.py
