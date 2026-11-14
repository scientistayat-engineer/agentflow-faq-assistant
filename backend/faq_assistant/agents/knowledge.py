"""Agent 2 - Knowledge Agent: retrieves relevant entries from the FAQ knowledge base (BM25)."""
import json
import math
from collections import Counter
from functools import lru_cache

from ..config import KB_PATH, MIN_COVERAGE, MIN_SCORE, TOP_K
from ..text import tokenize


@lru_cache(maxsize=1)
def load_faqs() -> tuple[dict, ...]:
    with open(KB_PATH, encoding="utf-8") as fh:
        return tuple(json.load(fh))


@lru_cache(maxsize=1)
def _index():
    docs = []
    for faq in load_faqs():
        tokens = (tokenize(faq["question"]) * 2 + tokenize(" ".join(faq.get("keywords", []))) * 2
                  + tokenize(faq["answer"]))
        docs.append(Counter(tokens))
    avg_len = sum(sum(d.values()) for d in docs) / len(docs)
    df = Counter(term for d in docs for term in d)
    return docs, avg_len, df


def search(question: str, category: str | None = None, k: int = TOP_K) -> list[dict]:
    """Rank FAQ entries for a question. Entries from the predicted category get a small boost."""
    query = set(tokenize(question))
    if not query:
        return []
    docs, avg_len, df = _index()
    n, k1, b = len(docs), 1.5, 0.75
    results = []
    for faq, doc in zip(load_faqs(), docs):
        length = sum(doc.values())
        score = 0.0
        for term in query:
            tf = doc.get(term, 0)
            if tf:
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / avg_len))
        coverage = sum(1 for t in query if doc.get(t)) / len(query)
        if category:
            score *= 1.25 if faq["category"] == category else 0.85
        results.append({"id": faq["id"], "category": faq["category"], "question": faq["question"],
                        "answer": faq["answer"], "score": round(score, 2), "coverage": round(coverage, 2)})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:k]


def retrieve(question: str, category: str | None = None) -> dict:
    """Return the entries that are relevant enough to answer from. Empty list means 'not in the FAQ'."""
    ranked = search(question, category)
    if not ranked or ranked[0]["coverage"] < MIN_COVERAGE or ranked[0]["score"] < MIN_SCORE:
        return {"found": False, "matches": []}
    top = ranked[0]["score"]
    matches = [r for r in ranked if r["score"] >= 0.5 * top and r["coverage"] >= MIN_COVERAGE]
    in_category = [r for r in matches if r["category"] == category]
    if in_category:  # prefer entries from the predicted category so sources stay on-topic
        matches = in_category
    return {"found": True, "matches": matches}
