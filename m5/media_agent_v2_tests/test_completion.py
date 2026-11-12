import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from media_analysis_agent.policy import AgentError, WORKSPACE
from media_analysis_agent import protocol
from media_analysis_agent_v2.controller import Agent
from media_analysis_agent_v2.packages import Deployment, build, inspect_bundle, sha

ROOT = Path(os.environ["MEDIA_AGENT_TEST_ROOT"])
spec = importlib.util.spec_from_file_location("foundation_cases", WORKSPACE / "media_agent_tests/test_agent.py")
_old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_old)


class Lifecycle(_old.AgentTests):
    async def asyncSetUp(self):
        self.root = ROOT / self._testMethodName
        self.agent = Agent(self.root, timeout=0.18, startup_timeout=0.4)

    async def asyncTearDown(self):
        await asyncio.wait_for(self.agent.close(), 3)

    async def test_aggregate_job_budget_before_send(self):
        await self.agent.close()
        self.agent = Agent(self.root, wire_limit=100)
        await self.ready(); await self.agent.submit("bounded")
        result = await asyncio.wait_for(self.agent.wait(), 2)
        self.assertEqual(result["error"], "communication-limit")
        self.assertIsNone(result["result"])

    async def test_aggregate_session_budget_includes_handshake(self):
        await self.agent.close()
        self.agent = Agent(self.root, session_limit=150)
        await self.ready(); await self.agent.submit("bounded")
        result = await asyncio.wait_for(self.agent.wait(), 2)
        self.assertEqual(result["error"], "communication-limit")

    async def test_exact_job_communication_boundary(self):
        await self.ready(); await self.agent.submit("boundary")
        await self.agent.wait()
        status = self.agent.status(); size = status["wire_tx"] + status["wire_rx"]
        await self.agent.close()
        for delta in (-1, 0, 1):
            self.agent = Agent(self.root / ("boundary-" + str(delta)), wire_limit=size+delta)
            await self.ready(); await self.agent.submit("boundary")
            result = await self.agent.wait()
            self.assertEqual(result["status"], "failed" if delta == -1 else "complete")
            await self.agent.close()

    async def test_session_budget_accumulates_across_jobs(self):
        await self.ready(); hello = self.agent.status()["session_bytes"]
        await self.agent.submit("budget"); await self.agent.wait()
        status = self.agent.status(); size = status["wire_tx"] + status["wire_rx"]
        await self.agent.close()
        self.agent = Agent(self.root / "accumulation", session_limit=hello + size)
        await self.ready(); await self.agent.submit("budget")
        self.assertEqual((await self.agent.wait())["status"], "complete")
        await self.agent.submit("budget")
        self.assertEqual((await self.agent.wait())["error"], "communication-limit")

    async def test_v2_limits_cannot_be_expanded(self):
        for options in ({"job_timeout":61}, {"job_timeout":float("nan")},
                        {"wire_limit":16385}, {"session_limit":1048577}, {"wire_limit":True}):
            with self.assertRaises(AgentError) as error: Agent(self.root / "invalid", **options)
            self.assertEqual(error.exception.code, "limit")

    async def test_duplicate_response_quarantines_result(self):
        await self.ready(); await self.agent.submit("duplicate", scenario="duplicate")
        await asyncio.wait_for(self.agent.wait(), 2)
        await asyncio.sleep(0.03)
        self.assertEqual(self.agent.status()["state"], "FAULTED")
        self.assertIsNone(self.agent.status()["job"]["result"])

    async def test_actual_previous_job_replay_rejected(self):
        await self.ready(); first = await self.agent.submit("first")
        await self.agent.wait()
        second = await self.agent.submit("second", scenario="stale")
        self.assertNotEqual(first["id"], second["id"])
        result = await asyncio.wait_for(self.agent.wait(), 2)
        self.assertEqual(result["status"], "failed")

    async def test_actual_revoked_session_rejected_after_restart(self):
        await self.ready(); old = self.agent.status()["session"]
        await self.agent.stop()
        self.assertEqual(self.agent.status()["revoked_session"], old)
        await self.agent.start()
        self.assertNotEqual(old, self.agent.status()["session"])
        await self.agent.submit(old, scenario="old-session")
        self.assertEqual((await self.agent.wait())["status"], "failed")

    async def test_unsolicited_handshake_fault(self):
        await self.agent.enable()
        try: await self.agent.start(startup="unsolicited")
        except AgentError: pass
        await asyncio.sleep(0.03)
        self.assertEqual(self.agent.status()["state"], "FAULTED")

    async def test_unsupported_response_version_no_downgrade(self):
        await self.ready(); await self.agent.submit("safe", scenario="unsupported")
        self.assertEqual((await self.agent.wait())["status"], "failed")
        self.assertEqual(self.agent.status()["state"], "FAULTED")

    async def test_missing_backend_executable_faults_without_retry(self):
        await self.agent.enable()
        async def unavailable(*args, **kwargs): raise FileNotFoundError("synthetic missing executable")
        with patch("asyncio.create_subprocess_exec", new=unavailable):
            with self.assertRaises(AgentError): await self.agent.start()
        self.assertEqual(self.agent.status()["state"], "FAULTED")
        self.assertIsNone(self.agent.status()["pid"])
        self.assertTrue(self.agent.status()["termination_confirmed"])

    async def test_complete_job_watchdog_includes_validation(self):
        await self.agent.close()
        self.agent = Agent(self.root, timeout=1, job_timeout=0.06)
        await self.ready()
        async def delayed(): await asyncio.sleep(0.5)
        with patch.object(self.agent, "_after_validation", new=delayed):
            await self.agent.submit("safe")
            result = await asyncio.wait_for(self.agent.wait(), 1)
        self.assertEqual(result["error"], "job-deadline")
        self.assertTrue(self.agent.status()["termination_confirmed"])
        self.assertIsNone(result["result"])

    async def test_cancel_late_result_and_revoke(self):
        await self.ready(); session = self.agent.status()["session"]
        await self.agent.submit("late", scenario="late")
        await self.agent.cancel()
        await asyncio.sleep(0.03)
        self.assertEqual(self.agent.status()["revoked_session"], session)
        self.assertIsNone(self.agent.status()["job"]["result"])

    async def test_manual_core_remains_usable_across_agent_failures(self):
        from creative_core import new_document, apply, save, load
        def edit(label):
            root = self.root / ("manual-" + label); root.mkdir()
            doc = new_document("synthetic-" + label)
            doc = apply(doc, {"op":"move", "element_id":"title", "x":90, "y":120}, root)
            save(doc, root)
            self.assertEqual(load(root), doc)
        edit("absent")
        edit("disabled")
        await self.ready(); await self.agent.submit("hang", scenario="hang")
        edit("hung")
        await self.agent.wait(); edit("timeout")
        await self.agent.recover(); await self.ready()
        await self.agent.submit("crash", scenario="crash"); await self.agent.wait()
        edit("crashed")
        await self.agent.recover(); await self.agent.enable()
        with self.assertRaises(AgentError): await self.agent.start(startup="bad-handshake")
        edit("incompatible")


class ProtocolRegression(_old.BoundaryTests):
    pass


class Packaging(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.root = ROOT / self._testMethodName
        self.root.mkdir(parents=True)
        self.deployment = Deployment(self.root / "deployment")

    def bundle(self, version="0.2.0", protocol_version=1, suffix=""):
        return build(self.root / (version + suffix + ".zip"), version, protocol_version=protocol_version)

    async def test_deterministic_offline_bundle_and_immutable_install(self):
        a = self.bundle(); b = self.bundle(suffix="-repeat")
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertLess(a["bytes"], 256 * 1024 * 1024)
        self.deployment.install(a["path"], expected_sha256=a["sha256"])
        with self.assertRaises(AgentError): self.deployment.install(a["path"], expected_sha256=a["sha256"])
        self.assertIsNone(self.deployment.selection()["active"])
        self.deployment.activate("0.2.0")
        self.assertFalse(self.deployment.verify("0.2.0")["real_media_enabled"])

    async def test_hash_and_protocol_incompatibility_refused(self):
        a = self.bundle()
        with self.assertRaises(AgentError): inspect_bundle(a["path"], "0" * 64)
        b = self.bundle("0.2.1", protocol_version=2)
        with self.assertRaises(AgentError): self.deployment.install(b["path"], expected_sha256=b["sha256"])
        self.assertFalse((self.deployment.root / "versions/0.2.1").exists())

    async def test_runtime_incompatibility_refused_before_activation(self):
        item = self.bundle(); self.deployment.install(item["path"], expected_sha256=item["sha256"])
        with patch("sys.version_info", (3, 14, 0)):
            with self.assertRaises(AgentError): self.deployment.activate("0.2.0")
        self.assertIsNone(self.deployment.selection()["active"])

    async def test_update_does_not_inherit_qualification_and_rollback_preserves_report(self):
        for release in ("0.2.0", "0.2.1"):
            item = self.bundle(release)
            self.deployment.install(item["path"], expected_sha256=item["sha256"])
        self.deployment.activate("0.2.0"); self.deployment.activate("0.2.1")
        self.assertEqual(self.deployment.activate("0.2.1")["previous"], "0.2.0")
        report = self.root / "synthetic-history.txt"
        report.write_bytes(b"synthetic immutable report sentinel, not an R2 record")
        before = sha(report.read_bytes())
        agent = Agent(self.root / "instance")
        try:
            await agent.enable(); await agent.start()
            active = agent.status()["session"]
            with self.assertRaises(AgentError): self.deployment.activate("0.2.0")
            selection = await self.deployment.rollback(agent)
            self.assertEqual(selection["active"], "0.2.0")
            self.assertIsNone(selection["qualification"])
            self.assertFalse(self.deployment.verify("0.2.1")["real_media_enabled"])
            self.assertEqual(agent.status()["revoked_session"], active)
            self.assertTrue(agent.status()["termination_confirmed"])
            self.assertEqual(before, sha(report.read_bytes()))
        finally: await agent.close()

    async def test_installed_payload_tamper_refused(self):
        item = self.bundle(); self.deployment.install(item["path"], expected_sha256=item["sha256"])
        (self.deployment.root / "versions/0.2.0/media_analysis_agent_v2/worker.py").write_text("# synthetic corruption")
        with self.assertRaises(AgentError): self.deployment.activate("0.2.0")

    async def test_installed_cli_default_off_and_echo(self):
        item = self.bundle(); self.deployment.install(item["path"], expected_sha256=item["sha256"])
        self.deployment.activate("0.2.0")
        command = self.deployment.command(self.root / "installed-instance")
        proc = await asyncio.create_subprocess_exec(*command, stdin=asyncio.subprocess.PIPE,
                 stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=self.root)
        commands = [{"op":"enable"},{"op":"start"},{"op":"submit","value":"తెలుగు / English"},
                    {"op":"wait"},{"op":"disable"},{"op":"quit"}]
        out, err = await asyncio.wait_for(proc.communicate(b"".join(protocol.encode(x) for x in commands)), 5)
        self.assertEqual(proc.returncode, 0, err.decode())
        rows = [json.loads(x) for x in out.splitlines()]
        self.assertEqual(rows[0]["status"]["state"], "DISABLED")
        self.assertTrue(all(x["ok"] for x in rows), rows)
        self.assertEqual(rows[4]["result"]["result"], "తెలుగు / English")

    async def test_v2_controller_death_no_restart_or_surviving_child(self):
        command = [sys.executable, "-I", "-B", str(WORKSPACE / "media_analysis_agent_v2/__main__.py"),
                   "serve", "--root", str(self.root / "controller-death")]
        proc = await asyncio.create_subprocess_exec(*command, stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            await asyncio.wait_for(proc.stdout.readline(), 1)
            for cmd in ({"op":"enable"},{"op":"start"}):
                proc.stdin.write(protocol.encode(cmd)); await proc.stdin.drain()
                row = json.loads(await asyncio.wait_for(proc.stdout.readline(), 1))
                self.assertTrue(row["ok"])
            child = row["result"]["pid"]
            proc.stdin.write(protocol.encode({"op":"submit","value":"safe","scenario":"hang"}))
            await proc.stdin.drain(); await asyncio.wait_for(proc.stdout.readline(), 1)
            proc.kill(); await asyncio.wait_for(proc.wait(), 1)
            for _ in range(100):
                try: os.kill(child, 0)
                except ProcessLookupError: break
                await asyncio.sleep(0.02)
            else: self.fail("synthetic child survived EOF")
        finally:
            if proc.returncode is None: proc.kill(); await proc.wait()
