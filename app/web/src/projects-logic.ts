// M7-B B4B-2: one Projects list from the data that already exists (no React, no DOM), unit-tested in
// tests/web/test_projects_logic.mjs. Nothing here is invented: a row only shows fields its source provides, and a
// poster-reel link exists only when the reel carries the converter's own record (build/conversion.json,
// written by app/poster_to_reel.py). Similar names or dates never make a link.

export type ReelSource = { name: string; brand?: string; status?: string; mode: 'speaker' | 'slides'; steps_done?: number; modified?: string; exports?: number; archived?: boolean }
export type PosterSource = { project_id: string; name: string; dirty: boolean; saved: boolean }
export type Link = { reel: string; posterId: string; posterName: string; revision: number | null; created: string | null }
export type Filter = 'all' | 'poster' | 'reel' | 'both'
export type Item = {
  key: string; kind: 'poster' | 'reel'; title: string; href: string
  status: string            // from the source's own state
  modified: string | null   // reels only: the poster list carries no date
  facts: string[]           // short supported facts, e.g. "slides reel", "3 exports"
  linked: { label: string; href: string | null }[]   // recorded poster-reel relationships
}

/** Reads a reel's conversion record. Anything that is not the converter's exact record for this reel gives null. */
export function parseLink(reel: string, raw: unknown): Link | null {
  if (!raw || typeof raw !== 'object') return null
  const v = raw as Record<string, unknown>; const p = v.poster as Record<string, unknown> | undefined
  if (v.format !== 'ideaframe-poster-to-reel@1' || v.project !== reel || !p || typeof p.project_id !== 'string' || !p.project_id) return null
  return { reel, posterId: p.project_id, posterName: typeof p.name === 'string' ? p.name : '', revision: typeof p.revision === 'number' ? p.revision : null, created: typeof v.created === 'string' ? v.created : null }
}

const plural = (n: number, w: string) => `${n} ${w}${n === 1 ? '' : 's'}`
export const reelHref = (name: string) => `#/p/${encodeURIComponent(name)}`
export const posterHref = (id: string) => `#/poster/${encodeURIComponent(id)}`

export function combine(reels: ReelSource[], posters: PosterSource[], links: Link[]): Item[] {
  const posterIds = new Set(posters.map(p => p.project_id)); const reelNames = new Set(reels.map(r => r.name))
  const live = links.filter(l => reelNames.has(l.reel))
  const reelItems: Item[] = reels.map(r => {
    const l = live.find(x => x.reel === r.name)
    return { key: `reel:${r.name}`, kind: 'reel', title: r.name, href: reelHref(r.name), modified: r.modified ?? null,
      status: r.archived ? 'Archived' : r.status ? `Status: ${r.status}` : 'Reel',   // the reel's own status word; its next step is shown inside the reel
      facts: [r.mode === 'speaker' ? 'speaker reel' : 'slides reel', ...(r.brand ? [`reel brand ${r.brand}`] : []), ...(typeof r.steps_done === 'number' ? [`${plural(r.steps_done, 'step')} done`] : []), ...(typeof r.exports === 'number' ? [plural(r.exports, 'export')] : [])],
      linked: l ? [{ label: posterIds.has(l.posterId) ? `Made from poster "${l.posterName || l.posterId}"${l.revision !== null ? ` (revision ${l.revision})` : ''}` : `Made from a poster that is not in this poster library${l.posterName ? ` ("${l.posterName}")` : ''}`,
        href: posterIds.has(l.posterId) ? posterHref(l.posterId) : null }] : [] }
  })
  const posterItems: Item[] = posters.map(p => ({ key: `poster:${p.project_id}`, kind: 'poster', title: p.name, href: posterHref(p.project_id), modified: null,
    status: p.dirty ? 'Unsaved changes' : p.saved ? 'Saved' : 'Not saved yet', facts: [],
    linked: live.filter(l => l.posterId === p.project_id).map(l => ({ label: `Reel made from it: ${l.reel}`, href: reelHref(l.reel) })) }))
  // dated rows first (newest first, as the reel list gives them), then posters by name: the poster list has no dates to sort by
  return [...reelItems, ...[...posterItems].sort((a, b) => a.title.localeCompare(b.title))]
}

export const matches = (i: Item, f: Filter) => f === 'all' || (f === 'both' ? i.linked.length > 0 : i.kind === f)
export const counts = (items: Item[]): Record<Filter, number> => ({ all: items.length, poster: items.filter(i => i.kind === 'poster').length, reel: items.filter(i => i.kind === 'reel').length, both: items.filter(i => i.linked.length > 0).length })
export const EMPTY: Record<Filter, string> = { all: 'No projects yet.', poster: 'No posters yet.', reel: 'No reels yet.', both: 'No poster has a reel made from it yet. Use "Make a reel from this poster" in the poster editor.' }
