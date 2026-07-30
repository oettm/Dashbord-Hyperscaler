"""Shared helpers for the per-company KPI parsers: number parsing and
label-anchored regex search over extracted document text."""
import re
from typing import Optional


def to_number(raw: str) -> Optional[float]:
    """Parse a formatted number like '1,234.5', '(1,234)', '7.35' -> float.
    Parenthesized numbers are treated as negative (standard accounting convention).
    """
    if raw is None:
        return None
    s = raw.strip()
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    s = s.replace(",", "").replace("$", "").replace("€", "").replace("%", "").strip()
    if s in ("", "-", "N/A", "NM"):
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if negative else val


NUM = r"\(?\$?€?[\d,]+(?:\.\d+)?\)?"


def find_one(text: str, label: str, flags=re.I) -> Optional[float]:
    """Find `label` then the first number that follows it."""
    m = re.search(re.escape(label) + r"[^0-9\-]{0,80}?(" + NUM + ")", text, flags)
    return to_number(m.group(1)) if m else None


def find_labeled_pattern(text: str, pattern: str, group: int = 1, flags=re.I) -> Optional[float]:
    """Find a full custom regex `pattern` and parse `group` as a number."""
    m = re.search(pattern, text, flags)
    return to_number(m.group(group)) if m else None


def find_two(text: str, label: str, flags=re.I | re.M) -> tuple[Optional[float], Optional[float]]:
    """Find `label` sitting alone on its own line (as in ASML/Google press
    release tables: label line, then prior-quarter number line, then
    current-quarter number line) and return (prior, current). Anchoring to a
    standalone line avoids false matches inside prose that happens to mention
    the same words (e.g. a headline sentence containing 'total net sales').

    PDF text extraction sometimes puts a lone '$' on its own line right
    before a number column (Google's tables do this); we strip currency
    symbols first and tolerate blank filler lines between label and numbers.
    """
    clean = text.replace("$", " ").replace("€", " ")
    blank = r"(?:[ \t]*\n)*"
    m = re.search(
        r"^[ \t.]*" + re.escape(label) + r"\d{0,2}[ \t]*\n"
        + blank + r"[ \t]*(" + NUM + r")[ \t]*\n"
        + blank + r"[ \t]*(" + NUM + ")",
        clean,
        flags,
    )
    if not m:
        return None, None
    return to_number(m.group(1)), to_number(m.group(2))


def find_sentence(text: str, keyword: str, window: int = 400) -> Optional[str]:
    """Grab a short passage around the first occurrence of `keyword`, trimmed
    to sentence-ish boundaries, for use as qualitative commentary."""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return None
    start = max(0, idx - 20)
    end = min(len(text), idx + window)
    snippet = text[start:end]
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet


def pct(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator * 100, 2)
