"""Fetch daily closing prices for the five companies from Twelve Data and
save them to stocks/data/prices.json. Run daily by the GitHub Actions
workflow (.github/workflows/update_stocks.yml); safe to run locally too if
TWELVE_DATA_API_KEY is set in the environment.

Plain US-listed tickers are used for all five (including ASML, which trades
as a USD ADR on Nasdaq under the same symbol) - unlike the main dashboard's
P/E calculation, a price chart has no EPS-currency to match, so there's no
reason to deal with exchange codes here.
"""
import json
import os
import sys
from pathlib import Path

import requests

TICKERS = {
    "ASML": "ASML",
    "Google/Alphabet": "GOOGL",
    "Microsoft": "MSFT",
    "TSMC": "TSM",
    "Vertiv": "VRT",
}

API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
OUT_PATH = Path(__file__).resolve().parent / "data" / "prices.json"
OUTPUT_SIZE = 180  # trading days of history to keep (~9 months)


def fetch_series(symbol: str) -> list[dict]:
    resp = requests.get(
        "https://api.twelvedata.com/time_series",
        params={"symbol": symbol, "interval": "1day", "outputsize": OUTPUT_SIZE, "apikey": API_KEY},
        timeout=20,
    )
    data = resp.json()
    if not isinstance(data, dict) or "values" not in data:
        print(f"ERROR fetching {symbol}: {data}", file=sys.stderr)
        return []
    return sorted(
        ({"date": v["datetime"], "close": float(v["close"])} for v in data["values"]),
        key=lambda x: x["date"],
    )


def main():
    if not API_KEY:
        print("TWELVE_DATA_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    result = {"tickers": TICKERS, "companies": {}}
    had_error = False
    for company, symbol in TICKERS.items():
        series = fetch_series(symbol)
        if not series:
            had_error = True
        result["companies"][company] = {"symbol": symbol, "series": series}
        print(f"{company} ({symbol}): {len(series)} points")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"Wrote {OUT_PATH}")

    if had_error:
        sys.exit(1)  # non-zero exit fails the Actions run visibly, but the (partial) file is still saved


if __name__ == "__main__":
    main()
