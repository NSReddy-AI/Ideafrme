"""Offline first-party bundles and isolated local deployment; no dependency installs.

Package metadata is NOT an R2 analysis format or security qualification certificate.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile

from media_analysis_agent.policy import AgentError, RUNTIME, WORKSPACE, DEPLOYMENT_BYTES

BASE = tuple("media_analysis_agent/" + x for x in
             ("__init__.py", "policy.py", "protocol.py", "storage.py", "backends.py", "worker.py", "controller.py", "__main__.py"))
REVISION = tuple("media_analysis_agent_v2/" + x for x in
                 ("__init__.py", "controller.py", "worker.py", "packages.py", "__main__.py", "README.md"))
NAMES = frozenset(BASE + REVISION + ("PYTHON-LICENSE.txt",))


def sha(raw): return hashlib.sha256(raw).hexdigest()


def safe(path):
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(RUNTIME) or path == RUNTIME:
        raise AgentError("path", "isolated absolute agent-runtime path required")
    for item in [path, *path.parents]:
        if item.is_symlink(): raise AgentError("path", "alias forbidden")
    if path.exists() and path.is_file() and path.stat().st_nlink != 1:
        raise AgentError("path", "hard link forbidden")
    return path


def version(value):
    if type(value) is not str or not re.fullmatch(r"[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}", value):
        raise AgentError("version", "bounded numeric release version required")
    return value


@contextmanager
def admission():
    fd = os.open(WORKSPACE / "media_analysis_agent/backends.py", os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc: raise AgentError("busy", "stop agent before deployment changes") from exc
        yield
    finally: os.close(fd)


def build(destination, release, *, protocol_version=1):
    destination = safe(destination)
    version(release)
    if destination.exists(): raise AgentError("exists", "never overwrite an archive")
    sources = {name: (WORKSPACE / name).read_bytes() for name in BASE + REVISION}
    original = {name: sha(raw) for name, raw in sources.items()}
    # Retain first-party originals in workspace. Local derived policy anchors package
    # runtime writes to this approved workspace, not the installed version directory.
    old = b"WORKSPACE = Path(__file__).resolve().parents[1]"
    if sources["media_analysis_agent/policy.py"].count(old) != 1:
        raise AgentError("source", "unexpected foundation policy")
    sources["media_analysis_agent/policy.py"] = sources["media_analysis_agent/policy.py"].replace(
        old, ("WORKSPACE = Path(" + repr(str(WORKSPACE)) + ")").encode())
    sources["media_analysis_agent_v2/__init__.py"] = (
        '"""Locally packaged optional synthetic agent."""\n__version__ = ' + repr(release) + '\n').encode()
    # Existing local tool notice only; not a download or a binary-runtime closure claim.
    licence = Path(sys.executable).resolve()
    candidates = [p / "LICENSE" for p in licence.parents]
    notice = next((p for p in candidates if p.is_file()), None)
    if notice is None: raise AgentError("license", "local Python notice unavailable")
    sources["PYTHON-LICENSE.txt"] = notice.read_bytes()
    manifest = {"package_schema": 1, "version": release, "protocol": protocol_version,
                "workspace": str(WORKSPACE), "qualification": None,
                "real_media_enabled": False, "python_required": "3.15",
                "python_executable_sha256": sha(Path(sys.executable).resolve().read_bytes()),
                "runtime_bundled": False, "source_inputs": original,
                "derivations": ["workspace-anchored first-party policy", "release identity"],
                "files": {n: {"sha256": sha(raw), "bytes": len(raw)} for n, raw in sources.items()}}
    sources["manifest.json"] = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(sources):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, sources[name])
    if destination.stat().st_size > DEPLOYMENT_BYTES:
        raise AgentError("limit", "deployment archive ceiling exceeded")
    return {"path": str(destination), "sha256": sha(destination.read_bytes()),
            "bytes": destination.stat().st_size, "full_runtime_closure": False}


def inspect_bundle(bundle, expected_sha256):
    bundle = safe(bundle)
    if bundle.stat().st_size > DEPLOYMENT_BYTES: raise AgentError("limit", "archive too large")
    raw = bundle.read_bytes()
    if sha(raw) != expected_sha256: raise AgentError("hash", "explicit archive pin mismatch")
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        if (len(infos) != len(NAMES) + 1 or len({x.filename for x in infos}) != len(infos)
                or {x.filename for x in infos} != NAMES | {"manifest.json"}
                or sum(x.file_size for x in infos) > 4 * 1_048_576
                or any(x.file_size > 524288 or stat.S_ISLNK(x.external_attr >> 16) for x in infos)):
            raise AgentError("package", "unexpected names, aliases or expanded bounds")
        files = {x.filename: archive.read(x) for x in infos}
    manifest = json.loads(files.pop("manifest.json"))
    if (manifest.get("package_schema") != 1 or type(manifest.get("protocol")) is not int
            or manifest["protocol"] != 1 or manifest.get("workspace") != str(WORKSPACE)
            or manifest.get("qualification") is not None or manifest.get("real_media_enabled") is not False
            or set(manifest.get("files", {})) != NAMES):
        raise AgentError("incompatible", "package protocol/scope/qualification refused")
    version(manifest["version"])
    for name, raw in files.items():
        if manifest["files"][name] != {"sha256": sha(raw), "bytes": len(raw)}:
            raise AgentError("hash", "package payload mismatch")
    return manifest, files


class Deployment:
    def __init__(self, root):
        self.root = safe(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def install(self, bundle, *, expected_sha256):
        manifest, files = inspect_bundle(bundle, expected_sha256)
        with admission():
            target = safe(self.root / "versions" / manifest["version"])
            if target.exists(): raise AgentError("exists", "immutable version already exists")
            target.mkdir(parents=True)
            for name, raw in files.items():
                path = safe(target / name)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream: stream.write(raw)
            with (target / "manifest.json").open("x") as stream:
                json.dump(manifest, stream, sort_keys=True)
        return manifest["version"]

    def verify(self, release):
        target = safe(self.root / "versions" / version(release))
        manifest = json.loads(safe(target / "manifest.json").read_bytes())
        if (manifest.get("version") != release or type(manifest.get("protocol")) is not int or manifest.get("protocol") != 1
                or manifest.get("qualification") is not None or manifest.get("real_media_enabled") is not False
                or manifest.get("workspace") != str(WORKSPACE)
                or tuple(sys.version_info[:2]) != (3, 15)
                or manifest.get("python_executable_sha256") != sha(Path(sys.executable).resolve().read_bytes())
                or set(manifest.get("files", {})) != NAMES):
            raise AgentError("incompatible", "installed version unqualified/incompatible")
        actual = {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()}
        if actual != NAMES | {"manifest.json"}: raise AgentError("package", "installed closure changed")
        for name, expected in manifest["files"].items():
            raw = safe(target / name).read_bytes()
            if expected != {"sha256": sha(raw), "bytes": len(raw)}:
                raise AgentError("hash", "installed source changed")
        return manifest

    def selection(self):
        path = safe(self.root / "selection.json")
        if not path.exists(): return {"active": None, "previous": None, "qualification": None}
        value = json.loads(path.read_bytes())
        if set(value) != {"active", "previous", "qualification"} or value["qualification"] is not None:
            raise AgentError("package", "invalid selection")
        return value

    def _publish(self, active, previous):
        data = {"active": active, "previous": previous, "qualification": None}
        pending = safe(self.root / "selection.pending")
        with pending.open("x") as stream:
            json.dump(data, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
        os.replace(pending, safe(self.root / "selection.json"))
        fd = os.open(self.root, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        return data

    def activate(self, release):
        with admission():
            self.verify(release)
            current = self.selection()
            previous = current["active"]
            if previous == release: return current  # preserve last useful rollback target
            return self._publish(release, previous)

    async def rollback(self, agent=None):
        if agent is not None:
            status = await agent.disable()
            if not status["termination_confirmed"]: raise AgentError("termination", "rollback fenced")
        with admission():
            selection = self.selection()
            if selection["previous"] is None: raise AgentError("version", "no previous release")
            self.verify(selection["previous"])
            return self._publish(selection["previous"], selection["active"])

    def command(self, instance):
        selected = self.selection()["active"]
        if selected is None: raise AgentError("version", "no explicit active release")
        self.verify(selected)
        return (sys.executable, "-I", "-B", str(self.root / "versions" / selected / "media_analysis_agent_v2/__main__.py"),
                "serve", "--root", str(safe(instance)))
