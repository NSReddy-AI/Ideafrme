"""Targeted deterministic creative-direction checks, all writes in fresh isolated evidence."""
import argparse,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'visual_poster_tests')]
from run_visual_resume_tests import guard,hashes

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--measurements',required=True);a=p.parse_args()
 os.environ['SEMANTIC_MEASUREMENTS']=str(Path(a.measurements).resolve())
 if not a.run_id.startswith('visual-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.run_id):raise SystemExit('Fresh visual- ID required.')
 root=ROOT/'.runtime/studio-ui'/a.run_id
 for parent in (root,*root.parents):
  if parent.is_symlink():raise SystemExit('Symlink refused.')
 root.mkdir(exist_ok=False);os.environ['VISUAL_TEST_ROOT']=str(root);before=hashes();rejected,commands=guard(root,child=True)
 from test_hybrid_jobs import JobTests,JobHTTPTests
 with (root/'tests.txt').open('x') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(JobTests),JobHTTPTests('test_http_security_and_live_status')]))
 after=hashes();drift=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)];report={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'source_drift':drift,'rejected':rejected,'commands':commands,'source_hashes':{n:h for n,h in after.items() if n.startswith(('visual_poster_studio/','tools/run_hybrid_ui','visual_poster_tests/test_hybrid_jobs','docs/CREATIVE_DIRECTOR_PHASE2G'))},'R1_read':False,'media_decoding':False,'concept_generation':False}
 (root/'results.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'}));return 0 if r.wasSuccessful() and not drift and not rejected else 1
if __name__=='__main__':raise SystemExit(main())
