import json
import os
import sys
from email.message import EmailMessage
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import smtplib

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.brain import CortexBrain

WEB_DIR = Path(__file__).resolve().parent
DIST_DIR = WEB_DIR.parent / "dist"

class CortexRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self._send_status()
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/ask":
            self._handle_ask()
            return
        if self.path == "/api/feedback":
            self._handle_feedback()
            return

        self.send_error(404, "Not Found")

    def _handle_ask(self):
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
        self._send_json({"response": response_text})

    def _handle_feedback(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(body)
            message = payload.get("message", "").strip()
            sender = payload.get("email", "anonymous@cortex.local").strip()
            if not message:
                raise ValueError("Empty feedback message")
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid request payload")
            return

        success, note = self._send_feedback_email(sender, message)
        if success:
            self._send_json({"status": "ok", "message": note})
        else:
            self._send_json({"status": "error", "error": note}, status=500)

    def _send_feedback_email(self, sender: str, message: str) -> tuple[bool, str]:
        recipient = os.environ.get("FEEDBACK_EMAIL_RECIPIENT", "khalilovshamil330@gmail.com")
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USERNAME")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        smtp_from = os.environ.get("SMTP_FROM", smtp_user or sender)

        email_message = EmailMessage()
        email_message["Subject"] = "CORTEX Feedback"
        email_message["From"] = smtp_from
        email_message["To"] = recipient
        email_message["Reply-To"] = sender
        email_message.set_content(
            f"Feedback from: {sender}\n\n"
            f"Message:\n{message}\n"
        )

        if smtp_server and smtp_user and smtp_password:
            try:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as smtp:
                    smtp.starttls()
                    smtp.login(smtp_user, smtp_password)
                    smtp.send_message(email_message)
                return True, "Feedback delivered by email."
            except Exception as exc:
                return False, f"Email delivery failed: {exc}"

        feedback_path = ROOT_DIR / "data" / "feedback.log"
        feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with feedback_path.open("a", encoding="utf-8") as handle:
            handle.write(f"---\nFrom: {sender}\nTo: {recipient}\n{message}\n\n")
        return True, "Feedback saved locally because SMTP is not configured."

    def _send_json(self, payload: dict, status: int = 200):
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_status(self):
        data = {
            "status": "ok",
            "backend": "CORTEX",
            "message": "Backend is reachable",
        }
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

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
