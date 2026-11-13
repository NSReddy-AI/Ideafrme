// M7-B B4B-2: one Projects page for posters, reels and recorded poster-to-reel pairs. It only reads what exists:
// the reel list (/api/projects), the poster list (/api/creative/projects) and each slides reel's own conversion
// record (served by /files). It opens projects in their existing editor or workflow and changes nothing.
import { useEffect, useState } from 'react'
import { api } from './api'
import { readLinks } from './project-links'
import { creative } from './creative'
import { EMPTY, combine, counts, matches, type Filter, type Item, type Link, type PosterSource, type ReelSource } from './projects-logic'
import { Btn, MOTION, Notice, PageHead, Pill, Spinner, Tabs, cx } from './ui'

const msg = (e: unknown) => (e as Error).message
type Loaded<T> = { rows: T[]; error: string | null }

export function ProjectsPage() {
  const [filter, setFilter] = useState<Filter>('all'); const [showAll, setShowAll] = useState(false)
  const [reels, setReels] = useState<Loaded<ReelSource> | null>(null); const [posters, setPosters] = useState<Loaded<PosterSource> | null>(null); const [links, setLinks] = useState<Link[]>([])
  useEffect(() => {
    let live = true
    api.projects(showAll).then(async rows => { if (!live) return; setReels({ rows, error: null }); const l = await readLinks(rows); if (live) setLinks(l) })
      .catch(e => { if (live) setReels({ rows: [], error: msg(e) }) })
    creative.list().then(rows => { if (live) setPosters({ rows, error: null }) }).catch(e => { if (live) setPosters({ rows: [], error: msg(e) }) })
    return () => { live = false }
  }, [showAll])

  const loading = !reels || !posters
  const items = loading ? [] : combine(reels.rows, posters.rows, links)
  const n = counts(items); const shown = items.filter(i => matches(i, filter))
  const down = !loading && !!reels.error && !!posters.error
  return (
    <div>
      <PageHead title="Projects" sub="Every poster and reel on this Mac. Opening one takes you to its own editor or steps." />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Tabs label="Show" value={filter} onChange={setFilter} tabs={[{ id: 'all', label: `All (${n.all})` }, { id: 'poster', label: `Poster (${n.poster})` }, { id: 'reel', label: `Reel (${n.reel})` }, { id: 'both', label: `Both (${n.both})` }]} />
        <label className="flex items-center gap-2 text-xs text-ink-2"><input type="checkbox" checked={showAll} onChange={e => setShowAll(e.target.checked)} />Show test and archived reels</label>
      </div>
      <p role="status" className="sr-only">{loading ? 'Loading projects' : `${shown.length} project${shown.length === 1 ? '' : 's'} shown`}</p>

      {loading ? <p className="flex items-center gap-2 text-sm text-ink-3"><Spinner />Loading projects…</p>
        : down ? <Notice tone="error" title="The project lists could not be loaded.">The local IDEAFRAME server is not answering. Start it again with the launcher, then reload this page. ({reels.error})</Notice>
        : <>
          {reels.error && <Notice tone="error" className="mb-3" title="Reels could not be loaded.">{reels.error} Posters are still listed.</Notice>}
          {posters.error && <Notice tone="error" className="mb-3" title="Posters could not be loaded.">{posters.error} Reels are still listed.</Notice>}
          {!shown.length ? <div className="rounded-box border border-line bg-raised px-4 py-8 text-center text-sm text-ink-2">
            <p>{EMPTY[items.length ? filter : 'all']}</p>
            <div className="mt-3 flex justify-center gap-2">{filter !== 'all' && items.length > 0 && <Btn kind="ghost" onClick={() => setFilter('all')}>Show all projects</Btn>}<a href="#/" className="inline-flex min-h-[var(--control-height)] items-center text-link hover:underline">Start from Home</a></div>
          </div>
            : <ul className="divide-y divide-line overflow-hidden rounded-box border border-line bg-raised">{shown.map(i => <Row key={i.key} i={i} />)}</ul>}
          {filter === 'both' && <p className="mt-3 text-xs text-ink-3">"Both" lists a poster and a reel only when the reel carries the record written by "Make a reel from this poster". Similar names are never treated as a link.</p>}
          <p className="mt-3 text-xs text-ink-3">Posters have no saved date in their data, so they are listed by name after the reels. <a href="#/posters" className="text-link hover:underline">Plain poster without a brief</a></p>
        </>}
    </div>
  )
}

function Row({ i }: { i: Item }) {
  return (
    <li className={cx('px-4 py-3 hover:bg-act-subtle', MOTION)}>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <a href={i.href} className="min-w-0 flex-1 truncate font-medium hover:underline">{i.title}<span className="sr-only">, open {i.kind}</span></a>
        <Pill ok={null}>{i.kind === 'poster' ? 'Poster' : 'Reel'}</Pill>
        <span className="text-xs text-ink-2">{i.status}</span>
        {i.modified && <span className="text-xs text-ink-3">Changed {i.modified}</span>}
      </div>
      {(i.facts.length > 0 || i.linked.length > 0) && <div className="mt-0.5 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-ink-3">
        {i.facts.length > 0 && <span>{i.facts.join(' · ')}</span>}
        {i.linked.map(l => l.href ? <a key={l.label} href={l.href} className="text-link hover:underline">{l.label}</a> : <span key={l.label}>{l.label}</span>)}
      </div>}
    </li>
  )
}
