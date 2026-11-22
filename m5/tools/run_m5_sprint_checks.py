"""Focused product-entry checks. Fresh local output only; no model/decoder execution."""
import argparse,json,sys,uuid,signal,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from visual_poster_studio.service import VisualStudio
from visual_poster_studio import product
from studio_manual_ui.service import UIError
from creative_core.document import canonical
from visual_poster_studio.brands import Store

def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();root=a.evidence
 if not root.is_absolute() or not root.resolve().is_relative_to(ROOT/'.runtime/studio-ui') or any(x.is_symlink() for x in (root,*root.parents)):raise SystemExit('Fresh runtime root required')
 root.mkdir(mode=0o700,exist_ok=False);s=VisualStudio(root/'visual-checks');server=SimpleNamespace(studio=s,brand_root=root/'brands');checks=[]
 def check(name,condition):
  if not condition:raise AssertionError(name)
  checks.append(name)
 try:
  base=dict(mode='quick',name='',idea='Read together / కలిసి చదువుదాం / e\u0301',language='te',brand_hash=None,purpose='',audience='',instructions='',direction='')
  v=product.create(server,base);identity=v['project']['project_id'];check('exact mixed Unicode',v['project']['content'][0]['text']==base['idea']);check('explicit defaults',v['resolutions']['purpose']=='disclosed-default');check('created saved',v['project']['saved'] and not v['project']['dirty']);before=canonical(s.manual.document(identity));h=product.history(server,dict(project_id=identity,media_id=None));check('read-only history',canonical(s.manual.document(identity))==before and h['project_id']==identity)
  for mode in ('guided','professional'):
   x=product.create(server,{**base,'mode':mode,'purpose':'Invite readers','audience':'Families','direction':'Open space'});check(mode+' same contract',x['project']['binding']['record']['brief']['purpose']=='Invite readers')
  try:product.create(server,{**base,'path':'/tmp/escape'})
  except UIError:check('arbitrary fields rejected',True)
  else:raise AssertionError('unexpected field accepted')
  try:product.create(server,{**base,'mode':'unknown'})
  except UIError:check('unknown mode rejected',True)
  else:raise AssertionError('unknown mode accepted')
  e=v['project']['elements'][0]['id'];x=s.action(dict(project_id=identity,expected_revision=v['project']['revision'],action='edit_text',element_id=e,text=base['idea']+'!'));s.action(dict(project_id=identity,expected_revision=x['revision'],action='save'));expected=canonical(s.manual.document(identity));s.close();s=VisualStudio(root/'visual-checks',resume=True);s.brand_library=Store(server.brand_root);check('restart exact document/history',canonical(s.manual.document(identity))==expected);check('restart exact text',s.view(identity)['content'][0]['text']==base['idea']+'!')
 finally:s.close()
 from studio_png_sandbox.controller import file_sha,sha
 import io
 raw=b'pinned-runtime-byte-check'*10000
 class Bounded(io.BytesIO):
  def read(self,n=-1):
   if not 0<n<=65536:raise AssertionError('Unbounded identity read')
   return super().read(n)
 stream=Bounded(raw);check('bounded artifact identity hashing',file_sha(SimpleNamespace(open=lambda mode:stream))==sha(raw))
 result={'passed':len(checks),'checks':checks};(root/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())
