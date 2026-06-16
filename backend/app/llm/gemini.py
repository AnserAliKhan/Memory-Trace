"""
Gemini API integration using google-genai SDK.

STRICT CONTRACT:
  Gemini is ONLY used for:
    1. Synthesizing an answer from pre-retrieved memory chunks
    2. Summarizing a list of memories
    3. Generating topic labels

  Gemini NEVER performs retrieval. All retrieval is done by FAISS + reranker.
"""
from __future__ import annotations

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


from google import genai
from google.genai import types


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
        self.client = genai.Client(api_key=api_key)        
        self.model_name = model_name

    def synthesize_answer(self, query: str, memory_chunks: list[dict]) -> str:
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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYNTHESIS_SYSTEM,
                ),
            )
            return response.text.strip()
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def summarize_memories(self, chunks: list[str]) -> str:
        combined = "\n\n".join(chunks[:10])
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=combined,
                config=types.GenerateContentConfig(
                    system_instruction=SUMMARY_SYSTEM,
                ),
            )
            return response.text.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_topics(self, text: str) -> list[str]:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text[:2000],
                config=types.GenerateContentConfig(
                    system_instruction=TOPICS_SYSTEM,
                ),
            )
            lines = [l.strip() for l in response.text.strip().splitlines() if l.strip()]
            return lines[:5]
        except Exception:
            return []