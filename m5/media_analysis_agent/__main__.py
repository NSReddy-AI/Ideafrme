"""Independent JSON-line CLI. Main Studio does not import or start this CLI."""
import argparse
import asyncio
import json
import sys

from .backends import capabilities
from .controller import Agent
from .policy import AgentError, FRAME_BYTES


async def serve(args):
    agent = Agent(args.root, timeout=args.timeout)
    def output(value):
        print(json.dumps(value, ensure_ascii=False), flush=True)
    output({"ok": True, "status": agent.status(), "capabilities": capabilities()})
    try:
        while True:
            # Trusted CLI input; bounded reads on a separate host IO thread keep deadlines active.
            raw = await asyncio.to_thread(sys.stdin.buffer.readline, FRAME_BYTES + 1)
            if not raw: break
            try:
                from .protocol import decode
                command = decode(raw)
                op = command.get("op")
                allowed = {"enable": {"op", "backend"}, "submit": {"op", "value", "scenario"}}
                if op not in {"enable", "disable", "start", "stop", "cancel", "recover", "rollback", "submit", "wait", "status", "capabilities", "quit"}:
                    raise AgentError("command", "unsupported operation")
                if not set(command) <= allowed.get(op, {"op"}):
                    raise AgentError("command", "unexpected fields")
                if op == "quit": break
                if op == "status": result = agent.status()
                elif op == "capabilities": result = capabilities()
                elif op == "enable": result = await agent.enable(command.get("backend", "synthetic"))
                elif op == "submit": result = await agent.submit(command.get("value"), scenario=command.get("scenario", "echo"))
                else: result = await getattr(agent, op)()
                output({"ok": True, "result": result})
            except Exception as exc:
                output({"ok": False, "error": getattr(exc, "code", "command"), "status": agent.status()})
                if len(raw) > FRAME_BYTES or not raw.endswith(b"\n"):
                    break  # do not reinterpret the suffix of an oversized command
    finally:
        await agent.close()


def main():
    parser = argparse.ArgumentParser(description="Optional synthetic-only media analysis agent")
    parser.add_argument("--root", required=True, help="named instance beneath .runtime/media-agent")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()
    try:
        asyncio.run(serve(args))
    except (AgentError, OSError) as exc:
        print(json.dumps({"ok": False, "error": getattr(exc, "code", "storage")}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
