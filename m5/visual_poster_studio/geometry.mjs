// UI geometry only; authority is the atomic core transaction validator.
export function targetsFor(elements,ids){const set=new Set(ids);return elements.filter(e=>set.has(e.id)).map(({id,x,y,width,height})=>({element_id:id,x,y,width,height}));}
export function translate(targets,dx,dy){if(![dx,dy].every(Number.isFinite))throw Error('Finite movement required.');return targets.map(t=>({...t,x:t.x+dx,y:t.y+dy}));}
export function resizeBox(box,corner,dx,dy,locked,view){
 if(!['nw','ne','sw','se'].includes(corner)||![dx,dy].every(Number.isFinite))throw Error('Invalid resize.');
 const west=corner.includes('w'),north=corner.includes('n'),ax=west?box.x+box.width:box.x,ay=north?box.y+box.height:box.y;
 let w=Math.max(1,box.width+(west?-dx:dx)),h=Math.max(1,box.height+(north?-dy:dy));
 const maxW=west?ax:view.width-ax,maxH=north?ay:view.height-ay;
 if(maxW<1||maxH<1)throw Error('Resize anchor outside canvas.');
 if(locked){const ratio=box.width/box.height;let scale=Math.abs(w/box.width-1)>=Math.abs(h/box.height-1)?w/box.width:h/box.height;scale=Math.min(scale,maxW/box.width,maxH/box.height);w=box.width*scale;h=w/ratio;}else{w=Math.min(w,maxW);h=Math.min(h,maxH);}
 w=Math.max(1,Math.round(w));h=Math.max(1,Math.round(h));
 return {x:west?ax-w:ax,y:north?ay-h:ay,width:w,height:h};
}
export function installResize(image,handles,api){
 let active=null;
 const finish=()=>{const g=active;active=null;if(g?.button.hasPointerCapture?.(g.pointerId))g.button.releasePointerCapture(g.pointerId);api.lock(false);api.preview(null);return g;};
 const cancel=()=>{if(active){finish();api.message('Resize cancelled; source unchanged.');}};
 for(const button of handles){
 button.addEventListener('pointerdown',event=>{if(event.button!==0||active||!api.ready())return;const s=api.snapshot();if(!s||s.selection.length!==1||s.pendingText)return;const e=s.elements.find(e=>e.id===s.selection[0]);if(!e)return;event.preventDefault();const rect=image.getBoundingClientRect();active={...s,element:e,button,pointerId:event.pointerId,sx:event.clientX,sy:event.clientY,rect,proposal:null};try{if(event.isTrusted)button.setPointerCapture(event.pointerId);}catch(_){active=null;return;}api.lock(true);});
 button.addEventListener('pointermove',event=>{const g=active;if(!g||g.pointerId!==event.pointerId)return;try{let dx=(event.clientX-g.sx)*g.view.width/g.rect.width,dy=(event.clientY-g.sy)*g.view.height/g.rect.height;const o=api.options();if(o.grid&&!event.altKey){dx=Math.round(dx/o.grid)*o.grid;dy=Math.round(dy/o.grid)*o.grid;}g.proposal=resizeBox(g.element,button.dataset.resize,dx,dy,o.aspect||event.shiftKey,g.view);api.preview({...g.proposal,guides:[]});}catch(e){cancel();api.message(e.message);}});
 button.addEventListener('pointerup',event=>{if(!active||active.pointerId!==event.pointerId)return;const g=finish(),now=api.snapshot();if(now?.projectId!==g.projectId||now?.revision!==g.revision){api.message('Stale resize cancelled.');return;}if(g.proposal&&Object.keys(g.proposal).some(k=>g.proposal[k]!==g.element[k]))api.commit(g,[{element_id:g.element.id,...g.proposal}]);});
 button.addEventListener('pointercancel',cancel);button.addEventListener('lostpointercapture',cancel);
 }
 window.addEventListener('blur',cancel);document.addEventListener('keydown',e=>{if(e.key==='Escape')cancel();});
}
