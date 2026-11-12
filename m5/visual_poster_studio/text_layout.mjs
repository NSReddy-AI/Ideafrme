// Explicit text edits only. No new persisted layout fields or font-shaping implementation.
export function wrapText(text,width,measure){
 if(typeof text!=='string'||Array.from(text).length>20000||!Number.isFinite(width)||width<1||width>4096)throw Error('Invalid text or wrap width.');
 if(!globalThis.Intl?.Segmenter)throw Error('Safe grapheme segmentation unavailable; use explicit newlines.');
 const segmenter=new Intl.Segmenter(undefined,{granularity:'grapheme'}),rows=[];
 const push=line=>{rows.push(line);if(rows.length>64)throw Error('Wrapping exceeds 64 lines; text was not changed.');};
 for(const paragraph of text.split('\n')){
  let line='';
  for(let token of paragraph.match(/\s+|\S+/gu)||[]){
   if(measure(line+token)<=width){line+=token;continue;}
   if(line){push(line);line='';}
   if(measure(token)<=width){line=token;continue;}
   let parts=Array.from(segmenter.segment(token),s=>s.segment),offset=0;
   while(offset<parts.length){let low=1,high=parts.length-offset,best=0;
    while(low<=high){const n=Math.floor((low+high)/2);if(measure(parts.slice(offset,offset+n).join(''))<=width){best=n;low=n+1;}else high=n-1;}
    if(!best)throw Error('One grapheme exceeds the text box. Increase width or reduce font size.');
    const piece=parts.slice(offset,offset+best).join('');offset+=best;if(offset<parts.length)push(piece);else line=piece;
   }
  }
  push(line);
 }
 return rows.join('\n');
}
export function fitTextBox(text,size,measure,descent=0){
 if(!Number.isInteger(size)||size<1||size>512||!Number.isFinite(descent)||descent<0)throw Error('Invalid text measurement.');
 const lines=text.split('\n');if(lines.length>64)throw Error('64 lines maximum.');
 return {width:Math.max(1,Math.ceil(Math.max(...lines.map(measure))+2)),height:Math.max(1,Math.ceil(size*1.02+(lines.length-1)*size*1.65+descent+2))};
}
export function keyboardGeometry(event,composing,editable){
 if(composing||event.isComposing||event.keyCode===229||editable||!event.altKey||!event.ctrlKey||event.metaKey)return null;
 const step=event.shiftKey?10:1;return ({ArrowLeft:{dw:-step,dh:0},ArrowRight:{dw:step,dh:0},ArrowUp:{dw:0,dh:-step},ArrowDown:{dw:0,dh:step}})[event.key]||null;
}
export function fontRuns(text){const out=[];for(const ch of text){const cp=ch.codePointAt(0),lang=(cp>=0x0c00&&cp<=0x0c7f)||cp===0x200c||cp===0x200d?'te':'en';if(out.at(-1)?.lang===lang)out.at(-1).text+=ch;else out.push({lang,text:ch});}return out;}
