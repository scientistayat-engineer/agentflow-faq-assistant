"""Central configuration. Everything tunable lives here or in environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KB_PATH = BASE_DIR / "knowledge_base" / "faqs.json"

CATEGORIES = ["orders", "payments", "delivery", "returns", "refunds"]
OTHER = "other"

# Retrieval thresholds: below these the Knowledge Agent reports "nothing found".
MIN_COVERAGE = 0.5   # share of the question's keywords that the FAQ entry covers
MIN_SCORE = 1.0      # minimum BM25 relevance score
TOP_K = 3

SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@shopease.example")


def classifier_model() -> str:
    return os.getenv("CLASSIFIER_MODEL", "llama-3.1-8b-instant")


def response_model() -> str:
    return os.getenv("RESPONSE_MODEL", "llama-3.3-70b-versatile")
