// Pure UI behaviour (no React, no DOM) so it can be unit-tested with plain Node: tests/web/test_ui_logic.mjs.

/** Roving focus for tabs and segmented controls (WAI-ARIA tabs pattern): arrows wrap, Home/End jump. */
export function nextTab(index: number, key: string, count: number): number | null {
  if (count < 1) return null
  if (key === 'ArrowRight' || key === 'ArrowDown') return (index + 1) % count
  if (key === 'ArrowLeft' || key === 'ArrowUp') return (index - 1 + count) % count
  if (key === 'Home') return 0
  if (key === 'End') return count - 1
  return null
}

export type Tone = 'info' | 'success' | 'warning' | 'error'

/** Toasts: errors stay until dismissed (Bible: never let critical text vanish); others leave after a delay. */
export function toastLifetime(tone: Tone): number | null {
  return tone === 'error' ? null : tone === 'warning' ? 8000 : 5000
}

/** Words + a symbol for every tone, so state is never shown by colour alone. */
export const TONE_LABEL: Record<Tone, { symbol: string; word: string }> = {
  info: { symbol: 'i', word: 'Note' }, success: { symbol: '✓', word: 'Done' },
  warning: { symbol: '!', word: 'Check' }, error: { symbol: '×', word: 'Problem' },
}
