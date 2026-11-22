import {installProduct} from '/product.mjs';
import {installMedia} from '/media.mjs';
import {installDirector} from '/director.mjs';
import {installBrands} from '/brands.mjs';
import {installHome} from '/home.mjs';
import {wrapText,fitTextBox,keyboardGeometry,fontRuns} from '/text_layout.mjs';
import {targetsFor,translate,installResize} from '/geometry.mjs';
import {loadFonts, inspectScene, qualifyEmbedded, raster, comparePng} from '/browser_acceptance.js';
import {compositionActive, shortcut, textStats, nextLayerIndex, zoomWidth, dialogStillCurrent, nudge} from '/editing.mjs';
import {sourcePoint, hitLayers, nextHit, clippedBox, alignPosition, shellQuote} from '/layout.mjs';
import {selectionBounds,toggleSelection,installDrag} from '/canvas.mjs';
'use strict';
// Local DOM/form UI only. No renderer, media inputs, external assets or agent launches.
const $ = id => document.getElementById(id);
let csrf = null, project = null, selected = null, projects = [], busy = false;
let compositionDisabled=[];
let composingField = null, focusAfter = null, previewSequence = 0;
let navigationData = null;
let brandWorking=false,brandDirty=false,bindingDirty=false;
let workflowVersions=[],workflowProposal=null,workflowImpact=null;
let director=null,mediaBridge=null,productUI=null;
let homeNavigation=null,createdCallback=()=>{};
let resizeHandles=[];
let selectedIds = new Set(), gestureActive = false, dragController = null;
let faces = null, fontReady = false, pngQualified = false, sceneReady = false, currentScene = null, previewURL = null, exporting = false;

function notice(message, error = false) {
  $('notice').textContent = message;
  $('notice').classList.toggle('error', error);
}

async function request(path, body, timeoutMs = 5000) {
  const mapped=mediaBridge?.route(path,body);if(mapped){path=mapped.path;body=mapped.body;timeoutMs=Math.max(timeoutMs,17000);}
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const options = {cache: 'no-store', credentials: 'same-origin', signal: controller.signal};
    if (body !== undefined) {
      options.method = 'POST';
      options.headers = {'Content-Type': 'application/json', 'X-CSRF-Token': csrf || ''};
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    const value = await response.json();
    if (!response.ok) throw new Error(value.detail || 'The local service refused the request.');
    mediaBridge?.observe(value);return value;
  } finally { clearTimeout(timer); }
}

function element() { return project?.elements.find(e => e.id === selected); }
function content(e) { return project?.content.find(c => c.id === e?.content_id); }
function pendingText() {
  const e = element();
  return e?.type === 'text' && $('layer-text').value !== content(e)?.text;
}

function render(preserveText = false) {
  if (composingField) return;
  const locked = busy || exporting || gestureActive;
  renderBinding(locked);
  director?.update(locked);
  mediaBridge?.update(locked);
  productUI?.update(locked);
  for(const id of ['wrap-text','fit-text','cancel-text-draft'])$(id).disabled=locked||!fontReady||selectedIds.size!==1||element()?.type!=='text';
  const current = project?.elements.find(e => e.id === selected);
  if (!current) selected = project?.elements[0]?.id || null;
  const e = element();
  selectedIds=new Set([...selectedIds].filter(id=>project?.elements.some(e=>e.id===id)));
  if(selected && !selectedIds.has(selected))selectedIds=new Set([selected]);
  const multiple=selectedIds.size>1;
  $('selection-count').textContent=`${selectedIds.size} selected${multiple?' · Atomic group geometry':''}`;
  $('select-all-layers').disabled=locked || !project?.elements.length;
  $('select-primary').disabled=locked || !multiple;
  $('project-title').textContent = project?.name || 'Your next idea starts here';
  $('project-meta').textContent = project ? `${project.view.width} × ${project.view.height} source · ${project.media_context?'Media v3 · ':''}Revision ${project.revision}` : 'Create a project to begin manual editing.';
  $('save-state').textContent = project ? (project.dirty || pendingText() ? 'Unsaved changes' : 'Saved locally') : 'No project';
  $('save').disabled = locked || !project;
  $('undo').disabled = locked || !project || (!project.can_undo && !pendingText());
  $('redo').disabled = locked || !project?.can_redo;
  $('reopen').disabled = locked || !project?.saved;
  $('refresh-navigation').disabled=locked;
  $('remove-layer').disabled = locked || multiple || !project || !element();
  $('properties').disabled = locked || multiple || !e;
  document.querySelectorAll('[data-align]').forEach(button=>button.disabled=locked || !e);
  for(const id of ['apply-position','apply-color'])$(id).disabled=locked || !e;
  $('apply-font').disabled=locked || !e || e.type!=='text';
  $('confirm-reorder').disabled=locked || !$('upgrade-ack').checked;
  $('cancel-reorder').disabled=locked;
  const layerIndex = project?.elements.findIndex(x=>x.id===selected) ?? -1;
  $('layer-back').disabled = locked || multiple || !project || layerIndex <= 0;
  $('layer-forward').disabled = locked || multiple || !project || layerIndex < 0 || layerIndex >= project.elements.length-1;
  $('text-fields').hidden = !e || e.type !== 'text';
  $('font-field').hidden = !e || e.type !== 'text';
  $('create-form').querySelectorAll('input,textarea,select,button').forEach(x => x.disabled = locked || !csrf);
  $('project-list').disabled = locked || !csrf;
  const remaining = project?.remaining_text_slots || {en: 0, te: 0};
  $('add-language').disabled = locked || !project;
  $('add-text').disabled = locked || !project || !remaining[$('add-language').value] || project.elements.length >= project.element_limit;
  for (const id of ['add-rectangle', 'add-ellipse']) $(id).disabled = locked || !project || project.elements.length >= project.element_limit;
  $('capacity').textContent = project ? `${remaining.en} English and ${remaining.te} Telugu text slots free · ${project.elements.length} / ${project.element_limit} layers` : 'Up to 32 text layers and 64 layers total.';
  const list = $('layers'); list.replaceChildren();
  if (!project) {
    const li = document.createElement('li'); li.className = 'empty'; li.textContent = 'Your layers will appear here.'; list.append(li);
  }
  project?.elements.forEach((layer, index) => {
    const li = document.createElement('li'), button = document.createElement('button');
    button.type = 'button'; button.disabled = locked;
    button.classList.toggle('selected', selectedIds.has(layer.id));
    button.setAttribute('aria-pressed', String(selectedIds.has(layer.id)));
    button.dataset.layerId = layer.id; button.tabIndex = layer.id === selected ? 0 : -1;
    const label = document.createElement('span'); label.className = 'layer-label';
    label.textContent = `${index + 1} · ${layer.type === 'text' ? (content(layer)?.language === 'te' ? 'TELUGU TEXT' : 'ENGLISH TEXT') : 'GEOMETRY'}`;
    const excerpt = document.createElement('span'); excerpt.className = 'layer-text';
    excerpt.textContent = layer.type === 'text' ? content(layer)?.text : layer.style.shape;
    button.append(label, excerpt);
    button.addEventListener('click', event => {
      selectLayer(layer.id,event.shiftKey || event.ctrlKey || event.metaKey);
    });
    li.append(button); list.append(li);
  });
  if (e && !preserveText) {
    $('layer-text').value = e.type === 'text' ? content(e).text : '';
    $('position-x').value = String(e.x); $('position-y').value = String(e.y);
    $('font-size').value = e.style.font_size || 64;
    $('layer-color').value = e.style.fill;
    $('layer-text').lang = e.type === 'text' ? content(e).language : 'en';
  }
  $('apply-text').disabled = locked || !e || e.type !== 'text' || !pendingText();
  $('save-state').textContent = project ? (project.dirty || pendingText() ? 'Unsaved changes' : 'Saved locally') : 'No project';
  updateTextStatus(); exportButtons(); updateSelection();
}

async function refreshProjects() {
  projects = (await request('/api/projects')).projects;
  const list = $('project-list'); list.replaceChildren();
  const placeholder = document.createElement('option'); placeholder.value = ''; placeholder.textContent = 'Choose a project'; list.append(placeholder);
  for (const item of projects) {
    const option = document.createElement('option'); option.value = item.project_id;
    option.textContent = `${item.name} · ${item.project_id.slice(0,8)}${item.dirty ? ' · unsaved' : ''}`; list.append(option);
  }
  list.value = project?.project_id || '';
  $('navigation-summary').textContent=`${projects.length} projects · ${navigationData?.exports.length ?? 0} retained exports · Analysis OFF`;
}

async function action(kind, extras = {}) {
  if (!project) return;
  project = (await request('/api/action', {project_id: project.project_id, expected_revision: project.revision, action: kind, ...extras})).project;
}

async function flushText() {
  if (pendingText()) await action('edit_text', {element_id: selected, text: $('layer-text').value});
}

async function run(task, message) {
  if (busy || exporting || gestureActive || $('workflow-dialog').open) return;
  if (composingField) {notice('Finish text composition before applying an action.');return;}
  const focusedId=document.activeElement?.id;
  busy = true;
  director?.update(true);
  productUI?.update(true);
  $('project-binding-panel').querySelectorAll('input,select,textarea,button').forEach(x=>x.disabled=true);
  $('editor-root').setAttribute('aria-busy','true');
  // Disable controls without resetting pending input values.
  for (const id of ['save', 'undo', 'redo', 'reopen', 'add-text', 'add-rectangle', 'add-ellipse', 'layer-back', 'layer-forward', 'remove-layer']) $(id).disabled = true;
  $('properties').disabled = true;
  $('project-list').disabled = true;
  $('add-language').disabled = true;
  $('create-form').querySelectorAll('input,textarea,select,button').forEach(x => x.disabled = true);
  $('layers').querySelectorAll('button').forEach(x => x.disabled = true);
  let failed = false;
  try { await task(); if(project?.dirty)await action('save'); await refreshProjects(); notice(message); }
  catch (error) { failed = true; notice(error.name === 'AbortError' ? 'Local service timed out. Your saved files were not automatically replaced.' : error.message, true); }
  finally {
    render(failed); await updatePreview(); busy = false; render(true); $('editor-root').setAttribute('aria-busy','false');
    if(focusAfter){const target=[...$('layers').querySelectorAll('button')].find(b=>b.dataset.layerId===focusAfter);target?.focus({preventScroll:true});focusAfter=null;}
    else {const target=$(focusedId);if(target && !target.disabled)target.focus({preventScroll:true});else if(focusedId==='apply-text')$('layer-text').focus({preventScroll:true});}
  }
}

function commit(kind, extras, message) {
  return run(async () => {
    await flushText(); await action(kind, extras);
    if (kind.startsWith('add_')) selected = project.elements[project.elements.length - 1].id;
  }, message);
}

$('create-form').addEventListener('submit', event => {
  event.preventDefault();
  if(bindingDirty){notice('Save or discard unsubmitted context fields before creating another project.',true);return;}
  const body = {name: $('project-name').value, text: $('initial-text').value, language: $('initial-language').value};
  run(async () => { await flushText(); const extra=createContext();project = (await request(extra?'/api/workflow/create':'/api/projects',extra?{...body,...extra}:body)).project; selected = project.elements[0].id; $('create-form').closest('details').open=false; }, 'Project created. Save it locally when ready.').then(()=>{if(project)createdCallback();});
});
$('project-list').addEventListener('change', () => {
  const id = $('project-list').value;
  if (!id) return;
  if(bindingDirty){$('project-list').value=project?.project_id||'';notice('Save or discard unsubmitted context fields before opening another project.',true);return;}
  run(async () => { await flushText(); project = (await request('/api/project/' + encodeURIComponent(id))).project; selected = project.elements[0]?.id; }, 'Project opened.');
});
$('save').addEventListener('click', () => run(async () => { await flushText(); await action('save'); await refreshNavigation(); }, 'Saved locally.'));
async function reopenSaved(){project=(await request('/api/reopen',{project_id:project.project_id,expected_revision:project.revision})).project;}
$('reopen').addEventListener('click',()=>{
  if(project?.dirty || pendingText())showWorkflow('reopen');
  else run(reopenSaved,'Saved version reopened.');
});
for(const kind of ['undo','redo'])$(kind).addEventListener('click',()=>{
  if(pendingText())showWorkflow(kind);
  else run(()=>action(kind),kind==='undo'?'Last committed edit undone.':'Edit redone.');
});
$('remove-layer').addEventListener('click',()=>showWorkflow('remove'));
$('add-language').addEventListener('change', () => render(true));
$('add-text').addEventListener('click', () => commit('add_text', {language: $('add-language').value}, 'Independent text layer added.'));
$('add-rectangle').addEventListener('click', () => commit('add_shape', {shape: 'rectangle'}, 'Rectangle added.'));
$('add-ellipse').addEventListener('click', () => commit('add_shape', {shape: 'ellipse'}, 'Ellipse added.'));
$('apply-text').addEventListener('click', () => run(flushText, 'Text updated exactly as entered.'));
$('layer-text').addEventListener('input', () => {
  $('apply-text').disabled = busy || exporting || Boolean(composingField) || !pendingText();
  $('save-state').textContent = project?.dirty || pendingText() ? 'Unsaved changes' : 'Saved locally';
  updateTextStatus(); exportButtons();
  $('undo').disabled=busy || exporting || Boolean(composingField) || !project || (!project.can_undo && !pendingText());
});
$('apply-position').addEventListener('click', () => commit('move', {element_id: selected, x: Number($('position-x').value), y: Number($('position-y').value)}, 'Position updated.'));
$('apply-font').addEventListener('click', () => commit('font_size', {element_id: selected, font_size: Number($('font-size').value)}, 'Font size updated.'));
$('apply-color').addEventListener('click', () => commit('color', {element_id: selected, color: $('layer-color').value}, 'Fill color updated.'));

async function refreshAnalysis() {
  try {
    const session = await request('/api/session'); csrf = session.csrf;
    const analysis = session.analysis;
    const status = analysis.session_status;
    $('session-status').textContent = status ? `${Object.keys(status.recovery).length ? 'Recovery required for '+Object.keys(status.recovery).length+' project(s); originals preserved.' : 'Visual session ready.'} ${status.exports.sets} retained export sets. ${status.exports.blocked ? 'Export storage requires review; exports blocked.' : ''} Recovery storage ${(status.recovery_bytes/1048576).toFixed(2)} / 128 MiB. Physical power-loss durability unverified.` : 'Session status unavailable.';
    $('analysis-state').textContent = `OFF · ${analysis.state}`;
    $('analysis-message').textContent = analysis.state === 'FAULTED' ? 'The independent agent has faulted. Manual editing is still available.' : analysis.state === 'INCOMPATIBLE' ? 'The analysis service is incompatible or unavailable. Manual editing is still available.' : 'Media processing is disabled on this installation.';
    $('analysis-error').textContent = analysis.error;
  } catch (_) {
    $('analysis-state').textContent = 'OFF · UNAVAILABLE';
    $('analysis-message').textContent = 'Availability could not be refreshed. No analysis was started.';
  }
  render(true);
}
$('refresh-analysis').addEventListener('click', refreshAnalysis);
window.addEventListener('beforeunload', event => { if (project?.dirty || pendingText() || projects.some(p => p.dirty)) { event.preventDefault(); event.returnValue = ''; } });
document.addEventListener('keydown',event=>{
  if(!$('brands-screen').hidden)return;
  if($('workflow-dialog').open||event.target.closest?.('#brands-screen'))return;
  const editable=event.target.matches?.('input,textarea,select,[contenteditable="true"]');
  const command=shortcut(event,composingField,editable);
  if(!command)return;
  if(command==='apply-text' && event.target.id!=='layer-text')return;
  event.preventDefault();const target=$(command);if(target && !target.disabled)target.click();
});
(async () => {
  render(); await refreshAnalysis();
  try { await refreshProjects(); } catch (_) { notice('The local project service is unavailable.', true); }
  render();
  await initializeFonts(); await updatePreview(); await refreshNavigation();
})();

async function initializeFonts() {
  try {
    const info = await request('/api/fonts');
    if (!info.fonts) throw Error(info.error || 'Pinned fonts unavailable.');
    faces = info.fonts; await loadFonts(faces); fontReady = true;
    const proof = await qualifyEmbedded(faces); pngQualified = proof.ok;
    $('font-status').textContent = proof.ok ? 'Pinned Inter Bold + Noto Sans Telugu Black loaded. Embedded-font raster probes passed; PNG enabled conditionally.' : 'PNG disabled: '+proof.reason;
  } catch(e) { $('font-status').textContent = 'Exports unavailable: '+e.message; }
}
function exportButtons() {
  $('export-svg').disabled = exporting || busy || Boolean(composingField) || pendingText() || !sceneReady;
  $('export-png').disabled = exporting || busy || Boolean(composingField) || pendingText() || !sceneReady || !pngQualified;
}
async function updatePreview() {
  if(project && sceneReady && currentScene?.project_id===project.project_id && currentScene?.revision===project.revision && !$('poster-preview').hidden){updateSelection();exportButtons();return;}
  sceneReady = false; exportButtons();
  if (!project || !fontReady) return;
  const identity=project.project_id, revision=project.revision, sequence=++previewSequence;
  try {
    const scene = await request('/api/scene',{project_id:identity,expected_revision:revision});
    const qa = await inspectScene(scene);
    if(sequence!==previewSequence || project?.project_id!==identity || project?.revision!==revision)return;
    if (previewURL) URL.revokeObjectURL(previewURL);
    previewURL = URL.createObjectURL(new Blob([scene.svg],{type:'image/svg+xml'}));
    $('poster-preview').src = previewURL; $('poster-preview').hidden = false;
    currentScene = scene; updateSelection();
    if (qa.overflow.length) throw Error('Overflow or line overlap: '+qa.overflow.join(', ')+'. Reduce text size, use explicit newlines or reposition. Export refused.');
    sceneReady = true; $('render-status').textContent = 'Preview current · Revision '+scene.revision+' · SVG '+scene.svg_sha256.slice(0,12);
    $('render-status').classList.remove('error');
  } catch(e) {
    if(sequence!==previewSequence || project?.project_id!==identity || project?.revision!==revision)return;
    $('render-status').textContent = e.message; $('render-status').classList.add('error');
    if (!currentScene || currentScene.project_id !== project.project_id || currentScene.revision !== project.revision) $('poster-preview').hidden = true;
  }
  exportButtons(); updateSelection();
}
function b64(bytes) {let s='';for(let i=0;i<bytes.length;i+=16384)s+=String.fromCharCode(...bytes.subarray(i,i+16384));return btoa(s);}
async function exportDraft(withPng) {
  if (exporting || busy || gestureActive || composingField || $('workflow-dialog').open) return;
  const exportFocus=withPng?'export-png':'export-svg';
  exporting = true; render(true); exportButtons();
  try {
    await flushText(); await updatePreview();
    if (!sceneReady || (withPng && !pngQualified)) throw Error('Export qualification incomplete.');
    const start = await request('/api/export/begin',{project_id:project.project_id,expected_revision:project.revision});
    const scene = start.scene;
    const qa = await inspectScene(scene); let encoded = null;
    qa.parity = false; qa.embedded_fonts = pngQualified;
    if (withPng) {
      const rendered = await raster(scene.svg);
      qa.parity = await comparePng(rendered.canvas, rendered.blob);
      if (!qa.parity) {pngQualified=false;throw Error('PNG disabled: decoded RGBA parity failed.');}
      if (rendered.blob.size > 8*1024*1024) throw Error('PNG exceeds 8 MiB.');
      encoded = b64(new Uint8Array(await rendered.blob.arrayBuffer()));
    }
    const saved = await request('/api/export/finish',{token:start.token,revision:scene.revision,png:encoded,qa});
    if (saved.manifest.svg_sha256 !== scene.svg_sha256) throw Error('Saved SVG identity mismatch.');
    await refreshNavigation(); $('export-list').value=saved.directory.split('/').pop(); showReceipt();
    $('export-status').textContent = 'Draft saved: '+saved.directory+' · SVG '+saved.manifest.svg_sha256+(saved.manifest.png_sha256?' · PNG '+saved.manifest.png_sha256:'');
  } catch(e) {
    if (withPng && /canvas|taint|decode|font|parity|SecurityError/i.test(e.message)) pngQualified = false;
    $('export-status').textContent = 'Export refused: '+e.message;
    try {await request('/api/export/cancel',{});} catch(_) {}
  } finally {exporting=false;render(true);exportButtons();if(!$(exportFocus).disabled)$(exportFocus).focus({preventScroll:true});}
}
$('export-svg').addEventListener('click',()=>exportDraft(false));
$('export-png').addEventListener('click',()=>exportDraft(true));


let pendingReorder = null;
async function commitReorder(delta,acknowledged) {
  await run(async()=>{
    await flushText();
    const ids=project.elements.filter(e=>e.view_id===project.view.id).map(e=>e.id), index=ids.indexOf(selected), target=index+delta;
    if(index<0 || target<0 || target>=ids.length)throw Error('Layer cannot move further.');
    [ids[index],ids[target]]=[ids[target],ids[index]];
    await action('reorder',{view_id:project.view.id,ordered_element_ids:ids,acknowledge_upgrade:acknowledged});
  },'Layer paint order changed in one reversible transaction.');
}
function reorderLayer(delta) {
  if (!project || selectedIds.size>1 || busy || exporting || gestureActive || composingField || $('workflow-dialog').open) return;
  if (project.history_version < 2) {
    pendingReorder={projectId:project.project_id,revision:project.revision,selected,delta};
    $('upgrade-ack').checked=false;$('confirm-reorder').disabled=true;$('upgrade-panel').hidden=false;
    $('upgrade-ack').focus();return;
  }
  commitReorder(delta,false);
}
$('upgrade-ack').addEventListener('change',()=>{$('confirm-reorder').disabled=!$('upgrade-ack').checked;});
$('cancel-reorder').addEventListener('click',()=>{pendingReorder=null;$('upgrade-panel').hidden=true;});
$('confirm-reorder').addEventListener('click',()=>{
  const pending=pendingReorder;
  if(!pending || !$('upgrade-ack').checked)return;
  pendingReorder=null;$('upgrade-panel').hidden=true;
  if(!project || project.project_id!==pending.projectId || project.revision!==pending.revision || selected!==pending.selected){notice('Project changed; request reorder again.',true);return;}
  commitReorder(pending.delta,true);
});
$('layer-back').addEventListener('click',()=>reorderLayer(-1));
$('layer-forward').addEventListener('click',()=>reorderLayer(1));

function updateTextStatus(){
  const area=$('layer-text'), stats=textStats(area.value), pending=pendingText();
  $('text-status').textContent=`${stats.codePoints} Unicode code points · ${stats.lines} / 64 lines${pending?' · Unapplied text; preview shows last applied revision.':''}`;
  $('composition-status').textContent=composingField?'Composing text — actions paused; your text and caret remain under keyboard control.':'Telugu / English input ready. Ctrl/Cmd+Enter applies text.';
  if(project && pending)$('save-state').textContent='Unapplied text';
}
for(const id of ['layer-text','initial-text','create-purpose','create-topic','create-audience','create-instructions','binding-purpose','binding-topic','binding-audience','binding-instructions']){
  $(id).addEventListener('compositionstart',()=>{
    if(!composingField)compositionDisabled=[...document.querySelectorAll('button')].map(b=>[b,b.disabled]);
    composingField=id;if(id.startsWith('binding-'))bindingDirty=true;
    document.querySelectorAll('button').forEach(button=>{if(button.id!=='refresh-analysis')button.disabled=true;});
    $('project-list').disabled=true;$('initial-language').disabled=true;$('add-language').disabled=true;
    updateTextStatus();exportButtons();
  });
  $(id).addEventListener('compositionend',()=>{if(composingField!==id)return;composingField=null;for(const [b,disabled] of compositionDisabled)b.disabled=disabled;compositionDisabled=[];render(true);updateTextStatus();});
}
$('layers').addEventListener('keydown',event=>{
  if(event.altKey || event.ctrlKey || event.metaKey || compositionActive(event,composingField) || busy || exporting || !['ArrowDown','ArrowUp','Home','End'].includes(event.key))return;
  const buttons=[...$('layers').querySelectorAll('button')],index=buttons.indexOf(event.target);
  if(index<0)return;event.preventDefault();const target=buttons[nextLayerIndex(index,event.key,buttons.length)];if(target)selectLayer(target.dataset.layerId,event.shiftKey);
});
$('preview-zoom').addEventListener('change',()=>{$('poster-checker').style.width=zoomWidth($('preview-zoom').value);});
if(location.hash==='#editing-checks')import('/editing_browser.mjs');

let workflow=null;
function showWorkflow(kind){
  if(!project || busy || exporting || composingField || $('workflow-dialog').open)return;
  for(const id of ['workflow-keep','workflow-discard','workflow-cancel'])$(id).disabled=false;
  workflow={kind,projectId:project.project_id,revision:project.revision,selected,focus:document.activeElement?.id};
  $('workflow-title').textContent=kind==='remove'?'Remove selected layer?':kind==='reopen'?'Reopen saved project?':'Unapplied text edits';
  $('workflow-description').textContent=kind==='remove'?'This removes the layer from the working project. Undo restores its identity and contents. Saved files remain unchanged until Save.':kind==='reopen'?'Choose whether to save current work first or discard it and reopen the last saved version. Cancel keeps all edits.':'Choose how to handle unapplied text before changing history. Cancel keeps your text and caret.';
  $('workflow-keep').hidden=kind==='remove' || kind==='redo';
  $('workflow-keep').textContent=kind==='reopen'?'Save and reopen':'Apply text, then undo';
  $('workflow-discard').textContent=kind==='remove'?'Remove layer':kind==='reopen'?'Discard and reopen':'Discard text and '+kind;
  $('workflow-dialog').showModal();$('workflow-cancel').focus();
}
function cancelWorkflow(){const focus=workflow?.focus;workflow=null;$('workflow-dialog').close();if(focus && !$(focus)?.disabled)$(focus)?.focus();}
$('workflow-cancel').addEventListener('click',cancelWorkflow);
$('workflow-dialog').addEventListener('cancel',event=>{event.preventDefault();cancelWorkflow();});
async function finishWorkflow(keep){
  const pending=workflow;
  if(!dialogStillCurrent(pending,project,selected)){cancelWorkflow();notice('Project changed. Request this action again.',true);return;}
  workflow=null;$('workflow-dialog').close();
  await run(async()=>{
    if(pending.kind==='remove'){
      await flushText();await action('remove',{element_id:pending.selected});selected=project.elements[0]?.id||null;
    }else if(pending.kind==='reopen'){
      if(keep){await flushText();await action('save');}await reopenSaved();
    }else{
      if(keep)await flushText();await action(pending.kind);
    }
  },pending.kind==='remove'?'Layer removed. Undo restores it.':pending.kind==='reopen'?'Saved version reopened.':'History updated.');
}
$('workflow-keep').addEventListener('click',()=>finishWorkflow(true));
$('workflow-discard').addEventListener('click',()=>finishWorkflow(false));
document.addEventListener('keydown',event=>{
  if(!$('brands-screen').hidden)return;
  if(event.defaultPrevented || $('workflow-dialog').open || busy || exporting || gestureActive || !project || !element())return;
  const delta=nudge(event,composingField,event.target.matches?.('input,textarea,select,[contenteditable="true"]'));
  if(!delta)return;event.preventDefault();if(selectedIds.size>1){requestGeometry(translate(targetsFor(project.elements,[...selectedIds]),delta.x,delta.y));return;}commit('move',{element_id:selected,x:element().x+delta.x,y:element().y+delta.y},'Layer nudged.');
});

function selectLayer(identity,toggle=false){
  if(!project || !project.elements.some(e=>e.id===identity) || composingField || busy || exporting || gestureActive || $('workflow-dialog').open)return;
  focusAfter=identity;return run(async()=>{await flushText();selectedIds=new Set(toggle?toggleSelection([...selectedIds],identity):[identity]);selected=selectedIds.has(identity)?identity:[...selectedIds].at(-1);focusAfter=selected;},'Layer selection updated.');
}
function placeBox(target,box){
  target.hidden=!box;
  if(box)for(const [key,value] of Object.entries(box))target.style[key]=value+'%';
}
function updateSelection(){
  const matching=project && currentScene?.project_id===project.project_id && currentScene?.revision===project.revision && !$('poster-preview').hidden;
  placeBox($('selection-outline'),matching?clippedBox(selectionBounds(project.elements,[...selectedIds]),project.view):null);
  if(typeof resizeHandles!=='undefined')for(const b of resizeHandles){const e=element();b.hidden=!matching||selectedIds.size!==1||busy||exporting;b.disabled=busy||exporting;if(!b.hidden){b.style.left=100*(e.x+(b.dataset.resize.includes('e')?e.width:0))/project.view.width+'%';b.style.top=100*(e.y+(b.dataset.resize.includes('s')?e.height:0))/project.view.height+'%';}}
  for(const id of ['geometry-size','geometry-move'])$(id).disabled=busy||exporting||gestureActive||!project||(id==='geometry-size'&&selectedIds.size!==1);
  if(element()&&!gestureActive){$('geometry-width').value=element().width;$('geometry-height').value=element().height;}
  const margin=Number($('layout-margin').value);
  const valid=matching && $('show-guides').checked && Number.isInteger(margin) && margin>=0 && 2*margin<Math.min(project.view.width,project.view.height);
  placeBox($('margin-guide'),valid?{left:100*margin/1080,top:100*margin/1350,width:100*(1080-2*margin)/1080,height:100*(1350-2*margin)/1350}:null);
}
$('poster-preview').addEventListener('click',event=>{
  if(dragController?.consumeClick())return;
  if(!project || currentScene?.project_id!==project.project_id || currentScene?.revision!==project.revision)return;
  const point=sourcePoint(event.clientX,event.clientY,$('poster-preview').getBoundingClientRect(),project.view);
  const identity=nextHit(hitLayers(project.elements,point),selected,event.altKey);
  if(identity)selectLayer(identity,event.shiftKey || event.ctrlKey || event.metaKey);else notice('No layer at this point. Choose covered layers from the Layers list.');
});
document.querySelectorAll('[data-align]').forEach(button=>button.addEventListener('click',()=>{
  if(!element() || gestureActive || composingField || busy || exporting)return;
  try{if(selectedIds.size>1){const targets=project.elements.filter(e=>selectedIds.has(e.id)).map(e=>({...targetsFor([e],[e.id])[0],...alignPosition(e,project.view,button.dataset.align,Number($('layout-margin').value))}));requestGeometry(targets);return;}const position=alignPosition(element(),project.view,button.dataset.align,Number($('layout-margin').value));if(position.x===element().x&&position.y===element().y){notice('Layer is already aligned.');return;}commit('move',{element_id:selected,...position},'Layer aligned.');}
  catch(e){notice(e.message,true);}
}));
$('layout-margin').addEventListener('input',updateSelection);$('show-guides').addEventListener('change',updateSelection);
function showReceipt(){
  const item=navigationData?.exports.find(e=>e.id===$('export-list').value);
  $('export-receipt').textContent=item?`DRAFT · ${item.state} · Revision ${item.revision ?? 'unknown'}\n${item.directory}\nSVG: ${item.svg_sha256 ?? 'not available'}\nPNG: ${item.png_sha256 ?? 'not included'}`:'Choose a retained export. Files stay in this session folder.';
}
async function refreshNavigation(){
  try{
    const previous=$('export-list').value;navigationData=await request('/api/navigation');
    $('session-root').value=navigationData.runtime_root;
    $('resume-command').value='cd '+shellQuote('/Users/Nadish/projects/AI Video Editor./Codex/AI Studio')+'\npython3 -B -m visual_poster_studio --resume --root '+shellQuote(navigationData.runtime_root)+' --port 0';
    $('navigation-summary').textContent=`${navigationData.projects.length} projects · ${navigationData.exports.length} retained exports · Analysis OFF`;
    $('session-status').textContent=`Visual session · ${navigationData.exports.length} retained export sets · Recovery storage ${(navigationData.recovery_bytes/1048576).toFixed(2)} / 128 MiB. ${Object.keys(navigationData.recovery).length?'Some projects require explicit recovery. ':''}${navigationData.export_status.blocked?'Export storage requires review. ':''}Physical power-loss durability unverified.`;
    const list=$('export-list');list.replaceChildren();const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='Choose a retained draft';list.append(placeholder);
    for(const item of navigationData.exports){const option=document.createElement('option');option.value=item.id;option.textContent=`${item.id.slice(-8)} · ${item.state} · revision ${item.revision ?? '?'}`;list.append(option);}
    list.value=previous;showReceipt();
  }catch(e){$('navigation-summary').textContent='Workspace navigation unavailable: '+e.message;}
}
$('refresh-navigation').addEventListener('click',async()=>{await refreshProjects();await refreshNavigation();});
$('export-list').addEventListener('change',showReceipt);
if(location.hash==='#layout-checks')import('/layout_browser.mjs');

$('select-all-layers').addEventListener('click',()=>run(async()=>{await flushText();selectedIds=new Set(project.elements.map(e=>e.id));selected=project.elements[0]?.id;},'Layers selected.'));
$('select-primary').addEventListener('click',()=>{if(busy||exporting||composingField)return;selectedIds=new Set(selected?[selected]:[]);render(true);});
dragController=installDrag($('poster-preview'),{
 snapshot:()=>project?{projectId:project.project_id,revision:project.revision,view:project.view,elements:project.elements,selection:[...selectedIds],pendingText:pendingText()}:null,
 ready:()=>!busy&&!exporting&&!composingField&&!$('workflow-dialog').open&&currentScene?.project_id===project?.project_id&&currentScene?.revision===project?.revision&&!$('poster-preview').hidden,
 lock:active=>{gestureActive=active;render(true);},
 options:()=>({snap:$('snap-enabled').checked,grid:$('grid-enabled').checked?Number($('grid-size').value):0,margin:Number($('layout-margin').value)}),
 preview:value=>{placeBox($('drag-preview'),value&&project?clippedBox(value,project.view):null);$('drag-status').textContent=value?`Preview move: X ${value.x}, Y ${value.y}${value.guides.length?' · snapped '+value.guides.join('/') : ''} · Release to apply; Escape cancels.`:'Drag selected layers to move. Shift constrains axis; Alt bypasses snapping.';},
 message:notice,
 commit:(snapshot,position,targets)=>{
  if(project?.project_id!==snapshot.projectId||project?.revision!==snapshot.revision){notice('Stale drag cancelled.',true);return;}
  if(targets){requestGeometry(targets);return;}
  focusAfter=snapshot.id;run(async()=>{selected=snapshot.id;selectedIds=new Set([selected]);await action('move',{element_id:selected,x:position.x,y:position.y});},'Layer moved in one undoable transaction.');
 }
});
if(location.hash==='#canvas-checks')import('/canvas_browser.mjs');

let pendingGeometry=null;
function requestGeometry(targets,ack=false){
 if(!project||busy||exporting||gestureActive||composingField)return;
 if(pendingText()){notice('Apply text before changing geometry.',true);return;}
 if(project.history_version<3&&!ack){pendingGeometry={projectId:project.project_id,revision:project.revision,targets};$('geometry-upgrade').hidden=false;$('geometry-ack').checked=false;$('geometry-confirm').disabled=true;$('geometry-ack').focus();return;}
 run(async()=>{await action('geometry',{view_id:project.view.id,targets,acknowledge_upgrade:ack});},'Geometry committed in one undoable transaction.');
}
$('geometry-ack').addEventListener('change',()=>{$('geometry-confirm').disabled=!$('geometry-ack').checked;});
$('geometry-cancel').addEventListener('click',()=>{pendingGeometry=null;$('geometry-upgrade').hidden=true;});
$('geometry-confirm').addEventListener('click',()=>{const p=pendingGeometry;if(!p||!$('geometry-ack').checked)return;pendingGeometry=null;$('geometry-upgrade').hidden=true;if(p.projectId!==project?.project_id||p.revision!==project?.revision){notice('Project changed; request geometry again.',true);return;}requestGeometry(p.targets,true);});
$('geometry-move').addEventListener('click',()=>{try{requestGeometry(translate(targetsFor(project.elements,[...selectedIds]),Number($('geometry-dx').value),Number($('geometry-dy').value)));}catch(e){notice(e.message,true);}});
$('geometry-size').addEventListener('click',()=>{try{if(selectedIds.size!==1)throw Error('Select one layer to resize.');const e=element(),width=Number($('geometry-width').value);let height=Number($('geometry-height').value);if($('aspect-lock').checked)height=Math.max(1,Math.round(width*e.height/e.width));requestGeometry([{element_id:e.id,x:e.x,y:e.y,width,height}]);}catch(e){notice(e.message,true);}});
resizeHandles=['nw','ne','sw','se'].map(corner=>{const b=document.createElement('button');b.className='resize-handle';b.dataset.resize=corner;b.setAttribute('aria-label','Resize '+corner+' corner; use Width and Height for keyboard resizing');b.hidden=true;$('poster-checker').append(b);return b;});
// Alignment is outside the single-element property fieldset so group actions stay available.
$('geometry-panel').prepend(document.querySelector('.alignment-controls'));
installResize($('poster-preview'),resizeHandles,{
 snapshot:()=>project?{projectId:project.project_id,revision:project.revision,view:project.view,elements:project.elements,selection:[...selectedIds],pendingText:pendingText()}:null,
 ready:()=>!busy&&!exporting&&!gestureActive&&!composingField&&currentScene?.revision===project?.revision,
 lock:v=>{gestureActive=v;render(true);},options:()=>({aspect:$('aspect-lock').checked,grid:$('grid-enabled').checked?Number($('grid-size').value):0}),
 preview:v=>placeBox($('drag-preview'),v?clippedBox(v,project.view):null),message:notice,commit:(_,targets)=>requestGeometry(targets)
});

if(location.hash==='#geometry-checks')import('/geometry_browser.mjs');

function textMeasure(){
 if(!fontReady||!faces)throw Error('Pinned fonts must be loaded before layout.');
 const e=element(),ctx=document.createElement('canvas').getContext('2d');if(!e||e.type!=='text'||!ctx)throw Error('Select one text layer.');
 const measure=text=>fontRuns(text).reduce((sum,run)=>{const f=faces[run.lang];ctx.font=`${f.weight} ${e.style.font_size}px "${f.family}"`;return sum+ctx.measureText(run.text).width;},0);
 const descent=Math.max(...Object.values(faces).map(f=>{ctx.font=`${f.weight} ${e.style.font_size}px "${f.family}"`;return ctx.measureText(f===faces.te?'తెలుగు':'gj').actualBoundingBoxDescent||0;}));
 return {measure,descent};
}
$('wrap-text').addEventListener('click',()=>{
 if(composingField||busy||exporting||gestureActive||selectedIds.size!==1)return;
 try{const {measure}=textMeasure(),area=$('layer-text'),before=area.value,next=wrapText(before,element().width,measure);area.value=next;area.dispatchEvent(new Event('input',{bubbles:true}));area.focus();area.setSelectionRange(0,0);updateTextStatus();exportButtons();$('text-layout-status').textContent=next===before?'Text already fits the measured width.':'Newlines inserted in draft only. Review and Apply text; Cancel draft restores applied text.';}
 catch(e){$('text-layout-status').textContent=e.message;}
});
$('fit-text').addEventListener('click',()=>{
 if(composingField||busy||exporting||gestureActive||selectedIds.size!==1)return;
 try{if(pendingText())throw Error('Apply text before fitting its box.');const e=element(),{measure,descent}=textMeasure(),size=fitTextBox(content(e).text,e.style.font_size,measure,descent);if(size.width>4096||size.height>4096||e.x<0||e.y<0||e.x+size.width>project.view.width||e.y+size.height>project.view.height)throw Error('Fitted box exceeds canvas. Reposition or reduce text size.');requestGeometry([{element_id:e.id,x:e.x,y:e.y,...size}]);}
 catch(e){$('text-layout-status').textContent=e.message;}
});
document.addEventListener('keydown',event=>{
  if(!$('brands-screen').hidden)return;
 if(event.defaultPrevented||compositionActive(event,composingField)||busy||exporting||gestureActive||$('workflow-dialog').open||!project)return;
 const editable=event.target.matches?.('input,textarea,select,[contenteditable="true"]');
 if(event.key==='F2'&&!editable&&selectedIds.size===1&&element()?.type==='text'){event.preventDefault();$('layer-text').focus();return;}
 if(event.key==='Escape'&&event.target.id==='layer-text'){event.preventDefault();$('layers').querySelector('[data-layer-id="'+selected+'"]')?.focus();return;}
 const delta=keyboardGeometry(event,composingField,editable);if(!delta||selectedIds.size!==1)return;event.preventDefault();const e=element();let width=e.width+delta.dw,height=e.height+delta.dh;
 if($('aspect-lock').checked){if(delta.dw)height=Math.round(width*e.height/e.width);else width=Math.round(height*e.width/e.height);}
 if(width<1||height<1||width>4096||height>4096){notice('Resize exceeds supported dimensions.',true);return;}
 requestGeometry([{element_id:e.id,x:e.x,y:e.y,width,height}]);
});
// Focus persists in the text field during composition; the OS owns all candidate input.
$('layer-text').addEventListener('keydown',event=>{if(compositionActive(event,composingField))event.stopPropagation();});
for(const b of resizeHandles)b.tabIndex=-1; // Equivalent numeric controls are the keyboard path.
if(location.hash==='#text-completion-checks')import('/text_completion_browser.mjs');

$('cancel-text-draft').addEventListener('click',()=>{if(composingField||busy||exporting||gestureActive||element()?.type!=='text')return;$('layer-text').value=content(element()).text;$('layer-text').dispatchEvent(new Event('input',{bubbles:true}));$('layer-text').focus();updateTextStatus();exportButtons();$('text-layout-status').textContent='Draft cancelled; applied text and history unchanged.';});

productUI=installProduct({request,run,current:()=>project,pending:()=>pendingText()||brandDirty||bindingDirty||Boolean(project?.dirty),route:name=>homeNavigation?.route(name),opened:value=>{project=value;selected=project.elements[0]?.id;selectedIds=new Set(selected?[selected]:[]);sceneReady=false;currentScene=null;}});

homeNavigation=installHome({request,ready:()=>!brandWorking&&!busy&&!exporting&&!gestureActive&&!composingField&&!$('workflow-dialog').open,pending:()=>pendingText()||brandDirty||bindingDirty,
 open:async identity=>{if(bindingDirty){notice('Save or discard unsubmitted context fields first.',true);return false;}if(busy||exporting||gestureActive||composingField)return false;let opened=false;await run(async()=>{await flushText();project=(await request('/api/project/'+encodeURIComponent(identity))).project;selected=project.elements[0]?.id;opened=true;},'Project opened.');return opened;},
 onCreated:fn=>{createdCallback=fn;}
});

mediaBridge=installMedia({request,run,current:()=>project,flush:flushText,pendingContext:()=>bindingDirty||brandDirty||pendingText()||Boolean(composingField),gesture:value=>{gestureActive=value;render(true);},invalidate:()=>{sceneReady=false;currentScene=null;previewSequence++;},opened:value=>{project=value;selected=project.elements[0]?.id;selectedIds=new Set(selected?[selected]:[]);},show:()=>document.querySelector('[data-page=editor]').click()});

director=installDirector({request,run,current:()=>project,selected:()=>selectedIds.size===1?selected:null,updated:value=>{project=value;},pending:()=>pendingText()||bindingDirty||brandDirty,opened:value=>{project=value;selected=project.elements.find(e=>e.type==='text')?.id||project.elements[0]?.id;selectedIds=new Set(selected?[selected]:[]);}});

installBrands({request,setDirty:v=>{brandDirty=v;},setWorking:v=>{brandWorking=v;},ready:()=>!busy&&!exporting&&!gestureActive&&!composingField&&!$('workflow-dialog').open});

function briefFields(prefix){return {purpose:$(prefix+'purpose').value,topic:$(prefix+'topic').value,audience:$(prefix+'audience').value,format:$(prefix+'format').value,instructions:$(prefix+'instructions').value};}
function createContext(){
 const fields=briefFields('create-'),brand=$('create-brand').value;
 if(!brand&&!Object.entries(fields).some(([k,v])=>k!=='format'&&v)&&!$('create-binding-ack').checked)return null;
 return {brief:fields,brand_hash:brand||null,acknowledge:$('create-binding-ack').checked};
}
async function refreshWorkflowVersions(){
 try{workflowVersions=(await request('/api/workflow/brands')).versions;for(const id of ['create-brand','binding-brand']){const select=$(id),prior=select.value;select.replaceChildren(new Option('No brand',''));for(const b of workflowVersions){const option=new Option(`${b.name} · r${b.revision}${b.eligible?'':' · blocked: '+b.reason}`,b.hash);option.disabled=!b.eligible;select.append(option);}select.value=prior;}showCreateBrand();}
 catch(e){$('create-brand-info').textContent='Brand selection unavailable: '+e.message;}
}
function showCreateBrand(){const b=workflowVersions.find(b=>b.hash===$('create-brand').value);$('create-brand-info').textContent=b?JSON.stringify({name:b.name,revision:b.revision,hash:b.hash,hard_rules:b.mandatory_rules,preferences:b.preferences,inspiration:b.inspiration,status:b.reason}):'No brand selected; no registered assets applied.';}
function renderBinding(locked){
 const state=project?.binding;$('binding-editor').hidden=!state;$('binding-status').textContent=state?`Binding r${state.record.revision} · ${state.eligible?'current metadata':'BLOCKED'} · ${state.status}`:project?'Legacy unbound project. No migration performed; create a new brief-bound project to use this workflow.':'Select a project.';
 $('binding-refresh').disabled=locked||!project;
 if(!state)return;
 if(!bindingDirty){const b=state.record;for(const [k,v] of Object.entries(b.brief))$('binding-'+k).value=v;
  const select=$('binding-brand'),h=b.brand?.hash||'';if(h&&![...select.options].some(o=>o.value===h))select.append(new Option(`${b.brand.record.payload.name} · pinned r${b.brand.revision}`,h));select.value=h;
 }
 $('binding-rules').textContent=JSON.stringify(state.record.brand?{identity:state.record.brand.hash,name:state.record.brand.record.payload.name,...state.record.brand.record.payload,status:state.status}: {brand:'None',status:state.status},null,2);
 for(const c of $('binding-editor').querySelectorAll('input,select,textarea,button'))c.disabled=locked;
 $('binding-confirm').disabled=locked||!workflowImpact||!$('binding-confirm-ack').checked;
 if(project?.media_context){for(const c of $('binding-editor').querySelectorAll('input,select,textarea,button'))c.disabled=true;$('binding-refresh').disabled=true;}
}
for(const id of ['binding-brand','binding-purpose','binding-topic','binding-audience','binding-format','binding-instructions'])$(id).addEventListener('input',()=>{bindingDirty=true;workflowImpact=null;workflowProposal=null;$('binding-confirm').disabled=true;});
$('create-brand-refresh').addEventListener('click',refreshWorkflowVersions);$('create-brand').addEventListener('change',showCreateBrand);
$('binding-refresh').addEventListener('click',()=>run(async()=>{if(bindingDirty)throw Error('Save or discard unsubmitted context fields before refreshing its head.');await refreshWorkflowVersions();project=(await request('/api/project/'+project.project_id)).project;},'Binding eligibility refreshed.'));
$('binding-discard').addEventListener('click',()=>{if(busy||exporting||composingField)return;bindingDirty=false;workflowImpact=null;workflowProposal=null;$('binding-impact').textContent='Unsubmitted context fields discarded.';render(true);});
$('binding-preview').addEventListener('click',()=>run(async()=>{
 await flushText();if(!project?.binding)throw Error('This is an unbound legacy project.');workflowProposal={project_id:project.project_id,expected_revision:project.revision,expected_binding:project.binding.hash,expected_head:project.binding.published_head,brand_hash:$('binding-brand').value||null,brief:briefFields('binding-')};
 const result=await request('/api/workflow/preview',workflowProposal);workflowImpact=result.impact_hash;$('binding-impact').textContent=JSON.stringify(result,null,2);$('binding-confirm-ack').checked=false;
},'Review the context-change impact before confirming.'));
$('binding-confirm-ack').addEventListener('change',()=>{$('binding-confirm').disabled=busy||exporting||!workflowImpact||!$('binding-confirm-ack').checked;});
$('binding-confirm').addEventListener('click',()=>run(async()=>{
 if(!workflowProposal||!workflowImpact||!$('binding-confirm-ack').checked)throw Error('Preview and confirm the impact first.');project=(await request('/api/workflow/change',{proposal:workflowProposal,impact_hash:workflowImpact,acknowledge:true})).project;bindingDirty=false;workflowProposal=null;workflowImpact=null;$('binding-impact').textContent='Document and binding committed together. Historical records preserved.';
},'Context revision saved atomically.'));
refreshWorkflowVersions();

$('bound-recovery-list').addEventListener('click',async()=>{try{const value=await request('/api/workflow/recovery',{project_id:$('bound-recovery-id').value});$('bound-recovery-results').textContent=JSON.stringify(value,null,2);}catch(e){$('bound-recovery-results').textContent=e.message;}});
window.addEventListener('beforeunload',event=>{if(bindingDirty){event.preventDefault();event.returnValue='';}});
