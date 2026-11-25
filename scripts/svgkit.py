"""Small SVG toolkit: themes, font measuring and embedding, and the drawing primitives every card uses.

Text is measured with the real font metrics and the fonts are embedded (subset to the characters each SVG uses),
so every viewer sees the same layout no matter which fonts they have installed.
"""

from __future__ import annotations

import base64
import io
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).parent / "fonts"

# family key -> (css family name, fallback stack, {weight: file stem})
FAMILIES = {
    "S": ("JJSans", "'Segoe UI',Helvetica,Arial,sans-serif", {400: "geist-400", 500: "geist-500", 600: "geist-600", 700: "geist-700"}),
    "M": ("JJMono", "Consolas,'SF Mono',Menlo,monospace", {400: "geist-mono-400", 500: "geist-mono-500", 700: "geist-mono-700"}),
}

THEMES = {
    "dark": {
        "ground": "#0B1220", "dots": "#1B2740", "ink": "#03060C", "panel": "#0F1729", "inset": "#0A101C",
        "text": "#E6EDF5", "muted": "#A9B8CA", "faint": "#7E90A6",
        "signal": "#2DD4BF", "on_signal": "#03211E",
        "tiles": {"teal": "#0E4A45", "blue": "#1A3A66", "amber": "#5A3F10", "violet": "#352A63", "rose": "#5A2234", "green": "#14532D"},
        "tile_text": "#E6EDF5",
        "heat": ["#17223A", "#0F4F49", "#127A70", "#1FB0A0", "#2DD4BF"],
        "heat_text": ["#7E90A6", "#E6EDF5", "#E6EDF5", "#03211E", "#03211E"],
        "dot_colors": ["#F87171", "#FBBF24", "#34D399"],
    },
    "light": {
        "ground": "#F3F6FA", "dots": "#D3DCE7", "ink": "#0B1220", "panel": "#FFFFFF", "inset": "#FFFFFF",
        "text": "#0B1220", "muted": "#334155", "faint": "#56657A",
        "signal": "#2DD4BF", "on_signal": "#03211E",
        "tiles": {"teal": "#C9F7EE", "blue": "#D8E7FD", "amber": "#FCE7BE", "violet": "#E5DFFF", "rose": "#FFDFE6", "green": "#CFF7DF"},
        "tile_text": "#0B1220",
        "heat": ["#E4EAF2", "#B5EFE5", "#6CDCCB", "#1FB0A0", "#0F766E"],
        "heat_text": ["#56657A", "#0B1220", "#0B1220", "#03211E", "#FFFFFF"],
        "dot_colors": ["#EF4444", "#F59E0B", "#10B981"],
    },
}


class _Fonts:
    def __init__(self) -> None:
        self._fonts: dict[tuple[str, int], TTFont] = {}

    def get(self, fam: str, weight: int) -> TTFont:
        key = (fam, weight)
        if key not in self._fonts:
            stem = FAMILIES[fam][2][weight]
            self._fonts[key] = TTFont(FONT_DIR / f"{stem}.woff2")
        return self._fonts[key]

    def width(self, s: str, fam: str, weight: int, size: float) -> float:
        font = self.get(fam, weight)
        cmap = font.getBestCmap()
        hmtx = font["hmtx"]
        upm = font["head"].unitsPerEm
        total = 0
        for ch in s:
            glyph = cmap.get(ord(ch))
            if glyph is None:
                raise ValueError(f"glyph {ch!r} (U+{ord(ch):04X}) is missing from {FAMILIES[fam][2][weight]}")
            total += hmtx[glyph][0]
        return total * size / upm


FONTS = _Fonts()


def text_width(s: str, size: float, fam: str = "S", weight: int = 400) -> float:
    return FONTS.width(s, fam, weight, size)


def wrap(s: str, maxw: float, size: float, fam: str = "S", weight: int = 400) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in s.split():
        trial = f"{cur} {word}" if cur else word
        if cur and text_width(trial, size, fam, weight) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def f1(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Svg:
    def __init__(self, w: float, h: float, theme: str, label: str) -> None:
        self.w, self.h = w, h
        self.t = THEMES[theme]
        self.label = label
        self.parts: list[str] = []
        self.used: dict[tuple[str, int], set[str]] = {}

    # primitives -------------------------------------------------------------------------------------------------
    def raw(self, s: str) -> None:
        self.parts.append(s)

    def rect(self, x, y, w, h, fill, rx=0, stroke=None, sw=2, extra="") -> None:
        st = f' stroke="{stroke}" stroke-width="{f1(sw)}"' if stroke else ""
        self.parts.append(
            f'<rect x="{f1(x)}" y="{f1(y)}" width="{f1(w)}" height="{f1(h)}" rx="{f1(rx)}" fill="{fill}"{st}{extra}/>'
        )

    def text(self, x, y, s, size, fill, fam="S", weight=400, anchor="start", extra="") -> float:
        self.used.setdefault((fam, weight), set()).update(s)
        w = text_width(s, size, fam, weight)
        self.parts.append(
            f'<text x="{f1(x)}" y="{f1(y)}" font-family="{FAMILIES[fam][0]},{FAMILIES[fam][1]}" font-weight="{weight}" '
            f'font-size="{f1(size)}" fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'
        )
        return w

    def spans(self, x, y, size, fam, pieces: list[tuple[str, str, int]]) -> float:
        """One line made of differently coloured pieces: [(text, fill, weight), ...]. Returns the line width."""
        out = []
        total = 0.0
        for s, fill, weight in pieces:
            self.used.setdefault((fam, weight), set()).update(s)
            total += text_width(s, size, fam, weight)
            out.append(f'<tspan font-weight="{weight}" fill="{fill}">{escape(s)}</tspan>')
        self.parts.append(
            f'<text x="{f1(x)}" y="{f1(y)}" font-family="{FAMILIES[fam][0]},{FAMILIES[fam][1]}" font-size="{f1(size)}" '
            f'xml:space="preserve">{"".join(out)}</text>'
        )
        return total

    # composed pieces --------------------------------------------------------------------------------------------
    def panel(self) -> None:
        """The card frame: ground colour, dot grid, hard outline. Call it last (once self.h is final); it is drawn
        underneath everything else."""
        t = self.t
        body = self.parts
        self.parts = []
        self.rect(1, 1, self.w - 2, self.h - 2, t["ground"], rx=18, stroke=t["ink"], sw=2)
        self.rect(2, 2, self.w - 4, self.h - 4, "url(#dots)", rx=17)
        self.parts += body

    def block(self, x, y, w, h, fill, rx=14, shadow=4, sw=2) -> None:
        """A raised block: a hard offset shadow, then the filled shape with an ink outline."""
        if shadow:
            self.rect(x + shadow, y + shadow, w, h, self.t["ink"], rx=rx)
        self.rect(x, y, w, h, fill, rx=rx, stroke=self.t["ink"], sw=sw)

    def chip(self, x, y, label, fill, size=15, fam="S", weight=600, h=32, pad=14, shadow=3, color=None) -> float:
        w = text_width(label, size, fam, weight) + 2 * pad
        self.block(x, y, w, h, fill, rx=min(9, h / 2), shadow=shadow, sw=2 if shadow else 1.5)
        self.text(x + w / 2, y + h / 2 + size * 0.36, label, size, color or self.t["tile_text"], fam, weight, "middle")
        return w

    def chip_flow(self, x, y, maxw, labels, fills, size=15, fam="S", weight=600, h=32, gap=10, pad=14, shadow=3,
                  color=None) -> float:
        """Lay chips left to right, wrapping at maxw. Returns the bottom y."""
        cx, cy = x, y
        for i, label in enumerate(labels):
            w = text_width(label, size, fam, weight) + 2 * pad
            if cx > x and cx + w > x + maxw:
                cx, cy = x, cy + h + gap
            self.chip(cx, cy, label, fills[i % len(fills)], size, fam, weight, h, pad, shadow, color)
            cx += w + gap
        return cy + h

    # output -----------------------------------------------------------------------------------------------------
    def _font_css(self) -> str:
        css = []
        for (fam, weight), chars in sorted(self.used.items()):
            chars = {c for c in chars if not c.isspace()} | {" "}
            font = TTFont(FONT_DIR / f"{FAMILIES[fam][2][weight]}.woff2")
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern"]
            opts.name_IDs = []
            opts.notdef_outline = True
            opts.drop_tables += ["FFTM"]
            sub = subset.Subsetter(opts)
            sub.populate(text="".join(chars))
            sub.subset(font)
            buf = io.BytesIO()
            font.flavor = "woff2"
            font.save(buf)
            data = base64.b64encode(buf.getvalue()).decode()
            css.append(
                f"@font-face{{font-family:{FAMILIES[fam][0]};font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
            )
        return "".join(css)

    def render(self) -> str:
        label = escape(self.label, quote=True)
        defs = (
            f"<defs><style>{self._font_css()}</style>"
            f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">'
            f'<circle cx="9" cy="9" r="1.1" fill="{self.t["dots"]}"/></pattern></defs>'
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{f1(self.w)}" height="{f1(self.h)}" '
            f'viewBox="0 0 {f1(self.w)} {f1(self.h)}" role="img" aria-label="{label}">'
            f"<title>{escape(self.label)}</title>{defs}{''.join(self.parts)}</svg>"
        )
