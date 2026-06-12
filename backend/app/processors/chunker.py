"""
Text chunking with sliding window.

Strategy:
  - Split by sentences (simple period/newline heuristic)
  - Accumulate sentences into chunks up to `chunk_size` characters
  - Overlap last `chunk_overlap` characters between consecutive chunks
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from parsers.base import ParsedDocument
from processors.cleaner import clean_text
from config import get_settings


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    token_count: int
    metadata: dict


def _split_sentences(text: str) -> list[str]:
    """Rough sentence splitter that keeps newlines as boundaries too."""
    # Split on sentence-ending punctuation or double newlines
    parts = re.split(r"(?<=[.!?])\s+|\n\n+", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_document(parsed: ParsedDocument) -> list[TextChunk]:
    """
    Produce overlapping chunks from a ParsedDocument.
    Sections are respected: chunks do not cross section boundaries.
    """
    cfg = get_settings()
    chunk_size = cfg.chunk_size
    overlap = cfg.chunk_overlap

    chunks: list[TextChunk] = []
    chunk_index = 0

    sources = parsed.sections if parsed.sections else [
        {"heading": parsed.title, "text": parsed.raw_text}
    ]

    for section in sources:
        text = clean_text(section.get("text", ""))
        if not text:
            continue

        sentences = _split_sentences(text)
        current = ""

        for sentence in sentences:
            candidate = (current + " " + sentence).strip() if current else sentence

            if len(candidate) <= chunk_size:
                current = candidate
            else:
                # Emit current chunk
                if current:
                    chunks.append(
                        TextChunk(
                            content=current,
                            chunk_index=chunk_index,
                            token_count=_approx_tokens(current),
                            metadata={"section": section.get("heading", "")},
                        )
                    )
                    chunk_index += 1

                    # Start next chunk with overlap from end of current
                    overlap_text = current[-overlap:] if overlap else ""
                    current = (overlap_text + " " + sentence).strip()
                else:
                    # Single sentence longer than chunk_size — emit as-is
                    chunks.append(
                        TextChunk(
                            content=sentence,
                            chunk_index=chunk_index,
                            token_count=_approx_tokens(sentence),
                            metadata={"section": section.get("heading", "")},
                        )
                    )
                    chunk_index += 1
                    current = ""

        # Emit remaining text
        if current:
            chunks.append(
                TextChunk(
                    content=current,
                    chunk_index=chunk_index,
                    token_count=_approx_tokens(current),
                    metadata={"section": section.get("heading", "")},
                )
            )
            chunk_index += 1

    return chunks


def _approx_tokens(text: str) -> int:
    """Approximate token count (words / 0.75)."""
    words = len(text.split())
    return max(1, int(words / 0.75))