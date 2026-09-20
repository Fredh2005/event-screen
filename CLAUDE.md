# Event Screen

A screener of dated, binary catalysts on listed equities, ranked by transparent
opportunity and risk scores. Built for a UK-based investor running a small
satellite sleeve alongside a VWRP core, trading a days-to-six-weeks event-driven
horizon.

Standalone project with its own repo, workflow and site. Analytical frame —
Rappaport, *Expectations Investing*: read the expectations embedded in the
price rather than forecasting a target.

## Files

- `data.js` — the analysis. Sets `window.__SCREEN__ = {asof, names, watch,
  resolved}` as a JSON literal. **This is the only file a refresh edits.**
- `index.html` — layout, scoring and rendering, all in the browser. It reads
  `data.js` with a plain `<script src>` and works opened straight from the
  filesystem with no server (it then uses each name's `snapshot` prices and
  says so). Rarely changes.
- `build.py` — fetches live quotes, FX rates and acquirer prices, writes them
  into `site/data.js` next to the analysis, copies `index.html` and the assets
  into `site/`. It renders nothing and never edits the analysis.
- `prices.py` — Yahoo Finance quotes. Defensive: a missing quote leaves the
  name on its `snapshot`, flagged on the card.
- `.github/workflows/screen.yml` — rebuilds on a weekday schedule and on push;
  deploys `site/` to GitHub Pages at https://fredh2005.github.io/event-screen/

Do not inline the data back into `index.html` and do not move the rendering
into Python. The split is deliberate: the page must open from a file, and a
refresh must be a one-file edit that cannot break the layout.

Run locally with `pip install -r requirements.txt` then `python3 build.py`.
Output goes to `site/`, which is gitignored.

## The rules that matter

These are not style preferences. Breaking them makes the tool actively harmful.

**Never fabricate an entry price, target price, or expected return.** The whole
design premise is that a "target: 214p" column is a made-up number wearing a
suit. Every price on the page is a *reference level* that exists independently:

- an offer price from a Rule 2.7 announcement, a tender offer, or a scheme
  implementation deed (mixed consideration is computed from the stated ratio
  and the acquirer's timestamped price)
- an undisturbed price (computed from the pre-approach close or back-solved from
  the announcement-day move)
- a published NAV or EPRA NDV, with its as-at date
- a 52-week extreme

Each level carries a `w` field saying what it actually is. If you cannot name
what a level *is*, it does not go on the page.

The three levels on a card are read as **Price now · If it works · If it fails**.
The two outcome levels are references, never targets — never invent a price to
fill the slot, and never present one as a forecast.

**The user supplies the probability.** The screen supplies payoffs and the
evidence. Do not write "70% chance of approval" anywhere.

**Any number derived from two outcome prices is only as honest as those
prices.** Breakeven odds, expected move, payoff ratio — all of them. So:

- Every entry carries `endpointBasis`, either `"contractual"` or
  `"indicative"`, and a one-line `basisNote` saying why.
- `"contractual"` only when **both** endpoints are observable outcomes of the
  specific event: a real offer price (or a computable consideration) against a
  real undisturbed price in a bid situation. Nothing else qualifies.
- `"indicative"` everywhere else. A 52-week high or low is a **historical
  reference**; it is never, by itself, an outcome of a specific catalyst. An
  offer-period high in a contested bid is a hope, not a price on the table.
  Every clinical and regulatory entry is indicative unless a real contractual
  pair exists for it.
- The page marks indicative breakevens (a `~` and a one-line caveat) and lets
  the reader **edit both endpoints** on every card, with a reset. Breakeven
  and expected move follow the reader's endpoints. Do not remove that.
- **Downside bias:** the 52-week low understates the failure case for a name
  that has already fallen, because its low sits close to spot; the lowest
  breakevens on the page are otherwise just the most beaten-down small caps.
  Where an entry is indicative and the price is in the bottom quarter of its
  52-week range, the page flags it and asks the reader for their own floor.
  It never adjusts the number silently. `index.html` computes this from the
  live position; there is nothing to set in `data.js`.
- The level labels are **Price now / If it works / If it fails**, with the
  small print saying what each price is. Nothing on the page tells the
  reader to enter or exit.

**Verify every date and figure against a primary source.** Takeover Code dates
come from the RNS announcement (Investegate). FDA dates come from the company's
8-K or press release. Prices come from a data provider, timestamped. If a figure
cannot be verified, leave the name off rather than guessing.

**A high opportunity score is not a recommendation.** Note that the highest
opportunity names on this screen also carry the highest risk scores. That
relationship is real and the page should never obscure it.

## Scoring

Computed in `index.html`, from four inputs each, all 0–10:

```
opportunity = asym×0.35 + clarity×0.20 + crowd×0.25 + evid×0.20   (×10)
risk        = liq ×0.20 + spof   ×0.30 + down ×0.30 + slip×0.20   (×10)
```

- `asym` — gap between downside and upside reference relative to spot
- `clarity` — Rule 2.6 deadline or PDUFA date = 10; "by end of October" = 6
- `crowd` — *un*crowdedness. Position in 52-week range and recent move. A name
  up 400% into its catalyst scores near 0. Recompute this every refresh even
  when nothing else changed, because price alone moves it.
- `evid` — is there a hard computable anchor, or only a soft one
- `liq` — illiquidity (high = bad). Market cap and average volume.
- `spof` — single point of failure. One FDA decision = 10; three staggered
  readouts = lower.
- `down` — distance to the floor reference
- `slip` — can the date move

These are judgements on a consistent scale, not measurements. The four inputs
are displayed as bars so a reader can disagree with one specifically rather than
with a black-box number. Keep that property.

## Entry shape (data.js → names[])

```json
{
  "id":"stem", "ticker":"LSE: STEM", "name":"SThree", "type":"bid|clin|reg", "market":"UK",
  "symbol":"STEM.L", "unit":"GBp",            // Yahoo symbol and its price unit
  "snapshot":{"price":297.5,"high52":324,"low52":137.2,"adv":458000,"cap":"£361m","asof":"…"},
  "date":"2026-10-07", "when":"5.00pm, 7 Oct 2026",
  "event":"…",                                // one line
  "close":"…",                                // when the position is over, and on what
  "down":{"v":276,"w":"Undisturbed price, implied by …"},   // if it fails
  "up":{"v":324,"w":"Offer-period high"},                    // if it works
  "ref":{"v":177.5,"w":"…"},                  // optional third reference (an offer, an NDV)
  "endpointBasis":"contractual|indicative",   // see the rule above
  "basisNote":"…",                            // one line: why
  "judgement":{"clarity":10,"evid":9,"spof":8,"slip":5},
  "about":"…","implied":"…","setup":"…","bull":"…","bear":"…","kill":"…","angle":"…"
}
```

A level's `v` is a number in the name's own unit, or a formula the build
resolves from live quotes:
`{"usd":5.214,"fx":"GBPUSD=X","to":"GBp"}` for a dollar offer on a sterling
line, `{"cash":30,"ratio":0.1574,"of":"BCO"}` for cash plus acquirer shares.

`asym`, `crowd`, `down` and `liq` are **not** in the file: the build computes
them from price each run. Only `clarity`, `evid`, `spof` and `slip` are
judgements. `kill` must be a specific checkable fact. `close` says what ends
the trade — a decision, a document, a deadline — so the reader knows when to
stop looking.

Resolved names go into `resolved[]` as `{"date","name","outcome","note"}` and
come out of `names[]`. The build parks any name whose date has passed in a
"Date passed" section until that is done.

## Refreshing

1. Prices refresh themselves. Update each name's `snapshot` anyway so the
   fallback is not stale, and check the `stale` flag on the built page.
2. Search for news since the last run: Rule 2.7/2.8 announcements, offer
   revisions, acceptance levels, Panel rulings, FDA decisions, CRLs, guidance
   changes.
3. Resolved catalysts come out of `names` and go into `resolved` with the
   outcome, so the user can score their own call.
4. Dates that moved: update, then revisit `clarity` and `slip`.
5. `crowd` and `asym` recompute themselves; revisit `spof` and `evid` if the
   structure of the event changed.
6. Add new names with a genuine dated event inside ten weeks, a verified price
   and a computable reference. Target 20–25 scored. Build the list up over runs
   rather than padding it to a round number.

Weight toward US small-cap biotech and UK bid situations — that is where the
largest individual moves are. Skip illiquid AIM microcaps with wide spreads;
the user trades a Trading 212 ISA and cannot transact meaningfully in them.

## Deployment note

GitHub Pages via `screen.yml`; Pages source must be set to GitHub Actions.
The live page is `site/index.html` + `site/data.js` (the analysis plus quotes).
Marks are per-browser localStorage. The original Claude artifact of this
project is abandoned in favour of the site.
