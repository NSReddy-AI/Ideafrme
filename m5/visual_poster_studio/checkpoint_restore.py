"""Explicit checkpoint restore to a fresh Visual session; never repairs the source."""
import argparse
import hashlib
import re
from pathlib import Path
import creative_core as core
from studio_manual_ui.service import decode,manual_subset,project_id,UIError
from .service import VisualStudio
from .session import read,safe,exclusive
from .__main__ import fresh_root

def restore(source,identity,digest,destination,acknowledge=False):
    if acknowledge is not True:raise UIError('acknowledgement','Restoration excludes all edits after the checkpoint; explicit acknowledgement required.')
    identity=project_id(identity)
    if type(digest)!=str or not re.fullmatch('[0-9a-f]{64}',digest):raise UIError('checkpoint','Invalid checkpoint hash.')
    if (source/'bound-projects'/identity).exists():raise UIError('bound-recovery','Bound project requires paired recovery; raw checkpoint restore would lose its context.')
    with _opened(source) as studio:
        path=safe(source/'projects'/identity/'legacy-checkpoints'/(digest+'.json'))
        info=path.stat();raw=read(path,8*1024*1024)
        if info.st_nlink!=1 or info.st_mode&0o222 or hashlib.sha256(raw).hexdigest()!=digest:raise UIError('checkpoint','Immutable checkpoint verification failed.')
        doc=decode(raw);manual_subset(doc);core.validate(doc,source/'projects'/identity)
        if doc['id']!=identity:raise UIError('checkpoint','Project identity mismatch.')
        # Legacy checkpoints may rely on older checkpoints for future explicit upgrades;
        # validation of historical snapshots does not rewrite those dependencies.
        target=VisualStudio(destination)
        try:
            (destination/'projects'/identity).mkdir(mode=0o700)
            target.manual._working[identity]=doc
            target.action({'project_id':identity,'expected_revision':doc['revision'],'action':'save'})
            import json
            exclusive(destination/'checkpoint-origin.json',json.dumps({'source_session':str(source),'project_id':identity,'checkpoint_sha256':digest,'subsequent_edits_excluded':True},sort_keys=True).encode())
        finally:target.close()
    return destination

from contextlib import contextmanager
@contextmanager
def _opened(root):
    studio=VisualStudio(root,resume=True)
    try:yield studio
    finally:studio.close()

def main():
    p=argparse.ArgumentParser(description='Restore a checkpoint into a NEW session. Subsequent edits are excluded.')
    p.add_argument('--session',type=Path,required=True);p.add_argument('--project',required=True);p.add_argument('--checkpoint',required=True)
    p.add_argument('--acknowledge-lost-subsequent-edits',action='store_true');a=p.parse_args()
    destination=fresh_root();restore(a.session,a.project,a.checkpoint,destination,a.acknowledge_lost_subsequent_edits);print(destination)
if __name__=='__main__':main()
