"""M4 caption approval regression tests; synthetic temporary projects only.

Run: ~/.venvs/reelstudio/bin/python -B tests/test_caption_fixes.py
Extract the actual handler and file helpers because importing server.py starts
its background worker. No app server, engine jobs, models or real projects run.
"""
import ast
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_handler(directory, events):
    source = ROOT / 'app' / 'server.py'
    tree = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
    names = {'caption_fixes', '_save_project'}
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise AssertionError('caption handler or file helper missing')
    for node in nodes:
        node.decorator_list = []

    def load(path):
        return json.loads(Path(path).read_text(encoding='utf-8'))

    def name_ok(name, write=False):
        if name != 'synthetic_speaker' or not write:
            raise AssertionError('handler must request writable synthetic project')
        return str(directory)

    def view(name):
        if name != 'synthetic_speaker':
            raise AssertionError('unexpected project view')
        result = {'project': load(directory / 'project.json'),
                  'words': load(directory / 'build/transcript.json')['words']}
        plan = directory / 'build/plan.json'
        if plan.exists():
            result['plan'] = load(plan)
        return result

    namespace = dict(os=os, json=json, CaptionFix=SimpleNamespace, load=load,
                     _name_ok=name_ok, _project_view=view,
                     _history=lambda d, message: events.append((d, message)))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['caption_fixes']


class CaptionFixTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='m4-caption-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        (self.directory / 'build').mkdir()
        self.events = []
        self.fix = load_handler(self.directory, self.events)
        self.save('project.json', {'approved': True, 'title': ['Keep me']})
        self.save('build/plan.json', {'approved': True, 'sentinel': 'keep'})
        self.save('build/transcript.json', {'words': [
            {'w': 'original', 's': 0, 'e': 1, 'review': True}]})

    def save(self, name, data):
        (self.directory / name).write_text(json.dumps(data), encoding='utf-8')

    def correct(self, word):
        return self.fix('synthetic_speaker', SimpleNamespace(fixes={0: word}))

    def test_changed_caption_withdraws_both_approvals(self):
        result = self.correct('corrected')
        self.assertIs(result['project']['approved'], False)
        self.assertIs(result['plan']['approved'], False)
        self.assertEqual(result['project']['title'], ['Keep me'])
        self.assertEqual(result['plan']['sentinel'], 'keep')
        self.assertEqual(result['words'][0]['w'], 'corrected')
        self.assertNotIn('review', result['words'][0])
        transcript = json.loads((self.directory / 'build/transcript.json').read_text())
        self.assertIs(transcript['corrected'], True)
        self.assertEqual(len(self.events), 3)

    def test_repeated_corrections_preserve_original_asr_word(self):
        first = self.correct('corrected')
        self.assertEqual(first['words'][0]['w_asr'], 'original')
        second = self.correct('corrected_again')
        self.assertEqual(second['words'][0]['w'], 'corrected_again')
        self.assertEqual(second['words'][0]['w_asr'], 'original')

    def test_unchanged_caption_preserves_approvals_and_files(self):
        before = {p: p.read_bytes() for p in self.directory.rglob('*.json')}
        result = self.correct(' original ')
        self.assertIs(result['project']['approved'], True)
        self.assertIs(result['plan']['approved'], True)
        self.assertEqual(self.events, [])
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_without_plan_preserves_project_approval(self):
        (self.directory / 'build/plan.json').unlink()
        before = (self.directory / 'project.json').read_bytes()
        result = self.correct('corrected')
        self.assertNotIn('plan', result)
        self.assertIs(result['project']['approved'], True)
        self.assertEqual((self.directory / 'project.json').read_bytes(), before)
        self.assertEqual(result['words'][0]['w'], 'corrected')
        self.assertEqual(result['words'][0]['w_asr'], 'original')
        self.assertEqual(len(self.events), 1)

    def test_unapproved_plan_still_withdraws_project_approval(self):
        self.save('build/plan.json', {'approved': False})
        result = self.correct('corrected')
        self.assertIs(result['plan']['approved'], False)
        self.assertIs(result['project']['approved'], False)
        self.assertEqual(len(self.events), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
