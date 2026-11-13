// M7-B B4C-2: client for the durable local tasks (app/tasks.py). A task only records what really happened:
// the screen reports a poster step at the moment the existing M5 call succeeds or fails; reel steps are filled in by
// the server from the engine's own jobs. Recording must never break the work itself, so report() does not throw.
export type StepStatus = 'pending' | 'running' | 'waiting' | 'done' | 'failed' | 'cancelled' | 'skipped'
export type TaskStatus = 'pending' | 'running' | 'waiting' | 'completed' | 'failed' | 'cancelled' | 'retrying'
export type TaskStep = { id: string; label: string; user: boolean; retry: 'client' | 'job' | null; status: StepStatus; detail: string | null; error: string | null; pct: number | null; attempts: number; started: string | null; finished: string | null }
export type Task = { id: string; kind: 'poster' | 'reel' | 'both'; status: TaskStatus; created: string; updated: string; cancelled: boolean
  project: { posters: string[]; reel: string | null }; meta: { prompt?: string; output?: string; title?: string }; steps: TaskStep[]
  events: { at: string; step: string | null; status: string; detail: string | null }[] }

async function call<T>(method: 'GET' | 'POST', url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, { method, headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined, body: body !== undefined ? JSON.stringify(body) : undefined })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw Error(typeof data.detail === 'string' ? data.detail : `request failed (${r.status})`)
  return data as T
}
export const tasks = {
  get: (id: string) => call<Task>('GET', `/api/tasks/${encodeURIComponent(id)}`),
  forPoster: (poster: string) => call<{ tasks: Task[] }>('GET', `/api/tasks?poster=${encodeURIComponent(poster)}`).then(r => r.tasks[0] ?? null),
  forReel: (reel: string) => call<{ tasks: Task[] }>('GET', `/api/tasks?reel=${encodeURIComponent(reel)}`).then(r => r.tasks[0] ?? null),
  recent: () => call<{ tasks: Task[]; invalid: { file: string; reason: string }[] }>('GET', '/api/tasks'),
  create: (b: { kind: Task['kind']; key?: string; poster?: string; reel?: string; meta?: Task['meta'] }) => call<Task>('POST', '/api/tasks', b),
  cancel: (id: string) => call<Task>('POST', `/api/tasks/${encodeURIComponent(id)}/cancel`),
  retry: (id: string) => call<Task>('POST', `/api/tasks/${encodeURIComponent(id)}/retry`),
  cleanup: (older_than_days: number) => call<{ removed: number; kept: number }>('POST', '/api/tasks/cleanup', { older_than_days }),
}
/** Record a real step change. Returns the task, or null if recording failed (the work itself carries on). */
export async function report(task: Task | string | null | undefined, step: string, status: StepStatus, extra: { detail?: string; error?: string; poster?: string; reel?: string } = {}): Promise<Task | null> {
  const id = typeof task === 'string' ? task : task?.id
  if (!id) return null
  try { return await call<Task>('POST', `/api/tasks/${encodeURIComponent(id)}/step`, { step, status, ...extra }) }
  catch (e) { console.warn(`task ${id}: could not record ${step} ${status}: ${(e as Error).message}`); return null }
}

// ---- pure helpers (unit-tested in tests/web/test_tasks_logic.mjs)
export const TASK_LABEL: Record<TaskStatus, string> = { pending: 'Not started', running: 'Working', waiting: 'Waiting for you', completed: 'Completed', failed: 'Failed', cancelled: 'Cancelled', retrying: 'Trying again' }
export const STEP_LABEL: Record<StepStatus, string> = { pending: 'Not started', running: 'Working', waiting: 'Waiting for you', done: 'Done', failed: 'Failed', cancelled: 'Cancelled', skipped: 'Not needed' }
export const STEP_SYMBOL: Record<StepStatus, string> = { pending: '·', running: '›', waiting: '●', done: '✓', failed: '✕', cancelled: '–', skipped: '–' }
export const active = (t: Task) => t.status === 'running' || t.status === 'retrying'
export const finished = (t: Task) => t.status === 'completed' || t.status === 'cancelled'
/** The step the person should look at now: the failed one, else the running one, else the one waiting for them. */
export function current(t: Task): TaskStep | null {
  return t.steps.find(s => s.status === 'failed') ?? t.steps.find(s => s.status === 'running') ?? t.steps.find(s => s.status === 'waiting') ?? null
}
export function summary(t: Task): string {
  const done = t.steps.filter(s => s.status === 'done' || s.status === 'skipped').length; const c = current(t)
  return t.status === 'completed' ? 'All steps finished' : t.status === 'cancelled' ? 'Cancelled' : `Step ${Math.min(done + 1, t.steps.length)} of ${t.steps.length}${c ? `: ${c.label}` : ''}`
}
const REEL_STEPS = ['plan', 'approve', 'narrate', 'title', 'build', 'render']
/** Where the person goes to act on a step. Only real screens: concepts, the poster editor, the reel's own steps. */
export function whereTo(t: Task, step: TaskStep | null): { href: string; label: string } | null {
  if (!step) return null
  const first = t.project.posters[0], last = t.project.posters[t.project.posters.length - 1]
  if (REEL_STEPS.includes(step.id)) return t.project.reel ? { href: `#/p/${encodeURIComponent(t.project.reel)}`, label: 'Open the reel steps' } : null
  if (step.id === 'concepts' || step.id === 'choose') return first ? { href: `#/concepts/${encodeURIComponent(first)}`, label: 'Open Concepts' } : null
  if (step.id === 'poster') return first ? { href: `#/concepts/${encodeURIComponent(first)}`, label: 'Open Concepts' } : null
  if (['review', 'qa', 'export', 'handoff'].includes(step.id)) return last && t.project.posters.length > 1 ? { href: `#/poster/${encodeURIComponent(last)}`, label: 'Open the poster' } : null
  return null
}
/** How often to ask the server again: quickly while something runs, slowly while it waits, not at all when finished. */
export const pollMs = (t: Task | null) => (!t ? 0 : active(t) ? 1200 : finished(t) ? 0 : 5000)
