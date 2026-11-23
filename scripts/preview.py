#!/usr/bin/env python3
"""Preview the website locally, assembled exactly like the Pages workflow does.

    python scripts/preview.py            # http://localhost:8000
    python scripts/preview.py --port 9000
    python scripts/preview.py --build    # only assemble _site/, do not serve
"""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import socketserver

from theme import DATA, ROOT

SITE, OUT = ROOT / "site", ROOT / "_site"


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SITE, OUT)
    (OUT / "data").mkdir(exist_ok=True)
    for name in ("modules.json", "ctfs.json", "contributions.json"):
        if (DATA / name).exists():
            shutil.copy(DATA / name, OUT / "data" / name)
    (OUT / ".nojekyll").touch()
    print(f"assembled {OUT.relative_to(ROOT)}/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--build", action="store_true", help="assemble _site/ and exit")
    a = ap.parse_args()
    build()
    if a.build:
        return
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    with socketserver.TCPServer(("127.0.0.1", a.port), handler) as srv:
        print(f"serving http://localhost:{a.port}  (Ctrl+C to stop; re-run to pick up edits)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
