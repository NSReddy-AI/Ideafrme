"""Bounded trusted synthetic tests; no reference media or resource stress experiments."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
from unittest.mock import AsyncMock, patch

from media_analysis_agent import protocol
from media_analysis_agent.backends import MediaRequest, capabilities, select
from media_analysis_agent.controller import Agent
from media_analysis_agent.policy import AgentError, DIAGNOSTIC_BYTES, FRAME_BYTES, WORKSPACE


ROOT = Path(os.environ["MEDIA_AGENT_TEST_ROOT"])


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.root = ROOT / self._testMethodName
        self.agent = Agent(self.root, timeout=0.18, startup_timeout=0.4)

    async def asyncTearDown(self):
        await self.agent.close()

    async def ready(self):
        await self.agent.enable()
        return await self.agent.start()

    def assertGone(self, pid):
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    async def test_default_off(self):
        self.assertEqual(self.agent.status()["state"], "DISABLED")
        self.assertIsNone(self.agent.status()["pid"])
        with self.assertRaises(AgentError): await self.agent.start()

    async def test_real_capabilities_cannot_enable_or_launch(self):
        for backend in ("image", "ocr-eng", "ocr-tel", "video", "unknown"):
            with self.subTest(backend=backend), self.assertRaises(AgentError):
                await self.agent.enable(backend)
        self.assertEqual(self.agent.status()["state"], "DISABLED")
        self.assertIsNone(self.agent.status()["pid"])
        self.assertEqual(sum(x["available"] for x in capabilities()), 1)

    async def test_enable_does_not_start(self):
        await self.agent.enable()
        self.assertEqual(self.agent.status()["state"], "STOPPED")
        self.assertIsNone(self.agent.status()["pid"])

    async def test_real_media_interface_never_reads_handles(self):
        for capability in ("image", "ocr-eng", "ocr-tel", "video"):
            request = MediaRequest(capability, -999, "0" * 64, "1" * 64)
            with patch("os.read", side_effect=AssertionError("must not read")), self.assertRaises(AgentError):
                await self.agent.submit_media(request)
        self.assertIsNone(self.agent.status()["pid"])

    async def test_idle_backend_crash_is_observed_without_job(self):
        pid = (await self.ready())["pid"]
        self.agent._process.kill()
        await asyncio.wait_for(self.agent._monitor_task, 1)
        self.assertEqual(self.agent.status()["state"], "FAULTED")
        self.assertFalse(self.agent.status()["enabled"])
        self.assertGone(pid)

    async def test_imports_do_not_create_project_paths(self):
        import importlib
        with patch("os.open", side_effect=AssertionError("no import writes")):
            for name in ("media_analysis_agent", "media_analysis_agent.protocol"):
                importlib.reload(sys.modules[name])

    async def test_echo_unicode_and_result_immutability(self):
        await self.ready()
        submitted = await self.agent.submit("తెలుగు English e\u0301")
        submitted["status"] = "forged"
        result = await self.agent.wait()
        self.assertEqual(result["result"], "తెలుగు English e\u0301")
        self.assertEqual(result["status"], "complete")
        self.assertFalse(result["operational_eligible"])
        result["status"] = "forged"
        self.assertEqual(self.agent.status()["job"]["status"], "complete")

    async def test_one_job_only(self):
        await self.ready()
        await self.agent.submit("safe", scenario="hang")
        with self.assertRaises(AgentError): await self.agent.submit("second")
        await self.agent.cancel()

    async def test_distinct_instances_cannot_launch_concurrent_backends(self):
        await self.ready()
        other = Agent(ROOT / "second-instance", timeout=0.2)
        try:
            await other.enable()
            with self.assertRaises(AgentError) as caught:
                await other.start()
            self.assertEqual(caught.exception.code, "busy")
            self.assertIsNone(other.status()["pid"])
            await self.agent.stop()
            await other.start()
            self.assertEqual(other.status()["state"], "READY")
        finally:
            await other.close()

    async def test_stop_confirmed_then_explicit_restart(self):
        pid = (await self.ready())["pid"]
        result = await self.agent.stop()
        self.assertEqual(result["state"], "STOPPED")
        self.assertTrue(result["termination_confirmed"])
        self.assertGone(pid)
        self.assertNotEqual((await self.agent.start())["pid"], pid)

    async def test_disable_cancels_and_does_not_restart(self):
        pid = (await self.ready())["pid"]
        await self.agent.submit("never accepted", scenario="hang")
        result = await self.agent.disable()
        self.assertEqual(result["state"], "DISABLED")
        self.assertEqual(result["job"]["status"], "canceled")
        self.assertIsNone(result["job"]["result"])
        self.assertGone(pid)
        await asyncio.sleep(0.02)
        self.assertIsNone(self.agent.status()["pid"])

    async def test_cancel_ignoring_term_still_confirms_kill(self):
        pid = (await self.ready())["pid"]
        await self.agent.submit("cancel", scenario="ignore-term")
        await asyncio.sleep(0.03)
        result = await self.agent.cancel()
        self.assertTrue(result["termination_confirmed"])
        self.assertEqual(result["job"]["status"], "canceled")
        self.assertGone(pid)

    async def test_timeout_fault_no_retry(self):
        pid = (await self.ready())["pid"]
        await self.agent.submit("timeout", scenario="hang")
        result = await self.agent.wait()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "timeout")
        self.assertEqual(self.agent.status()["state"], "FAULTED")
        self.assertGone(pid)
        await asyncio.sleep(0.03)
        self.assertIsNone(self.agent.status()["pid"])
        with self.assertRaises(AgentError): await self.agent.start()

    async def test_crash_recovery_never_resumes_old_job(self):
        await self.ready()
        old = await self.agent.submit("crash", scenario="crash")
        self.assertEqual((await self.agent.wait())["status"], "failed")
        recovered = await self.agent.recover()
        self.assertEqual(recovered["state"], "DISABLED")
        self.assertIsNone(recovered["pid"])
        await self.ready()
        new = await self.agent.submit("new")
        self.assertNotEqual(old["id"], new["id"])
        self.assertEqual((await self.agent.wait())["result"], "new")

    async def test_unconfirmed_termination_stays_faulted(self):
        await self.ready()
        with patch.object(self.agent, "_confirm_exit", new=AsyncMock(return_value=False)):
            result = await self.agent.disable()
            self.assertEqual(result["state"], "FAULTED")
            self.assertFalse(result["termination_confirmed"])
            self.assertEqual(result["last_error"], "termination-unconfirmed")
            with self.assertRaises(AgentError): await self.agent.recover()
        # The injected confirmation failure did not deliberately leave a live process.
        result = await self.agent.recover()
        self.assertTrue(result["termination_confirmed"])

    async def test_bad_results_never_publish(self):
        for scenario in ("malformed", "oversized", "wrong-session", "wrong-job", "extra-field"):
            with self.subTest(scenario=scenario):
                await self.ready()
                await self.agent.submit("do not trust", scenario=scenario)
                result = await self.agent.wait()
                self.assertEqual(result["status"], "failed")
                self.assertIsNone(result["result"])
                self.assertEqual(self.agent.status()["state"], "FAULTED")
                await self.agent.recover()

    async def test_startup_crash_timeout_handshake(self):
        for startup in ("crash", "hang", "bad-handshake"):
            with self.subTest(startup=startup):
                await self.agent.enable()
                with self.assertRaises(AgentError): await self.agent.start(startup=startup)
                self.assertEqual(self.agent.status()["state"], "FAULTED")
                self.assertTrue(self.agent.status()["termination_confirmed"])
                await self.agent.recover()

    async def test_canceled_startup_confirms_termination(self):
        await self.agent.enable()
        task = asyncio.create_task(self.agent.start(startup="hang"))
        for _ in range(50):
            if self.agent.status()["pid"] is not None: break
            await asyncio.sleep(0.005)
        self.assertIsNotNone(self.agent.status()["pid"])
        pid = self.agent.status()["pid"]
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertEqual(self.agent.status()["state"], "FAULTED")
        self.assertTrue(self.agent.status()["termination_confirmed"])
        self.assertGone(pid)

    async def test_cancellation_during_spawn_retains_and_reaps_handle(self):
        await self.agent.enable()
        original = asyncio.create_subprocess_exec
        launched = []
        async def capture(*args, **kwargs):
            proc = await original(*args, **kwargs)
            launched.append(proc.pid)
            return proc
        with patch("asyncio.create_subprocess_exec", new=capture):
            task = asyncio.create_task(self.agent.start())
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError): await task
        self.assertEqual(len(launched), 1)
        self.assertGone(launched[0])
        self.assertTrue(self.agent.status()["termination_confirmed"])
        self.assertEqual(self.agent.status()["state"], "FAULTED")

    async def test_fault_stop_does_not_acknowledge(self):
        await self.ready()
        await self.agent.submit("crash", scenario="crash")
        await self.agent.wait()
        self.assertEqual((await self.agent.stop())["state"], "FAULTED")
        self.assertEqual((await self.agent.disable())["state"], "FAULTED")

    async def test_input_and_deadline_cannot_expand(self):
        await self.ready()
        for value in ("x" * 1025, "\ud800", None, {}):
            with self.assertRaises(AgentError): await self.agent.submit(value)
        self.assertEqual(self.agent.status()["state"], "READY")
        for seconds in (16, float("nan"), float("inf"), -1, True):
            with self.assertRaises(AgentError): Agent(self.root / "invalid", timeout=seconds)

    async def test_reopen_enabled_config_never_autostarts(self):
        await self.agent.enable()
        await self.agent.close()
        self.agent = Agent(self.root)
        self.assertEqual(self.agent.status()["state"], "STOPPED")
        self.assertIsNone(self.agent.status()["pid"])

    async def test_instance_lock_and_diagnostic_bound(self):
        with self.assertRaises(AgentError): Agent(self.root)
        for _ in range(1500): self.agent._log("bounded")
        self.assertLessEqual((self.root / "diagnostics.jsonl").stat().st_size, DIAGNOSTIC_BYTES)
        self.assertGreater(self.agent.files.dropped, 0)

    async def test_diagnostics_do_not_contain_input(self):
        await self.ready()
        secret = "PRIVATE SYNTHETIC INPUT DO NOT LOG"
        await self.agent.submit(secret)
        await self.agent.wait()
        self.assertNotIn(secret, (self.root / "diagnostics.jsonl").read_text())

    async def test_logging_failure_does_not_break_lifecycle(self):
        with patch.object(self.agent.files, "diagnostic", side_effect=OSError("injected ENOSPC")):
            await self.ready()
            await self.agent.submit("safe")
            self.assertEqual((await self.agent.wait())["status"], "complete")
            self.assertTrue(self.agent.status()["diagnostic_error"])

    async def test_rollback_disables_without_deleting_history(self):
        await self.ready()
        await self.agent.submit("history")
        await self.agent.wait()
        before = (self.root / "diagnostics.jsonl").read_bytes()
        result = await self.agent.rollback()
        self.assertEqual(result["state"], "DISABLED")
        self.assertTrue((self.root / "diagnostics.jsonl").read_bytes().startswith(before))


class BoundaryTests(unittest.TestCase):
    def test_flat_closed_protocol(self):
        for raw in (b'{"v":1,"v":1}\n', b'{"v":{}}\n', b'{"v":[]}\n', b'{"v":1.0}\n',
                    b'{"v":NaN}\n', b'{"v":9223372036854775808}\n', b'{}',
                    b"\xff\n", b"x" * (FRAME_BYTES + 1) + b"\n"):
            with self.subTest(raw=raw[:25]), self.assertRaises((AgentError, UnicodeError)):
                protocol.decode(raw)

    def test_result_exact_binding_and_no_approval(self):
        valid = {"v": 1, "type": "result", "session": "s", "job_id": "j", "value": "ok"}
        protocol.result(valid, "s", "j")
        for key, value in (("approved", True), ("session", "other"), ("job_id", "other"), ("v", True)):
            invalid = dict(valid); invalid[key] = value
            with self.assertRaises(AgentError): protocol.result(invalid, "s", "j")

    def test_external_root_rejected_before_write(self):
        for path in (WORKSPACE, WORKSPACE / "r1_data", WORKSPACE / "examples", ROOT / ".." / "alias"):
            with self.assertRaises(AgentError): Agent(path)

    def test_aliases_and_config_corruption_refused(self):
        root = ROOT / "aliases"
        root.mkdir()
        alias = ROOT / "symlink-instance"
        alias.symlink_to(root, target_is_directory=True)
        with self.assertRaises(AgentError): Agent(alias)
        (root / "config.json").write_text('{"enabled":true,"enabled":false,"backend":"synthetic"}')
        with self.assertRaises(AgentError): Agent(root)

    def test_real_backends_have_no_command(self):
        for name in ("image", "ocr-eng", "ocr-tel", "video"):
            with self.assertRaises(AgentError): select(name)


class CLITests(unittest.IsolatedAsyncioTestCase):
    async def test_controller_death_closes_busy_synthetic_child(self):
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-B", "-m", "media_analysis_agent", "--root", str(ROOT / "controller-death"),
            cwd=WORKSPACE, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, env={"HOME": str(ROOT), "TMPDIR": str(ROOT)})
        child_pid = None
        try:
            await asyncio.wait_for(process.stdout.readline(), 1)
            for command in ({"op": "enable"}, {"op": "start"}):
                process.stdin.write(protocol.encode(command)); await process.stdin.drain()
                response = json.loads(await asyncio.wait_for(process.stdout.readline(), 1))
                self.assertTrue(response["ok"])
            child_pid = response["result"]["pid"]
            process.stdin.write(protocol.encode({"op": "submit", "value": "safe", "scenario": "hang"}))
            await process.stdin.drain()
            await asyncio.wait_for(process.stdout.readline(), 1)
            process.kill()
            await asyncio.wait_for(process.wait(), 1)
            # Verification only, NOT a quota/termination enforcement mechanism.
            for _ in range(100):
                try: os.kill(child_pid, 0)
                except ProcessLookupError: break
                await asyncio.sleep(0.02)
            else: self.fail("synthetic child survived controller EOF")
        finally:
            if process.returncode is None:
                process.kill(); await process.wait()

    async def test_independent_cli_lifecycle(self):
        root = ROOT / "cli"
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-B", "-m", "media_analysis_agent", "--root", str(root), "--timeout", "0.2",
            cwd=WORKSPACE, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, env={"HOME": str(ROOT), "TMPDIR": str(ROOT)})
        commands = [{"op": "enable"}, {"op": "start"}, {"op": "submit", "value": "తెలుగు"},
                    {"op": "wait"}, {"op": "disable"}, {"op": "quit"}]
        raw = b"".join(protocol.encode(x) for x in commands)
        out, err = await asyncio.wait_for(process.communicate(raw), 5)
        self.assertEqual(process.returncode, 0, err.decode())
        lines = [json.loads(x) for x in out.splitlines()]
        self.assertEqual(lines[0]["status"]["state"], "DISABLED")
        self.assertTrue(all(x["ok"] for x in lines))
        self.assertEqual(lines[4]["result"]["result"], "తెలుగు")
        self.assertEqual(lines[5]["result"]["state"], "DISABLED")


if __name__ == "__main__":
    unittest.main()
