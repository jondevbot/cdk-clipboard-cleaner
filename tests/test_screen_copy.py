from app.screen_copy import screen_copy_to_text

# Column layout matches a CDK copy. Name, email, and address are fake.
# Row 3 has a shorter part and an empty bin, which shifts the gap, not the price columns.
SCREEN = """\
Number: Q000001                         parts@example.test COMMENT
  Cust: 10000                      Invoices:
  Name: EXAMPLE MOTORS                 Zone:                Parts:       100.00
  Addr: 1 EXAMPLE ST              Sale Type: CHECKWH         Fees:         0.00
 C/S/Z: SAMPLE CITY, CA 90000    Price Code: 24           Freight:         0.00
 Phone: (555)555-0100           Salesperson:                  Tax:         0.00
   Emp: 1000                                                Total:       100.00
   Via: WILL CALL            PO:
├Q.S.─PART-NO.──────────DESC─────O.H.─BIN─────PRICE6──LIST────SALE────GPP──────┤
│   1  213-900-52-29-80 REMAN CO    5     128  306.00  204.00  142.80 14.6     │
│   1  213-900-52-29-70 CORE CON    5     128   32.00   32.00   22.40 15.2     │
│   2     213-680-02-01 TRIM BAR    0          562.60  388.00  271.60 14.6     │
"""


def test_screen_copy_aligns_prices_when_bin_is_blank():
    text = screen_copy_to_text(SCREEN)
    assert "EXAMPLE MOTORS" in text
    assert "Addr:" not in text
    assert "Phone:" not in text
    assert "Sale Type:" not in text
    assert "BEACH" not in text
    header = next(ln for ln in text.splitlines() if "LIST$" in ln)
    rows = [ln for ln in text.splitlines() if "213-" in ln]
    assert header.split("\t") == ["QTY", "PART-NO.", "DESC", "LIST$", "COST$"]
    assert len(rows) == 3
    for ln, list_p, cost in (
        (rows[0], "204.00", "142.80"),
        (rows[1], "32.00", "22.40"),
        (rows[2], "388.00", "271.60"),
    ):
        cols = ln.split("\t")
        assert cols[3] == list_p
        assert cols[4] == cost
    assert "TRIM BAR" in rows[2]


# Different customer header: SO / COMP / Q.S. at the end, and a letter in the part number.
# Sale Type is on the screen, but it is not the SALE column. Values sit in the header columns.
_COMP_HEADER = "├SO───PART-NO.──────────────DESC─────O.H.─BIN─────PRICE6──LIST────COMP────Q.S.─────┤"


def _aligned_row(header: str, values: dict[str, str]) -> str:
    from app.screen_copy import _header_labels

    labels = _header_labels(header)
    ends = {name: labels[i + 1][1] if i + 1 < len(labels) else len(header) - 1 for i, (name, _pos) in enumerate(labels)}
    chars = [" "] * len(header)
    chars[0] = "│"
    chars[-1] = "│"
    for name, value in values.items():
        start = dict(labels)[name]
        width = ends[name] - start
        text = value[:width].ljust(width)
        chars[start : start + width] = list(text)
    return "".join(chars)


COMP_SCREEN = "\n".join(
    [
        "Number: Q000002                    Additional Customer Info",
        "Cust: 10001                  Invoices:",
        "Name: EXAMPLE BODY                 Zone:                Parts:       100.00",
        "Addr: 1 EXAMPLE ST           Sale Type: CHECKWH         Fees:         0.00",
        _COMP_HEADER,
        _aligned_row(
            _COMP_HEADER,
            {"SO": "401", "PART-NO": "907-914-01-00", "DESC": "SEAT CUSH", "O.H.": "2", "BIN": "3019C", "PRICE6": "504.60", "LIST": "348.00", "COMP": "280.00", "Q.S.": "1"},
        ),
        _aligned_row(
            _COMP_HEADER,
            {"SO": "401", "PART-NO": "907-910-61-03-9K49", "DESC": "OUTER COV", "O.H.": "2", "BIN": "3013T", "PRICE6": "408.90", "LIST": "282.00", "COMP": "226.00", "Q.S.": "1"},
        ),
        _aligned_row(
            _COMP_HEADER,
            {"SO": "402", "PART-NO": "907-820-99-00-64", "DESC": "SENSOR MA", "O.H.": "2", "BIN": "124", "PRICE6": "151.80", "LIST": "92.00", "COMP": "74.00", "Q.S.": "1"},
        ),
        _aligned_row(
            _COMP_HEADER,
            {"SO": "401", "PART-NO": "907-914-09-00", "DESC": "BACKREST", "O.H.": "0", "BIN": "", "PRICE6": "327.00", "LIST": "218.00", "COMP": "175.00", "Q.S.": "1"},
        ),
    ]
)


def test_comp_header_uses_qs_not_so_and_keeps_letter_part():
    text = screen_copy_to_text(COMP_SCREEN)
    assert "EXAMPLE BODY" in text
    assert "Sale Type" not in text
    rows = [ln for ln in text.splitlines() if "907-" in ln]
    assert len(rows) == 4
    assert rows[0].split("\t") == ["1", "907-914-01-00", "SEAT CUSH", "348.00", "280.00"]
    assert rows[1].split("\t")[1] == "907-910-61-03-9K49"
    assert rows[1].split("\t")[3:] == ["282.00", "226.00"]
    assert rows[2].split("\t")[3:] == ["92.00", "74.00"]
    assert rows[3].split("\t") == ["1", "907-914-09-00", "BACKREST", "218.00", "175.00"]
    assert all(row.split("\t")[0] == "1" for row in rows)
