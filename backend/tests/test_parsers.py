"""Tests for all ReFound parsers."""

import json
import pytest
from app.parsers.chatgpt_parser import ChatGPTParser
from app.parsers.chatgpt_share_parser import ChatGPTShareParser
from app.parsers.claude_parser import ClaudeJsonParser, ClaudeShareParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.text_parser import TxtParser
from app.parsers.image_parser import ImageParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.base import ParsedDocument
from app.parsers.url_fetcher import detect_url_source


class TestChatGPTParser:
    def test_parses_single_conversation(self):
        data = json.dumps({
            "title": "Test Chat",
            "mapping": {
                "node1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["Hello"]},
                    }
                },
                "node2": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["Hi there!"]},
                    }
                },
            },
        })
        parser = ChatGPTParser()
        result = parser.parse(data.encode(), "export.json")
        assert result.source_type == "chatgpt"
        assert "Hello" in result.raw_text
        assert "Hi there!" in result.raw_text

    def test_handles_list_of_conversations(self):
        data = json.dumps([
            {"title": "Conv A", "mapping": {}},
            {"title": "Conv B", "mapping": {}},
        ])
        parser = ChatGPTParser()
        result = parser.parse(data.encode(), "export.json")
        assert result.metadata["conversation_count"] == 2

    def test_skips_non_user_assistant_roles(self):
        data = json.dumps({
            "title": "Test",
            "mapping": {
                "n1": {
                    "message": {
                        "author": {"role": "tool"},
                        "content": {"parts": ["tool output"]},
                    }
                },
                "n2": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["user query"]},
                    }
                },
            },
        })
        parser = ChatGPTParser()
        result = parser.parse(data.encode(), "export.json")
        assert "user query" in result.raw_text
        assert "tool output" not in result.raw_text


class TestChatGPTShareParser:
    def test_extracts_title_from_html(self):
        html = "<html><head><title>My Shared Chat</title></head><body></body></html>"
        parser = ChatGPTShareParser()
        result = parser.parse(html, "https://chatgpt.com/share/abc123")
        assert result.title == "My Shared Chat"
        assert result.source_type == "chatgpt_share"

    def test_parses_next_data(self):
        next_data = {
            "props": {
                "pageProps": {
                    "serverResponse": {
                        "data": {
                            "title": "Shared Chat",
                            "mapping": {
                                "root": {
                                    "message": None,
                                },
                                "msg1": {
                                    "parent": "root",
                                    "children": ["msg2"],
                                    "message": {
                                        "author": {"role": "user"},
                                        "content": {"parts": ["How does FAISS work?"]},
                                    },
                                },
                                "msg2": {
                                    "parent": "msg1",
                                    "children": [],
                                    "message": {
                                        "author": {"role": "assistant"},
                                        "content": {"parts": ["FAISS is a library for efficient similarity search..."]},
                                    },
                                },
                            },
                        }
                    }
                }
            },
        }
        html = f"<html><head><title>Test</title></head><body><script id=\"__NEXT_DATA__\" type=\"application/json\">{json.dumps(next_data)}</script></body></html>"
        parser = ChatGPTShareParser()
        result = parser.parse(html)
        assert "FAISS is a library" in result.raw_text
        assert "How does FAISS work" in result.raw_text
        assert result.metadata["method"] == "next_data"

    def test_falls_back_to_text_extraction(self):
        html = "<html><head><title>Fallback</title></head><body><main><p>Some fallback content.</p></main></body></html>"
        parser = ChatGPTShareParser()
        result = parser.parse(html, "https://chatgpt.com/share/xyz")
        assert result.metadata["method"] == "fallback"
        assert "Some fallback content" in result.raw_text


class TestClaudeJsonParser:
    def test_parses_single_conversation(self):
        data = json.dumps({
            "name": "My Claude Chat",
            "chat_messages": [
                {"sender": "human", "text": "Explain transformers"},
                {"sender": "assistant", "text": "Transformers are a neural network architecture..."},
            ],
        })
        parser = ClaudeJsonParser()
        result = parser.parse(data.encode(), "claude_export.json")
        assert result.source_type == "claude"
        assert "Explain transformers" in result.raw_text
        assert "Transformers are a neural network" in result.raw_text

    def test_groups_consecutive_same_sender(self):
        data = json.dumps({
            "name": "Test",
            "chat_messages": [
                {"sender": "human", "text": "Part 1"},
                {"sender": "human", "text": "Part 2"},
                {"sender": "assistant", "text": "Reply"},
            ],
        })
        parser = ClaudeJsonParser()
        result = parser.parse(data.encode(), "test.json")
        assert len(result.sections) == 2

    def test_handles_lists(self):
        data = json.dumps([
            {"name": "A", "chat_messages": []},
            {"name": "B", "chat_messages": []},
        ])
        parser = ClaudeJsonParser()
        result = parser.parse(data.encode(), "list.json")
        assert result.metadata["conversation_count"] == 2


class TestClaudeShareParser:
    def test_extracts_title_from_meta(self):
        html = '<html><head><meta property="og:title" content="Claude Shared Chat"></head><body></body></html>'
        parser = ClaudeShareParser()
        result = parser.parse(html, "https://claude.ai/share/test")
        assert result.title == "Claude Shared Chat"

    def test_extracts_from_testid_attrs(self):
        html = """
        <html><body>
            <div data-testid="user-message">Human message here</div>
            <div class="assistant">AI response text</div>
        </body></html>
        """
        parser = ClaudeShareParser()
        result = parser.parse(html, "https://claude.ai/share/test")
        assert "Human message here" in result.raw_text

    def test_falls_back_to_body_text(self):
        html = "<html><body><main><p>Just some content.</p></main></body></html>"
        parser = ClaudeShareParser()
        result = parser.parse(html, "https://claude.ai/share/test")
        assert "Just some content" in result.raw_text


class TestMarkdownParser:
    def test_parses_headings(self):
        md = b"# Title\n\nSome content.\n\n## Section 1\n\nMore content."
        parser = MarkdownParser()
        result = parser.parse(md, "test.md")
        assert result.title == "Title"
        assert len(result.sections) >= 1
        assert result.source_type == "markdown"


class TestTextParser:
    def test_parses_plain_text(self):
        parser = TxtParser()
        result = parser.parse(b"Hello world", "test.txt")
        assert result.raw_text == "Hello world"
        assert result.source_type == "txt"
        assert result.title == "test.txt"


class TestImageParser:
    def test_fallback_without_api_key(self, monkeypatch):
        from config import Settings
        monkeypatch.setattr(Settings, "gemini_api_key", "")
        parser = ImageParser()
        result = parser.parse(b"fake-image-bytes", "photo.png")
        assert "[Image: photo.png]" in result.raw_text
        assert result.source_type == "image"
        assert result.metadata["has_vision_description"] is False

    def test_detects_mime_from_extension(self, monkeypatch):
        from config import Settings
        monkeypatch.setattr(Settings, "gemini_api_key", "")
        parser = ImageParser()
        result = parser.parse(b"data", "screenshot.jpeg")
        assert result.metadata["mime_type"] == "image/jpeg"


class TestUrlFetcher:
    def test_detects_chatgpt_domain(self):
        assert detect_url_source("https://chatgpt.com/share/abc") == "chatgpt_share"
        assert detect_url_source("https://chat.openai.com/share/xyz") == "chatgpt_share"

    def test_detects_claude_domain(self):
        assert detect_url_source("https://claude.ai/share/test-123") == "claude_share"
        assert detect_url_source("https://claude.ai/share/something/else") == "claude_share"

    def test_falls_back_to_webpage(self):
        assert detect_url_source("https://example.com/article") == "webpage"
        assert detect_url_source("https://google.com") == "webpage"


class TestPdfParser:
    def test_requires_pymupdf(self):
        parser = PDFParser()
        try:
            import fitz
            data = fitz.open()
            page = data.new_page()
            pdf_bytes = data.tobytes()
            data.close()
            result = parser.parse(pdf_bytes, "test.pdf")
            assert result.source_type == "pdf"
            assert result.title == "test"
        except ImportError:
            result = parser.parse(b"%PDF-1.4 empty", "test.pdf")
            assert result is not None
