"""Walk the source folder and classify every earnings document.

Produces a flat list of DiscoveredFile records: company, quarter (Q1/Q2/None),
doc_type, absolute path. Quarter detection uses the Q1/Q2 subfolder when
present, falling back to filename patterns (used by Google and MSFT, which
don't use per-quarter subfolders).
"""
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional

from . import config

SUPPORTED_EXTS = {".pdf", ".pptx", ".xlsx"}


@dataclass
class DiscoveredFile:
    company: str
    quarter: Optional[str]  # "Q1" / "Q2" / None if undetermined
    doc_type: str
    path: Path

    @property
    def rel_path(self) -> str:
        return str(self.path.relative_to(config.SOURCE_DIR))


def _normalize(name: str) -> str:
    n = name.lower()
    for ch in "-_()":
        n = n.replace(ch, " ")
    return re.sub(r"\s+", " ", n).strip()


def _classify_doc_type(name: str) -> str:
    n = _normalize(name)
    if "press release" in n or "earnings release" in n or "earningsrelease" in n:
        return "press_release"
    if "transcript" in n:
        return "transcript"
    if "presentation" in n or "slides" in n or "outlook" in n:
        return "presentation"
    if n == "fs.pdf" or "statements" in n or "financial results" in n:
        return "financial_statement"
    return "other"


def _quarter_from_name(name: str) -> Optional[str]:
    n = _normalize(name)
    if re.search(r"(?:^|[^a-z0-9])q1(?:[^a-z0-9]|$)", n) or re.search(r"\b1q\d{2}\b", n) \
            or re.search(r"\d{4} ?q1\b", n) or re.search(r"fy\d{2}q1\b", n) or "first quarter" in n:
        return "Q1"
    if re.search(r"(?:^|[^a-z0-9])q2(?:[^a-z0-9]|$)", n) or re.search(r"\b2q\d{2}\b", n) \
            or re.search(r"\d{4} ?q2\b", n) or re.search(r"fy\d{2}q2\b", n) or "second quarter" in n:
        return "Q2"
    return None


def discover(source_dir: Path = config.SOURCE_DIR) -> list[DiscoveredFile]:
    results: list[DiscoveredFile] = []

    for company_dir in sorted(source_dir.iterdir()):
        if not company_dir.is_dir():
            continue
        folder_name = company_dir.name.strip()
        if folder_name in config.IGNORED_DIR_NAMES or folder_name.startswith("."):
            continue
        company = config.COMPANY_FOLDER_MAP.get(folder_name, folder_name)

        for path in sorted(company_dir.rglob("*")):
            if path.is_dir():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTS:
                continue
            if path.name.startswith("."):
                continue

            # quarter: prefer an explicit Q1/Q2 parent folder, else filename
            quarter = None
            for parent in path.relative_to(company_dir).parts[:-1]:
                if parent.upper() in config.QUARTERS:
                    quarter = parent.upper()
                    break
            if quarter is None:
                quarter = _quarter_from_name(path.name)

            doc_type = _classify_doc_type(path.name)
            # the MSFT workbook covers whichever quarters it has columns for;
            # leave quarter unset here, the MSFT parser resolves it internally.
            if path.suffix.lower() == ".xlsx":
                quarter = None

            results.append(DiscoveredFile(company=company, quarter=quarter, doc_type=doc_type, path=path))

    return results


if __name__ == "__main__":
    for f in discover():
        print(f"{f.company:20s} {str(f.quarter):4s} {f.doc_type:20s} {f.rel_path}")
