"""Fetches the public numbers the cards are drawn from and keeps a copy in state.json.

The contribution calendar is read from the same public page GitHub shows on the profile, so the counts match what
any visitor sees (private contributions included, as counts only, when the profile setting allows it). If a fetch
fails, the saved copy is used and the build reports the data as stale.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

STATE = Path(__file__).parent / "state.json"
TZ = timezone(timedelta(hours=-5))  # Colombia, no daylight saving
UA = {"User-Agent": "profile-cards-builder", "Accept": "text/html"}

_TD = re.compile(r'<td[^>]*?data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"', re.S)
_TD_ALT = re.compile(r'<td[^>]*?id="([^"]+)"[^>]*?data-date="(\d{4}-\d{2}-\d{2})"', re.S)
_TIP = re.compile(r'<tool-tip[^>]*?for="([^"]+)"[^>]*>\s*([^<]*)</tool-tip>', re.S)
_COUNT = re.compile(r"^([\d,]+) contributions?")


def today() -> date:
    return datetime.now(TZ).date()


def _get(url: str, headers: dict[str, str]) -> bytes:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_calendar(html: str) -> dict[str, int]:
    ids = {i: d for d, i in _TD.findall(html)}
    ids.update({i: d for i, d in _TD_ALT.findall(html)})
    days: dict[str, int] = {}
    for for_id, tip in _TIP.findall(html):
        if for_id not in ids:
            continue
        m = _COUNT.match(tip.strip())
        days[ids[for_id]] = int(m.group(1).replace(",", "")) if m else 0
    return days


def fetch_year(user: str, year: int) -> dict[str, int]:
    url = f"https://github.com/users/{user}/contributions?from={year}-01-01&to={year}-12-31"
    html = _get(url, UA).decode("utf-8", "replace")
    days = parse_calendar(html)
    if not days:
        raise RuntimeError(f"could not read any day from the {year} contribution calendar")
    return days


def fetch_user(user: str) -> dict:
    headers = {"User-Agent": "profile-cards-builder", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return json.loads(_get(f"https://api.github.com/users/{user}", headers))


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"days": {}, "user": {}, "fetched": {}}


def refresh(user: str) -> tuple[dict, list[str]]:
    """Returns (state, problems). problems lists every source that could not be fetched this run."""
    state = load_state()
    problems: list[str] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        u = fetch_user(user)
        state["user"] = {"created_at": u["created_at"], "public_repos": u["public_repos"], "followers": u["followers"]}
        state["fetched"]["user"] = now
    except Exception as exc:  # noqa: BLE001 - any failure falls back to the saved copy
        problems.append(f"user: {exc}")

    created = state.get("user", {}).get("created_at")
    first_year = int(created[:4]) if created else today().year - 1
    for year in range(first_year, today().year + 1):
        # Past years never change once fetched; the current and previous year are always refreshed.
        if year < today().year - 1 and any(d.startswith(str(year)) for d in state["days"]):
            continue
        try:
            state["days"].update(fetch_year(user, year))
            state["fetched"][str(year)] = now
        except Exception as exc:  # noqa: BLE001
            problems.append(f"calendar {year}: {exc}")

    state["days"] = dict(sorted(state["days"].items()))
    STATE.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
    return state, problems


def is_stale(state: dict, max_days: int = 3) -> bool:
    stamp = state.get("fetched", {}).get(str(today().year))
    if not stamp:
        return True
    return datetime.now(timezone.utc) - datetime.fromisoformat(stamp) > timedelta(days=max_days)
