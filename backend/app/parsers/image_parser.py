"""
Parser for image files using Gemini vision (or filename-only fallback).

Supported: .png .jpg .jpeg .gif .webp .bmp
"""

from __future__ import annotations

from app.parsers.base import BaseParser, ParsedDocument
from app.llm.gemini import GeminiClient
from config import get_settings

MIME_MAP: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


class ImageParser(BaseParser):
    source_type = "image"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ".png"
        mime = MIME_MAP.get(ext, "image/png")

        cfg = get_settings()
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

        if cfg.gemini_api_key:
            try:
                gemini = GeminiClient(cfg.gemini_api_key, cfg.gemini_model)
                description = gemini.describe_image(file_bytes, mime, filename)
            except Exception:
                description = f"[Image: {filename}] (Gemini unavailable)"
        else:
            description = f"[Image: {filename}] (No Gemini API key configured)"

        raw_text = f"=== {title} ===\n{description}"

        return ParsedDocument(
            title=title,
            raw_text=raw_text,
            source_type=self.source_type,
            metadata={
                "mime_type": mime,
                "file_size_bytes": len(file_bytes),
                "has_vision_description": bool(cfg.gemini_api_key),
            },
            sections=[{"heading": title, "text": description}],
        )
