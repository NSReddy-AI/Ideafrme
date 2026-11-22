// Pinned metadata only. No asset/font file loading or user-defined code.
export function installBrandApplication(api){
 const $=id=>document.getElementById(id);let stamp=null;
 return {update(locked){
  const p=api.current(),state=p?.brand_application,selected=api.selected?.(),identity=JSON.stringify([p?.project_id,p?.revision,state,selected,locked]);if(identity===stamp)return;stamp=identity;
  const colors=$('brand-a-colors');colors.replaceChildren();
  if(!state?.bound_brand){$('brand-a-status').textContent='Brand Application A: unbranded project; manual controls remain available.';$('brand-a-details').textContent='Select an approved brand through the existing explicit binding workflow to use its palette and supported typography.';return;}
  $('brand-a-status').textContent=state.export_eligible?'Brand Application A: current palette, supported typography and recognized rules satisfied. Draft only.':'Brand Application A: '+state.note+' '+(state.policy?.blocked||[]).join(' ')+(Object.keys(state.violations||{}).length?' Violations: '+Object.keys(state.violations).join(', '):'');
  $('brand-a-details').textContent=JSON.stringify(state.policy,null,2);
  for(const color of state.policy?.colors||[]){const b=document.createElement('button');b.type='button';b.textContent='Apply '+color+' to selected layer';b.disabled=locked||!state.supported||!selected||p.elements.find(e=>e.id===selected)?.style.fill.toLowerCase()===color.toLowerCase();b.style.borderLeft='12px solid '+color;
   b.addEventListener('click',()=>api.run(async()=>{if(api.pending())throw Error('Apply or discard unsubmitted text/brief fields first.');const current=api.current(),id=api.selected?.();if(!id)throw Error('Select exactly one layer.');const result=await api.request('/api/action',{action:'color',project_id:current.project_id,expected_revision:current.revision,element_id:id,color});(api.updated||api.opened)(result.project);},'Approved pinned color applied as one undoable layer edit.'));
   colors.append(b);
  }
 }};
}
