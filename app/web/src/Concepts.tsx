// M7-B B2: three concepts from the brief, compared side by side, one opened in the editor as an unapproved draft.
// The concepts come from M5's deterministic Creative Director (layout rules, no AI model: Codex rated AI integration NO-GO).
import { useEffect, useRef, useState } from 'react'
import { loadFonts } from '@m5/visual_poster_tests/browser_acceptance.js'
import { conceptSvg, nextConcept } from './concepts-logic'
import { creative, CreativeError, type Binding, type ConceptBundle, type ConceptRequest, type PosterProject } from './creative'
import { Btn, Card, MOTION, Notice, PageHead, cx } from './ui'
import { report } from './tasks'
import { TaskSteps } from './TaskTracker'
import { useTask } from './use-task'

const msg = (e: unknown) => (e as Error).message
// Proposed wording for the owner's review (M7-B decision point): what made these concepts, and that nothing is approved yet.
export const CONCEPTS_ORIGIN = 'These three concepts are arranged by layout rules on this Mac, from your brief. No AI model is used, and nothing is checked or approved for you.'

export function Concepts({ id, onOpen }: { id: string; onOpen: (posterId: string) => void }) {
  const [p, setP] = useState<PosterProject | null>(null); const [err, setErr] = useState<string | null>(null)
  const [briefOk, setBriefOk] = useState(false); const [seed, setSeed] = useState(7); const [busy, setBusy] = useState(false)
  const [bundle, setBundle] = useState<ConceptBundle | null>(null); const [req, setReq] = useState<ConceptRequest | null>(null)
  const [chosen, setChosen] = useState(0); const [rulesOk, setRulesOk] = useState(false); const [fonts, setFonts] = useState(false)
  const cards = useRef<(HTMLDivElement | null)[]>([]); const [tick, setTick] = useState(0)
  const tracked = useTask({ poster: id }, tick); const task = tracked.task && !tracked.task.cancelled ? tracked.task : null
  useEffect(() => { creative.view(id).then(setP).catch(e => setErr(msg(e))) }, [id])
  useEffect(() => { creative.fonts().then(f => f.fonts && loadFonts(f.fonts)).then(() => setFonts(true)).catch(() => setFonts(true)) }, [])

  if (!p) return err ? <Notice tone="error">{err}</Notice> : <p className="text-sm text-ink-3">Loading…</p>
  const b = p.binding as Binding | null
  if (!b) return <Notice tone="warning">This poster was not started from a brief, so concepts are not available for it. Start a new one in Create.</Notice>
  const brief = b.record.brief, brand = b.record.brand?.record.payload
  const generate = async (s: number) => {
    setBusy(true); setErr(null); setRulesOk(false)
    const r: ConceptRequest = { project_id: p.project_id, expected_revision: p.revision, expected_binding: b.hash, expected_head: b.published_head, seed: s, acknowledge_brief: true }
    await report(task, 'concepts', 'running')
    try { const made = await creative.concepts(r); setBundle(made); setReq(r); setSeed(s); setChosen(0); await report(task, 'concepts', 'done', { detail: `${made.concepts.length} concepts by layout rules (variation ${s})` }) }
    catch (e) { await report(task, 'concepts', 'failed', { error: msg(e) }); setErr(msg(e)) } finally { setBusy(false); setTick(t => t + 1) }
  }
  const open = async () => {
    if (!bundle || !req) return
    setBusy(true); setErr(null)
    await report(task, 'choose', 'done', { detail: `You chose "${bundle.concepts[chosen].name}"` }); await report(task, 'poster', 'running')
    try { const made = (await creative.chooseConcept(req, bundle, bundle.concepts[chosen].id)).project.project_id; await report(task, 'poster', 'done', { poster: made, detail: 'Opened as an unapproved draft' }); onOpen(made) }
    catch (e) { await report(task, 'poster', 'failed', { error: msg(e) }); setTick(t => t + 1); setErr(e instanceof CreativeError && /already exists/.test(e.message) ? `${e.message} Try other variations to get new concepts.` : msg(e)) }
    finally { setBusy(false) }
  }
  const key = (e: React.KeyboardEvent, i: number) => {
    const j = nextConcept(i, e.key, bundle?.concepts.length ?? 0)
    if (j !== null) { e.preventDefault(); setChosen(j); cards.current[j]?.focus() }
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); setChosen(i) }
  }
  return (
    <div className="space-y-6">
      <PageHead title="Concepts" sub={`${p.name}: compare three layouts and open one in the editor.`} />
      <Card title="Your brief" right={brand ? <span className="text-xs text-ink-2">Brand kit: {brand.name}</span> : <span className="text-xs text-ink-3">No brand kit</span>}>
        <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[8rem_1fr]">
          {([['Topic', brief.topic], ['Purpose', brief.purpose], ['Audience', brief.audience], ['Instructions', brief.instructions]] as const).map(([k, v]) => <div key={k} className="contents">
            <dt className="text-ink-3">{k}</dt><dd className={/[ఀ-౿]/.test(v) ? 'te' : undefined}>{v || '—'}</dd></div>)}
        </dl>
        <label className="mt-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={briefOk} onChange={e => setBriefOk(e.target.checked)} />I reviewed this brief</label>
        <div className="mt-3 flex flex-wrap gap-2">
          <Btn busy={busy && !bundle} disabled={!briefOk || busy} onClick={() => generate(seed)}>{bundle ? 'Make concepts again' : 'Make three concepts'}</Btn>
          {bundle && <Btn kind="ghost" disabled={!briefOk || busy} onClick={() => generate(seed + 1)}>Try other variations</Btn>}
        </div>
      </Card>

      {task && <section aria-label="Progress" className="rounded-box border border-line bg-raised p-5 shadow-soft"><TaskSteps task={task} onChange={tracked.setTask} /></section>}
      <Notice tone="info">{CONCEPTS_ORIGIN}</Notice>
      {err && <Notice tone="error">{err}</Notice>}

      {bundle && <>
        <div role="radiogroup" aria-label="Concepts" className="grid gap-4 md:grid-cols-3">
          {bundle.concepts.map((c, i) => <div key={c.id} ref={el => { cards.current[i] = el }} role="radio" aria-checked={chosen === i} tabIndex={chosen === i ? 0 : -1}
            onClick={() => setChosen(i)} onKeyDown={e => key(e, i)}
            className={cx('cursor-pointer rounded-box border-2 bg-raised p-3', 'transition duration-[var(--motion-base)] ease-[var(--ease-out)]',
              chosen === i ? 'border-act shadow-lift' : 'border-line hover:-translate-y-0.5 hover:shadow-soft motion-reduce:hover:translate-y-0')}>
            <div className="overflow-hidden rounded-field ring-1 ring-line" aria-hidden dangerouslySetInnerHTML={{ __html: fonts ? conceptSvg(c) : '' }} style={{ aspectRatio: '1080 / 1350' }} />
            <div className="mt-3 flex items-center gap-2"><h3 className="font-semibold">{c.name}</h3>{chosen === i && <span className="ml-auto text-xs font-semibold tracking-wide text-link">SELECTED</span>}</div>
            <p className="mt-1 text-sm text-ink-2">{c.rationale}</p>
          </div>)}
        </div>
        <p className="text-xs text-ink-3">Sketches for comparison. The editor shows the exact poster. Use the arrow keys to move between concepts.</p>

        <Card title="Before you open it">
          {bundle.rules.length > 0 && <><h3 className="text-xs font-semibold text-ink-3">BRAND RULES</h3><ul className="mt-1 mb-3 list-disc pl-5 text-sm">{bundle.rules.map((r, i) => <li key={i}>{r}</li>)}</ul></>}
          {bundle.instructions && <p className="mb-3 text-sm"><span className="text-ink-3">Your instructions: </span>{bundle.instructions}</p>}
          <details className="mb-3 text-xs text-ink-2"><summary className={cx('cursor-pointer', MOTION)}>What the concept tool says about its limits ({bundle.warnings.length})</summary>
            <ul className="mt-1 list-disc pl-5">{bundle.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></details>
          <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={rulesOk} onChange={e => setRulesOk(e.target.checked)} />
            <span>I reviewed the rules and instructions. The concept opens as an unapproved draft that I will check and edit.</span></label>
          <Btn className="mt-3" busy={busy} disabled={!rulesOk} onClick={open}>Open “{bundle.concepts[chosen].name}” in the editor</Btn>
        </Card>
      </>}
    </div>
  )
}
