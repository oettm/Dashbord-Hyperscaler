import streamlit as st

from ..prices import price_and_pe
from ..utils import NA, essential_kpi_keys, fmt_delta, fmt_number, kpi_label


def render(comparison: dict, records: dict):
    st.header("Per-company: Q1 vs Q2")

    companies = sorted(comparison.keys())
    company = st.selectbox("Company", companies)
    comp = comparison[company]
    kpis = comp["kpis"]

    if not comp["q2_available"]:
        st.info(f"**Q2 is not available for {company}** in this dataset - showing Q1 only where noted.")

    keys = essential_kpi_keys(kpis)
    cols = st.columns(4)
    for i, key in enumerate(keys):
        row = kpis[key]
        with cols[i % 4]:
            q1_display = fmt_number(row["q1"])
            if row["q2"] == NA:
                st.metric(kpi_label(key), q1_display, "Q2: not available", delta_color="off")
            else:
                st.metric(kpi_label(key), fmt_number(row["q2"]), fmt_delta(row))
                st.caption(f"Q1: {q1_display}")

    # P/E: live price (yfinance) / annualized quarterly EPS - not a KPI from
    # the earnings documents, computed on the fly and clearly labeled as an
    # approximation (quarterly EPS x4 stands in for trailing-twelve-months).
    eps_key = next((k for k in ["diluted_eps", "eps_basic", "eps_usd_per_adr"] if k in kpis), None)
    if eps_key:
        current_eps = kpis[eps_key]["q2"] if kpis[eps_key]["q2"] != NA else kpis[eps_key]["q1"]
        price, pe = price_and_pe(company, current_eps if isinstance(current_eps, (int, float)) else None)
        with cols[len(keys) % 4]:
            if pe is not None:
                st.metric("P/E (approx.)", f"{pe}x")
                st.caption(f"Price {fmt_number(price)} / EPS x4")
            else:
                st.metric("P/E (approx.)", "not available")
                st.caption("No live price (offline or ticker unavailable)")
