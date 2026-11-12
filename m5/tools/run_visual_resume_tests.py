"""Reorder/resume suites with bounded child servers and fresh local-only evidence."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'visual_poster_tests'))
MODIFIED=('creative_core/operations.py','creative_core/validation.py','visual_poster_studio/service.py','visual_poster_studio/index.html','visual_poster_studio/app.js','visual_poster_studio/__main__.py','visual_poster_studio/exports.py')
NEW=('visual_poster_studio/session.py','visual_poster_studio/recovery.py','visual_poster_tests/test_reorder.py','visual_poster_tests/test_compatibility.py','visual_poster_tests/test_resume.py','visual_poster_tests/test_recovery.py','tools/run_visual_resume_tests.py','docs/VISUAL_REORDER_RESUME_CONTRACT.md')
def allowed_read(p):
    s=str(p.relative_to(ROOT));return not any(x in {'.runtime','.git','__pycache__','node_modules','style_recipes','r1_tests'} for x in p.relative_to(ROOT).parts) and not ('R1' in s or '/G1_' in s or s.startswith('tools/r1') or s.startswith('tools/run_r1'))
def hashes():return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink() and allowed_read(p)}
def guard(root,*,child=False):
    rejected=[];commands=[]
    def inside(v,dir_fd=None):
        if isinstance(v,int):return
        p=Path(os.fsdecode(v))
        if not p.is_absolute():
            if isinstance(dir_fd,int) and dir_fd>=0:
                import fcntl
                base=Path(os.fsdecode(fcntl.fcntl(dir_fd, getattr(fcntl,'F_GETPATH',50), b'\0'*1024).split(b'\0',1)[0]))
                p=base/p
            else:p=Path.cwd()/p
        if not p.resolve().is_relative_to(root):rejected.append('outside-write');raise PermissionError('Write outside fresh evidence root')
    def audit(event,args):
        if event=='open':
            path,mode,flags=args
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):inside(path)
            elif isinstance(path,(str,bytes)) and any(part in {'style_recipes','r1_tests'} for part in Path(os.fsdecode(path)).parts):raise PermissionError('R1 read outside scope')
        elif event in {'os.remove','os.rmdir'}:inside(args[0],args[1] if len(args)>1 else None)
        elif event in {'os.mkdir','os.chmod'}:inside(args[0],args[2] if len(args)>2 else None)
        elif event in {'os.truncate','os.utime'}:inside(args[0])
        elif event in {'os.rename','os.link','os.symlink'}:inside(args[0]);inside(args[1])
        elif event=='subprocess.Popen':
            argv=args[1]
            if child or list(argv[:5])!=[sys.executable,'-I','-B',str(Path(__file__).resolve()),'--child-server']:rejected.append('process');raise PermissionError('Unapproved child process')
            commands.append(list(argv))
        elif event in {'os.fork','os.forkpty','os.exec','os.system','os.posix_spawn'}:rejected.append('process');raise PermissionError('Unapproved process')
        elif event.startswith('socket.'):
            okay=event=='socket.__new__' and args[1]==2
            if event in {'socket.bind','socket.connect'}:okay=isinstance(args[1],tuple) and args[1][0]=='127.0.0.1'
            if event=='socket.getaddrinfo':okay=args[0]=='127.0.0.1'
            if not okay:rejected.append('network');raise PermissionError('Loopback only')
    sys.addaudithook(audit);return rejected,commands

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--track',choices=['all','reorder','resume','regression','layout','canvas','geometry','text'],default='all');ap.add_argument('--run-id')
    ap.add_argument('--child-server',action='store_true');ap.add_argument('--root',type=Path);ap.add_argument('--resume',action='store_true');ap.add_argument('--fault',choices=['before-primary','after-primary']);ap.add_argument('--recover-copy');ap.add_argument('--candidate',choices=['after'])
    args=ap.parse_args()
    if args.child_server:
        parent=Path(os.environ['VISUAL_EVIDENCE_ROOT']);guard(parent,child=True)
        if args.root is None or not args.root.is_relative_to(parent):raise SystemExit('Child root refused')
        from visual_poster_studio import __main__ as app
        if args.fault:
            import creative_core.persistence as persistence
            original=persistence._atomic
            def interrupted(path,data):
                if path.name=='creative.json' and args.fault=='before-primary':os.kill(os.getpid(),signal.SIGKILL)
                result=original(path,data)
                if path.name=='creative.json' and args.fault=='after-primary':os.kill(os.getpid(),signal.SIGKILL)
                return result
            persistence._atomic=interrupted
        if args.recover_copy:
            import uuid
            app.fresh_root=lambda:parent/'cases'/('recovered-'+uuid.uuid4().hex)
        sys.argv=['visual_poster_studio','--root',str(args.root),'--port','0']+(['--resume'] if args.resume else [])+(['--recover-copy',args.recover_copy,'--candidate','after'] if args.recover_copy else [])
        return app.main()
    name=args.run_id
    if not name or not name.startswith('visual-') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):raise SystemExit('Fresh visual- run ID required')
    root=ROOT/'.runtime/studio-ui'/name
    for p in (root,*root.parents):
        if p.is_symlink():raise SystemExit('Symlink refused')
    root.mkdir(exist_ok=False,mode=0o700);cases=root/'cases';cases.mkdir()
    os.environ['VISUAL_TEST_ROOT']=str(cases);os.environ['VISUAL_EVIDENCE_ROOT']=str(root)
    os.environ['VISUAL_OLD_VALIDATOR']=str(ROOT/'.runtime/studio-ui/reorder-resume-implementation-20261110-01/before/creative_core/validation.py')
    for key in ('TMPDIR','TMP','TEMP','XDG_CACHE_HOME'):os.environ[key]=str(root)
    before=hashes();rejected,commands=guard(root);started=time.monotonic()
    def deadline(*_):raise KeyboardInterrupt('60-second suite deadline')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(60)
    from test_reorder import ReorderTests
    from test_compatibility import CompatibilityTests
    from test_resume import ResumeTests,ProcessResumeTests
    from test_recovery import RecoveryTests
    classes=[]
    if args.track in ('all','reorder'):classes += [ReorderTests,CompatibilityTests]
    if args.track in ('all','resume'):classes += [ResumeTests,RecoveryTests,ProcessResumeTests]
    if args.track in ('all','text'):
        from test_text_completion import TextCompletionTests
        classes += [TextCompletionTests]
    if args.track in ('all','geometry'):
        from test_geometry import GeometryTests
        classes += [GeometryTests]
    if args.track in ('all','canvas'):
        from test_canvas_transactions import CanvasTransactionTests
        classes += [CanvasTransactionTests]
    if args.track in ('all','layout'):
        from test_layout_navigation import LayoutNavigationTests,NavigationHTTPTests
        classes += [LayoutNavigationTests,NavigationHTTPTests]
    if args.track in ('all','regression'):
        spec=importlib.util.spec_from_file_location('scoped_core_tests',ROOT/'tests/test_core.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.RUNTIME=cases
        from test_service import ServiceCase
        from test_scene import SceneTests
        from test_fonts import FontTests
        from test_http import HTTPTests
        from test_editing_ui import EditingUITests
        from test_workflow import WorkflowTests
        classes += [module.CoreTests,ServiceCase,SceneTests,FontTests,HTTPTests,EditingUITests,WorkflowTests]
    suite=unittest.TestSuite();counts={}
    for cls in classes:
        names=sorted(n for n in cls.__dict__ if n.startswith('test_'));counts[cls.__name__]=len(names);suite.addTests(cls(n) for n in names)
    with (root/'tests.txt').open('x') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
    signal.alarm(0);after=hashes();drift=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    report={'tests':result.testsRun,'by_suite':counts,'failures':len(result.failures),'errors':len(result.errors),'seconds':time.monotonic()-started,'utc':datetime.now(timezone.utc).isoformat(),'track':args.track,'source_hashes':{n:after[n] for n in MODIFIED+NEW+('visual_poster_studio/styles.css','visual_poster_studio/server.py','visual_poster_studio/editing.mjs','visual_poster_tests/test_editing.mjs','visual_poster_tests/editing_browser.mjs','visual_poster_tests/test_editing_ui.py','docs/VISUAL_EDITING_BATCH_HANDOFF.md','visual_poster_tests/test_workflow.py','docs/VISUAL_WORKFLOW_BATCH_HANDOFF.md','visual_poster_studio/layout.mjs','visual_poster_tests/test_layout.mjs','visual_poster_tests/test_layout_navigation.py','visual_poster_tests/layout_browser.mjs','docs/VISUAL_LAYOUT_BATCH_HANDOFF.md','visual_poster_studio/canvas.mjs','visual_poster_tests/test_canvas.mjs','visual_poster_tests/test_canvas_transactions.py','visual_poster_tests/canvas_browser.mjs','docs/VISUAL_CANVAS_BATCH_HANDOFF.md','visual_poster_studio/geometry.mjs','visual_poster_studio/checkpoint_restore.py','visual_poster_tests/test_geometry.py','visual_poster_tests/test_geometry.mjs','visual_poster_studio/text_layout.mjs','visual_poster_tests/test_text_layout.mjs','visual_poster_tests/test_text_completion.py','visual_poster_tests/text_completion_browser.mjs') if n in after},'baseline_drift':drift,'baseline_hashes':before,'child_commands':commands,'rejected':rejected,'real_media':False,'gate_a_changed':False,'R1_read':False}
    report['evidence_bytes']=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    with (root/'results.json').open('x') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('hashes') and k!='child_commands'}));print(root)
    return 0 if result.wasSuccessful() and not drift and not rejected and report['evidence_bytes']<128*1024*1024 else 1
if __name__=='__main__':raise SystemExit(main())
