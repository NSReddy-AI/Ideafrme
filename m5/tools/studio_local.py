"""Local manual-Studio entry point and bounded internal source recovery kit. No acquisition."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
MAX_FILE=4*1024*1024
MAX_TOTAL=32*1024*1024

def regular(path):
    for parent in (path,*path.parents):
        if parent.is_symlink():raise ValueError('Symlink refused: '+str(parent))
    if not path.is_file() or path.stat().st_nlink!=1:raise ValueError('Regular single-link file required: '+str(path))
    if path.stat().st_size>MAX_FILE:raise ValueError('File exceeds kit bound.')
    return path.read_bytes()

def inventory(root=ROOT):
    # Runtime checks do not start a service, decode media or write caches.
    errors=[]
    if sys.version_info<(3,10):errors.append('Python 3.10+ required; only the recorded local interpreter is qualified.')
    if os.name!='posix':errors.append('POSIX fcntl writer locking required; Windows is not qualified.')
    try:
        import sqlite3
        sqlite_status={'available':True,'version':sqlite3.sqlite_version,'source_rebuild_verified':False}
    except ImportError:sqlite_status={'available':False,'reason':'Optional sqlite3 module absent; Brand Studio unavailable; manual editing remains independent.'}
    fonts=[]
    from visual_poster_studio.fonts import SPECS
    for lang,(name,digest,family,weight,mime) in SPECS.items():
        path=root/'examples/posters/assets/fonts'/name
        try:
            raw=regular(path);notice=regular(path.with_name(name+'.LICENSE.txt'))
            valid=hashlib.sha256(raw).hexdigest()==digest and b'SIL OPEN FONT LICENSE Version 1.1' in notice and b'Copyright' in notice
            if not valid:raise ValueError('Font hash or notice mismatch.')
            fonts.append({'language':lang,'file':str(path.relative_to(root)),'sha256':digest,'bytes':len(raw),'license':'OFL-1.1','notice_sha256':hashlib.sha256(notice).hexdigest()})
        except (ValueError,OSError) as e:errors.append(name+': '+str(e))
    required=source_paths(root)
    from visual_poster_studio.server import ASSETS
    for route,(name,kind) in ASSETS.items():
        try:regular(root/'visual_poster_studio'/name)
        except (OSError,ValueError):errors.append('Required fixed browser route unavailable: '+route)
    missing=[]
    for name in required:
        try:regular(root/name)
        except (OSError,ValueError) as e:missing.append({'file':name,'error':str(e)})
    errors.extend('Required local file unavailable: '+v['file'] for v in missing)
    return {'ready_for_local_start':not errors,'errors':errors,'workspace':str(root),'runtime':{'executable':sys.executable,'version':platform.python_version(),'system':platform.system(),'machine':platform.machine(),'implementation':platform.python_implementation(),'third_party_python_packages_required':[]},'fonts':fonts,'source_files':len(required),'browser':'User-provided compatible browser; embedded fonts, Canvas, SVG and PNG qualification required at runtime. No browser bundled.','media_analysis':'OFF; real-media execution not qualified','independence':{'local_files_present':not errors,'network_isolation_tested':False,'clean_offline_install_verified':False,'runtime_source_rebuild_verified':False,'distribution_approved':False},'brand_asset_studio':{'implemented':'separate metadata-only library','sqlite':sqlite_status,'project_integration':False,'decoding':False}}

def source_paths(root=ROOT):
    names=[]
    for folder in ('creative_core','studio_manual_ui','visual_poster_studio'):
        directory=root/folder
        if directory.is_symlink():raise ValueError('Source directory symlink refused.')
        names.extend(str(p.relative_to(root)) for p in directory.iterdir() if p.suffix in ('.py','.mjs','.js','.html','.css'))
    # Fixed server routes include browser acceptance modules; retain their exact source.
    names.extend(str(p.relative_to(root)) for p in (root/'visual_poster_tests').iterdir() if p.suffix in ('.js','.mjs','.html'))
    names+=['Start Studio.command','tools/studio_local.py','docs/LOCAL_STUDIO_START.md','PROJECT_ENGINEERING_POLICY.md','OFFLINE_BUILD_STRATEGY.md','docs/BRAND_ASSET_FOUNDATION_CONTRACT.md','docs/BRAND_LIBRARY_PORTABILITY_CONTRACT.md','docs/PROJECT_BINDING_CONTRACT.md','docs/CREATIVE_DIRECTOR_PHASE1.md']
    for name in ('Inter-Bold.otf','NotoSansTelugu-Black.ttf'):
        names.extend('examples/posters/assets/fonts/'+n for n in (name,name+'.LICENSE.txt'))
    if len(names)>200:raise ValueError('Kit file-count limit exceeded.')
    return sorted(set(names))

def sessions(root=ROOT):
    from visual_poster_studio.session import marker
    parent=root/'.runtime/studio-ui'
    if not parent.exists():return []
    for p in (parent,*parent.parents):
        if p.is_symlink():raise ValueError('Symlink runtime parent refused.')
    entries=list(parent.iterdir())
    if len(entries)>4096:raise ValueError('Session listing bound exceeded.')
    found=[]
    for path in sorted(entries):
        if path.is_symlink():continue
        if not path.is_dir() or not (path/'visual-session.json').is_file():continue
        try:marker(path);found.append({'root':str(path),'status':'owned; projects not inspected; writer availability checked only on explicit resume'})
        except (ValueError,OSError):found.append({'root':str(path),'status':'invalid ownership; resume refused'})
    return found

def build_kit(name,root=ROOT,parent=None):
    if type(name)!=str or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',name):raise ValueError('Simple kit name required.')
    root=root.resolve();parent=parent or root/'.runtime/studio-ui/local-kits'
    if not parent.is_absolute() or not parent.is_relative_to(root/'.runtime/studio-ui'):raise ValueError('Kit output must remain in the owned runtime tree.')
    for p in (parent,*parent.parents):
        if p.is_symlink():raise ValueError('Symlink output ancestor refused.')
    report=inventory(root)
    if not report['ready_for_local_start']:raise ValueError('Local dependency check failed; kit refused.')
    payload={};total=0
    for n in source_paths(root):
        raw=regular(root/n);total+=len(raw)
        if total>MAX_TOTAL:raise ValueError('Kit source exceeds 32 MiB.')
        payload[n]=raw
    manifest={'kind':'manual-studio-internal-source-kit','version':1,'files':{n:{'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for n,v in payload.items()},'excluded':['sessions','projects','exports','R1','M4','production','media backends','Python runtime','browser','SDKs','font build sources'],'release_approved':False,'offline_install_or_rebuild_proven':False}
    payload['LOCAL_KIT_MANIFEST.json']=json.dumps(manifest,sort_keys=True,indent=2).encode()+b'\n'
    # Capture once, then recheck source identity before any kit publication.
    for n,raw in payload.items():
        if n!='LOCAL_KIT_MANIFEST.json' and regular(root/n)!=raw:raise ValueError('Source changed during kit capture.')
    parent.mkdir(parents=True,exist_ok=True);destination=parent/name;destination.mkdir(mode=0o700,exist_ok=False)
    archive=destination/'manual-studio-source.zip'
    with archive.open('xb') as stream:
        with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for n,raw in sorted(payload.items()):
                info=zipfile.ZipInfo(n,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100755 if n=='Start Studio.command' else 0o100644)<<16;z.writestr(info,raw)
        stream.flush();os.fsync(stream.fileno())
    if archive.stat().st_size>MAX_TOTAL:raise ValueError('Compressed kit exceeds 32 MiB; retained for inspection.')
    with zipfile.ZipFile(archive) as z:
        if set(z.namelist())!=set(payload):raise ValueError('Kit entry verification failed.')
        for n,raw in payload.items():
            if z.read(n)!=raw:raise ValueError('Kit readback failed.')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    with (destination/'receipt.json').open('x') as f:json.dump({'archive_sha256':digest,'compressed_bytes':archive.stat().st_size,'source_bytes':total,'files':len(payload),'internal_only':True,'readback_verified':True,'physical_power_loss_verified':False},f,indent=2)
    return {'directory':str(destination),'sha256':digest,'compressed_bytes':archive.stat().st_size,'files':len(payload),'internal_only':True}

def main(argv=None):
    p=argparse.ArgumentParser(description='Local manual AI Reel Studio; no installs, media decoding or paid services.')
    sub=p.add_subparsers(dest='command')
    sub.add_parser('check',help='Read-only dependency and independence status')
    sub.add_parser('sessions',help='List owned sessions without opening project documents')
    k=sub.add_parser('kit',help='Create a bounded internal source kit; not a standalone installer');k.add_argument('--name',required=True)
    start=sub.add_parser('start');start.add_argument('--port',type=int,default=8766);start.add_argument('--root',type=Path);start.add_argument('--resume',action='store_true')
    a=p.parse_args(argv)
    try:
        if a.command=='check':r=inventory();print(json.dumps(r,indent=2));return 0 if r['ready_for_local_start'] else 2
        if a.command=='sessions':print(json.dumps(sessions(),indent=2));return 0
        if a.command=='kit':print(json.dumps(build_kit(a.name),indent=2));return 0
        report=inventory()
        if not report['ready_for_local_start']:print(json.dumps(report,indent=2));return 2
        from visual_poster_studio.__main__ import main as serve
        sys.argv=['visual_poster_studio','--port',str(getattr(a,'port',8766))]
        if getattr(a,'root',None):sys.argv+=['--root',str(a.root)]
        if getattr(a,'resume',False):sys.argv+=['--resume']
        return serve()
    except (OSError,ValueError,ImportError) as e:print(json.dumps({'error':'local-startup','detail':str(e),'automatic_repair':False}));return 2
if __name__=='__main__':raise SystemExit(main())
