"""Explicit fresh startup or Visual-owned resume; no legacy adoption or media launch."""
import argparse
import errno
from datetime import datetime,timezone
import json
from pathlib import Path
import uuid
from studio_manual_ui.service import RUNTIME,decode,manual_subset,project_id
from .service import VisualStudio
from .server import Server
from .session import exclusive
import creative_core as core

def fresh_root():return RUNTIME/('visual-session-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766)
    p.add_argument('--root',type=Path);p.add_argument('--resume',action='store_true')
    p.add_argument('--recover-copy',metavar='PROJECT_ID');p.add_argument('--candidate',choices=['before','after'])
    args=p.parse_args()
    if args.resume and args.root is None:p.error('--resume requires an absolute --root')
    if bool(args.recover_copy)!=bool(args.candidate) or (args.recover_copy and not args.resume):p.error('--recover-copy and --candidate require --resume and each other')
    root=args.root or fresh_root();studio=server=None
    try:
        studio=VisualStudio(root,resume=args.resume)
        if args.recover_copy:
            identity=project_id(args.recover_copy);raw=studio.journal.candidate(identity,args.candidate)
            doc=decode(raw);manual_subset(doc);core.validate(doc,root/'projects'/identity)
            if doc['id']!=identity:raise ValueError('Recovery identity mismatch')
            old=root;studio.close();studio=None;root=fresh_root();studio=VisualStudio(root)
            directory=root/'projects'/identity;directory.mkdir(mode=0o700)
            studio.manual._working[identity]=doc
            studio.action({'project_id':identity,'expected_revision':doc['revision'],'action':'save'})
            exclusive(root/'recovered-from.json',json.dumps({'source_session':str(old),'project_id':identity,'candidate':args.candidate},sort_keys=True).encode())
        server=Server(studio,args.port)
        print(json.dumps({'url':server.origin,'runtime_root':str(root),'analysis':'OFF','mode':'draft-visual','resumed':args.resume and not bool(args.recover_copy),'session_status':studio.status()}),flush=True)
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
    except Exception as exc:
        if isinstance(exc,OSError) and exc.errno==errno.EADDRINUSE:
            message={'error':'port-in-use','detail':'Loopback port unavailable; use --port 0 or a free port. Session data was not repaired or replaced.'}
        else:message={'error':getattr(exc,'code','startup'),'detail':getattr(exc,'detail','Startup failed; no automatic repair.')}
        print(json.dumps(message),flush=True);return 2
    finally:
        if server:server.server_close()
        if studio:studio.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
