from __future__ import annotations

import json
import os
from collections import defaultdict
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .agent import ConversationState, TravelWorkflowAgent
from .concur_client import ConcurClient, ConcurConfig

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"

concur = ConcurClient(
    ConcurConfig(
        base_url=os.getenv("CONCUR_BASE_URL", "https://www.concursolutions.com"),
        access_token=os.getenv("CONCUR_ACCESS_TOKEN"),
        client_id=os.getenv("CONCUR_CLIENT_ID"),
        client_secret=os.getenv("CONCUR_CLIENT_SECRET"),
        refresh_token=os.getenv("CONCUR_REFRESH_TOKEN"),
        token_url=os.getenv("CONCUR_TOKEN_URL", "https://us2.api.concursolutions.com/oauth2/v0/token"),
    )
)
agent = TravelWorkflowAgent(concur)
sessions: dict[str, ConversationState] = defaultdict(ConversationState)


class TravelHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if self.path == "/" or self.path == "":
            self.path = "/index.html"

        target = (STATIC_DIR / self.path.lstrip("/")).resolve()
        if target.is_file() and str(target).startswith(str(STATIC_DIR)):
            self._serve_file(target)
            return

        self._serve_file(STATIC_DIR / "index.html")

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            session_id = payload["session_id"]
            message = payload["message"]
        except Exception:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON body")
            return

        state = sessions[session_id]
        result = agent.respond(message, state)
        self._send_json(result)

    def _serve_file(self, file_path: Path) -> None:
        content = file_path.read_bytes()
        content_type = "text/html; charset=utf-8"
        if file_path.suffix == ".js":
            content_type = "application/javascript"
        elif file_path.suffix == ".css":
            content_type = "text/css"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def run(port: int = 8000) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), TravelHandler)
    print(f"Executive Travel Agent running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(int(os.getenv("PORT", "8000")))
