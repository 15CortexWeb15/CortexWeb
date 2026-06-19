"""Memory management for CORTEX.

Handles persistent memory storage using JSON.
"""

import json
from pathlib import Path


class MemoryManager:
    """Persistent memory manager."""

    def __init__(self) -> None:
        self.file_path = Path(__file__).resolve().parent.parent / "data" / "memory.json"
        self.memory = {}

    def load(self) -> None:
        """Load memory from disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if self.file_path.exists():
            with self.file_path.open("r", encoding="utf-8") as handle:
                try:
                    self.memory = json.load(handle)
                except json.JSONDecodeError:
                    self.memory = {}
        else:
            self.memory = {}

    def save(self) -> None:
        """Save memory to disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with self.file_path.open("w", encoding="utf-8") as handle:
            json.dump(self.memory, handle, indent=2)

    def recall(self, key: str):
        """Return a memory entry by key."""
        return self.memory.get(key)

    def remember(self, key: str, value) -> None:
        """Store a memory entry."""
        self.memory[key] = value
        self.save()

    def forget(self, key: str) -> bool:
        """Remove a memory entry by key."""
        if key in self.memory:
            del self.memory[key]
            self.save()
            return True
        return False

    def keys(self) -> list[str]:
        """Return stored memory keys."""
        return list(self.memory.keys())

    def remember_conversation(self, user_text: str, assistant_text: str) -> None:
        """Store recent conversation turns for context."""
        history = self.memory.get("conversation_history", [])
        if not isinstance(history, list):
            history = []
        history.append({"user": user_text, "assistant": assistant_text})
        self.memory["conversation_history"] = history[-10:]
        self.save()

    def get_recent_conversation(self, limit: int = 5) -> list[dict[str, str]]:
        """Return the most recent conversation turns."""
        history = self.memory.get("conversation_history", [])
        if not isinstance(history, list):
            return []
        return history[-limit:]

    def find_user_memory(self, query: str) -> dict[str, object]:
        """Return user-facing memory entries matching a query."""
        normalized_query = query.strip().lower()
        return {
            key: value
            for key, value in self.memory.items()
            if not key.endswith("_cache")
            and (normalized_query in key.lower() or normalized_query in str(value).lower())
        }

    def get_user_name(self):
        """Return the stored user name, if any."""
        return self.memory.get("user_name")

    def set_user_name(self, name: str) -> None:
        """Store the user name in persistent memory."""
        self.memory["user_name"] = name
        self.save()


class ChatLogManager:
    """Manage named chat sessions and save chat logs to disk."""

    def __init__(self) -> None:
        self.base_path = Path(__file__).resolve().parent.parent / "data"
        self.logs_file = self.base_path / "chat_logs.json"
        self.sessions: dict[str, dict] = {}

    def load(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)
        if self.logs_file.exists():
            with self.logs_file.open("r", encoding="utf-8") as handle:
                try:
                    data = json.load(handle)
                    self.sessions = data.get("sessions", {})
                except json.JSONDecodeError:
                    self.sessions = {}
        else:
            self.sessions = {}

    def save(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)
        with self.logs_file.open("w", encoding="utf-8") as handle:
            json.dump({"sessions": self.sessions}, handle, indent=2)

    def list_sessions(self) -> list[str]:
        return list(self.sessions.keys())

    def create_session(self, name: str) -> str:
        session_name = name.strip() or f"Chat Session {len(self.sessions) + 1}"
        original_name = session_name
        index = 1
        while session_name in self.sessions:
            index += 1
            session_name = f"{original_name} ({index})"
        timestamp = self._timestamp()
        self.sessions[session_name] = {
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": [],
        }
        self.save()
        return session_name

    def add_message(self, session_name: str, sender: str, text: str) -> None:
        if session_name not in self.sessions:
            raise KeyError(f"Chat session '{session_name}' does not exist.")
        timestamp = self._timestamp()
        self.sessions[session_name]["messages"].append(
            {"timestamp": timestamp, "sender": sender, "text": text}
        )
        self.sessions[session_name]["updated_at"] = timestamp
        self.save()

    def get_session_messages(self, session_name: str) -> list[dict[str, str]]:
        return self.sessions.get(session_name, {}).get("messages", [])

    def save_session_to_file(self, session_name: str, path: str) -> None:
        messages = self.get_session_messages(session_name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(f"Chat session: {session_name}\n")
            handle.write(f"Saved at: {self._timestamp()}\n\n")
            for message in messages:
                handle.write(
                    f"[{message['timestamp']}] {message['sender']}: {message['text']}\n"
                )

    @staticmethod
    def _timestamp() -> str:
        from datetime import datetime

        return datetime.now().isoformat(sep=" ", timespec="seconds")
