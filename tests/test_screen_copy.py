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
    assert "BEACH" not in text
    header = next(ln for ln in text.splitlines() if "LIST$" in ln)
    rows = [ln for ln in text.splitlines() if "213-" in ln]
    assert len(rows) == 3
    for ln, list_p, cost in (
        (rows[0], "204.00", "142.80"),
        (rows[1], "32.00", "22.40"),
        (rows[2], "388.00", "271.60"),
    ):
        assert header.index("LIST$") + len("LIST$") == ln.index(list_p) + len(list_p)
        assert header.index("COST$") + len("COST$") == ln.index(cost) + len(cost)
    assert "TRIM BAR" in rows[2]
