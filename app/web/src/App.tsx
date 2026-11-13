import { useCallback, useEffect, useRef, useState } from 'react'
import { api, fileUrl, type Catalog, type Job, type Project, type ProjectRow } from './api'

import { Btn, Card, Err, Field, MOTION, Notice, PageHead, Pill, Select, TextArea, cx } from './ui'
import { PosterEditor, PostersPage } from './Posters'
import { BrandStudio } from './BrandStudio'
import { DesignReference } from './DesignReference'
import { Create } from './Create'
import { Home } from './Home'
import { CapabilityList } from './CapabilityList'
import { ProjectsPage } from './Projects'
import { ExportsPage } from './ExportsPage'
import { TaskPage, TaskSteps } from './TaskTracker'
import { useTask } from './use-task'
import { Concepts } from './Concepts'

type Start = (b: Parameters<typeof api.job>[1]) => Promise<void>

// ------------------------------------------------------------------ jobs
function useJob(project: string, onFinish: () => void) {
  const [job, setJob] = useState<Job | null>(null); const since = useRef(0); const events = useRef<Job['events']>([])
  useEffect(() => {   // pick up a job that is still running after a page reload
    setJob(null)
    api.jobs(project).then(js => { const j = js.find(x => x.status === 'queued' || x.status === 'running'); if (j) { since.current = 0; events.current = []; setJob(j) } }).catch(() => {})
  }, [project])
  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'failed' || job.status === 'cancelled') return
    const t = setInterval(async () => {
      try {
        const j = await api.jobStatus(job.id, since.current); events.current = [...events.current, ...j.events]; since.current = j.n_events
        setJob({ ...j, events: events.current })
        if (j.status === 'done' || j.status === 'failed' || j.status === 'cancelled') onFinish()
      } catch { /* server restarting */ }
    }, 1000)
    return () => clearInterval(t)
  }, [job, onFinish])
  const start: Start = async b => { since.current = 0; events.current = []; const j = await api.job(project, b); setJob(j) }
  const cancel = async () => { if (job) await api.cancel(job.id).catch(() => {}) }
  return { job, start, cancel, busy: !!job && (job.status === 'queued' || job.status === 'running') }
}
const ACTION_NAMES: Record<string, string> = { plan: 'Transcribe + plan', hook: 'Check own hook', approve: 'Approve plan', narrate: 'Narration', build: 'Build edit', render: 'Render + QA' }
const HINTS: Record<string, string> = {
  TTS_MEMORY_LIMIT: 'The finished sentences are kept. Press "Make narration again" to finish the rest.',
  ASR_MEMORY_LIMIT: 'Speech-to-text was stopped to protect the Mac. Close other large apps and run it again.',
  BUSY_HEAVY_MODEL: 'Another AI model is still running - wait for it, then try again.',
  PLAN_NOT_APPROVED: 'Approve the plan (step 2) first.',
}
function JobPanel({ job, onCancel }: { job: Job | null; onCancel: () => void }) {
  if (!job) return null
  const errs = job.events.filter(e => e.event === 'error'); const warns = job.events.filter(e => e.event === 'warning')
  const last = [...job.events].reverse().find(e => e.event === 'progress' || e.event === 'log' || e.event === 'start')
  return (
    <div className="sticky top-0 z-10 mb-4 rounded-box border border-line bg-raised/95 p-4 shadow-float backdrop-blur">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <strong>{ACTION_NAMES[job.action] ?? job.action}</strong>
        <Pill ok={job.status === 'done' ? true : job.status === 'failed' || job.status === 'cancelled' ? false : null}>{job.status}</Pill>
        {job.seconds != null && <span className="text-ink-3">{job.seconds} s</span>}
        {job.peak_rss_gb != null && <span className="text-ink-3">peak memory {job.peak_rss_gb} GB</span>}
        <span className="ml-auto text-ink-3">{last?.step ? `${last.step}${last.platform ? ' · ' + last.platform : ''}` : ''}</span>
        {(job.status === 'running' || job.status === 'queued') && <Btn kind="ghost" onClick={onCancel}>Cancel</Btn>}
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-chip bg-surface"><div className={cx('h-full transition-all', job.status === 'failed' ? 'bg-bad-solid' : 'bg-act')} style={{ width: `${job.status === 'done' ? 100 : job.pct || 2}%` }} /></div>
      {errs.filter((e, i, a) => a.findIndex(x => x.code === e.code && x.message === e.message) === i).map((e, i) => <Err key={i} msg={`${e.code ?? 'error'}: ${e.message}${e.code && HINTS[e.code] ? ' - ' + HINTS[e.code] : ''}`} />)}
      {warns.length > 0 && <details className="mt-2 text-xs text-warn"><summary>{warns.length} warning(s)</summary>{warns.map((w, i) => <div key={i}>{w.code}: {w.message}</div>)}</details>}
    </div>
  )
}

// ------------------------------------------------------------------ home
function NewProject({ cat, onMade }: { cat: Catalog; onMade: (n: string) => void }) {
  const [brand, setBrand] = useState(cat.brands[0]?.id ?? ''); const b = cat.brands.find(x => x.id === brand)
  const [platform, setPlatform] = useState('instagram'); const [style, setStyle] = useState(b?.default_style ?? cat.styles[0]?.id)
  const [slug, setSlug] = useState(''); const [err, setErr] = useState<string | null>(null)
  const pickBrand = (id: string) => { setBrand(id); const nb = cat.brands.find(x => x.id === id); if (nb) setStyle(nb.default_style) }
  return (
    <Card title="New reel">
      <div className="grid gap-3 sm:grid-cols-4">
        <label className="text-sm">Brand<br /><Select className="w-full" value={brand} onChange={e => pickBrand(e.target.value)}>{cat.brands.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</Select></label>
        <label className="text-sm">Main platform<br /><Select className="w-full" value={platform} onChange={e => setPlatform(e.target.value)}>{cat.platforms.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</Select></label>
        <label className="text-sm">Style<br /><Select className="w-full" value={style} onChange={e => setStyle(e.target.value)}>{cat.styles.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</Select></label>
        <label className="text-sm">Short name<br /><Field value={slug} onChange={e => setSlug(e.target.value)} placeholder="e.g. housing_numbers" /></label>
      </div>
      <Btn className="mt-3" disabled={!slug.trim()} onClick={async () => { setErr(null); try { onMade((await api.create({ brand, platform, style, slug })).name) } catch (e) { setErr((e as Error).message) } }}>Create project</Btn>
      <Err msg={err} />
    </Card>
  )
}

// ------------------------------------------------------------------ project steps
function Inputs({ p, reload }: { p: Project; reload: (x?: Project) => void }) {
  const [err, setErr] = useState<string | null>(null); const [upl, setUpl] = useState<string | null>(null); const [notes, setNotes] = useState(p.notes)
  const up = async (f: File | undefined, kind: 'video' | 'slide' | 'recording') => {
    if (!f) return; setErr(null); setUpl(f.name)
    try { reload(await api.upload(p.name, f, kind)) } catch (e) { setErr((e as Error).message) } finally { setUpl(null) }
  }
  const videos = p.inputs.filter(f => /\.(mov|mp4|m4v|mkv|webm)$/i.test(f)); const slides = p.inputs.filter(f => /^slide_\d+\.png$/.test(f))
  return (
    <div className="space-y-3 text-sm">
      <div className="grid gap-3 sm:grid-cols-3 [&>*]:min-w-0">
        <label className="rounded-field border border-dashed border-line-strong p-3 hover:bg-surface">
          <div className="font-medium">Speaker video</div><div className="text-xs text-ink-3">a person talking → speaker reel through the AI planner</div>
          <input type="file" accept="video/*" className="mt-2 block w-full min-w-0 max-w-full text-xs" onChange={e => up(e.target.files?.[0], 'video')} />
        </label>
        <label className="rounded-field border border-dashed border-line-strong p-3 hover:bg-surface">
          <div className="font-medium">Slide pictures ({slides.length})</div><div className="text-xs text-ink-3">your own pictures, one per sentence, in order</div>
          <input type="file" accept="image/*" multiple className="mt-2 block w-full min-w-0 max-w-full text-xs" onChange={async e => { for (const f of Array.from(e.target.files ?? [])) await up(f, 'slide') }} />
        </label>
        <label className="rounded-field border border-dashed border-line-strong p-3 hover:bg-surface">
          <div className="font-medium">Your narration recording</div><div className="text-xs text-ink-3">your own voice (.wav/.m4a) - never cloned</div>
          <input type="file" accept="audio/*" className="mt-2 block w-full min-w-0 max-w-full text-xs" onChange={e => up(e.target.files?.[0], 'recording')} />
        </label>
      </div>
      {upl && <p className="text-ink-3">Uploading {upl}…</p>}
      {videos.length > 0 && (
        <div className="flex items-center gap-2">Source video:
          <Select value={p.project.video ?? ''} onChange={async e => { try { reload(await api.patch(p.name, { video: e.target.value })) } catch (x) { setErr((x as Error).message) } }}>
            <option value="">(none - slides reel)</option>{videos.map(v => <option key={v} value={`inputs/${v}`}>{v}</option>)}
          </Select>
        </div>
      )}
      <label className="block">Brief / notes<TextArea value={notes} onChange={e => setNotes(e.target.value)} rows={2} className="mt-1" /></label>
      {notes !== p.notes && <Btn kind="ghost" onClick={async () => reload(await api.patch(p.name, { notes }))}>Save notes</Btn>}
      <div className="flex flex-wrap gap-1 text-xs">{p.inputs.filter(f => !['notes.txt', 'urls.txt', 'script.txt'].includes(f) && !f.endsWith('.part')).map(f =>
        <span key={f} className="inline-flex items-center gap-1 rounded-chip bg-surface px-2 py-0.5">{f}<button title="Remove (kept in inputs/.removed)" className="text-ink-3 hover:text-bad"
          onClick={async () => { setErr(null); try { reload(await api.removeInput(p.name, f)) } catch (e) { setErr((e as Error).message) } }}>×</button></span>)}</div>
      {p.project.video && <Framing p={p} reload={reload} />}
      <Err msg={err} />
    </div>
  )
}

function Captions({ p, reload }: { p: Project; reload: (x?: Project) => void }) {
  const [edit, setEdit] = useState<Record<number, string>>({}); const [err, setErr] = useState<string | null>(null)
  const W = p.words ?? []; const n = Object.keys(edit).length; const review = W.filter(w => w.review).length
  return (
    <details className="rounded-field border border-line p-3">
      <summary className="cursor-pointer text-sm font-medium">Captions - the speaker's own words ({W.length}{review ? `, ${review} marked for review` : ''}) - click a word to fix its spelling</summary>
      <p className="mt-2 text-xs text-ink-3">Spelling fixes only - never change what was said. Fixing a word after approval withdraws the approval; approve again before building.</p>
      <div className="te mt-2 flex flex-wrap gap-1 text-base leading-relaxed">
        {W.map(w => edit[w.i] !== undefined
          ? <input key={w.i} autoFocus value={edit[w.i]} onChange={e => setEdit({ ...edit, [w.i]: e.target.value })} className="w-32 rounded-chip border border-act px-1" />
          : <button key={w.i} title={`${w.s.toFixed(1)} s${w.w_asr ? ` · heard: ${w.w_asr}` : ''}`} onClick={() => setEdit({ ...edit, [w.i]: w.w })}
              className={cx('rounded-chip px-1 hover:bg-surface', w.review && 'bg-warn-subtle', w.w_asr && 'underline decoration-act')}>{w.w}</button>)}
      </div>
      {n > 0 && <div className="mt-2 flex gap-2"><Btn onClick={async () => { setErr(null); try { reload(await api.captions(p.name, edit)); setEdit({}) } catch (e) { setErr((e as Error).message) } }}>Save {n} fix(es)</Btn><Btn kind="ghost" onClick={() => setEdit({})}>Cancel</Btn></div>}
      <Err msg={err} />
    </details>
  )
}

function Framing({ p, reload }: { p: Project; reload: (x?: Project) => void }) {
  const [fx, setFx] = useState<number>(p.project.face_x ?? 0.5); const [t, setT] = useState(3); const [src, setSrc] = useState(api.sourceFrame(p.name, 3))
  const saved = Math.abs(fx - (p.project.face_x ?? 0.5)) < 0.001
  return (
    <details className="rounded-field border border-line p-3">
      <summary className="cursor-pointer font-medium">Framing - where the speaker is in the video (the reel crops around this)</summary>
      <div className="mt-2 flex flex-wrap items-start gap-4">
        <div className="relative w-80"><img src={src} className="w-80 rounded-chip" /><div className="absolute top-0 h-full w-0.5 bg-act" style={{ left: `${fx * 100}%` }} /></div>
        <div className="space-y-2 text-xs">
          <label className="block">Speaker position {Math.round(fx * 100)}%<br /><input type="range" min={0} max={1} step={0.01} value={fx} onChange={e => setFx(Number(e.target.value))} className="w-56" /></label>
          <label className="block">Preview at second<br /><span className="mr-2 inline-block w-24 align-middle"><Field type="number" min={0} value={t} onChange={e => setT(Number(e.target.value))} /></span><Btn kind="ghost" onClick={() => setSrc(api.sourceFrame(p.name, t))}>Show</Btn></label>
          <Btn disabled={saved} onClick={async () => reload(await api.patch(p.name, { face_x: fx }))}>{saved ? 'Saved' : 'Save framing'}</Btn>
          <p className="text-ink-3">Takes effect at the next "Build edit".</p>
        </div>
      </div>
    </details>
  )
}

function PlanStep({ p, start, busy, reload }: { p: Project; start: Start; busy: boolean; reload: (x?: Project) => void }) {
  const pl = p.plan; const [choice, setChoice] = useState(pl?.hook_choice ?? 'A'); const [checked, setChecked] = useState(false); const [hook, setHook] = useState(''); const [err, setErr] = useState<string | null>(null)
  const go = (b: Parameters<Start>[0]) => { setErr(null); start(b).catch(e => setErr((e as Error).message)) }
  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Btn disabled={busy || !p.project.video} onClick={() => go({ action: 'plan' })}>{pl ? 'Plan again' : p.transcript ? 'Draft the plan' : 'Transcribe + draft the plan'}</Btn>
        <span className="text-xs text-ink-3">Telugu speech-to-text (≈10 min the first time), then the local Qwen3 planner. Captions stay verbatim.</span>
      </div>
      {pl?.error && <Err msg={pl.error} />}
      {pl && !pl.error && (
        <>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.entries(pl.options).map(([k, o]) => (
              <label key={k} className={cx('cursor-pointer rounded-field border p-3', choice === k ? 'border-act bg-act-subtle' : 'border-line')}>
                <div className="flex items-center gap-2"><input type="radio" checked={choice === k} onChange={() => setChoice(k)} /><strong>Hook {k}</strong>
                  {pl.approved && pl.hook_choice === k && <Pill ok>approved</Pill>}<span className="ml-auto text-xs text-ink-3">{o.source}</span></div>
                <div className="te mt-1 text-base leading-snug">{[o.line1, o.line2, o.line3].filter(Boolean).map((l, i) => <div key={i}>{l}</div>)}</div>
                <div className="te mt-1 text-xs text-ink-2">{(o.headline || []).join(' / ')}</div>
              </label>
            ))}
          </div>
          {pl.cards.length > 0 && <div className="te text-xs text-ink-2">Number cards: {pl.cards.map(c => `${c.number}${c.label ? ' ' + c.label : ''}`).join(' · ')}</div>}
          {pl.problems.length > 0 && <Err msg={'Problems: ' + pl.problems.join('; ')} />}
          {pl.marked.length > 0 && <Notice tone="warning" className="text-xs">❓ To check before approving:<ul className="te list-disc pl-5">{pl.marked.map((m, i) => <li key={i}>{m}</li>)}</ul></Notice>}
          {p.words && <Captions p={p} reload={reload} />}
          <details><summary className="cursor-pointer text-xs text-ink-2">Full plan (beats, captions, every on-screen word)</summary><pre className="te mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded-chip bg-surface p-3 text-xs">{pl.markdown}</pre></details>
          <div className="flex flex-wrap items-center gap-2">
            <Field value={hook} onChange={e => setHook(e.target.value)} aria-label="Your own hook" placeholder="Own hook D:  line1 / line2 / line3 / headline 1 / headline 2" className="te min-w-0 flex-1 sm:min-w-80" />
            <Btn kind="ghost" disabled={busy || !hook.trim()} onClick={() => go({ action: 'hook', hook })}>Add as option D</Btn>
          </div>
          <div className="flex flex-wrap items-center gap-3 border-t border-line pt-3">
            <label className="flex items-center gap-2"><input type="checkbox" checked={checked} onChange={e => setChecked(e.target.checked)} />I read the whole plan and checked every ❓</label>
            <Btn disabled={busy || (pl.marked.length > 0 && !checked)} onClick={() => go({ action: 'approve', choice, checked })}>Approve hook {choice}</Btn>
          </div>
        </>
      )}
      <Err msg={err} />
    </div>
  )
}

const flaggedLine = (l: Project['script'] extends infer S ? S extends { lines: (infer L)[] } ? L : never : never) =>
  l.numbers.some(n => n.check !== 'ok') || /\d/.test(l.say) || !!l.length?.too_long

function NarrationStep({ p, cat, reload, start, busy }: { p: Project; cat: Catalog; reload: (x?: Project) => void; start: Start; busy: boolean }) {
  const P = p.project; const te = (p.language ?? 'te') === 'te'; const [mode, setMode] = useState<string>(P.narration ?? (te ? 'ai' : 'none')); const [voice, setVoice] = useState<string>(P.narrator ?? 'prakash')
  const [style, setStyle] = useState<string>(P.narrator_style ?? 'news'); const [speed, setSpeed] = useState<number>(P.narration_speed ?? 1.0)
  const recs = p.inputs.filter(f => /\.(wav|m4a|mp3)$/i.test(f)); const [file, setFile] = useState<string>(P.narration_file ?? (recs[0] ? `inputs/${recs[0]}` : ''))
  const [text, setText] = useState(p.script ? p.script.lines.map(l => l.text).join('\n') : ''); const [checked, setChecked] = useState(false); const [err, setErr] = useState<string | null>(null)
  const wrap = (f: () => Promise<Project>) => { setErr(null); f().then(reload).catch(e => setErr((e as Error).message)) }
  const sameSettings = P.narration === mode && (mode !== 'ai' || (P.narrator === voice && P.narrator_style === style && Number(P.narration_speed) === speed)) && (mode !== 'recorded' || (P.narrator_style === style && P.narration_file === file))
  const textChanged = !p.script || p.script.lines.map(l => l.text).join('\n') !== text.split('\n').map(s => s.trim()).filter(Boolean).join('\n')
  const spoken = mode !== 'none' && te                  // number readings only matter when a Telugu voice speaks the text
  const flaggedOf = (l: Parameters<typeof flaggedLine>[0]) => spoken ? flaggedLine(l) : !!l.length?.too_long && mode !== 'none'
  const flagged = p.script?.lines.filter(flaggedOf).length ?? 0
  return (
    <div className="space-y-4 text-sm">
      <div className="flex flex-wrap items-end gap-3">
        <label>Narration<br /><Select value={mode} onChange={e => setMode(e.target.value)}>{te && <option value="ai">AI voice (offline)</option>}<option value="recorded">My recording</option><option value="none">None - text + music</option></Select></label>
        {mode === 'ai' && <label>Voice<br /><Select value={voice} onChange={e => setVoice(e.target.value)}>{Object.entries(cat.voices).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select></label>}
        {mode !== 'none' && <label>Style<br /><Select value={style} onChange={e => setStyle(e.target.value)}>{cat.narration_styles.map(s => <option key={s} value={s}>{s[0].toUpperCase() + s.slice(1)}</option>)}</Select></label>}
        {mode === 'ai' && <label>Speed<br /><Select value={speed} onChange={e => setSpeed(Number(e.target.value))}>{cat.speeds.map(s => <option key={s} value={s}>{s.toFixed(2)}×{s === 1 ? ' (default)' : ''}</option>)}</Select></label>}
        {mode === 'recorded' && <label>Recording<br /><Select value={file} onChange={e => setFile(e.target.value)}><option value="">(upload one above)</option>{recs.map(r => <option key={r} value={`inputs/${r}`}>{r}</option>)}</Select></label>}
        <Btn kind={sameSettings ? 'ghost' : 'primary'} disabled={sameSettings || (mode === 'recorded' && !file)} onClick={() => wrap(() => api.narration(p.name, { mode, voice: mode === 'ai' ? voice : undefined, style: mode !== 'none' ? style : undefined, speed: mode === 'ai' ? speed : undefined, file: mode === 'recorded' ? file : undefined }))}>{sameSettings ? 'Saved' : 'Save narration setting'}</Btn>
      </div>
      {mode === 'ai' && <p className="text-xs text-ink-3">A distinct synthetic narrator (never an imitation of a real person). The two-line Telugu AI disclosure is added on screen; switch on the platform's AI label when you upload.</p>}
      <div>
        <div className="mb-1 font-medium">Script - one sentence per line, exactly as it should appear in captions</div>
        <TextArea value={text} onChange={e => setText(e.target.value)} rows={8} aria-label="Narration script" className="te text-base! leading-relaxed!" />
        <Btn kind={textChanged ? 'primary' : 'ghost'} disabled={!text.trim() || !textChanged} onClick={() => wrap(() => api.script(p.name, text))}>{textChanged ? 'Prepare for review' : 'Prepared'}</Btn>
        <span className="ml-2 text-xs text-ink-3">Shows how every number will be spoken. The text is never rewritten; any edit needs a new approval.</span>
      </div>
      {p.script && (
        <div className="rounded-field border border-line p-3">
          <ol className="te space-y-1.5">
            {p.script.lines.map((l, i) => {
              const f = flaggedOf(l)
              return <li key={i} className={cx('rounded-chip px-2 py-1', f && 'bg-warn-subtle')}>
                <div><span className="mr-2 text-xs text-ink-3">{i + 1}.</span>{f && '❓ '}{l.text}</div>
                {spoken && l.say !== l.text && <div className="text-xs text-ink-2">spoken: {l.say}</div>}
                {spoken && l.numbers.filter(n => n.check !== 'ok').map((n, j) => <div key={j} className="text-xs text-warn">❓ {n.text} → {n.say}: {n.why}</div>)}
                {l.length?.too_long && mode !== 'none' && <div className="text-xs text-warn">❓ long sentence (≈{l.length.est_speech_s} s) - consider splitting; nothing is changed automatically</div>}
              </li>
            })}
          </ol>
          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-line pt-3">
            {p.script.approved ? <Pill ok>approved {p.script.approved_hash?.slice(0, 12)}</Pill> : <>
              <label className="flex items-center gap-2"><input type="checkbox" checked={checked} onChange={e => setChecked(e.target.checked)} />I checked the {flagged} ❓ line(s)</label>
              <Btn disabled={flagged > 0 && !checked} onClick={() => wrap(() => api.approveScript(p.name, checked))}>Approve this exact text</Btn></>}
          </div>
        </div>
      )}
      {P.narration && P.narration !== 'none' && p.script?.approved && (
        <div className="space-y-2 rounded-field border border-line p-3">
          <div className="flex flex-wrap items-center gap-3">
            <Btn disabled={busy || p.narration_ready === true} onClick={() => { setErr(null); start({ action: 'narrate' }).catch(e => setErr((e as Error).message)) }}>{p.narration_audio ? 'Make narration again' : 'Make narration'}</Btn>
            {p.narration_ready ? <Pill ok>narration ready</Pill> : p.narration_problem && <span className="text-xs text-ink-2">{p.narration_problem.message}</span>}
          </div>
          {p.narration_audio && <div className="flex flex-wrap items-center gap-3"><audio controls src={fileUrl(p.narration_audio.file) + `?d=${p.narration_audio.duration}`} />
            <span className="text-xs text-ink-3">{p.narration_audio.duration} s{p.narration_audio.memory?.peak_rss_gb ? ` · voice model peak ${p.narration_audio.memory.peak_rss_gb} GB of ${p.narration_audio.memory.limit_gb} GB` : ''}</span></div>}
          {p.narration_check && <div className="text-xs"><div>Speech-to-text check: character error {(p.narration_check.cer_total * 100).toFixed(1)}%</div>
            {p.narration_check.to_check.length > 0 && <Notice tone="warning" className="mt-1">Listen to these sentences:<ul className="te list-disc pl-5">{p.narration_check.to_check.map((x, i) => <li key={i}>{typeof x === 'string' ? x : [x.line, x.text, x.why].filter(v => v != null).join(' · ')}</li>)}</ul></Notice>}</div>}
        </div>
      )}
      <Err msg={err} />
    </div>
  )
}

const titleReady = (p: Project) => ['line1', 'line2', 'line3'].every(k => (p.project.hook?.[k] ?? '').trim())

function TitlePage({ p, reload, wordsFromPlan }: { p: Project; reload: (x?: Project) => void; wordsFromPlan?: boolean }) {
  const hk = p.project.hook ?? {}; const hl: string[] = p.project.title ?? ['', '']
  const [f, setF] = useState({ line1: hk.line1 ?? '', line2: hk.line2 ?? '', line3: hk.line3 ?? '', tag_top: hk.tag_top ?? '', tag_bottom: hk.tag_bottom ?? '', h1: hl[0] ?? '', h2: hl[1] ?? '' })
  const [err, setErr] = useState<string | null>(null)
  const saved = f.line1 === (hk.line1 ?? '') && f.line2 === (hk.line2 ?? '') && f.line3 === (hk.line3 ?? '') && f.tag_top === (hk.tag_top ?? '') && f.tag_bottom === (hk.tag_bottom ?? '') && f.h1 === (hl[0] ?? '') && f.h2 === (hl[1] ?? '')
  const inp = (k: keyof typeof f, ph: string) => <Field value={f[k]} onChange={e => setF({ ...f, [k]: e.target.value })} placeholder={ph} aria-label={ph} className="te text-base!" />
  const up = async (file: File | undefined, kind: 'title_person' | 'title_bg') => { if (!file) return; try { reload(await api.upload(p.name, file, kind)) } catch (e) { setErr((e as Error).message) } }
  return (
    <div className="space-y-3 text-sm">
      {wordsFromPlan ? <p className="te text-xs text-ink-3">The words come from the approved hook: {[hk.line1, hk.line2, hk.line3].filter(Boolean).join(' / ') || '(approve a hook first)'}. Add pictures here.</p> : <>
      <p className="text-xs text-ink-3">Your own words for the 4K cover / first frame, exactly as written (≤4 words per hook line). The headline stays at the top of the framed reel.</p>
      <div className="grid gap-2 sm:grid-cols-3">{inp('line1', 'Hook line 1')}{inp('line2', 'Hook line 2')}{inp('line3', 'Hook line 3 (big)')}</div>
      <div className="grid gap-2 sm:grid-cols-4">{inp('tag_top', 'Sign: top (optional)')}{inp('tag_bottom', 'Sign: bottom')}{inp('h1', 'Headline line 1')}{inp('h2', 'Headline line 2')}</div></>}
      <div className="flex flex-wrap items-center gap-4">
        {!wordsFromPlan && <Btn kind={saved ? 'ghost' : 'primary'} disabled={saved} onClick={async () => { setErr(null); try { reload(await api.title(p.name, { line1: f.line1, line2: f.line2, line3: f.line3, tag_top: f.tag_top, tag_bottom: f.tag_bottom, headline: [f.h1, f.h2] })) } catch (e) { setErr((e as Error).message) } }}>{saved ? 'Saved' : 'Save title page'}</Btn>}
        <label className="text-xs">Person cut-out (PNG, transparent): <input type="file" accept="image/png" className="max-w-full text-xs" onChange={e => up(e.target.files?.[0], 'title_person')} /><span className="text-ink-3"> {p.project.title_person ? 'set' : 'none'}</span></label>
        <label className="text-xs">Background photo: <input type="file" accept="image/*" className="max-w-full text-xs" onChange={e => up(e.target.files?.[0], 'title_bg')} /><span className="text-ink-3"> {p.project.title_bg ? 'set' : 'none'}</span></label>
      </div>
      <Err msg={err} />
    </div>
  )
}

function Exports({ p }: { p: Project }) {
  if (!p.exports.length) return <p className="text-sm text-ink-3">No exports yet.</p>
  return (
    <div className="space-y-6">
      {p.exports.map(g => (
        <div key={g.version}>
          <h3 className="mb-2 text-sm font-semibold">{g.version ? `Version v${g.version}` : "Original export (before versions)"} <span className="font-normal text-ink-3">{g.outputs[0]?.created}</span></h3>
          <div className="grid gap-4 md:grid-cols-3">
            {g.outputs.map(o => (
              <div key={o.file} className="rounded-field border border-line p-3 text-sm">
                <div className="mb-2 flex items-center gap-2"><strong className="capitalize">{o.platform}</strong><Pill ok={o.qa?.passed}>{o.qa ? (o.qa.passed ? 'QA PASS' : 'QA FAIL') : 'no QA'}</Pill><span className="ml-auto text-xs text-ink-3">{o.size_mb} MB</span></div>
                <video controls preload="metadata" src={fileUrl(o.file)} poster={fileUrl(o.cover)} className="aspect-[9/16] w-full rounded-chip bg-media" />
                {o.qa && <div className="mt-2 text-xs">
                  <div>{o.qa.duration?.toFixed(1)} s · {o.qa.loudness} LUFS · peak {o.qa.true_peak} dB</div>
                  <div className="mt-1 flex flex-wrap gap-1">{o.qa.checks.map(c => <Pill key={c.name} ok={c.passed}>{c.name}</Pill>)}</div>
                  {o.qa.warnings.length > 0 && <details className="mt-1 text-warn"><summary>{o.qa.warnings.length} warning(s)</summary><ul className="list-disc pl-4">{o.qa.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></details>}
                </div>}
                <div className="mt-2 flex flex-wrap gap-3 text-xs">
                  <a className="text-link underline" href={fileUrl(o.file)} download>Video</a>
                  {o.cover && <a className="text-link underline" href={fileUrl(o.cover)} target="_blank">4K cover</a>}
                  {o.qa?.contact_sheet && <a className="text-link underline" href={fileUrl(o.qa.contact_sheet)} target="_blank">QA contact sheet</a>}
                  {o.post && <a className="text-link underline" href={fileUrl(o.post)} target="_blank">Post copy</a>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <p className="text-xs text-ink-3">Nothing is published by IDEAFRAME. Review each reel, then upload it yourself{p.project.narration === 'ai' ? " with the platform's AI-generated content label switched on" : ''}.</p>
    </div>
  )
}

function ProjectView({ name, cat }: { name: string; cat: Catalog }) {
  const [p, setP] = useState<Project | null>(null); const [err, setErr] = useState<string | null>(null)
  const reload = useCallback((x?: Project) => { if (x) setP(x); else api.project(name).then(setP).catch(e => setErr((e as Error).message)) }, [name])
  useEffect(() => { setP(null); setErr(null); reload() }, [name, reload])
  const { job, start, cancel, busy } = useJob(name, reload)
  const tracked = useTask({ reel: name }, job ? job.n_events + (job.status === 'running' ? 0 : 1000) : 0)   // the server mirrors engine jobs into the reel's task
  const [pfs, setPfs] = useState<string[] | null>(null)
  if (err) return <Err msg={err} />
  if (!p) return <p className="text-sm text-ink-3">Loading…</p>
  const platforms = pfs ?? cat.brands.find(b => b.id === p.project.brand)?.default_platforms ?? [p.project.platform]
  const speaker = p.mode === 'speaker'
  const st = (doneIf: boolean, nextIf: boolean): 'done' | 'next' | 'todo' => doneIf ? 'done' : nextIf ? 'next' : 'todo'
  const planDone = !!p.plan?.approved; const narrDone = !!p.script?.approved && (p.project.narration === 'none' || p.narration_ready === true)
  const prepDone = speaker ? planDone : narrDone
  const run = (b: Parameters<Start>[0]) => { setErr(null); start(b).catch(e => setErr((e as Error).message)) }
  if (p.locked) return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{p.name}</h1>
      <Notice tone="info" title="Locked baseline (reel_002).">Read-only in the app. It is the reference that every engine change is checked against.</Notice>
      <Card title="Exports"><Exports p={p} /></Card>
    </div>
  )
  return (
    <div className="space-y-4">
      <JobPanel job={job} onCancel={cancel} />
      {tracked.task && <section aria-label="Progress of this reel" className="rounded-box border border-line bg-raised p-5 shadow-soft"><TaskSteps task={tracked.task} onChange={tracked.setTask} /></section>}
      <div>
        <div className="flex items-center gap-3"><h1 className="text-xl font-semibold">{p.name}</h1>
          <Btn kind="ghost" className="ml-auto" onClick={async () => reload(await api.patch(p.name, { archived: !p.archived }))}>{p.archived ? 'Restore from archive' : 'Archive'}</Btn></div>
        <div className="mt-1 flex flex-wrap gap-2 text-xs"><Pill>{p.project.brand}</Pill><Pill>{p.project.style}</Pill><Pill>{speaker ? 'speaker reel' : 'slides reel'}</Pill>{p.project.status === 'demo' && <Pill ok={false}>demo approvals - not for publishing</Pill>}</div>
        <p className="mt-2 rounded-field border border-line bg-raised px-3 py-2 text-xs text-ink-2"><strong>Next:</strong> {p.next}</p>
      </div>
      <Card step={1} title="Inputs" state={st(speaker ? !!p.project.video : !!p.script, false)}><Inputs p={p} reload={reload} /></Card>
      {speaker
        ? <>
          <Card step={2} title="AI plan → your approval" state={st(planDone, !planDone)}><PlanStep key={p.plan?.hook_choice ?? 'none'} p={p} start={start} busy={busy} reload={reload} /></Card>
          <Card title="Title page pictures (cover)" state={p.project.title_person || p.project.title_bg ? 'done' : 'todo'}><TitlePage p={p} reload={reload} wordsFromPlan /></Card>
        </>
        : <>
          <Card step={2} title="Narration + script → your approval" state={st(narrDone, !narrDone)}><NarrationStep key={`${p.project.narration ?? 'x'}-${p.script?.approved_hash ?? ''}`} p={p} cat={cat} reload={reload} start={start} busy={busy} /></Card>
          <Card title="Title page (cover + headline)" state={titleReady(p) ? 'done' : narrDone ? 'next' : 'todo'}><TitlePage p={p} reload={reload} /></Card>
        </>}
      <Card step={3} title="Build the edit (captions, graphics, music)" state={st(!!p.edit && prepDone, prepDone && !p.edit)}
        right={<Btn disabled={busy || !prepDone || (!speaker && !titleReady(p))} onClick={() => run({ action: 'build' })}>{p.edit ? 'Build again' : 'Build edit'}</Btn>}>
        {p.edit ? <div className="flex flex-wrap gap-4 text-sm"><video controls preload="metadata" src={fileUrl(p.edit) + `?t=${p.edit_layout?.duration}`} className="h-72 rounded-chip bg-media" />
          <div className="text-xs text-ink-2"><div>{p.edit_layout?.kind}</div><div>{p.edit_layout?.duration} s · {(p.edit_layout?.edit_size ?? []).join('×')}</div>{p.edit_layout?.slides && <div>{p.edit_layout.slides} slides</div>}<div>captions: {p.edit_layout?.captions_words ? `${p.edit_layout.captions_words} words (speaker's own)` : p.edit_layout?.captions ? 'approved script text' : 'none'}</div></div></div>
          : <p className="text-sm text-ink-3">Uses approved material only: {speaker ? 'plan beats in source order, silences cut, verbatim captions, approved number cards' : 'one slide per approved sentence, captions = approved text'}.</p>}
      </Card>
      <Card step={4} title="Render, QA and platform exports" state={st(p.exports.length > 0 && !!p.edit, !!p.edit && !p.exports.length)}
        right={<div className="flex flex-wrap items-center gap-3 text-sm">{cat.platforms.map(x => <label key={x.id} className="flex items-center gap-1"><input type="checkbox" checked={platforms.includes(x.id)} onChange={e => setPfs(e.target.checked ? [...platforms, x.id] : platforms.filter(y => y !== x.id))} />{x.name}</label>)}
          <Btn disabled={busy || !p.edit || !platforms.length} onClick={() => run({ action: 'render', platforms })}>Render</Btn></div>}>
        <Exports p={p} />
      </Card>
    </div>
  )
}

function SystemCheck() {
  const [c, setC] = useState<Record<string, any> | null>(null); const [err, setErr] = useState<string | null>(null)
  const run = () => { setErr(null); setC(null); api.check().then(setC).catch(e => setErr((e as Error).message)) }
  useEffect(run, [])
  const tools = c?.tools ?? {}; const pk = c?.python_packages ?? {}
  return (
    <Card title="System check" right={<Btn kind="ghost" onClick={run}>Check again</Btn>}>
      {!c ? <p className="text-sm text-ink-3">{err ?? 'Checking…'}</p> : (
        <div className="space-y-2 text-xs">
          <div className="flex flex-wrap gap-1">{Object.entries(tools).map(([k, v]) => <Pill key={k} ok={!!v}>{k}</Pill>)}{Object.entries(pk).map(([k, v]) => <Pill key={k} ok={!!v}>{k}</Pill>)}
            <Pill ok={!!c.telugu_layout}>Telugu text layout</Pill><Pill ok={!!c.asr_env}>speech-to-text env</Pill><Pill ok={!!c.tts_env}>voice env</Pill>
            {Object.entries(c.providers ?? {}).map(([k, v]) => <Pill key={k} ok={!!v}>planner: {k}</Pill>)}<Pill>{c.memory_gb} GB memory</Pill></div>
          {(c.settings ?? []).length > 0 && <ul className="list-disc pl-4 text-warn">{c.settings.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>}
          {c.providers && !c.providers.local && <p className="text-warn">The local planner (Ollama) is not running - start the Ollama app before planning a speaker reel.</p>}
        </div>)}
    </Card>
  )
}

// ------------------------------------------------------------------ pages
function ProjectList({ rows, onOpen }: { rows: ProjectRow[]; onOpen: (n: string) => void }) {
  if (!rows.length) return <p className="text-sm text-ink-3">No projects yet.</p>
  return (
    <ul className="divide-y divide-line overflow-hidden rounded-box border border-line bg-raised">
      {rows.map(r => (
        <li key={r.name}>
          <button onClick={() => onOpen(r.name)} className={cx('flex w-full flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left hover:bg-act-subtle', MOTION)}>
            <span className="w-full min-w-0 truncate font-medium sm:w-auto sm:flex-1">{r.name}</span>
            <span className="text-xs text-ink-3">{r.brand} · {r.mode === 'speaker' ? 'speaker reel' : 'slides reel'} · {r.exports} export(s){r.archived ? ' · archived' : ''}</span>
          </button>
        </li>
      ))}
    </ul>
  )
}

// ------------------------------------------------------------------ shell
// Routes live in the address bar: #/ (home), #/create, #/concepts/<id>, #/projects (posters and reels), #/exports, #/posters, #/brands, #/settings,
// #/design, #/p/<reel>, #/poster/<id>.
// An old Reel Studio link (#<project>) still opens that project.
type Page = 'home' | 'create' | 'projects' | 'posters' | 'brands' | 'exports' | 'settings' | 'design'
type Route = { page: Page } | { page: 'project'; name: string } | { page: 'poster'; id: string } | { page: 'concepts'; id: string } | { page: 'task'; id: string }
const readRoute = (): Route => {
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ''))
  if (!h) return { page: 'home' }
  if (h === 'create' || h === 'projects' || h === 'posters' || h === 'brands' || h === 'exports' || h === 'settings' || h === 'design') return { page: h }
  if (h.startsWith('poster/')) return { page: 'poster', id: h.slice(7) }
  if (h.startsWith('concepts/')) return { page: 'concepts', id: h.slice(9) }
  if (h.startsWith('task/')) return { page: 'task', id: h.slice(5) }
  return { page: 'project', name: h.startsWith('p/') ? h.slice(2) : h }
}
const hrefOf = (r: Route) => r.page === 'project' ? `#/p/${encodeURIComponent(r.name)}` : r.page === 'poster' ? `#/poster/${encodeURIComponent(r.id)}` : r.page === 'concepts' ? `#/concepts/${encodeURIComponent(r.id)}` : r.page === 'task' ? `#/task/${encodeURIComponent(r.id)}` : r.page === 'home' ? '#/' : `#/${r.page}`

const NAV: { page: Page; label: string }[] = [
  { page: 'home', label: 'Home' }, { page: 'create', label: 'Advanced Create' }, { page: 'projects', label: 'Projects' }, { page: 'brands', label: 'Brand Studio' }, { page: 'exports', label: 'Exports' }, { page: 'settings', label: 'Settings' }]
const TITLE: Record<Route['page'], string> = { home: 'Home', create: 'Advanced Create', projects: 'Projects', posters: 'Posters', brands: 'Brand Studio', exports: 'Exports', settings: 'Settings', design: 'Component reference', project: 'Reel', poster: 'Poster editor', concepts: 'Concepts', task: 'Progress' }

export default function App() {
  const [cat, setCat] = useState<Catalog | null>(null); const [rows, setRows] = useState<ProjectRow[]>([])
  const [route, setRoute] = useState<Route>(readRoute); const [err, setErr] = useState<string | null>(null)
  const go = (r: Route) => { location.hash = hrefOf(r) }
  useEffect(() => { api.catalog().then(setCat).catch(e => setErr((e as Error).message)) }, [])
  useEffect(() => { if (route.page === 'home') api.projects(false).then(setRows).catch(e => setErr((e as Error).message)) }, [route])
  useEffect(() => { document.title = `${TITLE[route.page]} · IDEAFRAME` }, [route.page])
  useEffect(() => {   // links / back button: follow the address bar
    const on = () => setRoute(readRoute())
    window.addEventListener('hashchange', on); return () => window.removeEventListener('hashchange', on)
  }, [])
  const section = route.page === 'project' || route.page === 'poster' || route.page === 'posters' || route.page === 'concepts' || route.page === 'task' ? 'projects' : route.page === 'design' ? 'settings' : route.page
  const recent = rows.filter(r => !r.archived).slice(0, 5)
  return (
    <div className="flex min-h-screen flex-col bg-surface text-ink md:flex-row">
      <a href="#main" onClick={e => { e.preventDefault(); document.getElementById('main')?.focus() }} className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-10 focus:rounded-btn focus:bg-raised focus:px-3 focus:py-2 focus:text-sm focus:text-link focus:shadow-lift">Skip to content</a>
      <aside className="flex shrink-0 flex-col border-b border-line bg-raised md:sticky md:top-0 md:h-screen md:w-60 md:border-r md:border-b-0">
        {/* Text wordmark only: the approved logo goes here once its vector master exists (Bible G1). */}
        <a href="#/" className="block px-5 pt-5 pb-3 md:pt-6 md:pb-5">
          <div className="font-head text-lg font-semibold tracking-[0.04em] text-ink">IDEAFRAME</div>
          <div className="mt-0.5 text-[length:var(--text-micro)] font-medium tracking-[0.24em] text-ink-3">BY AINRICH</div>
        </a>
        <nav aria-label="Main" className="flex flex-wrap gap-1 px-3 pb-3 md:block md:flex-1 md:space-y-0.5 md:pb-0">
          {NAV.map(n => (
            <a key={n.page} href={hrefOf({ page: n.page })} aria-current={section === n.page ? 'page' : undefined}
              className={cx('block rounded-field px-3 py-2 text-sm font-medium', MOTION, section === n.page ? 'bg-act-subtle text-link' : 'text-ink-2 hover:bg-surface hover:text-ink')}>{n.label}</a>
          ))}
        </nav>
        <p className="hidden border-t border-line px-5 py-4 md:block text-xs text-ink-3">Works on this Mac. Nothing is published.</p>
      </aside>
      <main id="main" tabIndex={-1} className="min-w-0 flex-1 px-4 py-6 outline-none! md:px-8 md:py-8">
        <div className={cx('mx-auto', route.page === 'poster' ? 'max-w-[104rem]' : 'max-w-5xl')}>
          <Err msg={err} />
          {!cat ? <p className="text-sm text-ink-3">Connecting to the local server…</p>
            : route.page === 'poster' ? <PosterEditor id={route.id} />
            : route.page === 'task' ? <TaskPage id={route.id} />
            : route.page === 'posters' ? <PostersPage onOpen={id => go({ page: 'poster', id })} />
            : route.page === 'create' ? <Create onConcepts={id => go({ page: 'concepts', id })} reelForm={<NewProject cat={cat} onMade={n => go({ page: 'project', name: n })} />} />
            : route.page === 'concepts' ? <Concepts id={route.id} onOpen={id => go({ page: 'poster', id })} />
            : route.page === 'brands' ? <BrandStudio />
            : route.page === 'design' ? <DesignReference />
            : route.page === 'project' ? <>
              <a href="#/projects" className="mb-4 inline-block text-sm text-link hover:underline">← Projects</a>
              <ProjectView name={route.name} cat={cat} />
            </>
            : route.page === 'projects' ? <ProjectsPage />
            : route.page === 'exports' ? <ExportsPage />
            : route.page === 'settings' ? <div className="space-y-4">
              <PageHead title="Settings" sub="Local tools, models and planner status." />
              <SystemCheck />
              <Card title="Design" right={<a href="#/design" className="text-sm text-link hover:underline">Component reference</a>}>
                <p className="text-sm text-ink-2">Every shared button, field, status, dialog and notice, in the IDEAFRAME tokens.</p>
              </Card>
              <Card title="Capabilities and providers">
                <p className="mb-2 text-sm text-ink-2">What works on this Mac right now, with each answer shown separately. A model that works for reels is not thereby qualified for posters.</p>
                <div className="text-sm"><CapabilityList detailed /></div>
              </Card>
            </div>
            : <div className="space-y-6">
              <Home onConcepts={id => go({ page: 'concepts', id })} reelForm={<NewProject cat={cat} onMade={n => go({ page: 'project', name: n })} />} />
              <section>
                <div className="mb-2 flex items-baseline gap-3"><h2 className="text-base font-semibold">Recent reels</h2><a href="#/projects" className="text-sm text-link hover:underline">All projects</a></div>
                <ProjectList rows={recent} onOpen={n => go({ page: 'project', name: n })} />
              </section>
            </div>}
        </div>
      </main>
    </div>
  )
}
