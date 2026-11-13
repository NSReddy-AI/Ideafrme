// Unit test for app/web/src/projects-logic.ts (M7-B B4B-2). Run: node tests/web/test_projects_logic.mjs
import assert from 'node:assert/strict'
import { EMPTY, combine, counts, matches, parseLink } from '../../app/web/src/projects-logic.ts'
let checks = 0
const eq = (a, b, m) => { checks++; assert.deepEqual(a, b, `${m ?? 'check ' + checks}: got ${JSON.stringify(a)}`) }
const ok = (v, m) => { checks++; assert.ok(v, m) }
const record = (reel, id, extra = {}) => ({ format: 'ideaframe-poster-to-reel@1', created: '2026-11-12 14:39:31', project: reel, poster: { project_id: id, name: 'Editorial hierarchy', revision: 27 }, ...extra })

// ---- a link exists only from the converter's exact record for that reel
eq(parseLink('r1', record('r1', 'p1')), { reel: 'r1', posterId: 'p1', posterName: 'Editorial hierarchy', revision: 27, created: '2026-11-12 14:39:31' })
eq(parseLink('r1', record('other', 'p1')), null, 'a record for another reel is not a link')
eq(parseLink('r1', record('r1', 'p1', { format: 'something-else@1' })), null); eq(parseLink('r1', { ...record('r1', ''), }), null); eq(parseLink('r1', null), null); eq(parseLink('r1', 'text'), null); eq(parseLink('r1', { format: 'ideaframe-poster-to-reel@1', project: 'r1' }), null)

const reels = [
  { name: '2026-11-12_reading_day', brand: 'tech_ai_tools', mode: 'slides', status: 'new', steps_done: 4, modified: '2026-11-12 14:41', exports: 3 },
  { name: '2026-11-03_reel_002', brand: 'jagan_for_andhra', mode: 'speaker', status: 'rendered', modified: '2026-11-03 10:00', exports: 0 },
  { name: 'zz_old', mode: 'slides', archived: true, modified: '2026-11-01 09:00', exports: 0 }]
const posters = [{ project_id: 'p2', name: 'Reading day', dirty: false, saved: true }, { project_id: 'p1', name: 'Editorial hierarchy', dirty: true, saved: true }]
const links = [parseLink('2026-11-12_reading_day', record('2026-11-12_reading_day', 'p1'))]

// ---- same names never link: "Reading day" poster and "reading_day" reel are unrelated without a record
let items = combine(reels, posters, [])
eq(counts(items), { all: 5, poster: 2, reel: 3, both: 0 }); ok(items.every(i => i.linked.length === 0), 'no link from similar names or dates')

// ---- recorded link: both sides are marked and point at each other
items = combine(reels, posters, links)
eq(counts(items), { all: 5, poster: 2, reel: 3, both: 2 })
const reel = items.find(i => i.key === 'reel:2026-11-12_reading_day'), poster = items.find(i => i.key === 'poster:p1')
eq(reel.linked, [{ label: 'Made from poster "Editorial hierarchy" (revision 27)', href: '#/poster/p1' }]); eq(poster.linked, [{ label: 'Reel made from it: 2026-11-12_reading_day', href: '#/p/2026-11-12_reading_day' }])
eq(items.filter(i => matches(i, 'both')).map(i => i.key), ['reel:2026-11-12_reading_day', 'poster:p1'])
eq(items.filter(i => matches(i, 'poster')).map(i => i.title), ['Editorial hierarchy', 'Reading day'], 'posters by name'); eq(items.filter(i => matches(i, 'reel')).length, 3); eq(items.filter(i => matches(i, 'all')).length, 5)

// ---- only supported facts: reel dates and steps from the reel list, no date for posters
eq(reel.modified, '2026-11-12 14:41'); eq(reel.status, 'Status: new'); eq(reel.facts, ['slides reel', 'reel brand tech_ai_tools', '4 steps done', '3 exports']); eq(reel.href, '#/p/2026-11-12_reading_day')
eq(items.find(i => i.key === 'reel:2026-11-03_reel_002').status, 'Status: rendered'); eq(items.find(i => i.key === 'reel:zz_old').status, 'Archived')
eq(poster.modified, null, 'no poster date is invented'); eq(poster.status, 'Unsaved changes'); eq(items.find(i => i.key === 'poster:p2').status, 'Saved'); eq(poster.href, '#/poster/p1')

// ---- a recorded poster that is not in this library: said so, no dead link; a record for a missing reel is ignored
items = combine(reels, [posters[0]], links)
eq(items.find(i => i.key === 'reel:2026-11-12_reading_day').linked, [{ label: 'Made from a poster that is not in this poster library ("Editorial hierarchy")', href: null }]); eq(counts(items).both, 1)
eq(counts(combine([reels[1]], posters, links)).both, 0)

// ---- empty states
eq(counts(combine([], [], [])), { all: 0, poster: 0, reel: 0, both: 0 }); ok(EMPTY.all && EMPTY.poster && EMPTY.reel && EMPTY.both)
console.log(JSON.stringify({ checks, failures: 0 }))
