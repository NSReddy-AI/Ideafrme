"""Design-token audit for the M6 web UI (M7-B B1). Read-only. Exit 1 if a screen hard-codes what the tokens own.

  python3 tools/m6_token_audit.py

Scans app/web/src (*.tsx, *.ts, *.css) except index.css, which maps the tokens. Flags:
  - literal colours: #rgb/#rrggbb, rgb()/hsl() in components;
  - Tailwind palette colours (bg-zinc-100, text-white, ...): colour must come from semantic tokens (bg-act, text-ink ...);
  - fixed radii (rounded, rounded-md ...): use rounded-chip/field/box/sheet/btn or rounded-full;
  - fixed motion (duration-150, ease-in-out ...): use duration-[var(--motion-*)] and ease-[var(--ease-*)].
A line can be exempted with a trailing comment containing "token-audit: allow <reason>"."""
import re, sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "app" / "web" / "src"
PALETTE = r"(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}"
RULES = [
    ("literal colour", re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?(?:[0-9a-fA-F]{2})?\b(?![\w-])")),
    ("literal colour function", re.compile(r"\b(?:rgb|rgba|hsl|hsla)\(")),
    ("palette colour class", re.compile(rf"\b(?:bg|text|border|ring|outline|fill|stroke|from|to|via|decoration|accent|shadow|divide|placeholder)-(?:white|black|{PALETTE})\b")),
    ("fixed radius", re.compile(r"(?<![\w-])rounded(?:-(?:none|sm|md|lg|xl|2xl|3xl))?(?![\w-])")),
    ("fixed motion", re.compile(r"(?<![\w-])(?:duration-\d+|ease-(?:in|out|in-out|linear))(?![\w-])")),
]


def scan_line(line):
    """[(rule, match)] for one source line."""
    if "token-audit: allow" in line: return []
    out = []
    for name, rx in RULES:
        for m in rx.finditer(line):
            if name == "literal colour" and not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", m.group(0)): continue
            out.append((name, m.group(0)))
    return out


def main():
    bad = []
    for f in sorted(SRC.rglob("*")):
        if f.suffix not in (".tsx", ".ts", ".css") or f.name in ("index.css",) or f.name.endswith(".d.ts"): continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            bad += [f"{f.relative_to(SRC)}:{n}: {name}: {hit}" for name, hit in scan_line(line)]
    for b in bad: print(b)
    print(f"{len(bad)} finding(s)", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
