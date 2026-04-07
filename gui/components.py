"""
GUI Components for JARVIS-Lite - Framework Agnostic

Specialized UI components for teaching, coding, and chat modes.
Works with or without CustomTkinter (useful for testing).
"""

from typing import Any


class MessageDisplay:
    """Enhanced text display for chat messages with formatting"""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        self.messages: list[dict[str, Any]] = []

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        color: str = "#ffffff",
    ) -> None:
        """Add formatted message to display"""
        self.messages.append(
            {"role": role, "content": content, "metadata": metadata, "color": color}
        )


class CodeDisplay:
    """Specialized display for code with syntax highlighting"""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        self.code = ""
        self.language = "python"

    def show_code(self, code: str, language: str = "python") -> None:
        """Display code snippet"""
        self.code = code
        self.language = language


class ExamDisplay:
    """Display for exam questions and answers"""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        self.current_question: str | None = None
        self.options: list[str] | None = None

    def show_question(
        self, question_text: str, options: list[str] | None = None
    ) -> None:
        """Display exam question"""
        self.current_question = question_text
        self.options = options or []


class SessionInfo:
    """Display session information and progress"""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        self.progress = 0.0
        self.stats: dict[str, Any] = {}

    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar"""
        if total > 0:
            self.progress = current / total

    def set_stats(self, **stats: Any) -> None:
        """Update statistics display"""
        self.stats = stats


class DarkThemeButton:
    """Styled button for dark theme"""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        self.config = {
            "fg_color": "#0066cc",
            "hover_color": "#0052a3",
            "text_color": "#ffffff",
            "border_width": 0,
            "corner_radius": 6,
            "height": 35,
            **kwargs,
        }


class SettingsPanel:
    """Settings and preferences panel"""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        self.model_var = "tinyllama"
        self.difficulty_var = "intermediate"
        self.style_var = "concise"
        self.config = kwargs
