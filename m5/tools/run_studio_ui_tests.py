"""Bounded new UI suites only, fresh runtime evidence and audited local operations."""
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
from studio_manual_ui.service import RUNTIME

NEW = tuple('studio_manual_ui/' + name for name in
            ('__init__.py','__main__.py','service.py','server.py','index.html','app.js','styles.css')) + (
            'studio_ui_tests/test_service.py','studio_ui_tests/test_http.py','tools/run_studio_ui_tests.py','docs/STUDIO_UI_HANDOFF.md')


def hashes():
    excluded={'.runtime','.git','node_modules','__pycache__'}
    return {str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in WORKSPACE.rglob('*') if not any(x in excluded for x in p.relative_to(WORKSPACE).parts)
            and p.is_file() and not p.is_symlink() and str(p.relative_to(WORKSPACE)) not in NEW}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True)
    identity=parser.parse_args().run_id
    if not identity or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in identity):
        raise SystemExit('Invalid run ID')
    root=RUNTIME/identity
    for p in (root,*root.parents):
        if p.is_symlink():raise SystemExit('Unexpected root symlink')
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    os.environ['STUDIO_UI_TEST_ROOT']=str(root/'cases')
    for key in ('TMPDIR','TMP','TEMP','HOME','XDG_CACHE_HOME'):os.environ[key]=str(root)
    baseline=hashes();rejected=[];network=[]

    def inside(value):
        if isinstance(value,int):return
        path=Path(os.fsdecode(value))
        if not path.is_absolute():path=Path.cwd()/path
        if not path.resolve().is_relative_to(root):
            rejected.append('outside-write');raise PermissionError('Outside fresh UI evidence root')

    def audit(event,args):
        if event=='open':
            path,mode,flags=args
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                inside(path)
        elif event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.truncate','os.utime'}:inside(args[0])
        elif event in {'os.rename','os.link','os.symlink'}:inside(args[0]);inside(args[1])
        elif event in {'subprocess.Popen','os.fork','os.forkpty','os.exec','os.system','os.posix_spawn'}:
            rejected.append('process');raise PermissionError('UI tests cannot launch children')
        elif event.startswith('socket.'):
            allowed=False
            if event=='socket.__new__':allowed=args[1]==2  # IPv4 only; endpoints checked below
            elif event in {'socket.bind','socket.connect'}:
                allowed=isinstance(args[1],tuple) and args[1][0]=='127.0.0.1'
                if allowed:network.append({'operation':event,'address':list(args[1])})
            elif event=='socket.getaddrinfo':allowed=args[0]=='127.0.0.1'
            if not allowed:
                rejected.append('network');raise PermissionError('Loopback HTTP only')

    sys.addaudithook(audit)
    def deadline(*_):raise KeyboardInterrupt('UI suite exceeded 60-second bound')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(60)
    started=time.monotonic()
    with (root/'tests.txt').open('x',encoding='utf-8') as transcript:
        suite=unittest.defaultTestLoader.discover(str(WORKSPACE/'studio_ui_tests'),pattern='test_*.py')
        result=unittest.TextTestRunner(stream=transcript,verbosity=2).run(suite)
    signal.alarm(0)
    after=hashes();drift=[p for p in set(baseline)|set(after) if baseline.get(p)!=after.get(p)]
    size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    report={'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'tests':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'seconds':time.monotonic()-started,
            'baseline_files':len(baseline),'changed_baseline':drift,'baseline_hashes':baseline,
            'source_hashes':{p:hashlib.sha256((WORKSPACE/p).read_bytes()).hexdigest() for p in NEW if (WORKSPACE/p).is_file()},
            'rejected_attempts':rejected,'loopback_activity':network,'evidence_bytes':size,
            'real_media_enabled':False,'browser_visual_verified':False,'gate_a_changed':False}
    with (root/'results.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k not in {'baseline_hashes','source_hashes','loopback_activity'}},sort_keys=True))
    print(root)
    return 0 if result.wasSuccessful() and not drift and not rejected and size<128*1024*1024 else 1


if __name__=='__main__':raise SystemExit(main())
