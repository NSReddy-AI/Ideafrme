"""Pinned local fonts and cmap coverage; shaping belongs to the browser."""
import base64
import hashlib
import struct
from pathlib import Path
from studio_manual_ui.service import UIError, read

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
 "en": ("Inter-Bold.otf", "00fd6f4691ee8884a33b46bf45851b341927c37c30064f558e1befb242971c49", "StudioInterPinned", 700, "font/otf"),
 "te": ("NotoSansTelugu-Black.ttf", "42a3167fc2d8ca089b03dcbfcdfe673ecaa176545944ea9c50377144947ae383", "StudioTeluguPinned", 900, "font/ttf")}

def coverage(data):
    """Read cmap formats 4/12 only from hash-qualified, bounded local sfnt bytes."""
    u16=lambda p: struct.unpack_from(">H",data,p)[0]
    u32=lambda p: struct.unpack_from(">I",data,p)[0]
    tables={data[12+i*16:16+i*16]:u32(20+i*16) for i in range(u16(4))}
    c=tables[b"cmap"]; result=set()
    for i in range(u16(c+2)):
        p=c+4+i*8; platform,enc=u16(p),u16(p+2)
        if platform not in (0,3) or (platform==3 and enc not in (1,10)):continue
        s=c+u32(p+4); fmt=u16(s)
        if fmt==12:
            for j in range(u32(s+12)):
                start,end,gid=struct.unpack_from(">III",data,s+16+12*j)
                if end-start>0x110000:raise ValueError("cmap range")
                result.update(cp for cp in range(start,end+1) if gid+cp-start)
        elif fmt==4:
            n=u16(s+6)//2; endp=s+14; startp=endp+2*n+2; deltap=startp+2*n; rangep=deltap+2*n
            for j in range(n):
                start,end=u16(startp+2*j),u16(endp+2*j)
                delta=u16(deltap+2*j); ro=u16(rangep+2*j)
                for cp in range(start,end+1):
                    gid=(cp+delta)&65535 if not ro else u16(rangep+2*j+ro+2*(cp-start))
                    if ro and gid:gid=(gid+delta)&65535
                    if gid and cp!=65535:result.add(cp)
    return frozenset(result)

class Fonts:
    def __init__(self):
        self.faces={}
        try:
            for lang,(name,digest,family,weight,mime) in SPECS.items():
                p=ROOT/"examples/posters/assets/fonts"/name
                raw=read(p,1024*1024)
                if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("hash")
                notice=read(p.with_name(name+".LICENSE.txt"),16384).decode()
                if "SIL OPEN FONT LICENSE Version 1.1" not in notice:raise ValueError("licence")
                self.faces[lang]={"family":family,"weight":weight,"hash":digest,"coverage":coverage(raw),
                    "uri":"data:"+mime+";base64,"+base64.b64encode(raw).decode(),"notice":notice}
        except (OSError,ValueError,KeyError,struct.error) as exc:
            raise UIError("font", "Pinned font unavailable, invalid or changed; export refused.") from exc
    def css(self):
        return "".join('@font-face{font-family:'+f['family']+';src:url("'+f['uri']+'");font-weight:'+str(f['weight'])+';font-style:normal;font-display:block;}' for f in self.faces.values())
    def public(self):
        return {k:{x:v for x,v in f.items() if x!='coverage'} for k,f in self.faces.items()}
    def runs(self,text):
        runs=[]; current=None
        for ch in text:
            cp=ord(ch)
            lang='te' if 0x0c00<=cp<=0x0c7f or cp in (0x200c,0x200d) else 'en'
            if ch=='\n':raise UIError('glyph','Unexpected newline in text run.')
            if cp not in (0x200c,0x200d) and (cp<32 or cp==127 or cp not in self.faces[lang]['coverage']):
                raise UIError('glyph',f'Unsupported glyph U+{cp:04X}; no fallback applied.')
            if lang!=current:runs.append([lang,ch]);current=lang
            else:runs[-1][1]+=ch
        return runs
