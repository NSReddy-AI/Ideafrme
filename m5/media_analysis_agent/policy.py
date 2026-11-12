"""Unchanged ceilings; these constants are NOT a hostile-worker enforcement boundary."""
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
RUNTIME = WORKSPACE / ".runtime" / "media-agent"
MEMORY_BYTES = 1_073_741_824
SCRATCH_BYTES = 134_217_728
WORKER_SECONDS = 15.0
JOB_SECONDS = 60.0
MAX_PROCESSES = 4
COMPUTE_THREADS = 1
RESULT_BYTES = 1_048_576
DEPLOYMENT_BYTES = 268_435_456
FRAME_BYTES = 8192  # Deliberately stricter synthetic transport, including newline.
VALUE_BYTES = 1024
DIAGNOSTIC_BYTES = 65_536
START_SECONDS = 2.0
TERMINATE_SECONDS = 1.0
SCENARIOS = frozenset({"echo", "hang", "crash", "malformed", "oversized",
                       "wrong-session", "wrong-job", "extra-field", "ignore-term"})


class AgentError(ValueError):
    def __init__(self, code, message):
        self.code = code
        # Diagnostics never include supplied data or media contents.
        super().__init__(message[:256])
