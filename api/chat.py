"""Vercel serverless endpoint:  POST /api/chat  {"question": "..."}"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from faq_assistant.graph import run_assistant  # noqa: E402

MAX_QUESTION_LENGTH = 500


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", os.getenv("ALLOWED_ORIGIN", "*"))
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"error": "Request body must be valid JSON."})
        question = str(body.get("question", "")).strip()
        if not question:
            return self._send(400, {"error": "Please provide a question."})
        if len(question) > MAX_QUESTION_LENGTH:
            return self._send(400, {"error": f"Question must be under {MAX_QUESTION_LENGTH} characters."})
        try:
            self._send(200, run_assistant(question))
        except Exception as exc:  # never leak internals to the browser
            print(f"assistant error: {exc!r}", file=sys.stderr)
            self._send(500, {"error": "The assistant is temporarily unavailable. Please try again."})
