from pathlib import Path

from app.cleaner import clean_line, clean_text
from app.main import SAMPLE_IN, SAMPLE_OUT, main

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_sample_from_spec():
    assert clean_text(SAMPLE_IN) == SAMPLE_OUT


def test_fixture_files():
    raw = (FIXTURE_DIR / "cdk_sample.txt").read_text(encoding="utf-8")
    expected = (FIXTURE_DIR / "cdk_sample_clean.txt").read_text(encoding="utf-8")
    assert clean_text(raw) == expected.rstrip("\n")


def test_crlf_input():
    crlf = SAMPLE_IN.replace("\n", "\r\n")
    assert clean_text(crlf) == SAMPLE_OUT


def test_leading_zeros_kept():
    assert clean_line("   006-990-43-40") == "0069904340"
    assert clean_line("   000-998-04-46") == "0009980446"


def test_already_clean_long_number():
    assert clean_line("910143-008003-64") == "91014300800364"


def test_empty_and_junk_lines_dropped():
    text = "906-697-60-98-64\n\n   \n---\n901-993-09-20\n"
    assert clean_text(text) == "906697609864\n9019930920"


def test_idempotent():
    once = clean_text(SAMPLE_IN)
    assert clean_text(once) == once


def test_self_test_exit_zero(capsys):
    assert main(["--self-test"]) == 0
    assert capsys.readouterr().out.strip() == "PASS"


def test_file_mode(tmp_path):
    src = tmp_path / "in.txt"
    dst = tmp_path / "out.txt"
    src.write_text(SAMPLE_IN, encoding="utf-8")
    assert main(["--in", str(src), "--out", str(dst)]) == 0
    assert dst.read_text(encoding="utf-8") == SAMPLE_OUT
