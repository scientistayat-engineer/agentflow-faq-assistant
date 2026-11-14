"""Agent 1 - FAQ Classifier: decides which support category a question belongs to."""
import json
import re

from ..config import CATEGORIES, OTHER, classifier_model
from ..llm import get_llm
from ..text import stem, tokenize

# Used when no LLM is available (demo mode) or when the LLM call fails.
# Ordered from most to least specific so ties resolve sensibly.
KEYWORDS = {
    "refunds": ["refund", "reimburse", "reimbursement", "money", "paisa", "paise"],
    "returns": ["return", "exchange", "replace", "replacement", "wrong", "pickup", "wapsi"],
    "payments": ["payment", "pay", "paid", "card", "cod", "cash", "wallet", "declined", "invoice", "receipt",
                 "charged", "transaction", "bank", "deducted", "kat"],
    "delivery": ["delivery", "deliver", "shipping", "shipment", "courier", "parcel", "package", "delayed",
                 "delay", "late", "arrive", "address", "damaged", "dispatch"],
    "orders": ["order", "cancel", "cancellation", "track", "tracking", "stock", "checkout", "cart", "confirmation"],
}
_STEMMED = {cat: {stem(w) for w in words} for cat, words in KEYWORDS.items()}

PROMPT = (
    "You are the FAQ Classifier for an online shop. Classify the customer's question into exactly one "
    f"category from: {', '.join(CATEGORIES)}, or '{OTHER}' if it is unrelated to shopping support. "
    "The question may be English or Roman Urdu. Reply with JSON only, for example "
    '{"category": "refunds", "confidence": 0.92}.'
)


def keyword_classify(question: str) -> tuple[str, float]:
    tokens = set(tokenize(question))
    best, best_hits = OTHER, 0
    for category, words in _STEMMED.items():
        hits = len(tokens & words)
        if hits > best_hits:
            best, best_hits = category, hits
    if best_hits == 0:
        return OTHER, 0.0
    return best, min(0.95, 0.55 + 0.2 * best_hits)


def _parse(raw: str) -> tuple[str, float]:
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    data = json.loads(match.group(0) if match else raw)
    category = str(data.get("category", "")).strip().lower()
    if category not in CATEGORIES + [OTHER]:
        raise ValueError(f"unknown category: {category!r}")
    confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
    return category, confidence


def classify_question(question: str) -> dict:
    llm = get_llm(classifier_model(), 0.0)
    if llm is not None:
        try:
            reply = llm.invoke([("system", PROMPT), ("human", question)])
            category, confidence = _parse(reply.content)
            return {"category": category, "confidence": round(confidence, 2), "method": "llm"}
        except Exception:  # network error, bad JSON, rate limit: fall back gracefully
            pass
    category, confidence = keyword_classify(question)
    return {"category": category, "confidence": round(confidence, 2), "method": "keywords"}
