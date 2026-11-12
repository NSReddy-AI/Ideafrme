// Pure helpers for the Concepts screen (no React, no DOM), unit-tested in tests/web/test_concepts_logic.mjs.

export type PlanLayer = { id: string; type: 'shape' | 'text'; x: number; y: number; width: number; height: number;
  style: { fill: string; shape?: 'rectangle' | 'ellipse'; font_size?: number }; text?: string }
export type ConceptPlan = { id: string; name: string; rationale: string; composition: string; emphasis?: string[]; layers: PlanLayer[] }

const esc = (s: string) => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!))
const safeColour = (c: string) => (/^#[0-9a-fA-F]{6}$/.test(c) ? c : 'none')   // proposal data only: anything else is not painted

/** A comparison sketch of one concept, drawn from its layers with M5's text metrics (baseline 1.02, line height 1.65)
 *  and the pinned font families. The editor shows the exact server-rendered poster after a concept is chosen. */
export function conceptSvg(plan: ConceptPlan, width = 1080, height = 1350): string {
  const parts = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(plan.name)}">`]
  for (const l of plan.layers) {
    const fill = safeColour(l.style.fill)
    if (l.type === 'shape') {
      parts.push(l.style.shape === 'ellipse'
        ? `<ellipse cx="${l.x + l.width / 2}" cy="${l.y + l.height / 2}" rx="${l.width / 2}" ry="${l.height / 2}" fill="${fill}"/>`
        : `<rect x="${l.x}" y="${l.y}" width="${l.width}" height="${l.height}" fill="${fill}"/>`)
    } else {
      const size = l.style.font_size ?? 48
      const lines = (l.text ?? '').split('\n')
      parts.push(`<text font-size="${size}" fill="${fill}" font-weight="900" font-family="StudioInterPinned, StudioTeluguPinned, sans-serif">`)
      lines.forEach((t, i) => parts.push(`<tspan x="${l.x}" y="${(l.y + size * 1.02 + i * size * 1.65).toFixed(1)}">${esc(t)}</tspan>`))
      parts.push('</text>')
    }
  }
  parts.push('</svg>')
  return parts.join('')
}

/** Next concept for arrow keys in the radio group: wraps around, Home/End jump. */
export function nextConcept(i: number, key: string, n: number): number | null {
  if (n < 1) return null
  if (key === 'ArrowRight' || key === 'ArrowDown') return (i + 1) % n
  if (key === 'ArrowLeft' || key === 'ArrowUp') return (i - 1 + n) % n
  if (key === 'Home') return 0
  if (key === 'End') return n - 1
  return null
}
