"""Data loading and formatting helpers shared by every dashboard view."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as pipeline_config  # noqa: E402

# Fixed company -> color mapping (Okabe-Ito colorblind-safe palette), reused
# across every chart so a given company always reads as the same color.
COMPANY_COLORS = {
    "ASML": "#0072B2",
    "Google/Alphabet": "#E69F00",
    "Microsoft": "#009E73",
    "TSMC": "#CC79A7",
    "Vertiv": "#D55E00",
}

NA = "not available"

KPI_LABELS = {
    "revenue": "Revenue (USD mn)",
    "revenue_ntd_bn": "Revenue (NTD bn)",
    "gross_profit": "Gross profit",
    "gross_margin_pct": "Gross margin %",
    "operating_income": "Operating income",
    "operating_margin_pct": "Operating margin %",
    "net_income": "Net income",
    "net_income_ntd_bn": "Net income (NTD bn)",
    "net_margin_pct": "Net margin %",
    "operating_cash_flow": "Operating cash flow (USD mn)",
    "operating_cash_flow_ntd_mn": "Operating cash flow (NTD mn)",
    "capex": "Capex",
    "free_cash_flow": "Free cash flow",
    "adjusted_operating_profit": "Adjusted operating profit",
    "adjusted_operating_margin_pct": "Adjusted operating margin %",
    "adjusted_free_cash_flow": "Adjusted free cash flow",
    "net_leverage_x": "Net leverage (x)",
    "net_debt": "Net debt (USD mn)",
    "net_cash": "Net cash (USD mn)",
    "net_cash_ntd_bn": "Net cash (NTD bn)",
    "long_term_debt_ntd_bn": "Long-term debt (NTD bn)",
    "cash_and_short_term_investments": "Cash & short-term investments",
    "cash_and_equivalents_usd_mn": "Cash & equivalents (USD mn)",
    "cash_and_marketable_securities_ntd_bn": "Cash & marketable securities (NTD bn)",
    "eps_basic": "EPS (basic)",
    "eps_ntd": "EPS (NTD)",
    "eps_usd_per_adr": "EPS (USD / ADR)",
    "diluted_eps": "Diluted EPS",
    "new_lithography_systems_units": "New lithography systems sold (units)",
    "used_lithography_systems_units": "Used lithography systems sold (units)",
    "currency": "Reporting currency",
    "implied_ntd_per_usd": "Implied NTD/USD rate",
}

# The essentials view shows exactly these seven KPIs (plus a live-computed
# P/E as an eighth) - nothing else. "Net debt" has three possible source
# fields depending on the company (Google/MSFT report net_debt directly,
# TSMC reports the mirror-image net_cash, Vertiv reports a leverage ratio
# instead of a dollar figure) - each is shown under its own correct label
# rather than forced into one field name with the wrong sign.
ESSENTIAL_KPIS = [
    ("revenue", None),
    ("gross_margin_pct", None),
    ("operating_cash_flow", None),
    ("free_cash_flow", None),
    ("capex", None),
    ("net_debt", ["net_debt", "net_cash", "net_leverage_x"]),
    ("eps", ["diluted_eps", "eps_basic", "eps_usd_per_adr"]),
]


# Flat version of the same essentials, used to filter the cross-company KPI
# picker - it can't resolve "whichever field this company happens to use"
# per row the way the per-company view does, so it just offers every field
# name that maps to one of the essential concepts.
CROSS_COMPANY_ESSENTIAL_KEYS = [
    "revenue", "gross_margin_pct", "operating_cash_flow", "free_cash_flow", "capex",
    "net_debt", "net_cash", "net_leverage_x",
    "diluted_eps", "eps_basic", "eps_usd_per_adr",
]


def essential_kpi_keys(kpis: dict) -> list[str]:
    """Resolve ESSENTIAL_KPIS against one company's kpi dict, returning the
    actual field name to show for each row (skipping rows with no data at
    all for this company, e.g. Vertiv has no gross_margin_pct)."""
    keys = []
    for primary, candidates in ESSENTIAL_KPIS:
        for candidate in candidates or [primary]:
            if candidate in kpis:
                keys.append(candidate)
                break
    return keys


def kpi_label(key: str) -> str:
    return KPI_LABELS.get(key, key.replace("_", " ").capitalize())


def _mtime_key() -> float:
    """Cache-busting key: newest mtime among the qoq output files, so the UI
    picks up changes automatically after a pipeline re-run without needing an
    app restart."""
    files = list(pipeline_config.QOQ_DIR.glob("*.json"))
    return max((f.stat().st_mtime for f in files), default=0.0)


@st.cache_data
def load_qoq_comparison(_cache_key: float):
    path = pipeline_config.QOQ_DIR / "qoq_comparison.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@st.cache_data
def load_cross_company(_cache_key: float):
    path = pipeline_config.QOQ_DIR / "cross_company.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@st.cache_data
def load_records(_cache_key: float):
    path = pipeline_config.QOQ_DIR / "company_quarter_records.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def get_data():
    key = _mtime_key()
    return (
        load_qoq_comparison(key),
        load_cross_company(key),
        load_records(key),
    )


def fmt_number(value, unit: str = "") -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    if abs(value) >= 1000:
        s = f"{value:,.0f}"
    elif abs(value) >= 1:
        s = f"{value:,.1f}"
    else:
        s = f"{value:,.2f}"
    return f"{s}{unit}"


def fmt_pct(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    return f"{value:+.1f}%" if isinstance(value, (int, float)) else str(value)


def fmt_delta(row: dict) -> str:
    """Human string for a {q1,q2,abs_delta,pct_delta} row's Q2-vs-Q1 change."""
    if row.get("q2") == NA:
        return NA
    pct = row.get("pct_delta")
    if pct is None:
        return ""
    arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "→")
    return f"{arrow} {pct:+.1f}%"
