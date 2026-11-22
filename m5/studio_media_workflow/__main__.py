"""Explicit quarantined CLI. No imports, processing, rendering, migration or automatic recovery."""
import argparse,json
from pathlib import Path
from .store import Store
from .containment import status
from visual_poster_studio.brands import Store as Library

def main():
 p=argparse.ArgumentParser(description='Media-workflow quarantine foundation; processing is unqualified/disabled.')
 p.add_argument('command',choices=['status','new','inspect','admit','process','candidates','recover-copy']);p.add_argument('--root',type=Path);p.add_argument('--library',type=Path);p.add_argument('--brand');p.add_argument('--name',default='Pending media');p.add_argument('--topic',default='Pending media');p.add_argument('--purpose',default='');p.add_argument('--audience',default='');p.add_argument('--asset');p.add_argument('--format',choices=['png','svg','ttf','otf']);p.add_argument('--expected-head');p.add_argument('--commit');p.add_argument('--destination',type=Path);p.add_argument('--acknowledge',action='store_true');a=p.parse_args();store=None
 try:
  if a.command=='status':print(json.dumps(status(),indent=2));return 2
  if a.root is None:p.error('--root required; no automatic directory/session selection')
  library=Library(a.library) if a.library else None
  store=Store(a.root,create=a.command=='new',library=library,name=a.name,fields={'purpose':a.purpose,'topic':a.topic,'audience':a.audience,'format':'poster','instructions':''} if a.command=='new' else None,brand_hash=a.brand)
  if a.command in ('new','inspect'):value={'head':store.head_token(),'workflow':store.current(),'processing_enabled':False}
  elif a.command=='admit':value={'head':store.admit(a.asset,a.format,a.expected_head),'processing_enabled':False}
  elif a.command=='process':store.request_processing(a.asset);raise AssertionError('No processing boundary implemented')
  elif a.command=='candidates':value={'candidates':store.candidates()}
  else:
   if a.destination is None:p.error('--destination required')
   value={'recovery_copy':str(store.recover_copy(a.commit,a.destination,acknowledge=a.acknowledge)),'processing_enabled':False}
  print(json.dumps(value,ensure_ascii=False,indent=2));return 0
 except (ValueError,OSError) as exc:print(json.dumps({'error':getattr(exc,'code','media-storage'),'detail':str(exc),'automatic_repair':False,'processing_enabled':False}));return 2
 finally:
  if store:store.close()
if __name__=='__main__':raise SystemExit(main())
