// M7-B B4B-1: Home with the Omnibar. A prompt is read by fixed rules (intent-logic.ts), shown back as an editable
// interpretation, and only then handed to the existing brief form and M5 workflow (Create.tsx BriefForm). Nothing is
// created, translated or approved from the prompt alone, and no model reads it.
import { useEffect, useRef, useState } from 'react'
import { useBrandChoices } from './brand-choices'
import { CAPABILITIES, STATE_LABEL } from './capabilities'
import { BriefForm } from './Create'
import { interpret, matchBrand, type Interpretation, type Note, type Output } from './intent-logic'
import { Btn, Card, MOTION, Notice, Select, Tabs, cx } from './ui'

const OUTPUTS: { id: Output; label: string }[] = [{ id: 'poster', label: 'Poster' }, { id: 'reel', label: 'Reel' }, { id: 'both', label: 'Both' }]
const EXAMPLES = ['Poster for Reading Day, to invite families. For parents in Guntur.', 'చదువుల పండుగ పోస్టర్']
const SCRIPT_NOTE: Record<Interpretation['script'], string> = {
  te: 'Telugu text found. It is used exactly as you typed it; nothing is translated.',
  mixed: 'Telugu and English text found. Each is used exactly as you typed it; nothing is translated.',
  en: 'English text found. It is used exactly as you typed it; nothing is translated.', none: '',
}
const hasTelugu = (s: string) => /[ఀ-౿]/.test(s)

export function Home({ reelForm, onConcepts }: { reelForm: React.ReactNode; onConcepts: (id: string) => void }) {
  const [prompt, setPrompt] = useState(''); const [output, setOutput] = useState<Output>('poster'); const [chose, setChose] = useState(false)
  const [brand, setBrand] = useState(''); const [read, setRead] = useState<{ it: Interpretation; brand: string; brandNote: Note | null } | null>(null)
  const { usable, unavailable } = useBrandChoices()
  const box = useRef<HTMLTextAreaElement>(null); const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => { if (read) heading.current?.focus() }, [read])

  const submit = () => {
    if (!prompt.trim()) return
    const it = interpret(prompt, chose ? output : null)
    const named = matchBrand(prompt, usable, unavailable.map(b => b.name))
    setOutput(it.output.value); setRead({ it, brand: brand || named.hash || '', brandNote: brand ? null : named.note })
  }
  const back = () => { setRead(null); requestAnimationFrame(() => box.current?.focus()) }
  const key = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {   // Enter continues, Shift+Enter makes a new line; never during Telugu (IME) composition
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) { e.preventDefault(); submit() }
  }

  if (read) {
    const { it } = read
    const notes = [...it.notes, ...(read.brandNote ? [read.brandNote] : [])]
    return (
      <div className="space-y-6">
        <div>
          <h1 ref={heading} tabIndex={-1} className="font-head text-2xl font-semibold tracking-tight outline-none!">Check what IDEAFRAME understood</h1>
          <p className="mt-1 text-sm text-ink-2">Fixed rules read your words. No AI model was used. Correct anything below before a project is created.</p>
        </div>
        <Card title="Your request" right={<Btn kind="quiet" onClick={back}>Change the request</Btn>}>
          <blockquote className={cx('whitespace-pre-wrap border-l-2 border-line-strong pl-3 text-sm', hasTelugu(it.original) && 'te')}>{it.original}</blockquote>
          {SCRIPT_NOTE[it.script] && <p className="mt-2 text-xs text-ink-3">{SCRIPT_NOTE[it.script]}</p>}
        </Card>
        {notes.map(n => <Notice key={n.code} tone={n.code === 'ambiguous-output' || n.code === 'brand-unavailable' ? 'warning' : 'info'}>{n.text}</Notice>)}
        <div className="flex flex-wrap items-center gap-3">
          <Tabs label="What to make" value={output} onChange={setOutput} tabs={OUTPUTS} />
          <span className="text-xs text-ink-3">{it.output.source === 'typed' ? (chose ? 'You chose this.' : 'Your words asked for this.') : it.output.source === 'missing' ? 'Please choose.' : 'Poster is the starting choice. Change it if you meant something else.'}</span>
        </div>
        {output === 'reel' ? <>
          <Notice tone="info">Reels start from your own video, pictures or recording, and use the reel brands in Reels. Nothing is rendered until you approve the plan or script there. Your request above is not copied into the reel; add what you need as notes after creating it.</Notice>
          {reelForm}
        </> : <BriefForm both={output === 'both'} onConcepts={onConcepts} title={output === 'both' ? 'Your brief (poster first, then a reel from it)' : 'Your brief'}
          initial={{ name: it.name.value, topic: it.topic.value, purpose: it.purpose.value, audience: it.audience.value, instructions: it.instructions.value, language: it.language, brand: read.brand }}
          sources={{ name: it.name.source, topic: it.topic.source, purpose: it.purpose.source, audience: it.audience.source, instructions: it.instructions.value ? it.instructions.source : undefined }} />}
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="mx-auto max-w-3xl pt-4 text-center md:pt-12">
        <h1 className="font-head text-3xl font-semibold tracking-tight md:text-4xl">What would you like to make?</h1>
        <p className="mt-3 text-base text-ink-2">Describe it in Telugu or English. You check everything before anything is created.</p>
      </div>

      <div className="mx-auto max-w-3xl">
        <div className="group relative">
          {/* brand moment: a soft glow around the box, never behind the text */}
          <div aria-hidden className="pointer-events-none absolute -inset-0.5 rounded-sheet opacity-25 blur-md transition-opacity duration-[var(--motion-panel)] ease-[var(--ease-out)] group-focus-within:opacity-70 motion-reduce:transition-none" style={{ background: 'var(--brand-gradient)' }} />
          <div className="relative rounded-sheet border border-line bg-raised p-3 shadow-lift">
            <label htmlFor="omnibar" className="sr-only">Describe what you want to make</label>
            <textarea id="omnibar" ref={box} rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={key} aria-describedby="omnibar-help"
              placeholder="e.g. Poster for Reading Day, to invite families. For parents in Guntur."
              className={cx('block w-full resize-none rounded-field bg-transparent px-3 py-2 text-lg text-ink placeholder:text-ink-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus', hasTelugu(prompt) && 'te')} />
            <div className="mt-2 flex flex-wrap items-center gap-3 px-1">
              <Tabs label="What to make" value={output} onChange={v => { setOutput(v); setChose(true) }} tabs={OUTPUTS} />
              <label className="flex min-w-0 items-center gap-2 text-sm text-ink-2">Brand kit
                <Select value={brand} onChange={e => setBrand(e.target.value)} className="max-w-56">
                  <option value="">No brand kit</option>
                  {usable.map(v => <option key={v.hash} value={v.hash}>{v.name} (approved v{v.revision})</option>)}
                  {unavailable.map(b => <option key={b.hash} value="" disabled>{b.name}: not available, rights not reviewed</option>)}
                </Select></label>
              <span className="ml-auto" />
              <Btn disabled={!prompt.trim()} onClick={submit}>Continue</Btn>
            </div>
          </div>
        </div>
        <p id="omnibar-help" className="mt-3 text-center text-xs text-ink-3">Press Enter to continue, Shift+Enter for a new line. If your words name a poster or a reel, that is used unless you choose one here.</p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-sm">
          <span className="text-ink-3">Try:</span>
          {EXAMPLES.map(x => <button key={x} onClick={() => { setPrompt(x); box.current?.focus() }} className={cx('max-w-full truncate rounded-btn border border-line bg-raised px-3 py-1.5 text-ink-2 hover:border-line-strong hover:text-ink', MOTION, hasTelugu(x) && 'te')}>{x}</button>)}
          <a href="#/create" className="ml-1 text-link hover:underline">Advanced Create</a>
        </div>
      </div>

      <details className="mx-auto max-w-3xl rounded-box border border-line bg-raised px-4 py-3 text-sm">
        <summary className={cx('cursor-pointer font-medium', MOTION)}>What this build can and cannot do</summary>
        <ul className="mt-3 divide-y divide-line">
          {CAPABILITIES.map(c => <li key={c.id} className="grid gap-x-4 gap-y-0.5 py-2 sm:grid-cols-[1fr_8rem]">
            <div><span className="font-medium">{c.label}</span><span className="block text-xs text-ink-2">{c.detail}</span></div>
            <span className={cx('text-xs font-semibold sm:text-right', c.state === 'available' ? 'text-ok' : 'text-ink-3')}>{STATE_LABEL[c.state]}</span></li>)}
        </ul>
        <p className="mt-2 text-xs text-ink-3">Everything runs on this Mac. The status of local tools and models is in <a href="#/settings" className="text-link hover:underline">Settings</a>.</p>
      </details>
    </div>
  )
}
