"""Trusted single-thread synthetic child. No image processing or descendant launches."""
import argparse
import os
from pathlib import Path
import signal
import select
import sys

# -I startup excludes arbitrary user/site paths. Only this verified first-party package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from media_analysis_agent.policy import FRAME_BYTES, SCENARIOS
from media_analysis_agent.protocol import decode, encode, identifier, request


def guard(event, args):
    if event in {"subprocess.Popen", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec", "os.system"} or event.startswith("socket."):
        raise PermissionError("synthetic child cannot launch or network")
    if event == "open":
        _, mode, flags = args
        if (isinstance(mode, str) and any(x in mode for x in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise PermissionError("synthetic child cannot open writable files")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--startup", choices=("normal", "crash", "hang", "bad-handshake"), default="normal")
    args = parser.parse_args()
    if not identifier(args.session):
        return 2
    sys.addaudithook(guard)
    def delay(seconds):
        # Observe controller EOF even during a simulated hang, without a watchdog thread.
        if select.select([sys.stdin.buffer], [], [], seconds)[0]:
            if not os.read(0, 1):
                raise SystemExit(0)
            raise SystemExit(26)  # no pipelining while busy
    if args.startup == "crash":
        os._exit(23)
    if args.startup == "hang":
        delay(15)
        return 0
    hello = {"v": 1, "type": "ready", "session": args.session, "backend": "synthetic"}
    if args.startup == "bad-handshake":
        hello["v"] = 2
    sys.stdout.buffer.write(encode(hello)); sys.stdout.buffer.flush()
    # All inputs and outputs bounded. EOF (controller death) ends an idle child.
    while True:
        raw = sys.stdin.buffer.readline(FRAME_BYTES + 1)
        if not raw:
            return 0
        value = decode(raw)
        request(value, args.session, SCENARIOS)
        scenario = value["scenario"]
        if scenario == "crash":
            os._exit(24)
        if scenario == "ignore-term":
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if scenario in {"hang", "ignore-term"}:
            # Bounded trusted simulation, not a media worker or resource stress probe.
            delay(2)
        if scenario == "malformed":
            output = b'{"v":\n'
        elif scenario == "oversized":
            output = b"x" * (FRAME_BYTES + 1) + b"\n"
        else:
            output_value = {"v": 1, "type": "result", "session": args.session,
                            "job_id": value["job_id"], "value": value["value"]}
            if scenario == "wrong-session": output_value["session"] = "wrong"
            if scenario == "wrong-job": output_value["job_id"] = "wrong"
            if scenario == "extra-field": output_value["approved"] = True
            output = encode(output_value)
        sys.stdout.buffer.write(output); sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # Do not leak request content in diagnostic traces.
        raise SystemExit(25)
