"""Explicit verified pair recovery to a fresh session; never repairs a source project."""
import argparse,copy
from pathlib import Path
from creative_core.document import canonical
from studio_manual_ui.service import project_id,UIError,read,MAX_DOCUMENT
from .session import exclusive,sync_directory
from .service import VisualStudio
from .project_bindings import sha,check
from .__main__ import fresh_root

def recover(source,identity,commit,destination,acknowledge=False):
 check(acknowledge is True,'Explicit acknowledgement required: selected pair excludes subsequent changes.')
 identity=project_id(identity);original=VisualStudio(source,resume=True)
 try:
  pair=original.pairs.chain(identity,commit);doc=copy.deepcopy(pair['document']);binding=pair['binding'];doc['approvals']=[];doc['revision']+=1
  target=VisualStudio(destination)
  try:
   (destination/'projects'/identity).mkdir(mode=0o700,exist_ok=False)
   # Retain the selected source ancestry verbatim as non-active recovery evidence.
   history=[];cursor=commit;size=0
   while cursor:
    v=original.pairs.pair(identity,cursor);files={}
    source_dir=original.pairs.directory(identity)/'commits'/cursor
    for name in ('creative.json','binding.json','manifest.json','origin-binding.json'):
     if (source_dir/name).exists():
      raw=read(source_dir/name,MAX_DOCUMENT if name=='creative.json' else 65536);files[name]=raw;size+=len(raw)
    history.append((cursor,files));cursor=v['manifest']['parent']
   target.journal.reserve(size+len(history)*8192)
   if not target.pairs.root.exists():target.pairs.root.mkdir(mode=0o700);sync_directory(destination)
   directory=target.pairs.directory(identity);directory.mkdir(mode=0o700);sync_directory(target.pairs.root)
   archive=directory/'origin-history';archive.mkdir(mode=0o700);sync_directory(directory)
   for name,files in history:
    folder=archive/name;folder.mkdir(mode=0o700);sync_directory(archive)
    for filename,raw in files.items():exclusive(folder/filename,raw,0o444)
   origin={'session_id':binding['session_id'],'project_id':identity,'commit':commit,'binding_hash':sha(canonical(binding))}
   new=target.pairs.new(identity,binding['brand'],binding['brief'],origin);target.pairs.commit(identity,doc,new,None,origin_raw=canonical(binding));target.pairs.install(target.manual,identity,doc)
  finally:target.close()
 finally:original.close()
 return destination

def main():
 p=argparse.ArgumentParser(description='Recover one complete document/binding pair into a NEW session.')
 p.add_argument('--session',type=Path,required=True);p.add_argument('--project',required=True);p.add_argument('--commit',required=True);p.add_argument('--acknowledge-excludes-subsequent-edits',action='store_true');a=p.parse_args()
 try:print(recover(a.session,a.project,a.commit,fresh_root(),a.acknowledge_excludes_subsequent_edits));return 0
 except (ValueError,OSError) as e:print('Recovery refused: '+str(e));return 2
if __name__=='__main__':raise SystemExit(main())
