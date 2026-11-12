"""Small trusted-local configuration/diagnostics store restricted to agent runtime.

Reject aliases; this is not a race-proof sandbox against a concurrent hostile local user.
"""
import fcntl
import json
import os
from pathlib import Path

from .policy import AgentError, RUNTIME, WORKSPACE, DIAGNOSTIC_BYTES


class Files:
    def __init__(self, root):
        self.root = Path(root)
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise AgentError("path", "absolute normalized runtime root required")
        try:
            relative = self.root.relative_to(RUNTIME)
        except ValueError as exc:
            raise AgentError("path", "outside agent runtime") from exc
        if not relative.parts:
            raise AgentError("path", "named instance root required")
        for path in [self.root, *self.root.parents]:
            if path.is_symlink():
                raise AgentError("path", "symlink forbidden")
        # Never resolve a user path into a protected project.
        if self.root.resolve() != self.root:
            raise AgentError("path", "noncanonical runtime root")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.fd = None
        try:
            self.fd = self._open("controller.lock", os.O_CREAT | os.O_RDWR)
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception as exc:
            self.close()
            raise AgentError("lock", "instance already owned or lock unavailable") from exc
        self.dropped = 0

    def _path(self, name):
        if name not in {"controller.lock", "config.json", "config.pending", "diagnostics.jsonl"}:
            raise AgentError("path", "unknown agent file")
        path = self.root / name
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_nlink != 1)):
            raise AgentError("path", "unsafe file alias")
        return path

    def _open(self, name, flags):
        fd = os.open(self._path(name), flags | os.O_NOFOLLOW, 0o600)
        if os.fstat(fd).st_nlink != 1:
            os.close(fd)
            raise AgentError("path", "hard-linked file")
        return fd

    def read_config(self):
        path = self._path("config.json")
        if not path.exists():
            return {"enabled": False, "backend": "synthetic"}
        fd = self._open("config.json", os.O_RDONLY)
        with os.fdopen(fd, "rb") as stream:
            raw = stream.read(4097)
        def pairs(items):
            value = {}
            for k, v in items:
                if k in value:
                    raise AgentError("config", "duplicate configuration key")
                value[k] = v
            return value
        try:
            value = json.loads(raw, object_pairs_hook=pairs)
            if len(raw) > 4096 or set(value) != {"enabled", "backend"} or type(value["enabled"]) is not bool or value["backend"] != "synthetic":
                raise ValueError()
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            raise AgentError("config", "invalid configuration; no auto repair") from exc
        return value

    def config(self, enabled):
        data = json.dumps({"enabled": enabled, "backend": "synthetic"}, sort_keys=True).encode()
        fd = self._open("config.pending", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        self._path("config.json")
        os.replace(self._path("config.pending"), self._path("config.json"))
        directory = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def diagnostic(self, event, code, state):
        # Closed caller-supplied codes only; never log input strings or raw exceptions.
        data = (json.dumps({"event": event[:32], "code": code[:32], "state": state[:32]}) + "\n").encode()
        path = self._path("diagnostics.jsonl")
        if (path.stat().st_size if path.exists() else 0) + len(data) > DIAGNOSTIC_BYTES:
            self.dropped += 1
            return
        fd = self._open("diagnostics.jsonl", os.O_CREAT | os.O_APPEND | os.O_WRONLY)
        with os.fdopen(fd, "ab") as stream:
            stream.write(data)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
