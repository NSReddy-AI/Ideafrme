"""Finite synthetic replay/compatibility cases, never real reference media."""
import argparse
import os
from pathlib import Path
import select
import signal
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from media_analysis_agent.worker import guard
from media_analysis_agent import protocol
from media_analysis_agent.policy import FRAME_BYTES, SCENARIOS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--startup", required=True)
    args = parser.parse_args()
    sys.addaudithook(guard)
    def delay(seconds):
        if select.select([sys.stdin.buffer], [], [], seconds)[0]:
            if not os.read(0, 1): raise SystemExit(0)
            raise SystemExit(26)
    def send(value):
        sys.stdout.buffer.write(protocol.encode(value)); sys.stdout.buffer.flush()
    if args.startup == "crash": os._exit(23)
    if args.startup == "hang": delay(15); return 0
    hello = {"v": 2 if args.startup == "bad-handshake" else 1,
             "type": "ready", "session": args.session, "backend": "synthetic"}
    send(hello)
    if args.startup == "unsolicited": send(hello)
    previous = None
    while True:
        raw = sys.stdin.buffer.readline(FRAME_BYTES + 1)
        if not raw: return 0
        request = protocol.decode(raw)
        protocol.request(request, args.session, SCENARIOS | {"duplicate", "stale", "old-session", "late", "unsupported"})
        mode = request["scenario"]
        if mode == "crash": os._exit(24)
        if mode == "ignore-term": signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if mode in {"hang", "ignore-term", "late"}: delay(2)
        result = {"v": 1, "type": "result", "session": args.session,
                  "job_id": request["job_id"], "value": request["value"]}
        if mode == "wrong-session": result["session"] = "wrong-session"
        if mode == "old-session": result["session"] = request["value"]
        if mode == "wrong-job": result["job_id"] = "wrong"
        if mode == "extra-field": result["approved"] = True
        if mode == "unsupported": result["v"] = 2
        if mode == "stale" and previous is not None: result = previous
        if mode == "malformed":
            sys.stdout.buffer.write(b'{"v":\n'); sys.stdout.buffer.flush()
        elif mode == "oversized":
            sys.stdout.buffer.write(b"x" * (FRAME_BYTES + 1) + b"\n"); sys.stdout.buffer.flush()
        else:
            send(result)
            if mode == "duplicate": send(result)
        previous = result


if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception: raise SystemExit(25)
