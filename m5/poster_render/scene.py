"""Strict render policy and renderer-neutral SVG mapping for creative@1.

No browser, codecs, external resources or creative source modifications here.
"""
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

from creative_core import fingerprint, validate, CreativeError
from creative_core.document import canonical
from creative_core.validation import confined, require

PROFILE = {"id": "m5-svg-poster@1", "color_space": "srgb", "line_height": {"te":1.65,"en":1.35},
           "baseline": 1.02, "rotation_origin": "element-center", "max_pixels": 8294400}
COLOR = re.compile(r"(?:#[0-9a-fA-F]{6}|#[0-9a-fA-F]{8}|none)\Z")
PATH = re.compile(r"[MmLlHhVvCcSsQqTtAaZz0-9eE+.,\s-]+\Z")
ID = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{0,79}\Z")
SAFE_TAGS = {"svg", "g", "rect", "circle", "ellipse", "line", "polyline", "polygon", "path"}
SAFE_ATTRS = {"viewBox", "width", "height", "x", "y", "x1", "x2", "y1", "y2", "cx", "cy",
              "r", "rx", "ry", "d", "points", "fill", "stroke", "stroke-width", "opacity"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _safe_svg(data):
    require(len(data) <= 500000 and b"<!" not in data and b"<?" not in data,
            "SVG declarations/entities are unsupported")
    try:
        tree = ET.fromstring(data)
    except ET.ParseError as exc:
        raise CreativeError("malformed SVG asset") from exc
    nodes = list(tree.iter())
    require(len(nodes) <= 1000, "SVG node budget exceeded")
    require(tree.tag == "{http://www.w3.org/2000/svg}svg", "SVG namespace required")
    for node in nodes:
        require(node.tag.startswith("{http://www.w3.org/2000/svg}")
                and node.tag.split("}")[-1] in SAFE_TAGS, "unsupported SVG element")
        require(not (node.text or "").strip() and not (node.tail or "").strip(),
                "SVG text assets unsupported; use editable text layers")
        for key, value in node.attrib.items():
            require(key in SAFE_ATTRS, "unsafe SVG attribute")
            if key in ("fill", "stroke"):
                require(bool(COLOR.fullmatch(value)), "unsafe SVG paint")
            else:
                require(len(value) <= 10000 and bool(PATH.fullmatch(value)), "unsafe SVG value")
    return data


def _asset(asset, root):
    path = confined(root, asset["path"], True)
    require(path.stat().st_size <= 10 * 1024 * 1024, "asset byte budget exceeded")
    data = path.read_bytes()
    require(asset.get("sha256") == sha(data), "render assets require matching SHA-256")
    kind = asset["kind"]
    if kind == "font":
        require(data[:4] in (b"\x00\x01\x00\x00", b"OTTO"), "only sfnt TTF/OTF fonts supported")
        mime = "font/otf" if data[:4] == b"OTTO" else "font/ttf"
    elif kind in ("vector", "logo"):
        _safe_svg(data)
        mime = "image/svg+xml"
    elif kind == "image":
        require(data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR"
                and len(data) >= 33, "only PNG raster assets supported")
        w, h = struct.unpack(">II", data[16:24])
        require(0 < w <= 8192 and 0 < h <= 8192 and w * h <= PROFILE["max_pixels"],
                "decoded PNG pixel budget exceeded")
        mime = "image/png"
    elif kind == "brand":
        mime = "application/json"
    else:
        raise CreativeError("video assets are deferred")
    return "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")


def render_identity(doc, policy, engine):
    implementation = {name: sha((Path(__file__).parent/name).read_bytes())
                      for name in ("scene.py", "backend.mjs", "approval.py")}
    return "sha256:" + sha(canonical({"document": fingerprint(doc), "policy": policy,
                                       "profile": PROFILE, "engine": engine,
                                       "implementation": implementation}))


def build_scene(doc, root, view_id, policy):
    """Return derived SVG + layout metadata. Policy is a separately hashed sidecar.

    Policy keys: background, safe_margin, required_elements, palette, fonts.
    Font IDs map to verified family names and scripts (te/en).
    """
    validate(doc, root)
    require(set(policy) == {"background", "safe_margin", "required_elements", "palette", "fonts"},
            "unknown/missing render policy fields")
    require(bool(COLOR.fullmatch(policy["background"])), "invalid background")
    require(isinstance(policy["palette"], list) and policy["palette"]
            and all(isinstance(c, str) and COLOR.fullmatch(c) for c in policy["palette"]),
            "invalid palette")
    require(all(c in policy["palette"] for c in [policy["background"]]), "background outside palette")
    views = {v["id"]: v for v in doc["views"]}
    require(view_id in views, "unknown view")
    view = views[view_id]
    w, h = view["width"], view["height"]
    require(type(w) is int and type(h) is int and 0 < w <= 2160 and 0 < h <= 3840
            and w * h <= PROFILE["max_pixels"], "unsupported output dimensions")
    margin = policy["safe_margin"]
    require(type(margin) is int and 0 <= margin < min(w, h) / 2, "invalid safe margin")
    assets = {a["id"]: a for a in doc["assets"]}
    fonts = policy["fonts"]
    require(isinstance(fonts, dict) and 0 < len(fonts) <= 8, "invalid fonts")
    uris = {key: _asset(asset, root) for key, asset in assets.items()}
    styles = []
    for key, font in fonts.items():
        require(key in assets and assets[key]["kind"] == "font", "missing policy font")
        require(isinstance(font, dict) and set(font) == {"family", "script", "weight"}, "invalid font policy")
        require(isinstance(font["family"], str) and re.fullmatch(r"[A-Za-z ]{1,60}", font["family"])
                and font["script"] in ("te", "en") and font["weight"] in (700,900), "invalid font family/script")
        styles.append(f'@font-face{{font-family:"{font["family"]}";src:url("{uris[key]}");font-weight:{font["weight"]};font-style:normal;}}')
    elements = [el for el in doc["elements"] if el["view_id"] == view_id]
    ids = {el["id"] for el in elements}
    require(isinstance(policy["required_elements"], list)
            and all(isinstance(i, str) and i in ids for i in policy["required_elements"]),
            "required brand element missing")
    require(len(elements) <= 150, "layer budget exceeded")
    content = {c["id"]: c for c in doc["content"]}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
             "<style>" + "".join(styles) + "</style>",
             f'<rect width="{w}" height="{h}" fill="{policy["background"]}"/>']
    boxes = []
    for el in elements:
        require(bool(ID.fullmatch(el["id"])), "render layer ID must be a safe identifier")
        x, y, ew, eh = (el[k] for k in ("x", "y", "width", "height"))
        require(x >= margin and y >= margin and x + ew <= w - margin and y + eh <= h - margin,
                f'{el["id"]}: outside safe area')
        style = el["style"]
        kind = el["type"]
        allowed = {"fill", "stroke", "stroke_width", "opacity", "rotation"}
        if kind == "text": allowed |= {"font_asset_id", "font_size"}
        if kind == "shape": allowed |= {"shape"}
        if kind == "vector" and "path" in style: allowed |= {"path"}
        require(set(style) <= allowed, "style property unsupported for this layer type")
        rotation = style.get("rotation", 0)
        require(rotation == 0, "rotated-layer bounds are deferred; rotation must be zero")
        for key in ("fill", "stroke"):
            if key in style:
                require(bool(COLOR.fullmatch(style[key])) and style[key] in policy["palette"],
                        "paint outside palette / unsupported paint")
        require(style.get("stroke_width", 0) <= 20, "stroke budget exceeded")
        stroke_pad = style.get("stroke_width", 0) / 2
        require(x-stroke_pad >= margin and y-stroke_pad >= margin
                and x+ew+stroke_pad <= w-margin and y+eh+stroke_pad <= h-margin,
                "stroke outside safe area")
        if kind in ("text", "shape") or "path" in style:
            require("fill" in style, "explicit paint required")
        paint = " ".join(f'{k.replace("_", "-")}="{html.escape(str(style[k]), quote=True)}"'
                         for k in ("fill", "stroke", "stroke_width") if k in style)
        parts.append(f'<g id="layer-{el["id"]}" opacity="{style.get("opacity", 1)}">')
        if kind == "text":
            font_id = style.get("font_asset_id")
            require(font_id in fonts and "font_size" in style, "explicit pinned font and size required")
            text = content[el["content_id"]]["text"]
            require(len(text) <= 1200 and not any(ord(c) < 32 and c != "\n" for c in text),
                    "invalid render text")
            require(all((32 <= ord(c) <= 126) or (0x0C00 <= ord(c) <= 0x0C7F)
                        or c in "\n–—‘’“”•…" for c in text), "unsupported glyph repertoire")
            if any(0x0C00 <= ord(c) <= 0x0C7F for c in text):
                require(fonts[font_id]["script"] == "te", "Telugu requires Telugu font")
            size = style["font_size"]
            require(8 <= size <= 320, "font size out of render range")
            lines = text.split("\n")
            require(len(lines) <= 12, "line budget exceeded")
            family = fonts[font_id]["family"]
            parts.append(f'<text font-family="{family}" font-weight="{fonts[font_id]["weight"]}" font-size="{size}" {paint}>')
            for i, line in enumerate(lines):
                baseline = y + size * PROFILE["baseline"] + i * size * PROFILE["line_height"][fonts[font_id]["script"]]
                parts.append(f'<tspan x="{x}" y="{baseline}">')
                # Keep Telugu clusters intact; explicit Latin runs prevent system fallback.
                for run in re.findall(r"[\u0c00-\u0c7f]+|[^\u0c00-\u0c7f]+", line):
                    script = "te" if any(0x0c00 <= ord(c) <= 0x0c7f for c in run) else "en"
                    face = next((f for f in fonts.values() if f["script"] == script), None)
                    require(face is not None, "missing script-specific font")
                    parts.append(f'<tspan font-family="{face["family"]}" font-weight="{face["weight"]}">{html.escape(run)}</tspan>')
                parts.append('</tspan>')
            parts.append("</text>")
        elif kind == "shape":
            if style["shape"] == "rectangle":
                parts.append(f'<rect x="{x}" y="{y}" width="{ew}" height="{eh}" {paint}/>')
            else:
                parts.append(f'<ellipse cx="{x+ew/2}" cy="{y+eh/2}" rx="{ew/2}" ry="{eh/2}" {paint}/>')
        elif kind == "vector" and "path" in style:
            require(bool(PATH.fullmatch(style["path"])) and len(style["path"]) <= 10000,
                    "unsafe vector path")
            parts.append(f'<svg x="{x}" y="{y}" width="{ew}" height="{eh}" viewBox="0 0 {ew} {eh}"><path d="{style["path"]}" {paint}/></svg>')
        elif kind in ("image", "logo", "vector"):
            aid = el["asset_id"]
            parts.append(f'<image x="{x}" y="{y}" width="{ew}" height="{eh}" preserveAspectRatio="xMidYMid meet" href="{uris[aid]}"/>')
        else:
            raise CreativeError("unsupported poster element")
        parts.append("</g>")
        boxes.append({"id": "layer-" + el["id"], "type": kind, "x": x, "y": y,
                      "width": ew, "height": eh})
    parts.append("</svg>")
    return {"svg": "".join(parts), "width": w, "height": h, "boxes": boxes,
            "document_fingerprint": fingerprint(doc), "policy": policy, "profile": PROFILE}
