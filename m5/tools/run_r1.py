"""Reproducible R1 acceptance runner; use the documented OS sandbox invocation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runtime/r1'
if Path.cwd()!=ROOT or any(p.is_symlink() for p in (ROOT,*ROOT.parents)):
    raise SystemExit('Run only from the real AI Studio workspace')
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
RUNTIME.mkdir(exist_ok=True)
tempfile.tempdir=str(RUNTIME)
for key in ('TMPDIR','TMP','TEMP','XDG_CACHE_HOME'):
    os.environ[key]=str(RUNTIME)
violations=[]
allowed_executables={str(Path(sys.executable).resolve()),str(Path(shutil.which('node')).resolve())}


def local_write(path):
    if isinstance(path,int):return
    p=Path(os.fsdecode(path)).absolute().resolve()
    if not (p.is_relative_to(RUNTIME) or p.is_relative_to(ROOT/'r1_data')):
        violations.append({'event':'write-outside-R1-data','path':str(p)})
        raise PermissionError('R1 audit: writes restricted to R1 runtime/data')


def audit(event,args):
    if event=='open':
        path,mode,flags=args
        if (mode and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            # Relative names with dir_fd are confined by Store's held workspace handles;
            # the OS sandbox independently enforces their actual write destinations.
            if isinstance(path,(str,bytes)) and not Path(os.fsdecode(path)).is_absolute():return
            local_write(path)
    elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.truncate','os.utime'):
        if Path(os.fsdecode(args[0])).is_absolute():local_write(args[0])
    elif event in ('os.rename','os.link'):
        for p in args[:2]:
            if Path(os.fsdecode(p)).is_absolute():local_write(p)
    elif event=='os.symlink':local_write(args[1])
    elif event in ('socket.connect','socket.bind','os.system','os.exec','os.posix_spawn'):
        violations.append(event);raise PermissionError('R1 audit: network/unsupported process denied')
    elif event=='subprocess.Popen':
        executable,argv,_,_=args
        resolved=shutil.which(os.fsdecode(executable))
        if not resolved or str(Path(resolved).resolve()) not in allowed_executables:
            violations.append('unexpected-executable');raise PermissionError('R1 audit: unexpected executable')


sys.addaudithook(audit)
start=time.monotonic()
log=(RUNTIME/'latest-tests.txt').open('w')
class Tee:
    def write(self,value):log.write(value);sys.stdout.write(value)
    def flush(self):log.flush();sys.stdout.flush()
suite=unittest.defaultTestLoader.discover(str(ROOT/'r1_tests'),pattern='test_*.py',top_level_dir=str(ROOT))
result=unittest.TextTestRunner(stream=Tee(),verbosity=2).run(suite)
log.close()
baseline=json.loads((RUNTIME/'protected-baseline.json').read_text())
changed=[name for name,h in baseline.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
node=subprocess.run(['node','--version'],stdout=subprocess.PIPE,check=True,timeout=10).stdout.decode().strip()
sources=[p for folder in ('style_recipes','r1_tests') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
sources += [ROOT/'tools/r1_canonical.mjs',ROOT/'tools/run_r1.py']
report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
            elapsed_seconds=round(time.monotonic()-start,3),python=sys.version,node=node,
            platform=' '.join(os.uname()),architecture=os.uname().machine,audit_violations=violations,
            protected_baseline_files=len(baseline),protected_changed=changed,
            source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},
            command="/usr/bin/sandbox-exec -f docs/R1_TEST_ISOLATION.sb python3 -B tools/run_r1.py",
            limitations=['ENOSPC fault injection; host disk was not exhausted',
                         'Real process termination and OS sync probes, not physical power-loss certification',
                         'Single trusted local actor; no cryptographic authentication',
                         'No independent clean runtime rebuild or G7 release acceptance'])
(RUNTIME/'acceptance-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('Evidence: .runtime/r1/acceptance-results.json')
raise SystemExit(0 if result.wasSuccessful() and not violations and not changed else 1)
