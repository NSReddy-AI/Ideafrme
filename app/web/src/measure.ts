// M7-A: poster QA on the text as the browser actually draws it (shaped glyphs), not on the layer's declared box.
// Measuring works like M5's inspectScene (browser_acceptance.js): the server's SVG is laid out off-screen with the
// pinned fonts, and each text group's bounding box is read with getBBox(). Nothing is changed or saved.
import type { Scene } from './creative'

export type Ink = { element_id: string; x: number; y: number; width: number; height: number }
export type MeasuredCheck = { name: 'measured_canvas' | 'measured_safe_area'; level: 'error' | 'warning'; element_id: string; detail: string }

export async function measureText(scene: Scene): Promise<Ink[]> {
  const xml = new DOMParser().parseFromString(scene.svg, 'image/svg+xml')
  if (xml.querySelector('parsererror')) throw Error('Invalid generated SVG.')
  const holder = document.createElement('div'); holder.className = 'measurement'; holder.setAttribute('aria-hidden', 'true')
  const svg = document.importNode(xml.documentElement, true) as unknown as SVGSVGElement
  holder.append(svg); document.body.append(holder)
  try {
    await document.fonts.ready
    const out: Ink[] = []
    for (const b of scene.boxes) {
      if (b.type !== 'text') continue
      const g = svg.querySelector('#' + b.id) as SVGGraphicsElement | null; if (!g) continue
      const r = g.getBBox()
      if (r.width > 0 && r.height > 0) out.push({ element_id: b.element_id, x: r.x, y: r.y, width: r.width, height: r.height })
    }
    return out
  } finally { holder.remove() }
}

/** Pure rules on measured ink: outside the poster = error (M5 also refuses export); inside the margin = warning. */
export function measuredChecks(ink: Ink[], view: { width: number; height: number }, margin: number): MeasuredCheck[] {
  const out: MeasuredCheck[] = []
  for (const r of ink) {
    const right = r.x + r.width, bottom = r.y + r.height
    if (r.x < 0 || r.y < 0 || right > view.width || bottom > view.height) {
      out.push({ name: 'measured_canvas', level: 'error', element_id: r.element_id, detail: 'drawn text goes outside the poster' })
      continue
    }
    const gaps = [['left', r.x], ['top', r.y], ['right', view.width - right], ['bottom', view.height - bottom]] as const
    const near = gaps.filter(([, g]) => g < margin)
    if (near.length) out.push({ name: 'measured_safe_area', level: 'warning', element_id: r.element_id,
      detail: `drawn text is ${near.map(([s, g]) => `${Math.max(0, Math.floor(g))} px from the ${s} edge`).join(', ')} (keep ${margin} px)` })
  }
  return out
}
