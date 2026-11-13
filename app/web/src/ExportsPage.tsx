// M7-B B4B-2: where finished files are. Read-only: reel exports come from the reel list (count per reel) and open
// in that reel's own Exports step; poster draft exports come from M5's overview (folder, revision, formats).
import { useEffect, useState } from 'react'
import { api, type ProjectRow } from './api'
import { creative, type PosterExportRow } from './creative'
import { posterHref, reelHref } from './projects-logic'
import { Card, Notice, PageHead, Pill, Spinner } from './ui'

const msg = (e: unknown) => (e as Error).message
const STATE: Record<PosterExportRow['state'], string> = { draft: 'Draft', partial: 'Incomplete', 'review-required': 'Needs review' }

export function ExportsPage() {
  const [reels, setReels] = useState<ProjectRow[] | null>(null); const [reelErr, setReelErr] = useState<string | null>(null)
  const [posters, setPosters] = useState<PosterExportRow[] | null>(null); const [posterErr, setPosterErr] = useState<string | null>(null)
  useEffect(() => {
    api.projects(false).then(r => setReels(r.filter(x => x.exports > 0))).catch(e => setReelErr(msg(e)))
    creative.overview().then(n => setPosters(n.exports)).catch(e => setPosterErr(msg(e)))
  }, [])
  return (
    <div className="space-y-6">
      <PageHead title="Exports" sub="Files saved on this Mac. Nothing is published or approved by IDEAFRAME." />
      <Card title="Reel exports">
        {reelErr ? <Notice tone="error">Reel exports could not be loaded. {reelErr}</Notice> : !reels ? <p className="flex items-center gap-2 text-sm text-ink-3"><Spinner />Loading reel exports…</p>
          : !reels.length ? <p className="text-sm text-ink-3">No reel has been rendered yet.</p>
          : <ul className="divide-y divide-line">{reels.map(r => <li key={r.name} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-2 text-sm">
            <a href={reelHref(r.name)} className="min-w-0 flex-1 truncate font-medium hover:underline">{r.name}<span className="sr-only">, open its exports</span></a>
            <span className="text-xs text-ink-2">{r.exports} file{r.exports === 1 ? '' : 's'}</span><span className="text-xs text-ink-3">Reel changed {r.modified}</span></li>)}</ul>}
        <p className="mt-3 text-xs text-ink-3">Open a reel to play, check and download its videos, covers and QA sheets.</p>
      </Card>
      <Card title="Poster draft exports">
        {posterErr ? <Notice tone="error">Poster exports could not be loaded. {posterErr}</Notice> : !posters ? <p className="flex items-center gap-2 text-sm text-ink-3"><Spinner />Loading poster exports…</p>
          : !posters.length ? <p className="text-sm text-ink-3">No poster has been exported yet. Use the Export step in a poster.</p>
          : <ul className="divide-y divide-line">{posters.map(x => <li key={x.id} className="py-2 text-sm">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1"><span className="font-medium">{x.id}</span><Pill ok={x.state === 'draft' ? null : false}>{STATE[x.state]}</Pill>
              {x.revision !== null && <span className="text-xs text-ink-2">Revision {x.revision} · {x.png_sha256 ? 'SVG and PNG' : 'SVG'}</span>}
              {x.poster ? <a href={posterHref(x.poster.project_id)} className="text-xs text-link hover:underline">Poster: {x.poster.name} · exported {x.poster.at}</a> : <span className="text-xs text-ink-3">Poster not recorded (exported before 13 Nov 2026)</span>}</div>
            <code className="mt-0.5 block break-all text-xs text-ink-3">{x.directory}</code></li>)}</ul>}
        <p className="mt-3 text-xs text-ink-3">These are draft files, not approved artwork. Newer exports name the poster they came from.</p>
      </Card>
    </div>
  )
}
