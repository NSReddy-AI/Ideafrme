"""Standalone explicit CLI: no change to the accepted Studio launch path."""
import argparse,json,uuid
from pathlib import Path
from .controller import Decoder
from .workflow import Workflow
from visual_poster_studio.brands import Store as Library
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--port',type=int,default=8776);p.add_argument('--create',action='store_true');p.add_argument('--brand');p.add_argument('--text');p.add_argument('--language',choices=['en','te'],default='en');p.add_argument('--acknowledge-version-2',action='store_true');a=p.parse_args()
 decoder=Decoder(a.build);library=Library(a.library)
 if a.create:
  if not a.acknowledge_version_2 or not a.brand or not a.text:p.error('Creation requires approved brand, exact text and explicit version-2 acknowledgement')
  from studio_manual_ui.service import Studio
  from visual_poster_studio.binding_workflow import pin
  from types import SimpleNamespace
  from .controller import ROOT
  manual=Studio(ROOT/'.runtime/studio-ui'/('png-source-'+uuid.uuid4().hex))
  try:v=manual.create({'name':'PNG brand poster','text':a.text,'language':a.language});doc=manual.document(v['project_id'])
  finally:manual.close()
  binding={'format':'studio-project-binding@1','version':1,'binding_id':str(uuid.uuid4()),'session_id':str(uuid.uuid4()),'project_id':doc['id'],'revision':1,'parent':None,'brand':pin(SimpleNamespace(brand_library=library),a.brand),'brief':{'purpose':'','topic':a.text,'audience':'','format':'poster','instructions':''},'origin':None}
  workflow=Workflow(a.root,library,decoder,base=doc,binding=binding,acknowledge=True)
 else:workflow=Workflow(a.root,library,decoder)
 from .server import serve
 try:serve(workflow,a.port)
 finally:workflow.close()
if __name__=='__main__':main()
