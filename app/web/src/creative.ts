// Thin client for the M5 poster routes on the M6 server (app/creative.py). Every call goes to the local server only.
export type View = { id: string; width: number; height: number; language: 'en' | 'te' }
export type Layer = {
  id: string; type: 'text' | 'shape'; view_id: string; content_id?: string
  x: number; y: number; width: number; height: number
  style: { fill: string; font_size?: number; shape?: 'rectangle' | 'ellipse' }
}
export type Content = { id: string; text: string; language: 'en' | 'te'; kind: string }
export type PosterProject = {
  project_id: string; name: string; revision: number; view: View; elements: Layer[]; content: Content[]
  can_undo: boolean; can_redo: boolean; saved: boolean; dirty: boolean
  remaining_text_slots: { en: number; te: number }; element_limit: number; history_version: number; binding: unknown
}
export type PosterRow = { project_id: string; name: string; dirty: boolean; saved: boolean }
export type Box = { id: string; element_id: string; x: number; y: number; width: number; height: number; type: string }
export type Scene = { project_id: string; revision: number; svg: string; svg_sha256: string; boxes: Box[]; profile: Record<string, unknown>; fonts: Record<string, string> }
export type Face = { family: string; weight: number; hash: string; uri: string; notice: string }
export type QACheck = { name: string; level: 'error' | 'warning'; passed: boolean; element_id: string; detail: string }
export type PosterQA = { passed: boolean; errors: number; warnings: number; checks: QACheck[]; revision: number; fonts_checked: boolean; rules: Record<string, number> }
export type ExportReceipt = { directory: string; manifest: { svg_sha256: string; png_sha256: string | null; revision: number } }

// Step 6: approved reel words (app/approved_content.py) and where they sit on a poster.
export type ApprovedItem = { id: string; kind: 'hook' | 'quote' | 'headline' | 'tag' | 'number' | 'post' | 'script'; text: string; language: 'en' | 'te'; verbatim: boolean; sha256: string }
export type ApprovedDoc = { format: string; source: { project: string; brand: string }; approvals: { type: 'plan' | 'narration' | 'project'; hash: string | null }[]; items: ApprovedItem[]; fingerprint: string }
export type ReelRow = { project: string; ok: boolean; approvals?: string[]; items?: number; code?: string; detail?: string }
export type ContentLink = { element_id: string; content_id: string; reel: string; item_id: string; kind: string; ok: boolean; detail: string }

export type Brief = { purpose: string; topic: string; audience: string; format: 'poster'; instructions: string }
export type Binding = { hash: string; published_head: string; record: { brief: Brief; brand: { record: { payload: { name: string; mandatory_rules: string[] } } } | null } }
export type ConceptRequest = { project_id: string; expected_revision: number; expected_binding: string; expected_head: string; seed: number; acknowledge_brief: true }
export type ConceptBundle = { mode: string; digest: string; rules: string[]; instructions: string; warnings: string[]; concepts: import('./concepts-logic').ConceptPlan[] }

/** A refused request keeps M5's error code, so the screen can react to e.g. "upgrade-required" or "conflict". */
export class CreativeError extends Error {
  code: string; status: number
  constructor(code: string, message: string, status: number) { super(message); this.code = code; this.status = status }
}

// M7-A: plain-language explanations for refusals a person can act on. The server's own detail is kept after it.
const FRIENDLY: Record<string, string> = {
  conflict: 'This poster changed somewhere else (another window or tab). The latest version is loaded; please repeat your change.',
  stale: 'The poster changed while it was being exported. Nothing was saved; export again.',
  timeout: 'The export took too long and was stopped. Nothing was saved; export again.',
  lock: 'Another IDEAFRAME window or server is already using this poster session. Close the other one, then reload this page.',
  'recovery-required': 'This poster has an interrupted save. Its original files are kept safe; it needs explicit recovery before more editing.',
  'durability-blocked': 'The disk could not confirm the save. Nothing was changed; check free space and try again.',
  internal: 'Something went wrong on this Mac. Nothing was changed; try again, and if it repeats, restart the app.',
}
const explain = (code: string, detail: string) => (FRIENDLY[code] ? `${FRIENDLY[code]} (${detail})` : detail)

async function call<T>(method: 'GET' | 'POST', url: string, body?: unknown): Promise<T> {
  let r: Response
  try { r = await fetch(url, { method, headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined, body: body !== undefined ? JSON.stringify(body) : undefined }) }
  catch { throw new CreativeError('offline', 'The local IDEAFRAME server is not answering. Start it again with the launcher, then reload this page.', 0) }
  const data = await r.json().catch(() => ({}))
  if (!r.ok) { const code = data.error ?? 'request'; throw new CreativeError(code, explain(code, typeof data.detail === 'string' ? data.detail : `request failed (${r.status})`), r.status) }
  return data as T
}
const at = (p: PosterProject) => ({ project_id: p.project_id, expected_revision: p.revision })

export const creative = {
  list: () => call<{ projects: PosterRow[] }>('GET', '/api/creative/projects').then(r => r.projects),
  view: (id: string) => call<{ project: PosterProject }>('GET', `/api/creative/projects/${encodeURIComponent(id)}`).then(r => r.project),
  create: (b: { name: string; text: string; language: 'en' | 'te' }) => call<{ project: PosterProject }>('POST', '/api/creative/projects', b).then(r => r.project),
  action: (p: PosterProject, action: string, extra: Record<string, unknown> = {}) =>
    call<{ project: PosterProject }>('POST', '/api/creative/action', { ...at(p), action, ...extra }).then(r => r.project),
  fonts: () => call<{ fonts: Record<string, Face> | null; error: string | null }>('GET', '/api/creative/fonts'),
  scene: (p: PosterProject) => call<Scene>('POST', '/api/creative/scene', at(p)),
  qa: (p: PosterProject) => call<PosterQA>('POST', '/api/creative/qa', at(p)),
  exportBegin: (p: PosterProject) => call<{ token: string; scene: Scene }>('POST', '/api/creative/export/begin', at(p)),
  exportFinish: (b: { token: string; revision: number; png: string | null; qa: { fonts_loaded: boolean; overflow: string[]; parity: boolean; embedded_fonts: boolean } }) =>
    call<ExportReceipt>('POST', '/api/creative/export/finish', b),
  exportCancel: () => call<{ cancelled: boolean }>('POST', '/api/creative/export/cancel', {}),
  approvedReels: () => call<{ reels: ReelRow[] }>('GET', '/api/creative/approved/reels').then(r => r.reels),
  approvedReel: (name: string) => call<ApprovedDoc>('GET', `/api/creative/approved/reels/${encodeURIComponent(name)}`),
  insertApproved: (p: PosterProject, doc: ApprovedDoc, item: ApprovedItem) =>
    call<{ project: PosterProject; link: ContentLink }>('POST', '/api/creative/approved/insert', { ...at(p), reel: doc.source.project, item_id: item.id, expected_fingerprint: doc.fingerprint }),
  toReel: (p: PosterProject, b: { brand: string; platform: string; style: string; slug: string }) =>
    call<{ project: string; slides: number; script: string[]; script_approved: boolean }>('POST', '/api/creative/to-reel', { ...at(p), ...b }),
  // M7-B B2: brief -> three concepts -> chosen draft (M5 binding workflow and deterministic Creative Director)
  eligibleBrands: () => call<{ versions: { hash: string; brand_id: string; revision: number; name: string; eligible: boolean; reason: string }[] }>('GET', '/api/creative/workflow/brands').then(r => r.versions),
  createFromBrief: (b: { name: string; text: string; language: 'en' | 'te'; brief: Brief; brand_hash: string | null; acknowledge: boolean }) =>
    call<{ project: PosterProject }>('POST', '/api/creative/workflow/create', b).then(r => r.project),
  concepts: (r: ConceptRequest) => call<ConceptBundle>('POST', '/api/creative/director/generate', r),
  chooseConcept: (source: ConceptRequest, bundle: ConceptBundle, concept_id: string) =>
    call<{ project: PosterProject; bundle_digest: string; concept_id: string; approved: boolean }>('POST', '/api/creative/director/select', { source, bundle_digest: bundle.digest, concept_id, acknowledge_rules: true }),
  links: (p: PosterProject) => call<{ links: ContentLink[] }>('GET', `/api/creative/approved/links/${encodeURIComponent(p.project_id)}`).then(r => r.links),
}
