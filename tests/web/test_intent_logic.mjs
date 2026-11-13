// Unit test for app/web/src/intent-logic.ts (M7-B B4B-1). Run: node tests/web/test_intent_logic.mjs
import assert from 'node:assert/strict'
import { interpret, matchBrand, missing, scriptOf } from '../../app/web/src/intent-logic.ts'
let checks = 0
const eq = (a, b, m) => { checks++; assert.deepEqual(a, b, `${m ?? 'check ' + checks}: got ${JSON.stringify(a)}`) }
const ok = (v, m) => { checks++; assert.ok(v, m) }
const codes = i => i.notes.map(n => n.code)

// ---- English prompt: only what is stated
let i = interpret('Poster for Reading Day, to invite families. For parents in Guntur. No prices.')
eq(i.original, 'Poster for Reading Day, to invite families. For parents in Guntur. No prices.', 'prompt kept exactly')
eq(i.output, { value: 'poster', source: 'typed' }); eq(i.script, 'en'); eq(i.language, 'en')
eq(i.topic, { value: 'Reading Day', source: 'default' }, 'topic suggested from the words after "poster for"')
eq(i.purpose, { value: 'Invite families', source: 'default' }); eq(i.audience, { value: 'parents in Guntur', source: 'default' })
eq(i.instructions, { value: 'No prices', source: 'typed' }, 'limits kept word for word')
eq(i.name.source, 'default'); eq(codes(i), [])

// ---- quoted and labelled values are taken exactly
i = interpret('Make a poster with the headline "Free eye camp this Sunday". Audience: residents of Tenali. Purpose: bring people to the camp')
eq(i.topic, { value: 'Free eye camp this Sunday', source: 'typed' }); eq(i.audience, { value: 'residents of Tenali', source: 'typed' }); eq(i.purpose, { value: 'bring people to the camp', source: 'typed' })

// ---- Telugu prompt: detected, never translated
i = interpret('చదువుల పండుగ పోస్టర్')
eq(i.script, 'te'); eq(i.language, 'te'); eq(i.output, { value: 'poster', source: 'typed' })
eq(i.topic, { value: 'చదువుల పండుగ', source: 'default' }, 'Telugu words kept as typed')
eq(i.purpose.source, 'missing'); eq(i.audience.source, 'missing'); ok(!codes(i).includes('no-translation'))

// ---- mixed-language prompt
i = interpret('Poster for చదువుల పండుగ, to invite families')
eq(i.script, 'mixed'); eq(i.topic.value, 'చదువుల పండుగ'); eq(i.language, 'te'); eq(i.purpose.value, 'Invite families')

// ---- asking for a language that was not typed: said plainly, nothing translated
i = interpret("Create a premium Children's Day campaign for parents in Guntur. Use Telugu as the primary language, make a beautiful poster, and prepare a cinematic Instagram reel.")
eq(i.output, { value: 'both', source: 'typed' }); ok(codes(i).includes('no-translation'), 'says it does not translate')
ok(!/[ఀ-౿]/.test(JSON.stringify(i)), 'no Telugu text is produced from an English prompt')
eq(i.audience.value, 'parents in Guntur'); eq(i.purpose.source, 'missing', 'purpose is not invented')
eq(i.topic.source, 'missing', 'the audience is not mistaken for the headline')
ok(interpret('Translate this poster to Telugu: "Reading day"').notes.some(n => n.code === 'no-translation'))

// ---- missing details stay missing; nothing is invented
i = interpret('I want something nice for the festival next week, it should feel warm and friendly and remind people of home.')
eq(i.output, { value: 'poster', source: 'default' }, 'no output named: poster is only a default'); eq(i.topic.source, 'missing'); eq(i.audience.source, 'missing'); eq(i.name, { value: '', source: 'missing' }, 'no project name is guessed without a topic')
ok(!/\d{4}|november|monday/i.test(JSON.stringify({ ...i, original: '' })), 'no date invented')
eq(missing({ name: 'x', topic: '', purpose: ' ', audience: 'a' }), ['topic', 'purpose'])
eq(interpret('   ').notes[0].code, 'empty')

// ---- output: explicit, both, chosen by hand, ambiguous
eq(interpret('a reel about our new shop').output, { value: 'reel', source: 'typed' }); eq(interpret('రీల్ కావాలి').output.value, 'reel')
eq(interpret('poster and a video for the launch').output.value, 'both')
eq(interpret('a reel about our shop', 'poster').output, { value: 'poster', source: 'typed' }, 'the control wins when the person set it')
i = interpret('Make a poster, not a reel, for the school fair'); eq(i.output.source, 'missing'); ok(codes(i).includes('ambiguous-output'))

// ---- unsupported requests are named, not attempted
ok(codes(interpret('Design a logo and a website banner for my shop')).includes('unsupported-format'))
ok(codes(interpret('Poster for Diwali, generate a photo of fireworks')).includes('no-generated-images'))

// ---- brands: eligible only; a named draft is reported and never used
const eligible = [{ hash: 'h1', name: 'Reading Trust' }]
eq(matchBrand('Poster for Reading Trust open day', eligible, ['Jagan For Andhra']), { hash: 'h1', note: null })
let b = matchBrand('Poster for Jagan For Andhra rally', eligible, ['Jagan For Andhra']); eq(b.hash, null); eq(b.note.code, 'brand-unavailable')
eq(matchBrand('Poster for a rally', [], ['Jagan For Andhra']), { hash: null, note: null })
eq(scriptOf('123 !!'), 'none')

console.log(JSON.stringify({ checks, failures: 0 }))
