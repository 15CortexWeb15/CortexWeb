import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.brain import CortexBrain

WEB_DIR = Path(__file__).resolve().parent
DIST_DIR = WEB_DIR.parent / "dist"

class CortexRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_POST(self):
        if self.path != "/api/ask":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(body)
            user_input = payload.get("query", "").strip()
            if not user_input:
                raise ValueError("Empty query")
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid request payload")
            return

        response_text = self.server.brain.execute_command(user_input)
        data = {"response": response_text}
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return


def run_server(host: str | None = None, port: int | None = None) -> None:
    if host is None:
        host = os.environ.get("HOST", "0.0.0.0")
    if port is None:
        port = int(os.environ.get("PORT", "8080"))

    brain = CortexBrain()
    brain.start()
    server = HTTPServer((host, port), CortexRequestHandler)
    server.brain = brain
    print(f"Serving CORTEX web demo at http://{host}:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server.")
        server.server_close()


if __name__ == "__main__":
    run_server()
