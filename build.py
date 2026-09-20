"""Add live prices to the screen and stage it in site/.

    python3 build.py

data.js is the analysis and the only file a refresh edits. index.html does all
the scoring and rendering in the browser, so it works opened straight from the
filesystem with no server — in which case it uses each name's stored snapshot
prices and says so on the card. This script's only job is to fetch live quotes
from Yahoo Finance (plus the FX rates and acquirer prices some exit levels are
computed from), write them into site/data.js alongside the analysis, and copy
the page and its assets next to it. It never touches the analysis itself.
"""

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import prices

LONDON = ZoneInfo("Europe/London")
OUT = Path("site")
COPY = ["index.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png"]
FX_PAIRS = ["GBPUSD=X", "AUDUSD=X"]
PREFIX = "window.__SCREEN__ ="


def load_screen(path="data.js"):
    """data.js is a JS assignment wrapping a JSON literal; read the literal."""
    text = Path(path).read_text()
    start = text.index(PREFIX) + len(PREFIX)
    end = text.rindex("}") + 1
    return json.loads(text[start:end]), text[:start]


def formula_symbols(data):
    syms = set()
    for n in data["names"]:
        for level in (n.get("up"), n.get("down"), n.get("ref")):
            if level and isinstance(level.get("v"), dict) and "of" in level["v"]:
                syms.add(level["v"]["of"])
    return sorted(syms)


def main():
    now = datetime.now(LONDON)
    data, _ = load_screen()
    names = data["names"]
    symbols = [n["symbol"] for n in names]
    extra = formula_symbols(data)
    print(f"building {now:%A %-d %B %H:%M}: {len(symbols)} names, {len(extra)} acquirers, {len(FX_PAIRS)} fx")

    quotes = prices.fetch_all(symbols + extra + FX_PAIRS)
    live = sum(1 for s in symbols if (quotes.get(s) or {}).get("price"))
    if live < len(symbols) // 2:
        sys.exit(f"only {live}/{len(symbols)} names priced live - not publishing")

    staged = dict(data)
    staged["quotes"] = {s: {k: v for k, v in q.items() if k != "symbol"} for s, q in quotes.items()}
    staged["built"] = now.isoformat(timespec="minutes")
    staged["live"] = live

    OUT.mkdir(exist_ok=True)
    (OUT / "data.js").write_text(
        "// Built by build.py: the analysis from data.js plus live quotes. Do not edit.\n"
        + PREFIX + " " + json.dumps(staged, ensure_ascii=False, default=str) + ";\n")
    for f in COPY:
        shutil.copy(f, OUT / f)
    print(f"  wrote site/data.js with {live}/{len(symbols)} live quotes; copied {len(COPY)} files")


if __name__ == "__main__":
    main()
