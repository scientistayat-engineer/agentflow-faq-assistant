"""Agent 3 - Response Agent: writes the customer reply, grounded only in retrieved FAQ entries."""
from ..config import SUPPORT_EMAIL, response_model
from ..llm import get_llm
from ..text import looks_like_roman_urdu

SYSTEM_PROMPT = """You are the Response Agent, a friendly customer support specialist for an online shop.
Answer the customer's question using ONLY the FAQ entries provided below.
Rules:
- Never invent policies, numbers, prices, deadlines or links that are not in the FAQ entries.
- If the entries do not directly answer the question, reply with exactly: NOT_FOUND
- Reply in the customer's language (English or Roman Urdu), in a warm, clear tone, in at most 90 words.
- Do not mention 'FAQ entries' or internal ids in your reply."""


def fallback_message(question: str) -> str:
    if looks_like_roman_urdu(question):
        return ("Mujhe is sawal ka jawab hamari FAQ mein nahi mila, is liye main andaza nahi lagaun ga. "
                f"Barah-e-meharbani hamari support team se rabta karein: {SUPPORT_EMAIL}")
    return ("I couldn't find a reliable answer to this in our FAQ, so I won't guess. "
            f"Please contact our support team at {SUPPORT_EMAIL} and a human agent will help you.")


def generate_response(question: str, matches: list[dict]) -> dict:
    """Returns {answer, grounded, method}. grounded=False means the caller should use the fallback."""
    llm = get_llm(response_model(), 0.2)
    if llm is not None:
        context = "\n\n".join(f"[{m['id']}] Q: {m['question']}\nA: {m['answer']}" for m in matches)
        try:
            reply = llm.invoke([("system", SYSTEM_PROMPT + "\n\nFAQ entries:\n" + context), ("human", question)])
            text = reply.content.strip()
            if text.upper().startswith("NOT_FOUND"):
                return {"answer": fallback_message(question), "grounded": False, "method": "llm"}
            return {"answer": text, "grounded": True, "method": "llm"}
        except Exception:
            pass  # fall through to the extractive answer
    return {"answer": matches[0]["answer"], "grounded": True, "method": "extractive"}
