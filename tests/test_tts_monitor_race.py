"""Exercise worker-exit race without models or processes."""
import ast
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock


class MonitorRace(unittest.TestCase):
    def sample(self, process, monitor):
        path = Path(__file__).resolve().parents[1] / 'engine/narrate.py'
        node = next(n for n in ast.parse(path.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'worker_rss')
        scope = dict(rss_bytes=monitor, subprocess=subprocess)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
        return scope['worker_rss'](process)

    def test_exited_worker_may_have_no_proc_info(self):
        p = Mock(pid=42); p.wait.return_value = 0
        self.assertEqual(self.sample(p, Mock(side_effect=RuntimeError('proc vanished'))), 0)
        p.wait.assert_called_once_with(timeout=0.1)

    def test_live_unmeasurable_worker_fails_closed(self):
        p = Mock(pid=42); p.wait.side_effect = subprocess.TimeoutExpired('worker', .1)
        with self.assertRaises(RuntimeError):
            self.sample(p, Mock(side_effect=RuntimeError('monitor denied')))

    def test_measured_memory_is_not_masked(self):
        p = Mock(pid=42)
        self.assertEqual(self.sample(p, Mock(return_value=9_000_000_000)), 9_000_000_000)
        p.wait.assert_not_called()


if __name__ == '__main__': unittest.main(verbosity=2)
