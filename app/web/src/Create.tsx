// M7-B B2: one place to start - idea and brief, output (Poster / Reel / Both), brand kit.
// Posters (and "Both") start through M5's brief workflow, so the next step can offer three concepts.
// Reels keep the existing M4 reel steps (passed in as reelForm).
import { useEffect, useState } from 'react'
import { brands as brandApi, type BrandRow } from './brands'
import { creative } from './creative'
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

function BriefForm({ both, onConcepts }: { both: boolean; onConcepts: (id: string) => void }) {
  const [name, setName] = useState(''); const [topic, setTopic] = useState(''); const [purpose, setPurpose] = useState('')
  const [audience, setAudience] = useState(''); const [instructions, setInstructions] = useState(''); const [language, setLanguage] = useState<'te' | 'en'>('te')
  const [brand, setBrand] = useState(''); const [ack, setAck] = useState(false); const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const [eligible, setEligible] = useState<{ hash: string; name: string; revision: number; eligible: boolean; reason: string }[] | null>(null)
  const [drafts, setDrafts] = useState<BrandRow[]>([])
  useEffect(() => {
    creative.eligibleBrands().then(setEligible).catch(() => setEligible([]))
    brandApi.list().then(l => setDrafts(l.brands.filter(b => b.record.state !== 'approved' || !b.approval_current))).catch(() => {})
  }, [])
  const usable = (eligible ?? []).filter(v => v.eligible)
  const ready = name.trim() && topic.trim() && purpose.trim() && audience.trim() && ack   // the concept step refuses a brief without purpose and audience
  const start = async () => {
    setBusy(true); setErr(null)
    try {
      const p = await creative.createFromBrief({ name: name.trim(), text: topic.trim(), language, acknowledge: true, brand_hash: brand || null,
        brief: { topic: topic.trim(), purpose: purpose.trim(), audience: audience.trim(), instructions: instructions.trim(), format: 'poster' } })
      onConcepts(p.project_id)
    } catch (e) { setErr(msg(e)) } finally { setBusy(false) }
  }
  return (
    <Card title={both ? 'Your idea (poster first, then a reel from it)' : 'Your idea'}>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormRow label="Project name">{a => <Field id={a.id} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Reading day" />}</FormRow>
        <FormRow label="Language of the headline">{a => <Select id={a.id} className="w-full" value={language} onChange={e => setLanguage(e.target.value as 'te' | 'en')}>
          <option value="te">Telugu</option><option value="en">English</option></Select>}</FormRow>
        <div className="sm:col-span-2"><FormRow label="Topic" help="The main message. It becomes the headline.">{a =>
          <Field id={a.id} aria-describedby={a.describedBy} value={topic} onChange={e => setTopic(e.target.value)} className={language === 'te' ? 'te' : undefined} placeholder={language === 'te' ? 'e.g. చదువుల పండుగ' : 'e.g. Reading day'} />}</FormRow></div>
        <FormRow label="Purpose" help="What should people do or feel?">{a => <Field id={a.id} aria-describedby={a.describedBy} value={purpose} onChange={e => setPurpose(e.target.value)} placeholder="e.g. Invite families" />}</FormRow>
        <FormRow label="Audience">{a => <Field id={a.id} value={audience} onChange={e => setAudience(e.target.value)} placeholder="e.g. Parents in Guntur" />}</FormRow>
        <div className="sm:col-span-2"><FormRow label="Instructions and limits" help="For example: no prices, no invented facts.">{a =>
          <TextArea id={a.id} aria-describedby={a.describedBy} rows={2} value={instructions} onChange={e => setInstructions(e.target.value)} />}</FormRow></div>
        <div className="sm:col-span-2"><FormRow label="Brand kit" help="Only approved brands with current rights can be used.">{a =>
          <Select id={a.id} aria-describedby={a.describedBy} className="w-full" value={brand} onChange={e => setBrand(e.target.value)}>
            <option value="">No brand kit</option>
            {usable.map(v => <option key={v.hash} value={v.hash}>{v.name} (approved v{v.revision})</option>)}
            {drafts.map(b => <option key={b.hash} value="" disabled>{b.record.payload.name}: not available, rights not reviewed and approved</option>)}
          </Select>}</FormRow></div>
      </div>
      <label className="mt-4 flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={ack} onChange={e => setAck(e.target.checked)} />
        <span>This poster keeps its brief and brand linked to it. Older M5 Studio versions cannot open posters like this.</span></label>
      {both && <Notice tone="info" className="mt-3">After you choose a concept and save the poster, use "Make a reel from this poster" in the editor.</Notice>}
      <Btn className="mt-4" busy={busy} disabled={!ready} onClick={start}>Continue to concepts</Btn>
      {!ready && <p className="mt-2 text-xs text-ink-3">Needs a project name, topic, purpose, audience and the confirmation above.</p>}
      {err && <Notice tone="error" className="mt-3">{err}</Notice>}
    </Card>
  )
}
