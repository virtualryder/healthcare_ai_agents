# agent/serve.py — minimal AgentCore Runtime contract (/invocations + /ping).
from __future__ import annotations
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "08-contact-center-member-services-agent")]
from agent.core import run_until_gate, resume  # noqa: E402


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        if self.path == "/ping":
            self._send(200, {"status": "healthy"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/invocations":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        state = run_until_gate(payload)
        if payload.get("human_approval"):
            state = resume(state, approval=payload["human_approval"])
        state.pop("_paused_at_gate", None)
        self._send(200, state)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
