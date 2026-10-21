"""Parse a CDK parts-screen text copy. Columns come from that screen's header."""

from __future__ import annotations

import re

from app.quote import PART_RE, Quote, format_quote, format_quote_html

# Sale Type contains "SALE", so the markers have to be on the table header line.
_SKIP_AFTER_LIST = {"Q.S.", "GPP", "SO"}
_COST_LABELS = ("SALE", "COMP", "COST", "NET")


def _norm_label(label: str) -> str:
    label = label.upper().rstrip(".")
    if label in {"Q.S", "QS"}:
        return "Q.S."
    if label in {"O.H", "OH"}:
        return "O.H."
    return label


def _header_labels(header: str) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for match in re.finditer(r"[A-Za-z][A-Za-z0-9.-]{0,12}", header):
        found.append((_norm_label(match.group(0)), match.start()))
    return found


def _header_line(lines: list[str]) -> str:
    for line in lines:
        labels = {name for name, _pos in _header_labels(line)}
        if "PART-NO" in labels and "LIST" in labels:
            return line
    return ""


def is_screen_copy(text: str) -> bool:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return bool(_header_line(lines))


def _field(line: str, start: int, end: int) -> str:
    if start < 0 or start >= len(line):
        return ""
    chunk = line[start:end if end <= len(line) else len(line)]
    return chunk.strip(" │|├┤┌┐└┘─-")


def _indexes(header: str) -> dict[str, int]:
    return {name: pos for name, pos in _header_labels(header)}


def _next_label(indexes: dict[str, int], key: str) -> str | None:
    ordered = sorted(indexes.items(), key=lambda item: item[1])
    for i, (name, _pos) in enumerate(ordered):
        if name == key and i + 1 < len(ordered):
            return ordered[i + 1][0]
    return None


def _cost_key(indexes: dict[str, int]) -> str:
    for name in _COST_LABELS:
        if name in indexes:
            return name
    nxt = _next_label(indexes, "LIST")
    if nxt and nxt not in _SKIP_AFTER_LIST:
        return nxt
    return ""


def _slice(line: str, indexes: dict[str, int], start_key: str, end_key: str | None) -> str:
    start = indexes.get(start_key, -1)
    if start < 0:
        return ""
    end = indexes.get(end_key, len(line)) if end_key else len(line)
    return _field(line, start, end)


def _labeled(text: str, label: str) -> str:
    match = re.search(rf"{label}\s*:?\s*(.+)", text, re.I)
    if not match:
        return ""
    rest = match.group(1)
    rest = re.split(
        r"\b(Invoices|Zone|Parts|Sale Type|Price Code|Salesperson|Fees|Freight|Tax|Total|PO)\b",
        rest,
        maxsplit=1,
        flags=re.I,
    )[0]
    return rest.strip(" :-")


def parse_screen_copy(text: str) -> Quote:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header = _header_line(lines)
    indexes = _indexes(header) if header else {}
    quote = Quote()
    blob = "\n".join(lines)
    ref = re.search(r"\bQ\d{3,}\b", blob, re.I)
    if ref:
        quote.ref = ref.group(0).upper()
    cust = re.search(r"\bCust\s*:?\s*(\d+)", blob, re.I)
    if cust:
        quote.cust = cust.group(1)
    quote.name = _labeled(blob, "Name")
    cost_key = _cost_key(indexes)
    cost_end = _next_label(indexes, cost_key) if cost_key else None
    parsed: list[tuple[str, str, str, str, str]] = []
    if indexes and cost_key:
        oh_at = indexes.get("O.H.", indexes.get("BIN", 10**6))
        for line in lines:
            if line == header or ("PART-NO" in line.upper() and "LIST" in line.upper()):
                continue
            part_match = PART_RE.search(line)
            if not part_match:
                continue
            part = part_match.group(0)
            if "Q.S." in indexes:
                qty = _slice(line, indexes, "Q.S.", _next_label(indexes, "Q.S.")) or "1"
            else:
                left = line[: part_match.start()]
                qty_match = re.search(r"(\d+)\s*$", left)
                qty = qty_match.group(1) if qty_match else "1"
            desc = line[part_match.end() : oh_at].strip(" │|-")
            if not desc:
                desc = _slice(line, indexes, "DESC", "O.H.")
            list_price = _slice(line, indexes, "LIST", cost_key)
            cost = _slice(line, indexes, cost_key, cost_end)
            parsed.append((qty, part, desc, list_price, cost))
    quote.lines = parsed
    return quote


def screen_copy_to_text(text: str) -> str:
    quote = parse_screen_copy(text)
    if not quote.lines:
        return ""
    return format_quote(quote)


def screen_copy_to_html(text: str) -> str:
    quote = parse_screen_copy(text)
    if not quote.lines:
        return ""
    return format_quote_html(quote)
