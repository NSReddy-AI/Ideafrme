"""Ephemeral session catalogue and explicit locked handover; no new persisted format."""
from pathlib import Path
import secrets
from studio_manual_ui.service import RUNTIME,UIError,exact,project_id
from .session import marker
from .service import VisualStudio

def catalogue(parent=RUNTIME):
    if parent.is_symlink():raise UIError('session','Session directory symlink refused.')
    entries=list(parent.iterdir()) if parent.exists() else []
    if len(entries)>4096:raise UIError('limit','Session catalogue exceeds scan limit.')
    result=[]
    for path in entries:
        if path.is_symlink() or not path.is_dir() or not (path/'visual-session.json').is_file():continue
        try:
            value=marker(path)
            result.append({'directory':path.name,'session_id':value['manual_id'],'folder_modified_ns':path.stat().st_mtime_ns,'status':'owned; lock checked on resume'})
        except (ValueError,OSError):
            result.append({'directory':path.name,'session_id':None,'folder_modified_ns':None,'status':'unavailable; ownership/profile validation failed'})
    return sorted(result,key=lambda r:(-(r['folder_modified_ns'] or 0),r['directory']))

def switch(server,request):
    exact(request,{'current_session_id','target_session_id','directory'})
    current=marker(server.studio.root)['manual_id']
    if request['current_session_id']!=current:raise UIError('conflict','Current session changed; refresh Home.',409)
    target_id=project_id(request['target_session_id']);name=request['directory']
    if type(name)!=str or not name or name in {'.','..'} or Path(name).name!=name or '/' in name or '\\' in name:raise UIError('path','Select a listed session, not a filesystem path.')
    target=RUNTIME/name
    if target==server.studio.root:raise UIError('session','Selected session is already active.',409)
    if marker(target)['manual_id']!=target_id:raise UIError('conflict','Selected session identity changed.',409)
    studio=server.studio
    if studio.exports.pending:raise UIError('busy','Finish or cancel the export before changing sessions.',409)
    for identity in studio.manual._working:
        if studio.manual.view(identity)['dirty']:raise UIError('unsaved','Save every unsaved project before changing sessions.',409)
    # Constructor acquires the target OS writer lock before accessing its projects.
    replacement=VisualStudio(target,resume=True)
    if hasattr(studio,'brand_library'):replacement.brand_library=studio.brand_library
    try:studio.close()
    except Exception:
        replacement.close();raise
    server.studio=replacement;server.csrf=secrets.token_hex(32)
    return {'resumed':True,'session_id':target_id,'reload_required':True}
