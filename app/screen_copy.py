"""Parse a CDK parts-screen text copy. Columns come from the header, not gaps."""

from __future__ import annotations

import re

from app.quote import PART_RE, Quote, format_quote, format_quote_html

_HEADER_MARKERS = ("PART-NO", "LIST", "SALE")


def is_screen_copy(text: str) -> bool:
    upper = text.upper()
    return all(marker in upper for marker in _HEADER_MARKERS)


def _field(line: str, start: int, end: int) -> str:
    if start < 0 or start >= len(line):
        return ""
    chunk = line[start:end if end <= len(line) else len(line)]
    return chunk.strip(" │|├┤┌┐└┘─-")


def _header_indexes(header: str) -> dict[str, int]:
    labels = ("Q.S.", "PART-NO", "DESC", "O.H.", "BIN", "PRICE6", "LIST", "SALE", "GPP")
    found: dict[str, int] = {}
    for label in labels:
        idx = header.find(label)
        if idx >= 0:
            found[label] = idx
    return found


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
    header = next((ln for ln in lines if is_screen_copy(ln)), "")
    indexes = _header_indexes(header) if header else {}
    quote = Quote()
    blob = "\n".join(lines)
    ref = re.search(r"\bQ\d{3,}\b", blob, re.I)
    if ref:
        quote.ref = ref.group(0).upper()
    cust = re.search(r"\bCust\s*:?\s*(\d+)", blob, re.I)
    if cust:
        quote.cust = cust.group(1)
    quote.name = _labeled(blob, "Name")
    quote.addr = _labeled(blob, "Addr")
    quote.city = _labeled(blob, r"C\s*/\s*S\s*/\s*Z")
    phone = re.search(r"(\(?\d{3}\)?\s*\d{3}-?\d{4})", blob)
    if phone:
        quote.phone = re.sub(r"\)(?=\d)", ") ", phone.group(1))
    email = re.search(r"[\w.+-]+@[\w.-]+", blob)
    if email:
        quote.email = email.group(0)
    emp = re.search(r"\bEmp\s*:?\s*(\d+)", blob, re.I)
    if emp:
        quote.emp = emp.group(1)
    quote.via = _labeled(blob, "Via")
    quote.sale_type = _labeled(blob, "Sale Type")
    code = re.search(r"Price\s*Code\s*:?\s*(\d+)", blob, re.I)
    if code:
        quote.price_code = code.group(1)

    parsed: list[tuple[str, str, str, str, str]] = []
    if indexes:
        oh_at = indexes.get("O.H.", indexes.get("BIN", 10**6))
        for line in lines:
            if "PART-NO" in line.upper() and "LIST" in line.upper():
                continue
            part_match = PART_RE.search(line)
            if not part_match:
                continue
            part = part_match.group(0)
            left = line[: part_match.start()]
            qty_match = re.search(r"(\d+)\s*$", left)
            qty = qty_match.group(1) if qty_match else "1"
            desc = _slice(line, indexes, "DESC", "O.H.")
            if not desc:
                desc = line[part_match.end() : oh_at].strip(" │|-")
            list_price = _slice(line, indexes, "LIST", "SALE")
            cost = _slice(line, indexes, "SALE", "GPP")
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
