"""Bounded metadata-only tests, no worker/codec/network/protected-file access."""
import argparse,json,os,signal,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'media_workflow_tests')]
from run_visual_resume_tests import guard,hashes

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args()
 if not a.run_id.startswith('visual-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.run_id):raise SystemExit('Fresh visual- run ID required.')
 root=ROOT/'.runtime/studio-ui'/a.run_id
 for q in (root,*root.parents):
  if q.is_symlink():raise SystemExit('Symlink refused')
 root.mkdir(exist_ok=False,mode=0o700);os.environ['MEDIA_TEST_ROOT']=str(root);before=hashes();rejected,commands=guard(root,child=True)
 def timeout(*_):raise RuntimeError('30-second test deadline')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(30)
 from test_boundary import BoundaryTests
 started=time.monotonic()
 with (root/'tests.txt').open('x') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryTests))
 signal.alarm(0);after=hashes();drift=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
 report={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'seconds':time.monotonic()-started,'source_drift':drift,'rejected':rejected,'child_commands':commands,'media_decoding':False,'worker_execution':False,'containment_qualified':False,'live_placement':'NO-GO','source_hashes':{n:h for n,h in after.items() if n.startswith(('studio_media_workflow/','media_workflow_tests/','tools/run_media_workflow'))}}
 (root/'results.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'}));return 0 if r.wasSuccessful() and not drift and not rejected and not commands else 1
if __name__=='__main__':raise SystemExit(main())
