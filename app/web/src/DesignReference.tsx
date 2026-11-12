// M7-B B1: one page showing every shared component in every state, in the app's real tokens (light, dark and the dark
// editor surface). For review and visual checks; it changes nothing and saves nothing.
import { useState } from 'react'
import { Btn, Card, Field, FormRow, Notice, PageHead, Pill, Select, Spinner, Tabs, TextArea, useConfirm, useToast } from './ui'

function Section({ editor, children }: { editor: boolean; children: React.ReactNode }) {
  return editor ? <div data-surface="editor" className="space-y-6 rounded-sheet bg-canvas p-6 text-ink">{children}</div> : <div className="space-y-6">{children}</div>
}

export function DesignReference() {
  const confirm = useConfirm(); const toast = useToast()
  const [tab, setTab] = useState<'light' | 'editor'>('light'); const [answer, setAnswer] = useState<string>('—')
  const [name, setName] = useState('')
  return (
    <div className="space-y-6">
      <PageHead title="Component reference" sub="Every shared component and state, drawn with the IDEAFRAME tokens. Nothing on this page is saved." />
      <Tabs label="Surface" value={tab} onChange={setTab} tabs={[{ id: 'light', label: 'App surface' }, { id: 'editor', label: 'Editor surface (dark)' }]} />
      <Section editor={tab === 'editor'}>
        <Card title="Buttons">
          <div className="flex flex-wrap items-center gap-3">
            <Btn>Primary</Btn><Btn kind="ghost">Secondary</Btn><Btn kind="quiet">Quiet</Btn><Btn kind="danger">Destructive</Btn>
            <Btn busy>Exporting…</Btn><Btn disabled>Disabled</Btn><Btn kind="ghost" disabled>Disabled</Btn>
          </div>
          <p className="mt-3 text-xs text-ink-3">Hover to see the hover state, press for a slight press-down, or use Tab to see the keyboard focus ring. A busy button shows progress and blocks repeat clicks.</p>
        </Card>
        <Card title="Form controls">
          <div className="grid gap-4 sm:grid-cols-2">
            <FormRow label="Poster name" help="Shown in Projects.">{a => <Field id={a.id} aria-describedby={a.describedBy} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Reading day" />}</FormRow>
            <FormRow label="Short name" error="Use letters, numbers and _ only.">{a => <Field id={a.id} aria-describedby={a.describedBy} invalid={a.invalid} defaultValue="tools poster!" />}</FormRow>
            <FormRow label="Language">{a => <Select id={a.id} className="w-full" defaultValue="te"><option value="te">Telugu</option><option value="en">English</option></Select>}</FormRow>
            <FormRow label="Disabled field" help="Explains why when it matters.">{a => <Field id={a.id} aria-describedby={a.describedBy} disabled value="Locked baseline" readOnly />}</FormRow>
            <div className="sm:col-span-2"><FormRow label="Script">{a => <TextArea id={a.id} rows={2} className="te" defaultValue="అక్కచెల్లెమ్మలకు 31 లక్షల ఇళ్ల పట్టాలు." />}</FormRow></div>
          </div>
        </Card>
        <Card title="Status">
          <div className="flex flex-wrap gap-2"><Pill ok>Approved</Pill><Pill ok={false}>Approval out of date</Pill><Pill>Draft v1</Pill><span className="inline-flex items-center gap-2 text-sm text-ink-2"><Spinner label="Loading" /> Loading…</span></div>
          <div className="mt-4 space-y-2">
            <Notice tone="info">Concepts are made by layout rules on this Mac.</Notice>
            <Notice tone="success">Draft exported.</Notice>
            <Notice tone="warning" title="Check:">Drawn text is 10 px from the left edge (keep 64 px).</Notice>
            <Notice tone="error" title="Export blocked:">approved reel words no longer match their approval.</Notice>
          </div>
        </Card>
        <Card title="Dialog and toasts">
          <div className="flex flex-wrap items-center gap-3">
            <Btn kind="danger" onClick={async () => setAnswer((await confirm({ title: 'Remove this layer?', body: 'You can bring it back with Undo.', confirmLabel: 'Remove layer', tone: 'danger' })) ? 'confirmed' : 'cancelled')}>Open confirm dialog</Btn>
            <span className="text-sm text-ink-2" aria-live="polite">Last answer: {answer}</span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Btn kind="ghost" onClick={() => toast('success', 'Draft exported (SVG and PNG).')}>Success toast</Btn>
            <Btn kind="ghost" onClick={() => toast('info', 'Working offline. Nothing is uploaded.')}>Info toast</Btn>
            <Btn kind="ghost" onClick={() => toast('warning', 'Brand rights not cleared for reels yet.')}>Warning toast</Btn>
            <Btn kind="ghost" onClick={() => toast('error', 'The local server is not answering. Nothing was changed.')}>Error toast (stays)</Btn>
          </div>
          <p className="mt-3 text-xs text-ink-3">Dialog: Escape cancels, focus stays inside and returns to the button. Toasts pause while hovered or focused; errors stay until dismissed.</p>
        </Card>
      </Section>
    </div>
  )
}
