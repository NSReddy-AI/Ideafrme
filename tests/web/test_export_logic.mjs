// Unit test for app/web/src/export-logic.ts and the M5 editing helpers the editor relies on (M7-B B3).
// Run: node tests/web/test_export_logic.mjs
import assert from 'node:assert/strict'
import { PHASES, readiness, savedFiles } from '../../app/web/src/export-logic.ts'
import { nextLayerIndex, nudge, shortcut, zoomWidth } from '../../m5/visual_poster_studio/editing.mjs'
let checks = 0
const ok = (v, m) => { checks++; assert.ok(v, m) }
const eq = (a, b, m) => { checks++; assert.deepEqual(a, b, m) }
const good = { locked: false, current: true, previewErr: null, overflow: 0, wordsBlocked: false, qaKnown: true, errors: 0, warnings: 0, fontsReady: true, pngOk: true, pngNote: 'PNG export available.' }
const state = (r, id) => r.items.find(i => i.id === id).state

// ---- ready
let r = readiness(good)
ok(r.svg.allowed && r.png.allowed && r.svg.reason === null, 'all clear: both formats')
ok(r.items.every(i => i.state === 'ok'), 'all items ready')

// ---- every blocking gate the toolbar had still blocks, for both formats
for (const [name, patch] of [['locked', { locked: true }], ['stale preview', { current: false }], ['overflow', { overflow: 2 }], ['approved words', { wordsBlocked: true }]]) {
  r = readiness({ ...good, ...patch })
  ok(!r.svg.allowed && !r.png.allowed && r.svg.reason, `${name} blocks SVG and PNG`)
}
eq(state(readiness({ ...good, overflow: 1 }), 'overflow'), 'blocked')
eq(state(readiness({ ...good, wordsBlocked: true }), 'approved'), 'blocked')
eq(state(readiness({ ...good, current: false }), 'preview'), 'pending')
eq(state(readiness({ ...good, current: false, previewErr: 'server refused' }), 'preview'), 'blocked')

// ---- PNG needs M5's probe; SVG does not
r = readiness({ ...good, pngOk: false, pngNote: 'PNG export unavailable: probe' })
ok(r.svg.allowed && !r.png.allowed && r.png.reason, 'no PNG without the probe')
eq(state(r, 'png'), 'advisory')
ok(r.items.find(i => i.id === 'png').detail.includes('probe'), 'probe reason is shown')

// ---- QA findings are shown, never hidden, and never reported as passing
r = readiness({ ...good, errors: 1, warnings: 2 })
eq(state(r, 'qa'), 'advisory'); ok(/1 error, 2 warnings/.test(r.items.find(i => i.id === 'qa').detail), 'counts are stated')
eq(state(readiness({ ...good, qaKnown: false }), 'qa'), 'pending', 'unknown QA is not a pass')
eq(state(readiness({ ...good, qaKnown: false }), 'approved'), 'pending', 'unknown approval check is not a pass')
ok(!JSON.stringify(readiness(good)).toLowerCase().includes('approved for'), 'no claim that the draft is approved')

// ---- phases and files
eq(PHASES.map(p => p.id), ['begin', 'check', 'raster', 'save'])
eq(savedFiles('/a/b/', true), ['/a/b/poster.draft.svg', '/a/b/poster.draft.png', '/a/b/manifest.json'])
eq(savedFiles('/a/b', false), ['/a/b/poster.draft.svg', '/a/b/manifest.json'])

// ---- M5 keyboard policy as the editor calls it: shortcut(event, composing, editable)
const k = (key, o = {}) => ({ key, ctrlKey: false, metaKey: false, altKey: false, shiftKey: false, ...o })
eq(shortcut(k('s', { metaKey: true }), false, true), 'save', 'save works inside a text box')
eq(shortcut(k('z', { metaKey: true }), false, false), 'undo'); eq(shortcut(k('z', { metaKey: true, shiftKey: true }), false, false), 'redo'); eq(shortcut(k('y', { ctrlKey: true }), false, false), 'redo')
eq(shortcut(k('z', { metaKey: true }), false, true), null, 'typing keeps its own undo')
eq(shortcut(k('Enter', { ctrlKey: true }), false, true), 'apply-text')
eq(shortcut(k('s', { metaKey: true }), true, false), null, 'nothing during IME composition')
eq(shortcut(k('s', { metaKey: true, isComposing: true }), false, false), null)
eq(shortcut(k('z'), false, false), null, 'plain keys are not shortcuts')
eq(nudge(k('ArrowLeft', { altKey: true }), false, false), { x: -1, y: 0 }); eq(nudge(k('ArrowDown', { altKey: true, shiftKey: true }), false, false), { x: 0, y: 10 })
eq(nudge(k('ArrowLeft', { altKey: true }), false, true), null, 'no nudge while typing'); eq(nudge(k('ArrowLeft'), false, false), null); eq(nudge(k('ArrowLeft', { altKey: true }), true, false), null)
eq(zoomWidth('fit'), 'min(100%, 540px)'); eq(zoomWidth('100'), '1080px'); eq(zoomWidth('50'), '540px')
assert.throws(() => zoomWidth('200')); checks++
eq(nextLayerIndex(0, 'ArrowDown', 3), 1); eq(nextLayerIndex(2, 'ArrowDown', 3), 2); eq(nextLayerIndex(1, 'Home', 3), 0); eq(nextLayerIndex(0, 'End', 3), 2); eq(nextLayerIndex(0, 'ArrowUp', 0), -1)
console.log(JSON.stringify({ checks, failures: 0 }))
