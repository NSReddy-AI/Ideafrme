"""Synthetic-only completion revision. Reuses the unchanged first foundation."""
import asyncio
import fcntl
import os
from pathlib import Path
import sys
import uuid

from media_analysis_agent.controller import Agent as Foundation
from media_analysis_agent.policy import AgentError, FRAME_BYTES, JOB_SECONDS, RESULT_BYTES, WORKSPACE
from media_analysis_agent import protocol
from . import __version__


class Agent(Foundation):
    def __init__(self, root, *, timeout=15.0, startup_timeout=2.0,
                 job_timeout=JOB_SECONDS, wire_limit=16_384, session_limit=RESULT_BYTES):
        for value, maximum in ((job_timeout, JOB_SECONDS), (wire_limit, 16_384), (session_limit, RESULT_BYTES)):
            if type(value) not in (int, float) or not 0 < value <= maximum:
                raise AgentError("limit", "policy may only be tightened")
        if type(wire_limit) is not int or type(session_limit) is not int:
            raise AgentError("limit", "integer byte budget required")
        super().__init__(root, timeout=timeout, startup_timeout=startup_timeout)
        self.job_timeout, self.wire_limit, self.session_limit = float(job_timeout), wire_limit, session_limit
        self._reader_task = self._pending = self._fault_task = self._expiry_task = None
        self._timer = None
        self._job_started = None
        self._job_session = None
        self._tx = self._rx = self._session_bytes = 0
        self._pending_id = None
        self._completed = set()
        self.revoked_session = None

    def _status(self):
        value = super()._status()
        value.update(agent_version=__version__, protocol_version=1,
                     session=self._session, revoked_session=self.revoked_session,
                     wire_tx=self._tx, wire_rx=self._rx, session_bytes=self._session_bytes,
                     job_timeout=self.job_timeout)
        return value

    def _revoke(self):
        if self._session is not None:
            self.revoked_session, self._session = self._session, None

    def _charge(self, count, *, transmit=False):
        self._session_bytes += count
        if self._job and self._session is not None and self._job_session == self._session:
            if transmit: self._tx += count
            else: self._rx += count
            if self._tx + self._rx > self.wire_limit:
                raise AgentError("communication-limit", "aggregate job communication exceeded")
        if self._session_bytes > self.session_limit:
            raise AgentError("communication-limit", "aggregate session communication exceeded")

    def _pending_response(self, job_id=None):
        if self._pending is not None and not self._pending.done():
            raise AgentError("state", "only one outstanding response")
        self._pending = asyncio.get_running_loop().create_future()
        self._pending_id = job_id
        return self._pending

    async def _frame(self, proc):
        # Used by startup only; the continuous receiver owns all stdout reads.
        future = self._pending_response()
        self._reader_task = asyncio.create_task(self._receive(proc))
        return await future

    async def _receive(self, proc):
        try:
            while True:
                raw = await proc.stdout.readline()
                if not raw: raise AgentError("crash", "backend EOF")
                self._charge(len(raw))
                value = protocol.decode(raw)
                if self._pending is None or self._pending.done():
                    raise AgentError("replay", "unsolicited or duplicate response")
                if self._pending_id is None:
                    protocol.ready(value, self._session)
                else:
                    protocol.result(value, self._session, self._pending_id)
                    if value["job_id"] in self._completed:
                        raise AgentError("replay", "completed request replay")
                future, self._pending = self._pending, None
                future.set_result(value)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            code = getattr(exc, "code", "protocol")
            if self._pending is not None and not self._pending.done():
                self._pending.set_exception(AgentError(code, "backend response rejected"))
            await self._fail(code)

    async def _monitor(self, proc):
        await super()._monitor(proc)
        if self.state == "FAULTED": self._revoke()

    async def start(self, *, startup="normal"):
        async with self._control_lock:
            self._check_open()
            if not self.enabled or self.state != "STOPPED":
                raise AgentError("state", "explicit enabled/stopped state required")
            if startup not in {"normal", "crash", "hang", "bad-handshake", "unsolicited"}:
                raise AgentError("capability", "unsupported startup")
            # Same stable coordinator as the first installed foundation, read only.
            fd = os.open(WORKSPACE / "media_analysis_agent/backends.py", os.O_RDONLY | os.O_NOFOLLOW)
            try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                os.close(fd)
                raise AgentError("busy", "backend admission occupied") from exc
            self._admission_fd = fd
            self.state, self.last_error = "STARTING", None
            self._session = str(uuid.uuid4())
            self._completed.clear()
            self._session_bytes = self._tx = self._rx = 0
            self._pending = self._fault_task = self._expiry_task = None
            env = {"HOME": str(self.files.root), "TMPDIR": str(self.files.root),
                   "XDG_CACHE_HOME": str(self.files.root), "OMP_NUM_THREADS": "1"}
            worker = Path(__file__).with_name("worker.py")
            try:
                async def launch_and_handshake():
                    launch = asyncio.create_task(asyncio.create_subprocess_exec(
                        sys.executable, "-I", "-B", str(worker), "--session", self._session,
                        "--startup", startup, cwd=self.files.root, env=env,
                        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT, limit=FRAME_BYTES,
                        pass_fds=(fd,), close_fds=True))
                    try: self._process = await asyncio.shield(launch)
                    except asyncio.CancelledError:
                        self._process = await launch
                        self._termination_confirmed = False
                        raise
                    self._termination_confirmed = False
                    self._monitor_task = asyncio.create_task(self._monitor(self._process))
                    return await self._frame(self._process)
                hello = await asyncio.wait_for(launch_and_handshake(), self.startup_timeout)
                protocol.ready(hello, self._session)
                if self.state == "FAULTED" or self._process.returncode is not None:
                    raise AgentError("crash", "startup failed")
                self.state = "READY"
                self._log("start-v2")
                return self.status()
            except asyncio.CancelledError:
                await self._fail("startup-canceled")
                raise
            except Exception as exc:
                await self._fail("timeout" if isinstance(exc, TimeoutError) else getattr(exc, "code", "launch"))
                raise AgentError(self.last_error, "startup failed") from exc

    async def _terminate(self):
        self._revoke()
        reader = self._reader_task
        if reader is not None and reader is not asyncio.current_task() and not reader.done():
            reader.cancel()
            await asyncio.gather(reader, return_exceptions=True)
        if self._pending is not None and not self._pending.done(): self._pending.cancel()
        result = await super()._terminate()
        if self._timer is not None:
            self._timer.cancel(); self._timer = None
        return result

    async def _fail(self, code):
        if self._fault_task is None or self._fault_task.done():
            self._revoke()
            if self._job:
                self._job.update(status="failed", result=None, error=code)
            self._fault_task = asyncio.create_task(super()._fail(code))
        await asyncio.shield(self._fault_task)

    async def submit(self, value, *, scenario="echo"):
        # Additional modes exist only in this trusted synthetic revision.
        if self.state != "READY": raise AgentError("state", "ready backend required")
        if scenario not in {"duplicate", "stale", "old-session", "late", "unsupported"}:
            mapped = scenario
        else: mapped = "echo"
        if len(self._completed) >= 128:
            raise AgentError("communication-limit", "explicit new session required")
        started = asyncio.get_running_loop().time()
        self._requested_scenario = scenario
        result = await super().submit(value, scenario=mapped)
        self._job_session = self._session
        self._job_started, self._tx, self._rx = started, 0, 0
        self._timer = asyncio.get_running_loop().call_at(
            started + self.job_timeout, self._schedule_expiry)
        return result

    def _schedule_expiry(self):
        self._expiry_task = asyncio.create_task(self._expire())

    async def _expire(self):
        if self._job and self._job["status"] == "running":
            self._job.update(status="failed", result=None, error="job-deadline")
            if self._job_task and not self._job_task.done():
                self._job_task.cancel()
                await asyncio.gather(self._job_task, return_exceptions=True)
            await self._fail("job-deadline")

    async def _after_validation(self):
        """Async extension point for bounded validation; no media or callbacks from data."""

    async def _run_job(self, proc, raw, job_id):
        try:
            value = protocol.decode(raw)
            value["scenario"] = self._requested_scenario
            raw = protocol.encode(value)
            self._charge(len(raw), transmit=True)
            future = self._pending_response(job_id)
            proc.stdin.write(raw)
            await proc.stdin.drain()
            result = await asyncio.wait_for(asyncio.shield(future), self.timeout)
            await self._after_validation()
            if asyncio.get_running_loop().time() - self._job_started >= self.job_timeout:
                await self._fail("job-deadline")
                return
            if self.state == "BUSY" and self.enabled and self._job["id"] == job_id:
                self._completed.add(job_id)
                self._job.update(status="complete", result=result["value"])
                self.state = "READY"
                self._log("result-v2")
                self._timer.cancel(); self._timer = None
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._fail("timeout" if isinstance(exc, TimeoutError) else getattr(exc, "code", "protocol"))

    async def wait(self):
        result = await super().wait()
        for task in (self._expiry_task, self._fault_task):
            if task and task is not asyncio.current_task(): await asyncio.shield(task)
        return self.status()["job"]
