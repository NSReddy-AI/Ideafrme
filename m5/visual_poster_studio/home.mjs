// Same-document navigation: editor drafts remain in their existing DOM/state.
export function installHome(api){
 const $=id=>document.getElementById(id),main=document.querySelector('main.workspace');
 const editorPanels=[...main.children].filter(e=>!['home-screen','projects-screen','recovery-screen','brands-screen'].includes(e.id));let active='home',catalogue=null;
 const message=(text,error=false)=>{$('home-status').textContent=text;$('navigation-status').textContent=text;$('home-status').classList.toggle('error',error);};
 function route(name,focus=true){
  if(!api.ready()){message('Finish the current action or text composition before navigating.',true);return;}
  active=name;for(const p of editorPanels)p.hidden=name!=='editor';
  for(const n of ['home','projects','recovery','brands'])$(n+'-screen').hidden=name!==n;
  for(const b of document.querySelectorAll('[data-page]'))b.setAttribute('aria-current',b.dataset.page===name?'page':'false');
  if(focus)(name==='editor'?$('editor-root'):$(name+'-title')).focus({preventScroll:true});
  if(name==='brands')document.dispatchEvent(new Event('studio-brand-open'));
  if(name!=='editor')refresh();
 }
 async function refresh(){
  try{
   const [nav,sessions]=await Promise.all([api.request('/api/navigation'),api.request('/api/sessions')]);catalogue=sessions;
   $('home-summary').textContent=`${nav.projects.length} projects in this session · ${nav.exports.length} retained exports · Analysis OFF`;
   $('home-session').textContent=nav.runtime_root;$('home-projects').replaceChildren();
   if(!nav.projects.length){const p=document.createElement('p');p.textContent='No projects in this session. Create a poster or explicitly resume another session.';$('home-projects').append(p);}
   for(const p of nav.projects){const row=document.createElement('article'),title=document.createElement('h3'),detail=document.createElement('p'),open=document.createElement('button');title.textContent=p.name;detail.textContent=`ID: ${p.project_id} · ${p.saved?'Saved version available':'Not yet saved'}${p.dirty?' · Unsaved working changes':''}`;open.textContent='Open in editor';open.addEventListener('click',async()=>{if(await api.open(p.project_id))route('editor');});row.append(title,detail,open);$('home-projects').append(row);}
   const select=$('home-sessions'),previous=select.value;select.replaceChildren();const placeholder=new Option('Choose a session explicitly','');select.append(placeholder);
   for(const s of sessions.sessions){const option=new Option(`${s.directory}${s.session_id===sessions.current_session_id?' · active':''} · ${s.status}`,s.directory);option.disabled=!s.session_id||s.session_id===sessions.current_session_id;select.append(option);}select.value=previous;
   $('session-empty').textContent=sessions.sessions.length?'Sorted by observed folder modification time; not last opened. Project names from other sessions are unavailable until explicit resume.':'No resumable owned sessions found.';
   $('recovery-list').replaceChildren();const issues=Object.entries(nav.recovery);
   if(!issues.length)$('recovery-list').textContent='No blocked projects reported in the active session.';
   for(const [id,value] of issues){const p=document.createElement('p');p.textContent=`Project ${id}: ${value.state}. Original files are preserved; use explicit recovery-copy instructions.`;$('recovery-list').append(p);}
   $('recovery-help').textContent=`Stop the service before CLI recovery. Existing journal-copy recovery: python3 -B -m visual_poster_studio --resume --root '${nav.runtime_root.replaceAll("'","'\\''")}' --recover-copy <project-id> --candidate after. Immutable checkpoint restoration: python3 -B -m visual_poster_studio.checkpoint_restore --session <session-root> --project <project-id> --checkpoint <sha256> --acknowledge-lost-subsequent-edits. Both create a separate session; later edits are excluded. No recovery is run by this screen.`;
   message('Local workspace refreshed.');
  }catch(e){message('Workspace unavailable: '+e.message,true);}
 }
 for(const b of document.querySelectorAll('[data-page]'))b.addEventListener('click',()=>route(b.dataset.page));
 $('home-create').addEventListener('click',()=>{route('editor');if(active==='editor'){document.getElementById('create-form').closest('details').open=true;$('project-name').focus();}});
 $('home-open').addEventListener('click',()=>route('projects'));
 $('home-resume').addEventListener('click',()=>{route('projects');$('home-sessions').focus();});
 $('home-refresh').addEventListener('click',refresh);
 $('home-switch').addEventListener('click',async()=>{
  if(!api.ready()||api.pending()){message('Save or discard unsubmitted editor/brand fields before changing sessions.',true);return;}
  const s=catalogue?.sessions.find(s=>s.directory===$('home-sessions').value);if(!s?.session_id){message('Choose an available session first.',true);return;}
  if(!$('home-resume-ack').checked){message('Acknowledge explicit session switching first.',true);return;}
  $('home-switch').disabled=true;
  try{await api.request('/api/session/switch',{current_session_id:catalogue.current_session_id,target_session_id:s.session_id,directory:s.directory});location.hash='projects';location.reload();}
  catch(e){message('Session was not switched: '+e.message,true);$('home-switch').disabled=false;}
 });
 document.querySelector('.skip-link').addEventListener('click',event=>{event.preventDefault();route('editor');});
 api.onCreated(()=>route('editor',false));
 route(location.hash==='#projects'?'projects':location.hash.endsWith('checks')?'editor':'home',false);
 return {route,refresh};
}
