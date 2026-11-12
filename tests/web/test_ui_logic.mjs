// Unit test for app/web/src/ui-logic.ts (Node runs the .ts directly). Run: node tests/web/test_ui_logic.mjs
import assert from 'node:assert/strict'
import { nextTab, toastLifetime, TONE_LABEL } from '../../app/web/src/ui-logic.ts'
assert.equal(nextTab(0, 'ArrowRight', 3), 1); assert.equal(nextTab(2, 'ArrowRight', 3), 0)
assert.equal(nextTab(0, 'ArrowLeft', 3), 2); assert.equal(nextTab(1, 'ArrowUp', 3), 0); assert.equal(nextTab(1, 'ArrowDown', 3), 2)
assert.equal(nextTab(1, 'Home', 3), 0); assert.equal(nextTab(0, 'End', 3), 2)
assert.equal(nextTab(1, 'a', 3), null); assert.equal(nextTab(0, 'ArrowRight', 0), null)
assert.equal(toastLifetime('error'), null, 'errors never vanish on their own')
assert.ok(toastLifetime('success') > 0 && toastLifetime('warning') > toastLifetime('success'))
for (const t of ['info', 'success', 'warning', 'error']) assert.ok(TONE_LABEL[t].symbol && TONE_LABEL[t].word, 'never colour alone: ' + t)
console.log(JSON.stringify({ checks: 14, failures: 0 }))
