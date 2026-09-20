# Event Screen

A single page of dated, binary catalysts on listed shares — bid deadlines, FDA
decisions, trial readouts — each with the price you'd enter at today, the two
prices you'd exit at depending on the result, when it happens, and an
opportunity and risk score built from inputs you can see. Rebuilt on live
prices three times each weekday. Add it to your home screen and it behaves
like an app.

**Live at:** https://fredh2005.github.io/event-screen/

## How it works

| Piece | What it does |
|---|---|
| `data.js` | The analysis: the names, the event and its date, the reference levels and what each one is, whether the pair is contractual or indicative, the four judgement scores, and the written case. **This is the only file a refresh edits.** |
| `index.html` | The page: layout, scoring and rendering, all in the browser. Opens straight from the filesystem (on snapshot prices) or from `site/` (on live ones). |
| `prices.py` | Live price, 52-week range, average volume and market cap per name from Yahoo Finance, plus the exchange rates and acquirer prices some levels are computed from. No API key. |
| `build.py` | Fetches the quotes, writes them into `site/data.js` beside the analysis, copies the page and assets. Renders nothing. |
| `make_icons.py` | Regenerates the home-screen icons. Run by hand; the PNGs are committed. |

## What the page shows, and does not

Every price on a card is a **reference level that exists independently**: an
offer price from an RNS, an undisturbed price, a published NAV, a 52-week
extreme. *Price now* is the live quote; *If it works* and *If it fails* are
the references, each saying what it is. Nothing is a forecast and nothing on
the page tells the reader to trade.

Each pair of references is marked **contractual** (both are real outcomes of
the specific event — an offer against the pre-bid price) or **indicative**
(a historical reference standing in for an outcome, which is every 52-week
extreme). Breakeven odds and the expected move are computed from whatever two
endpoints are in the boxes on the card — the defaults or the reader's own —
and are worth exactly what those endpoints are worth; indicative ones are
marked. Where a name is indicative and already in the bottom quarter of its
range, the card says the default floor is optimistic and asks for the
reader's own.

Offers in another currency, or paid partly in an acquirer's shares, are
recomputed on every build from the live exchange rate and acquirer price.

Four score inputs are computed from price each build (asymmetry,
uncrowdedness, downside to floor, illiquidity). Four are judgements set when
the name was added (date clarity, reference quality, single point of failure,
slip risk). All eight are shown as bars.

## The schedule

`.github/workflows/screen.yml` runs at **07:15, 17:45 and 22:15 UK** on
weekdays — after the open, the London close and the US close — and on every
push to `main`, so an edit to `data.js` is live within a couple of minutes.
`keepalive.yml` makes one commit a month so GitHub doesn't disable the schedule
for inactivity.

A name whose date has passed moves to a *Date passed* section automatically
until its outcome is written into `data.js` under `resolved`.

## Setup

No secrets. The only setting is Pages: Settings → Pages → Source → **GitHub
Actions**.

## Running it locally

Open `index.html` directly — it renders from `data.js` on snapshot prices, no
server needed. For live prices:

```bash
pip install -r requirements.txt
python3 build.py
open site/index.html
```

## What it will not do

It reports; it does not advise. No targets, no probabilities, no buy/sell/hold.
Prices are delayed Yahoo quotes. Marks, odds and edited endpoints are stored in the browser that made them and
go nowhere else.
