"""Async optional controller. Only the fixed trusted synthetic backend may launch."""
import asyncio
import copy
import fcntl
import os
import uuid

from . import backends, protocol
from .policy import (AgentError, FRAME_BYTES, VALUE_BYTES, START_SECONDS,
                     TERMINATE_SECONDS, WORKER_SECONDS, JOB_SECONDS, SCENARIOS)
from .storage import Files


class Agent:
    def __init__(self, root, *, timeout=WORKER_SECONDS, startup_timeout=START_SECONDS):
        if (type(timeout) not in (float, int) or not 0 < timeout <= WORKER_SECONDS
                or type(startup_timeout) not in (float, int) or not 0 < startup_timeout <= START_SECONDS):
            raise AgentError("limit", "timeouts may only tighten policy")
        self.files = Files(root)
        try:
            config = self.files.read_config()
        except Exception:
            self.files.close()
            raise
        self.enabled = config["enabled"]
        # Persistent enable preference never launches a process on reopen.
        self.state = "STOPPED" if self.enabled else "DISABLED"
        self.timeout, self.startup_timeout = float(timeout), float(startup_timeout)
        self._process = self._monitor_task = self._job_task = None
        self._admission_fd = None
        self._session = None
        self._job = None
        self._expected_exits = set()
        self._termination_confirmed = True
        self._control_lock = asyncio.Lock()
        self._cleanup_lock = asyncio.Lock()
        self.last_error = None
        self.diagnostic_error = False
        self.closed = False

    def _log(self, event, code="ok"):
        try:
            self.files.diagnostic(event, code, self.state)
        except Exception:
            # Logging failure cannot take down the caller's manual workflow.
            self.diagnostic_error = True

    def _status(self):
        return {"enabled": self.enabled, "state": self.state,
                "backend": "synthetic", "real_media_enabled": False,
                "pid": self._process.pid if self._process else None,
                "termination_confirmed": self._termination_confirmed,
                "last_error": self.last_error, "diagnostic_error": self.diagnostic_error,
                "job": copy.deepcopy(self._job)}

    def status(self):
        return self._status()

    def _check_open(self):
        if self.closed:
            raise AgentError("closed", "controller closed")

    def _set_disabled(self):
        self.enabled = False
        try:
            self.files.config(False)
        except Exception:
            self.diagnostic_error = True

    async def enable(self, backend="synthetic"):
        async with self._control_lock:
            self._check_open()
            backends.select(backend)  # reject real-media before configuration or launch
            if self.state == "FAULTED":
                raise AgentError("fault", "explicit recovery required")
            self.files.config(True)
            self.enabled = True
            if self.state == "DISABLED": self.state = "STOPPED"
            self._log("enable")
            return self._status()

    async def _frame(self, proc):
        try:
            raw = await proc.stdout.readline()
            if not raw:
                raise AgentError("crash", "backend closed output")
            return protocol.decode(raw)
        except (UnicodeError, ValueError) as exc:
            if isinstance(exc, AgentError): raise
            raise AgentError("protocol", "invalid or oversized backend frame") from exc

    async def _monitor(self, proc):
        await proc.wait()
        if self._process is proc and proc.pid not in self._expected_exits:
            self._termination_confirmed = True
            self._set_disabled()
            self.state = "FAULTED"
            self.last_error = "crash"
            self._log("fault", "crash")

    async def start(self, *, startup="normal"):
        async with self._control_lock:
            self._check_open()
            if not self.enabled or self.state != "STOPPED":
                raise AgentError("state", "enable and explicit stopped state required")
            if startup not in {"normal", "crash", "hang", "bad-handshake"}:
                raise AgentError("capability", "unknown synthetic startup")
            # Shared read-only inode lock; no global configuration/cache writes.
            fd = os.open(backends.__file__, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                os.close(fd)
                raise AgentError("busy", "another synthetic instance owns backend admission") from exc
            self._admission_fd = fd
            self.state, self.last_error = "STARTING", None
            self._session = str(uuid.uuid4())
            command = backends.select("synthetic").command(self._session, startup)
            env = {"HOME": str(self.files.root), "TMPDIR": str(self.files.root),
                   "TMP": str(self.files.root), "TEMP": str(self.files.root),
                   "XDG_CACHE_HOME": str(self.files.root), "LC_ALL": "C",
                   "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
            try:
                launch = asyncio.create_task(asyncio.create_subprocess_exec(
                    *command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT, limit=FRAME_BYTES,
                    cwd=self.files.root, env=env, close_fds=True,
                    pass_fds=(self._admission_fd,)))
                try:
                    self._process = await asyncio.shield(launch)
                except asyncio.CancelledError:
                    # Retain the process handle even if the caller cancels during spawn.
                    self._process = await launch
                    self._termination_confirmed = False
                    raise
                self._termination_confirmed = False
                self._monitor_task = asyncio.create_task(self._monitor(self._process))
                hello = await asyncio.wait_for(self._frame(self._process), self.startup_timeout)
                protocol.ready(hello, self._session)
                if self._process.returncode is not None or self.state == "FAULTED":
                    raise AgentError("crash", "backend exited during startup")
                self.state = "READY"
                self._log("start")
                return self._status()
            except asyncio.CancelledError:
                await self._fail("startup-canceled")
                raise
            except Exception as exc:
                await self._fail("timeout" if isinstance(exc, TimeoutError) else getattr(exc, "code", "launch"))
                raise AgentError(self.last_error, "synthetic startup failed") from exc

    async def _confirm_exit(self, proc):
        try:
            await asyncio.wait_for(asyncio.shield(proc.wait()), TERMINATE_SECONDS)
            return proc.returncode is not None
        except TimeoutError:
            return False

    async def _terminate(self):
        async with self._cleanup_lock:
            proc = self._process
            if proc is None:
                if self._termination_confirmed and self._admission_fd is not None:
                    os.close(self._admission_fd)
                    self._admission_fd = None
                return self._termination_confirmed
            self._expected_exits.add(proc.pid)
            if proc.stdin:
                proc.stdin.close()
            if proc.returncode is None:
                try:
                    # Immediate kill: no extra processing allowance after cancel/deadline.
                    proc.kill()
                except ProcessLookupError:
                    pass
                except OSError:
                    self._termination_confirmed = False
                    return False
            confirmed = await self._confirm_exit(proc)
            self._termination_confirmed = confirmed
            if confirmed:
                if self._monitor_task and self._monitor_task is not asyncio.current_task():
                    await self._monitor_task
                self._process = None
                self._expected_exits.discard(proc.pid)
                self._monitor_task = None
                if self._admission_fd is not None:
                    os.close(self._admission_fd)
                    self._admission_fd = None
            return confirmed

    async def _fail(self, code):
        self._set_disabled()
        self.state, self.last_error = "FAULTED", code
        if self._job and self._job["status"] == "running":
            self._job.update(status="failed", error=code, result=None)
        confirmed = await self._terminate()
        if not confirmed:
            self.last_error = "termination-unconfirmed"
        self._log("fault", self.last_error)

    async def submit(self, value, *, scenario="echo"):
        async with self._control_lock:
            self._check_open()
            if self.state != "READY" or not self.enabled or self._process is None:
                raise AgentError("state", "one ready synthetic backend required")
            if type(value) is not str or scenario not in SCENARIOS:
                raise AgentError("input", "synthetic string and known scenario required")
            try:
                if len(value.encode("utf-8")) > VALUE_BYTES:
                    raise ValueError()
            except (UnicodeError, ValueError) as exc:
                raise AgentError("limit", "synthetic input byte limit") from exc
            job_id = str(uuid.uuid4())
            message = {"v": 1, "type": "job", "session": self._session,
                       "job_id": job_id, "value": value, "scenario": scenario}
            raw = protocol.encode(message)
            self.state = "BUSY"
            self._job = {"id": job_id, "status": "running", "result": None, "error": None,
                         "synthetic": True, "operational_eligible": False}
            self._job_task = asyncio.create_task(self._run_job(self._process, raw, job_id))
            self._log("submit")
            return copy.deepcopy(self._job)

    async def submit_media(self, request):
        """Reserved interface: reject BEFORE reading a handle or launching anything."""
        self._check_open()
        if not isinstance(request, backends.MediaRequest) or request.capability not in {"image", "ocr-eng", "ocr-tel", "video"}:
            raise AgentError("capability", "real-media request descriptor required")
        backends.select(request.capability)  # all real-media entries fail closed
        raise AgentError("unqualified", "no real-media implementation authorized")

    async def _run_job(self, proc, raw, job_id):
        try:
            async def exchange():
                proc.stdin.write(raw)
                await proc.stdin.drain()
                result = await self._frame(proc)
                protocol.result(result, self._session, job_id)
                return result
            value = await asyncio.wait_for(exchange(), min(self.timeout, JOB_SECONDS))
            # Cancellation/disable can never publish a late result.
            if self.state == "BUSY" and self.enabled and self._job["id"] == job_id:
                self._job.update(status="complete", result=value["value"])
                self.state = "READY"
                self._log("result")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._fail("timeout" if isinstance(exc, TimeoutError) else getattr(exc, "code", "transport"))

    async def wait(self):
        task = self._job_task
        if task:
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if not task.cancelled(): raise
        return copy.deepcopy(self._job)

    async def _stop(self, *, disable, cancel):
        self._check_open()
        was_fault = self.state == "FAULTED"
        self.state = "STOPPING"
        if disable: self._set_disabled()
        task = self._job_task
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if self._job and self._job["status"] == "running":
            self._job.update(status="canceled", error="cancel" if cancel else "stop", result=None)
        confirmed = await self._terminate()
        if not confirmed:
            self.state, self.last_error = "FAULTED", "termination-unconfirmed"
            self._set_disabled()
        elif was_fault:
            self.state = "FAULTED"  # stop/disable never silently acknowledges a fault
        else:
            self.state = "STOPPED" if self.enabled else "DISABLED"
        self._log("cancel" if cancel else "stop", self.last_error or "ok")
        return self._status()

    async def stop(self):
        async with self._control_lock:
            return await self._stop(disable=False, cancel=False)

    async def cancel(self):
        async with self._control_lock:
            return await self._stop(disable=False, cancel=True)

    async def disable(self):
        async with self._control_lock:
            return await self._stop(disable=True, cancel=False)

    async def recover(self):
        async with self._control_lock:
            self._check_open()
            if self.state != "FAULTED":
                raise AgentError("state", "fault acknowledgement only")
            if not await self._terminate():
                raise AgentError("termination-unconfirmed", "cannot acknowledge live or unknown child")
            self._set_disabled()
            self.state, self.last_error = "DISABLED", None
            self._log("recover")
            # Explicit enable AND start are needed; never resume or retry an old job.
            return self._status()

    async def rollback(self):
        return await self.disable()  # no deletions, package switching or historical rewrite

    async def close(self):
        if self.closed: return
        await self.stop()
        if not self._termination_confirmed:
            raise AgentError("termination-unconfirmed", "retain instance ownership until confirmed")
        self.closed = True
        self.files.close()
