"""Live quotes for the screen, from Yahoo Finance.

Same source as the morning brief and the VWRP screener, so there is no API key
to keep alive. Everything is defensive: a page built with one stale price is
better than no page. When Yahoo will not answer for a symbol, the build keeps
the last verified snapshot from screen.json and says so on the card.
"""

import math
import time

import yfinance as yf

# Yahoo's price units. Most LSE lines quote in pence ("GBp").
UNIT_LABEL = {"USD": "$", "GBP": "£", "GBp": "p", "SEK": "SEK ", "AUD": "A$", "NOK": "NOK "}


def _num(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def _fast(ticker):
    """fast_info as a plain dict, or {} if Yahoo is unhappy."""
    try:
        info = ticker.fast_info
        return {
            "price": _num(getattr(info, "last_price", None)),
            "prev": _num(getattr(info, "previous_close", None)),
            "high52": _num(getattr(info, "year_high", None)),
            "low52": _num(getattr(info, "year_low", None)),
            "adv": _num(getattr(info, "three_month_average_volume", None)),
            "cap": _num(getattr(info, "market_cap", None)),
            "currency": getattr(info, "currency", None),
        }
    except Exception as exc:  # noqa: BLE001 - anything from Yahoo is a soft failure
        print(f"  fast_info failed for {ticker.ticker}: {type(exc).__name__}")
        return {}


def _month_change(ticker):
    """Percent change over roughly the last 21 trading days, or None."""
    try:
        history = ticker.history(period="2mo", auto_adjust=False)
        closes = history["Close"].dropna()
        if len(closes) >= 15:
            then = float(closes.iloc[max(0, len(closes) - 22)])
            now = float(closes.iloc[-1])
            if then:
                return 100.0 * (now / then - 1.0)
    except Exception as exc:  # noqa: BLE001
        print(f"  history failed for {ticker.ticker}: {type(exc).__name__}")
    return None


def quote(symbol, attempts=2):
    """One symbol's live numbers, with a short retry. Missing fields stay None."""
    for attempt in range(1, attempts + 1):
        ticker = yf.Ticker(symbol)
        data = _fast(ticker)
        if data.get("price"):
            data["m1"] = _month_change(ticker)
            data["symbol"] = symbol
            return data
        if attempt < attempts:
            time.sleep(1.5 * attempt)
    print(f"  no live quote for {symbol}")
    return {"symbol": symbol}


def fetch_all(symbols):
    """Quotes for every symbol, keyed by symbol. Never raises."""
    out = {}
    for symbol in symbols:
        out[symbol] = quote(symbol)
        time.sleep(0.3)  # be polite; 30-odd symbols, no rush
    live = sum(1 for q in out.values() if q.get("price"))
    print(f"  live quotes: {live}/{len(symbols)}")
    return out


def fx_rate(quotes, pair):
    """A currency pair's last price from the quotes dict, or None."""
    q = quotes.get(pair) or {}
    return q.get("price")


def fmt_price(value, unit):
    """Format a price in its own unit: 297.5p, $1.24, SEK 7.91, A$4.59."""
    if value is None:
        return "—"
    label = UNIT_LABEL.get(unit, "")
    if unit == "GBp":
        text = f"{value:,.1f}" if value >= 100 else f"{value:,.2f}"
        return f"{text}p"
    decimals = 2 if value < 1000 else 0
    if unit == "USD" and value < 1:
        decimals = 3
    return f"{label}{value:,.{decimals}f}"


def fmt_cap(value, currency):
    """Market cap as £361m / $5.5bn / SEK 3.7bn. Yahoo gives it in major units."""
    if not value:
        return None
    label = UNIT_LABEL.get({"GBp": "GBP"}.get(currency, currency) or "", "")
    if value >= 1e9:
        return f"{label}{value/1e9:,.2f}bn" if value < 1e10 else f"{label}{value/1e9:,.1f}bn"
    return f"{label}{value/1e6:,.0f}m"


def fmt_volume(value):
    if not value:
        return "—"
    if value >= 1e6:
        return f"{value/1e6:,.1f}m sh"
    return f"{value/1e3:,.0f}k sh"
