"""Tiny text utilities shared by the classifier and the knowledge agent."""
import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "do", "does", "did", "i", "my", "me", "we",
    "you", "your", "it", "its", "to", "of", "in", "on", "for", "and", "or", "if", "can", "how", "what",
    "when", "where", "why", "which", "will", "would", "should", "could", "this", "that", "with", "at",
    "by", "from", "have", "has", "had", "not", "no", "yes", "please", "get", "there", "any", "about",
    # Roman Urdu filler words
    "mera", "meri", "mere", "ka", "ki", "ke", "ko", "kya", "hai", "hain", "ho", "hoga", "se",
    "me", "mein", "tak", "aap", "ap", "hum", "ga", "gi", "aye", "aaye", "ayega", "karo", "karna",
    "kaise", "kese", "kia", "to", "bhi", "ye", "yeh", "wo", "woh", "par", "pe", "nahi", "nai",
}

ROMAN_URDU_HINTS = {
    "mera", "meri", "mere", "kab", "kya", "hai", "hain", "nahi", "mein", "aap", "kaise", "karo",
    "karna", "paisa", "wapas", "chahiye", "kahan", "kyun", "abhi", "bhi", "ka", "ki", "ko", "se",
}


def stem(word: str) -> str:
    """Very light stemmer so 'refunds' matches 'refund' and 'delivered' matches 'deliver'."""
    for suffix, extra in (("ing", 2), ("ed", 3), ("es", 3), ("s", 3)):
        if len(word) > len(suffix) + extra and word.endswith(suffix) and not word.endswith("ss"):
            return word[: -len(suffix)]
    return word


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    if not keep_stopwords:
        words = [w for w in words if w not in STOPWORDS]
    return [stem(w) for w in words]


def looks_like_roman_urdu(text: str) -> bool:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return len(words & ROMAN_URDU_HINTS) >= 2
