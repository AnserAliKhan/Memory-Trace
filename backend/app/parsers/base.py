"""
Base types shared by all parsers.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedDocument:
    """Normalised output from any parser."""

    title: str
    raw_text: str                          # full concatenated text
    source_type: str                       # chatgpt | markdown | txt | pdf
    metadata: dict = field(default_factory=dict)
    sections: list[dict] = field(default_factory=list)
    # sections: [{"heading": str, "text": str}]


class BaseParser:
    source_type: str = "unknown"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        raise NotImplementedError