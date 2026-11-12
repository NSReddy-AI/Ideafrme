"""Explicit Visual-owned session identity; legacy adoption is deliberately refused."""
import hashlib
import os
from pathlib import Path
from studio_manual_ui.service import RUNTIME, UIError, safe, read, decode, encoded, exact, project_id
from .scene import PROFILE
from .fonts import SPECS

MARKER='visual-session.json'

def sync_directory(path):
    fd=os.open(safe(path),os.O_RDONLY)
    try:os.fsync(fd)
    except OSError as exc:raise UIError('durability-blocked','Directory synchronization unavailable; durability not confirmed.') from exc
    finally:os.close(fd)

def exclusive(path,data,mode=0o600):
    path=safe(path);fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    sync_directory(path.parent)

def root_path(root):
    root=safe(Path(root))
    if not root.is_relative_to(RUNTIME) or root==RUNTIME:raise UIError('path','Visual root must be a canonical named runtime directory.')
    return root

def marker(root):
    root=root_path(root)
    try:value=decode(read(root/MARKER,4096))
    except FileNotFoundError as exc:raise UIError('legacy-session','Visual ownership marker missing; legacy adoption is deferred.') from exc
    exact(value,{'visual_session','manual_id','render_profile','font_hashes'})
    if type(value['visual_session'])!=int or value['visual_session']!=1:raise UIError('session','Unknown Visual session version.')
    project_id(value['manual_id'])
    manual=decode(read(root/'studio-session.json',1024));exact(manual,{'manual_ui','id'})
    if type(manual['manual_ui'])!=int or manual['manual_ui']!=1 or manual['id']!=value['manual_id']:raise UIError('session','Visual/manual ownership link mismatch.')
    if value['render_profile']!=PROFILE or value['font_hashes']!={k:v[1] for k,v in SPECS.items()}:raise UIError('profile','Renderer or font profile changed; explicit compatibility review required.')
    if not safe(root/'projects').is_dir() or not safe(root/'studio.lock').is_file():raise UIError('session','Incomplete session layout; no automatic repair.')
    return value

def initialize(root):
    manual=decode(read(root/'studio-session.json',1024))
    value={'visual_session':1,'manual_id':manual['id'],'render_profile':PROFILE,'font_hashes':{k:v[1] for k,v in SPECS.items()}}
    exclusive(root/MARKER,encoded(value)+b'\n');sync_directory(root.parent)
    return value
