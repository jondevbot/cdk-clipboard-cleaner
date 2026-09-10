"""Click → clean CDK part numbers on the clipboard → exit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.cleaner import clean_text

SAMPLE_IN = """906-697-60-98-64
   906-887-00-72
   006-990-43-40
   000-998-04-46
   001-992-02-05
   140-990-06-36
910143-008003-64
   901-993-09-20"""

SAMPLE_OUT = """906697609864
9068870072
0069904340
0009980446
0019920205
1409900636
91014300800364
9019930920"""


def _self_test() -> int:
    got = clean_text(SAMPLE_IN)
    ok = got == SAMPLE_OUT
    msg = "PASS" if ok else f"FAIL\n--- got ---\n{got!r}\n--- expected ---\n{SAMPLE_OUT!r}"
    print(msg)
    if getattr(sys, "frozen", False):
        Path(sys.executable).with_name("self_test_result.txt").write_text(
            msg + "\n", encoding="utf-8"
        )
    return 0 if ok else 1


def _file_mode(in_path: Path, out_path: Path) -> int:
    text = in_path.read_text(encoding="utf-8")
    cleaned = clean_text(text)
    out_path.write_text(cleaned, encoding="utf-8", newline="\n")
    return 0 if cleaned else 1


def _clipboard_mode() -> int:
    from app.clipboard_win import get_text, set_text

    raw = get_text()
    cleaned = clean_text(raw)
    if not cleaned:
        return 0
    set_text(cleaned)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the CDK sample fixture and exit 0/1 (no clipboard).",
    )
    parser.add_argument("--in", dest="in_path", type=Path, default=None)
    parser.add_argument("--out", dest="out_path", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.in_path or args.out_path:
        if not args.in_path or not args.out_path:
            print("--in and --out must be used together", file=sys.stderr)
            return 2
        return _file_mode(args.in_path, args.out_path)
    return _clipboard_mode()


if __name__ == "__main__":
    sys.exit(main())
