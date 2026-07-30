import plotly.graph_objects as go
import streamlit as st

from ..utils import COMPANY_COLORS, NA, fmt_number, kpi_label


def render(cross_company: dict):
    st.header("Cross-company comparison")

    kpi_keys = sorted(cross_company.keys())
    default_idx = kpi_keys.index("revenue") if "revenue" in kpi_keys else 0
    key = st.selectbox("KPI", kpi_keys, index=default_idx, format_func=kpi_label)
    rows = cross_company[key]

    # Missing values must always sort to the bottom regardless of rank
    # direction, so the "is missing" flag is sorted ascending (ties go last)
    # while the value itself is negated instead of using reverse=True -
    # reverse=True would also flip the missing-flag ordering and float
    # "not available" rows to the top.
    sort_by = st.radio("Rank by", ["Q1 level", "Q2 level", "QoQ % growth"], horizontal=True)
    if sort_by == "Q1 level":
        rows = sorted(rows, key=lambda r: (r["q1"] is None, -(r["q1"] or 0)))
    elif sort_by == "Q2 level":
        rows = sorted(rows, key=lambda r: (r["q2"] == NA, -(r["q2"] if r["q2"] != NA else 0)))
    else:
        rows = sorted(rows, key=lambda r: (r["qoq_pct_delta"] is None, -(r["qoq_pct_delta"] or 0)))

    table_rows = [{
        "Company": r["company"],
        "Q1": fmt_number(r["q1"]),
        "Q2": fmt_number(r["q2"]) if r["q2"] != NA else NA,
        "QoQ %": f"{r['qoq_pct_delta']:+.1f}%" if r["qoq_pct_delta"] is not None else "—",
    } for r in rows]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.subheader(f"{kpi_label(key)} - Q1 vs Q2 by company")
    companies = [r["company"] for r in rows]
    q1_vals = [r["q1"] if isinstance(r["q1"], (int, float)) else None for r in rows]
    q2_vals = [r["q2"] if isinstance(r["q2"], (int, float)) else None for r in rows]
    colors = [COMPANY_COLORS.get(c, "#888888") for c in companies]

    fig = go.Figure()
    fig.add_bar(name="Q1", x=companies, y=q1_vals, marker_color=colors, opacity=0.55,
                marker_line_width=0)
    fig.add_bar(name="Q2", x=companies, y=q2_vals, marker_color=colors, opacity=1.0,
                marker_line_width=0)
    fig.update_layout(
        barmode="group",
        yaxis_title=kpi_label(key),
        legend_title_text="Quarter",
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    if any(v is None for v in q2_vals):
        st.caption("Bars missing for Q2 indicate companies where Q2 data is not available.")
