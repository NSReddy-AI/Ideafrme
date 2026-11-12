import assert from 'node:assert/strict';
import {compositionActive,shortcut,textStats,nextLayerIndex,zoomWidth} from '../visual_poster_studio/editing.mjs';
let checks=0;function check(actual,expected){assert.deepEqual(actual,expected);checks++;}
check(compositionActive({isComposing:true},null),true);check(compositionActive({keyCode:229},null),true);check(compositionActive({},'layer-text'),true);check(compositionActive({},null),false);
for(const key of ['s','z','y','Enter'])check(shortcut({key,ctrlKey:true,isComposing:true},null),null);
check(shortcut({key:'s',metaKey:true},null),'save');check(shortcut({key:'Enter',ctrlKey:true},null,true),'apply-text');check(shortcut({key:'z',ctrlKey:true},null,true),null);check(shortcut({key:'z',ctrlKey:true},null,false),'undo');check(shortcut({key:'z',ctrlKey:true,shiftKey:true},null,false),'redo');check(shortcut({key:'s',ctrlKey:true,altKey:true},null),null);
check(textStats('తెలుగు\né'),{codePoints:9,lines:2});check(textStats('🦄'),{codePoints:1,lines:1});check(textStats('é').codePoints,1);check(textStats('é').codePoints,2);
check(nextLayerIndex(0,'ArrowUp',3),0);check(nextLayerIndex(2,'ArrowDown',3),2);check(nextLayerIndex(2,'Home',3),0);check(nextLayerIndex(0,'End',3),2);check(nextLayerIndex(0,'End',0),-1);
check(zoomWidth('fit'),'min(100%, 540px)');check(zoomWidth('50'),'540px');check(zoomWidth('100'),'1080px');assert.throws(()=>zoomWidth('200'));checks++;


import {dialogStillCurrent,nudge} from '../visual_poster_studio/editing.mjs';
const state={project_id:'p',revision:4};const snapshot={projectId:'p',revision:4,selected:'a'};
check(dialogStillCurrent(snapshot,state,'a'),true);check(dialogStillCurrent(snapshot,{...state,revision:5},'a'),false);check(dialogStillCurrent(snapshot,state,'b'),false);
check(nudge({altKey:true,key:'ArrowLeft'},null),{x:-1,y:0});check(nudge({altKey:true,shiftKey:true,key:'ArrowDown'},null),{x:0,y:10});check(nudge({altKey:true,key:'ArrowUp'},'layer-text'),null);check(nudge({altKey:true,key:'ArrowUp'},null,true),null);check(nudge({altKey:true,ctrlKey:true,key:'ArrowUp'},null),null);
console.log(JSON.stringify({tests:checks,failures:0,network:false,dependencies:'node built-in assert only'}));
