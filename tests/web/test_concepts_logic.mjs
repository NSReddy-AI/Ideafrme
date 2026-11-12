// Unit test for app/web/src/concepts-logic.ts. Run: node tests/web/test_concepts_logic.mjs
import assert from 'node:assert/strict'
import { conceptSvg, nextConcept } from '../../app/web/src/concepts-logic.ts'
const plan = { id: 'x', name: 'Name <b>"q"</b>', rationale: '', composition: 'x', layers: [
  { id: 'bg', type: 'shape', x: 0, y: 0, width: 1080, height: 1350, style: { fill: '#F6F4EF', shape: 'rectangle' } },
  { id: 'o', type: 'shape', x: 100, y: 200, width: 400, height: 200, style: { fill: '#F4B942', shape: 'ellipse' } },
  { id: 't', type: 'text', x: 80, y: 150, width: 920, height: 400, style: { fill: '#14213D', font_size: 100 }, text: 'Line one\n<script>alert(1)</script> & తెలుగు' },
  { id: 'bad', type: 'shape', x: 0, y: 0, width: 10, height: 10, style: { fill: 'red;stroke:url(evil)', shape: 'rectangle' } } ] }
const s = conceptSvg(plan)
assert.ok(s.startsWith('<svg') && s.endsWith('</svg>'))
assert.ok(!s.includes('<script>') && s.includes('&lt;script&gt;alert(1)&lt;/script&gt; &amp; తెలుగు'), 'text is escaped, Telugu kept')
assert.ok(s.includes('aria-label="Name &lt;b&gt;&quot;q&quot;&lt;/b&gt;"'), 'label escaped')
assert.ok(s.includes('<ellipse cx="300" cy="300" rx="200" ry="100" fill="#F4B942"/>'))
assert.ok(s.includes('<tspan x="80" y="252.0">Line one</tspan>') && s.includes('y="417.0"'), 'baseline 1.02, line height 1.65')
assert.ok(s.includes('fill="none"') && !s.includes('evil'), 'unsafe colour is not painted')
assert.equal(nextConcept(2, 'ArrowRight', 3), 0); assert.equal(nextConcept(0, 'ArrowLeft', 3), 2); assert.equal(nextConcept(1, 'End', 3), 2); assert.equal(nextConcept(1, 'x', 3), null)
console.log(JSON.stringify({ checks: 10, failures: 0 }))
