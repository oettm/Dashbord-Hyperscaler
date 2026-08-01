"""Google/Alphabet parser.

Q1 has a full press release with clean two-column ('prior quarter / this
quarter') tables - handled the same way as ASML. Q2 has NO press release in
this dataset, so KPIs are instead pulled from the CFO's prose remarks in the
earnings call transcript (Alphabet's transcripts consistently restate every
headline number in sentence form, e.g. "Google Cloud revenues were up 82% to
$24.8 billion").
"""
import re
from .common import find_two, find_sentence

CURRENCY = "USD"


def parse_press_release(text: str) -> dict:
    _, revenue = find_two(text, "Total revenues")
    _, gs_search = find_two(text, "Google Search & other")
    _, gs_youtube = find_two(text, "YouTube ads")
    _, gs_network = find_two(text, "Google Network")
    _, gs_subs = find_two(text, "Google subscriptions, platforms, and devices")
    _, gs_total_rev = find_two(text, "Google Services total")
    _, cloud_rev = find_two(text, "Google Cloud")
    _, other_bets_rev = find_two(text, "Other Bets")
    _, op_income = find_two(text, "Operating income")
    _, net_income = find_two(text, "Net income")

    # segment operating income lives in its own "Operating income (loss):"
    # block further down the doc; scope the search to that block so we don't
    # re-match the revenue table's "Google Services"/"Google Cloud" lines.
    op_section = text.split("Operating income (loss):", 1)
    op_section = op_section[1] if len(op_section) > 1 else ""
    _, gs_op_income = find_two(op_section, "Google Services")
    _, cloud_op_income = find_two(op_section, "Google Cloud")
    _, other_bets_op_income = find_two(op_section, "Other Bets")

    _, ocf = find_two(text, "Net cash provided by operating activities")
    _, capex = find_two(text, "Purchases of property and equipment")
    _, cost_of_revenue = find_two(text, "Cost of revenues")
    _, total_debt = find_two(text, "Long-term debt")
    _, cash_and_marketable = find_two(text, "Total cash, cash equivalents, and marketable securities")

    fcf = None
    if ocf is not None and capex is not None:
        fcf = round(ocf + capex, 1)  # capex already negative

    op_margin = None
    if op_income is not None and revenue:
        op_margin = round(op_income / revenue * 100, 1)

    gross_profit = gross_margin_pct = None
    if cost_of_revenue is not None and revenue:
        gross_profit = round(revenue - cost_of_revenue, 1)
        gross_margin_pct = round(gross_profit / revenue * 100, 1)

    net_debt = None
    if total_debt is not None and cash_and_marketable is not None:
        net_debt = round(total_debt - cash_and_marketable, 1)  # negative = net cash

    m = re.search(r"EPS increased [\d.]+%\s*to\s*\$(\d+\.\d+)", text, re.I)
    eps = float(m.group(1)) if m else None

    kpis = {
        "revenue": revenue,
        "currency": CURRENCY,
        "cost_of_revenue": cost_of_revenue,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "operating_income": op_income,
        "operating_margin_pct": op_margin,
        "net_income": net_income,
        "diluted_eps": eps,
        "operating_cash_flow": ocf,
        "capex": capex,
        "free_cash_flow": fcf,
        "net_debt": net_debt,
    }

    business_units = []
    if gs_total_rev is not None:
        business_units.append({
            "name": "Google Services",
            "revenue": gs_total_rev,
            "operating_income": gs_op_income,
            "currency": CURRENCY,
            "detail": {
                "Search & other": gs_search,
                "YouTube ads": gs_youtube,
                "Google Network": gs_network,
                "Subscriptions/platforms/devices": gs_subs,
            },
        })
    if cloud_rev is not None:
        business_units.append({
            "name": "Google Cloud",
            "revenue": cloud_rev,
            "operating_income": cloud_op_income,
            "currency": CURRENCY,
        })
    if other_bets_rev is not None:
        business_units.append({
            "name": "Other Bets",
            "revenue": other_bets_rev,
            "operating_income": other_bets_op_income,
            "currency": CURRENCY,
        })

    guidance = {}  # Alphabet does not give quantitative forward guidance in the release

    commentary = []
    quote = find_sentence(text, "said:", window=700)
    if quote:
        commentary.append(quote)

    return {"kpis": kpis, "business_units": business_units, "guidance": guidance, "commentary": commentary}


_PROSE_PATTERNS = {
    "revenue": r"Consolidated revenues were \$([\d.]+)\s*billion",
    "cost_of_revenue": r"Total cost of revenues was \$([\d.]+)\s*billion",
    "operating_income": r"Operating income increased [\d.]+%\s*to\s*\$([\d.]+)\s*billion",
    "operating_cash_flow": r"operating cash flow of \$([\d.]+)\s*billion in the second quarter",
    "capex": r"CapEx was \$([\d.]+)\s*billion in the second quarter",
    "free_cash_flow": r"(?:negative )?free cash flow of (?:-?\$)?([\d.]+)\s*billion in the second quarter",
    "cash_and_marketable": r"\$([\d.]+)\s*billion in cash and marketable securities",
    "total_debt": r"[Ll]ong.term debt was \$([\d.]+)\s*billion",
}

_BU_PROSE_PATTERNS = {
    "Google Services": (
        r"Google Services revenues increased [\d.]+%\s*to\s*\$([\d.]+)\s*billion",
        r"Google Services operating income increased [\d.]+%\s*to\s*\$([\d.]+)\s*billion",
    ),
    "Google Cloud": (
        r"Cloud revenues were up [\d.]+%\s*to\s*\$([\d.]+)\s*billion",
        r"Cloud operating income was \$([\d.]+)\s*billion",
    ),
    "Other Bets": (
        r"In Other Bets, revenues were \$([\d.]+)\s*million",
        None,
    ),
}


def parse_transcript_as_financials(text: str) -> dict:
    """Best-effort fallback used only when there is no press release for the
    quarter (Google Q2 in this dataset): parse the CFO's stated figures out
    of the call transcript prose instead of a structured table."""
    kpis = {"currency": CURRENCY}
    for key, pattern in _PROSE_PATTERNS.items():
        m = re.search(pattern, text, re.I)
        if m:
            val = float(m.group(1))
            # normalize "million" for Other Bets-scale figures isn't needed here (all in billions)
            kpis[key] = round(val * 1000, 1)  # billions -> millions, consistent with press-release units
    if "operating_income" in kpis and kpis.get("revenue"):
        kpis["operating_margin_pct"] = round(kpis["operating_income"] / kpis["revenue"] * 100, 1)
    if "cost_of_revenue" in kpis and kpis.get("revenue"):
        gross_profit = round(kpis["revenue"] - kpis["cost_of_revenue"], 1)
        kpis["gross_profit"] = gross_profit
        kpis["gross_margin_pct"] = round(gross_profit / kpis["revenue"] * 100, 1)
    # free cash flow stated as "negative free cash flow of $5.9 billion" -> negative
    if re.search(r"negative free cash flow", text, re.I) and "free_cash_flow" in kpis:
        kpis["free_cash_flow"] = -kpis["free_cash_flow"]
    if "capex" in kpis:
        kpis["capex"] = -kpis["capex"]  # outflow, matches the sign convention used elsewhere
    # net_debt: derived from two prose-only intermediates, not KPIs in their own right
    cash_and_marketable = kpis.pop("cash_and_marketable", None)
    total_debt = kpis.pop("total_debt", None)
    if cash_and_marketable is not None and total_debt is not None:
        kpis["net_debt"] = round(total_debt - cash_and_marketable, 1)  # negative = net cash

    m = re.search(r"\$(\d+\.\d{2})\b", text)  # diluted EPS is the only "$X.XX" figure stated in the transcript
    if m:
        kpis["diluted_eps"] = float(m.group(1))

    business_units = []
    for name, (rev_pat, op_pat) in _BU_PROSE_PATTERNS.items():
        rev = None
        op = None
        m = re.search(rev_pat, text, re.I)
        if m:
            rev = float(m.group(1))
            if "million" in rev_pat:
                pass  # already in millions
            else:
                rev = round(rev * 1000, 1)  # billions -> millions
        if op_pat:
            m2 = re.search(op_pat, text, re.I)
            if m2:
                op = round(float(m2.group(1)) * 1000, 1)
        if rev is not None:
            business_units.append({"name": name, "revenue": rev, "operating_income": op, "currency": CURRENCY})

    commentary = []
    for kw in ["outstanding second quarter", "Turning to segment results", "Turning to our outlook"]:
        s = find_sentence(text, kw, window=500)
        if s:
            commentary.append(s)

    return {
        "kpis": kpis,
        "business_units": business_units,
        "guidance": {},
        "commentary": commentary,
        "extraction_source": "transcript_prose_fallback",
    }


def parse_presentation(text: str) -> dict:
    """The earnings slides deck restates diluted EPS as the only "$X.XX"
    (two-decimal dollar) figure anywhere on the income-statement slide - a
    reliable enough anchor to pull it out even though the slide's PDF text
    order otherwise doesn't follow visual reading order. Used mainly for Q2,
    where there's no press release to get EPS from directly; harmless for Q1
    since the press release's own EPS value takes priority when merged."""
    kpis = {}
    eps_matches = re.findall(r"\$(\d+\.\d{2})\b", text)
    if len(eps_matches) == 2:
        kpis["diluted_eps"] = float(eps_matches[0])
    return {"kpis": kpis, "business_units": [], "guidance": {}, "commentary": []}


def parse(doc_type: str, text: str) -> dict:
    if doc_type == "press_release":
        return parse_press_release(text)
    if doc_type == "presentation":
        return parse_presentation(text)
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": []}


def parse_transcript(text: str, quarter: str, has_press_release: bool) -> dict:
    if not has_press_release and quarter == "Q2":
        return parse_transcript_as_financials(text)
    commentary = []
    for kw in ["Turning to segment results", "outlook"]:
        s = find_sentence(text, kw, window=500)
        if s:
            commentary.append(s)
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": commentary}
