import assert from 'node:assert/strict';
import {sourcePoint,hitLayers,nextHit,clippedBox,alignPosition,shellQuote} from '../visual_poster_studio/layout.mjs';
let tests=0;function equal(a,b){assert.deepEqual(a,b);tests++;}
const view={width:1080,height:1350},box={x:80,y:100,width:300,height:200};
equal(sourcePoint(270,337.5,{left:0,top:0,width:540,height:675},view),{x:540,y:675});
equal(sourcePoint(540,675,{left:0,top:0,width:1080,height:1350},view),{x:540,y:675});
equal(sourcePoint(0,0,{left:10,top:10,width:540,height:675},view),null);
equal(sourcePoint(0,0,{left:0,top:0,width:0,height:675},view),null);
const layers=[{...box,id:'text',type:'text',style:{}},{...box,id:'rect',type:'shape',style:{shape:'rectangle'}},{...box,id:'ellipse',type:'shape',style:{shape:'ellipse'}}];
equal(hitLayers(layers,{x:230,y:200}),['ellipse','rect','text']);equal(hitLayers(layers,{x:80,y:100}),['rect','text']);equal(hitLayers(layers,null),[]);equal(hitLayers(layers,{x:900,y:900}),[]);
equal(nextHit(['a','b'],'b',false),'a');equal(nextHit(['a','b'],'a',true),'b');equal(nextHit(['a','b'],'b',true),'a');equal(nextHit([],null,true),null);
equal(alignPosition(box,view,'left',32),{x:32,y:100});equal(alignPosition(box,view,'right',32),{x:748,y:100});equal(alignPosition(box,view,'center-x',32),{x:390,y:100});equal(alignPosition(box,view,'top',32),{x:80,y:32});equal(alignPosition(box,view,'bottom',32),{x:80,y:1118});equal(alignPosition(box,view,'center-y',32),{x:80,y:575});
for(const margin of [-1,1.5,NaN,541]){assert.throws(()=>alignPosition(box,view,'left',margin));tests++;}
assert.throws(()=>alignPosition({...box,width:1100},view,'left',32));tests++;assert.throws(()=>alignPosition(box,view,'resize',32));tests++;
equal(clippedBox({x:-10,y:0,width:20,height:1350},view),{left:0,top:0,width:1000/1080,height:100});equal(clippedBox({...box,x:2000},view),null);equal(clippedBox(null,view),null);
equal(shellQuote("a'b"),"'a'\"'\"'b'");equal(shellQuote('$(touch nope)'),"'$(touch nope)'");
console.log(JSON.stringify({tests,failures:0,network:false}));
