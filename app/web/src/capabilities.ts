// M7-B B4C-3: capability states for the screen (no React). The facts come from the server (app/capabilities.py:
// providers.json, the local model server on this Mac, the environment, local tool folders). This file only turns the
// seven separate answers into one honest headline, and never rounds an unknown up to "ready".
export type Qualified = 'yes' | 'no' | 'not-assessed'
export type Capability = {
  id: string; label: string; runner: 'rules' | 'local-model' | 'online' | 'none'; detail: string; source: string | null
  installed: boolean | null; configured: boolean | null; available: boolean; qualified: Qualified
  running: boolean; failed: boolean; unsupported: boolean; off: boolean
}
export type CapabilityReport = { checked: string; default: string; local: { reachable: boolean; error: string | null; models: string[]; loaded: string[]; wanted: string[] }; capabilities: Capability[] }
export type CapabilityState = 'unsupported' | 'failed' | 'off' | 'not-qualified' | 'running' | 'available' | 'installed' | 'not-configured' | 'not-installed'

/** One headline per capability. Order matters: a reason it cannot be used always wins over a reason it could. */
export function stateOf(c: Capability): CapabilityState {
  if (c.unsupported) return 'unsupported'
  if (c.failed) return 'failed'
  if (c.off) return 'off'
  if (c.qualified === 'no') return 'not-qualified'
  if (c.available) return c.running ? 'running' : 'available'
  if (c.installed === true) return 'installed'
  if (c.runner === 'online') return 'not-configured'
  return 'not-installed'
}
export const STATE_LABEL: Record<CapabilityState, string> = {
  unsupported: 'Unsupported', failed: 'Check failed', off: 'Switched off', 'not-qualified': 'Not qualified', running: 'Running now',
  available: 'Available', installed: 'Installed, not usable yet', 'not-configured': 'Not configured', 'not-installed': 'Not installed',
}
export const usable = (c: Capability) => { const s = stateOf(c); return s === 'available' || s === 'running' }
const yn = (v: boolean | null) => (v === null ? 'not known' : v ? 'yes' : 'no')
/** The seven separate answers, in plain words, for the detailed view. */
export function facets(c: Capability): [string, string][] {
  if (c.unsupported) return [['Unsupported', 'yes: not part of this build']]
  return [['Installed', c.runner === 'rules' ? 'yes (part of the app)' : c.runner === 'online' ? 'not applicable (online service)' : yn(c.installed)], ['Configured', yn(c.configured)],
    ['Available', c.off ? 'no (switched off)' : yn(c.available)], ['Qualified', c.qualified === 'yes' ? 'yes' : c.qualified === 'no' ? 'no' : 'not assessed'],
    ['Running', yn(c.running)], ['Failed', c.failed ? 'yes: the health check failed' : 'no']]
}
export async function fetchCapabilities(): Promise<CapabilityReport> {
  const r = await fetch('/api/capabilities'); if (!r.ok) throw Error(`the capability check failed (${r.status})`)
  return r.json()
}
