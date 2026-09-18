# Event Screen

A screener of dated, binary catalysts on listed equities, ranked by transparent
opportunity and risk scores. Built for a UK-based investor running a small
satellite sleeve alongside a VWRP core, trading a days-to-six-weeks event-driven
horizon.

Sister project to `vwrp-screener` (reverse-DCF on VWRP constituents). Same
analytical frame — Rappaport, *Expectations Investing*: read the expectations
embedded in the price rather than forecasting a target.

## Files

- `index.html` — the page. Layout, scoring functions, rendering. Rarely changes.
- `data.js` — the screen contents. Sets `window.__SCREEN__ = {names, watch}`.
  **This is the file a refresh edits.**

No build step, no dependencies. Open `index.html` directly, or
`python3 -m http.server` from this directory.

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

## Entry shape

```js
{
  t:"LSE: STEM", n:"SThree", type:"bid"|"clin"|"reg", mkt:"UK"|"US",
  px:"297.5p", cap:"£361m", rng:"137.2–324.0p", pos:86, adv:"3.5m sh",
  date:"2026-10-07",              // ISO, drives the countdown
  when:"5.00pm, 7 Oct 2026",      // human-readable, matches the announcement
  about:"…",                      // what the company is, 2–4 sentences, plain facts
  ev:"…",                         // the event, one line
  o:{asym,clarity,crowd,evid}, r:{liq,spof,down,slip},
  levels:[ {k,v,w,c:"dn"|"up"|undefined} × 3 ],
  implied:"…",  // what the current price implies. The most important field.
  setup:"…", bull:"…", bear:"…", kill:"…", angle:"…"
}
```

`kill` must be a specific checkable fact, not "the thesis breaks down".
`angle` is the point worth making in a buy-side interview — usually a mechanism
(Rule 9 conversion, cash confirmation, a conference front-running a PDUFA)
rather than a view.

## Refreshing

1. Re-price every name. Update `px`, `cap`, `rng`, `pos`, `adv`.
2. Search for news since the last run: Rule 2.7/2.8 announcements, offer
   revisions, acceptance levels, Panel rulings, FDA decisions, CRLs, guidance
   changes.
3. Resolved catalysts come out of `names` and go into `watch` as a one-line
   outcome, so the user can score their own call.
4. Dates that moved: update, then revisit `clarity` and `slip`.
5. Revisit `crowd` on everything.
6. Add new names with a genuine dated event inside ten weeks, a verified price
   and a computable reference. Target 20–25 scored. Build the list up over runs
   rather than padding it to a round number.

Weight toward US small-cap biotech and UK bid situations — that is where the
largest individual moves are. Skip illiquid AIM microcaps with wide spreads;
the user trades a Trading 212 ISA and cannot transact meaningfully in them.

## Deployment note

`index.html` checks for `window.claude.use("db")` and uses it when present (the
Claude artifact runtime, where marks are shared server-side). Served anywhere
else that call is absent and marks fall back to `localStorage`, which is
per-browser and per-device. If this is deployed somewhere real and the marks
need to persist properly, that is the seam to replace with a backend.
