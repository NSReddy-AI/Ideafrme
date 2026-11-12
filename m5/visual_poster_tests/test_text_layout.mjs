import assert from 'node:assert/strict';
import {wrapText,fitTextBox,keyboardGeometry,fontRuns} from '../visual_poster_studio/text_layout.mjs';
let checks=0;const eq=(a,b)=>{assert.deepEqual(a,b);checks++;};const width=s=>[...new Intl.Segmenter(undefined,{granularity:'grapheme'}).segment(s)].length;
eq(wrapText('hello world',6,width),'hello \nworld');eq(wrapText('a\n\nb',20,width),'a\n\nb');eq(wrapText('ééé',2,width),'éé\né');
for(const text of ['తెలుగు శ్రీ క్ష','a  b   c','é 🧑‍💻 Z','క్షక్షక్ష','A\nB']){const wrapped=wrapText(text,3,width);eq(wrapped.replaceAll('\n',''),text.replaceAll('\n',''));assert.ok(wrapped.split('\n').every(s=>width(s)<=3));checks++;}
for(const args of [['a',0],['a',NaN],['a'.repeat(20001),10],['a'.repeat(65),1]]){assert.throws(()=>wrapText(...args,width));checks++;}
assert.throws(()=>wrapText('é',1,()=>2));checks++;
eq(fitTextBox('a\nb',20,s=>s.length*10,5),{width:12,height:61});eq(fontRuns('aతెలుగుb').map(r=>r.lang),['en','te','en']);
eq(keyboardGeometry({ctrlKey:true,altKey:true,key:'ArrowRight'},false,false),{dw:1,dh:0});eq(keyboardGeometry({ctrlKey:true,altKey:true,shiftKey:true,key:'ArrowUp'},false,false),{dw:0,dh:-10});
for(const flags of [{isComposing:true},{keyCode:229},{metaKey:true}])eq(keyboardGeometry({ctrlKey:true,altKey:true,key:'ArrowRight',...flags},false,false),null);
eq(keyboardGeometry({ctrlKey:true,altKey:true,key:'ArrowRight'},true,false),null);eq(keyboardGeometry({ctrlKey:true,altKey:true,key:'ArrowRight'},false,true),null);
console.log(JSON.stringify({checks,failures:0}));
