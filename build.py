"""Assemble the Event Screen into site/index.html.

    python3 build.py

screen.json holds the judgement: which names, what the event is, the reference
levels and why each one is what it is, and the four inputs that are opinions
(date clarity, reference quality, single point of failure, slip risk). This
script adds everything that is arithmetic — live prices, days to the event,
position in the 52-week range, and the four score inputs that follow from price
alone — so the page moves with the market between edits without anyone
touching the analysis. A name whose date has passed drops into a "resolved"
section automatically until its outcome is written into screen.json.
"""

import html
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import prices

LONDON = ZoneInfo("Europe/London")
OUT = Path("site")
ASSETS = ["manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png", "apple-touch-icon.png"]
FX_PAIRS = ["GBPUSD=X", "AUDUSD=X"]

# Weights are the ones the methodology panel states. Change both or neither.
OPP_W = {"asym": .35, "clarity": .20, "crowd": .25, "evid": .20}
RISK_W = {"liq": .20, "spof": .30, "down": .30, "slip": .20}

TYPE_LABEL = {"bid": "Bid", "clin": "Clinical", "reg": "Regulatory"}

# Rough conversion of a name's own currency into USD for the liquidity score
# only. Precision is irrelevant here: the score moves one notch per 10x.
USD_PER_UNIT = {"USD": 1.0, "GBp": 0.0135, "GBP": 1.35, "SEK": 0.105, "AUD": 0.66, "NOK": 0.10}


def esc(value):
    return html.escape(str(value), quote=True)


def clamp(value, lo=0, hi=10):
    return max(lo, min(hi, value))


# ---------------------------------------------------------------- references

def resolve_level(level, quotes):
    """A level's value in the name's own unit. Numbers pass through; formulas
    are computed from live quotes so a mixed-consideration or foreign-currency
    offer moves with the market. Returns None when the inputs are missing."""
    v = level["v"]
    if isinstance(v, (int, float)):
        return float(v)
    if "cash" in v:                                # cash + ratio × acquirer
        acq = prices.fx_rate(quotes, v["of"])
        return None if acq is None else v["cash"] + v["ratio"] * acq
    if "usd" in v:                                 # a USD amount in another unit
        rate = prices.fx_rate(quotes, v["fx"])
        if rate is None:
            return None
        if v["fx"] == "GBPUSD=X":
            gbp = v["usd"] / rate
            return gbp * 100 if v.get("to") == "GBp" else gbp
        if v["fx"] == "AUDUSD=X":
            return v["usd"] / rate
    return None


# ------------------------------------------------------------------- scoring

def asym_score(up_pct, dn_pct):
    """Gap between upside and downside reference relative to spot. Equal gaps
    score 5; all upside 10; all downside 0. Probability is not in here."""
    if up_pct is None or dn_pct is None:
        return 5
    up, dn = max(up_pct, 0.0), max(dn_pct, 0.0)
    if up + dn == 0:
        return 5
    return int(round(clamp(5 + 5 * (up - dn) / (up + dn))))


def crowd_score(pos, m1):
    """UNcrowdedness. Position in the 52-week range carries most of it; a big
    one-month move into the date takes the rest. High = nobody is here yet."""
    if pos is None:
        return 5
    base = (1 - pos) * 7
    move = 3.0 if m1 is None or m1 <= 0 else max(0.0, 3 - m1 / 10)
    return int(round(clamp(base + move)))


def down_score(dn_pct):
    """Distance to the floor reference. 10 means the floor is more than half way down."""
    if dn_pct is None:
        return 5
    return int(round(clamp(dn_pct * 18)))


def liq_score(adv_shares, price, unit):
    """Illiquidity, from daily value traded in USD: $100k a day scores 10,
    $1m 7, $10m 4, $100m 1. High is bad."""
    if not adv_shares or not price:
        return 6
    usd = adv_shares * price * USD_PER_UNIT.get(unit, 1.0)
    if usd <= 0:
        return 10
    import math
    return int(round(clamp(10 - 3 * math.log10(usd / 1e5))))


def weighted(inputs, weights):
    return int(round(10 * sum(inputs[k] * w for k, w in weights.items())))


# ------------------------------------------------------------------ assembly

def enrich(name, quotes, today):
    snap = name["snapshot"]
    q = quotes.get(name["symbol"]) or {}
    live = bool(q.get("price"))
    unit = name["unit"]

    px = q["price"] if live else snap["price"]
    hi = q.get("high52") or snap["high52"]
    lo = q.get("low52") or snap["low52"]
    adv = q.get("adv") or snap.get("adv")
    cap = prices.fmt_cap(q.get("cap"), q.get("currency")) if live else None
    cap = cap or snap["cap"]
    m1 = q.get("m1")

    up_v = resolve_level(name["up"], quotes)
    dn_v = resolve_level(name["down"], quotes)
    ref_v = resolve_level(name["ref"], quotes) if name.get("ref") else None
    up_pct = None if up_v is None or not px else up_v / px - 1
    dn_pct = None if dn_v is None or not px else 1 - dn_v / px
    pos = None if hi is None or lo is None or hi == lo else clamp((px - lo) / (hi - lo), 0, 1)

    j = name["judgement"]
    opp_in = {"asym": asym_score(up_pct, dn_pct), "clarity": j["clarity"],
              "crowd": crowd_score(pos, m1), "evid": j["evid"]}
    risk_in = {"liq": liq_score(adv, px, unit), "spof": j["spof"],
               "down": down_score(dn_pct), "slip": j["slip"]}

    event_day = date.fromisoformat(name["date"])
    days = (event_day - today).days

    return dict(name,
        px=px, hi=hi, lo=lo, adv=adv, cap=cap, m1=m1, live=live,
        up_v=up_v, dn_v=dn_v, ref_v=ref_v, up_pct=up_pct, dn_pct=dn_pct, pos=pos,
        opp_in=opp_in, risk_in=risk_in,
        opp=weighted(opp_in, OPP_W), risk=weighted(risk_in, RISK_W),
        days=days, event_day=event_day,
    )


def pct(value, signed=True):
    if value is None:
        return "—"
    return f"{value*100:+.1f}%" if signed else f"{value*100:.1f}%"


def day_label(d):
    return f"{d.day} {d:%b}"


def bar(label, value, tone):
    return (f'<div class="bar"><span>{esc(label)}</span>'
            f'<span class="track"><span class="fill {tone}" style="width:{value*10}%"></span></span>'
            f'<b>{value}</b></div>')


def card(n, rank):
    unit = n["unit"]
    heat = "" if n["days"] < 0 else "hot" if n["days"] <= 14 else "warm" if n["days"] <= 35 else "cool"
    days_txt = ("resolved — outcome to record" if n["days"] < 0
                else "today" if n["days"] == 0
                else f"in {n['days']} day{'s' if n['days'] != 1 else ''}")
    stale = "" if n["live"] else ' <span class="stale" title="Yahoo did not answer for this line on this build">last verified quote</span>'
    ref_html = ""
    if n.get("ref") and n["ref_v"] is not None:
        ref_html = (f'<p class="ref">Also on the table: <b>{esc(prices.fmt_price(n["ref_v"], unit))}</b> '
                    f'— {esc(n["ref"]["w"])}</p>')
    m1 = "" if n["m1"] is None else f' · 1-month {n["m1"]:+.0f}%'

    return f'''
<article class="card" data-id="{esc(n["id"])}" data-type="{esc(n["type"])}" data-opp="{n["opp"]}" data-risk="{n["risk"]}" data-days="{n["days"]}" data-heat="{heat}">
  <header class="card-head">
    <div class="who">
      <span class="rank">{rank}</span>
      <h3>{esc(n["name"])}</h3>
      <span class="tag {esc(n["type"])}">{esc(TYPE_LABEL[n["type"]])}</span>
      <span class="tag">{esc(n["market"])}</span>
    </div>
    <p class="meta">{esc(n["ticker"])} · {esc(n["cap"])} · avg vol {esc(prices.fmt_volume(n["adv"]))}{m1}</p>
  </header>

  <div class="levels">
    <div class="lvl entry">
      <span class="k">Entry — price now</span>
      <span class="v">{esc(prices.fmt_price(n["px"], unit))}</span>
      <span class="w">{esc(pct(n["pos"], signed=False))} of its 52-week range{stale}</span>
    </div>
    <div class="lvl up">
      <span class="k">Exit if it works</span>
      <span class="v">{esc(prices.fmt_price(n["up_v"], unit))} <small>{esc(pct(n["up_pct"]))}</small></span>
      <span class="w">{esc(n["up"]["w"])}</span>
    </div>
    <div class="lvl dn">
      <span class="k">Exit if it fails</span>
      <span class="v">{esc(prices.fmt_price(n["dn_v"], unit))} <small>{esc(pct(-n["dn_pct"] if n["dn_pct"] is not None else None))}</small></span>
      <span class="w">{esc(n["down"]["w"])}</span>
    </div>
  </div>
  {ref_html}

  <div class="scores">
    <div class="score opp"><span class="v">{n["opp"]}</span><span class="k">Opportunity</span></div>
    <div class="score risk"><span class="v">{n["risk"]}</span><span class="k">Risk</span></div>
    <div class="score days"><span class="v">{n["days"] if n["days"] >= 0 else "—"}</span><span class="k">Days to event</span></div>
  </div>

  <ol class="timeline">
    <li><span class="dot"></span><b>Open now</b><span>the setup is live at today's price</span></li>
    <li><span class="dot"></span><b>Event · {esc(day_label(n["event_day"]))} · {esc(days_txt)}</b><span>{esc(n["when"])}</span></li>
    <li><span class="dot"></span><b>Close</b><span>{esc(n["close"])}</span></li>
  </ol>

  <p class="event"><b>The event.</b> {esc(n["event"])}</p>

  <details class="case">
    <summary>Read the case — what the company is, what the price implies, bull, bear, and what would make it wrong</summary>
    <div class="case-body">
      <h4>About the company</h4><p>{esc(n["about"])}</p>
      <h4 class="implied">What the price implies</h4><p class="implied-p">{esc(n["implied"])}</p>
      <h4>Setup</h4><p>{esc(n["setup"])}</p>
      <h4>Bull</h4><p>{esc(n["bull"])}</p>
      <h4>Bear</h4><p>{esc(n["bear"])}</p>
      <h4 class="kill">What would make the call wrong</h4><p>{esc(n["kill"])}</p>
      <h4>Interview angle</h4><p>{esc(n["angle"])}</p>
      <div class="bars">
        <div><h5>Opportunity inputs → {n["opp"]}</h5>
          {bar("Asymmetry", n["opp_in"]["asym"], "opp")}{bar("Date clarity", n["opp_in"]["clarity"], "opp")}
          {bar("Uncrowded", n["opp_in"]["crowd"], "opp")}{bar("Reference quality", n["opp_in"]["evid"], "opp")}</div>
        <div><h5>Risk inputs → {n["risk"]}</h5>
          {bar("Illiquidity", n["risk_in"]["liq"], "risk")}{bar("Single point of failure", n["risk_in"]["spof"], "risk")}
          {bar("Downside to floor", n["risk_in"]["down"], "risk")}{bar("Slip risk", n["risk_in"]["slip"], "risk")}</div>
      </div>
      <p class="fine">Asymmetry, uncrowdedness, downside and illiquidity are computed from the live price each build. Date clarity, reference quality, single-point-of-failure and slip risk are judgements, set when the name was added.</p>
    </div>
  </details>

  <div class="marks">
    <button type="button" data-mark="watch">Watch</button>
    <button type="button" data-mark="passed">Passed</button>
    <button type="button" data-mark="entered">Entered</button>
    <span class="mark-note"></span>
  </div>
</article>'''


def next_up(names):
    soon = sorted([n for n in names if n["days"] >= 0], key=lambda n: n["days"])[:6]
    items = "".join(
        f'<li><a href="#{esc(n["id"])}"><b>{esc(n["name"])}</b>'
        f'<span>{esc(day_label(n["event_day"]))} · {"today" if n["days"] == 0 else str(n["days"]) + " days"}</span></a></li>'
        for n in soon)
    return f'<ol class="nextup">{items}</ol>'


def watch_rows(items, today):
    rows = []
    for w in sorted(items, key=lambda w: w["date"]):
        d = date.fromisoformat(w["date"])
        days = (d - today).days
        rows.append(f'<li><span class="wd"><b>{days if days >= 0 else "—"}</b>days</span>'
                    f'<span><b>{esc(w["title"])}</b><small>{esc(w["note"])}</small></span></li>')
    return "<ul class=\"watch\">" + "".join(rows) + "</ul>"


def resolved_rows(items):
    if not items:
        return ""
    rows = "".join(
        f'<li><span class="wd"><b>{esc(date.fromisoformat(r["date"]).strftime("%-d %b"))}</b></span>'
        f'<span><b>{esc(r["name"])}</b> — {esc(r["outcome"])}<small>{esc(r.get("note",""))}</small></span></li>'
        for r in sorted(items, key=lambda r: r["date"], reverse=True))
    return f'<h2>Resolved</h2><p class="lead">What happened, so you can score your own call.</p><ul class="watch resolved">{rows}</ul>'


def main():
    now = datetime.now(LONDON)
    today = now.date()
    data = json.loads(Path("screen.json").read_text())

    symbols = [n["symbol"] for n in data["names"]]
    extra = sorted({v["v"]["of"] for n in data["names"] for v in (n["up"], n["down"], n.get("ref"))
                    if v and isinstance(v["v"], dict) and "of" in v["v"]})
    print(f"building for {today:%A %-d %B}: {len(symbols)} names, {len(extra)} acquirers, {len(FX_PAIRS)} fx")
    quotes = prices.fetch_all(symbols + extra + FX_PAIRS)

    names = [enrich(n, quotes, today) for n in data["names"]]
    live = sum(1 for n in names if n["live"])
    if live < len(names) // 2:
        sys.exit(f"only {live}/{len(names)} names priced live - not publishing")

    live_names = sorted([n for n in names if n["days"] >= 0], key=lambda n: -n["opp"])
    passed = sorted([n for n in names if n["days"] < 0], key=lambda n: n["days"])
    cards = "\n".join(card(n, i + 1) for i, n in enumerate(live_names))
    passed_cards = "\n".join(card(n, "·") for n in passed)
    if passed_cards:
        passed_cards = ('<h2>Date passed — outcome to be recorded</h2>'
                        '<p class="lead">These have resolved. They stay here, unscored, until the outcome is written up.</p>'
                        f'<div class="cards">{passed_cards}</div>')

    fx_note = ", ".join(f"{p[:6]} {prices.fx_rate(quotes, p):.4f}" for p in FX_PAIRS if prices.fx_rate(quotes, p))
    stamp = (f"Prices {now:%-d %b %Y, %H:%M %Z} · {live}/{len(names)} lines live from Yahoo Finance"
             + (f" · {fx_note}" if fx_note else "")
             + f" · analysis as of {date.fromisoformat(data['asof']):%-d %b}")

    page = (Path("template.html").read_text()
            .replace("{{STAMP}}", esc(stamp))
            .replace("{{COUNT}}", str(len(live_names)))
            .replace("{{NEXTUP}}", next_up(names))
            .replace("{{CARDS}}", cards)
            .replace("{{PASSED}}", passed_cards)
            .replace("{{WATCH}}", watch_rows(data["watch"], today))
            .replace("{{RESOLVED}}", resolved_rows(data.get("resolved", [])))
            .replace("{{ASOF}}", esc(f"{date.fromisoformat(data['asof']):%-d %B %Y}")))

    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(page)
    (OUT / "quotes.json").write_text(json.dumps(
        {s: {k: v for k, v in q.items() if k != "symbol"} for s, q in quotes.items()}, indent=1, default=str))
    for asset in ASSETS:
        if Path(asset).exists():
            shutil.copy(asset, OUT / asset)
    print(f"  wrote {OUT/'index.html'} ({len(page):,} bytes); "
          f"top: {[ (n['name'], n['opp'], n['risk']) for n in live_names[:5] ]}")


if __name__ == "__main__":
    main()
