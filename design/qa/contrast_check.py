#!/usr/bin/env python3
"""Contrast audit for design/tokens/tokens.css (WCAG 2.2 AA).

Run:  python3 design/qa/contrast_check.py
Exits 1 if any listed pair fails. Add a row to PAIRS for every new
foreground/background combination a component uses.
"""
import re
import sys
from pathlib import Path

TOKENS = Path(__file__).resolve().parents[1] / "tokens" / "tokens.css"

# (foreground token, background token, minimum ratio)
TEXT, LARGE_OR_UI = 4.5, 3.0
PAIRS = [
    ("color-text-primary", "color-bg-canvas", TEXT),
    ("color-text-primary", "color-bg-surface", TEXT),
    ("color-text-primary", "color-bg-raised", TEXT),
    ("color-text-secondary", "color-bg-canvas", TEXT),
    ("color-text-secondary", "color-bg-surface", TEXT),
    ("color-text-secondary", "color-bg-raised", TEXT),
    ("color-text-tertiary", "color-bg-canvas", TEXT),
    ("color-text-tertiary", "color-bg-surface", TEXT),
    ("color-text-tertiary", "color-bg-raised", TEXT),
    ("color-text-link", "color-bg-canvas", TEXT),
    ("color-text-link", "color-bg-surface", TEXT),
    ("color-text-link", "color-bg-raised", TEXT),
    ("color-text-link", "color-action-subtle", TEXT),
    ("color-text-primary", "color-action-subtle", TEXT),
    ("color-text-on-action", "color-action", TEXT),
    ("color-text-on-action", "color-action-hover", TEXT),
    ("color-text-on-action", "color-action-pressed", TEXT),
    ("color-text-on-action", "color-danger-solid", TEXT),
    ("color-text-on-action", "color-danger-solid-hover", TEXT),
    ("color-accent", "color-bg-canvas", TEXT),
    ("color-accent", "color-accent-subtle", TEXT),
    ("color-success", "color-bg-canvas", TEXT),
    ("color-success", "color-success-subtle", TEXT),
    ("color-warning", "color-bg-canvas", TEXT),
    ("color-warning", "color-warning-subtle", TEXT),
    ("color-danger", "color-bg-canvas", TEXT),
    ("color-danger", "color-danger-subtle", TEXT),
    ("color-info", "color-bg-canvas", TEXT),
    ("color-info", "color-info-subtle", TEXT),
    ("color-border-strong", "color-bg-canvas", LARGE_OR_UI),
    ("color-border-strong", "color-bg-surface", LARGE_OR_UI),
    ("color-border-strong", "color-bg-raised", LARGE_OR_UI),
    ("color-focus-ring", "color-bg-canvas", LARGE_OR_UI),
    ("color-focus-ring", "color-bg-surface", LARGE_OR_UI),
    ("color-focus-ring", "color-bg-raised", LARGE_OR_UI),
    ("color-action", "color-bg-canvas", LARGE_OR_UI),
    ("color-action", "color-bg-surface", LARGE_OR_UI),
]

HEX = re.compile(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\b")


def block(css: str, selector: str) -> dict:
    start = css.index(selector)
    body = css[css.index("{", start) + 1 : css.index("}", start)]
    return dict(HEX.findall(body))


def luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def main() -> int:
    css = TOKENS.read_text(encoding="utf-8")
    light = block(css, ":root {")
    dark = {**light, **block(css, ':root[data-theme="dark"]')}
    system_dark = {**light, **block(css, ':root:not([data-theme="light"])')}

    failures = 0
    if system_dark != dark:
        print("FAIL  the two dark-theme blocks in tokens.css differ")
        failures += 1

    for name, theme in (("light", light), ("dark", dark)):
        print(f"\n{name} theme")
        for fg, bg, need in PAIRS:
            got = ratio(theme[fg], theme[bg])
            ok = got >= need
            failures += not ok
            print(f"  {'pass' if ok else 'FAIL'}  {got:5.2f} (needs {need})  {fg} on {bg}")

    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
