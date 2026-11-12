// Thin client for app/server.py. Every call goes to the local server only.
export type Catalog = {
  brands: { id: string; name: string; handle: string; language: string; default_style: string; default_platforms: string[] }[]
  platforms: { id: string; name: string }[]
  styles: { id: string; name: string }[]
  voices: Record<string, string>
  narration_styles: string[]
  speeds: number[]
  providers: Record<string, boolean>
}
export type ProjectRow = {
  name: string; brand: string; platform: string; style: string; status: string; narration?: string
  archived?: boolean; mode: 'speaker' | 'slides'; steps_done: number; next: string; modified: string; exports: number
}
export type QA = {
  passed: boolean; duration: number; loudness: number; true_peak: number
  checks: { name: string; passed: boolean; detail: string }[]; warnings: string[]; contact_sheet: string | null
}
export type ExportItem = { platform: string; file: string; size_mb: number; cover: string | null; post: string | null; qa: QA | null; created: string }
export type PlanSummary = {
  markdown?: string; approved: boolean; hook_choice?: string; error?: string
  options: Record<string, { line1: string; line2: string; line3: string; headline: string[]; source?: string }>
  cards: { number: string; label?: string }[]; tag?: unknown; problems: string[]; marked: string[]
}
export type ScriptLine = { text: string; say: string; numbers: { text: string; say: string; check: string; why?: string }[]; length?: { too_long?: boolean; est_speech_s?: number } }
export type Project = {
  name: string; locked?: boolean; archived?: boolean; language?: string; mode: 'speaker' | 'slides'; done: string[]; next: string; inputs: string[]; notes: string
  project: Record<string, any>; transcript: boolean; edit: string | null; edit_layout: any
  exports: { version: number; outputs: ExportItem[] }[]
  plan?: PlanSummary
  words?: { i: number; w: string; s: number; e: number; review: boolean; w_asr?: string | null }[]
  script?: { review: string; approved: boolean; approved_hash?: string; lines: ScriptLine[] }
  narration_ready?: boolean | null; narration_problem?: { code: string; message: string } | null
  narration_check?: { cer_total: number; to_check: any[] }
  narration_audio?: { file: string; duration: number; memory?: { peak_rss_gb?: number; limit_gb?: number }; voice?: string; style?: string; speed?: number }
}
export type JobEvent = { event: string; pct?: number; step?: string; platform?: string; code?: string; message?: string; [k: string]: any }
export type Job = {
  id: string; project: string; action: string; status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled'; pct: number
  events: JobEvent[]; n_events: number; result?: JobEvent; ok?: boolean; seconds?: number; peak_rss_gb?: number | null; created: number
}

async function call<T>(method: string, url: string, body?: unknown, raw?: BodyInit): Promise<T> {
  const r = await fetch(url, {
    method,
    headers: raw ? { 'Content-Type': 'application/octet-stream' } : body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: raw ?? (body !== undefined ? JSON.stringify(body) : undefined),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `request failed (${r.status})`)
  return data as T
}
const P = (n: string) => `/api/projects/${encodeURIComponent(n)}`
export const api = {
  catalog: () => call<Catalog>('GET', '/api/catalog'),
  projects: (all = false) => call<ProjectRow[]>('GET', `/api/projects${all ? '?all=true' : ''}`),
  create: (b: { brand: string; platform: string; style: string; slug: string }) => call<Project>('POST', '/api/projects', b),
  project: (n: string) => call<Project>('GET', P(n)),
  patch: (n: string, b: { video?: string; brief?: string; notes?: string; face_x?: number; archived?: boolean }) => call<Project>('PATCH', P(n), b),
  captions: (n: string, fixes: Record<number, string>) => call<Project>('PUT', `${P(n)}/captions`, { fixes }),
  title: (n: string, b: { line1: string; line2: string; line3: string; tag_top: string; tag_bottom: string; headline: string[] }) => call<Project>('PUT', `${P(n)}/title`, b),
  upload: (n: string, f: File, kind: 'video' | 'slide' | 'recording' | 'title_person' | 'title_bg' | 'file') =>
    call<Project>('POST', `${P(n)}/upload?kind=${kind}&filename=${encodeURIComponent(f.name)}`, undefined, f),
  narration: (n: string, b: { mode: string; voice?: string; style?: string; speed?: number; file?: string }) => call<Project>('POST', `${P(n)}/narration`, b),
  script: (n: string, text: string) => call<Project>('POST', `${P(n)}/script`, { text }),
  approveScript: (n: string, checked: boolean) => call<Project>('POST', `${P(n)}/script/approve`, { checked }),
  job: (n: string, b: { action: string; choice?: string; checked?: boolean; hook?: string; platforms?: string[] }) => call<Job>('POST', `${P(n)}/jobs`, b),
  jobStatus: (id: string, since = 0) => call<Job>('GET', `/api/jobs/${id}?since=${since}`),
  cancel: (id: string) => call<Job>('POST', `/api/jobs/${id}/cancel`),
  removeInput: (n: string, f: string) => call<Project>('DELETE', `${P(n)}/inputs/${encodeURIComponent(f)}`),
  check: () => call<Record<string, any>>('GET', '/api/check'),
  sourceFrame: (n: string, t: number) => `${P(n)}/source_frame?t=${t}&r=${Date.now()}`,
  jobs: (project?: string) => call<Job[]>('GET', `/api/jobs${project ? `?project=${encodeURIComponent(project)}` : ''}`),
}
export const fileUrl = (rel: string | null | undefined) => (rel ? `/files/${rel.split('/').map(encodeURIComponent).join('/')}` : '')
