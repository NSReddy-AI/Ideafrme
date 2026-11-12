"""Fresh audited evidence for the completion revision; no legacy project suites."""
import argparse
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

NEW = tuple('media_analysis_agent_v2/' + name for name in
            ('__init__.py','controller.py','worker.py','packages.py','__main__.py','README.md')) + (
            'media_agent_v2_tests/test_completion.py','tools/run_media_agent_v2_tests.py','docs/MEDIA_AGENT_COMPLETION_HANDOFF.md')


def hashes():
    excluded = {'.runtime','.git','node_modules','__pycache__'}
    return {str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in WORKSPACE.rglob('*') if not any(x in excluded for x in p.relative_to(WORKSPACE).parts)
            and p.is_file() and not p.is_symlink() and str(p.relative_to(WORKSPACE)) not in NEW}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run-id',required=True)
    run = parser.parse_args().run_id
    if not run or any(x not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for x in run):
        raise SystemExit('invalid ID')
    root = RUNTIME / run
    for p in [root,*root.parents]:
        if p.is_symlink(): raise SystemExit('alias')
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.environ['MEDIA_AGENT_TEST_ROOT'] = str(root/'instances')
    for key in ('HOME','TMPDIR','TMP','TEMP','XDG_CACHE_HOME'): os.environ[key] = str(root)
    before = hashes(); rejections=[]; launches=[]

    def inside(value):
        if isinstance(value,int): return
        path = Path(os.fsdecode(value))
        if not path.is_absolute(): path = Path.cwd()/path
        if not path.resolve().is_relative_to(root):
            rejections.append('external-write'); raise PermissionError('outside fresh run')

    def guard(event,args):
        if event=='open':
            path,mode,flags=args
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                inside(path)
        elif event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.truncate','os.utime'}: inside(args[0])
        elif event in {'os.rename','os.link','os.symlink'}: inside(args[0]); inside(args[1])
        elif event.startswith('socket.'):
            if event != 'socket.__new__' or args[1] != 1:
                rejections.append('network'); raise PermissionError('no network')
        elif event=='subprocess.Popen':
            executable,argv,cwd,env=args
            allowed=False
            if list(argv[1:3])==['-I','-B'] and len(argv)>3:
                script=Path(argv[3])
                allowed=script in {WORKSPACE/'media_analysis_agent/worker.py',WORKSPACE/'media_analysis_agent_v2/worker.py',WORKSPACE/'media_analysis_agent_v2/__main__.py'}
                allowed=allowed or (script.is_relative_to(root) and script.parent.name=='media_analysis_agent_v2' and script.name in {'worker.py','__main__.py'})
            if not allowed or os.path.realpath(executable)!=os.path.realpath(sys.executable):
                rejections.append('process'); raise PermissionError('unexpected child')
            launches.append({'argv':list(argv),'cwd':str(cwd)})
        elif event in {'os.fork','os.forkpty','os.system','os.exec','os.posix_spawn'}:
            rejections.append('process'); raise PermissionError('unexpected launch')

    sys.addaudithook(guard)
    def deadline(*_): raise KeyboardInterrupt('60-second bounded suite deadline')
    signal.signal(signal.SIGALRM,deadline); signal.alarm(60)
    started=time.monotonic()
    with (root/'tests.txt').open('x') as transcript:
        suite=unittest.defaultTestLoader.discover(str(WORKSPACE/'media_agent_v2_tests'),pattern='test_completion.py')
        result=unittest.TextTestRunner(stream=transcript,verbosity=2).run(suite)
    signal.alarm(0)
    after=hashes()
    drift=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    report={'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),
            'seconds':time.monotonic()-started,'utc':datetime.now(timezone.utc).isoformat(),
            'baseline_files':len(before),'baseline_changed':drift,'baseline_hashes':before,
            'source_hashes':{p:hashlib.sha256((WORKSPACE/p).read_bytes()).hexdigest() for p in NEW if (WORKSPACE/p).exists()},
            'rejected_attempts':rejections,'child_commands':launches,'evidence_bytes':size,
            'real_media_enabled':False,'gate_a_qualified':False,'python':sys.version}
    with (root/'results.json').open('x') as stream: json.dump(report,stream,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k not in {'baseline_hashes','source_hashes','child_commands'}},sort_keys=True))
    print(root)
    return 0 if result.wasSuccessful() and not drift and not rejections and size<SCRATCH_BYTES else 1


if __name__=='__main__': raise SystemExit(main())
