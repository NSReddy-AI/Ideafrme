"""Explicit standalone controller and isolated package management. No Studio integration."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from media_analysis_agent.policy import AgentError, FRAME_BYTES
from media_analysis_agent import protocol
from media_analysis_agent.backends import capabilities
from media_analysis_agent_v2.controller import Agent
from media_analysis_agent_v2.packages import Deployment, build


async def serve(args):
    agent = Agent(args.root, timeout=args.timeout, job_timeout=args.job_timeout)
    def emit(value): print(json.dumps(value, ensure_ascii=False), flush=True)
    emit({"ok": True, "status": agent.status(), "capabilities": capabilities()})
    try:
        while True:
            raw = await asyncio.to_thread(sys.stdin.buffer.readline, FRAME_BYTES + 1)
            if not raw: break
            try:
                command = protocol.decode(raw); op = command.get("op")
                fields = {"enable": {"op", "backend"}, "submit": {"op", "value", "scenario"}}
                if op not in {"enable", "start", "stop", "cancel", "disable", "recover", "rollback", "status", "capabilities", "submit", "wait", "quit"}:
                    raise AgentError("command", "unknown operation")
                if not set(command) <= fields.get(op, {"op"}): raise AgentError("command", "unknown fields")
                if op == "quit": break
                if op == "status": result = agent.status()
                elif op == "capabilities": result = capabilities()
                elif op == "enable": result = await agent.enable(command.get("backend", "synthetic"))
                elif op == "submit": result = await agent.submit(command.get("value"), scenario=command.get("scenario", "echo"))
                else: result = await getattr(agent, op)()
                emit({"ok": True, "result": result})
            except Exception as exc:
                emit({"ok": False, "error": getattr(exc, "code", "command"), "status": agent.status()})
                if len(raw) > FRAME_BYTES or not raw.endswith(b"\n"): break
    finally: await agent.close()


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("serve")
    run.add_argument("--root", required=True)
    run.add_argument("--timeout", type=float, default=15)
    run.add_argument("--job-timeout", type=float, default=60)
    bundle = commands.add_parser("build"); bundle.add_argument("--output", required=True); bundle.add_argument("--version", required=True)
    install = commands.add_parser("install"); install.add_argument("--root", required=True); install.add_argument("--bundle", required=True); install.add_argument("--sha256", required=True)
    activate = commands.add_parser("activate"); activate.add_argument("--root", required=True); activate.add_argument("--version", required=True)
    rollback = commands.add_parser("rollback"); rollback.add_argument("--root", required=True)
    args = parser.parse_args()
    try:
        if args.command == "serve": asyncio.run(serve(args)); return 0
        if args.command == "build": result = build(args.output, args.version)
        elif args.command == "install": result = Deployment(args.root).install(args.bundle, expected_sha256=args.sha256)
        elif args.command == "activate": result = Deployment(args.root).activate(args.version)
        else: result = asyncio.run(Deployment(args.root).rollback())
        print(json.dumps({"ok": True, "result": result})); return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": getattr(exc, "code", "storage")})); return 2


if __name__ == "__main__": raise SystemExit(main())
