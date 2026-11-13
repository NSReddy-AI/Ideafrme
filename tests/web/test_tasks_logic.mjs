// Unit test for the pure helpers in app/web/src/tasks.ts (M7-B B4C-2). Run: node tests/web/test_tasks_logic.mjs
import assert from 'node:assert/strict'
import { STEP_LABEL, TASK_LABEL, active, current, finished, pollMs, summary, whereTo } from '../../app/web/src/tasks.ts'
let checks = 0
const eq = (a, b, m) => { checks++; assert.deepEqual(a, b, `${m ?? 'check ' + checks}: got ${JSON.stringify(a)}`) }
const step = (id, status, extra = {}) => ({ id, label: id, user: false, retry: null, status, detail: null, error: null, pct: null, attempts: 0, started: null, finished: null, ...extra })
const task = (status, steps, project = { posters: [], reel: null }) => ({ id: 'a'.repeat(12), kind: 'both', status, created: '', updated: '', cancelled: status === 'cancelled', project, meta: {}, steps, events: [] })

// ---- what to look at now: failed beats running beats waiting
let t = task('failed', [step('brief', 'done'), step('concepts', 'failed', { error: 'x' }), step('choose', 'waiting')])
eq(current(t).id, 'concepts'); eq(summary(t), 'Step 2 of 3: concepts'); eq(active(t), false); eq(finished(t), false)
t = task('running', [step('brief', 'done'), step('concepts', 'running'), step('choose', 'pending')]); eq(current(t).id, 'concepts'); eq(active(t), true)
t = task('waiting', [step('brief', 'done'), step('concepts', 'done'), step('choose', 'waiting')]); eq(current(t).id, 'choose'); eq(summary(t), 'Step 3 of 3: choose')
t = task('completed', [step('a', 'done'), step('b', 'skipped')]); eq(current(t), null); eq(summary(t), 'All steps finished'); eq(finished(t), true)
eq(summary(task('cancelled', [step('a', 'cancelled')])), 'Cancelled')

// ---- polling: fast only while something really runs, never after the end
eq(pollMs(null), 0); eq(pollMs(task('running', [step('a', 'running')])), 1200); eq(pollMs(task('retrying', [step('a', 'running')])), 1200)
eq(pollMs(task('waiting', [step('a', 'waiting')])), 5000); eq(pollMs(task('failed', [step('a', 'failed')])), 5000); eq(pollMs(task('completed', [step('a', 'done')])), 0); eq(pollMs(task('cancelled', [])), 0)

// ---- links go only to real screens, and only when the project they need exists
const both = { posters: ['p1', 'p2'], reel: '2026-11-12_x y' }
eq(whereTo(task('waiting', [], both), step('choose', 'waiting')), { href: '#/concepts/p1', label: 'Open Concepts' })
eq(whereTo(task('waiting', [], both), step('review', 'waiting')), { href: '#/poster/p2', label: 'Open the poster' })
eq(whereTo(task('waiting', [], both), step('handoff', 'waiting')).href, '#/poster/p2')
eq(whereTo(task('waiting', [], both), step('approve', 'waiting')), { href: '#/p/2026-11-12_x%20y', label: 'Open the reel steps' })
eq(whereTo(task('running', [], both), step('render', 'running')).href, '#/p/2026-11-12_x%20y')
eq(whereTo(task('waiting', [], { posters: ['p1'], reel: null }), step('review', 'waiting')), null, 'no chosen poster yet: no link')
eq(whereTo(task('waiting', [], { posters: [], reel: null }), step('approve', 'waiting')), null, 'no reel yet: no link'); eq(whereTo(task('waiting', []), null), null)
eq(whereTo(task('waiting', [], both), step('interpret', 'done')), null)

// ---- every state has plain words; none of the unfinished ones reads as finished
for (const k of ['pending', 'running', 'waiting', 'completed', 'failed', 'cancelled', 'retrying']) { checks++; assert.ok(TASK_LABEL[k]) }
for (const k of ['pending', 'running', 'waiting', 'failed', 'cancelled', 'skipped']) { checks++; assert.ok(!/done|complete|finished/i.test(STEP_LABEL[k]), k) }
console.log(JSON.stringify({ checks, failures: 0 }))
