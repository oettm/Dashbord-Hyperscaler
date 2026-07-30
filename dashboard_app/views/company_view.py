import streamlit as st

from ..utils import HEADLINE_KPIS, NA, fmt_delta, fmt_number, kpi_label


def render(comparison: dict, records: dict):
    st.header("Per-company: Q1 vs Q2")

    companies = sorted(comparison.keys())
    company = st.selectbox("Company", companies)
    comp = comparison[company]
    kpis = comp["kpis"]

    if not comp["q2_available"]:
        st.info(f"**Q2 is not available for {company}** in this dataset - showing Q1 only where noted.")

    st.subheader("Headline KPIs")
    headline_keys = [k for k in HEADLINE_KPIS if k in kpis] or list(kpis)[:6]
    cols = st.columns(min(len(headline_keys), 4) or 1)
    for i, key in enumerate(headline_keys):
        row = kpis[key]
        with cols[i % len(cols)]:
            q1_display = fmt_number(row["q1"])
            if row["q2"] == NA:
                st.metric(kpi_label(key), q1_display, "Q2: not available", delta_color="off")
            else:
                st.metric(kpi_label(key), fmt_number(row["q2"]), fmt_delta(row))
                st.caption(f"Q1: {q1_display}")

    st.subheader("Full KPI comparison")
    table_rows = []
    for key, row in sorted(kpis.items()):
        table_rows.append({
            "KPI": kpi_label(key),
            "Q1": fmt_number(row["q1"]),
            "Q2": fmt_number(row["q2"]) if row["q2"] != NA else NA,
            "Δ abs": fmt_number(row["abs_delta"]) if row["abs_delta"] is not None else "—",
            "Δ %": f"{row['pct_delta']:+.1f}%" if row["pct_delta"] is not None else "—",
        })
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    guidance = comp.get("guidance", {})
    if guidance.get("q1") or guidance.get("q2"):
        st.subheader("Guidance")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**As of Q1**")
            st.json(guidance.get("q1") or {}, expanded=False)
        with g2:
            st.markdown("**As of Q2**" if comp["q2_available"] else "**As of Q2** — not available")
            st.json(guidance.get("q2") or {}, expanded=False)

    with st.expander("Source documents used for this company"):
        st.write("Q1:", comp["source_files"]["q1"] or "—")
        st.write("Q2:", comp["source_files"]["q2"] or NA)
