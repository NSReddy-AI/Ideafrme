import assert from 'node:assert/strict';
import {targetsFor,translate,resizeBox} from '../visual_poster_studio/geometry.mjs';
const box={id:'a',x:100,y:100,width:200,height:100},view={width:1080,height:1350};let checks=0;const eq=(a,b)=>{assert.deepEqual(a,b);checks++;};
eq(targetsFor([box],['a']),[{element_id:'a',x:100,y:100,width:200,height:100}]);eq(translate(targetsFor([box],['a']),10,20)[0].x,110);
eq(resizeBox(box,'se',50,20,false,view),{x:100,y:100,width:250,height:120});eq(resizeBox(box,'nw',20,10,true,view),{x:120,y:110,width:180,height:90});
for(const corner of ['nw','ne','sw','se']){const b=resizeBox(box,corner,30,40,true,view);assert.ok(Math.abs(b.width/b.height-2)<1e-10);assert.ok(b.width>0&&b.height>0);checks++;}
eq(resizeBox(box,'se',10000,10000,false,view),{x:100,y:100,width:980,height:1250});assert.throws(()=>resizeBox(box,'wrong',0,0,false,view));checks++;assert.throws(()=>translate([],NaN,0));checks++;
console.log(JSON.stringify({checks,failures:0}));
