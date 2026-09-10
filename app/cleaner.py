"""Strip hyphens and whitespace from CDK part-number lists."""

from __future__ import annotations

import re

_JUNK = re.compile(r"[-\s]+")


def clean_line(line: str) -> str:
    """Remove hyphens and all whitespace from one line. Keep leading zeros."""
    return _JUNK.sub("", line)


def clean_text(text: str) -> str:
    """Clean a multi-line CDK paste.

    Each non-empty line becomes digits-only (hyphens and spaces gone).
    Empty / whitespace-only / hyphen-only lines are dropped.
    Lines are joined with ``\\n`` and there is no trailing extra blank line.
    """
    if text is None:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    for line in normalized.split("\n"):
        cleaned = clean_line(line)
        if cleaned:
            out.append(cleaned)
    return "\n".join(out)
