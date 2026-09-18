# Event Screen

A screener of dated, binary catalysts on listed equities, ranked by transparent
opportunity and risk scores. Built for a UK-based investor running a small
satellite sleeve alongside a VWRP core, trading a days-to-six-weeks event-driven
horizon.

Standalone project with its own repo, workflow and site. Analytical frame —
Rappaport, *Expectations Investing*: read the expectations embedded in the
price rather than forecasting a target.

## Files

- `screen.json` — the analysis. Names, events, dates, reference levels with
  their `w` labels, the four judgement scores, and the written case.
  **This is the file a refresh edits.**
- `build.py` — computes days-to-event, 52-week position and the four
  price-driven score inputs from live quotes, then renders `site/index.html`
  from `template.html`. Rarely changes.
- `prices.py` — Yahoo Finance quotes, FX pairs and acquirer prices. Defensive:
  a missing quote falls back to the name's `snapshot` and is flagged on the card.
- `template.html` — layout. Rarely changes.
- `.github/workflows/screen.yml` — rebuilds on a weekday schedule and on push;
  deploys to GitHub Pages at https://fredh2005.github.io/event-screen/

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

The three levels on a card are read as downside reference · current price
(the level you would enter at) · upside reference. They are the nearest honest
thing to "entry and exit" — never invent a target to fill the slot.

**The user supplies the probability.** The screen supplies payoffs and the
evidence. Do not write "70% chance of approval" anywhere.

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

## Entry shape (screen.json → names[])

```json
{
  "id":"stem", "ticker":"LSE: STEM", "name":"SThree", "type":"bid|clin|reg", "market":"UK",
  "symbol":"STEM.L", "unit":"GBp",            // Yahoo symbol and its price unit
  "snapshot":{"price":297.5,"high52":324,"low52":137.2,"adv":458000,"cap":"£361m","asof":"…"},
  "date":"2026-10-07", "when":"5.00pm, 7 Oct 2026",
  "event":"…",                                // one line
  "close":"…",                                // when the position is over, and on what
  "down":{"v":276,"w":"Undisturbed price, implied by …"},   // exit if it fails
  "up":{"v":324,"w":"Offer-period high"},                    // exit if it works
  "ref":{"v":177.5,"w":"…"},                  // optional third reference (an offer, an NDV)
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
Marks are per-browser localStorage. The original Claude artifact of this
project is abandoned in favour of the site.
