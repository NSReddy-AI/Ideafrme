"""Fresh-root, write-audited metadata library tests. No media decoders or subprocesses."""
import argparse,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(ROOT/'tools'),str(ROOT/'visual_poster_tests')]
from run_visual_resume_tests import guard,hashes

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args()
 if not a.run_id.startswith('visual-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in a.run_id):raise SystemExit('Fresh visual- ID required.')
 root=ROOT/'.runtime/studio-ui'/a.run_id
 for parent in (root,*root.parents):
  if parent.is_symlink():raise SystemExit('Symlink refused.')
 root.mkdir(exist_ok=False);os.environ['VISUAL_TEST_ROOT']=str(root);before=hashes();rejected,commands=guard(root,child=True)
 from test_brands import BrandTests
 with (root/'tests.txt').open('x') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BrandTests))
 after=hashes();drift=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)];report={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'source_drift':drift,'rejected':rejected,'commands':commands,'source_hashes':{n:h for n,h in after.items() if n.startswith(('visual_poster_studio/','tools/run_brand','visual_poster_tests/test_brands','docs/BRAND_ASSET_FOUNDATION_CONTRACT'))},'R1_read':False,'real_media':False}
 (root/'results.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'}));return 0 if r.wasSuccessful() and not drift and not rejected else 1
if __name__=='__main__':raise SystemExit(main())
