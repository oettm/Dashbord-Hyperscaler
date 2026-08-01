"""Build docs/index.html - a static, self-contained stock price page - from
stocks/data/prices.json. Run after fetch_prices.py, by the GitHub Actions
workflow or locally. GitHub Pages serves docs/ as-is, so this script's only
job is to produce one finished HTML file there.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

DATA_PATH = Path(__file__).resolve().parent / "data" / "prices.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "index.html"

# Same Okabe-Ito colorblind-safe palette as the main dashboard, so a given
# company reads as the same color in both places.
COMPANY_COLORS = {
    "ASML": "#0072B2",
    "Google/Alphabet": "#E69F00",
    "Microsoft": "#009E73",
    "TSMC": "#CC79A7",
    "Vertiv": "#D55E00",
}


def build_combined_chart(companies: dict) -> go.Figure:
    """All five on one chart. Raw prices span wildly different scales (ASML
    trades around 10x Vertiv's price) so plotting them together only works
    indexed to a common base (100 at each series' first available date) -
    the alternative, a second y-axis, is the #1 chart anti-pattern (two
    scales invite reading a spurious correlation into unrelated numbers)."""
    fig = go.Figure()
    for company, payload in companies.items():
        series = payload["series"]
        if not series:
            continue
        base = series[0]["close"]
        x = [p["date"] for p in series]
        y = [round(p["close"] / base * 100, 2) for p in series]
        fig.add_scatter(
            x=x, y=y, mode="lines", name=company,
            line=dict(color=COMPANY_COLORS.get(company, "#888888"), width=2),
        )
    fig.update_layout(
        title="All companies - indexed to 100 at first tracked date",
        yaxis_title="Indexed price (start = 100)",
        legend_title_text="Company",
        height=480,
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
    )
    return fig


def build_individual_chart(company: str, payload: dict) -> go.Figure:
    series = payload["series"]
    fig = go.Figure()
    if series:
        fig.add_scatter(
            x=[p["date"] for p in series], y=[p["close"] for p in series],
            mode="lines", name=company,
            line=dict(color=COMPANY_COLORS.get(company, "#888888"), width=2),
            showlegend=False,
        )
    fig.update_layout(
        title=f"{company} ({payload.get('symbol', '?')})",
        yaxis_title="Close price",
        height=340,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def main():
    if not DATA_PATH.exists():
        raise SystemExit(f"{DATA_PATH} not found - run fetch_prices.py first")
    data = json.loads(DATA_PATH.read_text())
    companies = data["companies"]

    combined_html = build_combined_chart(companies).to_html(full_html=False, include_plotlyjs="cdn")

    individual_html = ""
    for company, payload in companies.items():
        if not payload["series"]:
            individual_html += f'<div class="chart-card"><p class="missing">{company}: no data (fetch failed)</p></div>\n'
            continue
        fig_html = build_individual_chart(company, payload).to_html(full_html=False, include_plotlyjs=False)
        individual_html += f'<div class="chart-card">{fig_html}</div>\n'

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hyperscaler stock tracker</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px;
    background: #ffffff; color: #1a1a1a;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0e1117; color: #e6e6e6; }}
  }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
  .updated {{ color: #888; font-size: 0.9rem; margin-bottom: 28px; }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px; margin-top: 16px;
  }}
  .chart-card {{
    border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 8px;
    overflow-x: auto;
  }}
  .missing {{ padding: 40px; text-align: center; color: #888; }}
  section {{ margin-bottom: 40px; }}
</style>
</head>
<body>
  <h1>Hyperscaler stock tracker</h1>
  <p class="updated">Last updated {updated_at} - updates automatically once a day.
    Data: Twelve Data. Prices are the latest daily close, not real-time.</p>

  <section>
    <h2>All companies together</h2>
    {combined_html}
  </section>

  <section>
    <h2>Each company separately</h2>
    <div class="grid">
      {individual_html}
    </div>
  </section>
</body>
</html>
"""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(html)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
