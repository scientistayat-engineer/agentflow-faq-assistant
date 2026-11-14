"""Groq LLM factory. Returns None when no API key is set so the app can run in demo mode."""
import os
from functools import lru_cache


@lru_cache(maxsize=8)
def get_llm(model: str, temperature: float = 0.0):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        return None
    return ChatGroq(model=model, temperature=temperature, api_key=api_key, timeout=20, max_retries=1)
