// M7-B B4B-1: what this build can and cannot do, in one typed list (no React, no storage, no provider routing).
// Every entry is grounded in something that exists in this repository, or is explicitly marked as not available.
// The list is descriptive only: it never switches a capability on. A later orchestrator can read the same type.

export type CapabilityState =
  | 'available'      // works in this build without a model
  | 'needs-check'    // exists, but depends on local tools whose health is shown in Settings > system check
  | 'off'            // exists in the engine but is switched off in providers.json
  | 'unavailable'    // not in this build
export type CapabilityRunner = 'rules' | 'local-model' | 'online' | 'none'
export type Capability = { id: string; label: string; state: CapabilityState; runner: CapabilityRunner; detail: string }

export const CAPABILITIES: Capability[] = [
  { id: 'intent.rules', label: 'Reading your prompt', state: 'available', runner: 'rules', detail: 'Fixed rules pick out what you typed. No AI model reads the prompt.' },
  { id: 'poster.concepts.rules', label: 'Three poster concepts', state: 'available', runner: 'rules', detail: 'Arranged by layout rules on this Mac.' },
  { id: 'poster.edit-export', label: 'Poster editing, QA and SVG/PNG export', state: 'available', runner: 'rules', detail: 'Telugu and English with pinned fonts.' },
  { id: 'reel.workflow', label: 'Reels from your own video, pictures or recording', state: 'needs-check', runner: 'local-model', detail: 'Uses local tools and models. Their status is in Settings.' },
  { id: 'poster.concepts.ai', label: 'AI poster concepts', state: 'unavailable', runner: 'none', detail: 'The local model has not passed qualification for posters.' },
  { id: 'language.translation', label: 'Translation', state: 'unavailable', runner: 'none', detail: 'Text is used exactly as you type it.' },
  { id: 'media.generated-images', label: 'Generated pictures', state: 'unavailable', runner: 'none', detail: 'Posters are built from text and shapes.' },
  { id: 'provider.web-bridge', label: 'Web Bridge', state: 'unavailable', runner: 'none', detail: 'Not built. Nothing is sent online.' },
  { id: 'provider.pro-api', label: 'Paid online models', state: 'off', runner: 'online', detail: 'Switched off. Posters never use them.' },
]
export const STATE_LABEL: Record<CapabilityState, string> = { available: 'Works here', 'needs-check': 'See Settings', off: 'Switched off', unavailable: 'Not available' }
