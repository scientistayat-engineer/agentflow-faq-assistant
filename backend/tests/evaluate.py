"""Small labelled evaluation:  python backend/tests/evaluate.py  (uses the LLM if GROQ_API_KEY is set)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from faq_assistant.graph import run_assistant  # noqa: E402

IN_SCOPE = [  # (question, expected category, expected FAQ id)
    ("How do I place an order?", "orders", "O-01"),
    ("Can I cancel my order before it ships?", "orders", "O-02"),
    ("How do I change the size of an item I ordered?", "orders", "O-03"),
    ("Where is my order? I want to track it", "orders", "O-04"),
    ("I never got the confirmation email", "orders", "O-05"),
    ("Is this item back in stock?", "orders", "O-06"),
    ("Which payment methods can I use?", "payments", "P-01"),
    ("Do you offer cash on delivery?", "payments", "P-02"),
    ("My payment failed but money was deducted", "payments", "P-03"),
    ("Is paying online safe?", "payments", "P-04"),
    ("Where can I download my invoice?", "payments", "P-05"),
    ("Why was my card declined?", "payments", "P-06"),
    ("How long does delivery take?", "delivery", "D-01"),
    ("What is the delivery fee?", "delivery", "D-02"),
    ("My order is late", "delivery", "D-03"),
    ("Do you deliver to my city?", "delivery", "D-04"),
    ("My parcel arrived damaged", "delivery", "D-06"),
    ("What is your return policy?", "returns", "T-01"),
    ("How do I return an item?", "returns", "T-02"),
    ("Can I exchange for a different size?", "returns", "T-04"),
    ("I received the wrong item", "returns", "T-05"),
    ("How do I get a refund?", "refunds", "R-01"),
    ("How long does a refund take?", "refunds", "R-04"),
    ("Why haven't I received my refund yet?", "refunds", "R-05"),
    ("Where does my refund go?", "refunds", "R-07"),
    ("Mera refund kab tak aaye ga?", "refunds", "R-04"),
    ("payment fail ho gaya lekin paisa kat gaya", "payments", "P-03"),
    ("Mera order kahan hai?", "orders", "O-04"),
]
NOT_IN_FAQ = [
    "What is the weather today?", "Do you sell gift cards?", "Who won the cricket match?",
    "Can I change my delivery address after dispatch?", "Do you have a physical store in Lahore?",
    "Can you recommend a good laptop?",
]


def main() -> None:
    cat_ok = top1_ok = answered = 0
    misses = []
    for question, category, faq_id in IN_SCOPE:
        r = run_assistant(question, use_langgraph=False)
        cat_ok += r["category"] == category
        got = r["sources"][0]["id"] if r["sources"] else None
        top1_ok += got == faq_id
        answered += r["status"] == "answered"
        if r["category"] != category or got != faq_id:
            misses.append((question, r["category"], got, category, faq_id))
    refused = sum(run_assistant(q, use_langgraph=False)["status"] == "no_answer" for q in NOT_IN_FAQ)
    n, m = len(IN_SCOPE), len(NOT_IN_FAQ)
    print(f"Mode: {'LLM' if os.getenv('GROQ_API_KEY') else 'demo (keyword classifier, extractive answers)'}")
    print(f"In-scope questions: {n}")
    print(f"  Category accuracy:        {cat_ok}/{n} = {cat_ok / n:.0%}")
    print(f"  Correct FAQ ranked first: {top1_ok}/{n} = {top1_ok / n:.0%}")
    print(f"  Answered (not refused):   {answered}/{n} = {answered / n:.0%}")
    print(f"Questions not in the FAQ: {m}")
    print(f"  Correctly refused:        {refused}/{m} = {refused / m:.0%}")
    for row in misses:
        print("  MISS:", row)


if __name__ == "__main__":
    main()
