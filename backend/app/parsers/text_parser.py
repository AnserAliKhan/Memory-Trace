"""
Parser for plain text (.txt) files.
"""

from app.parsers.base import BaseParser, ParsedDocument


class TxtParser(BaseParser):
    source_type = "txt"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        text = file_bytes.decode("utf-8", errors="replace")

        return ParsedDocument(
            title=filename,
            raw_text=text,
            source_type=self.source_type,
            sections=[{"heading": filename, "text": text.strip()}],
        )