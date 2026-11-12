"""Replaceable interface; no real decoder imports or executable selection by callers."""
from dataclasses import dataclass
from pathlib import Path
import sys

from .policy import AgentError


@dataclass(frozen=True)
class MediaRequest:
    """Future handle-only ingress interface. No handle is read by this foundation."""
    capability: str  # image / ocr-eng / ocr-tel / video
    input_handle: int
    source_sha256: str
    profile_sha256: str


@dataclass(frozen=True)
class Backend:
    name: str
    capability: str
    qualified: bool
    reason: str

    def command(self, session, startup):
        if self.name != "synthetic" or not self.qualified:
            raise AgentError("unqualified", "real-media execution boundary not qualified")
        return (sys.executable, "-I", "-B", str(Path(__file__).with_name("worker.py")),
                "--session", session, "--startup", startup)


BACKENDS = (
    Backend("synthetic", "trusted-synthetic-lifecycle", True, "not a hostile-media boundary"),
    Backend("image", "image-poster-analysis", False, "Gate A blocked; artifact/quality gates open"),
    Backend("ocr-eng", "english-ocr", False, "Gate A blocked; engine/data unqualified"),
    Backend("ocr-tel", "telugu-ocr", False, "Gate A blocked; engine/data unqualified"),
    Backend("video", "reel-video-analysis", False, "Gate A blocked; temporal contract/profile unqualified"),
)


def select(name):
    for backend in BACKENDS:
        if backend.name == name:
            if not backend.qualified:
                raise AgentError("unqualified", backend.reason)
            return backend
    raise AgentError("capability", "unknown backend")


def capabilities():
    return tuple({"name": x.name, "capability": x.capability,
                  "available": x.qualified, "real_media": False if x.name == "synthetic" else True,
                  "reason": x.reason} for x in BACKENDS)
