"""
Gemini API integration.

STRICT CONTRACT:
  Gemini is ONLY used for:
    1. Synthesizing an answer from pre-retrieved memory chunks
    2. Summarizing a list of memories
    3. Generating topic labels

  Gemini NEVER performs retrieval. All retrieval is done by FAISS + reranker.
"""

from __future__ import annotations

import google.generativeai as genai

SYNTHESIS_SYSTEM = """You are a memory assistant. Your job is to help users understand information they have previously encountered.

You will be given a user question and a set of memory excerpts retrieved from their personal knowledge base. Synthesize a clear, helpful answer using ONLY the provided memories. Do not add information from outside the memories.

If the memories do not contain enough information to answer the question, say so clearly.

Always be concise and direct."""

SUMMARY_SYSTEM = """Summarize the following memory excerpts in 2-3 sentences. Focus on the key insight or solution."""

TOPICS_SYSTEM = """Given the following text, generate 3-5 short topic labels (2-4 words each) that describe what the content is about. Return only the labels, one per line."""


class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYNTHESIS_SYSTEM,
        )
        self.model_name = model_name

    def synthesize_answer(self, query: str, memory_chunks: list[dict]) -> str:
        """
        Generate an answer from retrieved memory chunks.

        memory_chunks: list of {"content": str, "source": str, "score": float}
        """
        if not memory_chunks:
            return "No relevant memories found for this query."

        context_parts = []
        for i, chunk in enumerate(memory_chunks, 1):
            source = chunk.get("source", "Unknown source")
            content = chunk.get("content", "")
            context_parts.append(f"[Memory {i}] (Source: {source})\n{content}")

        context = "\n\n---\n\n".join(context_parts)
        prompt = f"Question: {query}\n\nMemories:\n{context}\n\nAnswer:"

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def summarize_memories(self, chunks: list[str]) -> str:
        """Summarize a list of memory text chunks."""
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SUMMARY_SYSTEM,
        )
        combined = "\n\n".join(chunks[:10])  # cap to 10 chunks
        try:
            response = model.generate_content(combined)
            return response.text.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_topics(self, text: str) -> list[str]:
        """Generate topic labels for a piece of text."""
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=TOPICS_SYSTEM,
        )
        try:
            response = model.generate_content(text[:2000])
            lines = [l.strip() for l in response.text.strip().splitlines() if l.strip()]
            return lines[:5]
        except Exception:
            return []