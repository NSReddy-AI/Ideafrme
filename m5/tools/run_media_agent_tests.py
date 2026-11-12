"""Fresh bounded evidence; trusted synthetic tests only. No existing runners invoked."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE))
from media_analysis_agent.policy import RUNTIME, SCRATCH_BYTES

NEW_FILES = (
    *('media_analysis_agent/' + name for name in ('__init__.py', 'policy.py', 'protocol.py', 'storage.py',
       'backends.py', 'worker.py', 'controller.py', '__main__.py', 'README.md')),
    'media_agent_tests/test_agent.py', 'tools/run_media_agent_tests.py',
    'docs/MEDIA_ANALYSIS_AGENT_HANDOFF.md')


def hashes():
    excluded = {'.runtime', '.git', 'node_modules', '__pycache__'}
    return {str(p.relative_to(WORKSPACE)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in WORKSPACE.rglob('*') if not any(x in excluded for x in p.relative_to(WORKSPACE).parts)
            and p.is_file() and not p.is_symlink() and str(p.relative_to(WORKSPACE)) not in NEW_FILES}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if not args.run_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.run_id):
        raise SystemExit('invalid run ID')
    root = RUNTIME / args.run_id
    for p in [root, *root.parents]:
        if p.is_symlink(): raise SystemExit('symlink runtime root')
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.environ['MEDIA_AGENT_TEST_ROOT'] = str(root / 'instances')
    for key in ('TMPDIR', 'TMP', 'TEMP', 'HOME', 'XDG_CACHE_HOME'):
        os.environ[key] = str(root)
    before = hashes()
    rejected = []

    def inside(path):
        if isinstance(path, int): return
        value = Path(os.fsdecode(path))
        if not value.is_absolute(): value = Path.cwd() / value
        try: value.resolve().relative_to(root)
        except ValueError:
            rejected.append('external-write')
            raise PermissionError('test write outside fresh evidence root')

    def guard(event, values):
        if event == 'open':
            path, mode, flags = values
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
                inside(path)
        elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate', 'os.utime'}:
            inside(values[0])
        elif event in {'os.rename', 'os.link'}:
            inside(values[0]); inside(values[1])
        elif event == 'os.symlink':
            inside(values[0]); inside(values[1])
        elif event.startswith('socket.'):
            # asyncio's local self-pipe is a trusted runtime primitive, not network use.
            if event not in {'socket.__new__'}:
                rejected.append('network'); raise PermissionError('no networking')
        elif event == 'subprocess.Popen':
            executable, argv, cwd, env = values
            worker = [sys.executable, '-I', '-B', str(WORKSPACE / 'media_analysis_agent/worker.py')]
            cli = [sys.executable, '-B', '-m', 'media_analysis_agent']
            if (os.path.realpath(executable) != os.path.realpath(sys.executable)
                    or (list(argv[:4]) != worker and list(argv[:4]) != cli)):
                rejected.append('process'); raise PermissionError('unexpected child')
        elif event in {'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.system', 'os.exec'}:
            rejected.append('process'); raise PermissionError('unexpected launch')

    sys.addaudithook(guard)
    # Last-resort trusted-suite bound, not an untrusted-job enforcement mechanism.
    def deadline(*_):
        raise KeyboardInterrupt("synthetic suite deadline exceeded")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(60)
    os.environ['PYTHONASYNCIODEBUG'] = '0'
    started = time.monotonic()
    with (root / 'tests.txt').open('x', encoding='utf-8') as transcript:
        suite = unittest.defaultTestLoader.discover(str(WORKSPACE / 'media_agent_tests'), pattern='test_agent.py')
        result = unittest.TextTestRunner(stream=transcript, verbosity=2).run(suite)
    signal.alarm(0)
    after = hashes()
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    report = {'started_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'seconds': time.monotonic() - started, 'baseline_files': len(before),
              'changed_baseline': changed, 'rejected_attempts': rejected, 'evidence_bytes': size,
              'synthetic_only': True, 'gate_a_qualified': False,
              'source_hashes': {p: hashlib.sha256((WORKSPACE/p).read_bytes()).hexdigest()
                                for p in NEW_FILES if (WORKSPACE/p).is_file()},
              'baseline_hashes': before}
    (root / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in {'source_hashes', 'baseline_hashes'}}, sort_keys=True))
    print(str(root))
    return 0 if result.wasSuccessful() and not changed and size < SCRATCH_BYTES else 1


if __name__ == '__main__':
    raise SystemExit(main())
