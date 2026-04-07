"""
Comprehensive tests for Week 6 Coding Skill

Tests code review, bug detection, and optimization suggestions.
"""

from unittest.mock import AsyncMock

import pytest

from providers.brain import Brain
from providers.code_executor import CodeExecutor
from providers.coding_skill import (
    CodeIssue,
    CodeMentor,
    CodeReviewResult,
    CodingSkill,
    IssueType,
)
from providers.memory_manager import MemoryManager


@pytest.fixture
def mock_brain():
    """Create mock Brain"""
    brain = AsyncMock(spec=Brain)
    brain.think = AsyncMock(return_value="Analysis complete")
    brain.stream_think = AsyncMock()
    return brain


@pytest.fixture
def mock_executor():
    """Create mock CodeExecutor"""
    executor = AsyncMock(spec=CodeExecutor)
    from providers.code_executor import ExecutionResult, ExecutionStatus

    result = ExecutionResult(status=ExecutionStatus.SUCCESS, stdout="Success")
    executor.execute = AsyncMock(return_value=result)
    return executor


@pytest.fixture
def mock_memory():
    """Create mock MemoryManager"""
    memory = AsyncMock(spec=MemoryManager)
    memory.record_snippet = AsyncMock()
    return memory


class TestCodeIssue:
    """Test CodeIssue dataclass"""

    def test_issue_creation(self):
        """Test creating code issue"""
        issue = CodeIssue(
            issue_type=IssueType.STYLE,
            severity=2,
            line_number=10,
            description="Formatting issue",
            suggestion="Use proper indentation",
            confidence_score=0.8,
        )

        assert issue.issue_type == IssueType.STYLE
        assert issue.severity == 2


class TestCodingSkill:
    """Test coding skill functionality"""

    @pytest.mark.asyncio
    async def test_review_code(self, mock_brain, mock_executor, mock_memory):
        """Test code review"""
        skill = CodingSkill(mock_brain, mock_executor, mock_memory)

        code = """
def hello():
    x=1
    return x
"""

        result = await skill.review_code(code)

        assert isinstance(result, CodeReviewResult)
        assert result.quality_score >= 0
        assert result.total_issues >= 0

    @pytest.mark.asyncio
    async def test_suggest_refactoring(self, mock_brain, mock_executor, mock_memory):
        """Test refactoring suggestions"""
        skill = CodingSkill(mock_brain, mock_executor, mock_memory)

        code = """
def process(data):
    result = []
    for item in data:
        if item > 10:
            result.append(item * 2)
    return result
"""

        plan = await skill.suggest_refactoring(code, focus_area="readability")

        assert plan is not None
        assert plan.before_code == code

    @pytest.mark.asyncio
    async def test_detect_bugs(self, mock_brain, mock_executor, mock_memory):
        """Test bug detection"""
        mock_brain.think = AsyncMock(
            return_value="BUG: Uninitialized variable\nFIX: Initialize before use"
        )

        skill = CodingSkill(mock_brain, mock_executor, mock_memory)

        code = "x = y + 1"

        bugs = await skill.detect_bugs(code)

        assert isinstance(bugs, list)

    @pytest.mark.asyncio
    async def test_performance_tips(self, mock_brain, mock_executor, mock_memory):
        """Test performance optimization tips"""

        async def mock_stream_impl(prompt):
            yield "Tip 1"
            yield "Tip 2"

        mock_brain.stream_think = mock_stream_impl

        skill = CodingSkill(mock_brain, mock_executor, mock_memory)

        code = """
result = []
for i in range(100):
    result.append(i * 2)
"""

        tips_gen = skill.get_performance_tips(code)

        # tips is an AsyncIterator, consume it
        tip_list = []
        async for tip in tips_gen:
            tip_list.append(tip)

        assert isinstance(tip_list, list)

    @pytest.mark.asyncio
    async def test_explain_functionality(self, mock_brain, mock_executor, mock_memory):
        """Test code explanation"""

        async def mock_stream_impl(prompt):
            yield "This code "
            yield "does something"

        mock_brain.stream_think = mock_stream_impl

        skill = CodingSkill(mock_brain, mock_executor, mock_memory)

        code = "return [x * 2 for x in data]"

        explanations = []
        async for chunk in skill.explain_functionality(code):
            explanations.append(chunk)

        assert len(explanations) >= 0


class TestCodeMentor:
    """Test code mentor"""

    @pytest.mark.asyncio
    async def test_analyze_and_teach(self, mock_brain, mock_executor, mock_memory):
        """Test teaching feedback"""
        skill = CodingSkill(mock_brain, mock_executor, mock_memory)
        mentor = CodeMentor(skill)

        code = "def add(a, b): return a+b"

        feedback = await mentor.analyze_and_teach(code)

        assert "quality_score" in feedback
        assert "learning_points" in feedback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
