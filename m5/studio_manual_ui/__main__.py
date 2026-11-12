"""Explicit local startup; no automatic browser, analysis or renderer launch."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from .service import RUNTIME, Studio, UIError
from .server import Server


def main():
    parser = argparse.ArgumentParser(description="Isolated manual Creative Studio")
    parser.add_argument("--root", type=Path, help="fresh named root beneath .runtime/studio-ui")
    parser.add_argument("--resume", action="store_true", help="explicitly reopen an existing UI-owned session")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.resume and args.root is None: parser.error("--resume requires --root")
    root = args.root or RUNTIME / (datetime.now(timezone.utc).strftime("session-%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    studio = server = None
    try:
        studio = Studio(root, resume=args.resume)
        server = Server(studio, args.port)
        print(json.dumps({"url": server.origin, "runtime_root": str(root), "analysis": "disabled", "mode": "manual"}), flush=True)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt: pass
    except Exception as exc:
        print(json.dumps({"error": getattr(exc, "code", "startup"), "detail": "Local startup failed; existing data was not repaired or replaced."}), flush=True)
        return 2
    finally:
        if server: server.server_close()
        if studio: studio.close()
    return 0


if __name__ == "__main__": raise SystemExit(main())
