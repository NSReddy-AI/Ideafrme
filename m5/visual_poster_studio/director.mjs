// First-party deterministic concept comparison. No provider, model or external asset calls.
export function installDirector(api){
 const $=id=>document.getElementById(id);let bundle=null,source=null,stamp=null;
 const currentStamp=p=>JSON.stringify(p?[p.project_id,p.revision,p.dirty,p.binding?.hash,p.binding?.published_head]:null);
 function update(locked){
  const p=api.current(),next=currentStamp(p);if(stamp!==next){bundle=null;source=null;$('director-results').replaceChildren();$('director-rules').textContent='';$('director-review').checked=false;$('director-brief-ack').checked=false;stamp=next;}
  $('director-generate').disabled=locked||!p?.binding||p.dirty||!p.binding.eligible;
  $('director-seed').disabled=locked;$('director-brief-ack').disabled=locked;$('director-review').disabled=locked||!bundle;
  for(const b of $('director-results').querySelectorAll('button'))b.disabled=locked||!$('director-review').checked;
  $('director-status').textContent=!p?.binding?'Save an optional brand and complete brief in a new bound project first.':p.dirty?'Save project edits before planning.':!p.binding.eligible?'Pinned brand use is blocked: '+p.binding.status:'Saved brief available. Local deterministic planner; model-powered ideation is not qualified.';
 }
 function draw(){
  $('director-results').replaceChildren();$('director-rules').textContent=JSON.stringify({brief:bundle.inputs.brief,mandatory_rules:bundle.rules,preferences:bundle.preferences,inspiration:bundle.inspiration,typography_preferences:bundle.typography_preferences,warnings:bundle.warnings,seed:bundle.inputs.seed,digest:bundle.digest},null,2);
  for(const c of bundle.concepts){
   const card=document.createElement('article'),title=document.createElement('h3'),rationale=document.createElement('p'),detail=document.createElement('p'),layers=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre'),open=document.createElement('button');
   title.textContent=c.name;rationale.textContent=c.rationale;detail.textContent=`Emphasis: ${c.emphasis}. Text sizes: ${Object.entries(c.typography_hierarchy).map(([k,v])=>`${k} ${v}px`).join(', ')}.`;summary.textContent='Inspect proposed editable layers and exact copy';pre.textContent=JSON.stringify(c.layers,null,2);layers.append(summary,pre);open.textContent=`Open ${c.name} as new draft`;open.disabled=true;
   open.addEventListener('click',()=>api.run(async()=>{
    if(api.pending())throw Error('Save or discard unsubmitted text/brief fields first.');
    if(!$('director-review').checked)throw Error('Review all mandatory rules, instructions and the proposed layers first.');
    const result=await api.request('/api/director/select',{source,bundle_digest:bundle.digest,concept_id:c.id,acknowledge_rules:true});api.opened(result.project);
   },'Concept saved as a separate editable draft. Source project and approvals unchanged.'));
   card.append(title,rationale,detail,layers,open);$('director-results').append(card);
  }
 }
 $('director-generate').addEventListener('click',()=>api.run(async()=>{
  if(api.pending())throw Error('Save or discard unsubmitted text/brief fields first.');
  if(!$('director-brief-ack').checked)throw Error('Review and acknowledge the saved brief.');
  const p=api.current();source={project_id:p.project_id,expected_revision:p.revision,expected_binding:p.binding.hash,expected_head:p.binding.published_head,seed:Number($('director-seed').value),acknowledge_brief:true};
  bundle=await api.request('/api/director/generate',source);$('director-review').checked=false;draw();
 },'Three distinct deterministic proposals ready. Review rules and instructions before selecting.'));
 $('director-review').addEventListener('change',()=>update(false));
 $('director-seed').addEventListener('input',()=>{bundle=null;source=null;$('director-results').replaceChildren();$('director-rules').textContent='Seed changed; regenerate and review.';$('director-review').checked=false;});
 return {update};
}
