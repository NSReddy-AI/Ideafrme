// M7-A: Brand Studio - review content brands, record the owner's rights decision per asset, approve a brand version.
// Rules stay in M5's Brand Library (server side): rights are append-only, approval needs every asset cleared, an approval
// pins each asset's rights record, and a later rights change makes that approval out of date.
import { useCallback, useEffect, useState } from 'react'
import { brands, cleared, DESTINATIONS, SCOPES, type AssetRow, type BrandRow, type Destination, type Library, type Rights, type Scope } from './brands'
import { Btn, Card, Err, Field, MOTION, PageHead, Pill, Select, cx } from './ui'

const msg = (e: unknown) => (e as Error).message
const mb = (n: number) => n >= 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`
const day = (iso: string | null) => (iso ? iso.slice(0, 10) : '—')

export function BrandStudio() {
  const [lib, setLib] = useState<Library | null>(null); const [sel, setSel] = useState<string | null>(null); const [err, setErr] = useState<string | null>(null)
  const load = useCallback(() => brands.list().then(l => { setLib(l); setSel(s => s ?? l.brands[0]?.record.brand_id ?? null) }).catch(e => setErr(msg(e))), [])
  useEffect(() => { load() }, [load])
  const brand = lib?.brands.find(b => b.record.brand_id === sel) ?? null
  return (
    <div className="space-y-6">
      <PageHead title="Brand Studio" sub="Content brands for posters and reels. Record rights for every asset, then approve a brand version." />
      <Err msg={err} />
      {!lib ? <p className="text-sm text-ink-3">{err ? 'Brand Library unavailable.' : 'Loading…'}</p>
        : !lib.brands.length ? <p className="text-sm text-ink-3">No brands in the Library yet. Import the M4 brands with tools/m6_brands.py.</p>
        : <div className="grid gap-6 lg:grid-cols-[16rem_minmax(0,1fr)]">
          <nav aria-label="Brands" className="space-y-1">
            {lib.brands.map(b => <button key={b.record.brand_id} onClick={() => setSel(b.record.brand_id)} aria-pressed={sel === b.record.brand_id}
              className={cx('w-full rounded-field px-3 py-2 text-left text-sm', MOTION, sel === b.record.brand_id ? 'bg-act-subtle text-link' : 'hover:bg-raised')}>
              <div className="font-medium">{b.record.payload.name}</div>
              <div className="mt-1"><State b={b} /></div></button>)}
          </nav>
          {brand && <BrandDetail key={brand.hash} b={brand} lib={lib} reload={load} />}
        </div>}
    </div>
  )
}

function State({ b }: { b: BrandRow }) {
  if (b.record.state === 'approved') return b.approval_current ? <Pill ok>Approved v{b.record.revision}</Pill> : <Pill ok={false}>Approval out of date</Pill>
  return <Pill>Draft v{b.record.revision}</Pill>
}

function BrandDetail({ b, lib, reload }: { b: BrandRow; lib: Library; reload: () => void }) {
  const p = b.record.payload
  const assets = p.asset_ids.map(id => lib.assets.find(a => a.record.id === id)).filter((a): a is AssetRow => !!a)
  const review = assets.filter(a => !a.eligibility.eligible)
  const reelReady = assets.every(a => cleared(a.rights, 'commercial_design', 'reel'))
  const [open, setOpen] = useState<string | null>(null)
  const [reviewer, setReviewer] = useState(''); const [ack, setAck] = useState(false); const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const run = async (f: () => Promise<unknown>) => { setBusy(true); setErr(null); try { await f(); reload() } catch (e) { setErr(msg(e)) } finally { setBusy(false) } }
  return (
    <div className="min-w-0 space-y-4">
      <Card title={p.name} right={<State b={b} />}>
        <div className="flex flex-wrap gap-2" aria-label="Brand colours">{p.colors.map(c => <span key={c} className="flex items-center gap-1 text-xs text-ink-2">
          <span className="h-5 w-5 rounded-chip ring-1 ring-line" style={{ background: c }} />{c}</span>)}</div>
        {p.mandatory_rules.length > 0 && <div className="mt-4"><h3 className="text-xs font-semibold text-ink-3">MANDATORY RULES</h3>
          <ul className="mt-1 list-disc pl-5 text-sm">{p.mandatory_rules.map((r, i) => <li key={i}>{r}</li>)}</ul></div>}
        {p.preferences.length > 0 && <p className="mt-3 text-xs text-ink-2">{p.preferences.join(' · ')}</p>}
        <p className="mt-3 text-xs text-ink-3">{p.notes}</p>
        {b.record.state === 'approved' && <p className="mt-3 text-xs text-ink-2">Approved by {b.record.reviewer} on {day(b.record.approved_at)}.</p>}
      </Card>

      <Card title={`Assets and rights (${assets.length})`} right={<span className="text-xs text-ink-3">{assets.length - review.length} of {assets.length} cleared for review · reel export {reelReady ? 'ready' : 'not cleared'}</span>}>
        <p className="mb-3 text-xs text-ink-2">Rights are your legal statements. Record who holds them, your evidence, what they allow and until when. Every decision is kept; nothing is overwritten.</p>
        <ul className="divide-y divide-line">
          {assets.map(a => <li key={a.record.id} className="py-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="min-w-0 flex-1 truncate text-sm font-medium" title={a.record.sha256}>{a.record.name.replace(/__/g, '/')}</span>
              <span className="text-xs text-ink-3">{a.record.kind} · {mb(a.record.bytes)}</span>
              <RightsPill r={a.rights} />
              <Btn kind="quiet" onClick={() => setOpen(open === a.record.id ? null : a.record.id)} aria-expanded={open === a.record.id}>{open === a.record.id ? 'Close' : 'Record rights'}</Btn>
            </div>
            {a.rights?.status === 'granted' && <p className="mt-1 text-xs text-ink-2">{a.rights.authority} · until {day(a.rights.expires)} · {a.rights.scopes.join(', ')} → {a.rights.destinations.join(', ')}</p>}
            {open === a.record.id && <RightsForm a={a} onDone={() => { setOpen(null); reload() }} />}
          </li>)}
        </ul>
      </Card>

      <Card title="Approve this brand version">
        {b.record.state === 'approved' && b.approval_current ? <p className="text-sm text-ok">This version is approved and every asset's rights are still current.</p>
          : b.record.state === 'approved' ? <div className="space-y-2 text-sm">
              <p className="text-warn">A rights decision changed after approval, so this approval no longer counts. Start a new revision and approve it again.</p>
              <Btn kind="ghost" disabled={busy} onClick={() => run(() => brands.revise(b))}>Start new revision</Btn></div>
          : <div className="space-y-3 text-sm">
              {review.length > 0 && <p className="text-warn">{review.length} asset{review.length > 1 ? 's' : ''} not cleared for internal preview and library records yet. Approval stays blocked until each has a current grant.</p>}
              <label className="block text-xs text-ink-2">Reviewer<Field value={reviewer} onChange={e => setReviewer(e.target.value)} placeholder="Your name" /></label>
              <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={ack} onChange={e => setAck(e.target.checked)} />
                I reviewed this brand, its rules and every asset's rights.</label>
              <Btn disabled={busy || !ack || !reviewer.trim() || review.length > 0} onClick={() => run(() => brands.approve(b, reviewer.trim()))}>Approve version {b.record.revision}</Btn>
            </div>}
        <Err msg={err} />
      </Card>
    </div>
  )
}

function RightsPill({ r }: { r: Rights | null }) {
  if (!r || r.status === 'unknown') return <Pill>Rights unknown</Pill>
  if (r.status === 'denied') return <Pill ok={false}>Denied</Pill>
  return r.expires && Date.parse(r.expires) > Date.now() ? <Pill ok>Granted</Pill> : <Pill ok={false}>Grant expired</Pill>
}

function RightsForm({ a, onDone }: { a: AssetRow; onDone: () => void }) {
  const cur = a.rights
  const [status, setStatus] = useState<Rights['status']>(cur?.status === 'granted' ? 'granted' : 'denied')
  const [authority, setAuthority] = useState(''); const [evidence, setEvidence] = useState('')
  const [scopes, setScopes] = useState<Scope[]>([]); const [dests, setDests] = useState<Destination[]>([]); const [until, setUntil] = useState('')
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)
  const toggle = <T,>(list: T[], v: T) => (list.includes(v) ? list.filter(x => x !== v) : [...list, v])
  const grant = status === 'granted'
  const ready = !grant || (authority.trim() && evidence.trim() && scopes.length && dests.length && until)
  const save = async () => {
    setBusy(true); setErr(null)
    const rights: Rights = grant ? { status, authority: authority.trim(), evidence: evidence.trim(), scopes, destinations: dests, expires: `${until}T23:59:59Z` }
      : { status, authority: authority.trim(), evidence: evidence.trim(), scopes: [], destinations: [], expires: null }
    try { await brands.rights(a, rights); onDone() } catch (e) { setErr(msg(e)) } finally { setBusy(false) }
  }
  return (
    <div className="mt-3 space-y-3 rounded-field border border-line bg-surface p-3 text-sm">
      <label className="block text-xs text-ink-2">Decision<Select className="w-full" value={status} onChange={e => setStatus(e.target.value as Rights['status'])}>
        <option value="denied">Not allowed (denied)</option><option value="granted">Allowed (granted)</option><option value="unknown">Not known yet</option></Select></label>
      <label className="block text-xs text-ink-2">Who holds the rights{grant ? '' : ' (optional)'}<Field value={authority} onChange={e => setAuthority(e.target.value)} placeholder="e.g. the channel owner, the party, the photographer" /></label>
      <label className="block text-xs text-ink-2">Evidence{grant ? '' : ' (optional)'}<textarea value={evidence} onChange={e => setEvidence(e.target.value)} rows={2}
        className="mt-1 w-full rounded-field border border-line-strong bg-raised p-2 text-sm text-ink" placeholder="e.g. written permission dated …, own photograph, licence file name" /></label>
      {grant && <>
        <fieldset><legend className="text-xs text-ink-2">Allowed uses</legend><div className="mt-1 flex flex-wrap gap-3">
          {SCOPES.map(([k, t]) => <label key={k} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={scopes.includes(k)} onChange={() => setScopes(toggle(scopes, k))} />{t}</label>)}</div></fieldset>
        <fieldset><legend className="text-xs text-ink-2">Allowed outputs</legend><div className="mt-1 flex flex-wrap gap-3">
          {DESTINATIONS.map(([k, t]) => <label key={k} className="flex items-center gap-1 text-xs"><input type="checkbox" checked={dests.includes(k)} onChange={() => setDests(toggle(dests, k))} />{t}</label>)}</div></fieldset>
        <label className="block text-xs text-ink-2">Valid until<Field type="date" value={until} onChange={e => setUntil(e.target.value)} min={new Date().toISOString().slice(0, 10)} /></label>
        <p className="text-xs text-ink-3">Approving a brand needs Internal preview + Library records. Posters need Commercial design + Posters; reel export needs Commercial design + Reels.</p>
      </>}
      <div className="flex gap-2"><Btn disabled={busy || !ready} onClick={save}>Record decision</Btn></div>
      <Err msg={err} />
    </div>
  )
}
