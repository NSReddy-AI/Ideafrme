"""Rule-based poster QA for M5 creative@1 documents (M6 step 4). Pure functions: no I/O, no rendering, no model.

Like engine/qa.py for reels, it reports PASS/FAIL with every check listed. It never changes the document and does
not block export; the editor shows it before export. Checks that need the browser's real text shaping
(text overflowing its box, overlapping lines) stay in M5's browser inspectScene, which already refuses export.

Rules (owner decisions 12 Nov 2026: 64 px safe margin as initial default; 52 px large text kept, 390 px phone reference -
see tests/acceptance/m7a_telugu_shaping/README.md):
  canvas     every layer lies fully inside the poster (error)
  safe_area  text stays SAFE_MARGIN px inside each edge (warning)
  contrast   text against the layer it sits on, WCAG 2.2: 4.5:1, or 3:1 for large text (error).
             Posters are seen at phone size, so "large" uses the size on a 390 px wide phone:
             font_size * 390/1080 >= 18.66 px (14 pt bold; both pinned fonts are bold), i.e. font_size >= 52.
             Text over the transparent background or over more than one layer cannot be judged (warning).
  glyphs     every character is covered by the pinned font for its script (error; M5 refuses to render it)
  empty      a text layer has visible text (warning)
  overlap    two text layers do not overlap (warning)"""

SAFE_MARGIN = 64                      # owner-approved initial default (6 % of the 1080 px width)
PHONE_SCALE = 390 / 1080              # owner-approved reference phone width in CSS px (gives 52 px)
LARGE_PX = 18.66                      # WCAG large bold text, 14 pt


def _rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(hex_colour):
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in _rgb(hex_colour)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _box(e): return e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]


def _intersects(a, b):
    ax0, ay0, ax1, ay1 = _box(a); bx0, by0, bx1, by1 = _box(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def _contains(outer, inner):
    ox0, oy0, ox1, oy1 = _box(outer); ix0, iy0, ix1, iy1 = _box(inner)
    return ox0 <= ix0 and oy0 <= iy0 and ix1 <= ox1 and iy1 <= oy1


def _script(cp): return "te" if 0x0C00 <= cp <= 0x0C7F or cp in (0x200C, 0x200D) else "en"


def check(doc, coverage=None):
    """doc: a creative@1 document (one view). coverage: {"en": set(codepoints), "te": set(...)} from the pinned fonts."""
    view = doc["views"][0]; W, H = view["width"], view["height"]
    text = {c["id"]: c["text"] for c in doc["content"]}
    layers = [e for e in doc["elements"] if e["view_id"] == view["id"]]
    out = []
    add = lambda name, level, ok, eid, detail: out.append(dict(name=name, level=level, passed=bool(ok), element_id=eid, detail=detail))

    for i, e in enumerate(layers):
        x0, y0, x1, y1 = _box(e)
        add("canvas", "error", x0 >= 0 and y0 >= 0 and x1 <= W and y1 <= H, e["id"],
            "inside the poster" if x0 >= 0 and y0 >= 0 and x1 <= W and y1 <= H else f"reaches outside the {W}×{H} poster")
        if e["type"] != "text": continue
        t = text.get(e.get("content_id"), "")
        m = SAFE_MARGIN
        inside = x0 >= m and y0 >= m and x1 <= W - m and y1 <= H - m
        add("safe_area", "warning", inside, e["id"], f"{m} px from every edge" if inside else f"closer than {m} px to an edge")
        add("empty", "warning", t.strip() != "", e["id"], "has text" if t.strip() else "no visible text")

        size = e["style"].get("font_size", 0); large = size * PHONE_SCALE >= LARGE_PX; need = 3.0 if large else 4.5
        below = [b for b in layers[:i] if b["type"] == "shape" and _intersects(b, e)]
        top = below[-1] if below else None
        if top is None:
            add("contrast", "warning", False, e["id"], "on the transparent background: contrast depends on where the poster is shown")
        elif not _contains(top, e):
            add("contrast", "warning", False, e["id"], "spans more than one background: check contrast by eye")
        else:
            r = contrast(e["style"]["fill"], top["style"]["fill"])
            add("contrast", "error", r >= need, e["id"], f"{r:.2f}:1 against {top['id']} (needs {need}:1{' for large text' if large else ''})")

        if coverage is not None:
            missing = sorted({f"U+{ord(ch):04X}" for ch in t if ch != "\n" and ord(ch) not in (0x200C, 0x200D)
                              and ord(ch) not in coverage.get(_script(ord(ch)), set())})
            add("glyphs", "error", not missing, e["id"], "all characters in the pinned fonts" if not missing else "missing: " + ", ".join(missing[:8]))

    texts = [e for e in layers if e["type"] == "text"]
    for a_i, a in enumerate(texts):
        for b in texts[a_i + 1:]:
            if _intersects(a, b): add("overlap", "warning", False, a["id"], f"overlaps {b['id']}")

    errors = [c for c in out if c["level"] == "error" and not c["passed"]]
    warnings = [c for c in out if c["level"] == "warning" and not c["passed"]]
    return dict(passed=not errors, errors=len(errors), warnings=len(warnings), checks=out,
                rules=dict(safe_margin=SAFE_MARGIN, phone_scale=round(PHONE_SCALE, 4), large_text_px=LARGE_PX))
