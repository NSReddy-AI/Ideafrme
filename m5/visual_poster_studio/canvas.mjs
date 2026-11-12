// Native Pointer Events controller; source edits use the existing one-layer move transaction.
import {targetsFor,translate} from './geometry.mjs';
import {sourcePoint,hitLayers} from './layout.mjs';
export function selectionBounds(elements,ids){
 const set=new Set(ids),items=elements.filter(e=>set.has(e.id));if(!items.length)return null;
 const x=Math.min(...items.map(e=>e.x)),y=Math.min(...items.map(e=>e.y));return {x,y,width:Math.max(...items.map(e=>e.x+e.width))-x,height:Math.max(...items.map(e=>e.y+e.height))-y};
}
export function toggleSelection(ids,identity){const next=new Set(ids);if(next.has(identity)){if(next.size>1)next.delete(identity);}else next.add(identity);return [...next];}
export function snappedMove(element,dx,dy,view,options={},others=[]){
 if(![dx,dy].every(Number.isFinite))throw Error('Invalid drag coordinates.');
 if(element.width>view.width||element.height>view.height)throw Error('Layer exceeds canvas size; use precision position controls.');
 let x=element.x+dx,y=element.y+dy;
 const axis=options.constrain?(Math.abs(dx)>=Math.abs(dy)?'x':'y'):null;
 if(axis==='x')y=element.y;if(axis==='y')x=element.x;
 const grid=Number(options.grid||0),margin=Number(options.margin??32),tolerance=Number(options.tolerance??8);
 if(grid && (!Number.isInteger(grid)||grid<1||grid>100))throw Error('Grid must be an integer from 1 to 100.');
 if(!Number.isInteger(margin)||margin<0||margin>540||!Number.isFinite(tolerance)||tolerance<0)throw Error('Invalid snapping settings.');
 const clamp=(v,max)=>Math.max(0,Math.min(max,Math.round(v)));
 if(!options.bypass&&grid){x=Math.round(x/grid)*grid;y=Math.round(y/grid)*grid;}
 const guides=[];
 if(!options.bypass&&options.snap){
  const pick=(value,max,targets,axisName)=>{
   let nearest=null;
   for(const target of targets){const at=Math.round(target);if(at<0||at>max)continue;const distance=Math.abs(at-value);if(distance<=tolerance&&(!nearest||distance<nearest.distance))nearest={at,distance};}
   if(nearest){guides.push(axisName);return nearest.at;}return value;
  };
  const tx=[0,margin,(view.width-element.width)/2,view.width-margin-element.width,view.width-element.width],ty=[0,margin,(view.height-element.height)/2,view.height-margin-element.height,view.height-element.height];
  for(const e of others){if(e.id===element.id)continue;tx.push(e.x,e.x+e.width-element.width,e.x+e.width/2-element.width/2);ty.push(e.y,e.y+e.height-element.height,e.y+e.height/2-element.height/2);}
  if(axis!=='y')x=pick(x,view.width-element.width,tx,'x');if(axis!=='x')y=pick(y,view.height-element.height,ty,'y');
 }
 if(axis==='x')y=element.y;if(axis==='y')x=element.x;
 return {x:clamp(x,view.width-element.width),y:clamp(y,view.height-element.height),guides};
}
export function sameGesture(snapshot,current){return Boolean(current&&snapshot.projectId===current.projectId&&snapshot.revision===current.revision);}
export function installDrag(image,api){
 let gesture=null,skipClick=false;
 image.draggable=false;
 image.addEventListener('dragstart',event=>event.preventDefault());
 const release=()=>{const g=gesture;gesture=null;if(g&&image.hasPointerCapture?.(g.pointerId))image.releasePointerCapture(g.pointerId);api.lock(false);api.preview(null);};
 const cancel=message=>{if(!gesture)return;release();skipClick=true;if(message)api.message(message);};
 image.addEventListener('pointerdown',event=>{
  if(event.button!==0||event.isPrimary===false||gesture)return;
  skipClick=false;
  const state=api.snapshot();if(!state||!api.ready())return;
  const rect=image.getBoundingClientRect(),point=sourcePoint(event.clientX,event.clientY,rect,state.view),id=hitLayers(state.elements,point)[0];if(!id)return;
  gesture={...state,rect,id,element:{...state.elements.find(e=>e.id===id)},pointerId:event.pointerId,startX:event.clientX,startY:event.clientY,moved:false,proposal:null};
  if(event.isTrusted){try{image.setPointerCapture(event.pointerId);}catch(_){gesture=null;api.message('Pointer capture unavailable; drag cancelled.');return;}}
  // Lock only after actual movement, preserving ordinary click/Shift-click selection.
 });
 image.addEventListener('pointermove',event=>{
  const g=gesture;if(!g||event.pointerId!==g.pointerId)return;
  const sx=event.clientX-g.startX,sy=event.clientY-g.startY;if(!g.moved&&Math.hypot(sx,sy)<3)return;
  if(!g.moved){
   if(g.selection.length>1&&!g.selection.includes(g.id)){cancel('Drag inside the selected group.');return;}
   if(g.selection.length>1)g.element={...selectionBounds(g.elements,g.selection),id:'group'};
   if(g.pendingText){cancel('Apply text before dragging; your draft was preserved.');return;}
   g.moved=true;api.lock(true);
  }
  event.preventDefault();
  try{
   const options={...api.options(),bypass:event.altKey,constrain:event.shiftKey,tolerance:8*g.view.width/g.rect.width};
   g.proposal=snappedMove(g.element,sx*g.view.width/g.rect.width,sy*g.view.height/g.rect.height,g.view,options,g.elements);
   api.preview({...g.element,...g.proposal});
  }catch(e){cancel(e.message);}
 });
 image.addEventListener('pointerup',event=>{
  const g=gesture;if(!g||event.pointerId!==g.pointerId)return;
  const current=api.snapshot();release();
  if(!g.moved)return;
  skipClick=true;
  if(!sameGesture(g,current)){api.message('Project changed during drag; nothing was moved.');return;}
  if(g.proposal&&(g.proposal.x!==g.element.x||g.proposal.y!==g.element.y))api.commit(g,g.proposal,g.selection.length>1?translate(targetsFor(g.elements,g.selection),g.proposal.x-g.element.x,g.proposal.y-g.element.y):null);
 });
 image.addEventListener('pointercancel',()=>cancel('Drag cancelled; source unchanged.'));
 image.addEventListener('lostpointercapture',()=>{if(gesture)cancel('Drag capture lost; source unchanged.');});
 window.addEventListener('blur',()=>cancel('Drag cancelled when the window lost focus.'));
 document.addEventListener('keydown',event=>{if(gesture&&event.key==='Escape'){event.preventDefault();cancel('Drag cancelled; source unchanged.');}});
 return {consumeClick(){const value=skipClick;skipClick=false;return value;},cancel};
}
