"""Run tests with a Python audit guard against external writes/processes/network.

Run from AI Studio: python3 -B tests/run_isolated.py
This guard supplements the host sandbox; it is not a security boundary for hostile code.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = Path("/Users/Nadish/projects/AI Video Editor./Codex/AI Studio")
if ROOT != EXPECTED or Path.cwd() != ROOT:
    raise SystemExit("Refusing tests outside the authorized workspace")
if any(p.is_symlink() for p in (EXPECTED, *EXPECTED.parents)):
    raise SystemExit("Refusing a symlinked workspace")
RUNTIME = ROOT / ".runtime"
if not RUNTIME.is_dir() or RUNTIME.is_symlink():
    raise SystemExit("A real workspace-local .runtime directory is required")
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
tempfile.tempdir = str(RUNTIME)
for key in ("TMPDIR", "TMP", "TEMP", "XDG_CACHE_HOME"):
    os.environ[key] = str(RUNTIME)

violations = []


def local(path):
    if isinstance(path, int):
        return  # File descriptors originate from guarded open/mkstemp calls.
    resolved = Path(os.fsdecode(path)).absolute().resolve()
    if not resolved.is_relative_to(ROOT):
        violations.append("external-write")
        raise PermissionError("test audit guard: write outside AI Studio")


def audit(event, args):
    if event == "open":
        path, mode, flags = args
        if (mode and any(c in mode for c in "wax+")) or flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            local(path)
    elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.chown",
                   "os.truncate", "os.utime"):
        local(args[0])
    elif event in ("os.rename", "os.link"):
        local(args[0]); local(args[1])
    elif event == "os.symlink":
        local(args[1])
    elif event.startswith("subprocess.") or event in (
            "os.system", "os.posix_spawn", "os.exec", "socket.connect", "socket.bind"):
        violations.append("process-or-network")
        raise PermissionError("test audit guard: subprocess/network forbidden")


sys.addaudithook(audit)
suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(f"Isolation audit: {len(violations)} rejected external writes/process/network attempts")
raise SystemExit(0 if result.wasSuccessful() and not violations else 1)
