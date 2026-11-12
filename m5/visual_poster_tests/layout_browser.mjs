// One bounded synthetic project verifies preview selection -> alignment -> history -> save -> export navigation.
const $=id=>document.getElementById(id);const button=document.createElement('button');button.id='run-layout-checks';button.textContent='Run layout workflow check';const output=document.createElement('pre');output.id='layout-results';output.setAttribute('role','status');const panel=document.createElement('section');panel.className='panel';panel.append(button,output);document.querySelector('main').prepend(panel);
async function wait(test){const start=performance.now();while(!test() || $('editor-root').getAttribute('aria-busy')==='true'){if(performance.now()-start>7000)throw Error('Layout check timed out');await new Promise(r=>setTimeout(r,30));}}
const revision=()=>Number($('project-meta').textContent.match(/Revision (\d+)/)?.[1]);
button.addEventListener('click',async()=>{
 button.disabled=true;const results={tests:[],native_ime_verified:false};const check=(name,pass)=>{results.tests.push({name,pass:Boolean(pass)});if(!pass)throw Error(name);};
 try{
 await wait(()=>!$('create-form').querySelector('button').disabled);$('project-name').value='Preview selection and layout';$('initial-text').value='తెలుగు / Layout';$('create-form').requestSubmit();await wait(()=>revision()===0&&!$('save').disabled);
 $('add-rectangle').click();await wait(()=>revision()===1);document.querySelector('[data-align="center-x"]').click();await wait(()=>revision()===2);document.querySelector('[data-align="center-y"]').click();await wait(()=>revision()===3);
 check('alignment source coordinates',Number($('position-x').value)===390&&Number($('position-y').value)===575);
 $('undo').click();await wait(()=>revision()===4);check('alignment undo',Number($('position-y').value)===100);$('redo').click();await wait(()=>revision()===5);
 $('add-ellipse').click();await wait(()=>revision()===6);document.querySelector('[data-align="center-x"]').click();await wait(()=>revision()===7);document.querySelector('[data-align="center-y"]').click();await wait(()=>revision()===8);
 const buttons=()=>[...$('layers').querySelectorAll('button')];buttons()[0].click();await wait(()=>buttons()[0].getAttribute('aria-pressed')==='true');
 const image=$('poster-preview');await image.decode();const rect=image.getBoundingClientRect();image.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:rect.left+rect.width/2,clientY:rect.top+rect.height/2}));await wait(()=>buttons()[2].getAttribute('aria-pressed')==='true');check('preview selects topmost ellipse',buttons()[2].getAttribute('aria-pressed')==='true');
 image.dispatchEvent(new MouseEvent('click',{bubbles:true,altKey:true,clientX:rect.left+rect.width/2,clientY:rect.top+rect.height/2}));await wait(()=>buttons()[1].getAttribute('aria-pressed')==='true');check('Alt-click cycles covered layers',buttons()[1].getAttribute('aria-pressed')==='true');check('selection alone creates no revision',revision()===8);
 check('outline present',!$('selection-outline').hidden);const svg=$('render-status').textContent;$('show-guides').checked=false;$('show-guides').dispatchEvent(new Event('change'));check('guides do not change rendered source',$('render-status').textContent===svg);
 $('save').click();await wait(()=>$('save-state').textContent==='Saved locally'&&!$('save').disabled);
 $('export-png').click();await wait(()=>$('export-status').textContent.startsWith('Draft saved:')&&!$('export-png').disabled);check('export navigation populated',$('export-list').options.length>1&&$('export-receipt').textContent.includes('DRAFT'));
 check('session navigation available',$('session-root').value.includes('/.runtime/studio-ui/')&&$('resume-command').value.includes('--resume'));
 const before=$('render-status').textContent;$('reopen').click();await wait(()=>$('notice').textContent==='Saved version reopened.'&&!$('save').disabled);check('reopen keeps deterministic preview',$('render-status').textContent===before);
 results.pass=results.tests.every(t=>t.pass);
 }catch(e){results.pass=false;results.error=e.message;}
 output.textContent=JSON.stringify(results,null,2);
 try{const session=await(await fetch('/api/session')).json();const response=await fetch('/api/browser-evidence',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf},body:JSON.stringify({results})});output.textContent+='\nEvidence: '+(await response.json()).evidence;}catch(e){output.textContent+='\nEvidence save failed: '+e.message;}button.disabled=false;
});
