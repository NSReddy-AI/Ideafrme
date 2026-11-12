// Temporary external-tool adapter. No installs or automatic provisioning.
import fs from 'node:fs/promises';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {createRequire} from 'node:module';

const workspace = '/Users/Nadish/projects/AI Video Editor./Codex/AI Studio';
const root = await fs.realpath(process.cwd());
if (root !== workspace) throw Error('Wrong workspace');
if(process.env.M5_RENDER_ISOLATED !== 'seatbelt-v1') throw Error('Use the OS-isolated runner');
const [mode, input, output] = process.argv.slice(2);
const local = async p => {
  const parent = await fs.realpath(path.dirname(path.resolve(p)));
  if (!parent.startsWith(root + '/') || parent.includes('..')) throw Error('External output');
  try { if ((await fs.lstat(p)).isSymbolicLink()) throw Error('Symlink path'); }
  catch(e) { if(e.code !== 'ENOENT') throw e; }
  return path.resolve(p);
};
await local(input); await local(output);
const scene = mode === 'compare' ? null : JSON.parse(await fs.readFile(input,'utf8'));
const start = performance.now();
const requireExternal = createRequire('/opt/homebrew/lib/node_modules/hyperframes/package.json');
let report;
if (mode === 'chrome') {
  const puppeteer = requireExternal('puppeteer-core');
  const profile = await fs.mkdtemp(path.join(root,'.runtime','chrome-'));
  const browser = await puppeteer.launch({
    executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless:true, pipe:true, userDataDir:profile, timeout:20000, dumpio:true,
    env:{...process.env, TMPDIR:path.join(root,'.runtime'),
      MAC_CHROMIUM_TMPDIR:path.join(root,'.runtime'), CFFIXED_USER_HOME:profile},
    // macOS forbids Chromium applying a second Seatbelt sandbox under the inherited
    // mandatory one. The outer OS policy remains enforced for every child process.
    args:['--no-sandbox','--disable-gpu','--disable-background-networking','--disable-component-update',
      '--disable-crash-reporter',`--crash-dumps-dir=${profile}/Crashpad`,
      '--no-first-run','--no-default-browser-check',
      '--disable-sync','--force-color-profile=srgb','--disable-extensions',
      '--disable-gpu-shader-disk-cache','--disable-features=MediaRouter,OptimizationHints']
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({width:scene.width,height:scene.height,deviceScaleFactor:1});
    const requests=[];
    await page.setRequestInterception(true);
    page.on('request',r=> {
      if(r.url().startsWith('data:') || r.url()==='about:blank') r.continue();
      else {requests.push(r.url());r.abort();}
    });
    await page.setContent(`<html><head><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'"><style>html,body{margin:0;padding:0;background:transparent}svg{display:block}</style></head><body>${scene.svg}</body></html>`,{waitUntil:'load',timeout:15000});
    await page.evaluate(async()=>{await Promise.all(Array.from(document.fonts).map(f=>f.load())); await document.fonts.ready;
      await Promise.all(Array.from(document.querySelectorAll('svg image')).map(el=>{
        const img=new Image();img.src=el.href.baseVal;return img.decode();}));});
    const metrics = await page.evaluate(boxes=>boxes.map(b=>{
      const el=document.getElementById(b.id), r=el.getBBox();
      const lines=Array.from(el.querySelectorAll('text > tspan')).map(l=>{
        const v=l.getBBox();return {x:v.x,y:v.y,width:v.width,height:v.height};});
      const lineOverlap=lines.some((l,i)=>i && lines[i-1].y+lines[i-1].height>l.y+0.5);
      return {...b,ink:{x:r.x,y:r.y,width:r.width,height:r.height},
        lines,lineOverlap,
        overflow:lineOverlap || r.x < b.x-1 || r.y < b.y-1 || r.x+r.width>b.x+b.width+1 || r.y+r.height>b.y+b.height+1};
    }),scene.boxes);
    if(metrics.some(m=>m.overflow)) throw Error('Ink overflow: '+JSON.stringify(metrics.filter(m=>m.overflow)));
    if(requests.length) throw Error('External resource requests: '+requests.join(','));
    const fontStatus=await page.evaluate(()=>Array.from(document.fonts).map(f=>({family:f.family,status:f.status})));
    if(fontStatus.some(f=>f.status!=='loaded')) throw Error('Font load failure');
    const cdp=await page.createCDPSession();
    await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
    const {root:dom}=await cdp.send('DOM.getDocument');
    const {nodeIds}=await cdp.send('DOM.querySelectorAll',{nodeId:dom.nodeId,selector:'text tspan tspan'});
    const platformFonts=[];
    for(const nodeId of nodeIds) platformFonts.push(await cdp.send('CSS.getPlatformFontsForNode',{nodeId}));
    if(platformFonts.some(r=>r.fonts.some(f=>!f.isCustomFont))) throw Error('System font fallback detected');
    await page.screenshot({path:output,type:'png',omitBackground:true});
    report={engine:await browser.version(),metrics,requests,fontStatus,platformFonts};
  } finally {await browser.close();}
} else if(mode === 'sharp') {
  const sharp=requireExternal('sharp');
  const data=await sharp(Buffer.from(scene.svg),{density:72,limitInputPixels:8294400,failOn:'warning'})
    .png().toBuffer();
  await fs.writeFile(output,data);
  report={engine:'sharp',versions:sharp.versions};
} else if(mode === 'compare') {
  const sharp=requireExternal('sharp');
  const a=await sharp(input).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  const b=await sharp(output).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  if(a.info.width!==b.info.width || a.info.height!==b.info.height) throw Error('Size mismatch');
  let total=0, different=0, max=0;
  for(let i=0;i<a.data.length;i++){const d=Math.abs(a.data[i]-b.data[i]);total+=d;if(d)different++;max=Math.max(max,d);}
  console.log(JSON.stringify({width:a.info.width,height:a.info.height,mean_absolute_channel_error:total/a.data.length,
    differing_channel_fraction:different/a.data.length,max_channel_error:max}));
  process.exit(0);
} else throw Error('Unsupported backend');
report.elapsed_ms=performance.now()-start;
await local(output+'.metrics.json');
await fs.writeFile(output+'.metrics.json',JSON.stringify(report,null,2)+'\n');
