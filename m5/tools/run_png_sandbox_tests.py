"""Targeted no-network suite with fresh evidence and source association."""
import argparse,hashlib,json,os,signal,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'png_sandbox_tests')]
from run_visual_resume_tests import hashes
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--track',choices=['security','workflow','additional'],default='security');a=p.parse_args()
 for path in (a.build,a.evidence):
  if not path.is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(ROOT/'.runtime'):raise SystemExit('Isolated absolute runtime paths required')
 a.evidence.mkdir(mode=0o700,exist_ok=False);os.environ['PNG_BUILD']=str(a.build);os.environ['PNG_TEST_ROOT']=str(a.evidence)
 before=hashes();started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('Bounded 45 second suite deadline')));signal.alarm(45)
 from png_sandbox_tests.test_security import SecurityTests
 case=SecurityTests
 if a.track=='workflow':
  from png_sandbox_tests.test_workflow import WorkflowTests
  case=WorkflowTests
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(case)
 if a.track=='additional':suite=unittest.TestSuite(SecurityTests(n) for n in ('test_running_decode_cancellation_confirms_no_process','test_native_wall_alarm_without_input','test_scratch_accounting_conservative_bound','test_unconfirmed_termination_faults_supervisor'))
 with (a.evidence/'tests.txt').open('x') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 signal.alarm(0);after=hashes();drift=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
 report={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'seconds':time.monotonic()-started,'source_drift':drift,'source_hashes':{n:h for n,h in after.items() if n.startswith(('studio_png_sandbox/','png_sandbox_tests/','tools/build_png','tools/run_png'))},'build':json.loads((a.build/'build.json').read_text()),'metrics':getattr(SecurityTests,'metrics',[]),'live_placement_enabled':False,'host_memory_kernel_enforced':False}
 (a.evidence/'results.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('source_hashes','build','metrics')},indent=2));return 0 if r.wasSuccessful() and not drift else 1
if __name__=='__main__':raise SystemExit(main())
