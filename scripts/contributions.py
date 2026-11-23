#!/usr/bin/env python3
"""Render the graveyard contribution graph (assets/contributions.svg) from GitHub's GraphQL API.

Each day of the last year becomes a tiny tombstone; the more you contributed that
day, the brighter it glows. Also writes data/contributions.json for the website.

    python scripts/contributions.py                 # real data, needs a token
    python scripts/contributions.py --demo --out /tmp/demo.svg --json-out none
    python scripts/contributions.py --placeholder   # empty graveyard (used before the first real run)
    python scripts/contributions.py --from-json data/contributions.json   # re-render from saved data

Token: GH_PAT (a personal access token with `read:user`) is preferred, otherwise
GH_TOKEN / GITHUB_TOKEN. The default Actions GITHUB_TOKEN can read public
contributions; add GH_PAT as a repository secret if you also want private ones
counted (and enable "Include private contributions on my profile" in your settings).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path

from theme import (
    ASSETS, BG, DATA, FOG, GHOST, GREEN, MONO, MUTED, PANEL, PURPLE, USERNAME,
    esc, glow_filter, streaks, svg_open, today, tombstone_path, write_text,
)

W, H = 830, 262
CELL_W, CELL_H, PITCH = 11, 12, 14
GRID_X, GRID_Y = 66, 84
LEVEL_FILL = ["#12161b", "#0f3b2a", "#12704a", "#1fc47a", GREEN]
QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# --- data sources -----------------------------------------------------------------
def fetch(login: str, token: str, end: dt.date) -> dict[dt.date, int]:
    start = end - dt.timedelta(days=364)  # the API allows at most one year per query
    body = json.dumps({
        "query": QUERY,
        "variables": {"login": login, "from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "gphl-profile-generator"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GitHub API returned HTTP {e.code}. If this is 401/403, create a PAT with `read:user` and add it as the GH_PAT secret.") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Could not reach the GitHub API: {e.reason}") from e
    if payload.get("errors") or not (payload.get("data") or {}).get("user"):
        raise SystemExit(f"GraphQL query failed: {payload.get('errors') or 'user not found'}")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return {dt.date.fromisoformat(d["date"]): d["contributionCount"] for w in weeks for d in w["contributionDays"]}


def demo_days(end: dt.date) -> dict[dt.date, int]:
    rng = random.Random(1337)
    days = {}
    for i in range(371):
        d = end - dt.timedelta(days=370 - i)
        base = rng.random()
        wk = d.weekday() >= 5
        days[d] = 0 if base < (0.55 if wk else 0.25) else int(rng.expovariate(1 / 4)) + 1
    return days


def empty_days(end: dt.date) -> dict[dt.date, int]:
    return {end - dt.timedelta(days=370 - i): 0 for i in range(371)}


# --- rendering ------------------------------------------------------------------------
def levels_for(days: dict[dt.date, int]):
    mx = max(days.values(), default=0)

    def level(c: int) -> int:
        if c <= 0 or mx <= 0:
            return 0
        r = c / mx
        return 1 if r <= 0.25 else 2 if r <= 0.5 else 3 if r <= 0.75 else 4

    return level


def render(days: dict[dt.date, int], placeholder: bool = False) -> tuple[str, dict]:
    end = max(days)
    # a column per week, Sunday-first, like GitHub: 53 columns ending with the current week
    origin = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=52)
    level = levels_for(days)

    cells = {i: [] for i in range(5)}
    month_marks, last_month = [], None
    for d, c in sorted(days.items()):
        if d < origin or d > end:
            continue
        col, row = (d - origin).days // 7, (d.weekday() + 1) % 7
        x, y = GRID_X + col * PITCH, GRID_Y + row * PITCH
        lv = level(c)
        stroke = f' stroke="{GHOST}" stroke-width="1.2"' if d == end and not placeholder else ""
        if lv == 0:
            stroke = stroke or ' stroke="#1c222a" stroke-width="1"'
        cells[lv].append(
            f'<path d="{tombstone_path(x, y, CELL_W, CELL_H)}" fill="{LEVEL_FILL[lv]}"{stroke}/>'  # no <title>: tooltips never show inside <img>, and it halves the file size
        )
        if row == 0 and d.month != last_month:
            if last_month is not None or col == 0:
                month_marks.append((x, d.strftime("%b")))
            last_month = d.month

    total = sum(days.values())
    active = {d for d, c in days.items() if c > 0}
    cur, longest = streaks(active, end)
    best_day, best = max(days.items(), key=lambda kv: kv[1])

    p = [svg_open(W, H, "Souls Contributed: GitHub contribution graph",
                  f"{total} contributions in the last year; current streak {cur} days; longest streak {longest} days."), "<defs>",
         glow_filter("g3", 1.8), glow_filter("g4", 3.2),
         f'<linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#12171d"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
         "</defs>",
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#panel)" stroke="{FOG}"/>']

    def t(x, y, s, size=12, fill=GHOST, anchor="start", weight="normal", sp=0, extra=""):
        spc = f' letter-spacing="{sp}"' if sp else ""
        return f'<text x="{x:g}" y="{y:g}" font-family="{MONO}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{spc}{extra}>{esc(s)}</text>'

    # title
    cx = 28 + 7
    p += [
        f'<path d="{tombstone_path(28, 22, 14, 18)}" fill="#141a20" stroke="{GREEN}" stroke-width="1.4" filter="url(#g4)"/>',
        f'<path d="M{cx},{28} V{35} M{cx - 3},{30.5} H{cx + 3}" stroke="{GREEN}" stroke-width="1.3" stroke-linecap="round"/>',
        t(52, 37, "GITHUB CONTRIBUTIONS", 17, GREEN, weight="bold", sp=3, extra=' filter="url(#g3)"'),
        t(802, 37, f"{origin.strftime('%b %Y')} – {end.strftime('%b %Y')}", 11, MUTED, "end"),
    ]
    # month + weekday labels
    for x, m in month_marks:
        p.append(t(x, 76, m, 10, MUTED))
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(t(58, GRID_Y + row * PITCH + 10, label, 9.5, MUTED, "end"))
    # cells: glowing levels are grouped so one filter serves many tombstones
    p.append("<g>" + "".join(cells[0] + cells[1] + cells[2]) + "</g>")
    p.append('<g filter="url(#g3)">' + "".join(cells[3]) + "</g>")
    p.append('<g filter="url(#g4)">' + "".join(cells[4]) + "</g>")
    # legend
    lx = 802 - 5 * 18 - 60
    p.append(t(lx, 196, "Less", 10, MUTED, "end"))
    for i in range(5):
        p.append(f'<path d="{tombstone_path(lx + 8 + i * 18, 186, CELL_W, CELL_H)}" fill="{LEVEL_FILL[i]}"{" stroke=" + chr(34) + "#1c222a" + chr(34) if i == 0 else ""}/>')
    p.append(t(lx + 8 + 5 * 18 + 4, 196, "More", 10, MUTED))
    # stat tiles
    tiles = [
        (f"{total:,}", "Contributions"),
        (f"{cur}d", "Current streak"),
        (f"{longest}d", "Longest streak"),
        (f"{best}" + (f" · {best_day.strftime('%b')} {best_day.day}" if best else ""), "Busiest day"),
    ]
    gap, y, h = 12, 206, 44
    tw = ((802 - 28) - gap * 3) / 4
    for i, (v, label) in enumerate(tiles):
        x = 28 + i * (tw + gap)
        p += [
            f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{h}" rx="8" fill="{PANEL}" stroke="{FOG}"/>',
            f'<rect x="{x:.1f}" y="{y + 9}" width="3" height="{h - 18}" rx="1.5" fill="{PURPLE}"/>',
            t(x + 14, y + 22, v, 17, GHOST, weight="bold"),
            t(x + 14, y + 37, label.upper(), 9, MUTED, sp=1.2),
        ]
    if placeholder:
        p += [
            f'<rect x="{GRID_X + 150}" y="{GRID_Y + 22}" width="{PITCH * 53 - 300}" height="46" rx="10" fill="{BG}" fill-opacity="0.92" stroke="{GREEN}" stroke-opacity="0.5"/>',
            t(GRID_X + PITCH * 53 / 2, GRID_Y + 42, "The graveyard is quiet…", 13, GREEN, "middle", "bold"),
            t(GRID_X + PITCH * 53 / 2, GRID_Y + 59, "The first summoning runs with the next stats update.", 10.5, MUTED, "middle"),
        ]
    stats = {"total": total, "current_streak": cur, "longest_streak": longest, "busiest_day": [best_day.isoformat(), best]}
    return "".join(p) + "</svg>\n", stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="render synthetic data (for previews)")
    ap.add_argument("--placeholder", action="store_true", help="render an empty graveyard with a notice")
    ap.add_argument("--from-json", help="re-render from a previously saved contributions.json")
    ap.add_argument("--user", default=os.environ.get("GH_USER", USERNAME))
    ap.add_argument("--out", default=str(ASSETS / "contributions.svg"))
    ap.add_argument("--json-out", default=str(DATA / "contributions.json"), help="path, or 'none' to skip")
    a = ap.parse_args()

    end = today()
    if a.placeholder:
        days = empty_days(end)
    elif a.demo:
        days = demo_days(end)
    elif a.from_json:
        saved = json.loads(open(a.from_json, encoding="utf-8").read())
        days = {dt.date.fromisoformat(d): c for d, c in saved["days"]}
    else:
        token = os.environ.get("GH_PAT") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            print("No token found. Set GH_PAT, GH_TOKEN or GITHUB_TOKEN (or use --demo / --placeholder).", file=sys.stderr)
            return 2
        days = fetch(a.user, token, end)

    svg, stats = render(days, placeholder=a.placeholder)
    write_text(Path(a.out), svg)
    # only real data is saved for the website; demo and placeholder runs never touch it
    if a.json_out.lower() != "none" and not (a.demo or a.placeholder):
        payload = {"login": a.user, "generated": end.isoformat(), **stats,
                   "days": [[d.isoformat(), c] for d, c in sorted(days.items())]}
        write_text(Path(a.json_out), json.dumps(payload, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
