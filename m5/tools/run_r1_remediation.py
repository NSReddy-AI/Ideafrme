"""Targeted remediation run. Redirect legacy evidence without editing legacy runners."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence',required=True)
args=parser.parse_args()
EVIDENCE=Path(args.evidence).absolute()
if Path.cwd()!=ROOT or not EVIDENCE.is_relative_to(ROOT/'.runtime/r1') or not EVIDENCE.name.startswith('remediation-'):
    raise SystemExit('Use a fresh remediation-* evidence directory inside .runtime/r1')
if not (EVIDENCE/'before.json').is_file() or (EVIDENCE/'tests.txt').exists():
    raise SystemExit('Fresh pre-recorded run required; never overwrite a prior test run')
os.environ['R1_REMEDIATION_EVIDENCE']=str(EVIDENCE)
for key in ('TMPDIR','TMP','TEMP','XDG_CACHE_HOME'):
    os.environ[key]=str(EVIDENCE)
import tempfile
tempfile.tempdir=str(EVIDENCE)
from style_recipes.store import Store
import r1_tests.test_contracts as contracts
import r1_tests.test_persistence as persistence
import r1_tests.test_targeted_remediation as targeted

legacy_names=('cross-language-results.json','filesystem-qualification.json',
              'isolation-results.json','persistence-fault-results.json')
redirects={ROOT/'.runtime/r1'/name:EVIDENCE/name for name in legacy_names}
original_write_text=Path.write_text


def isolated_write_text(path,*a,**kw):
    destination=redirects.get(path.absolute(),path.absolute())
    if not destination.is_relative_to(EVIDENCE):
        raise PermissionError('Attempt to overwrite evidence outside this remediation run')
    return original_write_text(destination,*a,**kw)


def fresh_store():
    return Store.create(EVIDENCE/'legacy-test-stores'/str(uuid4()))


before=json.loads((EVIDENCE/'before.json').read_text())
suite=unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(targeted))
suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(contracts))
suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(persistence))
start=time.monotonic()
with (EVIDENCE/'tests.txt').open('x') as log:
    class Tee:
        def write(self,text):log.write(text);sys.stdout.write(text)
        def flush(self):log.flush();sys.stdout.flush()
    with patch.object(contracts,'new_store',fresh_store),patch.object(persistence,'new_store',fresh_store),patch.object(Path,'write_text',isolated_write_text):
        result=unittest.TextTestRunner(stream=Tee(),verbosity=2).run(suite)

def changed(mapping):
    return [name for name,h in mapping.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
previous_changes=changed(before['previous_evidence_sha256'])
protected_changes=changed(before['protected_baseline'])
sources=['style_recipes/state.py','style_recipes/manual.py','r1_tests/test_targeted_remediation.py','tools/run_r1_remediation.py']
report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),elapsed_seconds=round(time.monotonic()-start,3),
            previous_evidence_changes=previous_changes,protected_baseline_changes=protected_changes,
            source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},
            command=f'/usr/bin/sandbox-exec -f {EVIDENCE}/isolation.sb python3 -B tools/run_r1_remediation.py --evidence {EVIDENCE}',
            scope='two targeted defects; existing contracts/persistence tests isolated by output redirection',
            not_run=['original CLI test with hardcoded store destination','original 55-test runner'],
            acceptance='pending user review; R2-R6 not authorized')
(EVIDENCE/'results.json').write_text(json.dumps(report,indent=2)+'\n')
print('Fresh evidence:',EVIDENCE)
raise SystemExit(0 if result.wasSuccessful() and not previous_changes and not protected_changes else 1)
