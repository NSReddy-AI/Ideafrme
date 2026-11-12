"""Read-only capabilities from the accepted renderer/editor, with source identity checks."""
from pathlib import Path
from creative_core.document import canonical
from .scene import PROFILE,MAX_SVG
from .fonts import SPECS,Fonts
from .project_bindings import sha
from studio_manual_ui.service import MAX_DOCUMENT,MAX_ELEMENTS,read
ROOT=Path(__file__).resolve().parents[1]
SOURCES=('visual_poster_studio/scene.py','visual_poster_studio/fonts.py','studio_manual_ui/service.py','visual_poster_studio/service.py','visual_poster_studio/geometry.mjs','visual_poster_studio/text_layout.mjs','creative_core/operations.py','creative_core/validation.py')

def manifest():
 fonts=Fonts() # exact retained font hashes/cmap; no external font lookup
 value={'format':'studio-poster-capabilities@1','profile':dict(PROFILE),'fonts':{k:{'family':SPECS[k][2],'weight':SPECS[k][3],'sha256':SPECS[k][1],'selection':'automatic Unicode runs; never model-selected'} for k in SPECS},'elements':['text','rectangle','ellipse'],'text':{'alignment':['left'],'wrap':'explicit newlines only; no automatic reflow','line_height':PROFILE['line_height'],'baseline':PROFILE['baseline'],'font_size_editor':[1,512],'max_lines':64,'max_codepoints':20000,'max_layers':32,'glyphs':'verified cmap; no fallback; shaping by existing browser'},'geometry':{'units':'integer source pixels','paint_order':'array order','operations':['move','resize','atomic multi-layer geometry','reorder with explicit history upgrade'],'max_layers':MAX_ELEMENTS},'colors':'six-digit hex fill only','background':'transparent, or explicit editable filled rectangle','unsupported':['images','logos','custom fonts','rotation','paths','stroke','opacity','gradients','shadows','automatic center/right text alignment','independent font weights','automatic approval'],'exports':{'svg_max_bytes':MAX_SVG,'png_max_bytes':8*1024*1024,'png':'qualified browser only; pixel parity and overflow checks required'},'document_max_bytes':MAX_DOCUMENT,'qualification_subset':{'coordinate_unit_pixels':10,'x_units':[0,108],'y_units':[0,135],'text_size':[16,96],'max_blocks':5,'font_styles':'fixed renderer fonts only','assets':False,'copy':'exact supplied headline/support slots only','text_overlap':False},'sources':{n:sha(read(ROOT/n,1024*1024)) for n in SOURCES}}
 value['digest']=sha(canonical(value));return value
