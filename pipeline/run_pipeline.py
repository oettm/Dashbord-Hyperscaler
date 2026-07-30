"""Incremental extraction pipeline.

Walks the source folder, and for every earnings document not already parsed
(by content hash) extracts its text and runs it through the matching
company-specific KPI parser, writing one JSON record to data/parsed/ and
updating data/parsed/index.json. Files that haven't changed since the last
run are skipped entirely - safe to re-run any time after dropping new files
into the source folders.

Usage:
    python -m pipeline.run_pipeline           # incremental (default)
    python -m pipeline.run_pipeline --force   # re-parse everything
"""
import argparse
import json
import sys
from datetime import datetime, timezone

from . import config
from .discover import discover, _quarter_from_name
from .extract_text import file_hash, pdf_text, pptx_text
from .parsers import asml, google, tsmc, vertiv, msft

PARSER_MODULES = {
    "ASML": asml,
    "Google/Alphabet": google,
    "TSMC": tsmc,
    "Vertiv": vertiv,
}


def _load_index() -> dict:
    if config.INDEX_FILE.exists():
        return json.loads(config.INDEX_FILE.read_text())
    return {}


def _save_index(index: dict) -> None:
    config.INDEX_FILE.write_text(json.dumps(index, indent=2, sort_keys=True))


def _doc_id(rel_path: str, extra: str = "") -> str:
    safe = rel_path.replace("/", "__").replace(" ", "_").replace("(", "").replace(")", "")
    return f"{safe}{extra}.json"


def _parse_document(company: str, quarter: str, doc_type: str, path) -> dict:
    """Returns a parsed-document dict for any file except the MSFT workbook
    (which is handled separately since one file yields the Q1 record only)."""
    if path.suffix.lower() == ".pdf":
        text = pdf_text(path)
        extraction_status = "ok" if text.strip() else "empty"
    elif path.suffix.lower() == ".pptx":
        text, is_image_only = pptx_text(path)
        extraction_status = "no_text_layer" if is_image_only else ("ok" if text.strip() else "empty")
    else:
        text, extraction_status = "", "unsupported"

    result = {"kpis": {}, "business_units": [], "guidance": {}, "commentary": []}
    if extraction_status == "ok":
        if company == "Microsoft":
            pass  # MSFT has no per-doc-type parser; only the workbook is parsed for KPIs
        else:
            parser = PARSER_MODULES.get(company)
            if parser is not None:
                if company == "Google/Alphabet" and doc_type == "transcript":
                    has_pr = quarter == "Q1"  # only Q1 has a press release in this dataset
                    result = parser.parse_transcript(text, quarter, has_pr)
                else:
                    result = parser.parse(doc_type, text)

    return {
        "company": company,
        "quarter": quarter,
        "doc_type": doc_type,
        "rel_path": str(path.relative_to(config.SOURCE_DIR)),
        "extraction_status": extraction_status,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }


def run(force: bool = False) -> dict:
    index = {} if force else _load_index()
    files = discover()
    stats = {"parsed": 0, "skipped": 0, "errors": 0}

    for f in files:
        rel = f.rel_path
        h = file_hash(f.path)

        if not force and index.get(rel, {}).get("hash") == h:
            stats["skipped"] += 1
            continue

        try:
            if f.company == "Microsoft" and f.path.suffix.lower() == ".xlsx":
                parsed = msft.parse_workbook(f.path)
                doc = {
                    "company": "Microsoft",
                    "quarter": parsed["quarter"],
                    "doc_type": "financial_statement",
                    "rel_path": rel,
                    "extraction_status": "ok",
                    "parsed_at": datetime.now(timezone.utc).isoformat(),
                    "kpis": parsed["kpis"],
                    "business_units": parsed["business_units"],
                    "guidance": parsed["guidance"],
                    "commentary": parsed["commentary"],
                }
            elif f.path.suffix.lower() == ".pptx":
                quarter = f.quarter or _quarter_from_name(f.path.name)
                doc = _parse_document(f.company, quarter, f.doc_type, f.path)
            else:
                doc = _parse_document(f.company, f.quarter, f.doc_type, f.path)

            doc_id = _doc_id(rel)
            (config.PARSED_DIR / doc_id).write_text(json.dumps(doc, indent=2, sort_keys=True))
            index[rel] = {"hash": h, "doc_id": doc_id, "parsed_at": doc["parsed_at"]}
            stats["parsed"] += 1
            print(f"parsed  {f.company:20s} {str(f.quarter):4s} {f.doc_type:20s} {rel}")
        except Exception as e:  # noqa: BLE001 - keep going, report at the end
            stats["errors"] += 1
            print(f"ERROR   {rel}: {e}", file=sys.stderr)

    _save_index(index)
    print(f"\nDone. parsed={stats['parsed']} skipped(unchanged)={stats['skipped']} errors={stats['errors']}")
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-parse every file, ignoring the incremental cache")
    args = ap.parse_args()
    run(force=args.force)
