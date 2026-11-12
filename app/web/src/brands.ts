// Client for M5's Brand Library routes on the M6 server (/api/brands/*). Every decision here is the owner's:
// the screen records what the owner enters and never proposes or pre-fills a rights grant.
import { CreativeError } from './creative'

export type Scope = 'internal_preview' | 'commercial_design' | 'redistribute' | 'template_use' | 'font_embed'
export type Destination = 'poster' | 'reel' | 'library_metadata'
export type Rights = { status: 'unknown' | 'granted' | 'denied'; authority: string; evidence: string; scopes: Scope[]; destinations: Destination[]; expires: string | null; previous?: string | null }
export type AssetRow = {
  hash: string; rights_hash: string | null
  record: { id: string; name: string; kind: string; sha256: string; bytes: number; provenance: { owner: string; source: string; license: string } }
  rights: Rights | null; eligibility: { eligible: boolean; reason: string }
}
export type BrandRow = {
  hash: string; current_review_eligible?: boolean; approval_current?: boolean
  record: { brand_id: string; revision: number; parent: string | null; state: 'draft' | 'approved'; reviewer: string; approved_at: string | null
    payload: { name: string; colors: string[]; typography: { english: string; telugu: string }; mandatory_rules: string[]; preferences: string[]; inspiration: string[]; notes: string; asset_ids: string[] } }
}
export type Library = { brands: BrandRow[]; assets: AssetRow[]; initialized: boolean }

export const SCOPES: [Scope, string][] = [['internal_preview', 'Internal preview'], ['commercial_design', 'Commercial design'], ['template_use', 'Template use'], ['font_embed', 'Font embedding'], ['redistribute', 'Redistribution']]
export const DESTINATIONS: [Destination, string][] = [['poster', 'Posters'], ['reel', 'Reels'], ['library_metadata', 'Library records']]

async function call<T>(method: 'GET' | 'POST', url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, { method, headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined, body: body !== undefined ? JSON.stringify(body) : undefined })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new CreativeError(data.error ?? 'request', typeof data.detail === 'string' ? data.detail : `request failed (${r.status})`, r.status)
  return data as T
}

export const brands = {
  list: () => call<Library>('GET', '/api/brands'),
  rights: (asset: AssetRow, rights: Rights) => call<{ rights_hash: string }>('POST', '/api/brands/action', { action: 'rights', asset_id: asset.record.id, expected_rights: asset.rights_hash, rights }),
  revise: (b: BrandRow) => call<BrandRow>('POST', '/api/brands/action', { action: 'save', brand_id: b.record.brand_id, expected_head: b.hash, payload: b.record.payload }),
  approve: (b: BrandRow, reviewer: string) => call<BrandRow>('POST', '/api/brands/action', { action: 'approve', brand_id: b.record.brand_id, expected_head: b.hash, reviewer, acknowledge: true }),
}

/** Same rule as the Library's eligibility: granted, scope and destination listed, not expired. */
export function cleared(r: Rights | null, scope: Scope, destination: Destination, now = Date.now()) {
  return !!r && r.status === 'granted' && r.scopes.includes(scope) && r.destinations.includes(destination) && !!r.expires && Date.parse(r.expires) > now
}
