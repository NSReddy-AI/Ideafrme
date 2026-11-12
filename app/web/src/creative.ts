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

/** A refused request keeps M5's error code, so the screen can react to e.g. "upgrade-required" or "conflict". */
export class CreativeError extends Error {
  code: string; status: number
  constructor(code: string, message: string, status: number) { super(message); this.code = code; this.status = status }
}

async function call<T>(method: 'GET' | 'POST', url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, { method, headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined, body: body !== undefined ? JSON.stringify(body) : undefined })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new CreativeError(data.error ?? 'request', typeof data.detail === 'string' ? data.detail : `request failed (${r.status})`, r.status)
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
}
