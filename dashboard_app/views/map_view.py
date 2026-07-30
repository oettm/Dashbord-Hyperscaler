import pandas as pd
import plotly.express as px
import streamlit as st

from ..utils import COMPANY_COLORS
from pipeline.config import FACILITIES

# Two marker sizes/symbols so HQ reads as distinct from a production/data-
# center site at a glance, without relying on color alone (color already
# carries company identity).
_SIZE_BY_KIND = {"HQ": 16, "site": 10}


def _facilities_dataframe(companies: list[str]) -> pd.DataFrame:
    rows = []
    for company in companies:
        for f in FACILITIES.get(company, []):
            is_hq = "HQ" in f["type"]
            rows.append({
                "company": company,
                "name": f["name"],
                "type": f["type"],
                "country": f["country"],
                "lat": f["lat"],
                "lon": f["lon"],
                "kind": "HQ" if is_hq else "site",
                "size": _SIZE_BY_KIND["HQ" if is_hq else "site"],
            })
    return pd.DataFrame(rows)


def render():
    st.header("HQ & production sites")
    st.caption(
        "Manually curated from public company/investor-relations sources (not extracted from the "
        "earnings documents). For companies with dozens of sites (Vertiv's ~30 manufacturing/assembly "
        "facilities in 40+ countries; Microsoft/Google's hundreds of data centers) this is a "
        "representative subset, not an exhaustive list - see README for how to edit it."
    )

    all_companies = sorted(FACILITIES.keys())
    selected = st.multiselect("Companies", all_companies, default=all_companies)
    if not selected:
        st.info("Select at least one company.")
        return

    df = _facilities_dataframe(selected)

    # HQ vs. production/data-center site is encoded by marker size (HQ is
    # larger) plus the hover tooltip's "type" field, rather than a second
    # legend dimension - scatter_map's raster basemap doesn't support custom
    # marker symbols, and a size cue keeps company color as the one legend.
    fig = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        color="company",
        size="size",
        size_max=16,
        hover_name="name",
        hover_data={"type": True, "country": True, "lat": False, "lon": False, "size": False, "kind": False},
        color_discrete_map=COMPANY_COLORS,
        height=640,
        map_style="open-street-map",
        center={"lat": 25, "lon": 10},  # px's default (raw lat/lon mean) zooms into the
        zoom=1.0,                       # Mediterranean at zoom 8; this fits US-Europe-Asia instead.
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Company")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("All sites")
    table = df[["company", "name", "country", "type"]].sort_values(["company", "type"])
    st.dataframe(table.rename(columns={"name": "site", "type": "site type"}),
                 use_container_width=True, hide_index=True)
