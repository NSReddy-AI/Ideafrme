"""Bounded, explicit draft export handshake; no image decoder, approval or overwrite."""
import base64
import binascii
import hashlib
import json
import os
import secrets
import time
from studio_manual_ui.service import UIError,safe,read,decode

MAX_PNG=8*1024*1024
MAX_STORAGE=256*1024*1024

class Exports:
    def __init__(self,root,*,resume=False):
        self.root=safe(root/'exports')
        if resume and not self.root.is_dir():raise UIError('exports','Retained export root missing; no automatic repair.')
        if not self.root.exists():self.root.mkdir(mode=0o700)
        self.pending=None
        self.status=self.audit()
    def audit(self):
        count=0;total=0;partial=[];errors=[]
        for directory in self.root.iterdir():
            safe(directory);count+=1
            if not directory.is_dir():errors.append(directory.name);continue
            for f in directory.iterdir():
                safe(f)
                if not f.is_file():raise UIError('exports','Unexpected nested export layout.')
                total+=f.stat().st_size
                if f.name not in {'poster.draft.svg','poster.draft.png','manifest.json'}:errors.append(directory.name)
            if not (directory/'manifest.json').exists():partial.append(directory.name);continue
            try:
                m=decode(read(directory/'manifest.json',65536))
                if m['draft'] is not True:raise ValueError('not draft')
                if 'binding_identity' in m:
                    import html,re
                    from creative_core.document import canonical
                    ident=m['binding_identity']
                    if type(ident)!=dict or set(ident)!={'format','binding_hash','brand_hash','brief_hash','workflow_fingerprint'} or ident['format']!='studio-bound-render@1':raise ValueError('unknown bound export identity')
                    for key in ('binding_hash','brief_hash'):
                        if type(ident[key])!=str or not re.fullmatch('[0-9a-f]{64}',ident[key]):raise ValueError('binding identity hash')
                    if ident['brand_hash'] is not None and (type(ident['brand_hash'])!=str or not re.fullmatch('[0-9a-f]{64}',ident['brand_hash'])):raise ValueError('brand identity hash')
                    context={k:v for k,v in ident.items() if k!='workflow_fingerprint'}
                    expected='sha256:'+hashlib.sha256(canonical({'creative_fingerprint':m['source_fingerprint'],'context':context,'profile':m['profile']})).hexdigest()
                    if ident['workflow_fingerprint']!=expected:raise ValueError('workflow fingerprint')
                    marker='id="studio-binding-identity">'+html.escape(canonical(ident).decode())+'</metadata>'
                    if marker not in read(directory/'poster.draft.svg',4*1024*1024).decode():raise ValueError('SVG context mismatch')
                for name,key,limit in [('poster.draft.svg','svg_sha256',4*1024*1024),('poster.draft.png','png_sha256',MAX_PNG)]:
                    if m[key] is None:
                        if (directory/name).exists():raise ValueError('unexpected PNG')
                    elif hashlib.sha256(read(directory/name,limit)).hexdigest()!=m[key]:raise ValueError('hash')
            except (OSError,ValueError,KeyError,UIError):errors.append(directory.name)
        return {'sets':count,'bytes':total,'partial':partial,'errors':errors,
                'blocked':bool(errors) or count>20 or total>MAX_STORAGE}
    def cancel(self):self.pending=None
    def begin(self,identity,scene):
        if self.status['blocked']:raise UIError('exports','Retained exports require review; export writes blocked.')
        now=time.monotonic()
        if self.pending and now-self.pending['started']<=15:raise UIError('busy','One export is already in flight.',409)
        entries=list(self.root.iterdir())
        if len(entries)>=20:raise UIError('limit','20 export sets retained; nothing was deleted.')
        self.pending={'token':secrets.token_hex(24),'started':now,'identity':identity,'scene':scene}
        return {'token':self.pending['token'],'expires_seconds':15,'scene':scene}
    def finish(self,token,revision,png,qa,current_revision):
        if type(token)!=str or len(token)!=48 or any(c not in '0123456789abcdef' for c in token) or type(revision)!=int or revision<0:
            raise UIError('request','Invalid export token or revision.')
        p=self.pending
        if not p or token!=p['token']:raise UIError('export','Unknown export handshake.',409)
        self.pending=None  # every completion attempt consumes the handshake
        scene=p['scene']
        if time.monotonic()-p['started']>15:raise UIError('timeout','Export handshake expired.',409)
        if revision!=scene['revision'] or current_revision!=revision:raise UIError('stale','Project changed during export.',409)
        if type(qa)!=dict or set(qa)!={'fonts_loaded','overflow','parity','embedded_fonts'} or qa['fonts_loaded'] is not True or type(qa['overflow'])!=list or qa['overflow']!=[] or type(qa['parity'])!=bool or type(qa['embedded_fonts'])!=bool:
            raise UIError('qa','Font or overflow checks failed.')
        data=None
        if png is not None:
            if qa['parity'] is not True or qa['embedded_fonts'] is not True:raise UIError('png-disabled','PNG qualification failed.')
            if type(png)!=str or len(png)>((MAX_PNG+2)//3)*4:raise UIError('limit','PNG exceeds 8 MiB.')
            try:data=base64.b64decode(png,validate=True)
            except (ValueError,binascii.Error) as exc:raise UIError('png','Malformed generated PNG.') from exc
            if len(data)>MAX_PNG or len(data)<33 or data[:8]!=b'\x89PNG\r\n\x1a\n' or data[12:16]!=b'IHDR' or data[16:24]!=b'\x00\x00\x048\x00\x00\x05F':
                raise UIError('png','Generated PNG header or dimensions invalid.')
        raw=scene['svg'].encode()
        manifest={'draft':True,'source_fingerprint':scene['source_fingerprint'],'revision':revision,'profile':scene['profile'],
                  'svg_sha256':scene['svg_sha256'],'png_sha256':hashlib.sha256(data).hexdigest() if data else None,
                  'font_hashes':scene['fonts'],'browser_reported_qa':qa,'power_loss_durability':'unverified'}
        if 'binding_identity' in scene:manifest['binding_identity']=scene['binding_identity']
        m=json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2).encode()
        total=0
        for f in self.root.rglob('*'):
            safe(f)
            if f.is_file():total+=f.stat().st_size
        if total+len(raw)+len(data or b'')+len(m)>MAX_STORAGE:raise UIError('limit','Session export storage exhausted.')
        directory=safe(self.root/('draft-'+p['token'][:16]));directory.mkdir(mode=0o700)
        # Incomplete directories are retained and count against quota; never erase evidence.
        for name,value in [('poster.draft.svg',raw),('poster.draft.png',data),('manifest.json',m)]:
            if value is None:continue
            fd=os.open(safe(directory/name),os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(value);stream.flush();os.fsync(stream.fileno())
        return {'directory':str(directory),'manifest':manifest}
