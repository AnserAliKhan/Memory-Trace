"""Tests for GeminiClient and related utilities."""

import pytest
from unittest.mock import MagicMock, patch
from app.llm.gemini import GeminiClient, SYNTHESIS_SYSTEM


class TestGeminiClient:
    def test_init_requires_api_key(self):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiClient("")

    def test_synthesize_empty_chunks_returns_no_results(self):
        client = GeminiClient("fake-key")
        result = client.synthesize_answer("query", [])
        assert "No relevant memories" in result

    def test_synthesize_calls_gemini(self):
        client = GeminiClient("fake-key")
        mock_response = MagicMock()
        mock_response.text = "Synthesized answer."

        with patch.object(client.client.models, "generate_content", return_value=mock_response):
            result = client.synthesize_answer(
                "What is Python?",
                [{"source": "notes.md", "content": "Python is a programming language."}],
            )
            assert "Synthesized answer" in result

    def test_synthesize_handles_error(self):
        client = GeminiClient("fake-key")
        with patch.object(
            client.client.models,
            "generate_content",
            side_effect=Exception("API error"),
        ):
            result = client.synthesize_answer(
                "query",
                [{"source": "test", "content": "data"}],
            )
            assert "Error generating answer" in result

    def test_summarize_memories(self):
        client = GeminiClient("fake-key")
        mock_response = MagicMock()
        mock_response.text = "A summary."

        with patch.object(client.client.models, "generate_content", return_value=mock_response):
            result = client.summarize_memories(["chunk1", "chunk2"])
            assert result == "A summary."

    def test_generate_topics(self):
        client = GeminiClient("fake-key")
        mock_response = MagicMock()
        mock_response.text = "Topic 1\nTopic 2\nTopic 3"

        with patch.object(client.client.models, "generate_content", return_value=mock_response):
            result = client.generate_topics("some text content")
            assert result == ["Topic 1", "Topic 2", "Topic 3"]

    def test_topics_handles_error(self):
        client = GeminiClient("fake-key")
        with patch.object(
            client.client.models,
            "generate_content",
            side_effect=Exception("fail"),
        ):
            result = client.generate_topics("text")
            assert result == []

    def test_describe_image_calls_gemini(self):
        client = GeminiClient("fake-key")
        mock_response = MagicMock()
        mock_response.text = "A cat sitting on a windowsill."

        with patch.object(client.client.models, "generate_content", return_value=mock_response):
            result = client.describe_image(b"fakebytes", "image/png", "cat.png")
            assert "cat sitting" in result.lower()

    def test_describe_image_handles_error(self):
        client = GeminiClient("fake-key")
        with patch.object(
            client.client.models,
            "generate_content",
            side_effect=Exception("Vision error"),
        ):
            result = client.describe_image(b"bytes", "image/png", "test.png")
            assert "Error describing image" in result

    def test_synthesize_stream_yields_tokens(self):
        client = GeminiClient("fake-key")

        class MockChunk:
            def __init__(self, text):
                self.text = text

        mock_stream = iter([MockChunk("Hello "), MockChunk("world.")])

        with patch.object(client.client.models, "generate_content_stream", return_value=mock_stream):
            tokens = list(
                client.synthesize_answer_stream(
                    "query",
                    [{"source": "test", "content": "data"}],
                )
            )
            assert tokens == ["Hello ", "world."]

    def test_synthesize_stream_empty_chunks(self):
        client = GeminiClient("fake-key")
        tokens = list(client.synthesize_answer_stream("query", []))
        assert "No relevant memories" in tokens[0]

    def test_synthesize_stream_error(self):
        client = GeminiClient("fake-key")
        with patch.object(
            client.client.models,
            "generate_content_stream",
            side_effect=Exception("Stream error"),
        ):
            tokens = list(
                client.synthesize_answer_stream(
                    "query",
                    [{"source": "test", "content": "data"}],
                )
            )
            assert "Error generating answer" in tokens[0]
