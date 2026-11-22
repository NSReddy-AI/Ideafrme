"""Offline build against explicitly retained, pinned C API and WASI SDK inputs."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 for q in [a.inputs,a.output]:
  if not q.is_absolute() or q.is_symlink() or not q.resolve().is_relative_to(ROOT/'.runtime'):raise SystemExit('Explicit isolated runtime paths required')
 a.output.mkdir(exist_ok=False,mode=0o700)
 sdk=next((a.inputs/'wasi-sdk').iterdir());api=next((a.inputs/'wasmtime-c-api').iterdir());lode=next((a.inputs/'lodepng-source').iterdir())
 source=ROOT/'studio_png_sandbox';commands=[]
 def run(cmd):
  commands.append([str(x) for x in cmd]);r=subprocess.run(commands[-1],env={'PATH':'/usr/bin:/bin','TMPDIR':str(a.output),'HOME':str(a.output)},capture_output=True,timeout=60)
  (a.output/('command-%d.txt'%len(commands))).write_bytes(r.stdout+r.stderr)
  if r.returncode:raise SystemExit('Build failed; see '+str(a.output/('command-%d.txt'%len(commands))))
 run([sdk/'bin/clang','-x','c','-O2','-DLODEPNG_NO_COMPILE_CPP','-DLODEPNG_NO_COMPILE_DISK','-DLODEPNG_NO_COMPILE_ENCODER','-DLODEPNG_NO_COMPILE_ANCILLARY_CHUNKS','-I'+str(lode),'-nostartfiles','-Wl,--no-entry','-Wl,--export=input_ptr','-Wl,--export=pixels_ptr','-Wl,--export=image_width','-Wl,--export=image_height','-Wl,--export=decode_png','-Wl,--export=test_memory_limit','-Wl,--export=test_fuel','-Wl,--export=test_stack','-Wl,-z,stack-size=524288','-Wl,--max-memory=67108864',source/'decoder.c',lode/'lodepng.cpp','-o',a.output/'decoder.wasm'])
 run(['/usr/bin/clang','-O2','-Wall','-Wextra','-I'+str(api/'include'),source/'helper.c','-L'+str(api/'lib'),'-lwasmtime','-Wl,-rpath,'+str(api/'lib'),'-o',a.output/'png-helper'])
 runtime=api/'lib/libwasmtime.dylib'
 manifest={'format':'studio-png-build@1','commands':commands,'runtime':'wasmtime-50.0.1','runtime_library':str(runtime),'runtime_library_sha256':hashlib.sha256(runtime.read_bytes()).hexdigest(),'lodepng_commit':'7b2893e35891c0c85bee5595caafaf3c2044b409','wasi_sdk':'34.0','files':{n:hashlib.sha256((a.output/n).read_bytes()).hexdigest() for n in ['decoder.wasm','png-helper']},'live_placement_enabled':False}
 (a.output/'build.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
