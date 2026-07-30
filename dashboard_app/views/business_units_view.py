import plotly.graph_objects as go
import streamlit as st

from ..utils import NA, fmt_number
from pipeline.config import BUSINESS_UNIT_DESCRIPTIONS


def render(comparison: dict):
    st.header("Business units")
    st.caption(
        "What each segment is, how it performed Q1 vs Q2, and the outlook mentioned for it. "
        "Where a document doesn't break guidance out by segment, the company-level guidance is "
        "shown instead and labeled as such."
    )

    companies = sorted(comparison.keys())
    company = st.selectbox("Company", companies, key="bu_company")
    comp = comparison[company]
    bus = comp["business_units"]
    descriptions = BUSINESS_UNIT_DESCRIPTIONS.get(company, {})

    if not bus:
        st.warning(f"No business-unit / segment breakdown was extracted for {company}.")
        return

    if not comp["q2_available"]:
        st.info(f"Q2 is not available for {company} - showing Q1 business-unit figures only.")

    for name, fields in bus.items():
        with st.container(border=True):
            st.subheader(name)
            desc = descriptions.get(name)
            if desc:
                st.caption(desc)

            metric_cols = st.columns(3)
            for i, metric_key in enumerate(["revenue", "operating_income", "operating_margin_pct"]):
                if metric_key not in fields:
                    continue
                row = fields[metric_key]
                label = {"revenue": "Revenue", "operating_income": "Operating income",
                         "operating_margin_pct": "Operating margin %"}[metric_key]
                with metric_cols[i]:
                    if row["q2"] == NA:
                        st.metric(label, fmt_number(row["q1"]), "Q2: not available", delta_color="off")
                        st.caption("Q1 value shown (Q2 unavailable)")
                    else:
                        pct = row.get("pct_delta")
                        delta_str = f"{pct:+.1f}%" if pct is not None else None
                        st.metric(label, fmt_number(row["q2"]), delta_str)
                        st.caption(f"Q1: {fmt_number(row['q1'])}")

            if "revenue" in fields and fields["revenue"]["q2"] not in (None, NA):
                fig = go.Figure()
                fig.add_bar(x=["Q1", "Q2"], y=[fields["revenue"]["q1"], fields["revenue"]["q2"]],
                            marker_color=["#8a8a8a", "#0072B2"])
                fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                                   yaxis_title="Revenue")
                st.plotly_chart(fig, use_container_width=True, key=f"{company}-{name}-chart")

            share = fields.get("share_of_revenue_pct")
            if share is not None:
                q2_missing = share["q2"] in (None, NA)
                st.write(f"Share of total revenue - Q1: {fmt_number(share['q1'])}%"
                         + (", Q2: not available" if q2_missing else f", Q2: {fmt_number(share['q2'])}%"))

    guidance = comp.get("guidance", {})
    company_guidance = guidance.get("q2") or guidance.get("q1")
    if company_guidance:
        st.subheader("Outlook (company-level)")
        st.caption("These documents don't break guidance out by business unit; shown here for context.")
        st.json(company_guidance, expanded=False)
