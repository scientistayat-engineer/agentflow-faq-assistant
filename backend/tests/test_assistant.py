"""Offline tests (no API key needed): run with  python -m unittest discover -s backend/tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("GROQ_API_KEY", None)  # force demo mode

from faq_assistant.agents.classifier import keyword_classify  # noqa: E402
from faq_assistant.agents.knowledge import retrieve  # noqa: E402
from faq_assistant.graph import run_assistant  # noqa: E402


class ClassifierTests(unittest.TestCase):
    def test_categories(self):
        cases = {
            "Mera refund kab tak aaye ga?": "refunds",
            "How do I track my order?": "orders",
            "My card was declined at checkout": "payments",
            "My parcel is delayed": "delivery",
            "I want to exchange this size": "returns",
            "What is the weather today?": "other",
        }
        for question, expected in cases.items():
            self.assertEqual(keyword_classify(question)[0], expected, question)


class KnowledgeTests(unittest.TestCase):
    def test_finds_right_entry(self):
        cases = {
            "How long does a refund take?": "R-04",
            "Is cash on delivery available?": "P-02",
            "How can I track my order?": "O-04",
            "What is your return policy?": "T-01",
            "Kya cash on delivery available hai?": "P-02",
        }
        for question, expected in cases.items():
            result = retrieve(question)
            self.assertTrue(result["found"], question)
            self.assertEqual(result["matches"][0]["id"], expected, question)

    def test_unknown_questions_return_nothing(self):
        for question in ["What is the weather today?", "Do you sell gift cards?", "Who won the cricket match?"]:
            self.assertFalse(retrieve(question)["found"], question)


class PipelineTests(unittest.TestCase):
    def test_answered(self):
        result = run_assistant("How long does a refund take?", use_langgraph=False)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["sources"][0]["id"], "R-04")
        self.assertEqual([s["agent"] for s in result["trace"]], ["FAQ Classifier", "Knowledge Agent", "Response Agent"])

    def test_no_answer_never_invents(self):
        result = run_assistant("Do you sell gift cards?", use_langgraph=False)
        self.assertEqual(result["status"], "no_answer")
        self.assertEqual(result["sources"], [])
        self.assertEqual(len(result["trace"]), 3)

    def test_out_of_scope_skips_knowledge(self):
        result = run_assistant("What is the weather today?", use_langgraph=False)
        self.assertEqual(result["status"], "no_answer")
        self.assertEqual(result["trace"][1]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
