"""
Fetches and parses content from shared LLM URLs.
Detects source type from URL domain, fetches HTML, extracts text.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse
from html.parser import HTMLParser

import httpx
from bs4 import BeautifulSoup

from app.parsers.base import ParsedDocument

DOMAIN_SOURCE_MAP: dict[str, str] = {
    "chatgpt.com": "chatgpt_share",
    "chat.openai.com": "chatgpt_share",
    "claude.ai": "claude_share",
}

TIMEOUT_SECONDS = 15


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag in ("script", "style", "noscript", "svg"):
            self._skip = True

    def handle_endtag(self, tag: str):
        if tag in ("script", "style", "noscript", "svg"):
            self._skip = False
        if tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "div"):
            self.parts.append("\n")

    def handle_data(self, data: str):
        if not self._skip:
            text = data.strip()
            if text:
                self.parts.append(text + " ")

    def get_text(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r" {2,}", " ", raw)
        return raw.strip()


def detect_url_source(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    for domain, source_type in DOMAIN_SOURCE_MAP.items():
        if hostname.endswith(domain):
            return source_type
    return "webpage"


def extract_title(soup: BeautifulSoup, url: str) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    parsed = urlparse(url)
    return parsed.path.rsplit("/", 1)[-1] or parsed.hostname or "Imported Page"


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        element.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main:
        return main.get_text(separator="\n", strip=True)

    extractor = _TextExtractor()
    extractor.feed(html)
    text = extractor.get_text()
    return text or soup.get_text(separator="\n", strip=True)


async def fetch_url(url: str) -> tuple[str, str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=TIMEOUT_SECONDS) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "lxml")
    title = extract_title(soup, url)
    text = extract_text_from_html(html)
    source_type = detect_url_source(url)

    return text, title, source_type


async def import_url(url: str) -> ParsedDocument:
    text, title, source_type = await fetch_url(url)
    file_hash = hashlib.sha256(url.encode()).hexdigest()

    if not text.strip():
        raise ValueError("No extractable text content found at the provided URL")

    return ParsedDocument(
        title=title,
        raw_text=text,
        source_type=source_type,
        metadata={
            "url": url,
            "file_hash": file_hash,
            "import_method": "url",
        },
        sections=[{"heading": title, "text": text}],
    )
