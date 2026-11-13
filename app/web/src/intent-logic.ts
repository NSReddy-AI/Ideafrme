// M7-B B4B-1: rule-based reading of an Omnibar prompt (no React, no DOM, no model), unit-tested in
// tests/web/test_intent_logic.mjs. It only picks out what the person plainly typed. It never translates, and it
// never fills in a date, claim, endorsement, audience, purpose or brand permission that is not in the prompt.
// A qualified local model can later replace interpret() behind the same Interpretation type.

export type Source = 'typed' | 'default' | 'missing'
//   typed   = taken word for word from the prompt (a quoted or labelled value, or an explicit request)
//   default = a suggestion built from the prompt's own words, to be checked and edited
//   missing = not in the prompt; the person must supply it
export type Slot<T = string> = { value: T; source: Source }
export type Output = 'poster' | 'reel' | 'both'
export type Script = 'te' | 'en' | 'mixed' | 'none'
export type Note = { code: 'no-translation' | 'unsupported-format' | 'no-generated-images' | 'ambiguous-output' | 'brand-unavailable' | 'empty'; text: string }
export type Interpretation = {
  original: string                 // the prompt exactly as typed
  script: Script                   // which scripts the prompt uses
  language: 'te' | 'en'            // script of the suggested headline (never a translation)
  output: Slot<Output>
  name: Slot; topic: Slot; purpose: Slot; audience: Slot; instructions: Slot
  notes: Note[]
}

const TELUGU = /[ఀ-౿]/
const count = (s: string, re: RegExp) => (s.match(re) ?? []).length
export function scriptOf(s: string): Script {
  const te = count(s, /[ఀ-౿]/g), en = count(s, /[A-Za-z]/g)
  if (!te && !en) return 'none'
  if (te && en) return Math.min(te, en) / (te + en) < 0.1 ? (te > en ? 'te' : 'en') : 'mixed'
  return te ? 'te' : 'en'
}

const clean = (s: string) => s.replace(/\s+/g, ' ').replace(/^[\s,;:.\-–—]+|[\s,;:.\-–—]+$/g, '')
const POSTER = /\bposters?\b|పోస్టర్/i
const REEL = /\breels?\b|\bvideos?\b|రీల్|వీడియో/i
const NEGATED = /\b(no|not|without|don'?t|do not|skip|instead of)\s+(a\s+|an\s+|the\s+|any\s+)?(poster|reel|video)s?\b/i
const UNSUPPORTED = /\b(logo|website|web ?page|banner|flyer|brochure|carousel|thumbnail|story|stories|a4|a3|billboard|hoarding|business card|16:9|1:1|square|landscape)\b/i
const IMAGES = /\b(generate|create|make|draw|add)\b[^.!?\n]{0,40}\b(photo|photos|image|images|picture|pictures|illustration|illustrations|artwork)\b|\bai (image|photo|art)\b/i
const TRANSLATE = /\btranslat\w*|అనువద|అనువాద/i
const LABEL = (names: string) => new RegExp(`(?:^|[\\n.;])\\s*(?:${names})\\s*[:=]\\s*([^\\n;]+?)(?=[.!?](?:\\s|$)|[;\\n]|$)`, 'i')
const QUOTED = /["“”«»]([^"“”«»\n]{2,200})["“”«»]|(?:^|\s)'([^'\n]{2,200})'(?=\s|[.,;!?]|$)/
const AUDIENCE_NOUN = '(?:parents|families|students|teachers|children|kids|farmers|women|men|youth|voters|residents|citizens|customers|members|employees|workers|volunteers|doctors|nurses|patients|shopkeepers|traders|freelancers|editors|creators|beginners|professionals|seniors|elders|devotees|fans|everyone)'
const AUDIENCE = new RegExp(`\\b(?:for|aimed at|targeting|to reach)\\s+((?:the\\s+|all\\s+|young\\s+|local\\s+|new\\s+)?${AUDIENCE_NOUN}(?:\\s+(?:and|&)\\s+${AUDIENCE_NOUN})?(?:\\s+(?:in|of|from|at|across)\\s+[A-Z\\u0C00-\\u0C7F][\\w\\u0C00-\\u0C7F]*(?:\\s+[A-Z][\\w]*)?)?)`, 'i')
const PURPOSE = /\b(?:to|should|must)\s+((?:invite|inform|announce|celebrate|remind|thank|promote|educate|encourage|welcome|congratulate|introduce|launch|explain|teach|motivate|inspire)\b[^.!?\n;]{0,120})/i
const ABOUT = /\b(?:posters?|reels?|videos?|campaign|post|creative|design)\s+(?:for|about|on)\s+([^.!?\n;]{2,160})/i
const CONSTRAINT = /^(?:no|never|don'?t|do not|avoid|without|must|only|always|use|keep|make sure|ensure)\b/i

/** Reads a prompt. `chosen` is the Poster/Reel/Both control when the person set it themselves. */
export function interpret(prompt: string, chosen?: Output | null): Interpretation {
  const original = prompt
  const text = prompt.trim()
  const notes: Note[] = []
  const miss = (): Slot => ({ value: '', source: 'missing' })
  if (!text) return { original, script: 'none', language: 'en', output: { value: chosen ?? 'poster', source: chosen ? 'typed' : 'default' }, name: miss(), topic: miss(), purpose: miss(), audience: miss(), instructions: miss(),
    notes: [{ code: 'empty', text: 'Type what you want to make.' }] }

  // ---- output: only what is asked for in plain words
  const p = POSTER.test(text), r = REEL.test(text)
  let output: Slot<Output>
  if (chosen) output = { value: chosen, source: 'typed' }
  else if (NEGATED.test(text)) { output = { value: 'poster', source: 'missing' }; notes.push({ code: 'ambiguous-output', text: 'Your words rule something out, so the output is not clear. Choose Poster, Reel or Both.' }) }
  else if (p && r) output = { value: 'both', source: 'typed' }
  else if (r) output = { value: 'reel', source: 'typed' }
  else if (p) output = { value: 'poster', source: 'typed' }
  else output = { value: 'poster', source: 'default' }

  // ---- topic / headline: quoted or labelled words are taken exactly; otherwise a suggestion from the prompt's own words
  const labelled = (names: string): Slot | null => { const m = text.match(LABEL(names)); return m && clean(m[1]) ? { value: clean(m[1]), source: 'typed' } : null }
  const q = text.match(QUOTED)
  let topic: Slot = labelled('headline|topic|title|శీర్షిక|అంశం') ?? (q ? { value: clean(q[1] ?? q[2]), source: 'typed' } : miss())
  if (topic.source === 'missing') {
    const about = text.match(ABOUT)
    const stripped = clean(text.replace(/\b(please|create|make|design|build|prepare|generate|a|an|the|new|premium|beautiful|me)\b/gi, ' ').replace(POSTER, ' ').replace(REEL, ' ').replace(/\b(for|about|on|and)\b\s*$/i, ''))
    const people = new RegExp(`^(?:the\\s+|all\\s+|young\\s+|local\\s+|new\\s+)?${AUDIENCE_NOUN}\\b`, 'i')   // "campaign for parents" names the audience, not the topic
    if (about && people.test(clean(about[1]))) topic = miss()
    else if (about) topic = { value: clean(about[1].split(/\b(?:for|aimed at|targeting|to)\s+/i)[0]) || clean(about[1]), source: 'default' }
    else if (text.split(/\s+/).length <= 8 && !/[.!?\n]/.test(text) && stripped) topic = { value: stripped, source: 'default' }
  }
  const audience: Slot = labelled('audience|for whom|ప్రేక్షకులు') ?? (() => { const m = text.match(AUDIENCE); return m ? { value: clean(m[1]), source: 'default' as Source } : miss() })()
  const purpose: Slot = labelled('purpose|goal|aim|ఉద్దేశం') ?? (() => { const m = text.match(PURPOSE); return m ? { value: clean(m[1].replace(/^./, c => c.toUpperCase())), source: 'default' as Source } : miss() })()

  // ---- instructions: the person's own limiting sentences, word for word
  const limits = text.split(/(?<=[.!?\n])\s+|\n+/).map(clean).filter(s => CONSTRAINT.test(s))
  const instructions: Slot = labelled('instructions|limits|rules|సూచనలు') ?? (limits.length ? { value: limits.join('. ').slice(0, 2000), source: 'typed' } : { value: '', source: 'default' })

  // ---- name: a short working title from the topic, always editable; no topic, no guess
  const name: Slot = labelled('project name|name') ?? (topic.value ? { value: clean(topic.value.split(/\s+/).slice(0, 5).join(' ')).slice(0, 40), source: 'default' } : miss())

  // ---- honest notes about what this build does not do
  const language: 'te' | 'en' = TELUGU.test(topic.value || text) && scriptOf(topic.value || text) !== 'en' ? 'te' : 'en'
  const wantsOther = (/\btelugu\b|తెలుగులో/i.test(text) && !TELUGU.test(topic.value || text)) || (/\benglish\b/i.test(text) && !!topic.value && !/[A-Za-z]/.test(topic.value))
  if (TRANSLATE.test(text) || wantsOther) notes.push({ code: 'no-translation', text: 'IDEAFRAME does not translate. The headline is used exactly as you type it, so type it in the language you want on the poster.' })
  if (UNSUPPORTED.test(text)) notes.push({ code: 'unsupported-format', text: 'This build makes 1080 × 1350 posters and vertical reels. Other formats and sizes are not available.' })
  if (IMAGES.test(text)) notes.push({ code: 'no-generated-images', text: 'Posters here are built from text and shapes. Pictures are not generated.' })
  return { original, script: scriptOf(text), language, output, name, topic, purpose, audience, instructions, notes }
}

/** Required by the existing brief contract (M5 workflow + concept step) before a poster can be started. */
export const REQUIRED = ['name', 'topic', 'purpose', 'audience'] as const
export function missing(v: Record<(typeof REQUIRED)[number], string>): (typeof REQUIRED)[number][] {
  return REQUIRED.filter(k => !v[k].trim())
}

/** A brand named in the prompt is preselected only if it is eligible (approved, rights current). A named brand that
 *  is not eligible is reported, never used. Brand permission is never inferred. */
export function matchBrand(prompt: string, eligible: { hash: string; name: string }[], unavailable: string[]): { hash: string | null; note: Note | null } {
  const t = prompt.toLowerCase()
  const named = (n: string) => n.trim().length >= 3 && t.includes(n.trim().toLowerCase())
  const hit = eligible.find(b => named(b.name))
  if (hit) return { hash: hit.hash, note: null }
  const off = unavailable.find(named)
  return { hash: null, note: off ? { code: 'brand-unavailable', text: `"${off}" cannot be used: its rights are not reviewed and approved. Continue without a brand kit, or review it in Brand Studio.` } : null }
}

export const SOURCE_LABEL: Record<Source, string> = { typed: 'From your words', default: 'Suggested. Check it', missing: 'Needed' }
