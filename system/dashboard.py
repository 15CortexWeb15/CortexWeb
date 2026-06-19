"""Dashboard utilities for CORTEX."""


class Dashboard:
    """Provides status and report formatting."""

    def __init__(self) -> None:
        self.status = {}

    def render_status(self, **status_values) -> None:
        """Store status values for later report generation."""
        self.status = status_values

    def build_report(self) -> str:
        """Return a formatted dashboard report."""
        lines = ["CORTEX", "Computational Engineering Intelligence System", ""]
        for label, value in self.status.items():
            lines.append(f"{label.capitalize():<20}{value}")
        return "\n".join(lines)
