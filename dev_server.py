"""Run the whole app locally without the Vercel CLI:  python dev_server.py  ->  http://127.0.0.1:3000"""
import os
import sys
import types
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "api"))

env_file = ROOT / ".env"
if env_file.exists():  # minimal .env loader, no extra dependency
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"'))

import chat, faqs, health  # noqa: E402  (the same handlers Vercel runs)


class Dev(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "frontend"), **kwargs)

    def log_message(self, *args):  # quieter terminal
        pass

    def _api(self, module, method):
        self._send = types.MethodType(chat.handler._send, self)
        getattr(module.handler, method)(self)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/faqs":
            return self._api(faqs, "do_GET")
        if path == "/api/health":
            return self._api(health, "do_GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] == "/api/chat":
            return self._api(chat, "do_POST")
        self.send_error(404)

    def do_OPTIONS(self):
        self._api(chat, "do_OPTIONS")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    print(f"AgentFlow running at http://127.0.0.1:{port}  (LLM key set: {bool(os.getenv('GROQ_API_KEY'))})")
    ThreadingHTTPServer(("127.0.0.1", port), Dev).serve_forever()
