// M6 step 4: the M5 poster editor rebuilt in React on the M6 tokens.
// All document rules stay in M5 (server side, via /api/creative/*). The browser-side export rules are M5's own,
// imported unchanged: font loading, overflow check, rasterising and PNG parity (browser_acceptance.js), plus M5's
// alignment and resize helpers. Nothing here decides what a valid poster is; it only shows and asks.
import { useCallback, useEffect, useRef, useState } from 'react'
import { comparePng, inspectScene, loadFonts, qualifyEmbedded, raster } from '@m5/visual_poster_tests/browser_acceptance.js'
import { alignPosition, clippedBox } from '@m5/visual_poster_studio/layout.mjs'
import { resizeBox } from '@m5/visual_poster_studio/geometry.mjs'
import { creative, CreativeError, type ApprovedDoc, type ContentLink, type ExportReceipt, type Face, type Layer, type PosterProject, type PosterQA, type PosterRow, type ReelRow, type Scene } from './creative'
import { Btn, Card, Err, Field, MOTION, PageHead, Pill, Select, cx } from './ui'
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
  const frame = useRef<HTMLDivElement>(null); const seq = useRef(0)

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
    setBusy(true); setErr(null); setReceipt(null)
    try { setP(await creative.action(p, action, extra)); setUpgrade(null) }
    catch (e) {
      if (e instanceof CreativeError && e.code === 'upgrade-required') setUpgrade({ action, extra })
      else { setErr(msg(e)); if (e instanceof CreativeError && e.code === 'conflict') creative.view(p.project_id).then(setP).catch(() => {}) }
    } finally { setBusy(false) }
  }, [p])

  if (!p) return err ? <Err msg={err} /> : <p className="text-sm text-ink-3">Opening poster…</p>
  const view = p.view; const layers = p.elements.filter(e => e.view_id === view.id)
  const el = layers.find(e => e.id === sel) ?? null
  const textOf = (e: Layer) => p.content.find(c => c.id === e.content_id)
  const current = !!scene && scene.revision === p.revision && scene.project_id === p.project_id
  const locked = busy || exporting

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

  // ---- export: M5's own handshake and browser checks, unchanged
  const exportDraft = async (withPng: boolean) => {
    setExporting(true); setErr(null); setReceipt(null)
    try {
      if (!current) throw Error('The preview is not current yet.')
      const start = await creative.exportBegin(p)
      const check = await inspectScene(start.scene)
      let png: string | null = null; let parity = false
      if (withPng) {
        const r = await raster(start.scene.svg); parity = await comparePng(r.canvas, r.blob)
        if (!parity) { setPngOk(false); throw Error('PNG disabled: the decoded image did not match the preview exactly.') }
        if (r.blob.size > 8 * 1024 * 1024) throw Error('PNG exceeds 8 MiB.')
        const bytes = new Uint8Array(await r.blob.arrayBuffer()); let s = ''
        for (let i = 0; i < bytes.length; i += 16384) s += String.fromCharCode(...bytes.subarray(i, i + 16384))
        png = btoa(s)
      }
      const saved = await creative.exportFinish({ token: start.token, revision: start.scene.revision, png, qa: { fonts_loaded: check.fonts_loaded, overflow: check.overflow, parity, embedded_fonts: pngOk } })
      if (saved.manifest.svg_sha256 !== start.scene.svg_sha256) throw Error('Saved SVG does not match the preview.')
      setReceipt(saved)
    } catch (e) { setErr(`Export refused: ${msg(e)}`); creative.exportCancel().catch(() => {}) }
    finally { setExporting(false) }
  }

  // Server QA (declared boxes) + measured-ink QA from this browser. With a current preview, the measured safe-area check
  // replaces the box-based one (the box is usually larger than the drawn text).
  const failing = [...(qa?.checks.filter(c => !c.passed && !(c.name === 'safe_area' && current)) ?? []),
    ...(current ? measured.map(m => ({ ...m, passed: false })) : [])]
  const qaPass = !!qa && qa.passed && !overflow.length && !(current && measured.some(m => m.level === 'error'))
  const wordsBlocked = failing.some(c => c.name === 'approved_text')   // M7-A: the server refuses this export too
  return (
    <div data-surface="editor" className="rounded-sheet bg-canvas p-4 text-ink shadow-float">
      {/* toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h1 className="mr-2 truncate text-base font-semibold">{p.name}</h1>
        {p.dirty ? <Pill ok={false}>Unsaved changes</Pill> : <Pill ok>Saved</Pill>}
        <span className="ml-auto" />
        <Btn kind="quiet" disabled={locked || !p.can_undo} onClick={() => act('undo')}>Undo</Btn>
        <Btn kind="quiet" disabled={locked || !p.can_redo} onClick={() => act('redo')}>Redo</Btn>
        <Btn kind="ghost" disabled={locked || !p.dirty} onClick={() => act('save')}>Save</Btn>
        <Btn kind="ghost" disabled={locked || !current || overflow.length > 0 || wordsBlocked} onClick={() => exportDraft(false)}>Export SVG</Btn>
        <Btn disabled={locked || !current || overflow.length > 0 || !pngOk || wordsBlocked} onClick={() => exportDraft(true)}>Export PNG</Btn>
      </div>
      {upgrade && <div role="alert" className="mb-3 rounded-field bg-warn-subtle px-3 py-2 text-sm text-warn">
        This change needs the newer edit-history format (v3). Older M5 Studio versions cannot open this poster afterwards.
        <span className="ml-3 inline-flex gap-2"><Btn kind="ghost" disabled={locked} onClick={() => act(upgrade.action, { ...upgrade.extra, acknowledge_upgrade: true })}>Upgrade and continue</Btn><Btn kind="quiet" onClick={() => setUpgrade(null)}>Cancel</Btn></span></div>}
      {wordsBlocked && <p role="alert" className="mb-3 rounded-field bg-bad-subtle px-3 py-2 text-sm text-bad">Export blocked: approved reel words on this poster no longer match their approval. Undo the edit or insert the approved line again. If the new wording is intended, approve it in that reel first, then insert it from there.</p>}
      <Err msg={err} />
      {receipt && <p role="status" className="mb-3 rounded-field bg-ok-subtle px-3 py-2 text-sm text-ok">Draft exported: {receipt.directory}{receipt.manifest.png_sha256 ? ' (SVG and PNG)' : ' (SVG)'}</p>}

      <div className="grid gap-4 lg:grid-cols-[15rem_minmax(0,1fr)_18rem]">
        {/* layers */}
        <aside aria-label="Layers" className="space-y-3 rounded-box bg-surface p-3">
          <h2 className="text-xs font-semibold tracking-wide text-ink-3">LAYERS</h2>
          <ol className="space-y-1">
            {[...layers].reverse().map(l => <li key={l.id}><button onClick={() => setSel(l.id)} aria-pressed={sel === l.id} aria-label={l.type === 'text' ? `Text layer: ${textOf(l)?.text.split('\n')[0] || 'empty'}` : `${l.style.shape === 'ellipse' ? 'Ellipse' : 'Rectangle'} layer`}
              className={cx('w-full truncate rounded-field px-2 py-1.5 text-left text-sm', MOTION, sel === l.id ? 'bg-act-subtle text-link' : 'hover:bg-raised')}>
              {links.some(k => k.element_id === l.id) && <span title="Approved words from a reel" className={cx('mr-1 text-xs font-semibold', links.find(k => k.element_id === l.id)?.ok ? 'text-ok' : 'text-bad')}>✓A</span>}
              {l.type === 'text' ? <span className={textOf(l)?.language === 'te' ? 'te' : undefined}>{textOf(l)?.text.split('\n')[0] || '(empty text)'}</span> : <span className="text-ink-2">{l.style.shape === 'ellipse' ? 'Ellipse' : 'Rectangle'}</span>}
            </button></li>)}
          </ol>
          <div className="flex gap-1"><Btn kind="quiet" disabled={locked || !el} onClick={() => reorder(1)} title="Bring forward">Forward</Btn><Btn kind="quiet" disabled={locked || !el} onClick={() => reorder(-1)} title="Send backward">Backward</Btn></div>
          <div className="grid grid-cols-2 gap-1 border-t border-line pt-3 [&>button]:px-2 [&>button]:text-xs">
            <Btn kind="ghost" disabled={locked || p.remaining_text_slots.te < 1 || layers.length >= p.element_limit} onClick={() => act('add_text', { language: 'te' })}>+ Telugu</Btn>
            <Btn kind="ghost" disabled={locked || p.remaining_text_slots.en < 1 || layers.length >= p.element_limit} onClick={() => act('add_text', { language: 'en' })}>+ English</Btn>
            <Btn kind="ghost" disabled={locked || layers.length >= p.element_limit} onClick={() => act('add_shape', { shape: 'rectangle' })}>+ Rectangle</Btn>
            <Btn kind="ghost" disabled={locked || layers.length >= p.element_limit} onClick={() => act('add_shape', { shape: 'ellipse' })}>+ Ellipse</Btn>
          </div>
        </aside>

        {/* poster */}
        <section aria-label="Poster" className="min-w-0">
          <div ref={frame} onPointerMove={moveG} onPointerUp={endG} onPointerCancel={() => setGesture(null)} onPointerDown={() => setSel(null)}
            className="relative mx-auto w-full max-w-[30rem] select-none overflow-hidden rounded-field ring-1 ring-line"
            style={{ aspectRatio: `${view.width} / ${view.height}`, backgroundImage: 'conic-gradient(var(--color-bg-raised) 25%, var(--color-bg-surface) 0 50%, var(--color-bg-raised) 0 75%, var(--color-bg-surface) 0)', backgroundSize: '24px 24px' }}>
            {preview && <img src={preview} alt="Poster preview" draggable={false} className={cx('absolute inset-0 h-full w-full', !current && 'opacity-60')} />}
            <div aria-hidden className="pointer-events-none absolute border border-dashed border-line-strong/60"
              style={{ left: `${SAFE_MARGIN / view.width * 100}%`, top: `${SAFE_MARGIN / view.height * 100}%`, right: `${SAFE_MARGIN / view.width * 100}%`, bottom: `${SAFE_MARGIN / view.height * 100}%` }} />
            {layers.map(l => {
              const b = clippedBox(ghost(l), view); if (!b) return null
              const on = sel === l.id
              return <div key={l.id} onPointerDown={e => begin(e, l, 'move')} title={l.type === 'text' ? 'Text layer' : 'Shape layer'}
                className={cx('absolute cursor-move', on ? 'outline-2 outline-focus' : 'hover:outline hover:outline-1 hover:outline-focus/60', overflow.includes(l.id) && 'outline-2 outline-bad')}
                style={{ left: `${b.left}%`, top: `${b.top}%`, width: `${b.width}%`, height: `${b.height}%` }}>
                {on && <span onPointerDown={e => begin(e, l, 'resize')} title="Resize" className="absolute -right-1.5 -bottom-1.5 h-3 w-3 cursor-nwse-resize rounded-chip bg-focus" />}
              </div>
            })}
          </div>
          <p className="mt-2 text-center text-xs text-ink-3">{previewErr ? <span className="text-bad">{previewErr}</span>
            : current ? `Preview current · revision ${p.revision} · dashed line = ${SAFE_MARGIN} px safe area` : 'Updating preview…'}</p>
          <p className="text-center text-xs text-ink-3">{fontNote}</p>
        </section>

        {/* inspector + QA */}
        <aside aria-label="Inspector" className="space-y-4">
          <div className="rounded-box bg-surface p-3">
            <h2 className="mb-2 text-xs font-semibold tracking-wide text-ink-3">INSPECTOR</h2>
            {!el ? <p className="text-sm text-ink-3">Select a layer on the poster or in the list.</p>
              : <Inspector key={`${el.id}-${p.revision}`} p={p} el={el} text={textOf(el)} link={links.find(k => k.element_id === el.id)} locked={locked} act={act} />}
          </div>
          <div className="rounded-box bg-surface p-3">
            <div className="mb-2 flex items-center gap-2"><h2 className="text-xs font-semibold tracking-wide text-ink-3">POSTER QA</h2>
              {qa && qa.revision === p.revision && <Pill ok={qaPass}>{qaPass ? 'PASS' : 'FAIL'}</Pill>}</div>
            {overflow.length > 0 && <p className="mb-2 text-xs text-bad">Text overflows its box or lines overlap ({overflow.length} layer{overflow.length > 1 ? 's' : ''}). Export is blocked until fixed.</p>}
            {!qa ? <p className="text-xs text-ink-3">Checking…</p> : !failing.length ? <p className="text-xs text-ok">All checks pass.</p>
              : <ul className="space-y-1">{failing.map((c, i) => <li key={i}><button onClick={() => setSel(c.element_id)} className="w-full rounded-field px-1 py-0.5 text-left text-xs hover:bg-raised">
                <span className={c.level === 'error' ? 'font-semibold text-bad' : 'font-semibold text-warn'}>{c.level === 'error' ? 'Error' : 'Warning'} · {c.name.replace(/_/g, ' ')}</span>
                <span className="block text-ink-2">{c.detail}</span></button></li>)}</ul>}
          </div>
          <ApprovedPanel p={p} locked={locked} onInserted={(np, id) => { setP(np); setSel(id) }} />
          <MakeReelPanel p={p} locked={locked} />
        </aside>
      </div>
    </div>
  )
}

// ------------------------------------------------------------------ inspector for one layer
function Inspector({ p, el, text, link, locked, act }: { p: PosterProject; el: Layer; text?: { text: string; language: string }; link?: ContentLink; locked: boolean; act: (a: string, x?: Record<string, unknown>) => Promise<void> }) {
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
          <textarea value={draft} onChange={e => setDraft(e.target.value)} rows={4} onCompositionStart={() => setComposing(true)} onCompositionEnd={() => setComposing(false)}
            className={cx('mt-1 w-full rounded-field border border-line-strong bg-raised p-2 text-sm text-ink', text?.language === 'te' && 'te')} />
        </label>
        <div className="flex items-center gap-2"><Btn disabled={locked || composing || draft === text?.text || !draft.trim()} onClick={() => act('edit_text', { element_id: el.id, text: draft })}>Apply text</Btn>
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
      <Btn kind="danger" className="w-full" disabled={locked} onClick={() => { if (window.confirm('Remove this layer? You can undo it.')) act('remove', { element_id: el.id }) }}>Remove layer</Btn>
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
function MakeReelPanel({ p, locked }: { p: PosterProject; locked: boolean }) {
  const [cat, setCat] = useState<Catalog | null>(null); const [brand, setBrand] = useState(''); const [platform, setPlatform] = useState('instagram')
  const [style, setStyle] = useState(''); const [slug, setSlug] = useState(''); const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null); const [made, setMade] = useState<{ project: string; slides: number } | null>(null)
  useEffect(() => { api.catalog().then(c => { setCat(c); const b = c.brands[0]; if (b) { setBrand(b.id); setStyle(b.default_style) } }).catch(e => setErr(msg(e))) }, [])
  const go = async () => {
    setBusy(true); setErr(null); setMade(null)
    try { const r = await creative.toReel(p, { brand, platform, style, slug }); setMade(r) } catch (e) { setErr(msg(e)) } finally { setBusy(false) }
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
      {made && <p role="status" className="mt-2 rounded-field bg-ok-subtle px-2 py-1.5 text-xs text-ok">Reel created with {made.slides} slide{made.slides > 1 ? 's' : ''}. <a className="underline" href={`#/p/${encodeURIComponent(made.project)}`}>Open it in Reels</a> to approve the script, add title words, build and render.</p>}
      <Err msg={err} />
    </div>
  )
}
