"""Earnings dashboard entry point.

Run with:  streamlit run app.py
(from inside this `dashboard/` folder, or with its full path from anywhere)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from dashboard_app.utils import get_data
from dashboard_app.views import business_units_view, company_view, cross_company_view, notes_view

st.set_page_config(page_title="Earnings QoQ Dashboard", layout="wide")

comparison, cross_company, records = get_data()

st.sidebar.title("Earnings QoQ Dashboard")
if not comparison:
    st.sidebar.error("No data found. Run the pipeline first:")
    st.sidebar.code("python -m pipeline.run_pipeline\npython -m pipeline.build_qoq")
    st.stop()

page = st.sidebar.radio(
    "View",
    ["Per-company", "Cross-company", "Business units", "Qualitative notes"],
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Companies loaded: {', '.join(sorted(comparison.keys()))}")
st.sidebar.caption("Data is read from `data/qoq/`. After adding new files, rerun the pipeline "
                    "(see README) and refresh this page.")

if page == "Per-company":
    company_view.render(comparison, records)
elif page == "Cross-company":
    cross_company_view.render(cross_company)
elif page == "Business units":
    business_units_view.render(comparison)
elif page == "Qualitative notes":
    notes_view.render(comparison)
