// Unit test for the measured-text rules (app/web/src/measure.ts). Node 22.6+ runs the TypeScript file directly (types stripped).
// Run: node tests/web/test_measure.mjs
import assert from 'node:assert/strict'
import { measuredChecks } from '../../app/web/src/measure.ts'

const view = { width: 1080, height: 1350 }, M = 64
const at = (x, y, w, h) => [{ element_id: 'a', x, y, width: w, height: h }]
assert.deepEqual(measuredChecks(at(100, 100, 500, 80), view, M), [], 'well inside: no finding')
let r = measuredChecks(at(20, 100, 500, 80), view, M)
assert.equal(r.length, 1); assert.equal(r[0].name, 'measured_safe_area'); assert.equal(r[0].level, 'warning'); assert.match(r[0].detail, /20 px from the left edge/)
r = measuredChecks(at(600, 1300, 470, 40), view, M)
assert.match(r[0].detail, /right edge/); assert.match(r[0].detail, /bottom edge/)
r = measuredChecks(at(-3, 100, 500, 80), view, M)
assert.equal(r[0].name, 'measured_canvas'); assert.equal(r[0].level, 'error')
r = measuredChecks(at(900, 100, 200, 80), view, M)
assert.equal(r[0].name, 'measured_canvas', 'ink past the right edge is an error')
assert.deepEqual(measuredChecks(at(64, 64, 952, 1222), view, M), [], 'exactly on the margin is allowed')
console.log(JSON.stringify({ checks: 9, failures: 0 }))
