"""AI adapter for CORTEX.

This module supports Ollama local HTTP integration with a consistent professional style.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Optional


class AIAdapter:
    """Provides a simple bridge to an optional local AI provider."""

    def __init__(self, provider: Optional[str] = None) -> None:
        self.ollama_url = os.environ.get("OLLAMA_URL", "").strip()
        self.model = os.environ.get("OLLAMA_MODEL", "llama2").strip()
        self.provider = provider or self._select_provider()

    def _select_provider(self) -> str:
        if self.ollama_url:
            return "ollama"
        return "none"

    def ask(self, prompt: str) -> str:
        """Ask the configured AI provider for a response."""
        if self.provider == "ollama":
            return self._ask_ollama(prompt)
        return (
            "AI integration is not configured.\n"
            "CORTEX operates locally by default with built-in answers and simulations.\n"
            "Set OLLAMA_URL and OLLAMA_MODEL for optional advanced local Ollama responses."
        )

    def _system_instruction(self) -> str:
        return (
            "You are CORTEX, a professional computational intelligence assistant. "
            "Answer clearly and accurately using a calm engineering tone. "
            "Provide concise explanations, step-by-step guidance when useful, and practical recommendations. "
            "Avoid casual slang and keep responses aligned with factual knowledge and technical clarity."
        )

    def _ask_ollama(self, prompt: str) -> str:
        request_url = f"{self.ollama_url}/v1/generate"
        payload = {
            "model": self.model,
            "prompt": [
                {"role": "system", "content": self._system_instruction()},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 400,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        try:
            request = urllib.request.Request(request_url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=20) as response:
                response_data = json.load(response)
                return self._parse_ollama_response(response_data)
        except urllib.error.HTTPError as exc:
            return f"Ollama HTTP error: {exc.code} {exc.reason}"
        except urllib.error.URLError as exc:
            return f"Ollama connection failed: {exc.reason}"
        except Exception as exc:
            return f"Ollama request failed: {exc}"

    def _parse_ollama_response(self, response_data: dict) -> str:
        if "output" in response_data and isinstance(response_data["output"], list):
            return "".join(str(item) for item in response_data["output"]).strip()
        if "choices" in response_data and isinstance(response_data["choices"], list):
            first_choice = response_data["choices"][0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict) and "content" in message:
                    return str(message["content"]).strip()
                if "text" in first_choice:
                    return str(first_choice["text"]).strip()
        return json.dumps(response_data)
