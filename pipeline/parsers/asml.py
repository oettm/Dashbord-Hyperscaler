"""ASML parser.

Press releases use a stable two-column layout: a label line, then the prior
quarter's number, then the current quarter's number (e.g. 'Total net sales /
9,718 / 8,767' where 8,767 is the quarter being reported). We take the SECOND
number as the value for the quarter this document is about.
"""
import re
from .common import find_two, find_sentence, pct

CURRENCY = "EUR"


def parse_press_release(text: str) -> dict:
    _, total_net_sales = find_two(text, "Total net sales")
    _, ibm_sales = find_two(text, "of which Installed Base Management sales")
    _, new_units = find_two(text, "New lithography systems sold (units)")
    _, used_units = find_two(text, "Used lithography systems sold (units)")
    _, gross_profit = find_two(text, "Gross profit")
    _, gross_margin = find_two(text, "Gross margin (%)")
    _, net_income = find_two(text, "Net income")
    _, eps = find_two(text, "EPS (basic; in euros)")
    _, cash = find_two(text, "investments")  # end-quarter cash & short-term investments

    new_systems_sales = None
    if total_net_sales is not None and ibm_sales is not None:
        new_systems_sales = round(total_net_sales - ibm_sales, 1)

    kpis = {
        "revenue": total_net_sales,
        "currency": CURRENCY,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin,
        "net_income": net_income,
        "eps_basic": eps,
        "cash_and_short_term_investments": cash,
        "new_lithography_systems_units": new_units,
        "used_lithography_systems_units": used_units,
    }

    business_units = []
    if new_systems_sales is not None:
        business_units.append({
            "name": "New Systems",
            "revenue": new_systems_sales,
            "currency": CURRENCY,
        })
    if ibm_sales is not None:
        business_units.append({
            "name": "Installed Base Management",
            "revenue": ibm_sales,
            "currency": CURRENCY,
        })

    # next-quarter + FY guidance ranges, e.g. "between €8.4 billion and €9.0 billion"
    guidance = {}
    m = re.search(
        r"expects? Q\d 2026 total net sales between\s*€([\d.]+) billion and €([\d.]+) billion,?\s*"
        r"and a gross margin between\s*(\d+)%\s*and\s*(\d+)%",
        text, re.I,
    )
    if m:
        guidance["next_quarter_net_sales_eur_bn"] = [float(m.group(1)), float(m.group(2))]
        guidance["next_quarter_gross_margin_pct"] = [float(m.group(3)), float(m.group(4))]
    m = re.search(
        r"total net sales to be between\s*€([\d.]+) billion and €([\d.]+) billion,?\s*"
        r"with a gross margin between\s*(\d+)%\s*and\s*(\d+)%",
        text, re.I,
    )
    if m:
        guidance["full_year_net_sales_eur_bn"] = [float(m.group(1)), float(m.group(2))]
        guidance["full_year_gross_margin_pct"] = [float(m.group(3)), float(m.group(4))]

    commentary = []
    quote = find_sentence(text, "CEO statement and outlook", window=900)
    if quote:
        commentary.append(quote)

    return {"kpis": kpis, "business_units": business_units, "guidance": guidance, "commentary": commentary}


def parse_presentation(text: str) -> dict:
    # The deck's only mention of "Outlook" as a standalone word is its own
    # agenda/table-of-contents entry, not the actual outlook slide - not
    # useful as a commentary snippet, so we don't try to extract one here.
    # The press release's CEO quote already covers this quarter's outlook.
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": []}


def parse_transcript(text: str) -> dict:
    commentary = []
    # grab a couple of substantive-looking paragraphs
    for kw in ["demand", "guidance"]:
        s = find_sentence(text, kw, window=350)
        if s:
            commentary.append(s)
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": commentary}


def parse(doc_type: str, text: str) -> dict:
    if doc_type == "press_release":
        return parse_press_release(text)
    if doc_type == "presentation":
        return parse_presentation(text)
    if doc_type == "transcript":
        return parse_transcript(text)
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": []}
