// M7-B B3: what the Export step shows (no React, no DOM), unit-tested in tests/web/test_export_logic.mjs.
// These rules only DESCRIBE the gates the editor already had; they never loosen them. The server's export
// handshake (app/creative.py + M5) stays authoritative and refuses on its own: approved-text errors, stale
// revisions, overflow, PNG parity and font qualification.

export type ReadinessInput = {
  locked: boolean            // an edit or an export is in progress
  current: boolean           // the preview matches the poster's latest revision
  previewErr: string | null
  overflow: number           // layers whose text overflows its box (M5 inspectScene)
  wordsBlocked: boolean      // approved reel words no longer match their approval
  qaKnown: boolean           // poster QA has answered for this revision
  errors: number             // other QA errors (advisory here; shown, not hidden)
  warnings: number
  fontsReady: boolean        // pinned fonts loaded in this browser
  pngOk: boolean             // M5's probe says PNG output can be trusted here
  pngNote: string            // the probe's own explanation
}
export type ItemState = 'ok' | 'blocked' | 'advisory' | 'pending'
export type Item = { id: string; label: string; state: ItemState; detail: string }
export type Gate = { allowed: boolean; reason: string | null }

export function readiness(i: ReadinessInput): { items: Item[]; svg: Gate; png: Gate } {
  const items: Item[] = [
    i.previewErr ? { id: 'preview', label: 'Preview', state: 'blocked', detail: i.previewErr }
      : i.current ? { id: 'preview', label: 'Preview', state: 'ok', detail: 'Matches the latest revision.' }
      : { id: 'preview', label: 'Preview', state: 'pending', detail: 'Updating the preview…' },
    { id: 'fonts', label: 'Pinned fonts', state: i.fontsReady ? 'ok' : 'pending', detail: i.fontsReady ? 'Inter Bold and Noto Sans Telugu Black loaded.' : 'Loading pinned fonts…' },
    i.overflow > 0 ? { id: 'overflow', label: 'Text fits its boxes', state: 'blocked', detail: i.overflow > 1 ? `${i.overflow} layers have text that overflows or overlaps. Fix them in Edit.` : 'One layer has text that overflows or overlaps. Fix it in Edit.' }
      : { id: 'overflow', label: 'Text fits its boxes', state: i.current ? 'ok' : 'pending', detail: i.current ? 'No overflow or overlapping lines.' : 'Checked when the preview is current.' },
    i.wordsBlocked ? { id: 'approved', label: 'Approved words', state: 'blocked', detail: 'Approved reel words were changed. Undo the edit, or insert the approved line again.' }
      : { id: 'approved', label: 'Approved words', state: i.qaKnown ? 'ok' : 'pending', detail: i.qaKnown ? 'Any approved reel words match their approval.' : 'Checking…' },
    !i.qaKnown ? { id: 'qa', label: 'Poster QA', state: 'pending', detail: 'Checking…' }
      : { id: 'qa', label: 'Poster QA', state: i.errors || i.warnings ? 'advisory' : 'ok',
        detail: i.errors || i.warnings ? `${count(i.errors, 'error')}, ${count(i.warnings, 'warning')}. Review them in Edit before you share the poster.` : 'All checks pass.' },
    { id: 'png', label: 'PNG output', state: i.pngOk ? 'ok' : i.fontsReady ? 'advisory' : 'pending', detail: i.pngNote },
  ]
  const svgReason = i.locked ? 'Wait for the current action to finish.'
    : !i.current ? 'The preview is not current yet.'
    : i.overflow > 0 ? 'Text overflows its box.'
    : i.wordsBlocked ? 'Approved reel words were changed.'
    : null
  const svg = { allowed: svgReason === null, reason: svgReason }
  const png = { allowed: svg.allowed && i.pngOk, reason: svgReason ?? (i.pngOk ? null : 'PNG is not available in this browser.') }
  return { items, svg, png }
}

const count = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`

/** Export progress, in the order exportDraft runs it. */
export const PHASES = [
  { id: 'begin', label: 'Asking the server for the exact poster' },
  { id: 'check', label: 'Checking fonts and text fit in this browser' },
  { id: 'raster', label: 'Drawing the PNG and comparing it pixel for pixel' },
  { id: 'save', label: 'Saving and verifying the files' },
] as const
export type Phase = (typeof PHASES)[number]['id']

/** The files M5 writes into an export folder (m5/visual_poster_studio/exports.py). */
export function savedFiles(directory: string, png: boolean): string[] {
  const d = directory.replace(/\/+$/, '')
  return [`${d}/poster.draft.svg`, ...(png ? [`${d}/poster.draft.png`] : []), `${d}/manifest.json`]
}
