"""Vercel serverless endpoint:  GET /api/faqs  (read-only list for the Knowledge Base page)"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from faq_assistant.agents.knowledge import load_faqs  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        items = [{k: f[k] for k in ("id", "category", "question", "answer")} for f in load_faqs()]
        body = json.dumps(items, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(body)
