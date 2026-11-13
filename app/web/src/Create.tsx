// M7-B B2: one place to start - idea and brief, output (Poster / Reel / Both), brand kit.
// Posters (and "Both") start through M5's brief workflow, so the next step can offer three concepts.
// Reels keep the existing M4 reel steps (passed in as reelForm).
import { useState } from 'react'
import { useBrandChoices } from './brand-choices'
import { creative } from './creative'
import { SOURCE_LABEL, missing, type Source } from './intent-logic'
import { Btn, Card, Field, FormRow, Notice, PageHead, Select, Tabs, TextArea } from './ui'

type Output = 'poster' | 'reel' | 'both'
const msg = (e: unknown) => (e as Error).message

export function Create({ reelForm, onConcepts }: { reelForm: React.ReactNode; onConcepts: (id: string) => void }) {
  const [output, setOutput] = useState<Output>('poster')
  return (
    <div className="space-y-6">
      <PageHead title="Create" sub="Start from an idea. Choose a poster, a reel, or both." />
      <Tabs label="What to make" value={output} onChange={setOutput} tabs={[{ id: 'poster', label: 'Poster' }, { id: 'reel', label: 'Reel' }, { id: 'both', label: 'Both' }]} />
      {output === 'reel' ? <>
        <Notice tone="info">Reels start from your own video, pictures or recording, and use the reel brands in Reels.</Notice>
        {reelForm}
      </> : <BriefForm both={output === 'both'} onConcepts={onConcepts} />}
    </div>
  )
}

export type BriefValues = { name: string; topic: string; purpose: string; audience: string; instructions: string; language: 'te' | 'en'; brand: string }
type BriefField = 'name' | 'topic' | 'purpose' | 'audience' | 'instructions'
const FIELD_LABEL: Record<BriefField, string> = { name: 'a project name', topic: 'a topic', purpose: 'a purpose', audience: 'an audience', instructions: 'instructions' }

/** The one brief form. Advanced Create opens it empty; Home opens it filled from the Omnibar, with `sources` saying
 *  where each value came from. Either way it calls the same M5 brief workflow and keeps the same acknowledgement. */
export function BriefForm({ both, onConcepts, initial, sources, title }: { both: boolean; onConcepts: (id: string) => void
  initial?: Partial<BriefValues>; sources?: Partial<Record<BriefField, Source>>; title?: string }) {
  const [name, setName] = useState(initial?.name ?? ''); const [topic, setTopic] = useState(initial?.topic ?? ''); const [purpose, setPurpose] = useState(initial?.purpose ?? '')
  const [audience, setAudience] = useState(initial?.audience ?? ''); const [instructions, setInstructions] = useState(initial?.instructions ?? ''); const [language, setLanguage] = useState<'te' | 'en'>(initial?.language ?? 'te')
  const [brand, setBrand] = useState(initial?.brand ?? ''); const [ack, setAck] = useState(false); const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const [edited, setEdited] = useState<Partial<Record<BriefField, boolean>>>({})
  const { usable, unavailable } = useBrandChoices()
  const need = missing({ name, topic, purpose, audience })   // the concept step refuses a brief without purpose and audience
  const ready = !need.length && ack
  const touch = (k: BriefField) => setEdited(e => (e[k] ? e : { ...e, [k]: true }))
  // where a prefilled value came from, until the person edits it
  const hint = (k: BriefField, help?: string) => [sources && !edited[k] && sources[k] ? SOURCE_LABEL[sources[k]] : null, help].filter(Boolean).join(' · ') || undefined
  const start = async () => {
    setBusy(true); setErr(null)
    try {
      const p = await creative.createFromBrief({ name: name.trim(), text: topic.trim(), language, acknowledge: true, brand_hash: brand || null,
        brief: { topic: topic.trim(), purpose: purpose.trim(), audience: audience.trim(), instructions: instructions.trim(), format: 'poster' } })
      onConcepts(p.project_id)
    } catch (e) { setErr(msg(e)) } finally { setBusy(false) }
  }
  return (
    <Card title={title ?? (both ? 'Your idea (poster first, then a reel from it)' : 'Your idea')}>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormRow label="Project name" help={hint('name')}>{a => <Field id={a.id} aria-describedby={a.describedBy} value={name} onChange={e => { setName(e.target.value); touch('name') }} placeholder="e.g. Reading day" />}</FormRow>
        <FormRow label="Language of the headline">{a => <Select id={a.id} className="w-full" value={language} onChange={e => setLanguage(e.target.value as 'te' | 'en')}>
          <option value="te">Telugu</option><option value="en">English</option></Select>}</FormRow>
        <div className="sm:col-span-2"><FormRow label="Topic" help={hint('topic', 'The main message. It becomes the headline, exactly as typed.')}>{a =>
          <Field id={a.id} aria-describedby={a.describedBy} value={topic} onChange={e => { setTopic(e.target.value); touch('topic') }} className={language === 'te' ? 'te' : undefined} placeholder={language === 'te' ? 'e.g. చదువుల పండుగ' : 'e.g. Reading day'} />}</FormRow></div>
        <FormRow label="Purpose" help={hint('purpose', 'What should people do or feel?')}>{a => <Field id={a.id} aria-describedby={a.describedBy} value={purpose} onChange={e => { setPurpose(e.target.value); touch('purpose') }} placeholder="e.g. Invite families" />}</FormRow>
        <FormRow label="Audience" help={hint('audience')}>{a => <Field id={a.id} aria-describedby={a.describedBy} value={audience} onChange={e => { setAudience(e.target.value); touch('audience') }} placeholder="e.g. Parents in Guntur" />}</FormRow>
        <div className="sm:col-span-2"><FormRow label="Instructions and limits" help={hint('instructions', 'For example: no prices, no invented facts.')}>{a =>
          <TextArea id={a.id} aria-describedby={a.describedBy} rows={2} value={instructions} onChange={e => { setInstructions(e.target.value); touch('instructions') }} />}</FormRow></div>
        <div className="sm:col-span-2"><FormRow label="Brand kit" help="Only approved brands with current rights can be used.">{a =>
          <Select id={a.id} aria-describedby={a.describedBy} className="w-full" value={brand} onChange={e => setBrand(e.target.value)}>
            <option value="">No brand kit</option>
            {usable.map(v => <option key={v.hash} value={v.hash}>{v.name} (approved v{v.revision})</option>)}
            {unavailable.map(b => <option key={b.hash} value="" disabled>{b.name}: not available, rights not reviewed and approved</option>)}
          </Select>}</FormRow></div>
      </div>
      <label className="mt-4 flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={ack} onChange={e => setAck(e.target.checked)} />
        <span>This poster keeps its brief and brand linked to it. Older M5 Studio versions cannot open posters like this.</span></label>
      {both && <Notice tone="info" className="mt-3">After you choose a concept and save the poster, use "Make a reel from this poster" in the editor.</Notice>}
      <Btn className="mt-4" busy={busy} disabled={!ready} onClick={start}>Continue to concepts</Btn>
      {!ready && <p className="mt-2 text-xs text-ink-3">{need.length ? `Still needed: ${need.map(k => FIELD_LABEL[k]).join(', ')}${ack ? '.' : ', and the confirmation above.'}` : 'Tick the confirmation above to continue.'}</p>}
      {err && <Notice tone="error" className="mt-3">{err}</Notice>}
    </Card>
  )
}
