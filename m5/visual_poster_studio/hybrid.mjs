import {fontRuns,fitTextBox} from '/text_layout.mjs';
import {loadFonts,inspectScene} from '/browser_acceptance.js';

export async function measurements(texts,faces){
 await loadFonts(faces);const ctx=document.createElement('canvas').getContext('2d');if(!ctx)throw Error('Browser text measurement unavailable.');const table=[];
 for(const text of new Set(texts)){
  const sizes={};for(let size=16;size<=80;size++){
   const measure=t=>fontRuns(t).reduce((n,r)=>{const f=faces[r.lang];ctx.font=`${f.weight} ${size}px "${f.family}"`;return n+ctx.measureText(r.text).width;},0);
   const descent=Math.max(...Object.entries(faces).map(([lang,f])=>{ctx.font=`${f.weight} ${size}px "${f.family}"`;return ctx.measureText(lang==='te'?'తెలుగు':'gj').actualBoundingBoxDescent||0;}));const fit=fitTextBox(text,size,measure,descent);
   const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('width','1080');svg.setAttribute('height','1350');svg.classList.add('measurement');const el=document.createElementNS(ns,'text');el.setAttribute('font-size',size);el.setAttribute('xml:space','preserve');el.style.whiteSpace='pre';el.style.fontSynthesis='none';
   text.split('\n').forEach((line,i)=>{const t=document.createElementNS(ns,'tspan');t.setAttribute('x','0');t.setAttribute('y',String(size*1.02+i*size*1.65));for(const r of fontRuns(line)){const f=faces[r.lang],span=document.createElementNS(ns,'tspan');span.setAttribute('font-family',f.family);span.setAttribute('font-weight',f.weight);span.textContent=r.text;t.append(span);}el.append(t);});svg.append(el);document.body.append(svg);
   try{const b=el.getBBox();sizes[size]={width:Math.max(fit.width,Math.ceil(b.x+b.width)+2),height:Math.max(fit.height,Math.ceil(b.y+b.height)+2),left:Number(b.x.toFixed(4)),top:Number(b.y.toFixed(4))};}finally{svg.remove();}
  }table.push({text,sizes});
 }
 return {kind:'semantic-font-measurements@1',fonts:Object.fromEntries(Object.entries(faces).map(([k,v])=>[k,v.hash])),table};
}
export function installHybrid(api){
 const $=id=>document.getElementById(id);let job=null,available=false,locked=false,sourceStamp=null,timer=null,polling=false,urls=[],rendered=null;
 const stamp=p=>JSON.stringify(p?[p.project_id,p.revision,p.dirty,p.binding?.hash,p.binding?.published_head]:null);
 const active=()=>job&&['queued','verifying-artifacts','inferencing','compiling','cancelling'].includes(job.state);
 function clear(){for(const u of urls)URL.revokeObjectURL(u);urls=[];$('hybrid-results').replaceChildren();rendered=null;}
 function controls(){const p=api.current();if(rendered&&job?.state==='ready'&&sourceStamp===stamp(p))$('director-review').disabled=locked;$('hybrid-generate').disabled=locked||active()||!available||!p?.binding||p.dirty||!p.binding.eligible;$('hybrid-cancel').disabled=!active()&&job?.state!=='ready';$('hybrid-progress').hidden=!active();$('hybrid-results').querySelectorAll('button').forEach(b=>b.disabled=locked||!$('director-review').checked);}
 function report(){const unavailable=!available?'Local AI unavailable: pinned runtime/model absent or planner fault. Use explicit deterministic planning. ':'';$('hybrid-status').textContent=unavailable+(job?`${job.state} · ${job.elapsed_seconds}s · ${job.detail}`:'Ready on explicit request. Typical 94–128 seconds, up to 240 seconds.');controls();}
 async function draw(){
  clear();const result=job.result;const info=await api.request('/api/fonts');if(!info.fonts)throw Error(info.error||'Pinned fonts unavailable.');await loadFonts(info.fonts);
  const summary=document.createElement('p');summary.textContent=`AI interpretation (unapproved): ${result.editorial_intent.interpretation} Audience: ${result.editorial_intent.audience}. Tone: ${result.editorial_intent.tone}.`; $('hybrid-results').append(summary);
  const details=document.createElement('details'),pre=document.createElement('pre'),heading=document.createElement('summary');heading.textContent='Pinned rules, exact brief and provenance';pre.textContent=JSON.stringify({brief:result.brief,brand:result.pinned_brand,rationales:result.rationales,request_hash:result.request_hash,response_sha256:result.response_sha256},null,2);details.append(heading,pre);$('hybrid-results').append(details);
  for(let i=0;i<3;i++){
   const scene=result.scenes[i],qa=await inspectScene(scene);if(qa.overflow.length)throw Error('Concept '+(i+1)+' failed browser text bounds; selection disabled. Edit the brief or use explicit fallback.');
   const card=document.createElement('article'),title=document.createElement('h4'),image=document.createElement('img'),why=document.createElement('p'),open=document.createElement('button');title.textContent=result.plans[i].name;image.alt=`Unapproved concept ${i+1}: ${result.plans[i].name}`;image.style.maxWidth='220px';const url=URL.createObjectURL(new Blob([scene.svg],{type:'image/svg+xml'}));urls.push(url);image.src=url;why.textContent='Application rationale: '+result.rationales[i].text;open.textContent=`Open AI concept ${i+1} as editable draft`;open.disabled=true;
   open.addEventListener('click',()=>api.run(async()=>{
    if(api.pending())throw Error('Save or discard unsubmitted editor/brief fields first.');if(sourceStamp!==stamp(api.current()))throw Error('Source changed. Generate a new proposal explicitly.');if(!$('director-review').checked)throw Error('Review the AI interpretation, rules and all previews first.');
    const value=await api.request('/api/hybrid/select',{job_id:job.id,concept_id:String(i),acknowledge_rules:true});api.opened(value.project);clear();
   },'AI-assisted concept saved as a separate unapproved editable draft. Source unchanged.'));
   card.append(title,image,why,open);$('hybrid-results').append(card);
  }
  rendered=job.id;controls();
 }
 async function refresh(){
  if(polling)return;polling=true;
  try{const v=await api.request('/api/hybrid/status');available=v.available;job=v.job;report();
   if(job?.state==='ready'&&rendered!==job.id){if(sourceStamp===stamp(api.current()))await draw();else{clear();$('hybrid-status').textContent='A previous proposal exists, but its source is not the current saved project. Cancel/discard it or generate explicitly.';}}
  }catch(e){available=false;clear();$('hybrid-status').textContent='Planner status unavailable: '+e.message+'. Refresh to check; no automatic retry or fallback.';}
  finally{polling=false;controls();if(active())timer=setTimeout(refresh,1000);}
 }
 $('hybrid-generate').addEventListener('click',()=>api.run(async()=>{
  if(api.pending())throw Error('Save or discard unapplied text/brief fields first.');if(!$('director-brief-ack').checked)throw Error('Acknowledge the saved brief first.');
  clear();$('director-review').checked=false;const p=api.current(),info=await api.request('/api/fonts');if(!info.fonts)throw Error(info.error||'Pinned fonts unavailable.');sourceStamp=stamp(p);
  const source={project_id:p.project_id,expected_revision:p.revision,expected_binding:p.binding.hash,expected_head:p.binding.published_head,seed:Number($('director-seed').value),acknowledge_brief:true};
  const measured=await measurements([p.binding.record.brief.topic,p.binding.record.brief.purpose],info.fonts);if(sourceStamp!==stamp(api.current()))throw Error('Source changed during measurement.');job=await api.request('/api/hybrid/start',{source,measurements:measured});report();clearTimeout(timer);timer=setTimeout(refresh,200);
 },'Local AI generation started. Continue editing if needed; changed sources invalidate selection.'));
 $('hybrid-cancel').addEventListener('click',async()=>{if(!job)return;try{job=await api.request('/api/hybrid/cancel',{job_id:job.id});clear();report();clearTimeout(timer);timer=setTimeout(refresh,100);}catch(e){$('hybrid-status').textContent='Cancellation not confirmed: '+e.message+'. Refresh status; do not assume inference stopped.';}});
 $('hybrid-refresh').addEventListener('click',()=>{clearTimeout(timer);refresh();});$('director-review').addEventListener('change',controls);
 refresh();
 return {ready:()=>Boolean(rendered&&job?.state==='ready'&&sourceStamp===stamp(api.current())),update(value){locked=value;controls();if(rendered&&sourceStamp!==stamp(api.current()))clear();}};
}
