"""Tests for Week 7 GUI Layer

Tests cover GUI components, integration, and interaction patterns.
"""

from gui.components import (
    CodeDisplay,
    ExamDisplay,
    MessageDisplay,
    SessionInfo,
    SettingsPanel,
)


class TestMessageDisplay:
    """Test message display component"""

    def test_message_display_creation(self):
        """Test creating message display"""
        display = MessageDisplay()
        assert display is not None
        assert display.messages == []

    def test_add_message(self):
        """Test adding message to display"""
        display = MessageDisplay()
        display.add_message("user", "Hello")
        assert len(display.messages) == 1
        assert display.messages[0]["role"] == "user"
        assert display.messages[0]["content"] == "Hello"


class TestCodeDisplay:
    """Test code display component"""

    def test_code_display_creation(self):
        """Test creating code display"""
        display = CodeDisplay()
        assert display is not None
        assert display.code == ""
        assert display.language == "python"

    def test_show_code(self):
        """Test displaying code"""
        display = CodeDisplay()
        code = "def hello():\n    print('world')"
        display.show_code(code, "python")
        assert display.code == code
        assert display.language == "python"


class TestExamDisplay:
    """Test exam display component"""

    def test_exam_display_creation(self):
        """Test creating exam display"""
        display = ExamDisplay()
        assert display is not None
        assert display.current_question is None
        assert display.options is None

    def test_show_question(self):
        """Test displaying exam question"""
        display = ExamDisplay()
        question = "What is 2+2?"
        options = ["3", "4", "5"]
        display.show_question(question, options)
        assert display.current_question == question
        assert display.options == options


class TestSessionInfo:
    """Test session info component"""

    def test_session_info_creation(self):
        """Test creating session info"""
        session_info = SessionInfo()
        assert session_info is not None
        assert session_info.progress == 0.0
        assert session_info.stats == {}

    def test_update_progress(self):
        """Test updating progress"""
        session_info = SessionInfo()
        session_info.update_progress(5, 10)
        assert session_info.progress == 0.5

    def test_set_stats(self):
        """Test setting statistics"""
        session_info = SessionInfo()
        session_info.set_stats(questions=10, correct=8, accuracy="80%")
        assert session_info.stats["questions"] == 10
        assert session_info.stats["correct"] == 8


class TestSettingsPanel:
    """Test settings panel component"""

    def test_settings_panel_creation(self):
        """Test creating settings panel"""
        panel = SettingsPanel()
        assert panel is not None
        assert panel.model_var == "tinyllama"
        assert panel.difficulty_var == "intermediate"
        assert panel.style_var == "concise"


class TestGUIIntegration:
    """Test GUI integration scenarios"""

    def test_chat_workflow(self):
        """Test chat message workflow"""
        display = MessageDisplay()
        display.add_message("user", "What is Python?")
        display.add_message("assistant", "Python is a programming language.")
        assert len(display.messages) == 2
        assert display.messages[0]["role"] == "user"
        assert display.messages[1]["role"] == "assistant"

    def test_exam_workflow(self):
        """Test exam session workflow"""
        exam = ExamDisplay()
        session = SessionInfo()

        exam.show_question("Question 1?", ["A", "B", "C"])
        session.update_progress(1, 3)
        session.set_stats(current=1, total=3, correct=1)

        assert exam.current_question == "Question 1?"
        assert session.progress == 1 / 3
        assert session.stats["correct"] == 1
