"""
Fetches and parses content from shared LLM URLs.
Detects source type from URL domain, fetches HTML, and routes to the
appropriate specialised parser (ChatGPTShare, ClaudeShare, etc.).
"""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.parsers.base import ParsedDocument
from app.parsers import get_share_parser

DOMAIN_SOURCE_MAP: dict[str, str] = {
    "chatgpt.com": "chatgpt_share",
    "chat.openai.com": "chatgpt_share",
    "claude.ai": "claude_share",
}

TIMEOUT_SECONDS = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def detect_url_source(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    for domain, source_type in DOMAIN_SOURCE_MAP.items():
        if hostname.endswith(domain):
            return source_type
    return "webpage"


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    parsed = urlparse(url)
    return parsed.path.rsplit("/", 1)[-1] or parsed.hostname or "Imported Page"


def _fallback_text(soup: BeautifulSoup) -> str:
    for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        element.decompose()
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main:
        return main.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


async def import_url(url: str) -> ParsedDocument:
    source_type = detect_url_source(url)

    async with httpx.AsyncClient(follow_redirects=True, timeout=TIMEOUT_SECONDS) as client:
        resp = await client.get(url, headers=HEADERS)
        resp.raise_for_status()
        html = resp.text

    file_hash = hashlib.sha256(url.encode()).hexdigest()

    share_parser = get_share_parser(source_type)
    if share_parser is not None:
        parsed = share_parser.parse(html, url)
        parsed.metadata["url"] = url
        parsed.metadata["file_hash"] = file_hash
        return parsed

    soup = BeautifulSoup(html, "lxml")
    title = _extract_title(soup, url)
    text = _fallback_text(soup)

    if not text.strip():
        raise ValueError("No extractable text content found at the provided URL")

    return ParsedDocument(
        title=title,
        raw_text=text,
        source_type=source_type,
        metadata={
            "url": url,
            "file_hash": file_hash,
            "import_method": "url_generic",
        },
        sections=[{"heading": title, "text": text}],
    )
