# Weekly refresh procedure

This is the checklist the weekly refresh follows. It is written for an agent
starting with zero context, in a clean clone of this repo. The only file a
refresh edits is `screen.json`. Read `CLAUDE.md` first — its rules (no invented
prices, no probabilities, verify every date against a primary source) are not
optional.

## 0. Setup

```bash
pip install -r requirements.txt
python3 build.py          # must succeed before you start and after you finish
```

`build.py` prints the top names and writes `site/index.html`. If it fails at
the end of your edits, you have broken `screen.json`; fix it before committing.
Today's date is whatever `date` says; the window is the next **ten weeks**.

## 1. Resolve what has happened

For every entry in `names[]` whose `date` is today or earlier, and for any
other entry where news says the event has already resolved:

1. Find the outcome from a primary source — the RNS on Investegate, the
   company's 8-K or press release, the FDA's own announcement. Not a
   headline aggregator.
2. Move it to `resolved[]` as
   `{"date": "<event date>", "name": "<name>", "outcome": "<one line: what happened>", "note": "<one line: where the price went, from the exit references on the card>"}`.
3. Remove it from `names[]`.

A name with two dated events (Capricor, Mirum, Summit) stays in `names[]`
after the first resolves: update `date`, `when`, `event`, `close` and the
case text to the second event, and record the first outcome in the `setup`.

## 2. Kick out what is no longer a good opportunity

Remove from `names[]` (and add a one-line entry to `watch[]` if the date is
still worth knowing) any name where, after checking news since the last
refresh:

- the event has slipped beyond ten weeks from today;
- the date has become vague where it used to be firm (a PUSU deadline
  extended twice with no financing update; a readout moved from a month to a
  quarter) **and** the price has already run to the upside reference;
- the bid or approval has become a formality with under 2% to the upside
  reference and no plausible counterbid — keep at most one such name as
  the control case;
- the stock has become untradeable: under roughly $500k a day of value or a
  quoted spread wider than 3%.

Do not remove a name just because its opportunity score is middling; that is
what the score is for. Do remove it if the reason it was on the screen no
longer exists.

## 3. Update what stayed

For every remaining name:

- Search for news since the last refresh: Rule 2.7 / 2.8 announcements,
  scheme documents, offer revisions, acceptance levels, Panel rulings,
  regulatory decisions, guidance changes, financings, CRLs, extensions.
- If the date moved: update `date` and `when`, then revisit `clarity` and
  `slip` in `judgement`.
- If the structure changed (a counterbidder appeared, an offer went to
  cash, an AdCom was called): update `event`, `close`, `up`/`down`/`ref`
  and the case text. A new offer price is a new `up` or `ref` level.
- Refresh `snapshot` (price, high52, low52, adv, cap, asof) from the live
  build output (`site/quotes.json`) so the fallback is not stale.
- Re-read `implied`, `bull`, `bear`, `kill`: if a sentence is no longer true,
  rewrite it. `kill` must remain a specific checkable fact.

## 4. Find replacements

Target **20–25** names in `names[]`. Build the list up with real ones; never
pad. A candidate qualifies only if all four hold:

1. **A dated event inside ten weeks**, verified against a primary source:
   a Rule 2.6 deadline or scheme timetable (Investegate RNS), a PDUFA date
   (the company's 8-K / press release), a trial readout with month-level
   guidance from the company, a regulator's published decision deadline
   (CMA, FTC, EC), a tender expiry, a scheme meeting date. Aggregator
   calendars are leads, not sources — several list events that already
   happened.
2. **A verified, timestamped price** — the build gets it from Yahoo; make
   sure the Yahoo symbol resolves (`python3 -c "import yfinance as yf; print(yf.Ticker('SYMB').fast_info.last_price)"`).
3. **A computable upside and downside reference** that exists independently:
   offer price, undisturbed price, published NAV, 52-week extreme, or a
   formula from an acquirer's price / an FX rate. If you cannot name what a
   level *is*, the name does not go on.
4. **Tradeable size**: roughly $500k a day or more of value traded.

Where to look, in order of yield: UK offer periods (Investegate, search
"Rule 2.6" and "Rule 2.7" in the last fortnight); US small-cap biotech
PDUFAs and Phase 3 readouts in the window (company 8-Ks; the FDA calendars on
BioPharmCatalyst / MarketBeat as leads); contested or go-shop schemes on the
ASX, Euronext, Oslo and Stockholm; pending mergers with a regulator's
decision date. Weight toward names with the largest plausible moves — US
small-cap biotech and UK bids — and toward names the market has stopped
watching (flat into the date, low in the 52-week range).

Write the entry in the shape shown in `CLAUDE.md`. Set only the four
judgement scores (`clarity`, `evid`, `spof`, `slip`) on the scale used by the
existing entries; the build computes the rest. Write `about`, `implied`,
`setup`, `bull`, `bear`, `kill`, `angle` and `close` in the same register as
the existing cards: plain, specific, no hype, no probabilities.

## 5. Finish

1. Update the top-level `asof` to today.
2. `python3 build.py` — must succeed, with at least 20 names live from Yahoo.
3. Commit with a message that lists what was resolved, removed and added,
   and push to `main`. The site rebuilds itself from the push.
4. If nothing changed (no resolutions, no news, no new qualifying names),
   still update `asof` and the snapshots and commit, so the page's
   "analysis as of" date is honest.
