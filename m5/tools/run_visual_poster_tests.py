"""New visual suites only; fresh bounded evidence, loopback-only sockets, no children."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'visual_poster_tests'))
NEW=tuple('visual_poster_studio/'+n for n in ('__init__.py','__main__.py','service.py','server.py','scene.py','fonts.py','exports.py','index.html','app.js','styles.css'))+tuple('visual_poster_tests/'+n for n in ('test_scene.py','test_fonts.py','test_service.py','test_http.py','browser_acceptance.html','browser_acceptance.js'))+('tools/run_visual_poster_tests.py','docs/VISUAL_POSTER_HANDOFF.md')
def hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink() and not any(x in {'.runtime','.git','__pycache__','node_modules'} for x in p.relative_to(ROOT).parts) and str(p.relative_to(ROOT)) not in NEW}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);name=ap.parse_args().run_id
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):raise SystemExit('Invalid run ID')
    root=ROOT/'.runtime/studio-ui'/name
    if not name.startswith('visual-'):raise SystemExit('Use a visual- run ID')
    for p in (root,*root.parents):
        if p.is_symlink():raise SystemExit('Unexpected symlink')
    root.mkdir(exist_ok=False,mode=0o700);os.environ['VISUAL_TEST_ROOT']=str(root/'cases')
    for key in ('TMPDIR','TMP','TEMP','XDG_CACHE_HOME'):os.environ[key]=str(root)
    before=hashes();rejected=[]
    def inside(v):
        if isinstance(v,int):return
        p=Path(os.fsdecode(v))
        if not p.is_absolute():p=Path.cwd()/p
        if not p.resolve().is_relative_to(root):rejected.append('outside-write');raise PermissionError('Outside evidence root')
    def audit(event,args):
        if event=='open':
            path,mode,flags=args
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):inside(path)
        elif event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.truncate','os.utime'}:inside(args[0])
        elif event in {'os.rename','os.link','os.symlink'}:inside(args[0]);inside(args[1])
        elif event in {'subprocess.Popen','os.fork','os.forkpty','os.exec','os.system','os.posix_spawn'}:rejected.append('process');raise PermissionError('No child processes')
        elif event.startswith('socket.'):
            okay=event=='socket.__new__' and args[1]==2
            if event in {'socket.bind','socket.connect'}:okay=isinstance(args[1],tuple) and args[1][0]=='127.0.0.1'
            if event=='socket.getaddrinfo':okay=args[0]=='127.0.0.1'
            if not okay:rejected.append('network');raise PermissionError('Loopback only')
    sys.addaudithook(audit)
    def timeout(*_):raise KeyboardInterrupt('60-second suite deadline')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(60);started=time.monotonic()
    suite=unittest.TestSuite()
    # Explicit classes prevent inherited fixture classes from being collected repeatedly.
    from test_service import ServiceCase
    from test_scene import SceneTests
    from test_fonts import FontTests
    from test_http import HTTPTests
    for cls in (ServiceCase,SceneTests,FontTests,HTTPTests):
        names=[n for n in cls.__dict__ if n.startswith('test_')]
        suite.addTests(cls(n) for n in sorted(names))
    with (root/'tests.txt').open('x') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
    signal.alarm(0);after=hashes();drift=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    report={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'seconds':time.monotonic()-started,'utc':datetime.now(timezone.utc).isoformat(),'baseline_hashes':before,'baseline_drift':drift,'rejected':rejected,'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in NEW if (ROOT/p).exists()},'python':sys.version,'real_media':False,'gate_a_changed':False}
    size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    report['evidence_bytes']=size
    with (root/'results.json').open('x') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('hashes')}));print(root)
    return 0 if result.wasSuccessful() and not drift and not rejected and size<128*1024*1024 else 1
if __name__=='__main__':raise SystemExit(main())
