// Explicit test-only UI harness, loaded solely by #editing-checks. Synthetic events are not native IME evidence.
const button=document.createElement('button');button.id='run-editing-checks';button.textContent='Run editing acceptance checks';
const output=document.createElement('pre');output.id='editing-results';output.setAttribute('role','status');
const panel=document.createElement('section');panel.className='panel';panel.setAttribute('aria-label','Synthetic editing acceptance');panel.append(button,output);document.querySelector('main').prepend(panel);
async function wait(test){const start=performance.now();while(!test() || document.getElementById('editor-root')?.getAttribute('aria-busy')==='true'){if(performance.now()-start>7000)throw Error('Timed out waiting for editor');await new Promise(r=>setTimeout(r,30));}}
const $=id=>document.getElementById(id);
function input(id,value){$(id).value=value;$(id).dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText'}));}
button.addEventListener('click',async()=>{
 button.disabled=true;const result={synthetic_composition:true,native_ime_verified:false,tests:[]};
 const check=(name,pass)=>{result.tests.push({name,pass:Boolean(pass)});if(!pass)throw Error(name);};
 const rev=()=>Number($('project-meta').textContent.match(/Revision (\d+)/)?.[1]);
 try{
 await wait(()=>$('create-form').querySelector('button').disabled===false);
 input('project-name','Editing and Telugu composition acceptance');input('initial-text','కొత్త ఆలోచన / New idea');$('create-form').requestSubmit();await wait(()=>rev()===0 && !$('save').disabled);
 const area=$('layer-text');area.focus();area.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:''}));
 input('layer-text','శ్రీ విద్య క్షేత్రం\nEnglish é é');area.setSelectionRange(3,5);const caret=[area.selectionStart,area.selectionEnd];
 check('composition keeps Apply and Save disabled',$('apply-text').disabled&&$('save').disabled);
 document.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'s',ctrlKey:true,isComposing:true}));check('composition shortcut does not change revision',rev()===0);
 $('refresh-analysis').click();await new Promise(r=>setTimeout(r,120));check('refresh preserves composing text and caret',area.value==='శ్రీ విద్య క్షేత్రం\nEnglish é é'&&area.selectionStart===caret[0]&&area.selectionEnd===caret[1]);
 area.dispatchEvent(new CompositionEvent('compositionend',{bubbles:true,data:area.value}));area.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertCompositionText'}));check('composition end enables explicit Apply',!$('apply-text').disabled);
 area.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'Enter',ctrlKey:true}));await wait(()=>rev()===1 && !$('save').disabled);
 check('Apply preserves exact text',area.value==='శ్రీ విద్య క్షేత్రం\nEnglish é é');check('focus returns to text after Apply',document.activeElement===area);
 $('font-size').value='40';$('apply-font').click();await wait(()=>rev()===2 && !$('save').disabled);
 const source=$('render-status').textContent;$('preview-zoom').value='100';$('preview-zoom').dispatchEvent(new Event('change'));check('zoom is preview-only',$('poster-checker').style.width==='1080px'&&$('render-status').textContent===source);
 $('preview-zoom').value='fit';$('preview-zoom').dispatchEvent(new Event('change'));
 $('add-rectangle').click();await wait(()=>rev()===3 && !$('save').disabled);
 const layers=()=>[...$('layers').querySelectorAll('button')];layers()[1].focus();layers()[1].dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'Home'}));await wait(()=>layers()[0].getAttribute('aria-pressed')==='true'&&document.activeElement===layers()[0]);
 check('Home selects and focuses first layer',layers()[0].tabIndex===0&&layers()[1].tabIndex===-1);
 input('layer-text','తెలుగు draft é');layers()[0].dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'End'}));await wait(()=>rev()===4&&layers()[1].getAttribute('aria-pressed')==='true');
 layers()[1].dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'Home'}));await wait(()=>layers()[0].getAttribute('aria-pressed')==='true'&&!$('save').disabled);check('switching layers preserves pending draft',area.value==='తెలుగు draft é');
 document.dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'s',ctrlKey:true}));await wait(()=>$('save-state').textContent==='Saved locally');
 const id=$('project-list').value;const model=(await(await fetch('/api/project/'+id)).json()).project;check('saved source preserves Telugu and combining marks',model.content.find(c=>c.id===model.elements[0].content_id).text==='తెలుగు draft é');
 const revisionBefore=rev();$('remove-layer').click();await wait(()=>$('workflow-dialog').open);check('remove requires confirmation',rev()===revisionBefore);$('workflow-cancel').click();check('cancel removal preserves project',rev()===revisionBefore&&!$('workflow-dialog').open);
 $('remove-layer').click();await wait(()=>$('workflow-dialog').open);$('workflow-discard').click();await wait(()=>rev()===revisionBefore+1&&!$('save').disabled);check('layer removal applied once',layers().length===1);
 $('undo').click();await wait(()=>rev()===revisionBefore+2&&!$('save').disabled);check('undo restores removed layer',layers().length===2);
 layers()[0].click();await wait(()=>area.value==='తెలుగు draft é'&&!$('save').disabled);input('layer-text','తెలుగు saved workflow é');$('reopen').click();await wait(()=>$('workflow-dialog').open);$('workflow-cancel').click();check('cancel reopen preserves unapplied text',area.value==='తెలుగు saved workflow é');
 $('reopen').click();await wait(()=>$('workflow-dialog').open);$('workflow-keep').click();await wait(()=>$('save-state').textContent==='Saved locally'&&!$('save').disabled);check('save and reopen preserves draft',area.value==='తెలుగు saved workflow é');
 const stable=rev();input('layer-text','Discard this draft');$('reopen').click();await wait(()=>$('workflow-dialog').open);$('workflow-discard').click();await wait(()=>area.value==='తెలుగు saved workflow é'&&!$('save').disabled);check('explicit discard restores saved text',rev()===stable);
 layers()[0].focus();layers()[0].dispatchEvent(new KeyboardEvent('keydown',{bubbles:true,key:'ArrowRight',altKey:true}));await wait(()=>rev()===stable+1&&!$('save').disabled);check('keyboard nudge changes one source coordinate',Number($('position-x').value)===81);
 $('save').click();await wait(()=>$('save-state').textContent==='Saved locally'&&!$('save').disabled);
 check('analysis remains OFF',$('analysis-state').textContent.startsWith('OFF'));
 check('skip link and descriptions present',Boolean(document.querySelector('a[href="#editor-root"]'))&&area.getAttribute('aria-describedby').includes('composition-status'));
 result.pass=result.tests.every(t=>t.pass);
 }catch(e){result.pass=false;result.error=e.message;}
 output.textContent=JSON.stringify(result,null,2);
 try{const session=await(await fetch('/api/session')).json();const response=await fetch('/api/browser-evidence',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf},body:JSON.stringify({results:result})});const saved=await response.json();output.textContent+='\nEvidence: '+saved.evidence;}catch(e){output.textContent+='\nEvidence save failed: '+e.message;}
 button.disabled=false;
});
