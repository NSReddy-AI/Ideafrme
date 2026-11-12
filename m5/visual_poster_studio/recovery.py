"""Append-only bounded save intents/checkpoints. Never repairs primary or previous files."""
import hashlib
from pathlib import Path
import uuid
from creative_core.document import canonical
from studio_manual_ui.service import UIError, safe, read, decode, encoded, project_id, MAX_DOCUMENT
from .session import exclusive,sync_directory

BUDGET=128*1024*1024

def sha(raw):return hashlib.sha256(raw).hexdigest()

class Journal:
    def __init__(self,root,*,resume=False):
        self.extra_usage=lambda:0;self.session=root;self.root=safe(root/'recovery');self.states={}
        if resume:
            if not self.root.is_dir():raise UIError('recovery','Recovery journal missing; no automatic initialization.')
        else:self.root.mkdir(mode=0o700);sync_directory(root)
        self.usage()
    def usage(self):
        total=0;count=0
        trees=[self.root]
        projects=safe(self.session/'projects')
        for p in projects.iterdir():
            safe(p);project_id(p.name)
            q=p/'legacy-checkpoints'
            if q.exists() or q.is_symlink():trees.append(safe(q))
        for tree in trees:
            for p in tree.rglob('*'):
                safe(p);count+=1
                if count>8192:raise UIError('recovery-limit','Recovery entry limit exceeded.')
                if p.is_file():total+=p.stat().st_size
                if total>BUDGET:raise UIError('recovery-limit','Recovery storage exceeds 128 MiB; writes blocked.')
        total+=self.extra_usage()
        if total>BUDGET:raise UIError('recovery-limit','Combined recovery/checkpoint/binding storage exceeds 128 MiB.')
        return total
    def reserve(self,n):
        if self.usage()+n>BUDGET:raise UIError('recovery-limit','128 MiB recovery budget exhausted; save refused.')
    def checkpoint(self,identity,doc):
        project_id(identity);raw=canonical(doc)+b'\n';digest=sha(raw)
        if len(raw)>MAX_DOCUMENT:raise UIError('limit','Checkpoint document exceeds limit.')
        parent=safe(self.session/'projects'/identity/'legacy-checkpoints');path=parent/(digest+'.json')
        if path.exists():
            if read(path,MAX_DOCUMENT)!=raw or path.stat().st_mode&0o222:raise UIError('checkpoint','Checkpoint identity or permissions changed.')
            return digest
        self.reserve(len(raw)+4096)
        if not parent.exists():parent.mkdir(mode=0o700);sync_directory(parent.parent)
        exclusive(path,raw,0o444)
        if read(path,MAX_DOCUMENT)!=raw:raise UIError('checkpoint','Checkpoint readback failed.')
        return digest
    def _directories(self,identity):
        parent=safe(self.root/project_id(identity))
        if not parent.exists():return []
        dirs=[]
        for p in parent.iterdir():
            safe(p)
            if not p.is_dir() or len(p.name)!=8 or not p.name.isascii() or not p.name.isdigit():raise UIError('recovery','Unknown journal entry.')
            dirs.append(p)
        return sorted(dirs)
    def inspect(self,identity):
        """Exact-byte primary comparison; unfinished/unknown states block mutation."""
        identity=project_id(identity);dirs=self._directories(identity)
        primary=safe(self.session/'projects'/identity/'creative.json')
        raw=read(primary,MAX_DOCUMENT) if primary.exists() else None
        last=None
        for index,p in enumerate(dirs,1):
            try:
                intent_raw=read(p/'intent.json',4096);intent=decode(intent_raw)
                if int(p.name)!=index:raise ValueError('generation gap')
                if set(intent)!={'version','project_id','generation','before_sha256','after_sha256','revision'} or intent['version']!=1 or intent['project_id']!=identity or intent['generation']!=int(p.name):raise ValueError('intent')
                if intent['before_sha256']!=(sha(last) if last is not None else None):raise ValueError('broken save ancestry')
                after=read(p/'after.json',MAX_DOCUMENT)
                if sha(after)!=intent['after_sha256']:raise ValueError('after hash')
                if intent['before_sha256'] is not None and sha(read(p/'before.json',MAX_DOCUMENT))!=intent['before_sha256']:raise ValueError('before hash')
                complete=decode(read(p/'complete.json',4096))
                if complete!={'intent_sha256':sha(intent_raw),'after_sha256':sha(after)}:raise ValueError('completion')
                last=after
            except (OSError,ValueError,UIError):
                state={'state':'interrupted-save','generation':p.name,'primary':'unknown','detail':'No automatic repair; explicit recovery copy required.'}
                try:
                    intent=decode(read(p/'intent.json',4096));actual=sha(raw) if raw is not None else None
                    state['primary']='candidate' if actual==intent.get('after_sha256') else 'previous' if actual==intent.get('before_sha256') else 'unknown'
                except (OSError,ValueError,UIError):pass
                self.states[identity]=state;return state
        if dirs and raw!=last:state={'state':'primary-conflict','detail':'Primary differs from last completed save.'}
        elif raw is not None and not dirs:state={'state':'untracked-document','detail':'Primary has no journal record.'}
        else:state={'state':'clean','saved':raw is not None}
        self.states[identity]=state;return state
    def save(self,manual,request):
        identity=request['project_id'];state=self.inspect(identity)
        if state['state']!='clean':raise UIError('recovery-required','Interrupted or conflicting save; explicit recovery required.',409)
        doc=manual.document(identity)
        if type(request.get('expected_revision'))!=int or request['expected_revision']!=doc['revision']:raise UIError('conflict','Stale save revision.',409)
        after=canonical(doc)+b'\n';primary=safe(self.session/'projects'/identity/'creative.json')
        before=read(primary,MAX_DOCUMENT) if primary.exists() else None
        if before==after:
            self.reserve(1);return manual.action(request)
        self.reserve(len(after)+len(before or b'')+8192)
        parent=safe(self.root/identity)
        if not parent.exists():parent.mkdir(mode=0o700);sync_directory(self.root)
        dirs=self._directories(identity);generation=int(dirs[-1].name)+1 if dirs else 1
        if generation>99999999:raise UIError('recovery-limit','Journal generation exhausted.')
        path=parent/f'{generation:08d}';path.mkdir(mode=0o700);sync_directory(parent)
        intent={'version':1,'project_id':identity,'generation':generation,'before_sha256':sha(before) if before is not None else None,'after_sha256':sha(after),'revision':doc['revision']}
        try:
            if before is not None:exclusive(path/'before.json',before,0o444)
            exclusive(path/'after.json',after,0o444)
            intent_raw=encoded(intent)+b'\n';exclusive(path/'intent.json',intent_raw,0o444)
            result=manual.action(request)
            if read(primary,MAX_DOCUMENT)!=after:raise UIError('recovery','Saved primary readback differs.')
            sync_directory(primary.parent)
            exclusive(path/'complete.json',encoded({'intent_sha256':sha(intent_raw),'after_sha256':sha(after)})+b'\n',0o444)
            return result
        except (OSError,UIError):
            self.states[identity]={'state':'interrupted-save','detail':'Save durability unconfirmed; explicit recovery required.'}
            raise UIError('recovery-required','Save interrupted or synchronization failed; no automatic repair.',409)
    def candidate(self,identity,which):
        if which not in {'before','after'}:raise UIError('recovery','Choose before or after explicitly.')
        dirs=self._directories(identity)
        if not dirs:raise UIError('recovery','No retained save candidate.')
        p=dirs[-1];intent=decode(read(p/'intent.json',4096));raw=read(p/(which+'.json'),MAX_DOCUMENT)
        if intent.get(which+'_sha256')!=sha(raw):raise UIError('recovery','Recovery candidate hash mismatch.')
        return raw
