// M7-C: automated accessibility checks for the running IDEAFRAME screens. No package is needed: paste this file into the
// browser console (or run it through a browser automation tool) on any screen; it defines window.ideaframeA11y() and
// returns a list of findings for the screen that is showing. It is a set of mechanical checks, not an accessibility
// certification: it cannot judge reading order, wording, or how a screen reader actually sounds.
//
// Checks: images without alt · controls without an accessible name (placeholder-only counts as a weak name) ·
// duplicate ids · one h1 and no skipped heading levels · main and nav landmarks · positive tabindex ·
// aria-describedby / aria-labelledby / label[for] pointing at nothing · tabs outside a tablist · dialogs without a name ·
// text contrast below 4.5:1 (3:1 for large text) against the nearest solid background · targets under 24 x 24 px.
window.ideaframeA11y = function () {
  const out = []; const add = (rule, el, detail) => out.push({ rule, detail, where: describe(el) })
  const describe = el => !el ? 'page' : `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.getAttribute && el.getAttribute('role') ? '[role=' + el.getAttribute('role') + ']' : ''} "${(el.getAttribute && (el.getAttribute('aria-label') || '') || el.innerText || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 40)}"`
  const shown = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 1 && r.height > 1      /* 1 x 1 = visually hidden until focused (skip link, sr-only) */ && s.visibility !== 'hidden' && s.display !== 'none' && !el.closest('[hidden], [aria-hidden="true"]') && !(el.tagName !== 'SUMMARY' && el.closest('details:not([open])')) }      /* content of a closed disclosure is not reachable */
  const byId = id => document.getElementById(id)

  // ---- names
  for (const img of document.querySelectorAll('img')) if (shown(img) && !img.hasAttribute('alt')) add('image-alt', img, 'image has no alt text')
  const name = el => {
    const lb = el.getAttribute('aria-labelledby'); if (lb && lb.split(/\s+/).map(byId).filter(Boolean).map(x => x.innerText).join(' ').trim()) return 'ok'
    if ((el.getAttribute('aria-label') || '').trim()) return 'ok'
    if (el.id && [...document.querySelectorAll('label')].some(l => l.htmlFor === el.id && l.innerText.trim())) return 'ok'
    const wrap = el.closest('label'); if (wrap && wrap.innerText.trim()) return 'ok'
    if (!['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName) && (el.innerText || '').trim()) return 'ok'
    if (el.tagName === 'INPUT' && ['submit', 'button'].includes(el.type) && el.value) return 'ok'
    if ((el.getAttribute('title') || '').trim()) return 'ok'
    if ((el.getAttribute('placeholder') || '').trim()) return 'weak'
    return 'none'
  }
  for (const el of document.querySelectorAll('button, a[href], input:not([type=hidden]), select, textarea, [role=button], [role=tab], [role=radio], [role=checkbox], summary')) {
    if (!shown(el)) continue
    const n = name(el); if (n === 'none') add('control-name', el, 'control has no accessible name'); else if (n === 'weak') add('control-name-weak', el, 'control is named only by its placeholder')
  }

  // ---- structure
  const ids = {}; for (const el of document.querySelectorAll('[id]')) ids[el.id] = (ids[el.id] || 0) + 1
  for (const [id, n] of Object.entries(ids)) if (n > 1) add('duplicate-id', byId(id), `id "${id}" is used ${n} times`)
  const heads = [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')].filter(shown); const h1 = heads.filter(h => h.tagName === 'H1').length
  if (h1 !== 1) add('one-h1', null, `${h1} visible h1 headings`)
  let last = 0; for (const h of heads) { const lv = Number(h.tagName[1]); if (last && lv > last + 1) add('heading-order', h, `h${last} is followed by h${lv}`); last = lv }
  if (!document.querySelector('main')) add('landmark', null, 'no main landmark'); if (!document.querySelector('nav')) add('landmark', null, 'no nav landmark')
  for (const el of document.querySelectorAll('[tabindex]')) if (Number(el.getAttribute('tabindex')) > 0) add('tabindex', el, 'positive tabindex changes the natural order')
  for (const attr of ['aria-describedby', 'aria-labelledby', 'aria-controls']) for (const el of document.querySelectorAll(`[${attr}]`)) for (const id of el.getAttribute(attr).split(/\s+/)) if (id && !byId(id)) add('broken-reference', el, `${attr} points at "${id}", which does not exist`)
  for (const l of document.querySelectorAll('label[for]')) if (l.htmlFor && !byId(l.htmlFor)) add('broken-reference', l, `label points at "${l.htmlFor}", which does not exist`)
  for (const t of document.querySelectorAll('[role=tab]')) if (!t.closest('[role=tablist]')) add('tab-outside-tablist', t, 'tab is not inside a tablist')
  for (const d of document.querySelectorAll('dialog[open], [role=dialog]')) if (!d.getAttribute('aria-label') && !d.getAttribute('aria-labelledby')) add('dialog-name', d, 'dialog has no name')

  // ---- contrast (text against the nearest solid background colour)
  const rgb = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 && !Number.isNaN(p[3]) ? p[3] : 1 } }
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b) }
  const over = (top, under) => ({ r: top.r * top.a + under.r * (1 - top.a), g: top.g * top.a + under.g * (1 - top.a), b: top.b * top.a + under.b * (1 - top.a), a: 1 })
  const background = el => { const layers = []; let known = true
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const s = getComputedStyle(n); if (s.backgroundImage !== 'none') { known = false; break } const c = rgb(s.backgroundColor); if (c && c.a > 0) { layers.push(c); if (c.a === 1) break } }
    if (!known) return null
    let base = { r: 255, g: 255, b: 255, a: 1 }; for (const c of layers.reverse()) base = over(c, base); return base }
  const seen = new Set()
  for (const el of document.querySelectorAll('main *, nav *, aside *')) {
    if (!shown(el) || el.closest('section[aria-label="Poster"] .relative, [aria-label="Poster preview"]')) continue      // the poster itself is the user's artwork, checked by poster QA
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!own) continue
    const s = getComputedStyle(el); if (Number(s.opacity) < 1 || el.closest('[disabled], [aria-disabled="true"]') || el.disabled) continue
    const fg = rgb(s.color), bg = background(el); if (!fg || !bg) continue
    const text = over(fg, bg); const a = lum(text), b = lum(bg); const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
    const px = parseFloat(s.fontSize), bold = Number(s.fontWeight) >= 700; const need = px >= 24 || (px >= 18.66 && bold) ? 3 : 4.5
    const key = `${s.color}|${s.backgroundColor}|${Math.round(px)}|${ratio.toFixed(2)}`
    if (ratio < need && !seen.has(key)) { seen.add(key); add('contrast', el, `${ratio.toFixed(2)}:1, needs ${need}:1 (${s.color} on rgb(${Math.round(bg.r)}, ${Math.round(bg.g)}, ${Math.round(bg.b)}), ${Math.round(px)}px)`) }
  }

  // ---- target size (WCAG 2.2: 24 x 24 px, links inside a sentence excepted)
  for (const el of document.querySelectorAll('button, a[href], input[type=checkbox], input[type=radio], select, [role=tab], [role=radio], summary')) {
    if (!shown(el)) continue
    const r = el.getBoundingClientRect(); const inline = el.tagName === 'A' && getComputedStyle(el).display === 'inline' && el.parentElement && el.parentElement.innerText.trim().length > el.innerText.trim().length
    const boxed = el.closest('label') && el.closest('label').getBoundingClientRect().height >= 24      // a checkbox inside a taller label is reached through the label
    if (!inline && !boxed && (r.width < 24 || r.height < 24)) add('target-size', el, `${Math.round(r.width)} x ${Math.round(r.height)} px`)
  }
  return out
}
