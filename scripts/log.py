#!/usr/bin/env python3
"""Log a completed module or CTF and refresh the charts.

    python scripts/log.py module "Intro to Burp Suite" --platform THM --category Web
    python scripts/log.py ctf "Cap" --platform HTB --difficulty easy --category Linux --points 20
    python scripts/log.py module "Some module" --platform THM --date 2026-11-20   # log a past day
    python scripts/log.py clear-samples                                          # delete the demo entries

Platform shortcuts (THM, HTB, PICO, PSA, ...) are expanded to their full names.
The date defaults to today in IST. Use --no-render to skip regenerating the SVGs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from theme import DATA, DIFFICULTY_ORDER, canon_platform, today

FILES = {"module": DATA / "modules.json", "ctf": DATA / "ctfs.json"}


def load(path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):  # tolerate a bare list
        raw = {"entries": raw}
    raw.setdefault("entries", [])
    return raw


def save(path, doc) -> None:
    doc["entries"].sort(key=lambda e: e["date"])
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for kind in ("module", "ctf"):
        sp = sub.add_parser(kind, help=f"log a completed {kind}")
        sp.add_argument("name", help="name of the module / challenge")
        sp.add_argument("--platform", required=True, help="e.g. THM, HTB, PortSwigger")
        sp.add_argument("--category", default="General")
        sp.add_argument("--date", help="YYYY-MM-DD (default: today in IST)")
        sp.add_argument("--no-render", action="store_true")
        if kind == "ctf":
            sp.add_argument("--difficulty", choices=DIFFICULTY_ORDER, default="easy")
            sp.add_argument("--points", type=int)
    sub.add_parser("clear-samples", help="remove every entry marked \"sample\": true")
    a = ap.parse_args(argv)

    if a.cmd == "clear-samples":
        for path in FILES.values():
            doc = load(path)
            before = len(doc["entries"])
            doc["entries"] = [e for e in doc["entries"] if not e.get("sample")]
            save(path, doc)
            print(f"{path.name}: removed {before - len(doc['entries'])} sample entries")
        import charts

        charts.render_all()
        return 0

    try:
        date = dt.date.fromisoformat(a.date) if a.date else today()
    except ValueError:
        print(f"error: --date must be YYYY-MM-DD, got {a.date!r}", file=sys.stderr)
        return 2
    name = a.name.strip()
    if not name:
        print("error: name must not be empty", file=sys.stderr)
        return 2

    entry = {"date": date.isoformat(), "platform": canon_platform(a.platform), "name": name, "category": a.category.strip() or "General"}
    if a.cmd == "ctf":
        entry = {"date": entry["date"], "platform": entry["platform"], "name": name, "difficulty": a.difficulty,
                 "category": entry["category"], **({"points": a.points} if a.points is not None else {})}

    path = FILES[a.cmd]
    doc = load(path)
    key = lambda e: (e.get("date"), (e.get("platform") or "").lower(), (e.get("name") or "").lower())  # noqa: E731
    if key(entry) in {key(e) for e in doc["entries"]}:
        print(f"already logged: {entry['date']} {entry['platform']} - {name}")
        return 0
    doc["entries"].append(entry)
    save(path, doc)
    print(f"logged {a.cmd}: {entry['date']} {entry['platform']} - {name}")

    if not a.no_render:
        import charts

        charts.render_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
