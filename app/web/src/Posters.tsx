// M6 step 4: the M5 poster editor rebuilt in React on the M6 tokens.
// All document rules stay in M5 (server side, via /api/creative/*). The browser-side export rules are M5's own,
// imported unchanged: font loading, overflow check, rasterising and PNG parity (browser_acceptance.js), plus M5's
// alignment and resize helpers. Nothing here decides what a valid poster is; it only shows and asks.
import { useCallback, useEffect, useRef, useState } from 'react'
import { comparePng, inspectScene, loadFonts, qualifyEmbedded, raster } from '@m5/visual_poster_tests/browser_acceptance.js'
import { alignPosition, clippedBox } from '@m5/visual_poster_studio/layout.mjs'
import { resizeBox } from '@m5/visual_poster_studio/geometry.mjs'
import { nextLayerIndex, nudge, shortcut, zoomWidth } from '@m5/visual_poster_studio/editing.mjs'
import { creative, CreativeError, type ApprovedDoc, type Binding, type ContentLink, type ExportReceipt, type Face, type Layer, type PosterProject, type PosterQA, type PosterRow, type ReelRow, type Scene } from './creative'
import { Btn, Card, Err, Field, MOTION, Notice, PageHead, Pill, Select, Tabs, TextArea, cx, useConfirm } from './ui'
import { PHASES, readiness, savedFiles, type ItemState, type Phase } from './export-logic'
import { readLinks } from './project-links'
import { reelHref, reelStatusLabel } from './projects-logic'
import { report, type Task } from './tasks'
import { TaskStrip } from './TaskTracker'
import { useTask } from './use-task'
import { api, type Catalog } from './api'
import { measureText, measuredChecks, type MeasuredCheck } from './measure'

const SAFE_MARGIN = 64   // same proposed value as app/poster_qa.py
const msg = (e: unknown) => (e as Error).message

// ------------------------------------------------------------------ list + new poster
export function PostersPage({ onOpen }: { onOpen: (id: string) => void }) {
  const [rows, setRows] = useState<PosterRow[] | null>(null); const [err, setErr] = useState<string | null>(null)
  const [name, setName] = useState(''); const [text, setText] = useState(''); const [language, setLanguage] = useState<'en' | 'te'>('te')
  useEffect(() => { creative.list().then(setRows).catch(e => setErr(msg(e))) }, [])
  const make = async () => { setErr(null); try { onOpen((await creative.create({ name, text, language })).project_id) } catch (e) { setErr(msg(e)) } }
  return (
    <div className="space-y-6">
      <PageHead title="Posters" sub="Editable 1080 × 1350 posters in Telugu and English. Saved on this Mac." />
      <Card title="New poster">
        <div className="grid gap-3 sm:grid-cols-[1fr_2fr_auto]">
          <label className="text-sm">Name<Field value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Reading day" /></label>
          <label className="text-sm">First text<Field value={text} onChange={e => setText(e.target.value)} className={language === 'te' ? 'te' : undefined} placeholder="Headline" /></label>
          <label className="text-sm">Language<Select className="w-full" value={language} onChange={e => setLanguage(e.target.value as 'en' | 'te')}><option value="te">Telugu</option><option value="en">English</option></Select></label>
        </div>
        <Btn className="mt-4" disabled={!name.trim() || !text.trim()} onClick={make}>Create poster</Btn>
        <Err msg={err} />
      </Card>
      <section>
        <h2 className="mb-2 text-base font-semibold">Your posters</h2>
        {!rows ? <p className="text-sm text-ink-3">{err ? 'Poster service unavailable.' : 'Loading…'}</p>
          : !rows.length ? <p className="text-sm text-ink-3">No posters yet.</p>
          : <ul className="divide-y divide-line overflow-hidden rounded-box border border-line bg-raised">
            {rows.map(r => <li key={r.project_id}><button onClick={() => onOpen(r.project_id)} className={cx('flex w-full items-center gap-4 px-4 py-3 text-left hover:bg-act-subtle', MOTION)}>
              <span className="flex-1 truncate font-medium">{r.name}</span>{r.dirty ? <Pill ok={false}>Unsaved changes</Pill> : <Pill ok>Saved</Pill>}</button></li>)}
          </ul>}
      </section>
    </div>
  )
}

// ------------------------------------------------------------------ editor
type Gesture = { id: string; kind: 'move' | 'resize'; sx: number; sy: number; scale: number; dx: number; dy: number }
type Pending = { action: string; extra: Record<string, unknown> }

type Zoom = 'fit' | '25' | '50' | '75' | '100'
type Mode = 'edit' | 'export'
type Side = 'layers' | 'props' | 'quality' | 'reel'
type Finding = { name: string; level: string; detail: string; element_id: string }
type Run = { png: boolean; phase: Phase }
const ZOOMS: [Zoom, string][] = [['fit', 'Fit'], ['25', '25%'], ['50', '50%'], ['75', '75%'], ['100', '100%']]
const MOD = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl+'
const CHECKER = { backgroundImage: 'conic-gradient(var(--color-bg-raised) 25%, var(--color-bg-surface) 0 50%, var(--color-bg-raised) 0 75%, var(--color-bg-surface) 0)', backgroundSize: '24px 24px' }
const layerKind = (l: Layer, text?: { language: string }) => l.type === 'text' ? (text?.language === 'te' ? 'Telugu text' : 'English text') : l.style.shape === 'ellipse' ? 'Ellipse' : 'Rectangle'
const layerName = (l: Layer, text?: { text: string }) => l.type === 'text' ? (text?.text.split('\n')[0] || 'empty text') : l.style.shape === 'ellipse' ? 'Ellipse' : 'Rectangle'
const PANEL_HEAD = 'text-xs font-semibold tracking-wide text-ink-3'

export function PosterEditor({ id }: { id: string }) {
  const [p, setP] = useState<PosterProject | null>(null)
  const [sel, setSel] = useState<string | null>(null)
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const [upgrade, setUpgrade] = useState<Pending | null>(null)
  const [faces, setFaces] = useState<Record<string, Face> | null>(null); const [pngOk, setPngOk] = useState(false); const [fontNote, setFontNote] = useState('Loading pinned fonts…')
  const [scene, setScene] = useState<Scene | null>(null); const [preview, setPreview] = useState<string | null>(null)
  const [overflow, setOverflow] = useState<string[]>([]); const [previewErr, setPreviewErr] = useState<string | null>(null)
  const [measured, setMeasured] = useState<MeasuredCheck[]>([])
  const [qa, setQa] = useState<PosterQA | null>(null); const [links, setLinks] = useState<ContentLink[]>([])
  const [gesture, setGesture] = useState<Gesture | null>(null)
  const [exporting, setExporting] = useState(false); const [receipt, setReceipt] = useState<ExportReceipt | null>(null)
  const [mode, setMode] = useState<Mode>('edit'); const [zoom, setZoom] = useState<Zoom>('fit'); const [side, setSide] = useState<Side>('props')
  const [scale, setScale] = useState<number | null>(null); const [reelFound, setReelFound] = useState<{ id: string; rows: { name: string; status: string }[] } | null>(null)
  const [run, setRun] = useState<Run | null>(null); const [exportErr, setExportErr] = useState<string | null>(null)
  const frame = useRef<HTMLDivElement>(null); const seq = useRef(0)
  const composing = useRef(false); const layerBtns = useRef<(HTMLButtonElement | null)[]>([])
  const root = useRef<HTMLDivElement>(null); const [narrow, setNarrow] = useState(false)
  const [tick, setTick] = useState(0); const tracked = useTask({ poster: id }, tick); const task = tracked.task && !tracked.task.cancelled ? tracked.task : null

  useEffect(() => { setP(null); setSel(null); creative.view(id).then(setP).catch(e => setErr(msg(e))) }, [id])
  useEffect(() => {   // M5's pinned fonts, then M5's own probe that decides whether PNG export is trustworthy here
    creative.fonts().then(async f => {
      if (!f.fonts) throw Error(f.error ?? 'Pinned fonts unavailable.')
      await loadFonts(f.fonts); setFaces(f.fonts)
      const proof = await qualifyEmbedded(f.fonts); setPngOk(proof.ok)
      setFontNote(proof.ok ? 'Pinned Inter Bold and Noto Sans Telugu Black loaded. PNG export available.' : `PNG export unavailable: ${proof.reason}`)
    }).catch(e => setFontNote(`Export unavailable: ${msg(e)}`))
  }, [])
  useEffect(() => {   // every revision: fresh SVG from the server, M5's overflow check in this browser, and poster QA
    if (!p || !faces) return
    const n = ++seq.current
    creative.scene(p).then(async s => {
      const check = await inspectScene(s)
      if (n !== seq.current) return
      const ink = await measureText(s)
      if (n !== seq.current) return
      setScene(s); setOverflow(check.overflow); setMeasured(measuredChecks(ink, s.profile as unknown as { width: number; height: number }, SAFE_MARGIN)); setPreviewErr(null)
      setPreview(old => { if (old) URL.revokeObjectURL(old); return URL.createObjectURL(new Blob([s.svg], { type: 'image/svg+xml' })) })
    }).catch(e => { if (n === seq.current) { setScene(null); setPreviewErr(msg(e)) } })
    creative.qa(p).then(q => { if (n === seq.current) setQa(q) }).catch(() => { if (n === seq.current) setQa(null) })
    creative.links(p).then(l => { if (n === seq.current) setLinks(l) }).catch(() => {})
  }, [p, faces])
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  useEffect(() => {   // do not lose unsaved work by closing the window
    const on = (e: BeforeUnloadEvent) => { if (p?.dirty) e.preventDefault() }
    window.addEventListener('beforeunload', on); return () => window.removeEventListener('beforeunload', on)
  }, [p?.dirty])

  const act = useCallback(async (action: string, extra: Record<string, unknown> = {}) => {
    if (!p) return
    setBusy(true); setErr(null); setReceipt(null); setRun(null); setExportErr(null)
    try { setP(await creative.action(p, action, extra)); setUpgrade(null) }
    catch (e) {
      if (e instanceof CreativeError && e.code === 'upgrade-required') setUpgrade({ action, extra })
      else { setErr(msg(e)); if (e instanceof CreativeError && e.code === 'conflict') creative.view(p.project_id).then(setP).catch(() => {}) }
    } finally { setBusy(false) }
  }, [p])

  // Keyboard: M5's own policy (editing.mjs) decides what a key means, including IME composition and text fields.
  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if (!p || e.defaultPrevented || document.querySelector('dialog[open]')) return
      const t = e.target as HTMLElement | null
      const editable = !!t?.matches?.('input,textarea,select,[contenteditable="true"]')
      const idle = !busy && !exporting && !gesture
      const command = shortcut(e, composing.current, editable)
      if (command === 'apply-text') {
        if (t?.id !== 'if-layer-text') return
        e.preventDefault(); (document.getElementById('if-apply-text') as HTMLButtonElement | null)?.click(); return
      }
      if (command) {
        e.preventDefault()   // also keeps the browser's own Save dialog away
        if (!idle) return
        if (command === 'save' && p.dirty) act('save')
        if (command === 'undo' && p.can_undo) act('undo')
        if (command === 'redo' && p.can_redo) act('redo')
        return
      }
      if (mode !== 'edit' || !idle) return
      const layer = p.elements.find(x => x.id === sel)
      const delta = nudge(e, composing.current, editable)
      if (delta && layer) { e.preventDefault(); act('move', { element_id: layer.id, x: layer.x + delta.x, y: layer.y + delta.y }) }
      else if (e.key === 'Escape' && !editable && sel) setSel(null)
    }
    document.addEventListener('keydown', on); return () => document.removeEventListener('keydown', on)
  }, [p, sel, busy, exporting, gesture, mode, act])

  const loaded = !!p
  const reelLinks = reelFound && reelFound.id === id ? reelFound.rows : null
  useEffect(() => {   // the real zoom of "Fit": the frame's width against the 1080 px poster
    const node = frame.current; if (!node || !loaded) return
    const measure = () => setScale(Math.round(node.getBoundingClientRect().width / 1080 * 100))
    measure(); const ro = new ResizeObserver(measure); ro.observe(node); return () => ro.disconnect()
  }, [loaded, mode, zoom])
  useEffect(() => {   // B4B-4: below ~42rem of editor width the layer list moves into the panel tabs, so the canvas comes first
    const node = root.current; if (!node || !loaded) return
    const measure = () => setNarrow(node.getBoundingClientRect().width < 672)
    measure(); const ro = new ResizeObserver(measure); ro.observe(node); return () => ro.disconnect()
  }, [loaded])
  useEffect(() => {   // reels that carry the converter's record for this poster (read-only; same source as Projects)
    let live = true
    api.projects(false).then(async rows => { const l = await readLinks(rows); if (live) setReelFound({ id, rows: l.filter(x => x.posterId === id).map(x => ({ name: x.reel, status: reelStatusLabel(rows.find(r => r.name === x.reel) ?? {}) })) }) }).catch(() => { if (live) setReelFound({ id, rows: [] }) })
    return () => { live = false }
  }, [id])

  if (!p) return <div><a href="#/projects" className="mb-4 inline-block text-sm text-link hover:underline">← Projects</a>{err ? <Err msg={err} /> : <p className="text-sm text-ink-3">Opening poster…</p>}</div>
  const view = p.view; const layers = p.elements.filter(e => e.view_id === view.id)
  const el = layers.find(e => e.id === sel) ?? null
  const textOf = (e: Layer) => p.content.find(c => c.id === e.content_id)
  const current = !!scene && scene.revision === p.revision && scene.project_id === p.project_id
  const locked = busy || exporting
  const stack = [...layers].reverse()   // top layer first, as in the list

  // ---- pointer gestures on the poster: move a layer, or resize it from its corner handle
  const begin = (e: React.PointerEvent, layer: Layer, kind: Gesture['kind']) => {
    if (locked || !frame.current) return
    e.preventDefault(); e.stopPropagation(); setSel(layer.id)
    ;(e.target as Element).setPointerCapture(e.pointerId)
    setGesture({ id: layer.id, kind, sx: e.clientX, sy: e.clientY, scale: view.width / frame.current.getBoundingClientRect().width, dx: 0, dy: 0 })
  }
  const moveG = (e: React.PointerEvent) => { if (gesture) setGesture({ ...gesture, dx: (e.clientX - gesture.sx) * gesture.scale, dy: (e.clientY - gesture.sy) * gesture.scale }) }
  const ghost = (layer: Layer) => {
    if (!gesture || gesture.id !== layer.id) return layer
    if (gesture.kind === 'move') return { ...layer, x: Math.round(layer.x + gesture.dx), y: Math.round(layer.y + gesture.dy) }
    try { return { ...layer, ...resizeBox(layer, 'se', gesture.dx, gesture.dy, false, view) } } catch { return layer }
  }
  const endG = () => {
    if (!gesture) return
    const layer = layers.find(x => x.id === gesture.id); setGesture(null)
    if (!layer || Math.abs(gesture.dx) + Math.abs(gesture.dy) < 1) return
    const g = ghost(layer)
    if (gesture.kind === 'move') act('move', { element_id: layer.id, x: g.x, y: g.y })
    else act('geometry', { view_id: view.id, targets: [{ element_id: layer.id, x: g.x, y: g.y, width: g.width, height: g.height }], acknowledge_upgrade: false })
  }
  const reorder = (delta: number) => {
    if (!el) return
    const ids = layers.map(x => x.id); const i = ids.indexOf(el.id); const j = i + delta
    if (j < 0 || j >= ids.length) return
    ;[ids[i], ids[j]] = [ids[j], ids[i]]
    act('reorder', { view_id: view.id, ordered_element_ids: ids, acknowledge_upgrade: false })
  }
  const layerKey = (e: React.KeyboardEvent, i: number) => {   // arrow keys walk the layer list (M5's nextLayerIndex)
    if (!['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key) || e.altKey || e.ctrlKey || e.metaKey) return
    e.preventDefault()
    const j = nextLayerIndex(i, e.key, stack.length)
    if (j >= 0 && stack[j]) { setSel(stack[j].id); layerBtns.current[j]?.focus() }
  }

  // ---- export: M5's own handshake and browser checks, unchanged (the phase is only reported, never decided, here)
  const exportDraft = async (withPng: boolean) => {
    setExporting(true); setErr(null); setExportErr(null); setReceipt(null); setRun({ png: withPng, phase: 'begin' })
    // B4C-2: exporting ends the review; the QA numbers recorded are the ones on screen for this revision
    await report(task, 'review', 'done', { detail: `Revision ${p.revision}` })
    if (qa && qa.revision === p.revision) await report(task, 'qa', 'done', { detail: `${failing.filter(c => c.level === 'error').length} errors, ${failing.filter(c => c.level !== 'error').length} warnings on revision ${p.revision}` })
    await report(task, 'export', 'running', { detail: withPng ? 'SVG and PNG' : 'SVG' })
    try {
      if (!current) throw Error('The preview is not current yet.')
      const start = await creative.exportBegin(p)
      setRun({ png: withPng, phase: 'check' })
      const check = await inspectScene(start.scene)
      let png: string | null = null; let parity = false
      if (withPng) {
        setRun({ png: withPng, phase: 'raster' })
        const r = await raster(start.scene.svg); parity = await comparePng(r.canvas, r.blob)
        if (!parity) { setPngOk(false); throw Error('PNG disabled: the decoded image did not match the preview exactly.') }
        if (r.blob.size > 8 * 1024 * 1024) throw Error('PNG exceeds 8 MiB.')
        const bytes = new Uint8Array(await r.blob.arrayBuffer()); let s = ''
        for (let i = 0; i < bytes.length; i += 16384) s += String.fromCharCode(...bytes.subarray(i, i + 16384))
        png = btoa(s)
      }
      setRun({ png: withPng, phase: 'save' })
      const saved = await creative.exportFinish({ token: start.token, revision: start.scene.revision, png, qa: { fonts_loaded: check.fonts_loaded, overflow: check.overflow, parity, embedded_fonts: pngOk } })
      if (saved.manifest.svg_sha256 !== start.scene.svg_sha256) throw Error('Saved SVG does not match the preview.')
      setReceipt(saved); await report(task, 'export', 'done', { detail: `${saved.manifest.png_sha256 ? 'SVG and PNG' : 'SVG'} saved, revision ${saved.manifest.revision}` })
    } catch (e) { setExportErr(`Export refused: ${msg(e)}`); creative.exportCancel().catch(() => {}); await report(task, 'export', 'failed', { error: msg(e) }) }
    finally { setExporting(false); setTick(t => t + 1) }
  }

  // Server QA (declared boxes) + measured-ink QA from this browser. With a current preview, the measured safe-area check
  // replaces the box-based one (the box is usually larger than the drawn text).
  const failing = [...(qa?.checks.filter(c => !c.passed && !(c.name === 'safe_area' && current)) ?? []),
    ...(current ? measured.map(m => ({ ...m, passed: false })) : [])]
  const wordsBlocked = failing.some(c => c.name === 'approved_text')   // M7-A: the server refuses this export too
  const ready = readiness({ locked, current, previewErr, overflow: overflow.length, wordsBlocked, qaKnown: !!qa && qa.revision === p.revision,
    errors: failing.filter(c => c.level === 'error' && c.name !== 'approved_text').length, warnings: failing.filter(c => c.level !== 'error').length,
    fontsReady: !!faces, pngOk, pngNote: fontNote })
  const aspect = `${view.width} / ${view.height}`
  const status = previewErr ? previewErr : current ? 'Preview current' : 'Updating preview…'
  const brandName = (p.binding as Binding | null)?.record.brand?.record.payload.name
  const blocking = ready.items.filter(i => i.state === 'blocked').length; const toReview = failing.length
  const handoff = task?.kind === 'both' && ['waiting', 'failed'].includes(task.steps.find(s => s.id === 'handoff')?.status ?? '')
  const sideTabs: { id: Side; label: string }[] = [...(narrow ? [{ id: 'layers' as Side, label: 'Layers' }] : []), { id: 'props', label: 'Properties' },
    { id: 'quality', label: blocking ? `Quality · ${blocking} blocking` : toReview ? `Quality · ${toReview}` : 'Quality' }, { id: 'reel', label: handoff ? 'Reel · next' : 'Reel' }]
  const layersBody = <>
          <div className="flex items-center"><h2 className={PANEL_HEAD}>LAYERS</h2><span className="ml-auto text-xs text-ink-3">{layers.length} of {p.element_limit}</span></div>
          <ol className="space-y-0.5">
            {stack.map((l, i) => {
              const t = textOf(l); const link = links.find(k => k.element_id === l.id); const on = sel === l.id
              return <li key={l.id}><button ref={b => { layerBtns.current[i] = b }} onClick={() => setSel(l.id)} onKeyDown={e => layerKey(e, i)} aria-pressed={on}
                aria-label={l.type === 'text' ? `Text layer: ${layerName(l, t)}` : `${layerName(l)} layer`}
                className={cx('flex w-full items-center gap-2 rounded-field border-l-2 px-2 py-1.5 text-left text-sm', MOTION, on ? 'border-act bg-act-subtle text-link' : 'border-transparent hover:bg-raised')}>
                <span aria-hidden className={cx('grid h-5 w-5 shrink-0 place-items-center rounded-chip text-xs font-semibold', on ? 'bg-act text-on-act' : 'bg-raised text-ink-2')}>{l.type === 'text' ? 'T' : l.style.shape === 'ellipse' ? '○' : '□'}</span>
                <span className="min-w-0 flex-1">
                  <span className={cx('block truncate', on && 'font-medium', l.type === 'text' && t?.language === 'te' && 'te')}>{l.type === 'text' ? (t?.text.split('\n')[0] || '(empty text)') : layerName(l)}</span>
                  <span className={cx('block truncate text-xs', on ? 'text-link' : 'text-ink-3')}>{l.type === 'text' ? layerKind(l, t) : `${l.width} × ${l.height} px`}{link ? (link.ok ? ' · approved words' : ' · approved words changed') : ''}</span>
                </span>
                {link && <span title="Approved words from a reel" className={cx('text-xs font-semibold', link.ok ? 'text-ok' : 'text-bad')}>{link.ok ? '✓' : '!'}</span>}
              </button></li>
            })}
          </ol>
          <div>
            <div className="mb-1 text-xs text-ink-3">Order of the selected layer</div>
            <div className="grid grid-cols-2 gap-1"><Btn kind="quiet" disabled={locked || !el} onClick={() => reorder(1)} title="Bring forward">Forward</Btn><Btn kind="quiet" disabled={locked || !el} onClick={() => reorder(-1)} title="Send backward">Backward</Btn></div>
          </div>
          <div className="border-t border-line pt-3">
            <div className="mb-1 text-xs text-ink-3">Add a layer</div>
            <div className="grid grid-cols-2 gap-1 [&>button]:px-2 [&>button]:text-xs">
              <Btn kind="ghost" disabled={locked || p.remaining_text_slots.te < 1 || layers.length >= p.element_limit} onClick={() => act('add_text', { language: 'te' })}>+ Telugu</Btn>
              <Btn kind="ghost" disabled={locked || p.remaining_text_slots.en < 1 || layers.length >= p.element_limit} onClick={() => act('add_text', { language: 'en' })}>+ English</Btn>
              <Btn kind="ghost" disabled={locked || layers.length >= p.element_limit} onClick={() => act('add_shape', { shape: 'rectangle' })}>+ Rectangle</Btn>
              <Btn kind="ghost" disabled={locked || layers.length >= p.element_limit} onClick={() => act('add_shape', { shape: 'ellipse' })}>+ Ellipse</Btn>
            </div>
          </div>
  </>
  const shownSide: Side = side === 'layers' && !narrow ? 'props' : side
  const zoomLabel = zoom === 'fit' ? (scale ? `Fit · ${scale}%` : 'Fit') : `${zoom}%`
  return (
    <div ref={root} data-surface="editor" className="@container overflow-hidden rounded-sheet bg-canvas text-ink shadow-float">
      {/* toolbar: where you are, what it is, its real save state, history, and the two views */}
      <div role="toolbar" aria-label="Poster" className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-line bg-surface px-4 py-2.5">
        <a href="#/projects" className={cx('rounded-field px-1 text-sm text-ink-2 hover:text-ink', MOTION)}>← Projects</a>
        <span aria-hidden className="hidden h-6 w-px bg-line sm:block" />
        <div className="min-w-0 max-w-full">
          <h1 className="truncate text-sm font-semibold">{p.name}</h1>
          <p className="truncate text-xs text-ink-3">Poster · {view.width} × {view.height} px · revision {p.revision}{brandName ? ` · brand kit ${brandName}` : ''}</p>
        </div>
        <span role="status">{p.dirty ? <Pill ok={false}>Unsaved changes</Pill> : <Pill ok>Saved on this Mac</Pill>}</span>
        <span className="ml-auto" />
        <Tabs label="Editor view" value={mode} onChange={setMode} tabs={[{ id: 'edit', label: 'Edit' }, { id: 'export', label: 'Export' }]} />
        <span aria-hidden className="hidden h-6 w-px bg-line sm:block" />
        <Btn kind="quiet" disabled={locked || !p.can_undo} onClick={() => act('undo')} title={`Undo (${MOD}Z)`}>Undo</Btn>
        <Btn kind="quiet" disabled={locked || !p.can_redo} onClick={() => act('redo')} title={`Redo (${MOD}Shift+Z)`.replace('⌘Shift+', '⇧⌘')}>Redo</Btn>
        <Btn kind={p.dirty ? 'primary' : 'ghost'} disabled={locked || !p.dirty} onClick={() => act('save')} title={`Save (${MOD}S)`}>Save</Btn>
      </div>
      <TaskStrip task={task} />
      {(upgrade || wordsBlocked || err) && <div className="space-y-2 border-b border-line px-4 py-3">
        {upgrade && <Notice tone="warning">
          This change needs the newer edit-history format (v3). Older M5 Studio versions cannot open this poster afterwards.
          <span className="ml-3 inline-flex gap-2"><Btn kind="ghost" disabled={locked} onClick={() => act(upgrade.action, { ...upgrade.extra, acknowledge_upgrade: true })}>Upgrade and continue</Btn><Btn kind="quiet" onClick={() => setUpgrade(null)}>Cancel</Btn></span></Notice>}
        {wordsBlocked && <Notice tone="error" title="Export blocked.">Approved reel words on this poster no longer match their approval. Undo the edit or insert the approved line again. If the new wording is intended, approve it in that reel first, then insert it from there.</Notice>}
        {err && <Notice tone="error">{err}</Notice>}
      </div>}

      {mode === 'edit' ? <div className="grid @2xl:grid-cols-[13rem_minmax(0,1fr)] @4xl:h-[calc(100vh-8.5rem)] @4xl:min-h-[36rem] @4xl:grid-cols-[13rem_minmax(0,1fr)_18rem] @6xl:grid-cols-[15rem_minmax(0,1fr)_20rem]">
        {!narrow && <aside aria-label="Layers" className="flex flex-col gap-3 border-b border-line bg-surface p-3 @2xl:border-r @4xl:overflow-auto @4xl:border-b-0">{layersBody}</aside>}

        {/* canvas: the poster is the focus; zoom floats over the workspace */}
        <section aria-label="Poster" className="relative flex min-h-[24rem] min-w-0 flex-col">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 text-xs text-ink-3">
            <span>{view.width} × {view.height} px</span><span>Zoom {zoomLabel}</span>
            <span className={previewErr ? 'text-bad' : undefined}>{status}</span>
            <span className="ml-auto">Dashed line: {SAFE_MARGIN} px safe area</span>
          </div>
          <div className="min-h-0 flex-1 overflow-auto px-6 pt-2 pb-20" tabIndex={zoom === 'fit' ? undefined : 0} aria-label={zoom === 'fit' ? undefined : 'Poster, scrollable'}>
            <div ref={frame} onPointerMove={moveG} onPointerUp={endG} onPointerCancel={() => setGesture(null)} onPointerDown={() => setSel(null)}
              className="relative mx-auto select-none overflow-hidden rounded-chip shadow-float ring-1 ring-line"
              style={{ width: zoomWidth(zoom), aspectRatio: aspect, ...CHECKER }}>
              {preview && <img src={preview} alt="Poster preview" draggable={false} className={cx('absolute inset-0 h-full w-full', !current && 'opacity-60')} />}
              <div aria-hidden className="pointer-events-none absolute border border-dashed border-line-strong/60"
                style={{ left: `${SAFE_MARGIN / view.width * 100}%`, top: `${SAFE_MARGIN / view.height * 100}%`, right: `${SAFE_MARGIN / view.width * 100}%`, bottom: `${SAFE_MARGIN / view.height * 100}%` }} />
              {layers.map(l => {
                const b = clippedBox(ghost(l), view); if (!b) return null
                const on = sel === l.id
                return <div key={l.id} onPointerDown={e => begin(e, l, 'move')} title={l.type === 'text' ? 'Text layer' : 'Shape layer'}
                  className={cx('absolute cursor-move', on ? 'z-10 outline-2 outline-offset-2 outline-focus' : 'hover:outline hover:outline-1 hover:outline-focus/60', overflow.includes(l.id) && 'outline-2 outline-bad')}
                  style={{ left: `${b.left}%`, top: `${b.top}%`, width: `${b.width}%`, height: `${b.height}%` }}>
                  {on && <span onPointerDown={e => begin(e, l, 'resize')} title="Resize" className="absolute -right-2 -bottom-2 h-3.5 w-3.5 cursor-nwse-resize rounded-chip bg-focus ring-2 ring-canvas" />}
                </div>
              })}
            </div>
          </div>
          <div role="group" aria-label="Zoom" className="absolute bottom-14 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-box border border-line bg-raised/95 p-1 shadow-lift backdrop-blur">
            <Btn kind="quiet" aria-pressed={zoom === 'fit'} onClick={() => setZoom('fit')}>Fit</Btn>
            <Select aria-label="Zoom level" value={zoom} onChange={e => setZoom(e.target.value as Zoom)}>{ZOOMS.map(([v, t]) => <option key={v} value={v}>{v === 'fit' ? zoomLabel.replace(/^Fit$/, t) : t}</option>)}</Select>
            <Btn kind="quiet" aria-pressed={zoom === '100'} onClick={() => setZoom('100')}>100%</Btn>
          </div>
          <div className="border-t border-line bg-surface px-4 py-2 text-xs text-ink-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="min-w-0 truncate">{el ? <>Selected: <span className={textOf(el)?.language === 'te' ? 'te' : undefined}>{layerName(el, textOf(el))}</span> · X {el.x}, Y {el.y} · {el.width} × {el.height}</> : 'Nothing selected'}</span>
              <details className="relative ml-auto"><summary className={cx('cursor-pointer text-ink-2', MOTION)}>Keyboard shortcuts</summary>
                <div className="absolute right-0 bottom-full z-10 mb-2 w-72 rounded-box border border-line bg-raised p-3 text-ink-2 shadow-float">
                  <ul className="space-y-1">
                    <li><kbd>{MOD}S</kbd> Save</li><li><kbd>{MOD}Z</kbd> Undo · <kbd>{MOD === '⌘' ? '⇧⌘Z' : 'Ctrl+Shift+Z'}</kbd> Redo</li>
                    <li><kbd>{MOD}Enter</kbd> Apply text (in the text box)</li><li><kbd>{MOD === '⌘' ? '⌥' : 'Alt+'}Arrow</kbd> Move 1 px · with <kbd>Shift</kbd> 10 px</li>
                    <li><kbd>↑ ↓ Home End</kbd> Walk the layer list</li><li><kbd>Esc</kbd> Clear the selection</li>
                  </ul>
                  <p className="mt-2 text-ink-3">Undo and redo shortcuts work outside text boxes, so typing keeps its own undo.</p></div></details>
            </div>
          </div>
        </section>

        {/* right: properties of the selection, quality and readiness, reel context */}
        <aside aria-label="Inspector" className="flex flex-col border-t border-line bg-surface @2xl:col-span-2 @4xl:col-span-1 @4xl:overflow-auto @4xl:border-t-0 @4xl:border-l">
          <div className="sticky top-0 z-10 overflow-x-auto border-b border-line bg-surface p-2"><Tabs label="Inspector" value={shownSide} onChange={setSide} tabs={sideTabs} /></div>
          <div className="space-y-4 p-3">
            {shownSide === 'layers' && <div className="flex flex-col gap-3" role="region" aria-label="Layers">{layersBody}</div>}
            {shownSide === 'props' && (!el ? <p className="text-sm text-ink-3">Select a layer on the poster or in the list to edit its text, size, colour and position.</p>
              : <>
                <div><h2 className={PANEL_HEAD}>{layerKind(el, textOf(el)).toUpperCase()}</h2>
                  <p className={cx('mt-1 truncate text-sm font-medium', textOf(el)?.language === 'te' && 'te')}>{layerName(el, textOf(el))}</p></div>
                <Inspector key={`${el.id}-${p.revision}`} p={p} el={el} text={textOf(el)} link={links.find(k => k.element_id === el.id)} locked={locked} act={act} onComposing={v => { composing.current = v }} />
              </>)}
            {shownSide === 'quality' && <QualityPanel ready={ready} qa={qa && qa.revision === p.revision ? qa : null} failing={failing} brand={brandName} onShow={id => { setSel(id); setSide('props') }} onExport={() => setMode('export')} />}
            {shownSide === 'reel' && <>
              <div>
                <h2 className={cx('mb-2', PANEL_HEAD)}>REELS MADE FROM THIS POSTER</h2>
                {reelLinks === null ? <p className="text-xs text-ink-3">Checking…</p> : !reelLinks.length ? <p className="text-xs text-ink-3">None recorded yet.</p>
                  : <ul className="space-y-1">{reelLinks.map(r => <li key={r.name} className="rounded-field bg-raised p-2 text-sm"><a href={reelHref(r.name)} className="font-medium text-link hover:underline">{r.name}</a>
                    <span className="block text-xs text-ink-3">{r.status} · opens its reel steps</span></li>)}</ul>}
                <p className="mt-2 text-xs text-ink-3">Reels are edited in their own steps. There is no reel timeline in this editor.</p>
              </div>
              <ApprovedPanel p={p} locked={locked} onInserted={(np, id) => { setP(np); setSel(id); setSide('props') }} />
              {handoff && <Notice tone="info" title="Next: the reel.">This creation was started as poster and reel. Export the poster as SVG and PNG, save it, then make the reel below. You approve its script in the reel before anything is built or rendered.</Notice>}
              <MakeReelPanel p={p} locked={locked} task={task} onMade={() => setTick(t => t + 1)} />
            </>}
          </div>
        </aside>
      </div>
        : <div className="grid gap-4 p-4 @4xl:grid-cols-[minmax(0,1fr)_minmax(0,28rem)]">
          <section aria-label="Poster preview" className="min-w-0">
            <div className="relative mx-auto overflow-hidden rounded-chip shadow-float ring-1 ring-line" style={{ width: zoomWidth('fit'), aspectRatio: aspect, ...CHECKER }}>
              {preview && <img src={preview} alt="Poster preview" draggable={false} className={cx('absolute inset-0 h-full w-full', !current && 'opacity-60')} />}
            </div>
            <p className={cx('mt-2 text-center text-xs', previewErr ? 'text-bad' : 'text-ink-3')}>{status} · revision {p.revision}</p>
          </section>
          <ExportStep p={p} ready={ready} exporting={exporting} run={run} receipt={receipt} error={exportErr} qaErrors={failing.filter(c => c.level === 'error')} qaWarnings={failing.filter(c => c.level !== 'error')}
            onExport={exportDraft} onEdit={id => { if (id) { setSel(id); setSide('props') } setMode('edit') }} />
        </div>}
    </div>
  )
}

// ------------------------------------------------------------------ M7-B B4B-3: quality and readiness (the real checks only)
// Everything shown here was actually run: M5's overflow check and poster QA on the server, measured text in this browser,
// and the export gates. What this build does not check is listed as not checked, never as passed.
const NOT_CHECKED = ['Spelling, facts, dates and names in your text', 'Whether colours and fonts match a brand kit', 'Translation: text is used exactly as typed', 'Accessibility certification: the contrast rule here is IDEAFRAME\'s own check, not a WCAG audit']
const CHECK_LABEL: Record<string, string> = { canvas: 'Inside the poster', safe_area: 'Safe area', empty: 'Text present', contrast: 'Contrast against its background', glyphs: 'Characters in the pinned fonts', overlap: 'Text overlap', approved_text: 'Approved words', measured_canvas: 'Drawn text inside the poster', measured_safe_area: 'Drawn text in the safe area' }
const checkLabel = (n: string) => CHECK_LABEL[n] ?? n.replace(/_/g, ' ')

function ReadinessList({ items }: { items: ReturnType<typeof readiness>['items'] }) {
  return <ul className="space-y-2">{items.map(i => <li key={i.id} className="grid grid-cols-[1.25rem_1fr] gap-x-1 text-sm">
    <span aria-hidden className={cx('font-semibold', STATE[i.state].tone)}>{STATE[i.state].symbol}</span>
    <div><span className="font-medium">{i.label}</span> <span className={cx('text-xs font-semibold', STATE[i.state].tone)}>{STATE[i.state].word}</span>
      <span className="block text-xs text-ink-2">{i.detail}</span></div></li>)}</ul>
}
function BrandRights({ brand }: { brand?: string }) {
  return <>
    <p className="text-sm">{brand ? `Brand kit: ${brand} (approved version, linked to this poster).` : 'No brand kit is linked to this poster.'}</p>
    <p className="mt-1 text-xs text-ink-2">This editor places no logos or other brand assets, so none are exported. Brands whose rights are not reviewed and approved cannot be used. Check any names, marks or quotes in your own text before sharing.</p>
  </>
}

function QualityPanel({ ready, qa, failing, brand, onShow, onExport }: { ready: ReturnType<typeof readiness>; qa: PosterQA | null; failing: Finding[]; brand?: string; onShow: (elementId: string) => void; onExport: () => void }) {
  const blocked = ready.items.some(i => i.state === 'blocked'); const pending = ready.items.some(i => i.state === 'pending')
  const errors = failing.filter(c => c.level === 'error'), warnings = failing.filter(c => c.level !== 'error')
  const passed = qa ? Object.entries(qa.checks.filter(c => c.passed).reduce<Record<string, number>>((m, c) => ({ ...m, [c.name]: (m[c.name] ?? 0) + 1 }), {})) : []
  return <>
    <div>
      <div className="mb-2 flex items-center gap-2"><h2 className={PANEL_HEAD}>EXPORT READINESS</h2>
        <span className="ml-auto" role="status"><Pill ok={blocked ? false : pending || errors.length || warnings.length ? null : true}>{blocked ? 'Blocked' : pending ? 'Checking' : errors.length || warnings.length ? 'Review first' : 'Ready'}</Pill></span></div>
      <ReadinessList items={ready.items} />
      <Btn kind="ghost" className="mt-3 w-full" onClick={onExport}>Open Export</Btn>
    </div>
    <div className="border-t border-line pt-3">
      <h2 className={cx('mb-2', PANEL_HEAD)}>POSTER QA</h2>
      {!qa ? <p className="text-xs text-ink-3">Checking this revision…</p> : <>
        {errors.length > 0 && <Findings title={`Errors (${errors.length})`} tone="text-bad" rows={errors} onShow={onShow} />}
        {warnings.length > 0 && <Findings title={`Warnings (${warnings.length})`} tone="text-warn" rows={warnings} onShow={onShow} />}
        {!failing.length && <p className="text-xs text-ok">No errors or warnings on this revision.</p>}
        {passed.length > 0 && <details className="mt-2 text-xs"><summary className={cx('cursor-pointer text-ink-2', MOTION)}>Passed checks ({passed.reduce((n, [, c]) => n + c, 0)})</summary>
          <ul className="mt-1 space-y-0.5 text-ink-2">{passed.map(([name, n]) => <li key={name}><span aria-hidden className="mr-1 font-semibold text-ok">✓</span>{checkLabel(name)} <span className="text-ink-3">· {n} layer{n === 1 ? '' : 's'}</span></li>)}</ul></details>}
      </>}
    </div>
    <div className="border-t border-line pt-3">
      <h2 className={cx('mb-2', PANEL_HEAD)}>NOT CHECKED BY IDEAFRAME</h2>
      <ul className="space-y-0.5 text-xs text-ink-2">{NOT_CHECKED.map(t => <li key={t}><span aria-hidden className="mr-1 text-ink-3">–</span>{t}</li>)}</ul>
      <p className="mt-2 text-xs text-ink-3">These checks are rules, not AI. Nothing is repaired or approved for you.</p>
    </div>
    <div className="border-t border-line pt-3"><h2 className={cx('mb-2', PANEL_HEAD)}>BRAND AND RIGHTS</h2><BrandRights brand={brand} /></div>
  </>
}
function Findings({ title, tone, rows, onShow }: { title: string; tone: string; rows: Finding[]; onShow: (elementId: string) => void }) {
  return <div className="mb-2"><h3 className={cx('text-xs font-semibold', tone)}>{title}</h3>
    <ul className="mt-1 space-y-1">{rows.map((c, i) => <li key={i}><button onClick={() => onShow(c.element_id)} title="Select this layer" className={cx('w-full rounded-field px-1.5 py-1 text-left text-xs hover:bg-raised', MOTION)}>
      <span className="font-medium">{checkLabel(c.name)}</span><span className="block text-ink-2">{c.detail}</span></button></li>)}</ul></div>
}

// ------------------------------------------------------------------ M7-B B3: the Export step
// It shows the gates; it does not own them. The buttons use the same conditions the toolbar had, and the server
// (M5 handshake + approved-text block) still refuses on its own.
const STATE: Record<ItemState, { symbol: string; word: string; tone: string }> = {
  ok: { symbol: '✓', word: 'Ready', tone: 'text-ok' }, blocked: { symbol: '✕', word: 'Blocked', tone: 'text-bad' },
  advisory: { symbol: '!', word: 'Review', tone: 'text-warn' }, pending: { symbol: '…', word: 'Checking', tone: 'text-ink-3' },
}

function ExportStep({ p, ready, exporting, run, receipt, error, qaErrors, qaWarnings, onExport, onEdit }: {
  p: PosterProject; ready: ReturnType<typeof readiness>; exporting: boolean; run: Run | null; receipt: ExportReceipt | null; error: string | null
  qaErrors: Finding[]; qaWarnings: Finding[]; onExport: (withPng: boolean) => void; onEdit: (elementId?: string) => void }) {
  const [copied, setCopied] = useState(false)
  const brand = (p.binding as Binding | null)?.record.brand?.record.payload.name
  const steps = PHASES.filter(s => s.id !== 'raster' || run?.png)
  const at = run ? steps.findIndex(s => s.id === run.phase) : -1
  const copy = async () => { if (!receipt) return; try { await navigator.clipboard.writeText(receipt.directory); setCopied(true) } catch { setCopied(false) } }
  const box = 'rounded-box bg-surface p-3'
  return (
    <section aria-label="Export" className="space-y-4">
      <div className={box}>
        <div className="mb-2 flex items-center gap-2"><h2 className={PANEL_HEAD}>OUTPUT</h2><span className="ml-auto"><Pill ok={null}>Draft · not approved</Pill></span></div>
        <dl className="grid grid-cols-[6.5rem_1fr] gap-y-1 text-sm">
          <dt className="text-ink-3">Type</dt><dd>Poster draft</dd>
          <dt className="text-ink-3">Size</dt><dd>{p.view.width} × {p.view.height} px</dd>
          <dt className="text-ink-3">Background</dt><dd>Transparent</dd>
          <dt className="text-ink-3">Formats</dt><dd>SVG, or SVG with a PNG copy. No other formats.</dd>
          <dt className="text-ink-3">Revision</dt><dd>{p.revision}{p.dirty ? ' · not saved yet' : ''}</dd>
        </dl>
        <p className="mt-2 text-xs text-ink-3">An export is a draft file for you to check. IDEAFRAME does not approve posters, and exporting does not approve this one.</p>
      </div>

      <div className={box}>
        <h2 className={cx('mb-2', PANEL_HEAD)}>READINESS</h2>
        <ReadinessList items={ready.items} />
        {(qaErrors.length > 0 || qaWarnings.length > 0) && <details className="mt-3 text-xs" open={qaErrors.length > 0}>
          <summary className={cx('cursor-pointer text-ink-2', MOTION)}>QA summary: {qaErrors.length} error{qaErrors.length === 1 ? '' : 's'}, {qaWarnings.length} warning{qaWarnings.length === 1 ? '' : 's'}</summary>
          <ul className="mt-1 space-y-1">{[...qaErrors, ...qaWarnings].map((c, i) => <li key={i}><button onClick={() => onEdit(c.element_id)} title="Show this layer in Edit" className="w-full rounded-field px-1 py-0.5 text-left hover:bg-raised">
            <span className={c.level === 'error' ? 'font-semibold text-bad' : 'font-semibold text-warn'}>{c.level === 'error' ? 'Error' : 'Warning'} · {c.name.replace(/_/g, ' ')}</span>
            <span className="block text-ink-2">{c.detail}</span></button></li>)}</ul></details>}
      </div>

      <div className={box}>
        <h2 className={cx('mb-2', PANEL_HEAD)}>BRAND AND RIGHTS</h2>
        <BrandRights brand={brand} />
      </div>

      <div className={box}>
        <h2 className={cx('mb-2', PANEL_HEAD)}>EXPORT</h2>
        <div className="flex flex-wrap gap-2">
          <Btn kind="ghost" busy={exporting && run?.png === false} disabled={!ready.svg.allowed} onClick={() => onExport(false)}>Export SVG</Btn>
          <Btn busy={exporting && run?.png === true} disabled={!ready.png.allowed} onClick={() => onExport(true)}>Export SVG and PNG</Btn>
          <Btn kind="quiet" disabled={exporting} onClick={() => onEdit()}>Back to Edit</Btn>
        </div>
        {!exporting && (ready.svg.reason ?? ready.png.reason) && <p className="mt-2 text-xs text-ink-2">{ready.svg.reason ? `Export is not available: ${ready.svg.reason}` : `SVG only: ${ready.png.reason}`}</p>}
        {run && <ol role="status" aria-label="Export progress" className="mt-3 space-y-1 text-xs">
          {steps.map((s, i) => {
            const state = receipt || i < at ? 'done' : i === at ? (error ? 'failed' : 'now') : 'todo'
            return <li key={s.id} className={cx('flex items-center gap-2', state === 'done' ? 'text-ok' : state === 'failed' ? 'text-bad' : state === 'now' ? 'text-ink' : 'text-ink-3')}>
              <span aria-hidden className="w-4 text-center font-semibold">{state === 'done' ? '✓' : state === 'failed' ? '✕' : state === 'now' ? '›' : '·'}</span>
              {s.label}<span className="sr-only"> ({state === 'done' ? 'done' : state === 'failed' ? 'failed' : state === 'now' ? 'in progress' : 'waiting'})</span></li>
          })}</ol>}
        {error && <Notice tone="error" className="mt-3">{error}</Notice>}
        {receipt && <Notice tone="success" className="mt-3" title={`Draft exported${receipt.manifest.png_sha256 ? ' (SVG and PNG)' : ' (SVG)'}.`}>
          <span className="block">Revision {receipt.manifest.revision}, saved on this Mac in:</span>
          <code className="mt-1 block break-all text-xs">{receipt.directory}</code>
          <ul className="mt-1 text-xs">{savedFiles(receipt.directory, !!receipt.manifest.png_sha256).map(f => <li key={f}>{f.split('/').pop()}</li>)}</ul>
          <span className="mt-2 flex items-center gap-2"><Btn kind="ghost" onClick={copy}>Copy folder path</Btn>{copied && <span className="text-xs">Copied.</span>}</span>
        </Notice>}
      </div>
    </section>
  )
}

// ------------------------------------------------------------------ inspector for one layer
function Inspector({ p, el, text, link, locked, act, onComposing }: { onComposing: (v: boolean) => void; p: PosterProject; el: Layer; text?: { text: string; language: string }; link?: ContentLink; locked: boolean; act: (a: string, x?: Record<string, unknown>) => Promise<void> }) {
  const confirm = useConfirm()
  const [draft, setDraft] = useState(text?.text ?? ''); const [composing, setComposing] = useState(false)
  const [size, setSize] = useState(String(el.style.font_size ?? '')); const [fill, setFill] = useState(el.style.fill)
  const [box, setBox] = useState({ x: String(el.x), y: String(el.y), width: String(el.width), height: String(el.height) })
  const [err, setErr] = useState<string | null>(null)
  const num = (v: string) => (/^-?\d+$/.test(v.trim()) ? Number(v) : NaN)
  const posChanged = num(box.x) !== el.x || num(box.y) !== el.y; const sizeChanged = num(box.width) !== el.width || num(box.height) !== el.height
  const align = (kind: Parameters<typeof alignPosition>[2]) => {
    setErr(null)
    try { const at = alignPosition(el, p.view, kind, SAFE_MARGIN); act('move', { element_id: el.id, x: at.x, y: at.y }) } catch (e) { setErr(msg(e)) }
  }
  const label = 'block text-xs text-ink-2'
  return (
    <div className="space-y-3 text-sm">
      {link && <p className={cx('rounded-field px-2 py-1.5 text-xs', link.ok ? 'bg-ok-subtle text-ok' : 'bg-bad-subtle text-bad')}>
        Approved words ({link.kind}) from reel {link.reel}: {link.detail}.{link.ok ? ' Do not change them.' : ' Undo the edit, or remove this layer and insert the line again.'}</p>}
      {el.type === 'text' && <>
        <label className={label}>Text
          <TextArea id="if-layer-text" value={draft} onChange={e => setDraft(e.target.value)} rows={4} onCompositionStart={() => { setComposing(true); onComposing(true) }} onCompositionEnd={() => { setComposing(false); onComposing(false) }}
            className={cx('mt-1 w-full', text?.language === 'te' && 'te')} />
        </label>
        <div className="flex items-center gap-2"><Btn id="if-apply-text" title={`Apply text (${MOD}Enter)`} disabled={locked || composing || draft === text?.text || !draft.trim()} onClick={() => act('edit_text', { element_id: el.id, text: draft })}>Apply text</Btn>
          <span className="text-xs text-ink-3">{[...draft].length} characters · exactly as typed</span></div>
        <label className={label}>Font size (px)<div className="mt-1 flex gap-2"><Field type="number" min={1} max={512} value={size} onChange={e => setSize(e.target.value)} />
          <Btn kind="ghost" disabled={locked || num(size) === el.style.font_size || !(num(size) >= 1 && num(size) <= 512)} onClick={() => act('font_size', { element_id: el.id, font_size: num(size) })}>Set</Btn></div></label>
      </>}
      <label className={label}>Colour<div className="mt-1 flex items-center gap-2">
        <input type="color" value={fill.toLowerCase()} onChange={e => setFill(e.target.value)} aria-label="Pick colour" className="h-9 w-10 rounded-field border border-line-strong bg-raised" />
        <Field value={fill} onChange={e => setFill(e.target.value)} aria-label="Colour as #RRGGBB" />
        <Btn kind="ghost" disabled={locked || fill.toLowerCase() === el.style.fill.toLowerCase() || !/^#[0-9a-fA-F]{6}$/.test(fill)} onClick={() => act('color', { element_id: el.id, color: fill })}>Set</Btn></div></label>
      <div className="grid grid-cols-2 gap-2">
        {(['x', 'y', 'width', 'height'] as const).map(k => <label key={k} className={label}>{k === 'x' ? 'X' : k === 'y' ? 'Y' : k === 'width' ? 'Width' : 'Height'}
          <Field type="number" value={box[k]} onChange={e => setBox({ ...box, [k]: e.target.value })} /></label>)}
      </div>
      <div className="flex flex-wrap gap-2">
        <Btn kind="ghost" disabled={locked || !posChanged || Number.isNaN(num(box.x)) || Number.isNaN(num(box.y))} onClick={() => act('move', { element_id: el.id, x: num(box.x), y: num(box.y) })}>Move</Btn>
        <Btn kind="ghost" disabled={locked || !sizeChanged || !(num(box.width) >= 1) || !(num(box.height) >= 1)}
          onClick={() => act('geometry', { view_id: p.view.id, targets: [{ element_id: el.id, x: el.x, y: el.y, width: num(box.width), height: num(box.height) }], acknowledge_upgrade: false })}>Resize</Btn>
      </div>
      <div>
        <div className="mb-1 text-xs text-ink-2">Align inside the safe area</div>
        <div className="grid grid-cols-3 gap-1">
          {([['left', 'Left'], ['center-x', 'Centre'], ['right', 'Right'], ['top', 'Top'], ['center-y', 'Middle'], ['bottom', 'Bottom']] as const).map(([k, t]) =>
            <Btn key={k} kind="quiet" disabled={locked} onClick={() => align(k)}>{t}</Btn>)}
        </div>
      </div>
      <Err msg={err} />
      <Btn kind="danger" className="w-full" disabled={locked} onClick={async () => { if (await confirm({ title: 'Remove this layer?', body: 'You can bring it back with Undo.', confirmLabel: 'Remove layer', tone: 'danger' })) act('remove', { element_id: el.id }) }}>Remove layer</Btn>
    </div>
  )
}

// ------------------------------------------------------------------ step 6: approved reel words
const KIND_LABEL: Record<string, string> = { hook: 'Hook', quote: 'Quote (speaker\'s words)', headline: 'Headline', tag: 'Tag', number: 'Number card', post: 'Post intro', script: 'Script line' }

function ApprovedPanel({ p, locked, onInserted }: { p: PosterProject; locked: boolean; onInserted: (p: PosterProject, elementId: string) => void }) {
  const [reels, setReels] = useState<ReelRow[] | null>(null); const [reel, setReel] = useState('')
  const [doc, setDoc] = useState<ApprovedDoc | null>(null); const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false)
  useEffect(() => { creative.approvedReels().then(r => setReels(r.filter(x => x.ok))).catch(e => setErr(msg(e))) }, [])
  useEffect(() => { setDoc(null); setErr(null); if (reel) creative.approvedReel(reel).then(setDoc).catch(e => setErr(msg(e))) }, [reel])
  const insert = async (i: ApprovedDoc['items'][number]) => {
    if (!doc) return
    setBusy(true); setErr(null)
    try { const r = await creative.insertApproved(p, doc, i); onInserted(r.project, r.link.element_id) }
    catch (e) { setErr(msg(e)); if (e instanceof CreativeError && e.code === 'stale-approval') creative.approvedReel(reel).then(setDoc).catch(() => {}) }
    finally { setBusy(false) }
  }
  return (
    <div className="rounded-box bg-surface p-3">
      <h2 className="mb-2 text-xs font-semibold tracking-wide text-ink-3">APPROVED REEL WORDS</h2>
      {!reels ? <p className="text-xs text-ink-3">{err ?? 'Loading…'}</p> : !reels.length ? <p className="text-xs text-ink-3">No reel has approved words yet. Approve a plan or script in Reels first.</p> : <>
        <Select className="w-full" value={reel} onChange={e => setReel(e.target.value)} aria-label="Reel with approved words">
          <option value="">Choose a reel…</option>{reels.map(r => <option key={r.project} value={r.project}>{r.project} ({r.items})</option>)}</Select>
        {doc && <>
          <p className="mt-2 text-xs text-ink-3">{doc.approvals.map(a => a.type === 'project' ? 'hand-approved project (no fingerprint)' : `${a.type} approval ${a.hash?.slice(0, 10)}`).join(' · ')}</p>
          <ul className="mt-2 max-h-72 space-y-1 overflow-auto">{doc.items.map(i => <li key={i.id} className="rounded-field bg-raised p-2">
            <div className="flex items-center gap-2"><span className="text-xs text-ink-3">{KIND_LABEL[i.kind] ?? i.kind}</span>
              <Btn kind="quiet" className="ml-auto" disabled={locked || busy} onClick={() => insert(i)}>Insert</Btn></div>
            <div className={cx('text-sm', i.language === 'te' && 'te')}>{i.text}</div></li>)}</ul>
          <p className="mt-2 text-xs text-ink-3">Inserted exactly as approved. Poster QA flags any later edit.</p>
        </>}
      </>}
      <Err msg={err} />
    </div>
  )
}

// ------------------------------------------------------------------ step 7: poster -> ordinary reel (owner approves the script in Reels)
function MakeReelPanel({ p, locked, task, onMade }: { p: PosterProject; locked: boolean; task: Task | null; onMade: () => void }) {
  const [cat, setCat] = useState<Catalog | null>(null); const [brand, setBrand] = useState(''); const [platform, setPlatform] = useState('instagram')
  const [style, setStyle] = useState(''); const [slug, setSlug] = useState(''); const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null); const [made, setMade] = useState<{ project: string; slides: number } | null>(null)
  useEffect(() => { api.catalog().then(c => { setCat(c); const b = c.brands[0]; if (b) { setBrand(b.id); setStyle(b.default_style) } }).catch(e => setErr(msg(e))) }, [])
  const go = async () => {
    setBusy(true); setErr(null); setMade(null)
    const chain = task?.kind === 'both' ? task : null     // B4C-4: a poster-then-reel task continues into the reel it really made
    try { const r = await creative.toReel(p, { brand, platform, style, slug }); setMade(r); await report(chain, 'handoff', 'done', { reel: r.project, detail: `Reel ${r.project} created from the poster's PNG export; its script is not approved yet` }) }
    catch (e) { setErr(msg(e)); if (chain?.steps.find(s => s.id === 'handoff')?.status === 'waiting') await report(chain, 'handoff', 'failed', { error: msg(e) }) }
    finally { setBusy(false); onMade() }
  }
  if (!cat) return null
  return (
    <div className="rounded-box bg-surface p-3">
      <h2 className="mb-2 text-xs font-semibold tracking-wide text-ink-3">MAKE A REEL FROM THIS POSTER</h2>
      <p className="mb-2 text-xs text-ink-3">Uses the saved poster's latest PNG export as slides and its text, top to bottom, as the script. You approve the script in Reels before anything is rendered.</p>
      <div className="grid grid-cols-2 gap-2">
        <label className="text-xs text-ink-2">Brand<Select className="w-full" value={brand} onChange={e => { setBrand(e.target.value); const b = cat.brands.find(x => x.id === e.target.value); if (b) setStyle(b.default_style) }}>
          {cat.brands.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</Select></label>
        <label className="text-xs text-ink-2">Platform<Select className="w-full" value={platform} onChange={e => setPlatform(e.target.value)}>{cat.platforms.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</Select></label>
        <label className="text-xs text-ink-2">Style<Select className="w-full" value={style} onChange={e => setStyle(e.target.value)}>{cat.styles.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</Select></label>
        <label className="text-xs text-ink-2">Short name<Field value={slug} onChange={e => setSlug(e.target.value)} placeholder="e.g. tools_poster" /></label>
      </div>
      <Btn kind="ghost" className="mt-2 w-full" disabled={locked || busy || !slug.trim() || p.dirty} onClick={go}>{p.dirty ? 'Save the poster first' : 'Make reel'}</Btn>
      {made && <p role="status" className="mt-2 rounded-field bg-ok-subtle px-2 py-1.5 text-xs text-ok">Reel created with {made.slides} slide{made.slides > 1 ? 's' : ''}. <a className="underline" href={`#/p/${encodeURIComponent(made.project)}`}>Open the reel</a> to approve its script, set the title page words, then build and render.</p>}
      <Err msg={err} />
    </div>
  )
}
