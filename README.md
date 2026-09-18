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
| `screen.json` | The analysis: the names, the event and its date, the reference levels and what each one is, the four judgement scores, and the written case. **This is the file a refresh edits.** |
| `prices.py` | Live price, 52-week range, average volume and market cap per name from Yahoo Finance, plus the exchange rates and acquirer prices that some exit levels are computed from. No API key. |
| `build.py` | Adds everything that is arithmetic — days to the event, position in range, the four price-driven score inputs — and renders `site/`. |
| `template.html` | The page: light and dark, safe-area aware, PWA metadata, sort and filter, per-device marks. |
| `make_icons.py` | Regenerates the home-screen icons. Run by hand; the PNGs are committed. |

## What the page shows, and does not

Every price on a card is a **reference level that exists independently**: an
offer price from an RNS, an undisturbed price, a published NAV, a 52-week
extreme. *Entry* is the current price. *Exit if it works* and *Exit if it
fails* are those references labelled as what you would do with them. Nothing
is a forecast, and no probability is written anywhere — the page gives the
payoff either way and the reader supplies the odds.

Offers in another currency, or paid partly in an acquirer's shares, are
recomputed on every build from the live exchange rate and acquirer price, so
the exit level moves with the market.

Four score inputs are computed from price each build (asymmetry,
uncrowdedness, downside to floor, illiquidity). Four are judgements set when
the name was added (date clarity, reference quality, single point of failure,
slip risk). All eight are shown as bars.

## The schedule

`.github/workflows/screen.yml` runs at **07:15, 17:45 and 22:15 UK** on
weekdays — after the open, the London close and the US close — and on every
push to `main`, so an edit to `screen.json` is live within a couple of minutes.
`keepalive.yml` makes one commit a month so GitHub doesn't disable the schedule
for inactivity.

A name whose date has passed moves to a *Date passed* section automatically
until its outcome is written into `screen.json` under `resolved`.

## Setup

No secrets. The only setting is Pages: Settings → Pages → Source → **GitHub
Actions**.

## Running it locally

```bash
pip install -r requirements.txt
python3 build.py
open site/index.html
```

## What it will not do

It reports; it does not advise. No targets, no probabilities, no buy/sell/hold.
Prices are delayed Yahoo quotes. Marks (Watch, Passed, Entered) are stored in
the browser that made them and go nowhere else.
