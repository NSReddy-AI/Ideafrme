// M7-B B4C-3: the capability list, from a real check of this Mac. Used on Home (short) and in Settings (with every answer).
import { useEffect, useState } from 'react'
import { STATE_LABEL, facets, fetchCapabilities, stateOf, usable, type CapabilityReport } from './capabilities'
import { Btn, Notice, cx } from './ui'

export function CapabilityList({ detailed = false }: { detailed?: boolean }) {
  const [r, setR] = useState<CapabilityReport | null>(null); const [err, setErr] = useState<string | null>(null); const [n, setN] = useState(0)
  useEffect(() => { let live = true; fetchCapabilities().then(x => { if (live) { setR(x); setErr(null) } }).catch(e => { if (live) setErr((e as Error).message) }); return () => { live = false } }, [n])
  if (err) return <Notice tone="error">The status of this Mac could not be read, so nothing is shown as available. {err}</Notice>
  if (!r) return <p role="status" className="text-sm text-ink-3">Checking this Mac…</p>
  return (
    <div>
      <ul className="divide-y divide-line">
        {r.capabilities.map(c => { const s = stateOf(c); return <li key={c.id} className="py-2">
          <div className="grid gap-x-4 gap-y-0.5 sm:grid-cols-[1fr_11rem]">
            <div><span className="font-medium">{c.label}</span><span className="block text-xs text-ink-2">{c.detail}</span></div>
            <span className={cx('text-xs font-semibold sm:text-right', usable(c) ? 'text-ok' : s === 'failed' ? 'text-bad' : 'text-ink-3')}>{STATE_LABEL[s]}</span>
          </div>
          {detailed && <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-ink-3">{facets(c).map(([k, v]) => <div key={k} className="flex gap-1"><dt>{k}:</dt><dd className="text-ink-2">{v}</dd></div>)}
            {c.source && <div className="basis-full"><dt className="sr-only">Based on</dt><dd>{c.source}</dd></div>}</dl>}
        </li> })}
      </ul>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-ink-3">
        <span>Checked on this Mac at {r.checked}. Local is the default; nothing is sent online to check.</span>
        {detailed && <Btn kind="quiet" onClick={() => setN(x => x + 1)}>Check again</Btn>}
      </div>
      {detailed && <p className="mt-1 text-xs text-ink-3">Local model server: {r.local.reachable ? `answering, models ${r.local.models.join(', ') || 'none'}${r.local.loaded.length ? `; in memory now: ${r.local.loaded.join(', ')}` : ''}` : r.local.error ?? 'not answering'}.</p>}
    </div>
  )
}
