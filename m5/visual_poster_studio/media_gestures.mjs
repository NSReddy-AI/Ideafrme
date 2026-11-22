import {snappedMove} from '/canvas.mjs';
import {resizeBox} from '/geometry.mjs';
export function hitPNG(items,x,y){return [...items].reverse().find(p=>x>=p.geometry.x&&y>=p.geometry.y&&x<=p.geometry.x+p.geometry.width&&y<=p.geometry.y+p.geometry.height)||null;}
export function installPNGGestures(api){
 const image=document.getElementById('poster-preview'),host=document.getElementById('poster-checker');let selected=null,active=null;
 const box=document.createElement('div');box.className='media-gesture-box';box.hidden=true;host.append(box);
 const handles=['nw','ne','sw','se'].map(c=>{const b=document.createElement('button');b.type='button';b.className='media-corner';b.dataset.corner=c;b.setAttribute('aria-label','Resize PNG '+c+' corner; aspect ratio protected');b.hidden=true;host.append(b);return b;});
 image.tabIndex=0;image.setAttribute('aria-describedby','preview-selection-help');
 function current(){return api.current()?.media_context;}
 function layer(){return current()?.placements.find(p=>p.id===selected);}
 function show(g){const p=api.current(),r=image.getBoundingClientRect();const visible=g&&r.width>0&&!image.hidden;box.hidden=!visible;for(const b of handles)b.hidden=!visible;if(!visible)return;for(const [k,n] of Object.entries(g))box.style[k==='x'?'left':k==='y'?'top':k]=(n/(k==='x'||k==='width'?p.view.width:p.view.height)*100)+'%';for(const b of handles){b.style.left=((g.x+(b.dataset.corner.includes('e')?g.width:0))/p.view.width*100)+'%';b.style.top=((g.y+(b.dataset.corner.includes('s')?g.height:0))/p.view.height*100)+'%';b.style.transform='translate(-50%,-50%)';}}
 function render(){if(selected&&!layer())selected=null;document.body.classList.toggle('png-selected',Boolean(selected&&layer()));show(active?.proposal||layer()?.geometry);}
 function choose(id){selected=id;api.selected(id);render();}
 function finish(){const g=active;active=null;if(g){try{if(g.target.hasPointerCapture(g.pointerId))g.target.releasePointerCapture(g.pointerId);}catch(_){}api.lock(false);}render();return g;}
 function cancel(){if(active){finish();api.message('PNG gesture cancelled; saved geometry unchanged.');}}
 function begin(event,target,corner=null){if(event.button!==0||active||!api.ready())return;let item=layer();const p=api.current(),rect=image.getBoundingClientRect();if(!p?.media_context||!rect.width)return;
  if(!corner){const x=(event.clientX-rect.left)*p.view.width/rect.width,y=(event.clientY-rect.top)*p.view.height/rect.height;item=hitPNG(p.media_context.placements,x,y);if(!item){choose(null);return;}choose(item.id);}
  if(!item)return;event.preventDefault();event.stopImmediatePropagation();image.focus({preventScroll:true});active={item:structuredClone(item),target,corner,pointerId:event.pointerId,sx:event.clientX,sy:event.clientY,rect,view:p.view,head:p.media_context.head,id:p.media_context.id,proposal:null};try{target.setPointerCapture(event.pointerId);}catch(_){active=null;return;}api.lock(true);
 }
 function move(event){const g=active;if(!g||g.pointerId!==event.pointerId)return;event.preventDefault();event.stopImmediatePropagation();const dx=(event.clientX-g.sx)*g.view.width/g.rect.width,dy=(event.clientY-g.sy)*g.view.height/g.rect.height;try{if(g.corner)g.proposal=resizeBox(g.item.geometry,g.corner,dx,dy,true,g.view);else{const o=api.options(),m=snappedMove(g.item.geometry,dx,dy,g.view,{...o,constrain:event.shiftKey,bypass:event.altKey},[]);g.proposal={x:m.x,y:m.y,width:g.item.geometry.width,height:g.item.geometry.height};}show(g.proposal);}catch(e){cancel();api.message(e.message);}}
 function up(event){if(!active||active.pointerId!==event.pointerId)return;event.preventDefault();event.stopImmediatePropagation();const g=finish();if(g.proposal&&Object.keys(g.proposal).some(k=>g.proposal[k]!==g.item.geometry[k]))api.commit(g,g.proposal);}
 image.addEventListener('pointerdown',e=>begin(e,image),true);
 for(const target of [image,...handles]){if(target!==image)target.addEventListener('pointerdown',e=>begin(e,target,target.dataset.corner));target.addEventListener('pointermove',move,true);target.addEventListener('pointerup',up,true);target.addEventListener('pointercancel',cancel);target.addEventListener('lostpointercapture',cancel);}
 document.getElementById('layers').addEventListener('click',()=>choose(null),true);image.addEventListener('load',render);window.addEventListener('resize',render);window.addEventListener('blur',cancel);
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&active){event.preventDefault();event.stopImmediatePropagation();cancel();return;}if(!selected||!api.ready()||event.isComposing||event.keyCode===229||event.target.matches('input,textarea,select,[contenteditable="true"]'))return;const p=api.current(),item=layer();if(!item)return;
  if(event.key==='Escape'){choose(null);return;}
  if(event.key==='Delete'||event.key==='Backspace'){event.preventDefault();event.stopImmediatePropagation();api.remove(selected);return;}
  const delta={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[event.key];if(!delta)return;event.preventDefault();event.stopImmediatePropagation();const [dx,dy]=delta.map(n=>n*(event.shiftKey?10:1));const g={item,id:p.media_context.id,head:p.media_context.head};const proposal=event.ctrlKey&&event.altKey?resizeBox(item.geometry,'se',dx,dy,true,p.view):{...item.geometry,x:item.geometry.x+dx,y:item.geometry.y+dy};api.commit(g,proposal);
 },true);
 return {choose,render,selection:()=>selected,cancel};
}
