// Unit test for app/web/src/capabilities.ts (M7-B B4C-3). Run: node tests/web/test_capabilities_logic.mjs
import assert from 'node:assert/strict'
import { STATE_LABEL, facets, stateOf, usable } from '../../app/web/src/capabilities.ts'
let checks = 0
const eq = (a, b, m) => { checks++; assert.deepEqual(a, b, `${m ?? 'check ' + checks}: got ${JSON.stringify(a)}`) }
const cap = (o = {}) => ({ id: 'x', label: 'x', runner: 'local-model', detail: '', source: null, installed: true, configured: true, available: true, qualified: 'yes', running: false, failed: false, unsupported: false, off: false, ...o })

eq(stateOf(cap()), 'available'); eq(usable(cap()), true); eq(stateOf(cap({ running: true })), 'running'); eq(usable(cap({ running: true })), true)
// a reason it cannot be used always wins, whatever else is true
eq(stateOf(cap({ unsupported: true })), 'unsupported'); eq(stateOf(cap({ failed: true })), 'failed'); eq(stateOf(cap({ off: true })), 'off')
eq(stateOf(cap({ qualified: 'no' })), 'not-qualified', 'installed and available but not qualified is never shown as available'); eq(usable(cap({ qualified: 'no', running: true })), false)
eq(stateOf(cap({ available: false })), 'installed'); eq(stateOf(cap({ available: false, installed: false })), 'not-installed'); eq(stateOf(cap({ available: false, installed: null })), 'not-installed', 'unknown is not rounded up')
eq(stateOf(cap({ runner: 'online', installed: null, available: false, configured: false })), 'not-configured'); eq(stateOf(cap({ runner: 'online', installed: null, available: false, off: true, configured: true })), 'off', 'a key never switches a provider on')
eq(stateOf(cap({ running: true, available: false })), 'installed', 'running alone is not available')
for (const s of ['unsupported', 'failed', 'off', 'not-qualified', 'installed', 'not-configured', 'not-installed']) { checks++; assert.ok(!/ready|available$/i.test(STATE_LABEL[s]) || s === 'available', s) }
eq(facets(cap({ unsupported: true })).length, 1); eq(facets(cap()).map(f => f[0]), ['Installed', 'Configured', 'Available', 'Qualified', 'Running', 'Failed'])
eq(facets(cap({ installed: null }))[0][1], 'not known'); eq(facets(cap({ qualified: 'not-assessed' }))[3][1], 'not assessed'); eq(facets(cap({ off: true }))[2][1], 'no (switched off)')
console.log(JSON.stringify({ checks, failures: 0 }))
