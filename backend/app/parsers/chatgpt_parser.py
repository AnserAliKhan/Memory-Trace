"""
Parser for ChatGPT conversation export JSON.
"""

import json
from app.parsers.base import BaseParser, ParsedDocument


class ChatGPTParser(BaseParser):
    source_type = "chatgpt"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        data = json.loads(file_bytes.decode("utf-8", errors="replace"))

        if not isinstance(data, list):
            data = [data]

        sections = []
        all_text_parts = []

        for conversation in data:
            title = conversation.get("title", "Untitled Conversation")
            mapping = conversation.get("mapping", {})

            messages = []
            for node in mapping.values():
                msg = node.get("message")
                if not msg:
                    continue
                role = msg.get("author", {}).get("role", "unknown")
                if role not in ("user", "assistant"):
                    continue
                parts = msg.get("content", {}).get("parts", [])
                text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
                if text:
                    messages.append(f"[{role.upper()}] {text}")

            if messages:
                section_text = "\n\n".join(messages)
                sections.append({"heading": title, "text": section_text})
                all_text_parts.append(f"=== {title} ===\n{section_text}")

        raw_text = "\n\n".join(all_text_parts)
        top_title = data[0].get("title", filename) if data else filename

        return ParsedDocument(
            title=top_title,
            raw_text=raw_text,
            source_type=self.source_type,
            sections=sections,
            metadata={"conversation_count": len(data)},
        )