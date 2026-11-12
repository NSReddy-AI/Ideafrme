"""Telugu shaping: reels (engine: Pillow + RAQM/HarfBuzz) versus posters (browser shaping of M5's SVG) - same font file.

  ~/.venvs/reelstudio/bin/python -B tools/m6_telugu_shaping.py <out_dir>

Writes <out_dir>/engine/NN.png (each word drawn by the engine's own text call: ImageFont.truetype(..., layout_engine=RAQM),
96 px, ink-cropped), words.json, and compare.html. Open compare.html through a local web server: it draws every word the
way posters are drawn (SVG <text> with the pinned font embedded, rasterised by the browser), crops both to their ink,
compares them at the same size and reports, per word, the share of ink matched within 1 px both ways and the size difference. Identical shaping gives
an ink match close to 1 at the same size (anti-aliasing allowed 1 px); a missing conjunct or misplaced vowel sign drops it clearly and changes the size.
Results are left in window.__shaping for automated reading. Nothing else is written."""
import base64, hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, features

ROOT = Path(__file__).resolve().parents[1]
ENGINE_FONT = ROOT / "engine" / "fonts" / "NotoSansTelugu-Black.ttf"
M5_FONT = ROOT / "m5" / "examples" / "posters" / "assets" / "fonts" / "NotoSansTelugu-Black.ttf"
SIZE = 96


def engine_png(word, path):
    f = ImageFont.truetype(str(ENGINE_FONT), SIZE, layout_engine=ImageFont.Layout.RAQM)
    im = Image.new("L", (SIZE * (len(word) + 4), SIZE * 3), 255)
    ImageDraw.Draw(im).text((SIZE, SIZE), word, font=f, fill=0)
    box = ImageOps.invert(im).getbbox(); im.crop(box).save(path)


def main(out):
    out = Path(out); (out / "engine").mkdir(parents=True, exist_ok=True)
    if not features.check("raqm"): sys.exit("Pillow has no RAQM layout here; the engine could not shape Telugu either.")
    if ENGINE_FONT.read_bytes() != M5_FONT.read_bytes(): sys.exit("Engine and poster fonts differ; comparison would not be like for like.")
    words = json.loads((ROOT / "tests" / "fixtures" / "telugu_shaping_words.json").read_text(encoding="utf-8"))["words"]
    for i, w in enumerate(words): engine_png(w, out / "engine" / f"{i:02d}.png")
    meta = dict(words=words, size=SIZE, font=ENGINE_FONT.name, font_sha256=hashlib.sha256(ENGINE_FONT.read_bytes()).hexdigest(),
                pillow_raqm=features.version("raqm"), harfbuzz=features.version("harfbuzz") if hasattr(features, "version") else None)
    (out / "words.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    font_uri = "data:font/ttf;base64," + base64.b64encode(M5_FONT.read_bytes()).decode()
    (out / "compare.html").write_text(PAGE.replace("__FONT__", font_uri).replace("__META__", json.dumps(meta, ensure_ascii=False)), encoding="utf-8")
    print(json.dumps({k: v for k, v in meta.items() if k != "words"} | {"words": len(words), "out": str(out)}))


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Telugu shaping check</title><style>
body{font:14px/1.4 -apple-system,system-ui,sans-serif;margin:16px;background:#fff;color:#101828}
table{border-collapse:collapse}td,th{border-bottom:1px solid #D8DEEA;padding:6px 10px;text-align:left;vertical-align:middle}
img,canvas{height:48px;background:#F5F7FA}.bad{color:#B42318;font-weight:600}.ok{color:#166534}
</style></head><body><h1>Telugu shaping: engine (reels) vs browser (posters)</h1><p id="sum">Running…</p>
<table><thead><tr><th>#</th><th>Word</th><th>Engine (Pillow+RAQM)</th><th>Browser (SVG)</th><th>Ink match (±1 px)</th><th>Width / height diff</th><th></th></tr></thead><tbody id="rows"></tbody></table>
<script>
const META=__META__, FONT="__FONT__", S=META.size, FAMILY="ShapingPinned";
const esc=s=>s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const load=src=>new Promise((ok,no)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=no;i.src=src});
function gray(img,w,h){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d',{willReadFrequently:true});x.fillStyle='#fff';x.fillRect(0,0,w,h);x.drawImage(img,0,0,w,h);return x.getImageData(0,0,w,h)}
function inkBox(d){let x0=1e9,y0=1e9,x1=-1,y1=-1;for(let y=0;y<d.height;y++)for(let x=0;x<d.width;x++)if(d.data[(y*d.width+x)*4]<128){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y)}return x1<0?null:{x:x0,y:y0,w:x1-x0+1,h:y1-y0+1}}
function crop(src,b){const c=document.createElement('canvas');c.width=b.w;c.height=b.h;c.getContext('2d').drawImage(src,b.x,b.y,b.w,b.h,0,0,b.w,b.h);return c}
async function browserWord(w){
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${S*(w.length+4)}" height="${S*3}"><style>@font-face{font-family:${FAMILY};src:url("${FONT}");font-weight:900}</style><rect width="100%" height="100%" fill="#fff"/><text x="${S}" y="${S*2}" font-size="${S}" font-family="${FAMILY}" font-weight="900" fill="#000">${esc(w)}</text></svg>`;
  const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));try{const img=await load(url);await img.decode();
  const d=gray(img,img.naturalWidth,img.naturalHeight);const b=inkBox(d);const c=document.createElement('canvas');c.width=d.width;c.height=d.height;c.getContext('2d').putImageData(d,0,0);return crop(c,b)}finally{URL.revokeObjectURL(url)}}
function mask(c,W,H){const x=document.createElement('canvas');x.width=W;x.height=H;const g=x.getContext('2d',{willReadFrequently:true});g.fillStyle='#fff';g.fillRect(0,0,W,H);g.drawImage(c,0,0);const d=g.getImageData(0,0,W,H).data;const m=new Uint8Array(W*H);for(let i=0;i<W*H;i++)m[i]=d[i*4]<128?1:0;return m}
function covered(m,o,W,H){let n=0,hit=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++){if(!m[y*W+x])continue;n++;let f=0;for(let dy=-1;dy<=1&&!f;dy++)for(let dx=-1;dx<=1&&!f;dx++){const yy=y+dy,xx=x+dx;if(yy>=0&&yy<H&&xx>=0&&xx<W&&o[yy*W+xx])f=1}hit+=f}return n?hit/n:1}
// Same size (96 px, same font file): compare at native size, aligned on the ink box, with 1 px tolerance for anti-aliasing.
function compare(a,b){const W=Math.max(a.width,b.width),H=Math.max(a.height,b.height),ma=mask(a,W,H),mb=mask(b,W,H);
  let inter=0,uni=0;for(let i=0;i<W*H;i++){if(ma[i]&&mb[i])inter++;if(ma[i]||mb[i])uni++}
  return{iou:uni?inter/uni:1,match:Math.min(covered(ma,mb,W,H),covered(mb,ma,W,H)),dw:b.width-a.width,dh:b.height-a.height,width_ratio:b.width/a.width}}
(async()=>{
  await new FontFace(FAMILY,`url("${FONT}")`,{weight:'900'}).load().then(f=>document.fonts.add(f));
  const out=[];const rows=document.getElementById('rows');
  for(const [i,w] of META.words.entries()){
    const eng=await load(`engine/${String(i).padStart(2,'0')}.png`);const br=await browserWord(w);const r=compare(eng,br);
    const flag=r.match<0.97||Math.abs(r.dw)>3||Math.abs(r.dh)>3;out.push({i,word:w,...r,review:flag});
    const tr=document.createElement('tr');tr.innerHTML=`<td>${i}</td><td>${esc(w)}</td><td></td><td></td><td>${r.match.toFixed(3)} (IoU ${r.iou.toFixed(2)})</td><td>${r.dw>=0?'+':''}${r.dw} / ${r.dh>=0?'+':''}${r.dh} px</td><td class="${flag?'bad':'ok'}">${flag?'REVIEW':'match'}</td>`;
    tr.children[2].append(eng);tr.children[3].append(br);rows.append(tr)}
  // Negative controls: the browser draws a deliberately WRONG form; the check must flag every one of these.
  const controls=[[2,"క్\u200cష","conjunct broken by ZWNJ"],[0,"తేలుగు","wrong vowel sign"],[9,"ఇల్ల","different consonant"]];const ctl=[];
  for(const [i,wrong,why] of controls){const eng=await load(`engine/${String(i).padStart(2,'0')}.png`);const br=await browserWord(wrong);const r=compare(eng,br);
    const caught=r.match<0.97||Math.abs(r.dw)>3||Math.abs(r.dh)>3;ctl.push({engine_word:META.words[i],browser_word:wrong,why,match:r.match,dw:r.dw,dh:r.dh,caught});
    const tr=document.createElement('tr');tr.innerHTML=`<td>ctl</td><td>${esc(wrong)} <small>(${why})</small></td><td></td><td></td><td>${r.match.toFixed(3)}</td><td>${r.dw} / ${r.dh} px</td><td class="${caught?'ok':'bad'}">${caught?'caught':'MISSED'}</td>`;
    tr.children[2].append(eng);tr.children[3].append(br);rows.append(tr)}
  const bad=out.filter(r=>r.review);window.__shaping={meta:{...META,words:undefined},results:out,controls:ctl,controls_caught:ctl.every(c=>c.caught),review:bad.length,min_match:Math.min(...out.map(r=>r.match)),max_size_diff_px:Math.max(...out.map(r=>Math.max(Math.abs(r.dw),Math.abs(r.dh)))),user_agent:navigator.userAgent};
  document.getElementById('sum').textContent=`${out.length} words · ${bad.length} to review · lowest ink match ${window.__shaping.min_match.toFixed(3)}, largest size difference ${window.__shaping.max_size_diff_px} px (match = ≥ 0.97 of ink within 1 px both ways, size within 3 px)`;
})().catch(e=>{document.getElementById('sum').textContent='Failed: '+e.message;window.__shaping={error:e.message}});
</script></body></html>"""

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tests" / "acceptance" / "m7a_telugu_shaping")
