// Pure editing policy. Browser/OS retain shaping, grapheme segmentation and IME ownership.
export function compositionActive(event,field){return Boolean(field || event?.isComposing || event?.keyCode===229);}
export function shortcut(event,field,editable=false){
 if(compositionActive(event,field) || !(event.ctrlKey||event.metaKey) || event.altKey)return null;
 const key=event.key?.toLowerCase();
 if(key==='s')return 'save';
 if(key==='enter')return 'apply-text';
 if(!editable && key==='z')return event.shiftKey?'redo':'undo';
 if(!editable && key==='y')return 'redo';
 return null;
}
export function textStats(text){return {codePoints:Array.from(text).length,lines:text.split('\n').length};}
export function nextLayerIndex(index,key,count){
 if(!count)return -1;
 if(key==='Home')return 0;if(key==='End')return count-1;
 if(key==='ArrowDown')return Math.min(count-1,index+1);
 if(key==='ArrowUp')return Math.max(0,index-1);
 return index;
}
export function zoomWidth(value){
 if(value==='fit')return 'min(100%, 540px)';
 if(!['25','50','75','100'].includes(String(value)))throw Error('Unsupported preview zoom.');
 return `${1080*Number(value)/100}px`;
}

export function dialogStillCurrent(snapshot,project,selected){return Boolean(snapshot && project && snapshot.projectId===project.project_id && snapshot.revision===project.revision && snapshot.selected===selected);}
export function nudge(event,field,editable=false){
 if(editable || compositionActive(event,field) || !event.altKey || event.ctrlKey || event.metaKey)return null;
 const step=event.shiftKey?10:1;
 return ({ArrowLeft:{x:-step,y:0},ArrowRight:{x:step,y:0},ArrowUp:{x:0,y:-step},ArrowDown:{x:0,y:step}})[event.key] || null;
}
