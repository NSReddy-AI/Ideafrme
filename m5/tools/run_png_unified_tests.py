"""Focused main-Studio media integration tests; fresh outputs only, no network."""
import argparse,json,os,sys,signal,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from run_visual_resume_tests import hashes
def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
 if not a.evidence.is_absolute() or not a.evidence.resolve().is_relative_to(ROOT/'.runtime/studio-ui') or any(x.is_symlink() for x in (a.evidence,*a.evidence.parents)):raise SystemExit('Fresh isolated evidence root required')
 a.evidence.mkdir(mode=0o700,exist_ok=False);os.environ['PNG_TEST_ROOT']=str(a.evidence);os.environ['PNG_BUILD']=str(ROOT/'.runtime/png-first-001/build-08');before=hashes();started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('60-second suite limit')));signal.alarm(60)
 from png_sandbox_tests.test_unified import UnifiedTests
 with (a.evidence/'tests.txt').open('x') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(UnifiedTests))
 signal.alarm(0);after=hashes();drift=[n for n,h in before.items() if after.get(n)!=h];v={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'seconds':time.monotonic()-started,'source_drift':drift,'source_hashes':after};(a.evidence/'results.json').write_text(json.dumps(v,indent=2));print(json.dumps({k:x for k,x in v.items() if k!='source_hashes'},indent=2));return 0 if r.wasSuccessful() and not drift else 1
if __name__=='__main__':raise SystemExit(main())
