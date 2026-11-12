// Independent G1 verifier. Node built-ins only; no files written, no imports from Python.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

function parse(raw) {
  if (Buffer.byteLength(raw, 'utf8') > 1048576 || raw.startsWith('\ufeff')) throw Error('byte bound/BOM');
  let at=0, members=0, items=0;
  const whitespace=()=>{while (/[\x20\t\r\n]/.test(raw[at] ?? '\u0000')) at++;};
  function string() {
    const start=at++;
    while(at<raw.length) {
      const c=raw[at++];
      if(c==='\\') at++;
      else if(c==='"') {
        const s=JSON.parse(raw.slice(start,at));
        if([...s].length>4096 || [...s].some(c=>{const n=c.codePointAt(0);return n>=0xd800&&n<=0xdfff;})) throw Error('string bound/surrogate');
        return s;
      }
    }
    throw Error('unterminated string');
  }
  function value(depth) {
    whitespace(); const c=raw[at];
    if(c==='{' || c==='[') {
      if(depth>32) throw Error('depth');
      at++; whitespace(); const object=c==='{', end=object?'}':']'; const keys=new Set();
      if(raw[at]===end) {at++;return;}
      while(true) {
        whitespace();
        if(object) {
          if(raw[at]!=='"') throw Error('key');
          const key=string(); if(keys.has(key)) throw Error('duplicate decoded key');keys.add(key);
          if(++members>500) throw Error('members');
          whitespace();if(raw[at++]!==':') throw Error('colon');
        } else if(++items>4096) throw Error('items');
        value(depth+1); whitespace();const next=raw[at++];
        if(next===end) return;
        if(next!==',') throw Error('separator');
      }
    }
    if(c==='"') {string();return;}
    for(const token of ['true','false','null']) if(raw.startsWith(token,at)) {at+=token.length;return;}
    const match=/^-?(?:0|[1-9][0-9]*)/.exec(raw.slice(at));
    if(!match || match[0]==='-0') throw Error('integer grammar');
    const number=BigInt(match[0]);
    if(number<-(1n<<63n) || number>=(1n<<63n)) throw Error('signed64');
    at+=match[0].length;
  }
  value(1);whitespace();if(at!==raw.length) throw Error('trailing/noninteger token');
  // Node's source-aware reviver preserves integers beyond Number's exact range.
  return JSON.parse(raw, (key,v,context)=> typeof v==='number' ? BigInt(context.source) : v);
}

function scalarCompare(a,b) {
  const x=[...a].map(c=>c.codePointAt(0)),y=[...b].map(c=>c.codePointAt(0));
  for(let i=0;i<Math.min(x.length,y.length);i++) if(x[i]!==y[i]) return x[i]-y[i];
  return x.length-y.length;
}
function canonical(value) {
  if(value===null) return 'null';
  if(typeof value==='bigint') return value.toString(10);
  if(typeof value==='string' || typeof value==='boolean') return JSON.stringify(value);
  if(Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
  return '{'+Object.keys(value).sort(scalarCompare).map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
}
for(const line of readFileSync(0,'utf8').split('\n').filter(Boolean)) {
  const test=JSON.parse(line);
  try {
    const bytes=Buffer.from(canonical(parse(test.raw)),'utf8');
    console.log(JSON.stringify({id:test.id,hex:bytes.toString('hex'),sha256:createHash('sha256').update(bytes).digest('hex')}));
  } catch(e) {console.log(JSON.stringify({id:test.id,rejected:true}));}
}
