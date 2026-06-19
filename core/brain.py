"""Core brain module for CORTEX.

This module provides the high-level orchestration layer that ties
reasoning, memory, simulation, decision-making, and optimisation.
"""

from system.dashboard import Dashboard
from core.reasoning import ReasoningEngine
from core.memory import MemoryManager, ChatLogManager
from core.simulation import SimulationEngine
from core.decision_engine import DecisionEngine
from core.optimizer import Optimizer
from core.search import KnowledgeSearch
from core.browser import MiniBrowser


class CortexBrain:
    """Primary CORTEX brain controller."""

    def __init__(self) -> None:
        self.dashboard = Dashboard()
        self.reasoning = ReasoningEngine()
        self.memory = MemoryManager()
        self.chat_logs = ChatLogManager()
        self.simulation = SimulationEngine()
        self.decision_engine = DecisionEngine()
        self.optimizer = Optimizer()
        self.wikipedia = KnowledgeSearch()
        self.browser = MiniBrowser()
        self.command_history: list[str] = []
        self.active_chat_session: str | None = None

    def start(self) -> None:
        """Initialize CORTEX and display a startup report."""
        self.memory.load()
        self.chat_logs.load()
        self.dashboard.render_status(
            core="ONLINE",
            reasoning="ACTIVE",
            memory="ACTIVE",
            simulation="READY",
            knowledge="LOADED",
        )

    def execute_command(self, command: str) -> str:
        """Execute a user command or freeform request and return the report text."""
        command = command.strip()
        if not command:
            return self.dashboard.build_report()

        self.command_history.append(command)
        parts = command.split(None, 1)
        keyword = parts[0].lower()
        rest = parts[1].strip() if len(parts) > 1 else ""

        if keyword in ("help", "h"):
            return self._help_text()
        if keyword in ("status", "st"):
            return self.dashboard.build_report()
        if keyword in ("simulate", "sim", "run"):
            return self.simulation.run_simulation(rest)
        if keyword in ("decision", "dec"):
            return self.decision_engine.evaluate()
        if keyword in ("search", "wikipedia", "wiki"):
            return self._handle_wikipedia(rest)
        if keyword in ("browse", "browser", "open"):
            return self._handle_browser(rest)
        if keyword in ("chatlogs", "chats"):
            return self._chat_logs_report(rest)
        if keyword in ("fun", "joke", "laugh"):
            return self._fun_report()
        if keyword in ("ask", "q", "query"):
            return self._handle_question(rest)
        if keyword in ("clear", "cls"):
            return "__CORTEX_CLEAR_SCREEN__"
        if keyword in ("history", "recent", "log"):
            return self._history_report()
        if keyword in ("version", "about"):
            return self._version_report()
        if keyword in ("memories", "memory", "notes") and not rest:
            return self._memory_report()
        if keyword in ("forget", "remove"):
            return self._forget_memory(rest)

        return self._process_chat_message(command)

    def _help_text(self) -> str:
        return (
            self.dashboard.build_report()
            + "\n\nSupported commands:\n"
            + "- status, simulate, decision, search/wiki, browse, chatlogs, fun, ask, convert\n"
            + "- remember, recall, forget, memories, history, clear, about\n"
            + "- You can also chat naturally and ask for smart engineering guidance.\n"
            + "Example: 'browse example.com', 'simulate a mission', or 'chatlogs new mychat'."
        )

    def _handle_wikipedia(self, rest: str) -> str:
        if rest:
            result = self.wikipedia.search(rest)
            if result:
                return result
            return "Wikipedia search did not return a result."
        return "Please provide a search query after the command."

    def _handle_question(self, rest: str) -> str:
        if rest:
            return self.reasoning.answer_request(rest)
        return "Please provide a question after the command."

    def _handle_browser(self, rest: str) -> str:
        if not rest:
            return "Please enter a URL or search query after the browse command."
        return self.browser.browse(rest)

    def _chat_logs_report(self, rest: str) -> str:
        if not rest:
            sessions = self.chat_logs.list_sessions()
            if not sessions:
                return "No chat sessions found. Use 'chatlogs new <session name>' to create one."
            lines = ["Saved Chat Sessions:"]
            lines.extend(f"- {name}" for name in sessions)
            lines.append("\nCommands: chatlogs new <name>, chatlogs open <name>, chatlogs save <name>, chatlogs history <name>")
            return "\n".join(lines)

        parts = rest.split(None, 1)
        command = parts[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""

        if command == "new":
            session_name = self.chat_logs.create_session(argument or f"Chat Session {len(self.chat_logs.sessions) + 1}")
            self.active_chat_session = session_name
            return f"Created new chat session: '{session_name}'."
        if command == "open":
            if argument in self.chat_logs.sessions:
                self.active_chat_session = argument
                return f"Opened chat session: '{argument}'."
            return f"Chat session '{argument}' not found."
        if command == "save":
            if not argument:
                return "Provide the chat session name to save."
            if argument not in self.chat_logs.sessions:
                return f"Chat session '{argument}' does not exist."
            path = self.chat_logs.base_path / f"{argument}.txt"
            self.chat_logs.save_session_to_file(argument, str(path))
            return f"Chat session '{argument}' saved to {path}."
        if command == "history":
            if not argument:
                return "Provide the chat session name to view history."
            messages = self.chat_logs.get_session_messages(argument)
            if not messages:
                return f"Chat session '{argument}' is empty or not found."
            lines = [f"History for '{argument}':"]
            lines.extend(
                f"[{msg['timestamp']}] {msg['sender']}: {msg['text']}" for msg in messages
            )
            return "\n".join(lines)

        return "Unknown chatlogs command. Use 'chatlogs new <name>', 'chatlogs open <name>', 'chatlogs save <name>', or 'chatlogs history <name>'."

    def _process_chat_message(self, message: str) -> str:
        if not self.active_chat_session:
            self.active_chat_session = self.chat_logs.create_session("Default Chat")
        user_name = self.memory.get_user_name() or "User"
        self.chat_logs.add_message(self.active_chat_session, user_name, message)
        response = self.reasoning.answer_request(message)
        self.chat_logs.add_message(self.active_chat_session, "CORTEX", response)
        return response

    def _stargaze_report(self) -> str:
        facts = [
            "Polaris is almost fixed in our sky because it lies close to Earth's north celestial pole.",
            "The Milky Way is home to more than 100 billion stars, but only about 6,000 are visible without a telescope.",
            "Light from the nearest star, Proxima Centauri, takes about 4.24 years to reach us.",
            "A shooting star is not a star at all: it is dust or rock burning up in our atmosphere.",
            "Some stars are so large, they would swallow our entire solar system if placed where the Sun is.",
        ]
        return "Star Gazing Mode:\n" + random.choice(facts)

    def _fun_report(self) -> str:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the robot go on vacation? To recharge its batteries!",
            "What do you call a spaceship that eats too much? A chew-niverse.",
            "If you ask CORTEX for a joke, it will return with a starry pun. You’ve been warned.",
            "I told a joke about the cosmos once — it was out of this world.",
        ]
        return "Fun Mode:\n" + random.choice(jokes) + "\nTry 'ask me something funny' for more.\n"

    def _history_report(self) -> str:
        if not self.command_history:
            return "No commands have been issued yet."
        recent = self.command_history[-10:]
        lines = ["Command History (last 10):"]
        for index, item in enumerate(recent, start=max(1, len(self.command_history) - len(recent) + 1)):
            lines.append(f"{index}. {item}")
        return "\n".join(lines)

    def _memory_report(self) -> str:
        keys = self.memory.keys()
        if not keys:
            return "Memory is empty. Use 'remember <key> as <value>' to store a note."
        lines = ["Stored Memory Keys:"]
        lines.extend(f"- {key}" for key in keys)
        return "\n".join(lines)

    def _forget_memory(self, rest: str) -> str:
        key = rest.strip()
        if not key:
            return "Please specify the memory key to forget. Example: forget favorite color"
        if self.memory.forget(key):
            return f"Forgot memory entry '{key}'."
        return f"No memory entry found for '{key}'."

    def _version_report(self) -> str:
        return (
            "CORTEX Assistant v2.0\n"
            "Capabilities: reasoning, simulation, memory, conversion, Wikipedia search, local AI fallback.\n"
            "Platform: Windows standalone or Python runtime.\n"
            "Use 'help' for a full list of commands."
        )
