#!/usr/bin/env python3
"""Generate assets/modules.svg and assets/ctfs.svg from data/modules.json and data/ctfs.json.

Pure standard library. The SVGs carry their own dark background, use only system
monospace fonts and contain no JavaScript, so they render the same on GitHub in
light and dark mode.

    python scripts/charts.py            # regenerate both charts
    python scripts/charts.py --check    # exit 1 if the SVGs on disk are out of date
"""
from __future__ import annotations

import datetime as dt
import math
import sys
from collections import Counter

from theme import (
    ASSETS, BG, BLOOD, DIFFICULTY_COLORS, DIFFICULTY_ORDER, FOG, GHOST, GREEN, MONO,
    MUTED, PANEL, PURPLE, TIMEZONE, esc, glow_filter, load_entries, streaks, svg_open,
    today, tombstone_path, trunc, write_text,
)

W, H = 830, 360
LEFT, RIGHT = 28, 802  # content margins


# --- small helpers ------------------------------------------------------------
def nice_step(raw: float) -> int:
    raw = max(raw, 1)
    p = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 5, 10):
        if raw <= m * p:
            return int(m * p)
    return int(10 * p)


def fmt_date(d: dt.date, span: int) -> str:
    return f"{d.strftime('%b')} '{d.strftime('%y')}" if span > 120 else f"{d.strftime('%b')} {d.day}"


def defs() -> str:
    return (
        "<defs>"
        + glow_filter("glow", 2.2)
        + glow_filter("glowBig", 5)
        + f'<linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#12171d"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        + f'<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0.38"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>'
        + f'<linearGradient id="barG" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{PURPLE}"/><stop offset="1" stop-color="{GREEN}"/></linearGradient>'
        + f'<linearGradient id="barP" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5b3fb0"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>'
        + "</defs>"
    )


def tomb_icon(x: float, y: float) -> str:
    cx = x + 7
    return (
        f'<path d="{tombstone_path(x, y, 14, 18)}" fill="#141a20" stroke="{GREEN}" stroke-width="1.4" filter="url(#glow)"/>'
        f'<path d="M{cx},{y + 6} V{y + 13} M{cx - 3},{y + 8.5} H{cx + 3}" stroke="{GREEN}" stroke-width="1.3" stroke-linecap="round"/>'
    )


def text(x, y, s, size=12, fill=GHOST, anchor="start", weight="normal", spacing=0, extra="") -> str:
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (
        f'<text x="{x:g}" y="{y:g}" font-family="{MONO}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" font-weight="{weight}"{sp}{extra}>{esc(s)}</text>'
    )


def frame(title: str, as_of: dt.date, tiles: list[tuple[str, str]], sample: bool) -> list[str]:
    p = [
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#panel)" stroke="{FOG}"/>',
        tomb_icon(LEFT, 22),
        text(LEFT + 24, 37, title, 17, GREEN, weight="bold", spacing=3, extra=' filter="url(#glow)"'),
        text(RIGHT, 37, f"as of {as_of.isoformat()} IST", 11, MUTED, "end"),
    ]
    if sample:
        p += [
            f'<rect x="{RIGHT - 262}" y="22" width="104" height="20" rx="10" fill="none" stroke="{BLOOD}"/>',
            text(RIGHT - 210, 36, "SAMPLE DATA", 10, "#e0505c", "middle", "bold", 1.2),
        ]
    # stat tiles
    gap, y, h = 12, 62, 58
    tw = ((RIGHT - LEFT) - gap * (len(tiles) - 1)) / len(tiles)
    for i, (value, label) in enumerate(tiles):
        x = LEFT + i * (tw + gap)
        p += [
            f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{h}" rx="8" fill="{PANEL}" stroke="{FOG}"/>',
            f'<rect x="{x:.1f}" y="{y + 10}" width="3" height="{h - 20}" rx="1.5" fill="{GREEN}" opacity="0.85"/>',
            text(x + 16, y + 31, value, 24, GHOST, weight="bold"),
            text(x + 16, y + 48, label.upper(), 10, MUTED, spacing=1.2),
        ]
    return p


def section_label(x: float, y: float, label: str) -> str:
    return text(x, y, label, 10.5, MUTED, spacing=1.6)


def cumulative(entries: list[dict], end: dt.date, x0: float, y0: float, w: float, h: float, label_y: float) -> list[str]:
    """Stepped cumulative-total chart over time."""
    p = [section_label(LEFT, 152, "CUMULATIVE TOTAL OVER TIME")]
    if not entries:
        p.append(text(x0 + w / 2, y0 + h / 2, "No souls collected yet. Log your first ritual.", 12, MUTED, "middle"))
        return p
    first = entries[0]["date"]
    start = min(first - dt.timedelta(days=1), end - dt.timedelta(days=13))
    span = max((end - start).days, 1)
    counts = Counter(e["date"] for e in entries)
    total = len(entries)
    step = nice_step(total / 4)
    ymax = max(step * math.ceil(total / step), step * 2)

    def X(d: dt.date) -> float:
        return x0 + (d - start).days / span * w

    def Y(v: float) -> float:
        return y0 + h - v / ymax * h

    # grid + y labels
    for v in range(0, ymax + 1, step):
        yy = Y(v)
        p.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x0 + w}" y2="{yy:.1f}" stroke="{FOG}" stroke-width="1" stroke-dasharray="{"0" if v == 0 else "3 4"}"/>')
        p.append(text(x0 - 8, yy + 4, str(v), 10, MUTED, "end"))
    # x labels
    ticks = 5
    for i in range(ticks + 1):
        d = start + dt.timedelta(days=round(i * span / ticks))
        anchor = "start" if i == 0 else "end" if i == ticks else "middle"
        p.append(text(X(d), label_y, fmt_date(d, span), 10, MUTED, anchor))
    # step path
    run, prev_y = 0, Y(0)
    d_path = f"M{X(start):.1f},{prev_y:.1f}"
    dots = []
    for d in sorted(counts):
        px = X(d)
        d_path += f" L{px:.1f},{prev_y:.1f}"
        run += counts[d]
        prev_y = Y(run)
        d_path += f" L{px:.1f},{prev_y:.1f}"
        dots.append((px, prev_y))
    d_path += f" L{X(end):.1f},{prev_y:.1f}"
    area = d_path + f" L{X(end):.1f},{Y(0):.1f} L{X(start):.1f},{Y(0):.1f} Z"
    p.append(f'<path d="{area}" fill="url(#area)"/>')
    p.append(f'<path d="{d_path}" fill="none" stroke="{GREEN}" stroke-width="2.2" stroke-linejoin="round" filter="url(#glow)"/>')
    for px, py in dots:
        p.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{BG}" stroke="{GREEN}" stroke-width="1.5"/>')
    lx, ly = dots[-1]
    p.append(
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="{GREEN}" opacity="0.9"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="none" stroke="{GREEN}">'
        f'<animate attributeName="r" values="4;11;4" dur="2.6s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.8;0;0.8" dur="2.6s" repeatCount="indefinite"/></circle>'
    )
    p.append(text(lx, ly - 11, str(total), 12, GHOST, "middle", "bold"))
    return p


def bar_rows(x: float, y: float, w: float, rows: list[tuple[str, int]], grad: str, row_h: int = 26) -> list[str]:
    p = []
    if not rows:
        return [text(x, y + 12, "Nothing here yet.", 11.5, MUTED)]
    mx = max(v for _, v in rows) or 1
    label_w, count_w = 104, 26
    track_w = w - label_w - count_w
    for i, (name, v) in enumerate(rows):
        yy = y + i * row_h
        fw = max(8, v / mx * track_w)
        p += [
            text(x, yy + 11, trunc(name, 14), 11.5, GHOST),
            f'<rect x="{x + label_w}" y="{yy + 2}" width="{track_w}" height="10" rx="5" fill="{FOG}"/>',
            f'<rect x="{x + label_w}" y="{yy + 2}" width="{fw:.1f}" height="10" rx="5" fill="url(#{grad})"/>',
            text(x + w, yy + 11, str(v), 11.5, GREEN, "end", "bold"),
        ]
    return p


def top_rows(counter: Counter, limit: int) -> list[tuple[str, int]]:
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0].lower()))
    if len(items) > limit:
        rest = sum(v for _, v in items[limit - 1:])
        items = items[: limit - 1] + [("Others", rest)]
    return items


def last_30(entries: list[dict], end: dt.date) -> int:
    cutoff = end - dt.timedelta(days=29)
    return sum(1 for e in entries if cutoff <= e["date"] <= end)


# --- the two charts -------------------------------------------------------------
def modules_svg(entries: list[dict], end: dt.date) -> str:
    cur, _ = streaks({e["date"] for e in entries}, end)
    platforms = Counter(e.get("platform") or "Other" for e in entries)
    tiles = [
        (str(len(entries)), "Modules done"),
        (str(last_30(entries, end)), "Last 30 days"),
        (str(cur), "Day streak"),
        (str(len(platforms)), "Platforms"),
    ]
    sample = any(e.get("sample") for e in entries)
    parts = [svg_open(W, H, "Rituals Completed: training modules", f"{len(entries)} training modules completed, cumulative over time and by platform."), defs()]
    parts += frame("TRAINING MODULES", end, tiles, sample)
    parts += cumulative(entries, end, 62, 172, 458, 138, 332)
    parts.append(section_label(548, 152, "BY PLATFORM"))
    parts += bar_rows(548, 166, 254, top_rows(platforms, 6), "barG")
    return "".join(parts) + "</svg>\n"


def ctfs_svg(entries: list[dict], end: dt.date) -> str:
    cur, _ = streaks({e["date"] for e in entries}, end)
    points = sum(int(e.get("points") or 0) for e in entries)
    last = ("Points", f"{points:,}") if points else ("Platforms", str(len({e.get("platform") for e in entries})))
    tiles = [
        (str(len(entries)), "CTFs banished"),
        (str(last_30(entries, end)), "Last 30 days"),
        (str(cur), "Day streak"),
        (last[1], last[0]),
    ]
    sample = any(e.get("sample") for e in entries)
    parts = [svg_open(W, H, "Spirits Banished: CTFs completed", f"{len(entries)} CTF challenges completed, cumulative over time, by difficulty and by category."), defs()]
    parts += frame("CTF CHALLENGES", end, tiles, sample)
    parts += cumulative(entries, end, 62, 172, 458, 138, 332)

    # difficulty: one stacked bar + legend
    diff = Counter(str(e.get("difficulty") or "other").lower() for e in entries)
    order = [d for d in DIFFICULTY_ORDER if d in diff] + sorted(d for d in diff if d not in DIFFICULTY_ORDER)
    x, w = 548, 254
    parts.append(section_label(x, 152, "BY DIFFICULTY"))
    total = sum(diff.values())
    if total:
        cx = float(x)
        for d in order:
            sw = diff[d] / total * w
            color = DIFFICULTY_COLORS.get(d, MUTED)
            parts.append(f'<rect x="{cx:.1f}" y="162" width="{max(sw - 2, 2):.1f}" height="12" rx="3" fill="{color}"/>')
            cx += sw
        for i, d in enumerate(order[:6]):
            lx, ly = x + (i % 2) * 128, 192 + (i // 2) * 16
            color = DIFFICULTY_COLORS.get(d, MUTED)
            parts.append(f'<rect x="{lx}" y="{ly - 8}" width="8" height="8" rx="2" fill="{color}"/>')
            parts.append(text(lx + 14, ly, f"{d} {diff[d]}", 11.5, GHOST))
    else:
        parts.append(text(x, 176, "Nothing here yet.", 11.5, MUTED))
    # category bars
    parts.append(section_label(x, 238, "BY CATEGORY"))
    cats = Counter(e.get("category") or "General" for e in entries)
    parts += bar_rows(x, 250, w, top_rows(cats, 4), "barP", row_h=24)
    return "".join(parts) + "</svg>\n"


def build() -> dict[str, str]:
    end = today()
    return {
        "modules.svg": modules_svg(load_entries("modules"), end),
        "ctfs.svg": ctfs_svg(load_entries("ctfs"), end),
    }


def main(argv: list[str]) -> int:
    outputs = build()
    if "--check" in argv:
        stale = [n for n, s in outputs.items() if not (ASSETS / n).exists() or (ASSETS / n).read_text(encoding="utf-8") != s]
        print("stale: " + ", ".join(stale) if stale else "charts are up to date")
        return 1 if stale else 0
    for name, svg in outputs.items():
        write_text(ASSETS / name, svg)
    return 0


def render_all() -> None:
    """Used by log.py after it appends an entry."""
    main([])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
