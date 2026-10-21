"""Turn a CDK quote screenshot's OCR boxes into aligned text."""

from __future__ import annotations

import re
from dataclasses import dataclass

PART_RE = re.compile(r"\b\d{3}(?:-\d{2,3}){2,5}\b")
MONEY_RE = re.compile(r"\b\d+\.\d{2}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+")
REF_RE = re.compile(r"\bQ\d{3,}\b", re.I)
_LABEL = re.compile(
    r"^(sale|type|fees|zone|parts|invoices|price|freight|tax|total|po|salesperson)\b",
    re.I,
)


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float
    text: str

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class Quote:
    ref: str = ""
    cust: str = ""
    name: str = ""
    addr: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    emp: str = ""
    via: str = ""
    sale_type: str = ""
    price_code: str = ""
    lines: list[tuple[str, str, str, str, str]] | None = None

    def __post_init__(self) -> None:
        if self.lines is None:
            self.lines = []


def _rows(boxes: list[Box]) -> list[list[Box]]:
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda b: (b.cy, b.x))
    heights = sorted(b.h for b in ordered if b.h > 0) or [16]
    tol = max(8.0, heights[len(heights) // 2] * 0.7)
    rows: list[list[Box]] = []
    for box in ordered:
        if rows and abs(box.cy - rows[-1][0].cy) <= tol:
            rows[-1].append(box)
        else:
            rows.append([box])
    for row in rows:
        row.sort(key=lambda b: b.x)
    return rows


def _after_colon(text: str) -> str:
    if ":" in text:
        return text.split(":", 1)[1].strip(" -")
    return text.strip()


def _join_row(row: list[Box]) -> str:
    return " ".join(b.text.strip() for b in row if b.text.strip())


def _clean_city(text: str) -> str:
    text = re.sub(r"[- ]Price.*$", "", text, flags=re.I).strip(" -")
    return text


def _addr_from_row(row: list[Box]) -> str:
    bits = []
    started = False
    for box in row:
        text = box.text.strip()
        if re.match(r"addr\s*:?", text, re.I):
            started = True
            rest = _after_colon(text)
            if rest:
                bits.append(rest)
            continue
        if not started:
            continue
        if _LABEL.match(text) or re.match(r"type\s*:", text, re.I):
            break
        # OCR sometimes glues the last address token to the Sale label.
        text = re.sub(r"sale$", "", text, flags=re.I).strip()
        if text:
            bits.append(text)
    return " ".join(bits).strip(" -")


def _via_from_blob(blob: str) -> str:
    m = re.search(r"via\s*:?\s*(.+)", blob, re.I)
    if not m:
        return ""
    rest = re.split(r"\bpo\b", m.group(1), flags=re.I)[0]
    return rest.strip(" :-")


def _phone(text: str) -> str:
    text = text.strip()
    return re.sub(r"\)(?=\d)", ") ", text)


def _header(rows: list[list[Box]], quote: Quote) -> None:
    for row in rows:
        blob = _join_row(row)
        low = blob.lower()
        if not quote.ref:
            m = REF_RE.search(blob)
            if m:
                quote.ref = m.group(0).upper()
        if not quote.cust and re.search(r"\bcust\b", low):
            m = re.search(r"cust\s*:?\s*(\d+)", blob, re.I)
            if m:
                quote.cust = m.group(1)
        if not quote.email:
            m = EMAIL_RE.search(blob)
            if m:
                quote.email = m.group(0)
        if not quote.name and re.search(r"\bname\b", low):
            words = []
            for box in row:
                t = box.text.strip()
                if re.match(r"name\s*:?", t, re.I):
                    rest = _after_colon(t)
                    if rest:
                        words.append(rest)
                    continue
                if re.match(r"^(zone|parts|invoices)\b", t, re.I):
                    break
                if t and not t.endswith(":"):
                    words.append(t)
            quote.name = " ".join(words).strip()
        if not quote.addr and re.search(r"\baddr\b", low):
            quote.addr = _addr_from_row(row)
        if not quote.city and re.search(r"c\s*/\s*s\s*/\s*z", low):
            m = re.search(r"c\s*/\s*s\s*/\s*z\s*:?\s*(.+)", blob, re.I)
            if m:
                quote.city = _clean_city(m.group(1))
            else:
                # value may sit in the next box on the row
                for box in row:
                    if re.search(r"[A-Z]{2}\s+\d{5}", box.text):
                        quote.city = _clean_city(box.text)
                        break
        if not quote.phone and re.search(r"phone", low):
            m = re.search(r"(\(?\d{3}\)?\s*\d{3}-?\d{4})", blob)
            if m:
                quote.phone = _phone(m.group(1))
        if not quote.emp and re.search(r"\bemp\b", low):
            m = re.search(r"emp\s*:?\s*(\d+)", blob, re.I)
            if m:
                quote.emp = m.group(1)
        if not quote.via and re.search(r"\bvia\b", low):
            quote.via = _via_from_blob(blob)
        if not quote.sale_type and re.search(r"\btype\b", low):
            m = re.search(r"type\s*:?\s*([A-Z0-9-]+)", blob, re.I)
            if m and m.group(1).upper() not in {"SALE"}:
                quote.sale_type = m.group(1)
        if not quote.price_code and re.search(r"ecode|price\s*code", low):
            m = re.search(r"(?:e\s*code|price\s*code)\s*:?\s*(\d+)", blob, re.I)
            if m:
                quote.price_code = m.group(1)


def _part_lines(rows: list[list[Box]]) -> list[tuple[str, str, str, str, str]]:
    found: list[tuple[str, str, str, str, str]] = []
    for row in rows:
        parts = [b for b in row if PART_RE.fullmatch(b.text.strip())]
        if not parts:
            continue
        for part in parts:
            same = [b for b in row if abs(b.cy - part.cy) <= max(part.h, 12)]
            left = [b for b in same if b.x + b.w < part.x + 4]
            right = [b for b in same if b.x > part.x + 4]
            qty = ""
            for b in reversed(left):
                if re.fullmatch(r"\d+", b.text.strip()):
                    qty = b.text.strip()
                    break
            moneys = []
            desc_bits = []
            for b in right:
                text = b.text.strip()
                if MONEY_RE.fullmatch(text):
                    moneys.append((b.x, text))
                elif re.fullmatch(r"[A-Za-z][A-Za-z0-9 /-]*", text):
                    # skip bin codes like 3018T; keep description words
                    if re.fullmatch(r"\d+[A-Za-z]\d*", text):
                        continue
                    desc_bits.append(text.upper())
            moneys.sort()
            list_price = moneys[-2][1] if len(moneys) >= 2 else (moneys[0][1] if moneys else "")
            cost = moneys[-1][1] if moneys else ""
            if len(moneys) >= 3:
                list_price = moneys[-2][1]
                cost = moneys[-1][1]
            desc = " ".join(desc_bits).strip()
            found.append((qty or "1", part.text.strip(), desc, list_price, cost))
    return found


def parse_boxes(boxes: list[Box]) -> Quote:
    rows = _rows(boxes)
    quote = Quote()
    _header(rows, quote)
    quote.lines = _part_lines(rows)
    return quote


def _col(value: str, width: int, align: str) -> str:
    if align == "right":
        return value.rjust(width)
    return value.ljust(width)


def format_quote(quote: Quote) -> str:
    lines: list[str] = []
    if quote.ref:
        lines.append(f"Ref # {quote.ref}")
    if quote.cust:
        lines.append(f"Cust# {quote.cust}")
    if quote.name:
        lines.append(f"Name: {quote.name}")
    if quote.addr:
        lines.append(f"Addr: {quote.addr}")
    if quote.city:
        lines.append(f"C/S/Z: {quote.city}")
    if quote.phone:
        lines.append(f"Phone: {quote.phone}")
    if quote.email:
        lines.append(f"Email: {quote.email}")
    if quote.emp:
        lines.append(f"Emp: {quote.emp}")
    if quote.via:
        lines.append(f"Via: {quote.via}")
    if quote.sale_type:
        lines.append(f"Sale Type: {quote.sale_type}")
    if quote.price_code:
        lines.append(f"Price Code: {quote.price_code}")
    if quote.lines:
        if lines:
            lines.append("")
        desc_w = max(4, max(len(r[2]) for r in quote.lines))
        part_w = max(8, max(len(r[1]) for r in quote.lines))
        # right-align money so LIST$ ends on the list figures and COST$ on cost
        header = "  ".join(
            [
                _col("QTY", 4, "right"),
                _col("PART-NO.", part_w, "left"),
                _col("DESC", desc_w, "left"),
                _col("LIST$", 7, "right"),
                _col("COST$", 7, "right"),
            ]
        )
        lines.append(header.rstrip())
        for qty, part, desc, list_price, cost in quote.lines:
            lines.append(
                "  ".join(
                    [
                        _col(qty, 4, "right"),
                        _col(part, part_w, "left"),
                        _col(desc, desc_w, "left"),
                        _col(list_price, 7, "right"),
                        _col(cost, 7, "right"),
                    ]
                ).rstrip()
            )
    return "\n".join(lines)
