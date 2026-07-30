"""TSMC parser.

TSMC's press release is plain prose (no tables) with every headline figure
stated in a sentence, e.g. "TSMC today announced consolidated revenue of
NT$1,134.10 billion, net income of NT$572.48 billion... In US dollars, first
quarter revenue was $35.90 billion". The presentation deck adds a
'Revenue by Platform' pie chart (HPC/Smartphone/IoT/Automotive/DCE/Others) -
present for Q1 but the Q2 deck in this dataset renders it without an
extractable text layer, so that field is simply left absent for Q2 (not
fabricated). FS.pdf (financial statements) supplies balance-sheet debt/cash.
"""
import re
from .common import to_number, find_sentence

NTD = "NTD"
USD = "USD"

_PLATFORMS = ["HPC", "Smartphone", "IoT", "Automotive", "DCE", "Others"]


def parse_press_release(text: str) -> dict:
    kpis = {}

    m = re.search(
        r"consolidated revenue of\s*NT\$([\d,.]+)\s*billion,\s*net income of\s*NT\$([\d,.]+)\s*billion,\s*"
        r"and diluted earnings per share of\s*NT\$([\d.]+)\s*\(US\$([\d.]+)\s*per ADR unit\)",
        text, re.I,
    )
    if m:
        kpis["revenue_ntd_bn"] = to_number(m.group(1))
        kpis["net_income_ntd_bn"] = to_number(m.group(2))
        kpis["eps_ntd"] = to_number(m.group(3))
        kpis["eps_usd_per_adr"] = to_number(m.group(4))

    m = re.search(r"revenue was\s*\$([\d.]+)\s*billion", text, re.I)
    if m:
        kpis["revenue"] = to_number(m.group(1)) * 1000  # USD billions -> millions
        kpis["currency"] = USD

    m = re.search(
        r"Gross margin for the quarter was\s*([\d.]+)%,\s*operating margin was\s*([\d.]+)%,\s*"
        r"and net profit margin was\s*([\d.]+)%",
        text, re.I,
    )
    if m:
        kpis["gross_margin_pct"] = to_number(m.group(1))
        kpis["operating_margin_pct"] = to_number(m.group(2))
        kpis["net_margin_pct"] = to_number(m.group(3))

    guidance = {}
    m = re.search(
        r"Revenue is expected to be between\s*US\$([\d.]+)\s*billion and US\$([\d.]+)\s*billion", text, re.I
    )
    if m:
        guidance["next_quarter_revenue_usd_bn"] = [to_number(m.group(1)), to_number(m.group(2))]
    m = re.search(
        r"Gross profit margin is expected to be between\s*([\d.]+)%\s*and\s*([\d.]+)%", text, re.I
    )
    if m:
        guidance["next_quarter_gross_margin_pct"] = [to_number(m.group(1)), to_number(m.group(2))]
    m = re.search(
        r"Operating profit margin is expected to be between\s*([\d.]+)%\s*and\s*([\d.]+)%", text, re.I
    )
    if m:
        guidance["next_quarter_operating_margin_pct"] = [to_number(m.group(1)), to_number(m.group(2))]

    commentary = []
    quote = find_sentence(text, "said Wendell Huang", window=350)
    if quote:
        commentary.append(quote)

    return {"kpis": kpis, "business_units": [], "guidance": guidance, "commentary": commentary}


def parse_presentation(text: str) -> dict:
    """Extract the 'Revenue by Platform' breakdown when the chart has an
    extractable text layer (not guaranteed every quarter - see module docstring)."""
    business_units = []
    m = re.search(r"Revenue by Platform\s*\n((?:.|\n)*?)(?:\n\s*\n|\Z)", text, re.I)
    block = m.group(1) if m else ""
    for platform in _PLATFORMS:
        pm = re.search(re.escape(platform) + r"\s*\n\s*(\d+)\s*%", block, re.I)
        if pm:
            business_units.append({"name": platform, "share_of_revenue_pct": float(pm.group(1))})

    # "Balance Sheets & Key Indices" slide: label, then VALUE, then PCT%,
    # repeated for (this quarter / QoQ base / YoY base) - take the first value.
    kpis = {}
    m = re.search(r"Cash\s*&\s*Marketable Securities\s*\n\s*([\d,.]+)\s*\n\s*[\d.]+\s*%", text, re.I)
    if m:
        kpis["cash_and_marketable_securities_ntd_bn"] = to_number(m.group(1))
    m = re.search(r"Long-term Interest-bearing Debts\s*\n\s*([\d,.]+)\s*\n\s*[\d.]+\s*%", text, re.I)
    if m:
        kpis["long_term_debt_ntd_bn"] = to_number(m.group(1))
    if "cash_and_marketable_securities_ntd_bn" in kpis and "long_term_debt_ntd_bn" in kpis:
        kpis["net_cash_ntd_bn"] = round(
            kpis["cash_and_marketable_securities_ntd_bn"] - kpis["long_term_debt_ntd_bn"], 1
        )

    return {"kpis": kpis, "business_units": business_units, "guidance": {}, "commentary": []}


def parse_financial_statement(text: str) -> dict:
    """FS.pdf: pull balance-sheet cash/debt. TSMC typically carries very
    little debt and a large net-cash position, so we report both raw legs
    plus the computed net cash instead of a leverage ratio (leverage isn't a
    meaningful concept here, unlike Vertiv)."""
    kpis = {}
    m = re.search(
        r"Cash and Cash Equivalents\s*\n?\s*\$?\s*([\d,]+)\s*\n?\s*\$?\s*([\d,]+)", text, re.I
    )
    if m:
        kpis["cash_and_equivalents_usd_mn"] = to_number(m.group(1))

    # TSMC's cash-flow statement column layout changes shape by quarter: Q1
    # shows 4 numbers (USD-quarter, NTD-quarter, NTD-QoQ-base, NTD-YoY-base);
    # Q2+ inserts a "six months cumulative" pair in front, giving 5 numbers
    # (USD-cumulative, NTD-cumulative, NTD-THIS-quarter, NTD-prior-quarter,
    # NTD-YoY-quarter). We grab up to 5 trailing numbers and pick the single-
    # quarter NTD figure based on how many columns are actually present,
    # rather than assuming a fixed position.
    m = re.search(
        r"Net Cash Generated by Operating Activities\s*\n"
        r"((?:\s*\$?\s*\(?[\d,]+\)?\s*\n?){4,5})",
        text, re.I,
    )
    if m:
        nums = [to_number(n) for n in re.findall(r"\(?[\d,]+\)?", m.group(1))]
        if len(nums) == 4:
            kpis["operating_cash_flow_ntd_mn"] = nums[1]
        elif len(nums) >= 5:
            kpis["operating_cash_flow_ntd_mn"] = nums[2]

    return {"kpis": kpis, "business_units": [], "guidance": {}, "commentary": []}


def parse_transcript(text: str) -> dict:
    commentary = []
    for kw in ["second quarter 2026 to be", "demand"]:
        s = find_sentence(text, kw, window=350)
        if s:
            commentary.append(s)
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": commentary}


def parse(doc_type: str, text: str) -> dict:
    if doc_type == "press_release":
        return parse_press_release(text)
    if doc_type == "presentation":
        return parse_presentation(text)
    if doc_type == "financial_statement":
        return parse_financial_statement(text)
    if doc_type == "transcript":
        return parse_transcript(text)
    return {"kpis": {}, "business_units": [], "guidance": {}, "commentary": []}
