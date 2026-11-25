"""Every card on the profile. Each function returns the SVG text for one (theme, phone) variant."""

from __future__ import annotations

from datetime import date, timedelta

from svgkit import Svg, f1, text_width, wrap

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TILE_ORDER = ["teal", "blue", "violet", "amber", "rose", "green"]


def fmt(n: int) -> str:
    return f"{n:,}"


def day_label(d: date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]}"


# ---------------------------------------------------------------------------------------------------- icons
def icon(svg: Svg, kind: str, x: float, y: float, color: str, s: float = 24) -> None:
    """Simple line icons drawn on a 24-unit grid at (x, y)."""
    k = s / 24
    paths = {
        "calendar": "M4 6h16v14H4z M4 10h16 M8 3v5 M16 3v5",
        "flame": "M12 3c1 4 6 6 6 11a6 6 0 0 1-12 0c0-3 2-4 3-6 1 2 2 3 3 3-1-3-1-5 0-8z",
        "trophy": "M7 4h10v5a5 5 0 0 1-10 0z M7 6H4v2a3 3 0 0 0 3 3 M17 6h3v2a3 3 0 0 1-3 3 M12 14v4 M8 20h8",
        "bars": "M5 20V12 M10 20V6 M15 20V9 M20 20V4",
        "folder": "M3 6h6l2 2h10v11H3z",
        "pulse": "M3 12h4l2-6 4 12 2-6h6",
        "bolt": "M13 2 5 14h6l-1 8 8-12h-6z",
        "arrow": "M7 17 17 7 M9 7h8v8",
        "in": "M6 10v8 M6 6v.5 M10 18v-8 M10 13a3 3 0 0 1 6 0v5",
        "mail": "M3 6h18v12H3z M3 7l9 6 9-6",
        "globe": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M3 12h18 M12 3c3 3 3 15 0 18 M12 3c-3 3-3 15 0 18",
    }
    svg.raw(
        f'<path transform="translate({f1(x)} {f1(y)}) scale({k:.3f})" d="{paths[kind]}" fill="none" stroke="{color}" '
        f'stroke-width="{f1(2.2 / k if k < 1 else 2.2)}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


# ---------------------------------------------------------------------------------------------------- hero
def hero(p: dict, theme: str, phone: bool) -> str:
    h = p["hero"]
    W = 440 if phone else 880
    svg = Svg(W, 10, theme, f"Hi, I'm {h['name']}. {h['tagline']}")
    t = svg.t
    if phone:
        m, ms, y = 24, 72, 24
    else:
        m, ms, y = 40, 112, 44
    svg.block(m, y, ms, ms, t["signal"], rx=18, shadow=5)
    svg.text(m + ms / 2, y + ms / 2 + ms * 0.16, h["monogram"], ms * 0.42, t["on_signal"], "S", 700, "middle")

    # sticker with the site, top right
    site = h["site_label"]
    ssize = 14 if phone else 16
    sw = text_width(site, ssize, "M", 700) + 28
    sx, sy = W - sw - (22 if phone else 30), (34 if phone else 30)
    svg.raw(f'<g transform="rotate(-4 {f1(sx + sw / 2)} {f1(sy + 17)})">')
    svg.block(sx, sy, sw, 34, t["signal"], rx=10, shadow=4)
    svg.text(sx + sw / 2, sy + 22.5, site, ssize, t["on_signal"], "M", 700, "middle")
    svg.raw("</g>")

    tx = m if phone else m + ms + 30
    tsize = 42 if phone else 56
    ty = (y + ms + 58) if phone else y + 60
    hi = "Hi, I'm "
    hw = svg.text(tx, ty, hi, tsize, t["text"], "S", 700)
    nw = text_width(h["name"], tsize, "S", 700)
    svg.rect(tx + hw - 8, ty - tsize * 0.86, nw + 18, tsize * 1.12, t["tiles"]["teal"], rx=12, stroke=t["ink"], sw=2)
    svg.text(tx + hw + 1, ty, h["name"], tsize, t["tile_text"], "S", 700)

    sub_size = 17 if phone else 19
    maxw = W - tx - (24 if phone else 40)
    ly = ty + (40 if phone else 44)
    for line in wrap(h["tagline"], maxw, sub_size, "S", 500):
        svg.text(tx, ly, line, sub_size, t["muted"], "S", 500)
        ly += sub_size * 1.4
    fills = [t["tiles"][c] for c in TILE_ORDER]
    bottom = svg.chip_flow(tx, ly - sub_size * 0.4 + 8, maxw, h["chips"], fills, size=14 if phone else 15, h=30 if phone else 32)
    svg.h = bottom + (28 if phone else 40)
    svg.panel()
    return svg.render()


# ---------------------------------------------------------------------------------------------------- badges
def badge(b: dict, theme: str) -> str:
    svg = Svg(10, 44, theme, f"{b['label']}: {b['handle']}")
    t = svg.t
    lw = text_width(b["label"], 17, "S", 600)
    hw = text_width(b["handle"], 15, "M", 400)
    w = 14 + 26 + 10 + lw + 12 + hw + 16
    svg.w = w + 6
    svg.block(1, 3, w, 36, t["tiles"][b["tile"]], rx=10, shadow=3)
    svg.rect(14, 11, 26, 20, t["panel"], rx=5, stroke=t["ink"], sw=1.5)
    icon(svg, b["icon"], 18, 12.5, t["signal"] if theme == "dark" else "#0F766E", 17)
    svg.text(50, 27, b["label"], 17, t["tile_text"], "S", 600)
    svg.text(50 + lw + 12, 26.5, b["handle"], 15, t["tile_text"], "M", 400)
    return svg.render()


# ---------------------------------------------------------------------------------------------------- stats
def stats(st: dict, theme: str, phone: bool, stamp: str) -> str:
    W = 440 if phone else 880
    label = (
        f"On GitHub: {fmt(st['year_total'])} contributions in the last year, a {st['current']}-day current streak, "
        f"longest streak {st['longest']} days, {fmt(st['all_total'])} contributions since {st['since_year']}, "
        f"{st['active_days']} active days in the last year, best day {st['best']} contributions, "
        f"{st['public_repos']} public repos."
    )
    svg = Svg(W, 10, theme, label)
    t = svg.t
    m = 24 if phone else 32
    svg.text(m, 50 if phone else 54, "On GitHub", 26 if phone else 30, t["text"], "S", 700)
    if not phone:
        svg.text(W - m, 52, f"redrawn every night · {stamp}", 15, t["faint"], "M", 400, "end")

    big = [
        (fmt(st["year_total"]), "contributions in the last year", "teal", "calendar"),
        (f"{st['current']} days" if st["current"] != 1 else "1 day",
         f"current streak, since {st['current_since']}" if st["current"] else "current streak", "green", "flame"),
        (f"{st['longest']} days", "longest streak ever", "amber", "trophy"),
        (fmt(st["all_total"]), f"contributions since {st['since_year']}", "violet", "bars"),
    ]
    small = [
        (str(st["public_repos"]), "public repos", "blue", "folder"),
        (str(st["active_days"]), "active days in 12 months", "teal", "pulse"),
        (str(st["best"]), f"best day · {st['best_day']}", "rose", "bolt"),
    ]
    y0 = 74 if phone else 78
    cols = 2 if phone else 4
    gap = 16 if phone else 18
    tw = (W - 2 * m - (cols - 1) * gap) / cols
    th = 124 if phone else 138
    nsize = 32 if phone else 40
    lsize = 13 if phone else 15
    for i, (num, lab, tile, ic) in enumerate(big):
        x = m + (i % cols) * (tw + gap)
        y = y0 + (i // cols) * (th + gap)
        svg.block(x, y, tw, th, t["tiles"][tile], rx=18)
        icon(svg, ic, x + tw - 38, y + 14, t["tile_text"], 22)
        svg.text(x + 16, y + (62 if phone else 70), num, nsize, t["tile_text"], "S", 700)
        ly = y + (88 if phone else 96)
        for line in wrap(lab, tw - 30, lsize, "M", 400)[:2]:
            svg.text(x + 16, ly, line, lsize, t["tile_text"], "M", 400)
            ly += lsize * 1.3
    y = y0 + ((len(big) + cols - 1) // cols) * (th + gap) + 6
    if phone:
        sw_, sh_ = W - 2 * m, 56
        positions = [(m, y + i * (sh_ + 12)) for i in range(len(small))]
        bottom = y + len(small) * (sh_ + 12) - 12
    else:
        sh_ = 64
        sw_ = (W - 2 * m - 2 * gap) / 3
        positions = [(m + i * (sw_ + gap), y) for i in range(len(small))]
        bottom = y + sh_
    for (num, lab, tile, ic), (x, yy) in zip(small, positions):
        svg.block(x, yy, sw_, sh_, t["tiles"][tile], rx=16)
        icon(svg, ic, x + 16, yy + sh_ / 2 - 12, t["tile_text"], 24)
        nw = svg.text(x + 52, yy + sh_ / 2 + 11, num, 30 if not phone else 26, t["tile_text"], "S", 700)
        lsz = 15 if not phone else 14
        lines = wrap(lab, sw_ - (52 + nw + 10) - 12, lsz, "M", 400)
        if len(lines) > 2:
            raise ValueError(f"stat label does not fit: {lab!r}")
        ly = yy + sh_ / 2 + 6 - (len(lines) - 1) * lsz * 0.62
        for line in lines:
            svg.text(x + 52 + nw + 10, ly, line, lsz, t["tile_text"], "M", 400)
            ly += lsz * 1.24
    if phone:
        svg.text(m, bottom + 34, f"redrawn every night · {stamp}", 13, t["faint"], "M", 400)
        bottom += 24
    svg.h = bottom + 32
    svg.panel()
    return svg.render()


# ---------------------------------------------------------------------------------------------------- heatmap
def _weeks(days: dict[str, int], start: date, end: date) -> list[list[tuple[date, int | None]]]:
    """Columns of 7 days (Sunday first) covering start..end; days outside the range are None."""
    first = start - timedelta(days=(start.weekday() + 1) % 7)
    weeks = []
    d = first
    while d <= end:
        col = []
        for _ in range(7):
            col.append((d, days.get(d.isoformat(), 0) if start <= d <= end else None))
            d += timedelta(days=1)
        weeks.append(col)
    return weeks


def _level(c: int, mx: int) -> int:
    if c <= 0 or mx <= 0:
        return 0
    r = c / mx
    return 1 if r <= 0.25 else 2 if r <= 0.5 else 3 if r <= 0.75 else 4


def heatmap(days: dict[str, int], start: date, end: date, title_num: int, title: str, theme: str, phone: bool,
            split: int = 1) -> str:
    """A contribution grid for start..end. split > 1 stacks the range as that many rows of weeks (phone years)."""
    W = 440 if phone else 880
    svg = Svg(W, 10, theme, f"{fmt(title_num)} {title}.")
    t = svg.t
    o = 16 if phone else 28  # inner block offset
    ix, iw = o, W - 2 * o
    pad = 14 if phone else 16
    all_weeks = _weeks(days, start, end)
    per = -(-len(all_weeks) // split)
    segments = [all_weeks[i:i + per] for i in range(0, len(all_weeks), per)]
    max_cols = max(len(s) for s in segments)
    gx0, gw = ix + pad, iw - 2 * pad
    step = gw / max_cols
    cell = step - (3 if step > 16 else 2.5 if step > 10 else 2)
    numbers = cell >= 21
    mx = max([c for w in all_weeks for _, c in w if c is not None] + [0])

    y = o + (38 if phone else 40)
    nsize = 20 if phone else 24
    nw = svg.text(ix + pad, y, fmt(title_num), nsize, t["text"], "S", 700)
    svg.text(ix + pad + nw + 8, y, title, 14 if phone else 17, t["text"], "M", 400)
    y += 30
    for seg in segments:
        # month labels where a month starts inside the segment
        last = None
        for ci, col in enumerate(seg):
            firsts = [d for d, c in col if c is not None and d.day <= 7]
            mon = firsts[0].month if firsts else None
            if mon and mon != last and (ci < len(seg) - 1):
                svg.text(gx0 + ci * step, y, MONTHS[mon - 1], 13 if phone else 15, t["faint"], "M", 400)
                last = mon
        y += 10
        for ci, col in enumerate(seg):
            for ri, (d, c) in enumerate(col):
                if c is None:
                    continue
                lv = _level(c, mx)
                cx, cy = gx0 + ci * step, y + ri * step
                svg.rect(cx, cy, cell, cell, t["heat"][lv], rx=min(6, cell * 0.28), stroke=t["ink"], sw=1 if cell > 9 else 0.6)
                if numbers and c > 0:
                    fs = 11 if c >= 100 else 12.5
                    svg.text(cx + cell / 2, cy + cell / 2 + fs * 0.36, str(c), fs, t["heat_text"][lv], "M", 700, "middle")
        y += 7 * step + (22 if split > 1 else 10)
    # legend
    y += 16
    svg.text(gx0, y, "contributions per day", 13 if phone else 15, t["muted"], "M", 400)
    lsz = 13 if phone else 15
    lx = gx0 + gw - text_width("More", lsz, "M", 400)
    svg.text(lx, y, "More", lsz, t["muted"], "M", 400)
    lx -= 6
    for lv in range(4, -1, -1):
        lx -= 18
        svg.rect(lx, y - 12, 14, 14, t["heat"][lv], rx=3, stroke=t["ink"], sw=1)
    svg.text(lx - 8, y, "Less", lsz, t["muted"], "M", 400, "end")
    inner_h = y + 18 - o
    body = svg.parts
    svg.parts = []
    svg.block(ix, o, iw, inner_h, t["panel"], rx=16, shadow=4)
    svg.parts += body
    svg.h = o + inner_h + o + 4
    svg.panel()
    return svg.render()


# ---------------------------------------------------------------------------------------------------- line chart
def line30(days: dict[str, int], end: date, theme: str, phone: bool) -> str:
    W = 440 if phone else 880
    series = [(end - timedelta(days=29 - i)) for i in range(30)]
    vals = [days.get(d.isoformat(), 0) for d in series]
    total = sum(vals)
    svg = Svg(W, 10, theme, f"{fmt(total)} contributions in the last 30 days, at most {max(vals)} in one day.")
    t = svg.t
    o = 16 if phone else 28
    ix, iw = o, W - 2 * o
    pad = 14 if phone else 16
    y = o + (38 if phone else 40)
    nw = svg.text(ix + pad, y, fmt(total), 20 if phone else 24, t["text"], "S", 700)
    svg.text(ix + pad + nw + 8, y, "contributions in the last 30 days", 14 if phone else 17, t["text"], "M", 400)

    top = y + 34
    ph = 150 if phone else 200
    bottom = top + ph
    mx = max(vals) or 1
    raw = mx / 4
    mag = 10 ** (len(str(int(raw))) - 1) if raw >= 1 else 1
    stepv = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw)
    ticks = []
    v = 0.0
    while v < mx:
        ticks.append(v)
        v += stepv
    ticks.append(float(mx))
    if len(ticks) >= 2 and (mx - ticks[-2]) < stepv * 0.35:
        ticks.pop(-2)
    axis_w = max(text_width(str(int(tk)), 13 if phone else 15, "M", 400) for tk in ticks) + 10
    x0 = ix + pad + axis_w
    x1 = ix + iw - pad - 6
    for tk in ticks:
        yy = bottom - tk / mx * ph
        svg.raw(f'<line x1="{f1(x0)}" y1="{f1(yy)}" x2="{f1(x1)}" y2="{f1(yy)}" stroke="{t["dots"]}" stroke-width="1" stroke-dasharray="3 5"/>')
        svg.text(x0 - 8, yy + 5, str(int(tk)), 13 if phone else 15, t["faint"], "M", 400, "end")
    pts = [(x0 + i * (x1 - x0) / 29, bottom - v / mx * ph) for i, v in enumerate(vals)]
    poly = " ".join(f"{f1(px)},{f1(py)}" for px, py in pts)
    svg.raw(f'<polygon points="{f1(x0)},{f1(bottom)} {poly} {f1(x1)},{f1(bottom)}" fill="{t["signal"]}" fill-opacity="0.18"/>')
    svg.raw(f'<polyline points="{poly}" fill="none" stroke="{t["signal"]}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    for (px, py), v in zip(pts, vals):
        if v > 0:
            svg.raw(f'<circle cx="{f1(px)}" cy="{f1(py)}" r="4" fill="{t["signal"]}" stroke="{t["ink"]}" stroke-width="1.5"/>')
    every = 7 if phone else 4
    for i, d in enumerate(series):
        if (29 - i) % every == 0:
            svg.text(pts[i][0], bottom + 22, str(d.day), 13 if phone else 15, t["faint"], "M", 400, "middle")
    inner_h = bottom + 40 - o
    body = svg.parts
    svg.parts = []
    svg.block(ix, o, iw, inner_h, t["panel"], rx=16, shadow=4)
    svg.parts += body
    svg.h = o + inner_h + o + 4
    svg.panel()
    return svg.render()


# ---------------------------------------------------------------------------------------------------- whoami
def whoami(p: dict, theme: str, phone: bool) -> str:
    w = p["whoami"]
    W = 440 if phone else 880
    plain = " ".join(
        " ".join(seg[0] for seg in line) if isinstance(line, list) else line
        for block in w["blocks"] for line in [block["cmd"]] + block["out"]
    )
    svg = Svg(W, 10, theme, plain)
    t = svg.t
    o = 16 if phone else 24
    ix, iw = o, W - 2 * o
    size = 14 if phone else 18
    lh = size * 1.62
    x = ix + (18 if phone else 24)
    maxw = iw - 2 * (x - ix)
    y = o + 52 + (14 if phone else 22)
    for bi, block in enumerate(w["blocks"]):
        if bi:
            y += lh * 0.45
        svg.spans(x, y, size, "M", [("$ ", t["signal"], 500), (block["cmd"], t["text"], 500)])
        y += lh
        for line in block["out"]:
            arrow = line.startswith("> ")
            body = line[2:] if arrow else line
            indent = text_width("› ", size, "M", 400) if arrow else 0
            for li, piece in enumerate(wrap(body, maxw - indent, size, "M", 400)):
                pieces = []
                if arrow:
                    pieces.append(("› " if li == 0 else "  ", t["signal"], 500))
                pieces.append((piece, t["muted"] if not arrow else t["text"], 400))
                svg.spans(x, y, size, "M", pieces)
                y += lh
    pw = text_width("$ ", size, "M", 500)
    svg.spans(x, y, size, "M", [("$ ", t["signal"], 500)])
    svg.rect(x + pw, y - size * 0.82, size * 0.55, size * 1.02, t["signal"])
    inner_h = y + (22 if phone else 30) - o
    body = svg.parts
    svg.parts = []
    svg.block(ix, o, iw, inner_h, t["inset"], rx=14, shadow=4)
    svg.raw(f'<line x1="{f1(ix)}" y1="{f1(o + 40)}" x2="{f1(ix + iw)}" y2="{f1(o + 40)}" stroke="{t["ink"]}" stroke-width="2"/>')
    for i, c in enumerate(t["dot_colors"]):
        svg.raw(f'<circle cx="{f1(ix + 22 + i * 18)}" cy="{f1(o + 20)}" r="5.5" fill="{c}"/>')
    svg.text(ix + iw / 2 + (24 if phone else 0), o + 25, w["title"], 13 if phone else 15, t["faint"], "M", 400, "middle")
    svg.parts += body
    svg.h = o + inner_h + o + 4
    svg.panel()
    return svg.render()


# ---------------------------------------------------------------------------------------------------- toolbox
def toolbox(p: dict, theme: str, phone: bool) -> str:
    groups = p["toolbox"]
    W = 440 if phone else 880
    svg = Svg(W, 10, theme, "Toolbox: " + "; ".join(f"{g['label']}: {', '.join(g['items'])}" for g in groups) + ".")
    t = svg.t
    m = 24 if phone else 32
    svg.text(m, 50 if phone else 54, "Toolbox", 26 if phone else 30, t["text"], "S", 700)
    y = 78 if phone else 84
    lab_w = 0 if phone else 176
    for gi, g in enumerate(groups):
        tile = t["tiles"][TILE_ORDER[gi % len(TILE_ORDER)]]
        if phone:
            svg.text(m, y + 14, g["label"].upper(), 12, t["faint"], "M", 500)
            y += 24
            y = svg.chip_flow(m, y, W - 2 * m, g["items"], [tile], size=13, fam="M", weight=500, h=28, gap=8, pad=10, shadow=2)
            y += 18
        else:
            svg.text(m, y + 21, g["label"].upper(), 13, t["faint"], "M", 500)
            y = svg.chip_flow(m + lab_w, y, W - 2 * m - lab_w, g["items"], [tile], size=14, fam="M", weight=500, h=30,
                              gap=10, pad=12, shadow=3)
            y += 16
    svg.h = y + (12 if phone else 18)
    svg.panel()
    return svg.render()


# ---------------------------------------------------------------------------------------------------- section label
def section_label(title: str, note: str, tile: str, theme: str, phone: bool) -> str:
    svg = Svg(10, 66, theme, f"{title}: {note}")
    t = svg.t
    size = 26 if phone else 28
    tw = text_width(title, size, "S", 700) + 36
    svg.block(12, 10, tw, 44, t["tiles"][tile], rx=12, shadow=4)
    svg.text(30, 42, title, size, t["tile_text"], "S", 700)
    if phone:  # a phone has no room for the note next to the title
        svg.w = 12 + tw + 8
        return svg.render()
    nsize = 15
    nw = text_width(note, nsize, "M", 500) + 24
    svg.rect(12 + tw + 22, 20, nw, 30, t["panel"], rx=6, stroke=t["ink"], sw=1.5)
    svg.text(12 + tw + 22 + nw / 2, 40, note, nsize, t["text"], "M", 500, "middle")
    svg.w = 12 + tw + 22 + nw + 8
    return svg.render()


# ---------------------------------------------------------------------------------------------------- project card
def project(pr: dict, idx: int, theme: str, phone: bool) -> str:
    W, H = 440, (262 if phone else 304)
    svg = Svg(W, H, theme, f"{pr['name']} ({pr['status']}): {pr['description']} Built with {', '.join(pr['stack'])}.")
    t = svg.t
    tile = t["tiles"][pr.get("tile", TILE_ORDER[idx % len(TILE_ORDER)])]
    svg.block(16, 16, 408, H - 38, tile, rx=18, shadow=6)
    svg.block(36, 38, 72, 72, t["panel"], rx=16, shadow=0)
    svg.text(72, 38 + 36 + 11, pr["initials"], 30, t["text"], "S", 700, "middle")
    if pr.get("url"):
        svg.block(378, 32, 28, 28, t["signal"], rx=8, shadow=2)
        icon(svg, "arrow", 380, 34, t["on_signal"], 24)
    # The name is as big as fits next to the icon (bigger on phones, where the card is shown at ~40% scale).
    room = 240 if pr.get("url") else 284
    name_size = 40 if phone else 28
    while name_size > 22 and text_width(pr["name"], name_size, "S", 700) > room:
        name_size -= 1
    svg.text(124, 80 if phone else 76, pr["name"], name_size, t["tile_text"], "S", 700)
    if phone:
        svg.chip(124, 94, pr["status"], t["signal"], size=17, fam="M", weight=500, h=30, pad=12, shadow=0, color=t["on_signal"])
    else:
        svg.chip(124, 88, pr["status"], t["signal"], size=13, fam="M", weight=500, h=24, pad=10, shadow=0, color=t["on_signal"])
    if phone:
        # Shown at about 40% scale on a phone: one short line in big type, nothing else.
        y = 160
        for line in wrap(pr["short"], 368, 30, "S", 600)[:3]:
            svg.text(36, y, line, 30, t["tile_text"], "S", 600)
            y += 38
    else:
        y = 146
        desc = wrap(pr["description"], 368, 18, "S", 500)
        if len(desc) > 3:
            raise ValueError(f"{pr['name']}: the description needs {len(desc)} lines, the card has room for 3")
        for line in desc:
            svg.text(36, y, line, 18, t["tile_text"], "S", 500)
            y += 24
        cx = 36
        for s in pr["stack"]:
            w = text_width(s, 13, "M", 500) + 18
            if cx + w > 404:
                break
            svg.rect(cx, 222, w, 24, t["panel"], rx=6, stroke=t["ink"], sw=1.5)
            svg.text(cx + w / 2, 238.5, s, 13, t["text"], "M", 500, "middle")
            cx += w + 8
        svg.text(36, 266, pr["footer"], 14, t["tile_text"], "M", 400)
    svg.panel()
    return svg.render()
