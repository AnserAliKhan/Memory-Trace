"""
Parser for Markdown files.
Extracts headings as section boundaries.
"""

import re
from parsers.base import BaseParser, ParsedDocument


class MarkdownParser(BaseParser):
    source_type = "markdown"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        text = file_bytes.decode("utf-8", errors="replace")

        # Split on headings (# / ## / ###)
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        sections = []
        if not matches:
            sections = [{"heading": filename, "text": text.strip()}]
        else:
            for i, match in enumerate(matches):
                heading_text = match.group(2).strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                body = text[start:end].strip()
                if body:
                    sections.append({"heading": heading_text, "text": body})

        # Derive title from first H1 or filename
        first_h1 = next(
            (m.group(2) for m in matches if m.group(1) == "#"), None
        )
        title = first_h1 or filename

        return ParsedDocument(
            title=title,
            raw_text=text,
            source_type=self.source_type,
            sections=sections,
        )