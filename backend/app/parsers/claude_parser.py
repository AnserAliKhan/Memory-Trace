"""
Parser for Claude conversations — both JSON exports and shared links.

JSON export format (downloaded from Claude):
  {"chat_messages": [{"sender": "human"|"assistant", "text": "..."}], "name": "..."}

Shared links (claude.ai/share/xxx):
  Extracts conversation from the rendered HTML DOM.
"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from app.parsers.base import BaseParser, ParsedDocument


class ClaudeJsonParser(BaseParser):
    """Parses a Claude JSON export file."""

    source_type = "claude"

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        data = json.loads(file_bytes.decode("utf-8", errors="replace"))

        if isinstance(data, list):
            conversations = data
        else:
            conversations = [data]

        all_sections: list[dict] = []
        all_text: list[str] = []

        for conv in conversations:
            name = conv.get("name") or conv.get("title") or "Claude Conversation"
            messages = conv.get("chat_messages", [])

            current_speaker = None
            current_parts: list[str] = []
            conv_sections: list[dict] = []

            for msg in messages:
                sender = msg.get("sender", "unknown")
                text = msg.get("text", "").strip()
                if not text:
                    continue

                if current_speaker == sender:
                    current_parts.append(text)
                else:
                    if current_parts:
                        conv_sections.append(_make_section(current_speaker, current_parts))
                    current_speaker = sender
                    current_parts = [text]

            if current_parts:
                conv_sections.append(_make_section(current_speaker, current_parts))

            conv_text = _sections_to_text(name, conv_sections)
            all_text.append(conv_text)
            all_sections.extend(conv_sections)

        title = conversations[0].get("name") or filename
        raw_text = "\n\n".join(all_text)

        return ParsedDocument(
            title=title,
            raw_text=raw_text,
            source_type=self.source_type,
            sections=all_sections,
            metadata={"conversation_count": len(conversations)},
        )


class ClaudeShareParser:
    """Parses a Claude shared conversation page (claude.ai/share/xxx)."""

    source_type = "claude_share"

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

        raw_text = _sections_to_text(title, sections)
        return ParsedDocument(
            title=title,
            raw_text=raw_text,
            source_type=self.source_type,
            metadata={"url": url, "method": "dom_extraction", "message_count": len(sections)},
            sections=sections,
        )

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        meta = soup.find("meta", property="og:title")
        if meta and meta.get("content"):
            content = meta["content"].strip()
            if content:
                return content
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return url.rsplit("/", 1)[-1] or "Claude Conversation"

    def _extract_conversation(self, soup: BeautifulSoup) -> list[dict]:
        messages = self._extract_from_attrs(soup)
        if messages:
            return _group_into_sections(messages)

        messages = self._extract_from_classes(soup)
        if messages:
            return _group_into_sections(messages)

        return []

    def _extract_from_attrs(self, soup: BeautifulSoup) -> list[dict]:
        human_msgs = soup.find_all(attrs={"data-testid": "user-message"})
        assistant_msgs = soup.find_all(attrs={"data-test-render-count": True})

        if not human_msgs:
            human_divs = soup.select('[class*="human"]')
            assistant_divs = soup.select('[class*="assistant"]')
        else:
            human_divs = human_msgs
            assistant_divs = assistant_msgs if assistant_msgs else soup.select('[class*="assistant"]')

        if not human_divs and not assistant_divs:
            return []

        tagged: list[tuple[str, str]] = []
        for div in human_divs:
            text = div.get_text(separator=" ", strip=True)
            if text:
                tagged.append(("human", text))
        for div in assistant_divs:
            text = div.get_text(separator=" ", strip=True)
            if text:
                tagged.append(("assistant", text))

        if not tagged:
            return []

        sorted_msgs = self._sort_by_dom_order(soup, tagged)
        return [{"role": role, "speaker": role, "text": text} for role, text in sorted_msgs]

    def _extract_from_classes(self, soup: BeautifulSoup) -> list[dict]:
        text_blocks = soup.find_all(
            ["p", "div", "span"],
            string=lambda s: s and len(s.strip()) > 30 if s else False,
        )
        if not text_blocks:
            return []

        seen = set()
        messages: list[dict] = []
        for block in text_blocks:
            text = block.get_text(strip=True)
            if text and text not in seen:
                seen.add(text)
                parent = block.find_parent(attrs={"data-testid": True})
                role = "assistant" if parent and "assistant" in str(parent.get("data-testid", "")).lower() else "human"
                messages.append({"role": role, "speaker": role, "text": text})
        return messages

    def _sort_by_dom_order(self, soup, tagged: list[tuple[str, str]]) -> list[tuple[str, str]]:
        body = soup.find("body")
        if not body:
            return tagged

        body_text = body.get_text()
        positions = []
        for role, text in tagged:
            idx = body_text.find(text)
            positions.append((idx if idx >= 0 else 999999, role, text))
        positions.sort(key=lambda x: x[0])
        return [(role, text) for _, role, text in positions]

    def _fallback_text(self, soup: BeautifulSoup) -> str:
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            return main.get_text(separator="\n", strip=True)
        return soup.get_text(separator="\n", strip=True)


def _make_section(speaker: str, parts: list[str]) -> dict:
    text = "[{}]\n{}".format(speaker.upper(), "\n".join(parts))
    heading = "{} — {}".format(
        speaker.upper(),
        _truncate(re.sub(r"\s+", " ", parts[0]), 60),
    )
    return {"heading": heading, "text": text}


def _group_into_sections(messages: list[dict]) -> list[dict]:
    sections: list[dict] = []
    current_speaker = None
    current_parts: list[str] = []

    for msg in messages:
        role = msg.get("role", "unknown")
        speaker = msg.get("speaker", role)
        text = msg.get("text", "").strip()
        if not text:
            continue

        if current_speaker == speaker:
            current_parts.append(text)
        else:
            if current_parts:
                sections.append(_make_section(current_speaker, current_parts))
            current_speaker = speaker
            current_parts = [text]

    if current_parts:
        sections.append(_make_section(current_speaker, current_parts))
    return sections


def _sections_to_text(title: str, sections: list[dict]) -> str:
    parts = ["=== {} ===".format(title)]
    for s in sections:
        parts.append(s["text"])
    return "\n\n".join(parts)


def _truncate(text: str, max_len: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 1] + "…"
