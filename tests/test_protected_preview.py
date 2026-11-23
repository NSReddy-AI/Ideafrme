"""The preview GET writes a JPEG, so it must enforce baseline write protection."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class ProtectedPreview(unittest.TestCase):
    def test_baseline_rejected_before_read_or_render(self):
        path = Path(__file__).resolve().parents[1] / 'app/server.py'
        node = next(n for n in ast.parse(path.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'source_frame')
        node.decorator_list = []

        def guard(name, write=False):
            self.assertTrue(write, 'preview writes source_frame.jpg; write guard required')
            raise PermissionError('protected baseline')

        read = Mock()
        render = Mock()
        scope = dict(_name_ok=guard, load=read, subprocess=SimpleNamespace(run=render))
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
        with self.assertRaises(PermissionError):
            scope['source_frame']('2026-11-03_reel_002_development')
        read.assert_not_called()
        render.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
