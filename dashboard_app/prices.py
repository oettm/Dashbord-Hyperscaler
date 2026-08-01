"""Minimal, on-demand stock price lookup - used only to compute P/E in the
essentials view. No charts, no history, no background fetching: one cached
price per ticker per hour. Network failures (offline, rate-limited, Yahoo
Finance unreachable) degrade to None ("not available"), never a crash or a
fabricated number.
"""
import streamlit as st

TICKERS = {
    "ASML": "ASML.AS",      # Euronext Amsterdam, EUR - matches ASML's EUR-denominated EPS
    "Google/Alphabet": "GOOGL",
    "Microsoft": "MSFT",
    "TSMC": "TSM",           # NYSE ADR, USD - matches the eps_usd_per_adr field
    "Vertiv": "VRT",
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_price(ticker: str) -> float | None:
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).fast_info
        price = info.get("lastPrice") or info.get("last_price") or info.get("regularMarketPrice")
        if price:
            return float(price)
    except Exception:
        pass

    try:
        import yfinance as yf

        hist = yf.Ticker(ticker).history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass

    return None


def price_and_pe(company: str, quarterly_eps: float | None) -> tuple[float | None, float | None]:
    """Returns (price, pe). PE uses quarterly EPS annualized (x4) as an
    approximation of trailing-twelve-month EPS - flagged as such wherever
    it's displayed, since it's not true TTM."""
    ticker = TICKERS.get(company)
    if not ticker:
        return None, None
    price = get_price(ticker)
    if price is None or not quarterly_eps or quarterly_eps <= 0:
        return price, None
    pe = round(price / (quarterly_eps * 4), 1)
    return price, pe
