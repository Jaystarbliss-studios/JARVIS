"""
Week 2 Tests: Exam Generation and Tools Framework
Tests batch exam generation, streaming, validation, and tool execution
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from providers.exam_generator import (
    AnswerResult,
    ExamGenerator,
    ExamSession,
    Question,
    QuestionType,
)
from providers.tools import (
    ToolParser,
    ToolRegistry,
)


class TestExamGenerator:
    """Test suite for exam generation"""

    @pytest.fixture
    def mock_brain(self):
        """Mock Brain instance"""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def exam_gen(self, mock_brain):
        """Create ExamGenerator with mock brain"""
        return ExamGenerator(mock_brain)

    @pytest.mark.asyncio
    async def test_exam_generator_initialization(self, exam_gen):
        """Test ExamGenerator creates successfully"""
        assert exam_gen.brain is not None
        assert hasattr(exam_gen, "generate_exam")

    @pytest.mark.asyncio
    async def test_difficulty_prompts_exist(self, exam_gen):
        """Test all difficulty levels have prompts"""
        for difficulty in range(1, 6):
            assert difficulty in exam_gen.DIFFICULTY_PROMPTS
            assert len(exam_gen.DIFFICULTY_PROMPTS[difficulty]) > 0

    @pytest.mark.asyncio
    async def test_time_estimates_valid(self, exam_gen):
        """Test time estimates for each difficulty"""
        for difficulty in range(1, 6):
            assert difficulty in exam_gen.TIME_ESTIMATES
            assert exam_gen.TIME_ESTIMATES[difficulty] > 0

    @pytest.mark.asyncio
    async def test_question_dataclass(self):
        """Test Question dataclass"""
        q = Question(
            id=1,
            text="What is Python?",
            question_type=QuestionType.SHORT_ANSWER,
            correct_answer="A programming language",
            difficulty=2,
            explanation="Python is an interpreted language",
            topic="Python Basics",
        )

        assert q.id == 1
        assert q.text == "What is Python?"
        assert q.difficulty == 2
        assert q.topic == "Python Basics"

    @pytest.mark.asyncio
    async def test_question_to_dict(self):
        """Test Question serialization"""
        q = Question(
            id=1,
            text="Test?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A", "B", "C"],
            difficult=2,
        )

        d = q.to_dict()
        assert d["id"] == 1
        assert d["text"] == "Test?"
        assert d["type"] == "multiple_choice"

    @pytest.mark.asyncio
    async def test_exam_session_creation(self):
        """Test ExamSession tracks progress"""
        session = ExamSession(
            exam_id="test1",
            topic="Python",
            difficulty=3,
        )

        assert session.exam_id == "test1"
        assert session.topic == "Python"
        assert len(session.questions) == 0
        assert session.progress == (0, 0)

    @pytest.mark.asyncio
    async def test_exam_session_score_calculation(self):
        """Test score calculation"""
        session = ExamSession(
            exam_id="test1",
            topic="Python",
            difficulty=3,
            scores=[1.0, 0.8, 0.6, 1.0, 0.5],
        )

        expected_score = (1.0 + 0.8 + 0.6 + 1.0 + 0.5) / 5
        assert session.score == pytest.approx(expected_score)

    @pytest.mark.asyncio
    async def test_exam_session_progress_tracking(self):
        """Test progress tracking"""
        session = ExamSession(
            exam_id="test1",
            topic="Python",
            difficulty=3,
            questions=[Mock(id=i) for i in range(5)],
            answers=[(1, "answer1"), (2, "answer2")],
        )

        assert session.progress == (2, 5)

    @pytest.mark.asyncio
    async def test_parse_question_json_valid(self, exam_gen):
        """Test parsing valid question JSON"""
        data = {
            "id": 1,
            "text": "What is Python?",
            "type": "short_answer",
            "correct": "A language",
            "explanation": "Python is...",
        }

        q = exam_gen._parse_question_json(data, 1, "Python", 3)
        assert q is not None
        assert q.text == "What is Python?"
        assert q.correct_answer == "A language"

    @pytest.mark.asyncio
    async def test_parse_question_json_invalid(self, exam_gen):
        """Test parsing invalid question JSON"""
        data = {
            "text": "",  # Empty text
            "type": "short_answer",
        }

        q = exam_gen._parse_question_json(data, 1, "Python", 3)
        assert q is None

    @pytest.mark.asyncio
    async def test_parse_question_type_mapping(self, exam_gen):
        """Test question type mapping"""
        test_cases = [
            ("multiple_choice", QuestionType.MULTIPLE_CHOICE),
            ("short_answer", QuestionType.SHORT_ANSWER),
            ("true_false", QuestionType.TRUE_FALSE),
            ("code", QuestionType.CODE),
        ]

        for type_str, expected_type in test_cases:
            data = {
                "id": 1,
                "text": "Q?",
                "type": type_str,
                "correct": "yes",
            }
            q = exam_gen._parse_question_json(data, 1, "Test", 3)
            assert q.question_type == expected_type

    @pytest.mark.asyncio
    async def test_answer_validation_result(self):
        """Test AnswerResult creation"""
        result = AnswerResult(
            is_correct=True,
            score=0.95,
            feedback="Great answer!",
            explanation="Because...",
            time_taken_seconds=30.5,
        )

        assert result.is_correct is True
        assert result.score == 0.95
        assert result.time_taken_seconds == 30.5

    @pytest.mark.asyncio
    async def test_validate_answer_integration(self, exam_gen, mock_brain):
        """Test answer validation"""
        mock_brain.think = AsyncMock(
            return_value='{"is_correct": true, "score": 1.0, "feedback": "Correct!"}'
        )

        q = Question(
            id=1,
            text="What is 2+2?",
            question_type=QuestionType.SHORT_ANSWER,
            correct_answer="4",
            difficulty=1,
        )

        result = await exam_gen.validate_answer(q, "4", time_taken_seconds=10)
        assert result.is_correct is True
        assert result.score == 1.0


class TestToolRegistry:
    """Test suite for tool registration and execution"""

    def test_registry_initialization(self):
        """Test ToolRegistry creates successfully"""
        registry = ToolRegistry()
        assert len(registry.get_tools()) == 0

    def test_register_sync_tool(self):
        """Test registering a synchronous tool"""
        registry = ToolRegistry()

        def my_tool(x: int) -> int:
            return x * 2

        registry.register(
            name="double",
            description="Double a number",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
            handler=my_tool,
            is_async=False,
        )

        assert len(registry.get_tools()) == 1
        tool = registry.get_tool("double")
        assert tool is not None
        assert tool.name == "double"

    def test_register_async_tool(self):
        """Test registering an async tool"""
        registry = ToolRegistry()

        async def my_async_tool(x: int) -> int:
            return x * 3

        registry.register(
            name="triple",
            description="Triple a number",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
            handler=my_async_tool,
            is_async=True,
        )

        tool = registry.get_tool("triple")
        assert tool.is_async is True

    def test_get_nonexistent_tool(self):
        """Test getting non-existent tool"""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None

    @pytest.mark.asyncio
    async def test_execute_sync_tool(self):
        """Test executing a sync tool"""
        registry = ToolRegistry()

        def add(a: int, b: int) -> int:
            return a + b

        registry.register(
            name="add",
            description="Add two numbers",
            parameters={},
            handler=add,
            is_async=False,
        )

        result = await registry.execute("add", {"a": 5, "b": 3})
        assert result.success is True
        assert result.result == 8

    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """Test executing an async tool"""
        registry = ToolRegistry()

        async def multiply(a: int, b: int) -> int:
            await asyncio.sleep(0.01)
            return a * b

        registry.register(
            name="multiply",
            description="Multiply two numbers",
            parameters={},
            handler=multiply,
            is_async=True,
        )

        result = await registry.execute("multiply", {"a": 4, "b": 7})
        assert result.success is True
        assert result.result == 28

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing non-existent tool"""
        registry = ToolRegistry()
        result = await registry.execute("nonexistent", {})
        assert result.success is False
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_error(self):
        """Test tool that raises exception"""
        registry = ToolRegistry()

        def failing_tool():
            raise ValueError("Something went wrong")

        registry.register(
            name="fail",
            description="Fails deliberately",
            parameters={},
            handler=failing_tool,
        )

        result = await registry.execute("fail", {})
        assert result.success is False
        assert "Something went wrong" in result.error

    def test_to_schema_format(self):
        """Test OpenAI schema generation"""
        registry = ToolRegistry()

        def my_tool(x: int) -> int:
            return x

        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            handler=my_tool,
        )

        schemas = registry.to_schema()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "test_tool"


class TestToolParser:
    """Test suite for parsing tool calls from LLM output"""

    def test_parse_xml_tool_call(self):
        """Test parsing XML-style tool calls"""
        text = '<tool_call>{"tool": "generate_exam", "args": {"topic": "Python"}}</tool_call>'
        calls = ToolParser.parse_from_text(text)

        assert len(calls) == 1
        assert calls[0].tool_name == "generate_exam"
        assert calls[0].arguments["topic"] == "Python"

    def test_parse_json_code_block(self):
        """Test parsing JSON in code blocks"""
        text = '```json\n{"action": "run_code", "arguments": {"code": "print(1)"}}\n```'
        calls = ToolParser.parse_from_text(text)

        assert len(calls) == 1
        assert calls[0].tool_name == "run_code"

    def test_parse_multiple_calls(self):
        """Test parsing multiple tool calls"""
        text = """
<tool_call>{"tool": "tool1", "args": {"x": 1}}</tool_call>
Some text
<tool_call>{"tool": "tool2", "args": {"y": 2}}</tool_call>
"""
        calls = ToolParser.parse_from_text(text)

        assert len(calls) == 2
        assert calls[0].tool_name == "tool1"
        assert calls[1].tool_name == "tool2"

    def test_parse_no_calls(self):
        """Test parsing text with no tool calls"""
        text = "This is just plain text with no tool calls"
        calls = ToolParser.parse_from_text(text)

        assert len(calls) == 0

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON"""
        text = '<tool_call>{"invalid json}</tool_call>'
        calls = ToolParser.parse_from_text(text)

        assert len(calls) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
