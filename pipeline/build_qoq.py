"""Build the QoQ (Q1 vs Q2) comparison layer from the parsed per-document
JSON files: one consolidated company-quarter record per company, a per-company
Q1-vs-Q2 KPI/BU comparison, and a cross-company ranking table.

Run after pipeline.run_pipeline. Pure aggregation - no PDF/Excel parsing here.

Usage:
    python -m pipeline.build_qoq
"""
import json
from collections import defaultdict

from . import config

DOC_TYPE_PRIORITY = {"press_release": 0, "financial_statement": 1, "presentation": 2, "transcript": 3, "other": 4}

# TSMC reports natively in NTD; these two keys need a USD conversion derived
# from that quarter's own revenue-implied exchange rate so cross-company
# tables can compare like-for-like.
_TSMC_NTD_TO_USD_KEYS = {
    "operating_cash_flow_ntd_mn": "operating_cash_flow",
    "net_cash_ntd_bn": "net_cash",  # -> USD millions
}


def _load_all_docs() -> list[dict]:
    docs = []
    for path in sorted(config.PARSED_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        docs.append(json.loads(path.read_text()))
    return docs


def _merge_kpis(docs: list[dict]) -> dict:
    merged = {}
    for doc in sorted(docs, key=lambda d: DOC_TYPE_PRIORITY.get(d["doc_type"], 9), reverse=True):
        for k, v in doc.get("kpis", {}).items():
            if v is not None:
                merged[k] = v  # later (higher-priority, since we iterate low->high reversed) overwrites
    return merged


def _merge_business_units(docs: list[dict]) -> dict:
    """Returns {bu_name: merged_fields}, merged in doc-type priority order
    (same rule as _merge_kpis) so a press release's numbers win over a
    presentation's when both mention the same segment."""
    merged: dict[str, dict] = {}
    for doc in sorted(docs, key=lambda d: DOC_TYPE_PRIORITY.get(d["doc_type"], 9), reverse=True):
        for bu in doc.get("business_units", []):
            name = bu["name"]
            merged.setdefault(name, {})
            for k, v in bu.items():
                if k != "name" and v is not None:
                    merged[name][k] = v
    return merged


def _merge_guidance(docs: list[dict]) -> dict:
    merged = {}
    for doc in docs:
        merged.update({k: v for k, v in doc.get("guidance", {}).items() if v is not None})
    return merged


def _merge_commentary(docs: list[dict]) -> list[str]:
    seen = []
    for doc in docs:
        for c in doc.get("commentary", []):
            if c and c not in seen:
                seen.append(c)
    return seen


def _apply_tsmc_fx(kpis: dict) -> dict:
    if "revenue_ntd_bn" not in kpis or "revenue" not in kpis:
        return kpis
    rate = kpis["revenue_ntd_bn"] * 1000 / kpis["revenue"]  # NTD per USD, implied by this quarter's own figures
    for ntd_key, usd_key in _TSMC_NTD_TO_USD_KEYS.items():
        if ntd_key in kpis:
            unit = 1000 if ntd_key.endswith("_bn") else 1  # _bn -> millions before conversion
            kpis[usd_key] = round(kpis[ntd_key] * unit / rate, 1)
    kpis["implied_ntd_per_usd"] = round(rate, 2)
    return kpis


def build_company_quarter_records(docs: list[dict]) -> dict:
    """{company: {quarter: {kpis, business_units, guidance, commentary, doc_types_used}}}"""
    grouped = defaultdict(list)
    for doc in docs:
        if doc.get("quarter") not in ("Q1", "Q2"):
            continue
        grouped[(doc["company"], doc["quarter"])].append(doc)

    records: dict = defaultdict(dict)
    for (company, quarter), company_docs in grouped.items():
        kpis = _merge_kpis(company_docs)
        if company == "TSMC":
            kpis = _apply_tsmc_fx(kpis)
        records[company][quarter] = {
            "kpis": kpis,
            "business_units": _merge_business_units(company_docs),
            "guidance": _merge_guidance(company_docs),
            "commentary": _merge_commentary(company_docs),
            "doc_types_used": sorted({d["doc_type"] for d in company_docs}),
            "source_files": sorted({d["rel_path"] for d in company_docs}),
        }
    return records


def _delta(q1, q2):
    if q1 is None or q2 is None:
        return None, None
    if not isinstance(q1, (int, float)) or not isinstance(q2, (int, float)):
        return None, None
    abs_delta = round(q2 - q1, 2)
    pct_delta = round((q2 - q1) / q1 * 100, 2) if q1 != 0 else None
    return abs_delta, pct_delta


def build_qoq_comparison(records: dict) -> dict:
    """Per-company Q1-vs-Q2 KPI comparison. If a company has no Q2 record at
    all, every KPI is explicitly marked unavailable rather than omitted."""
    comparison = {}
    for company, quarters in records.items():
        q1 = quarters.get("Q1", {})
        q2 = quarters.get("Q2")  # may be entirely absent (Vertiv), or present but
        # data-free (Microsoft's Q2 "record" is only an image-only presentation
        # with no extractable KPIs) - either way that's "not available" to us.
        if not (q2 and (q2.get("kpis") or q2.get("business_units"))):
            q2 = None
        q1_kpis = q1.get("kpis", {})
        q2_kpis = (q2 or {}).get("kpis", {})

        # A field reads "not available" whenever IT has no value, regardless
        # of whether that's because the whole quarter is missing (Vertiv,
        # Microsoft) or just that one field wasn't extracted from an
        # otherwise-populated quarter (e.g. TSMC's Q2 platform mix) - the
        # dashboard shouldn't have to tell those two cases apart.
        all_keys = sorted(set(q1_kpis) | set(q2_kpis))
        kpi_rows = {}
        for key in all_keys:
            v1 = q1_kpis.get(key)
            v2 = q2_kpis.get(key)
            abs_delta, pct_delta = _delta(v1, v2)
            kpi_rows[key] = {
                "q1": v1,
                "q2": v2 if v2 is not None else "not available",
                "abs_delta": abs_delta,
                "pct_delta": pct_delta,
            }

        # business units QoQ
        bu_names = sorted(set(q1.get("business_units", {})) | set((q2 or {}).get("business_units", {})))
        bu_rows = {}
        for name in bu_names:
            b1 = q1.get("business_units", {}).get(name, {})
            b2 = (q2 or {}).get("business_units", {}).get(name, {})
            row = {}
            for field in sorted(set(b1) | set(b2)):
                v1 = b1.get(field)
                v2 = b2.get(field)
                abs_delta, pct_delta = _delta(v1, v2)
                row[field] = {
                    "q1": v1,
                    "q2": v2 if v2 is not None else "not available",
                    "abs_delta": abs_delta,
                    "pct_delta": pct_delta,
                }
            bu_rows[name] = row

        comparison[company] = {
            "q2_available": q2 is not None,
            "kpis": kpi_rows,
            "business_units": bu_rows,
            "guidance": {"q1": q1.get("guidance", {}), "q2": (q2 or {}).get("guidance", {})},
            "commentary": {"q1": q1.get("commentary", []), "q2": (q2 or {}).get("commentary", [])},
            "source_files": {"q1": q1.get("source_files", []), "q2": (q2 or {}).get("source_files", [])},
        }
    return comparison


def build_cross_company(records: dict) -> dict:
    """For every KPI that appears for at least one company, a ranking table
    of Q1 level, Q2 level, and QoQ % growth across all companies."""
    all_kpi_keys = set()
    for quarters in records.values():
        for q in quarters.values():
            all_kpi_keys.update(q.get("kpis", {}).keys())

    tables = {}
    for key in sorted(all_kpi_keys):
        rows = []
        for company, quarters in records.items():
            q2_has_data = bool(quarters.get("Q2", {}).get("kpis"))
            q1_val = quarters.get("Q1", {}).get("kpis", {}).get(key)
            q2_val = quarters.get("Q2", {}).get("kpis", {}).get(key) if q2_has_data else None
            _, pct_delta = _delta(q1_val, q2_val)
            rows.append({
                "company": company,
                "q1": q1_val,
                "q2": q2_val if q2_has_data else "not available",
                "qoq_pct_delta": pct_delta,
            })
        tables[key] = rows
    return tables


def main():
    docs = _load_all_docs()
    records = build_company_quarter_records(docs)
    comparison = build_qoq_comparison(records)
    cross_company = build_cross_company(records)

    (config.QOQ_DIR / "company_quarter_records.json").write_text(json.dumps(records, indent=2, sort_keys=True))
    (config.QOQ_DIR / "qoq_comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True))
    (config.QOQ_DIR / "cross_company.json").write_text(json.dumps(cross_company, indent=2, sort_keys=True))

    print(f"Wrote QoQ outputs for {len(records)} companies to {config.QOQ_DIR}")
    for company, comp in comparison.items():
        print(f"  {company:20s} Q2 available: {comp['q2_available']}")


if __name__ == "__main__":
    main()
