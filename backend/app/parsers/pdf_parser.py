"""
Parser for PDF files using PyMuPDF (fitz).
"""

import io
from app.parsers.base import BaseParser, ParsedDocument


class PDFParser(BaseParser):
    source_type = "pdf"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        try:
            import fitz
        except ImportError:
            raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")

        doc = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")

        sections = []
        all_pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:
                sections.append({"heading": f"Page {page_num + 1}", "text": text})
                all_pages.append(text)

        doc.close()

        raw_text = "\n\n".join(all_pages)
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

        return ParsedDocument(
            title=title,
            raw_text=raw_text,
            source_type=self.source_type,
            sections=sections,
            metadata={"page_count": len(sections)},
        )