"""
Comprehensive tests for Week 5 Teaching Skill

Tests interactive tutoring, adaptive difficulty, and session management.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from providers.brain import Brain
from providers.exam_generator import ExamGenerator, Question, QuestionType
from providers.memory_manager import MemoryManager
from providers.teaching_skill import (
    AdaptiveTutorSession,
    LearningRecommendation,
    TeachingSkill,
    TutorSession,
)


@pytest.fixture
def mock_brain():
    """Create mock Brain"""
    brain = AsyncMock(spec=Brain)
    brain.think = AsyncMock(return_value="Explanation of topic")
    brain.stream_think = AsyncMock()
    return brain


async def mock_stream():
    """Mock streaming generator"""
    for chunk in ["This ", "is ", "an ", "explanation"]:
        yield chunk


@pytest.fixture
def mock_exam_generator():
    """Create mock ExamGenerator"""
    gen = AsyncMock(spec=ExamGenerator)

    # Create sample question
    question = Question(
        id=1,
        text="What is Python?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["A language", "A snake", "Both"],
        correct_answer="A language",
        difficulty=2,
        explanation="Python is a programming language",
        topic="Python",
        estimated_time_seconds=30,
    )

    async def mock_stream_questions(topic, num_questions, difficulty):
        yield question

    gen.stream_questions = mock_stream_questions
    return gen


@pytest.fixture
def mock_memory_manager():
    """Create mock MemoryManager"""
    manager = AsyncMock(spec=MemoryManager)
    manager.record_exam = AsyncMock()
    manager.record_conversation = AsyncMock()
    return manager


class TestTutorSession:
    """Test TutorSession dataclass"""

    def test_session_creation(self):
        """Test creating session"""
        session = TutorSession(
            id="session_001",
            topic="Python",
            initial_difficulty=2,
            current_difficulty=2,
            questions_asked=0,
            correct_answers=0,
            incorrect_answers=0,
            started_at=datetime.now().isoformat(),
        )

        assert session.id == "session_001"
        assert session.topic == "Python"
        assert session.current_difficulty == 2

    def test_session_progress(self):
        """Test session tracks progress"""
        session = TutorSession(
            id="session_001",
            topic="Python",
            initial_difficulty=2,
            current_difficulty=2,
            questions_asked=5,
            correct_answers=4,
            incorrect_answers=1,
            started_at=datetime.now().isoformat(),
        )

        accuracy = session.correct_answers / session.questions_asked
        assert accuracy == 0.8


class TestTeachingSkill:
    """Test teaching skill functionality"""

    @pytest.mark.asyncio
    async def test_start_session(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test starting a session"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        session = await skill.start_session("Python", 2)

        assert session.topic == "Python"
        assert session.current_difficulty == 2
        assert session.questions_asked == 0

    @pytest.mark.asyncio
    async def test_select_question(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test selecting a question"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        question = await skill.select_or_generate_question("Python", 2)

        assert question is not None
        assert question.topic == "Python"

    @pytest.mark.asyncio
    async def test_evaluate_correct_answer(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test evaluating correct answer"""
        mock_brain.think = AsyncMock(return_value="YES, that's correct")

        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 2)

        question = Question(
            id=1,
            text="What is Python?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A language", "A snake"],
            correct_answer="A language",
            difficulty=2,
            explanation="Python is a programming language",
            topic="Python",
            estimated_time_seconds=30,
        )

        is_correct, feedback, _ = await skill.evaluate_answer(question, "A language")

        assert is_correct is True
        assert "✓" in feedback

    @pytest.mark.asyncio
    async def test_evaluate_incorrect_answer(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test evaluating incorrect answer"""
        mock_brain.think = AsyncMock(return_value="NO, incorrect")

        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 2)

        question = Question(
            id=1,
            text="What is Python?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["A language", "A snake"],
            correct_answer="A language",
            difficulty=2,
            explanation="Python is a programming language",
            topic="Python",
            estimated_time_seconds=30,
        )

        is_correct, feedback, _ = await skill.evaluate_answer(question, "A snake")

        assert is_correct is False
        assert "✗" in feedback

    @pytest.mark.asyncio
    async def test_difficulty_increase(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test increasing difficulty with high accuracy"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 2)

        # High accuracy
        new_difficulty = await skill.adjust_difficulty(0.95)

        assert new_difficulty == 3

    @pytest.mark.asyncio
    async def test_difficulty_decrease(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test decreasing difficulty with low accuracy"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 3)

        # Low accuracy
        new_difficulty = await skill.adjust_difficulty(0.4)

        assert new_difficulty == 2

    @pytest.mark.asyncio
    async def test_difficulty_maintain(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test maintaining difficulty with medium accuracy"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 3)

        # Medium accuracy
        new_difficulty = await skill.adjust_difficulty(0.7)

        assert new_difficulty == 3

    @pytest.mark.asyncio
    async def test_get_session_progress(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test getting session progress"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 2)

        # Simulate some answers
        if skill.current_session:
            skill.current_session.questions_asked = 10
            skill.current_session.correct_answers = 8

            progress = await skill.get_session_progress()

            assert progress is not None
            assert progress["accuracy"] == 0.8
            assert "progress_bar" in progress

    @pytest.mark.asyncio
    async def test_end_session_records_results(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test ending session records results"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 2)

        # Simulate answers
        if skill.current_session:
            skill.current_session.questions_asked = 5
            skill.current_session.correct_answers = 4

            report = await skill.end_session()

            assert report is not None
            assert report.total_questions == 5
            assert report.correct_answers == 4
            assert mock_memory_manager.record_exam.called

    @pytest.mark.asyncio
    async def test_generate_recommendations_high_accuracy(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test generating recommendations for high accuracy"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        await skill.start_session("Python", 2)

        if skill.current_session:
            skill.current_session.questions_asked = 10
            skill.current_session.correct_answers = 9

            recommendations = await skill._generate_recommendations(
                skill.current_session
            )

            assert len(recommendations) > 0
            # Should recommend increased difficulty
            assert any(
                "challenge" in r.suggested_action.lower() for r in recommendations
            )

    @pytest.mark.asyncio
    async def test_stream_explanation(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test streaming explanation"""

        async def mock_stream_impl(prompt):
            for chunk in ["This ", "is ", "an ", "explanation"]:
                yield chunk

        mock_brain.stream_think = mock_stream_impl

        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)

        chunks = []
        async for chunk in skill.get_interactive_explanation("Python"):
            chunks.append(chunk)

        assert len(chunks) > 0


class TestAdaptiveTutorSession:
    """Test adaptive tutor session"""

    @pytest.mark.asyncio
    async def test_session_workflow(
        self, mock_brain, mock_exam_generator, mock_memory_manager
    ):
        """Test complete session workflow"""
        skill = TeachingSkill(mock_brain, mock_exam_generator, mock_memory_manager)
        session = AdaptiveTutorSession(skill)

        # Start session
        started = await session.start("Python", 2)
        assert started.topic == "Python"

        # Get question
        question = await session.ask_question()
        assert question is not None

        # End session
        report = await session.end()
        assert report is not None


class TestLearningRecommendation:
    """Test learning recommendation"""

    def test_recommendation_creation(self):
        """Test creating recommendation"""
        rec = LearningRecommendation(
            topic="Python",
            reason="Strong performance",
            difficulty_level=3,
            suggested_action="Try harder problems",
            confidence_score=0.9,
        )

        assert rec.topic == "Python"
        assert rec.confidence_score == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
