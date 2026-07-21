"""
Parser for ChatGPT shared conversation pages (chatgpt.com/share/xxx).

Extracts embedded __NEXT_DATA__ JSON to recover the full conversation
structure with roles, then normalises into ParsedDocument.
"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from app.parsers.base import ParsedDocument


class ChatGPTShareParser:
    """Parses a ChatGPT shared page's HTML into a structured ParsedDocument."""

    source_type = "chatgpt_share"

    def parse(self, html: str, url: str = "") -> ParsedDocument:
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_title(soup, url)
        sections = self._extract_conversation(soup)

        if not sections:
            body_text = self._fallback_text(soup)
            return ParsedDocument(
                title=title,
                raw_text=body_text,
                source_type=self.source_type,
                metadata={"url": url, "method": "fallback"},
                sections=[{"heading": title, "text": body_text}],
            )

        raw_text = self._sections_to_text(title, sections)
        return ParsedDocument(
            title=title,
            raw_text=raw_text,
            source_type=self.source_type,
            metadata={"url": url, "method": "next_data", "message_count": len(sections)},
            sections=sections,
        )

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title and title != "ChatGPT":
                return title

        meta = soup.find("meta", property="og:title")
        if meta and meta.get("content"):
            content = meta["content"].strip()
            if content != "ChatGPT":
                return content

        return url.rsplit("/", 1)[-1] or "ChatGPT Conversation"

    def _extract_conversation(self, soup: BeautifulSoup) -> list[dict]:
        next_data = self._find_next_data(soup)
        if not next_data:
            return []

        mapping = self._navigate_mapping(next_data)
        if not mapping or not isinstance(mapping, dict):
            return []

        return self._build_conversation(mapping)

    def _find_next_data(self, soup: BeautifulSoup) -> dict | None:
        tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
        if not tag or not tag.string:
            return None
        try:
            return json.loads(tag.string)
        except (json.JSONDecodeError, TypeError):
            return None

    def _navigate_mapping(self, data: dict) -> dict | None:
        page_props = data.get("props", {}).get("pageProps", {})
        if isinstance(page_props, dict):
            for key in ("serverResponse", "sharedConversation"):
                blob = page_props.get(key, {})
                if isinstance(blob, dict):
                    inner = blob.get("data", blob)
                    if isinstance(inner, dict):
                        mapping = inner.get("mapping")
                        if mapping:
                            return mapping
            mapping = page_props.get("mapping")
            if mapping:
                return mapping
        return None

    def _build_conversation(self, mapping: dict) -> list[dict]:
        root_id = self._find_root_id(mapping)
        if not root_id:
            return self._all_messages_flat(mapping)

        ordered = self._walk_tree(mapping, root_id)
        if not ordered:
            return self._all_messages_flat(mapping)

        sections: list[dict] = []
        current_speaker = None
        current_parts: list[str] = []

        for msg in ordered:
            role = msg.get("role", "unknown")
            speaker = msg.get("speaker", role)
            text = msg.get("text", "").strip()
            if not text:
                continue

            if current_speaker == speaker:
                current_parts.append(text)
            else:
                if current_parts:
                    sections.append({
                        "heading": f"{current_speaker.upper()} — {self._truncate(current_parts[0], 60)}",
                        "text": f"[{current_speaker.upper()}]\n" + "\n".join(current_parts),
                    })
                current_speaker = speaker
                current_parts = [text]

        if current_parts:
            sections.append({
                "heading": f"{current_speaker.upper()} — {self._truncate(current_parts[0], 60)}",
                "text": f"[{current_speaker.upper()}]\n" + "\n".join(current_parts),
            })

        return sections

    def _all_messages_flat(self, mapping: dict) -> list[dict]:
        messages: list[dict] = []
        for node in mapping.values():
            if not isinstance(node, dict):
                continue
            msg = node.get("message")
            if not isinstance(msg, dict):
                continue
            role = msg.get("author", {})
            if isinstance(role, dict):
                role = role.get("role", "unknown")
            content = msg.get("content", {})
            parts = content.get("parts", []) if isinstance(content, dict) else []
            text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
            if text:
                messages.append({
                    "role": role,
                    "speaker": role,
                    "text": text,
                })
        return self._to_sections(messages)

    def _find_root_id(self, mapping: dict) -> str | None:
        for node_id, node in mapping.items():
            if isinstance(node, dict):
                parent = node.get("parent")
                if parent is None:
                    return node_id
        return None

    def _walk_tree(self, mapping: dict, start_id: str) -> list[dict]:
        seen: set[str] = set()
        ordered: list[dict] = []
        stack = [start_id]

        while stack:
            node_id = stack.pop()
            if node_id in seen:
                continue
            seen.add(node_id)

            node = mapping.get(node_id)
            if not isinstance(node, dict):
                continue

            msg = node.get("message")
            if isinstance(msg, dict):
                role = msg.get("author", {})
                speaker = role.get("role", "unknown") if isinstance(role, dict) else str(role)
                content = msg.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
                if text:
                    ordered.append({
                        "role": speaker,
                        "speaker": speaker,
                        "text": text,
                    })

            children = node.get("children", [])
            for child_id in reversed(children):
                if child_id not in seen:
                    stack.append(child_id)

        return ordered

    def _to_sections(self, messages: list[dict]) -> list[dict]:
        sections = []
        for i, msg in enumerate(messages):
            role = msg["role"]
            text = msg["text"]
            sections.append({
                "heading": f"{role.upper()} #{i + 1} — {self._truncate(text, 60)}",
                "text": f"[{role.upper()}]\n{text}",
            })
        return sections

    def _sections_to_text(self, title: str, sections: list[dict]) -> str:
        parts = [f"=== {title} ==="]
        for s in sections:
            parts.append(s["text"])
        return "\n\n".join(parts)

    def _fallback_text(self, soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        conversation_divs = soup.find_all(
            "div", attrs={"data-message-author-role": True}
        )
        if conversation_divs:
            parts = []
            for div in conversation_divs:
                role = div.get("data-message-author-role", "unknown")
                text = div.get_text(separator=" ", strip=True)
                if text:
                    parts.append(f"[{role.upper()}] {text}")
            return "\n\n".join(parts)

        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            return main.get_text(separator="\n", strip=True)
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        clean = re.sub(r"\s+", " ", text).strip()
        if len(clean) <= max_len:
            return clean
        return clean[: max_len - 1] + "…"
