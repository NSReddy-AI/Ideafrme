"""Workspace-confined immutable records, durable HEAD publication and explicit recovery."""
from contextlib import contextmanager
from copy import deepcopy
import ctypes
import errno
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import sys
from uuid import uuid4
from .canonical import loads, canonical, digest, envelope, ref, require, StyleError
from .schema import FORMATS, validate, reference, shape
from .state import Snapshot, SnapshotView, kind, refs

WORKSPACE = Path(__file__).resolve().parent.parent
SUPPORTED = ('manual-style-authoring',)


def common(typ, actor, now):
    return dict(format=FORMATS[typ],record_id=str(uuid4()),created_at=now,created_by=actor)


class Store:
    """Single-user store. Test fault hook is never exposed to imported JSON or CLI."""
    def __init__(self,path, fault=None):
        self.path=Path(path).absolute()
        require('..' not in self.path.parts,'storage','$','parent traversal forbidden')
        try:
            relative=self.path.relative_to(WORKSPACE)
        except ValueError:
            raise StyleError('storage','$','store must remain inside AI Studio')
        require(relative.parts and (relative.parts[0]=='r1_data' or relative.parts[:2]==('.runtime','r1')),
                'storage','$','store must be inside r1_data or .runtime/r1')
        self.relative=relative
        self.fault=fault or (lambda stage:None)
        self.fds={}
        self._published=False
        self.qualified=False
        self.qualified_identity=None

    def _hit(self,stage):
        self.fault(stage)

    def _root(self):
        fd=os.open(WORKSPACE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for name in self.relative.parts:
                new=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                os.close(fd);fd=new
            return fd
        except BaseException:
            os.close(fd);raise

    @classmethod
    def create(cls,path):
        obj=cls(path)
        # Walk and create parents with no-follow handles; final root must be new.
        fd=os.open(WORKSPACE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for i,name in enumerate(obj.relative.parts):
                last=i==len(obj.relative.parts)-1
                try:
                    os.mkdir(name,0o700,dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    require(not last,'conflict','$','store already exists; never initialize populated store')
                new=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                os.close(fd);fd=new
            for name in ('records','staging','quarantine'):
                os.mkdir(name,0o700,dir_fd=fd)
            lock=os.open('.writer.lock',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
            os.fsync(lock);os.close(lock);os.fsync(fd)
        finally:
            os.close(fd)
        # Qualification explicitly performs real primitive probes within this new store.
        obj.qualify()
        return obj

    @contextmanager
    def opened(self,write=False):
        require(not self.fds,'storage','$','nested store handle use')
        try:
            self.fds['root']=self._root()
            for name in ('records','staging','quarantine'):
                self.fds[name]=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=self.fds['root'])
            if write:
                require(self.qualified,'storage','$','filesystem qualification required before writes')
                require(self._inode(self.fds['root'])==self.qualified_identity,
                        'storage','$','qualified store identity changed; requalification required')
                self.fds['lock']=os.open('.writer.lock',os.O_RDWR|os.O_NOFOLLOW,dir_fd=self.fds['root'])
                self._regular(self.fds['lock'])
                try:
                    fcntl.flock(self.fds['lock'],fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError as e:
                    raise StyleError('conflict','$','writer busy; lock not stolen') from e
            self._identity()
            yield
        finally:
            for fd in reversed(list(self.fds.values())):
                os.close(fd)
            self.fds={}

    def _identity(self):
        fd=self._root()
        try:
            require(self._inode(fd)==self._inode(self.fds['root']),'storage','$','root identity changed')
        finally:
            os.close(fd)
        for name,fd in self.fds.items():
            if name=='root':
                continue
            require(os.fstat(fd).st_dev==os.fstat(self.fds['root']).st_dev,
                    'storage','$','store children must share qualified local filesystem')
            st=os.stat('.writer.lock' if name=='lock' else name,dir_fd=self.fds['root'],follow_symlinks=False)
            require((st.st_dev,st.st_ino)==self._inode(fd),'storage','$','store directory/lock replaced')

    @staticmethod
    def _inode(fd):
        st=os.fstat(fd);return st.st_dev,st.st_ino

    @staticmethod
    def _regular(fd):
        st=os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink==1,'storage','$','regular unlinked-alias-free file required')

    def _read(self,directory,name,maximum=1048576,missing=False):
        try:
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=self.fds[directory])
        except FileNotFoundError:
            if missing:return None
            raise StyleError('storage','$','required file missing')
        try:
            self._regular(fd)
            require(os.fstat(fd).st_size<=maximum,'limit','$','file byte bound')
            data=b''
            while len(data)<=maximum:
                chunk=os.read(fd,min(65536,maximum+1-len(data)))
                if not chunk:break
                data+=chunk
            require(len(data)<=maximum,'limit','$','file grew beyond bound')
            return data
        finally:
            os.close(fd)

    def _sync(self,fd,label,directory=False):
        self._hit('before:'+label+':sync')
        os.fsync(fd)
        if not directory and sys.platform=='darwin':
            fcntl.fcntl(fd,getattr(fcntl,'F_FULLFSYNC',51))
        self._hit('after:'+label+':sync')

    def _exclusive(self,directory,name,data,label):
        self._hit('before:'+label+':create')
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fds[directory])
        try:
            self._hit('after:'+label+':create')
            halfway=max(1,len(data)//2)
            for chunk in (data[:halfway],data[halfway:]):
                self._hit('before:'+label+':write')
                while chunk:
                    n=os.write(fd,chunk)
                    require(n>0,'storage','$','short write')
                    chunk=chunk[n:]
                self._hit('after:'+label+':write')
            self._sync(fd,label)
        finally:
            os.close(fd)
        require(self._read(directory,name)==data,'storage','$','reopen bytes differ')

    def _record(self,p,label):
        validate(p);data=envelope(p);name=digest(p)+'.json'
        # Real sibling staging is write-once and never authoritative.
        temp=str(uuid4())+'.json'
        self._exclusive('staging',temp,data,'staging')
        try:
            self._exclusive('records',name,data,label)
        except FileExistsError:
            require(self._read('records',name)==data,'storage','$','existing immutable record corrupt')
        os.unlink(temp,dir_fd=self.fds['staging'])

    def _pointer(self,name):
        raw=self._read('root',name,1024,True)
        if raw is None:return None
        value=loads(raw,1024);reference(value)
        require(canonical(value)==raw,'schema','$','noncanonical pointer')
        return value

    def _snapshot(self,head):
        records={};active=set();size=0;identities={}
        def visit(r,depth):
            nonlocal size
            h=r['sha256']
            require(h not in active and depth<=64,'reference','$','cycle or depth overflow')
            if h in records:
                require(ref(records[h])==r,'reference','$','reference identity mismatch');return
            require(len(records)+len(active)<4096,'limit','$','closure record bound')
            raw=self._read('records',h+'.json');size+=len(raw)
            require(size<=64*1024*1024,'limit','$','closure byte bound')
            e=loads(raw);shape(e,'payload sha256');p=e['payload'];validate(p)
            require(e['sha256']==h and ref(p)==r and envelope(p)==raw,'hash','$','record bytes/hash mismatch')
            require(p['record_id'] not in identities or identities[p['record_id']]==h,'conflict','$','duplicate record identity')
            identities[p['record_id']]=h
            active.add(h)
            for child in refs(p):visit(child,depth+1)
            active.remove(h);records[h]=p
        if head:visit(head,1)
        return Snapshot(records,head)

    def read(self):
        with self.opened():
            head=self._pointer('HEAD')
            if head is None:
                require(not os.listdir(self.fds['records']) and self._pointer('PREVIOUS') is None,
                        'storage','$','missing HEAD on populated store; recovery required')
            return self._snapshot(head)

    def _replace(self,name,data,guard):
        self._identity();guard()
        temp='.'+name+'-'+str(uuid4())
        self._exclusive('root',temp,data,name.lower())
        self._identity();guard()
        self._hit('before:'+name.lower()+':replace')
        os.replace(temp,name,src_dir_fd=self.fds['root'],dst_dir_fd=self.fds['root'])
        if name=='HEAD':self._published=True
        self._hit('after:'+name.lower()+':replace')
        self._sync(self.fds['root'],name.lower()+':directory',True)

    def qualify(self):
        """Probe primitives, not power-loss certification. Only local APFS write support."""
        require(sys.platform=='darwin','storage','$','R1 writer supports local macOS APFS only')
        root=self._root()
        try:
            class FS(ctypes.Structure):
                _fields_=[('bsize',ctypes.c_uint32),('iosize',ctypes.c_int32),('counts',ctypes.c_uint64*5),
                          ('fsid',ctypes.c_int32*2),('owner',ctypes.c_uint32),('type',ctypes.c_uint32),
                          ('flags',ctypes.c_uint32),('subtype',ctypes.c_uint32),('fstype',ctypes.c_char*16),
                          ('mount',ctypes.c_char*1024),('source',ctypes.c_char*1024),('reserved',ctypes.c_uint32*8)]
            fs=FS();libc=ctypes.CDLL(None,use_errno=True)
            require(libc.fstatfs(root,ctypes.byref(fs))==0,'storage','$','filesystem query failed')
            require(fs.fstype==b'apfs' and fs.flags & 0x1000,'storage','$','only local APFS qualified')
            self.qualified_identity=self._inode(root)
        finally:os.close(root)
        self.qualified=True
        try:
            with self.opened(write=True):
                other=os.open('.writer.lock',os.O_RDWR|os.O_NOFOLLOW,dir_fd=self.fds['root'])
                try:
                    try:
                        fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError:pass
                    else:raise StyleError('storage','$','exclusive locking unavailable')
                finally:os.close(other)
                name='qualification-'+str(uuid4())
                self._exclusive('staging',name,b'qualification','qualification')
                renamed=name+'-renamed'
                os.replace(name,renamed,src_dir_fd=self.fds['staging'],dst_dir_fd=self.fds['staging'])
                self._sync(self.fds['staging'],'qualification:directory',True)
                require(self._read('staging',renamed)==b'qualification','storage','$','replace probe failed')
                os.unlink(renamed,dir_fd=self.fds['staging'])
                self._sync(self.fds['staging'],'qualification:cleanup',True)
        except BaseException:
            self.qualified=False;self.qualified_identity=None;raise
        return {'filesystem':'local APFS','file_fsync':True,'F_FULLFSYNC':True,
                'directory_fsync':True,'exclusive_lock_probe':True,'replace_reopen':True,
                'power_loss_certified':False}

    def commit(self,additions,expected,actor,now,action='save',roots=None,confirmed=False,
               verified_evidence=None,brand_classification=None):
        additions=deepcopy(additions)
        if not self.qualified:self.qualify()
        self._published=False
        try:
            with self.opened(write=True):
                old=self._pointer('HEAD');require(old==expected,'conflict','$','stale expected HEAD')
                if old is None:
                    require(not os.listdir(self.fds['records']) and self._pointer('PREVIOUS') is None,
                            'storage','$','populated store without HEAD')
                snapshot=self._snapshot(old)
                SnapshotView(snapshot,snapshot.visible).check_additions(additions,action)
                require(sum(len(envelope(p)) for p in additions)<=64*1024*1024,'limit','$','transaction bound')
                for p in additions:
                    if kind(p)=='brand' and p['parent']:
                        require(brand_classification in ('benign','adverse'),'authority','$','brand classification required')
                        require(confirmed and p['created_by']==actor,'authority','$','brand authority confirmation required')
                        if brand_classification=='adverse':
                            oldbrand=p['parent']['sha256']
                            affected=[ref(d) for d in snapshot.visible.values() if kind(d)=='dependency' and d['kind']=='brand' and d['content_sha256']==oldbrand]
                            require(all(snapshot.event(r)[1] and snapshot.event(r)[1]['state'] in ('stale','revoked') for r in affected),
                                    'dependency','$','adverse brand events must precede version save')
                        evidence=canonical(dict(brand=ref(p),parent=p['parent'],classification=brand_classification,
                                                actor=actor,confirmed_at=now))
                        self._exclusive('quarantine','brand-review-'+str(uuid4())+'.json',evidence,'brand-evidence')
                        self._sync(self.fds['quarantine'],'brand-evidence:directory',True)
                    if kind(p) in ('review','dependency-event','rights-decision'):
                        require(confirmed and p['created_by']==actor,'authority','$','explicit actor confirmation required')
                    if kind(p)=='review' and p['decision']=='approve':
                        subject=snapshot.get(p['subject'])
                        result=snapshot.eligible(p['subject'],now,prerequisites=True,supported=SUPPORTED)
                        require(result['eligible'],'authority','$','; '.join(result['reasons']))
                        if kind(subject)=='rights-decision':
                            require(verified_evidence==subject['evidence_sha256'],'authority','$','B must attest exact rights evidence hash')
                newroots=deepcopy(roots if roots is not None else snapshot.roots)
                if roots is None:
                    for p in additions:
                        logical=next((f for f in ('recipe_id','association_id','finding_id','brand_id','rights_id','dependency_id') if f in p),None)
                        if logical:
                            newroots=[r for r in newroots if snapshot.records.get(r['sha256'],{}).get(logical)!=p[logical]]
                        if kind(p) in ('review','dependency-event'):
                            newroots=[r for r in newroots if not (snapshot.records.get(r['sha256'],{}).get('subject')==p['subject'] and
                                snapshot.records.get(r['sha256'],{}).get('scope')==p.get('scope'))]
                        newroots.append(ref(p))
                c=common('commit',actor,now)
                c.update(previous=old,sequence=len(snapshot.commits)+1,action=action,
                         additions=sorted([ref(p) for p in additions],key=lambda r:r['record_id']),
                         roots=sorted(newroots,key=lambda r:r['record_id']),recovery_from=None)
                combined={**snapshot.records,**{digest(p):p for p in additions},digest(c):c}
                require(sum(len(envelope(p)) for p in combined.values())<=64*1024*1024,
                        'limit','$','complete proposed closure exceeds 64 MiB')
                Snapshot(combined,ref(c))  # whole proposed history and graph, before any publication
                for p in additions:self._record(p,'record')
                self._sync(self.fds['records'],'records:directory',True)
                self._record(c,'commit');self._sync(self.fds['records'],'commit:directory',True)
                def guard():require(self._pointer('HEAD')==old,'conflict','$','HEAD generation changed')
                if old:
                    prev=self._pointer('PREVIOUS')
                    if prev:self._snapshot(prev)
                    self._snapshot(old)
                    self._replace('PREVIOUS',canonical(old),guard)
                self._replace('HEAD',canonical(ref(c)),guard)
                return ref(c)
        except OSError as e:
            raise StyleError('storage','$',('UNCERTAIN COMMIT: ' if self._published else 'not published: ')+str(e)) from e

    def recovery_generation(self):
        with self.opened():
            raw=self._read('root','HEAD',1024,True)
            prev=self._pointer('PREVIOUS')
            require(prev is not None,'storage','$','no valid recovery pointer; separate salvage required')
            self._snapshot(prev)
            return dict(head_present=raw is not None,head_bytes_sha256=hashlib.sha256(raw or b'').hexdigest(),previous=prev)

    def recover(self,expected,actor,now,confirmed=False):
        require(confirmed,'authority','$','exact-generation recovery confirmation required')
        if not self.qualified:self.qualify()
        self._published=False
        try:
            with self.opened(write=True):
                def guard():
                    raw=self._read('root','HEAD',1024,True)
                    observed=dict(head_present=raw is not None,head_bytes_sha256=hashlib.sha256(raw or b'').hexdigest(),previous=self._pointer('PREVIOUS'))
                    require(observed==expected,'conflict','$','stale recovery generation')
                    return raw
                raw=guard();base=self._snapshot(expected['previous'])
                # This evidence is synced BEFORE publication; recovery never changes PREVIOUS.
                evidence=canonical(dict(generation=expected,head_hex=(raw or b'').hex(),actor=actor,confirmed_at=now))
                q=str(uuid4())+'.json';self._exclusive('quarantine',q,evidence,'quarantine')
                self._sync(self.fds['quarantine'],'quarantine:directory',True)
                c=common('commit',actor,now)
                c.update(previous=expected['previous'],sequence=len(base.commits)+1,action='recover',
                         additions=[],roots=base.roots,recovery_from=expected)
                Snapshot({**base.records,digest(c):c},ref(c))
                self._record(c,'commit');self._sync(self.fds['records'],'commit:directory',True)
                guard();self._snapshot(expected['previous'])
                self._replace('HEAD',canonical(ref(c)),guard)
                return ref(c)
        except OSError as e:
            raise StyleError('storage','$',('UNCERTAIN RECOVERY: ' if self._published else 'recovery not published: ')+str(e)) from e
