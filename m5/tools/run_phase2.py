"""Isolated renderer acceptance and draft poster export. No production integration."""
from pathlib import Path
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from creative_core import load
from creative_core.document import canonical
from poster_render import build_scene
from poster_render.approval import check_export

require_root = Path('/Users/Nadish/projects/AI Video Editor./Codex/AI Studio')
assert ROOT == require_root and Path.cwd() == ROOT
assert not any(p.is_symlink() for p in (ROOT, *ROOT.parents))
runtime=ROOT/'.runtime/phase2'
runtime.mkdir(exist_ok=True)
out=ROOT/'output/phase2'
out.mkdir(parents=True,exist_ok=True)
for folder in (runtime,out): assert not folder.is_symlink() and folder.resolve().is_relative_to(ROOT)
env=dict(os.environ, TMPDIR=str(runtime), TMP=str(runtime), TEMP=str(runtime),
         M5_RENDER_ISOLATED='seatbelt-v1',
         XDG_CACHE_HOME=str(runtime/'cache'), PYTHONDONTWRITEBYTECODE='1',
         FONTCONFIG_FILE=str(runtime/'fonts.conf'), FONTCONFIG_PATH=str(runtime))
fonts=ROOT/'examples/posters/assets/fonts'
(runtime/'font-cache').mkdir(exist_ok=True)
(runtime/'fonts.conf').write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>{fonts}</dir><cachedir>{runtime/"font-cache"}</cachedir></fontconfig>')

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):digest(p) for folder in ('creative_core','tests')
           for p in (ROOT/folder).glob('*.py') if p.name not in ('test_render_policy.py',)}

def isolated(args, label):
    """Enforce OS write confinement and no network for the process tree."""
    command=['/usr/bin/sandbox-exec','-f',str(ROOT/'poster_render/isolation.sb'),*args]
    start=time.monotonic()
    proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          start_new_session=True)
    peak=0
    while proc.poll() is None:
        if time.monotonic()-start > 35:
            os.killpg(proc.pid,signal.SIGKILL)
            raise RuntimeError('Render timeout')
        # Sample the complete descendant tree, not just the Node parent process.
        listing=subprocess.run(['/bin/ps','-axo','pid=,ppid=,rss='],capture_output=True,text=True,check=True)
        rows=[tuple(map(int,line.split())) for line in listing.stdout.splitlines() if len(line.split())==3]
        tree={proc.pid}
        for _ in range(8): tree |= {pid for pid,ppid,rss in rows if ppid in tree}
        peak=max(peak,sum(rss for pid,ppid,rss in rows if pid in tree))
        time.sleep(.05)
    stdout,stderr=proc.communicate()
    (runtime/(label+'.stdout.txt')).write_bytes(stdout)
    (runtime/(label+'.stderr.txt')).write_bytes(stderr)
    if proc.returncode:
        raise RuntimeError(f'{label} failed ({proc.returncode}): {stderr.decode(errors="replace")[-3000:]}')
    return {'wall_s':round(time.monotonic()-start,3),'sampled_tree_peak_rss_kib':peak,
            'stdout':stdout.decode(errors='replace')}

# Fail closed if Seatbelt is unavailable or not enforcing either restriction.
probe=sys.executable
write_probe='from pathlib import Path; p=Path("/private/tmp/m5-phase2-forbidden-write");\ntry: p.write_text("forbidden")\nexcept PermissionError: print("WRITE_DENIED")\nelse: raise RuntimeError("write sandbox not enforced")'
network_probe='import socket; s=socket.socket();\ntry: s.connect(("127.0.0.1",9))\nexcept PermissionError: print("NETWORK_DENIED")\nelse: raise RuntimeError("network sandbox not enforced")'
assert 'WRITE_DENIED' in isolated([probe,'-B','-c',write_probe],'isolation-write-probe')['stdout']
assert 'NETWORK_DENIED' in isolated([probe,'-B','-c',network_probe],'isolation-network-probe')['stdout']

project=ROOT/'examples/posters'
source_hash=digest(project/'creative.json')
doc=load(project)
policies=json.loads((project/'render-policies.json').read_text())
results=[]
backend=str(ROOT/'poster_render/backend.mjs')
node='/opt/homebrew/bin/node'
for view in doc['views']:
    name=view['id']
    scene=build_scene(doc,project,name,policies[name])
    scene_path=out/(name+'.scene.json')
    scene_path.write_text(json.dumps(scene,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/(name+'.svg')).write_text(scene['svg'],encoding='utf-8')
    chrome=out/(name+'.draft.png')
    result=isolated([node,backend,'chrome',str(scene_path),str(chrome)],name+'-chrome')
    metrics=json.loads(Path(str(chrome)+'.metrics.json').read_text())
    gate=check_export(doc,policies[name],metrics['engine'],draft=True)
    manifest={**gate,'view':name,'source_sha256':source_hash,'png_sha256':digest(chrome),
              'scene_sha256':digest(out/(name+'.svg')),'renderer':metrics['engine'],
              'profile':scene['profile'],'policy':policies[name],'performance':result,
              'qa':{'ink_overflow':False,'external_requests':metrics['requests'],
                    'font_status':metrics['fontStatus']},'human_visual_approval':'pending'}
    comparison=out/(name+'.sharp.png')
    sharp=isolated([node,backend,'sharp',str(scene_path),str(comparison)],name+'-sharp')
    diff=isolated([node,backend,'compare',str(chrome),str(comparison)],name+'-comparison')
    manifest['sharp_performance']=sharp
    manifest['comparison']=json.loads(diff['stdout'])
    # Repeatability: fresh process renders, decoded pixel equivalence via Sharp.
    repeated=out/(name+'.repeat.png')
    repeated_result=isolated([node,backend,'chrome',str(scene_path),str(repeated)],name+'-repeat')
    identity_diff=isolated([node,backend,'compare',str(chrome),str(repeated)],name+'-repeat-diff')
    manifest['repeat_comparison']=json.loads(identity_diff['stdout'])
    manifest['repeat_performance']=repeated_result
    assert manifest['repeat_comparison']['max_channel_error']==0, 'Non-deterministic decoded pixels'
    assert result['wall_s'] < 15 and result['sampled_tree_peak_rss_kib'] < 3*1024*1024
    assert metrics['platformFonts'] and any(r['fonts'] for r in metrics['platformFonts'])
    (out/(name+'.manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    results.append(manifest)
    print(f'{name}: Chrome {result["wall_s"]}s, Sharp {sharp["wall_s"]}s; deterministic pixels',flush=True)
assert source_hash==digest(project/'creative.json')
assert all(digest(ROOT/p)==value for p,value in protected.items()), 'Phase 1 source changed'
# Rendering must refuse overlong text rather than clipping it into a deliverable.
from copy import deepcopy
bad=deepcopy(doc)
bad['content'][0]['text']='W'*100
bad_scene=build_scene(bad,project,'editorial',policies['editorial'])
bad_path=out/'overflow-negative.scene.json'
bad_path.write_text(json.dumps(bad_scene))
try:
    isolated([node,backend,'chrome',str(bad_path),str(out/'overflow-must-not-exist.png')],'overflow-negative')
except RuntimeError as exc:
    assert 'Ink overflow' in str(exc), str(exc)
else:
    raise AssertionError('Overflow was not rejected')
assert not (out/'overflow-must-not-exist.png').exists()
(out/'acceptance.json').write_text(json.dumps({'status':'automated checks passed; human visual review pending',
    'source_unchanged':True,'phase1_sources_unchanged':True,'os_write_confinement':'Seatbelt workspace only',
    'network':'Seatbelt deny IP network; allow local Unix IPC; CDP pipe',
    'overflow_negative_test':'passed; no PNG emitted','results':results},ensure_ascii=False,indent=2)+'\n')
print('Phase 2 automated acceptance complete. Drafts only; human Telugu/visual approval pending.')
