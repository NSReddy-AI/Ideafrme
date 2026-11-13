// M7-B B4C-2: shows a task's real steps. No timers pretend to work: the list is whatever the server recorded, asked for
// again while something is running. A step shows a percentage only when the engine reported one.
import { useState } from 'react'
import { STEP_LABEL, STEP_SYMBOL, TASK_LABEL, active, current, summary, tasks, whereTo, type StepStatus, type Task } from './tasks'
import { useTask } from './use-task'
import { Btn, MOTION, Notice, Pill, Spinner, cx } from './ui'

const TONE: Record<StepStatus, string> = { pending: 'text-ink-3', running: 'text-link', waiting: 'text-warn', done: 'text-ok', failed: 'text-bad', cancelled: 'text-ink-3', skipped: 'text-ink-3' }
const pillOk = (t: Task) => (t.status === 'completed' ? true : t.status === 'failed' ? false : null)

function Actions({ task, onChange }: { task: Task; onChange: (t: Task) => void }) {
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const run = async (fn: () => Promise<Task>) => { setBusy(true); setErr(null); try { onChange(await fn()) } catch (e) { setErr((e as Error).message) } finally { setBusy(false) } }
  const failed = task.steps.find(s => s.status === 'failed')
  const canCancel = task.status !== 'completed' && task.status !== 'cancelled'
  if (!canCancel && !failed) return null
  return <div className="mt-3">
    <div className="flex flex-wrap gap-2">
      {failed && failed.retry && !task.cancelled && <Btn kind="ghost" busy={busy} onClick={() => run(() => tasks.retry(task.id))}>{failed.retry === 'job' ? 'Run this step again' : 'Allow another try'}</Btn>}
      {canCancel && <Btn kind="quiet" disabled={busy} onClick={() => run(() => tasks.cancel(task.id))}>{active(task) ? 'Cancel' : 'Stop tracking this'}</Btn>}
    </div>
    {failed && !failed.retry && <p className="mt-2 text-xs text-ink-3">This step is yours to do again in its own screen. It is never repeated automatically.</p>}
    {err && <Notice tone="error" className="mt-2">{err}</Notice>}
  </div>
}

/** The full step list: used on the progress page, on Concepts and on a reel. */
export function TaskSteps({ task, onChange, heading = true }: { task: Task; onChange: (t: Task) => void; heading?: boolean }) {
  const now = current(task); const go = whereTo(task, now)
  return (
    <div>
      {heading && <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold">Progress</h2><span role="status"><Pill ok={pillOk(task)}>{TASK_LABEL[task.status]}</Pill></span>
        <span className="text-xs text-ink-3">{summary(task)}</span>
        <a href={`#/task/${task.id}`} className="ml-auto text-sm text-link hover:underline">Full view</a></div>}
      <ol className="space-y-1.5">
        {task.steps.map(s => <li key={s.id} aria-current={now?.id === s.id ? 'step' : undefined} className={cx('grid grid-cols-[1.5rem_1fr] gap-x-1 rounded-field px-2 py-1.5 text-sm', MOTION, now?.id === s.id && 'bg-raised ring-1 ring-line')}>
          <span aria-hidden className={cx('pt-px text-center font-semibold', TONE[s.status])}>{s.status === 'running' ? <Spinner /> : STEP_SYMBOL[s.status]}</span>
          <div className="min-w-0">
            <span className={cx(s.status === 'pending' || s.status === 'skipped' ? 'text-ink-3' : 'font-medium')}>{s.label}</span>{' '}
            <span className={cx('text-xs font-semibold', TONE[s.status])}>{STEP_LABEL[s.status]}{s.attempts > 1 && s.status === 'running' ? ` (try ${s.attempts})` : ''}</span>
            {s.status === 'running' && s.pct !== null && <div className="mt-1 flex items-center gap-2"><div role="progressbar" aria-label={s.label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(s.pct)} className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
              <div className="h-full bg-act transition-[width] duration-[var(--motion-base)] ease-[var(--ease-out)]" style={{ width: `${s.pct}%` }} /></div><span className="w-9 text-right text-xs tabular-nums text-ink-2">{Math.round(s.pct)}%</span></div>}
            {s.detail && s.status !== 'failed' && <span className="block text-xs text-ink-2">{s.detail}</span>}
            {s.error && <span role="alert" className="block text-xs text-bad">{s.error}</span>}
          </div></li>)}
      </ol>
      {go && now && (now.status === 'waiting' || now.status === 'failed') && <a href={go.href} className={cx('mt-3 inline-flex min-h-[var(--control-height)] items-center rounded-btn border border-line-strong px-[var(--control-padding-x)] text-sm font-medium hover:bg-raised', MOTION)}>{go.label}</a>}
      <Actions task={task} onChange={onChange} />
    </div>
  )
}

/** One line for toolbars: where the task stands, with a link to the full view. Nothing when there is no open task. */
export function TaskStrip({ task }: { task: Task | null }) {
  if (!task || task.status === 'completed' || task.status === 'cancelled') return null
  const now = current(task)
  return <div role="status" className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line bg-surface px-4 py-1.5 text-xs">
    <Pill ok={pillOk(task)}>{TASK_LABEL[task.status]}</Pill>
    <span className="text-ink-2">{summary(task)}</span>
    {now?.error && <span className="text-bad">{now.error}</span>}
    <a href={`#/task/${task.id}`} className="ml-auto text-link hover:underline">View progress</a>
  </div>
}

/** The progress page (#/task/<id>): the prototype's dark "engine" screen, driven only by the recorded steps. */
export function TaskPage({ id }: { id: string }) {
  const { task, err, loaded, setTask } = useTask({ id })
  if (!task) return <div><a href="#/projects" className="mb-4 inline-block text-sm text-link hover:underline">← Projects</a>{err ? <Notice tone="error">{err}</Notice> : loaded ? <Notice tone="warning">This progress record was not found.</Notice> : <p className="text-sm text-ink-3">Loading…</p>}</div>
  const now = current(task)
  return (
    <div data-surface="editor" className="overflow-hidden rounded-sheet bg-canvas text-ink shadow-float">
      <div className="flex flex-wrap items-center gap-3 border-b border-line bg-surface px-4 py-2.5">
        <a href="#/projects" className={cx('rounded-field px-1 text-sm text-ink-2 hover:text-ink', MOTION)}>← Projects</a>
        <h1 className="text-sm font-semibold">{task.meta.title || (task.kind === 'reel' ? task.project.reel : 'Creation')} · progress</h1>
        <span role="status" className="ml-auto"><Pill ok={pillOk(task)}>{TASK_LABEL[task.status]}</Pill></span>
      </div>
      <div className="mx-auto max-w-2xl px-4 py-8">
        <div className="mb-6 flex items-center gap-4">
          {/* the ring turns only while a step is really running; with reduced motion it stays still */}
          <div aria-hidden className={cx('grid h-14 w-14 shrink-0 place-items-center rounded-full border-2', active(task) ? 'animate-spin border-act border-r-transparent motion-reduce:animate-none' : task.status === 'failed' ? 'border-bad-solid' : task.status === 'completed' ? 'border-ok' : 'border-line-strong')}>
            <span className={cx('text-lg font-semibold', active(task) && 'hidden')}>{task.status === 'completed' ? '✓' : task.status === 'failed' ? '✕' : task.status === 'waiting' ? '●' : '·'}</span></div>
          <div className="min-w-0"><p className="text-lg font-semibold">{now ? now.label : TASK_LABEL[task.status]}</p>
            <p className="text-sm text-ink-2">{summary(task)}. Each line below is the recorded state of a real step; nothing is estimated.</p></div>
        </div>
        {task.meta.prompt && <blockquote className={cx('mb-6 whitespace-pre-wrap border-l-2 border-line-strong pl-3 text-sm text-ink-2', /[ఀ-౿]/.test(task.meta.prompt) && 'te')}>{task.meta.prompt}</blockquote>}
        <TaskSteps task={task} onChange={setTask} heading={false} />
        <details className="mt-6 text-xs text-ink-2"><summary className={cx('cursor-pointer', MOTION)}>History ({task.events.length})</summary>
          <ul className="mt-2 space-y-0.5">{task.events.map((e, i) => <li key={i}><span className="text-ink-3">{e.at}</span> · {e.step ?? 'task'} · {e.status}{e.detail ? ` · ${e.detail}` : ''}</li>)}</ul></details>
      </div>
    </div>
  )
}
