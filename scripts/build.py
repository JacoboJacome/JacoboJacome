"""Redraws every card in assets/ and rewrites README.md.

Run: python scripts/build.py            (fetches fresh numbers, falls back to scripts/state.json)
     python scripts/build.py --offline  (draws from scripts/state.json only)
Exits 1 when a source could not be fetched or the saved calendar is more than 3 days old, after drawing anyway.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import cards
import data

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
THEMES = ("dark", "light")


def compute_stats(days: dict[str, int], today: date, state: dict) -> dict:
    start = today - timedelta(days=364)
    last_year = {k: v for k, v in days.items() if start.isoformat() <= k <= today.isoformat()}

    cur = 0
    d = today if days.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        cur += 1
        d -= timedelta(days=1)
    current_since = cards.day_label(d + timedelta(days=1))

    longest = run = 0
    prev = None
    for k in sorted(days):
        dk = date.fromisoformat(k)
        if days[k] > 0:
            run = run + 1 if prev and (dk - prev).days == 1 and days.get(prev.isoformat(), 0) > 0 else 1
            longest = max(longest, run)
        prev = dk

    best_key = max(days, key=lambda k: (days[k], k)) if days else today.isoformat()
    bd = date.fromisoformat(best_key)
    created = state.get("user", {}).get("created_at", "")
    return {
        "year_total": sum(last_year.values()),
        "current": cur,
        "current_since": current_since,
        "longest": longest,
        "all_total": sum(days.values()),
        "since_year": created[:4] or min(days)[:4],
        "active_days": sum(1 for v in last_year.values() if v > 0),
        "best": days.get(best_key, 0),
        "best_day": f"{bd.day} {cards.MONTHS[bd.month - 1]} {bd.year}",
        "public_repos": state.get("user", {}).get("public_repos", 0),
    }


def write(name: str, svg: str) -> None:
    (ASSETS / f"{name}.svg").write_text(svg, encoding="utf-8")


def variants(name: str, fn) -> None:
    """fn(theme, phone) -> svg; writes name-{theme}.svg and name-phone-{theme}.svg."""
    for theme in THEMES:
        write(f"{name}-{theme}", fn(theme, False))
        write(f"{name}-phone-{theme}", fn(theme, True))


def picture(name: str, alt: str, width: str | None = "100%", phone: bool = True, attrs: str = "") -> str:
    src = []
    if phone:
        src.append(f'<source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/{name}-phone-dark.svg">')
        src.append(f'<source media="(max-width: 600px)" srcset="assets/{name}-phone-light.svg">')
    src.append(f'<source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">')
    alt = alt.replace('"', "&quot;")
    return (
        "<picture>" + "".join(src)
        + f'<img src="assets/{name}-light.svg"' + (f' width="{width}"' if width else "") + f' alt="{alt}"{attrs}></picture>'
    )


def link(url: str | None, inner: str) -> str:
    return f'<a href="{url}">{inner}</a>' if url else inner


def main() -> int:
    offline = "--offline" in sys.argv
    profile = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
    user = profile["user"]
    if offline:
        state, problems = data.load_state(), []
    else:
        state, problems = data.refresh(user)
    if data.is_stale(state):
        problems.append("the saved contribution calendar is more than 3 days old")

    today = data.today()
    days = {k: v for k, v in state["days"].items() if k <= today.isoformat()}
    st = compute_stats(days, today, state)
    stamp = f"{today.day} {cards.MONTHS[today.month - 1]} {today.year}"
    ASSETS.mkdir(exist_ok=True)

    variants("hero", lambda th, ph: cards.hero(profile, th, ph))
    for b in profile["badges"]:
        for theme in THEMES:
            write(f"badge-{b['id']}-{theme}", cards.badge(b, theme))
    variants("github", lambda th, ph: cards.stats(st, th, ph, stamp))

    six_start = (today - timedelta(days=182))
    six_total = sum(v for k, v in days.items() if k >= six_start.isoformat())
    variants("graph-6m", lambda th, ph: cards.heatmap(
        days, (today - timedelta(days=90)) if ph else six_start, today,
        sum(v for k, v in days.items() if k >= (today - timedelta(days=90)).isoformat()) if ph else six_total,
        "contributions in the last 3 months" if ph else "contributions in the last 6 months", th, ph))
    year_start = today - timedelta(days=364)
    variants("graph-12m", lambda th, ph: cards.heatmap(
        days, year_start, today, st["year_total"], "contributions in the last 12 months", th, ph, split=2 if ph else 1))
    years = list(range(today.year, int(st["since_year"]) - 1, -1))
    for y in years:
        total = sum(v for k, v in days.items() if k.startswith(str(y)))
        end = min(date(y, 12, 31), today)
        variants(f"graph-{y}", lambda th, ph, y=y, total=total, end=end: cards.heatmap(
            days, date(y, 1, 1), end, total, f"contributions in {y}", th, ph, split=2 if ph else 1))
    variants("line-30d", lambda th, ph: cards.line30(days, today, th, ph))
    variants("whoami", lambda th, ph: cards.whoami(profile, th, ph))
    variants("toolbox", lambda th, ph: cards.toolbox(profile, th, ph))
    n = len(profile["projects"])
    variants("label-ship", lambda th, ph: cards.section_label("What I ship", f"{n} products, built end to end", "amber", th, ph))
    for i, pr in enumerate(profile["projects"]):
        variants(f"app-{pr['id']}", lambda th, ph, pr=pr, i=i: cards.project(pr, i, th, ph))

    # README -------------------------------------------------------------------------------------------------
    h = profile["hero"]
    out = ["<!-- Generated by scripts/build.py from profile.json. Edit those, not this file. -->", ""]
    out.append(link(h["site_url"], picture("hero", f"Hi, I'm {h['name']}. {h['tagline']}")))
    out.append("")
    out.append('<p align="center">')
    for b in profile["badges"]:
        out.append(link(b["url"], picture(f"badge-{b['id']}", f"{b['label']}: {b['handle']}", width=None, phone=False,
                                           attrs=' height="44"')))
    out.append("</p>")
    out.append("")
    out.append(picture("github", f"On GitHub: {st['year_total']:,} contributions in the last year, "
                                  f"{st['current']}-day current streak, longest streak {st['longest']} days, "
                                  f"{st['all_total']:,} contributions since {st['since_year']}."))
    out.append("")
    out.append(picture("graph-6m", f"Contribution graph: {six_total:,} contributions in the last 6 months."))
    out.append("")
    out.append("<details><summary><b>Last 12 months</b></summary>")
    out.append("")
    out.append(picture("graph-12m", f"Contribution graph: {st['year_total']:,} contributions in the last 12 months."))
    out.append("</details>")
    for y in years:
        total = sum(v for k, v in days.items() if k.startswith(str(y)))
        out.append(f"<details><summary><b>{y}</b> · {total:,} contributions</summary>")
        out.append("")
        out.append(picture(f"graph-{y}", f"Contribution graph for {y}: {total:,} contributions."))
        out.append("</details>")
    out.append("")
    last30 = sum(v for k, v in days.items() if k > (today - timedelta(days=30)).isoformat())
    out.append(picture("line-30d", f"{last30:,} contributions in the last 30 days, day by day."))
    out.append("")
    out.append(picture("whoami", "whoami: full-stack engineer from Colombia. Now: Software Engineer at Solvo Global, "
                                 "building with Claude Code and MCP, learning RAG and Vertex AI."))
    out.append("")
    out.append(picture("toolbox", "Toolbox: " + "; ".join(f"{g['label']}: {', '.join(g['items'])}" for g in profile["toolbox"])))
    out.append("")
    out.append(picture("label-ship", f"What I ship: {n} products, built end to end.", width=None, attrs=' height="66"'))
    out.append("")
    projects = profile["projects"]
    for i in range(0, n, 2):
        out.append('<p align="center">')
        for pr in projects[i:i + 2]:
            alt = f"{pr['name']} ({pr['status']}): {pr['description']}"
            out.append(link(pr.get("url"), picture(f"app-{pr['id']}", alt, width="49%")))
        out.append("</p>")
    out.append("")
    out.append('<p align="center"><sub>Client projects live in private repositories, so only a summary is shown here. '
               "Every card here is an SVG drawn by <code>scripts/build.py</code> from public GitHub data and redrawn "
               "every night by a GitHub Action.</sub></p>")
    (ROOT / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")

    if problems:
        print("build finished with problems:", *problems, sep="\n  ", file=sys.stderr)
        return 1
    print(f"ok: {len(list(ASSETS.glob('*.svg')))} cards, {st['year_total']} contributions in the last year")
    return 0


if __name__ == "__main__":
    sys.exit(main())
