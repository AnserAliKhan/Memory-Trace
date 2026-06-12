"""
Text cleaning utilities applied before chunking.
"""

import re


def clean_text(text: str) -> str:
    """
    Normalize whitespace, remove control characters, and strip boilerplate.
    Preserves sentence structure.
    """
    if not text:
        return ""

    # Remove null bytes and other control chars (keep \n \t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse runs of 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse runs of spaces/tabs within a line
    text = re.sub(r"[ \t]+", " ", text)

    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()