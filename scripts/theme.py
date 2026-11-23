"""Shared palette, paths, date helpers and SVG helpers for the GPHL125241O generators.

Everything here is plain standard-library Python. Edit the constants below to
re-theme every generated SVG at once.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from xml.sax.saxutils import escape as esc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

# --- identity ---------------------------------------------------------------
USERNAME = "GPHL125241O"
ALIAS = "The Ghost of Hacking"
TIMEZONE = "Asia/Kolkata"  # "today" and the daily cron are both IST

# --- palette ----------------------------------------------------------------
BG = "#0b0d10"       # near-black
FOG = "#1a1f26"      # fog gray
GHOST = "#e6f1ef"    # ghost white
GREEN = "#39ff9c"    # spectral green
PURPLE = "#8b5cf6"   # ghost purple
BLOOD = "#b0212d"    # blood red (sparingly)
MUTED = "#8b9a96"    # secondary text
PANEL = "#10141a"    # tile / panel fill

# System fonts only: SVGs shown through <img> on GitHub cannot load web fonts.
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
SERIF = "Georgia, 'Times New Roman', serif"

DIFFICULTY_ORDER = ["easy", "medium", "hard", "insane"]
DIFFICULTY_COLORS = {
    "easy": GREEN,
    "medium": PURPLE,
    "hard": BLOOD,
    "insane": GHOST,
}

PLATFORM_ALIASES = {
    "thm": "TryHackMe",
    "tryhackme": "TryHackMe",
    "htb": "HackTheBox",
    "hackthebox": "HackTheBox",
    "htba": "HTB Academy",
    "htbacademy": "HTB Academy",
    "pico": "picoCTF",
    "picoctf": "picoCTF",
    "psa": "PortSwigger",
    "portswigger": "PortSwigger",
    "pwn": "pwn.college",
    "pwncollege": "pwn.college",
    "ctftime": "CTFtime",
}


def canon_platform(name: str) -> str:
    key = name.strip().lower().replace(" ", "")
    return PLATFORM_ALIASES.get(key, name.strip())


# --- dates ------------------------------------------------------------------
def _tz():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(TIMEZONE)
    except Exception:  # tzdata missing: IST has no DST, so a fixed offset is exact
        return dt.timezone(dt.timedelta(hours=5, minutes=30))


def today() -> dt.date:
    return dt.datetime.now(_tz()).date()


def streaks(days: set[dt.date], end: dt.date) -> tuple[int, int]:
    """Return (current, longest) streak over a set of active dates.

    The current streak counts back from `end`, or from the day before if `end`
    itself has no activity yet (so it does not reset to 0 at midnight).
    """
    cur = 0
    d = end if end in days else end - dt.timedelta(days=1)
    while d in days:
        cur += 1
        d -= dt.timedelta(days=1)
    longest = run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    return cur, longest


# --- data -------------------------------------------------------------------
def load_entries(name: str) -> list[dict]:
    """Load data/<name>.json -> list of entries with `date` parsed to datetime.date."""
    path = DATA / f"{name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw["entries"] if isinstance(raw, dict) else raw
    out = []
    for e in entries:
        try:
            d = dt.date.fromisoformat(str(e["date"]))
        except (KeyError, ValueError):
            print(f"warning: skipping {name} entry with a bad or missing date: {e!r}")
            continue
        out.append({**e, "date": d})
    out.sort(key=lambda e: e["date"])
    return out


# --- svg helpers ------------------------------------------------------------
def svg_open(w: int, h: int, title: str, desc: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
    )


def glow_filter(fid: str = "glow", std: float = 2.5) -> str:
    return (
        f'<filter id="{fid}" x="-60%" y="-60%" width="220%" height="220%">'
        f'<feGaussianBlur stdDeviation="{std}" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


def tombstone_path(x: float, y: float, w: float, h: float) -> str:
    """Rounded-top tombstone with its bottom-left corner at (x, y+h)."""
    r = w / 2
    return f"M{x:.2f},{y + h:.2f} V{y + r:.2f} A{r:.2f},{r:.2f} 0 0 1 {x + w:.2f},{y + r:.2f} V{y + h:.2f} Z"


def trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    try:
        shown = path.resolve().relative_to(ROOT)
    except ValueError:  # output outside the repo (e.g. /tmp preview)
        shown = path
    print(f"wrote {shown}")
