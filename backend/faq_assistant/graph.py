"""LangGraph pipeline: classifier -> knowledge -> response, with a no-guessing fallback branch."""
import operator
import sys
import time
from functools import lru_cache
from typing import Annotated, TypedDict

from .agents.classifier import classify_question
from .agents.knowledge import retrieve
from .agents.responder import fallback_message, generate_response
from .config import CATEGORIES

CLASSIFIER, KNOWLEDGE, RESPONSE = "FAQ Classifier", "Knowledge Agent", "Response Agent"


class AssistantState(TypedDict, total=False):
    question: str
    category: str
    confidence: float
    found: bool
    matches: list
    answer: str
    status: str  # "answered" | "no_answer"
    trace: Annotated[list, operator.add]  # each agent appends its own step


def _step(agent: str, status: str, summary: str, started: float | None = None, **extra) -> dict:
    ms = round((time.perf_counter() - started) * 1000) if started else 0
    return {"agent": agent, "status": status, "summary": summary, "duration_ms": ms, **extra}


def classifier_node(state: AssistantState) -> dict:
    t = time.perf_counter()
    result = classify_question(state["question"])
    summary = f"{result['category'].title()} ({round(result['confidence'] * 100)}% confidence)"
    return {"category": result["category"], "confidence": result["confidence"],
            "trace": [_step(CLASSIFIER, "done", summary, t, method=result["method"])]}


def knowledge_node(state: AssistantState) -> dict:
    t = time.perf_counter()
    result = retrieve(state["question"], state.get("category"))
    count = len(result["matches"])
    summary = f"{count} FAQ entr{'y' if count == 1 else 'ies'} found" if result["found"] else "No relevant FAQ entry found"
    return {"found": result["found"], "matches": result["matches"],
            "trace": [_step(KNOWLEDGE, "done" if result["found"] else "no_match", summary, t)]}


def response_node(state: AssistantState) -> dict:
    t = time.perf_counter()
    result = generate_response(state["question"], state["matches"])
    if not result["grounded"]:  # the LLM judged the FAQ entries insufficient: refuse to guess
        return {"answer": result["answer"], "status": "no_answer", "matches": [],
                "trace": [_step(RESPONSE, "fallback", "FAQ did not answer the question", t)]}
    return {"answer": result["answer"], "status": "answered",
            "trace": [_step(RESPONSE, "done", "Grounded reply ready", t, method=result["method"])]}


def fallback_node(state: AssistantState) -> dict:
    steps = []
    done = {s["agent"] for s in state.get("trace", [])}
    if KNOWLEDGE not in done:
        steps.append(_step(KNOWLEDGE, "skipped", "Question is outside shopping support"))
    steps.append(_step(RESPONSE, "fallback", "Safe fallback used, nothing invented"))
    return {"answer": fallback_message(state["question"]), "status": "no_answer", "matches": [], "trace": steps}


def route_after_classifier(state: AssistantState) -> str:
    return "knowledge" if state["category"] in CATEGORIES else "fallback"


def route_after_knowledge(state: AssistantState) -> str:
    return "response" if state["found"] else "fallback"


def build_graph():
    from langgraph.graph import END, StateGraph

    graph = StateGraph(AssistantState)
    graph.add_node("classifier", classifier_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("response", response_node)
    graph.add_node("fallback", fallback_node)
    graph.set_entry_point("classifier")
    graph.add_conditional_edges("classifier", route_after_classifier, {"knowledge": "knowledge", "fallback": "fallback"})
    graph.add_conditional_edges("knowledge", route_after_knowledge, {"response": "response", "fallback": "fallback"})
    graph.add_edge("response", END)
    graph.add_edge("fallback", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()


def _run_sequential(state: AssistantState) -> AssistantState:
    """Same nodes and routing as the graph, used for tests or when langgraph is not installed."""
    def apply(update):
        state.update({k: v for k, v in update.items() if k != "trace"})
        state["trace"] = state.get("trace", []) + update.get("trace", [])
    apply(classifier_node(state))
    if route_after_classifier(state) == "fallback":
        apply(fallback_node(state))
        return state
    apply(knowledge_node(state))
    apply(response_node(state) if route_after_knowledge(state) == "response" else fallback_node(state))
    return state


def run_assistant(question: str, use_langgraph: bool = True) -> dict:
    initial: AssistantState = {"question": question, "trace": []}
    graph = None
    if use_langgraph:
        try:
            graph = get_graph()
        except ImportError:  # langgraph not installed: run the same nodes sequentially
            print("warning: langgraph is not installed, running nodes sequentially", file=sys.stderr)
    final = graph.invoke(initial) if graph else _run_sequential(initial)
    sources = [{"id": m["id"], "category": m["category"], "question": m["question"], "score": m["score"]}
               for m in final.get("matches", [])]
    return {"question": question, "category": final.get("category"), "confidence": final.get("confidence"),
            "status": final["status"], "answer": final["answer"], "sources": sources, "trace": final["trace"]}
