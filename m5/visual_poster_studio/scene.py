"""Single deterministic manual creative@1 to SVG mapping. No renderer or I/O."""
import hashlib
import html
from creative_core import fingerprint
from studio_manual_ui.service import manual_subset, UIError

PROFILE={"id":"visual-poster-draft@1","width":1080,"height":1350,"background":"transparent","baseline":1.02,"line_height":1.65}
MAX_SVG=4*1024*1024

def build_scene(doc, fonts):
    manual_subset(doc)
    if len(doc['views'])!=1 or doc['views'][0]['width']!=1080 or doc['views'][0]['height']!=1350:
        raise UIError('view','Only 1080 × 1350 posters are supported.')
    if sum(e['type']=='text' for e in doc['elements'])>32:raise UIError('limit','Text layer limit exceeded.')
    content={c['id']:c for c in doc['content']}
    if sum(len(content[e['content_id']]['text']) for e in doc['elements'] if e['type']=='text')>20000:
        raise UIError('limit','Active text exceeds 20,000 Unicode code points.')
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350" overflow="hidden"><metadata>'+html.escape('\n\n'.join(f['notice'] for f in fonts.faces.values()))+'</metadata><style>'+fonts.css()+'</style>']
    boxes=[]
    for index,e in enumerate(doc['elements']):
        x,y,w,h=(e[k] for k in ('x','y','width','height'))
        if e['view_id']!=doc['views'][0]['id']:raise UIError('view','Unexpected element view.')
        boxes.append({'id':'v'+str(index),'element_id':e['id'],'x':x,'y':y,'width':w,'height':h,'type':e['type']})
        fill=e['style']['fill'];parts.append('<g id="v'+str(index)+'">')
        if e['type']=='text':
            text=content[e['content_id']]['text'];lines=text.split('\n');size=e['style']['font_size']
            if len(lines)>64:raise UIError('limit','Text exceeds 64 explicit lines.')
            parts.append(f'<text xml:space="preserve" style="white-space:pre;font-synthesis:none" font-size="{size}" fill="{fill}">')
            for i,line in enumerate(lines):
                baseline=y+size*PROFILE['baseline']+i*size*PROFILE['line_height']
                parts.append(f'<tspan x="{x}" y="{baseline:.6f}">')
                for lang,run in fonts.runs(line):
                    face=fonts.faces[lang]
                    parts.append(f'<tspan font-family="{face["family"]}" font-weight="{face["weight"]}">'+html.escape(run,quote=True)+'</tspan>')
                parts.append('</tspan>')
            parts.append('</text>')
        elif e['style']['shape']=='rectangle':parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>')
        else:parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}"/>')
        parts.append('</g>')
    parts.append('</svg>');svg=''.join(parts)
    if len(svg.encode())>MAX_SVG:raise UIError('limit','SVG exceeds 4 MiB.')
    return {'project_id':doc['id'],'svg':svg,'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'source_fingerprint':fingerprint(doc),
            'revision':doc['revision'],'profile':PROFILE,'boxes':boxes,'fonts':{k:f['hash'] for k,f in fonts.faces.items()}}
