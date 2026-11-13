// Recorded poster-to-reel links, read from each slides reel's own conversion record (build/conversion.json, written by
// app/poster_to_reel.py and served by the existing /files route). No file, or anything else, means no link.
import { fileUrl } from './api'
import { parseLink, type Link, type ReelSource } from './projects-logic'

export async function readLinks(reels: ReelSource[]): Promise<Link[]> {
  const found = await Promise.all(reels.filter(r => r.mode === 'slides').map(async r => {
    try { const res = await fetch(fileUrl(`projects/${r.name}/build/conversion.json`)); return res.ok ? parseLink(r.name, await res.json()) : null } catch { return null }
  }))
  return found.filter((l): l is Link => l !== null)
}
