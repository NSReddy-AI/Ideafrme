'use strict';
// Local DOM/form UI only. No renderer, media inputs, external assets or agent launches.
const $ = id => document.getElementById(id);
let csrf = null, project = null, selected = null, projects = [], busy = false;

function notice(message, error = false) {
  $('notice').textContent = message;
  $('notice').classList.toggle('error', error);
}

async function request(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
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
    return value;
  } finally { clearTimeout(timer); }
}

function element() { return project?.elements.find(e => e.id === selected); }
function content(e) { return project?.content.find(c => c.id === e?.content_id); }
function pendingText() {
  const e = element();
  return e?.type === 'text' && $('layer-text').value !== content(e)?.text;
}

function render(preserveText = false) {
  const current = project?.elements.find(e => e.id === selected);
  if (!current) selected = project?.elements[0]?.id || null;
  const e = element();
  $('project-title').textContent = project?.name || 'Your next idea starts here';
  $('project-meta').textContent = project ? `${project.view.width} × ${project.view.height} source · Revision ${project.revision}` : 'Create a project to begin manual editing.';
  $('save-state').textContent = project ? (project.dirty || pendingText() ? 'Unsaved changes' : 'Saved locally') : 'No project';
  $('save').disabled = busy || !project;
  $('undo').disabled = busy || !project?.can_undo;
  $('redo').disabled = busy || !project?.can_redo;
  $('reopen').disabled = busy || !project?.saved;
  $('properties').disabled = busy || !e;
  $('text-fields').hidden = !e || e.type !== 'text';
  $('font-field').hidden = !e || e.type !== 'text';
  $('create-form').querySelectorAll('input,textarea,select,button').forEach(x => x.disabled = busy || !csrf);
  $('project-list').disabled = busy || !csrf;
  const remaining = project?.remaining_text_slots || {en: 0, te: 0};
  $('add-language').disabled = busy || !project;
  $('add-text').disabled = busy || !project || !remaining[$('add-language').value] || project.elements.length >= project.element_limit;
  for (const id of ['add-rectangle', 'add-ellipse']) $(id).disabled = busy || !project || project.elements.length >= project.element_limit;
  $('capacity').textContent = project ? `${remaining.en} English and ${remaining.te} Telugu text slots free · ${project.elements.length} / ${project.element_limit} layers` : 'Up to 32 text layers and 64 layers total.';
  const list = $('layers'); list.replaceChildren();
  if (!project) {
    const li = document.createElement('li'); li.className = 'empty'; li.textContent = 'Your layers will appear here.'; list.append(li);
  }
  project?.elements.forEach((layer, index) => {
    const li = document.createElement('li'), button = document.createElement('button');
    button.type = 'button'; button.disabled = busy;
    button.classList.toggle('selected', layer.id === selected);
    button.setAttribute('aria-pressed', String(layer.id === selected));
    const label = document.createElement('span'); label.className = 'layer-label';
    label.textContent = `${index + 1} · ${layer.type === 'text' ? (content(layer)?.language === 'te' ? 'TELUGU TEXT' : 'ENGLISH TEXT') : 'GEOMETRY'}`;
    const excerpt = document.createElement('span'); excerpt.className = 'layer-text';
    excerpt.textContent = layer.type === 'text' ? content(layer)?.text : layer.style.shape;
    button.append(label, excerpt);
    button.addEventListener('click', () => {
      if (pendingText() && !window.confirm('Discard unapplied text edits before changing layers?')) return;
      selected = layer.id; render();
    });
    li.append(button); list.append(li);
  });
  if (e && !preserveText) {
    $('layer-text').value = e.type === 'text' ? content(e).text : '';
    $('position-x').value = String(e.x); $('position-y').value = String(e.y);
    $('font-size').value = e.style.font_size || 64;
    $('layer-color').value = e.style.fill;
  }
  $('apply-text').disabled = busy || !e || e.type !== 'text' || !pendingText();
  $('save-state').textContent = project ? (project.dirty || pendingText() ? 'Unsaved changes' : 'Saved locally') : 'No project';
}

async function refreshProjects() {
  projects = (await request('/api/projects')).projects;
  const list = $('project-list'); list.replaceChildren();
  const placeholder = document.createElement('option'); placeholder.value = ''; placeholder.textContent = 'Choose a project'; list.append(placeholder);
  for (const item of projects) {
    const option = document.createElement('option'); option.value = item.project_id;
    option.textContent = `${item.name}${item.dirty ? ' · unsaved' : ''}`; list.append(option);
  }
  list.value = project?.project_id || '';
}

async function action(kind, extras = {}) {
  if (!project) return;
  project = (await request('/api/action', {project_id: project.project_id, expected_revision: project.revision, action: kind, ...extras})).project;
}

async function flushText() {
  if (pendingText()) await action('edit_text', {element_id: selected, text: $('layer-text').value});
}

async function run(task, message) {
  if (busy) return;
  busy = true;
  // Disable controls without resetting pending input values.
  for (const id of ['save', 'undo', 'redo', 'reopen', 'add-text', 'add-rectangle', 'add-ellipse']) $(id).disabled = true;
  $('properties').disabled = true;
  $('project-list').disabled = true;
  $('add-language').disabled = true;
  $('create-form').querySelectorAll('input,textarea,select,button').forEach(x => x.disabled = true);
  $('layers').querySelectorAll('button').forEach(x => x.disabled = true);
  let failed = false;
  try { await task(); await refreshProjects(); notice(message); }
  catch (error) { failed = true; notice(error.name === 'AbortError' ? 'Local service timed out. Your saved files were not automatically replaced.' : error.message, true); }
  finally { busy = false; render(failed); }
}

function commit(kind, extras, message) {
  return run(async () => {
    await flushText(); await action(kind, extras);
    if (kind.startsWith('add_')) selected = project.elements[project.elements.length - 1].id;
  }, message);
}

$('create-form').addEventListener('submit', event => {
  event.preventDefault();
  const body = {name: $('project-name').value, text: $('initial-text').value, language: $('initial-language').value};
  run(async () => { await flushText(); project = (await request('/api/projects', body)).project; selected = project.elements[0].id; }, 'Project created. Save it locally when ready.');
});
$('project-list').addEventListener('change', () => {
  const id = $('project-list').value;
  if (!id) return;
  run(async () => { await flushText(); project = (await request('/api/project/' + encodeURIComponent(id))).project; selected = project.elements[0]?.id; }, 'Project opened.');
});
$('save').addEventListener('click', () => run(async () => { await flushText(); await action('save'); }, 'Saved locally.'));
$('reopen').addEventListener('click', () => {
  if ((project?.dirty || pendingText()) && !window.confirm('Discard unsaved changes and reopen the saved version?')) return;
  run(async () => { project = (await request('/api/reopen', {project_id: project.project_id, expected_revision: project.revision})).project; }, 'Saved version reopened.');
});
for (const kind of ['undo', 'redo']) $(kind).addEventListener('click', () => {
  if (pendingText() && !window.confirm('Discard unapplied text edits?')) return;
  run(() => action(kind), kind === 'undo' ? 'Last committed edit undone.' : 'Edit redone.');
});
$('add-language').addEventListener('change', () => render(true));
$('add-text').addEventListener('click', () => commit('add_text', {language: $('add-language').value}, 'Independent text layer added.'));
$('add-rectangle').addEventListener('click', () => commit('add_shape', {shape: 'rectangle'}, 'Rectangle added.'));
$('add-ellipse').addEventListener('click', () => commit('add_shape', {shape: 'ellipse'}, 'Ellipse added.'));
$('apply-text').addEventListener('click', () => run(flushText, 'Text updated exactly as entered.'));
$('layer-text').addEventListener('input', () => {
  $('apply-text').disabled = busy || !pendingText();
  $('save-state').textContent = project?.dirty || pendingText() ? 'Unsaved changes' : 'Saved locally';
});
$('apply-position').addEventListener('click', () => commit('move', {element_id: selected, x: Number($('position-x').value), y: Number($('position-y').value)}, 'Position updated.'));
$('apply-font').addEventListener('click', () => commit('font_size', {element_id: selected, font_size: Number($('font-size').value)}, 'Font size updated.'));
$('apply-color').addEventListener('click', () => commit('color', {element_id: selected, color: $('layer-color').value}, 'Fill color updated.'));

async function refreshAnalysis() {
  try {
    const session = await request('/api/session'); csrf = session.csrf;
    const analysis = session.analysis;
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
document.addEventListener('keydown', event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') { event.preventDefault(); if (project && !busy) $('save').click(); } });
(async () => {
  render(); await refreshAnalysis();
  try { await refreshProjects(); } catch (_) { notice('The local project service is unavailable.', true); }
  render();
})();
