"""
Week 5: Teaching Skill - Interactive Tutoring System

Combines Brain, ExamGenerator, CodeExecutor, and MemoryManager
into an adaptive learning experience.

Features:
- Interactive tutoring mode
- Adaptive difficulty scaling
- Personalized recommendations
- Session tracking and reports
- Multi-turn explanations
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from providers.brain import Brain
from providers.code_executor import CodeExecutor, DebugAnalyzer
from providers.exam_generator import ExamGenerator, Question
from providers.memory_manager import MemoryManager
from providers.tools import ToolRegistry


class DifficultyAdjustment(Enum):
    """How to adjust difficulty"""

    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"


@dataclass
class TutorSession:
    """Active tutoring session"""

    id: str
    topic: str
    initial_difficulty: int
    current_difficulty: int
    questions_asked: int
    correct_answers: int
    incorrect_answers: int
    started_at: str
    ended_at: str | None = None
    total_time_seconds: float = 0.0
    difficulty_progression: list[int] = field(default_factory=list)


@dataclass
class LearningRecommendation:
    """Personalized learning recommendation"""

    topic: str
    reason: str
    difficulty_level: int
    suggested_action: str
    confidence_score: float


@dataclass
class SessionReport:
    """Summary of learning session"""

    session_id: str
    topic: str
    total_questions: int
    correct_answers: int
    accuracy: float
    difficulty_progression: list[int]
    time_minutes: float
    recommendations: list[LearningRecommendation]
    metadata: dict[str, Any]


class TeachingSkill:
    """
    Interactive tutoring system combining all Week 1-4 components.

    Workflow:
    1. User selects topic and starting difficulty
    2. System generates adaptive questions
    3. User answers, gets feedback
    4. Difficulty adjusts based on performance
    5. Progress tracked and stored
    6. Personalized recommendations generated
    """

    def __init__(
        self,
        brain: Brain,
        exam_generator: ExamGenerator,
        memory_manager: MemoryManager,
        code_executor: CodeExecutor | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        """
        Initialize teaching skill.

        Args:
            brain: Brain for explanations
            exam_generator: Generator for questions
            memory_manager: For tracking progress
            code_executor: For code examples
            tool_registry: For tool support
        """
        self.brain = brain
        self.exam_gen = exam_generator
        self.memory = memory_manager
        self.executor = code_executor or CodeExecutor()
        self.tools = tool_registry or ToolRegistry()
        self.analyzer = DebugAnalyzer()

        self.current_session: TutorSession | None = None
        self.session_counter = 0

    async def start_session(
        self, topic: str, starting_difficulty: int = 2
    ) -> TutorSession:
        """
        Start a new learning session.

        Args:
            topic: Topic to learn
            starting_difficulty: Initial difficulty (1-5)

        Returns:
            TutorSession object
        """
        import uuid

        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.current_session = TutorSession(
            id=session_id,
            topic=topic,
            initial_difficulty=starting_difficulty,
            current_difficulty=starting_difficulty,
            questions_asked=0,
            correct_answers=0,
            incorrect_answers=0,
            started_at=datetime.now().isoformat(),
            difficulty_progression=[starting_difficulty],
        )
        self.session_counter += 1
        return self.current_session

    async def end_session(self) -> SessionReport | None:
        """End current session and generate report"""
        if not self.current_session:
            return None

        from datetime import datetime as dt

        session = self.current_session
        session.ended_at = dt.now().isoformat()

        # Calculate time
        start_time = dt.fromisoformat(session.started_at)
        end_time = dt.fromisoformat(session.ended_at)
        session.total_time_seconds = (end_time - start_time).total_seconds()

        # Record exam result
        total_q = session.questions_asked
        correct = session.correct_answers
        score = correct / total_q if total_q > 0 else 0.0

        await self.memory.record_exam(
            topic=session.topic,
            num_questions=total_q,
            difficulty=session.current_difficulty,
            score=score,
            time_taken_seconds=session.total_time_seconds,
            questions_answered=total_q,
            correct_answers=correct,
            metadata={
                "session_id": session.id,
                "initial_difficulty": session.initial_difficulty,
                "final_difficulty": session.current_difficulty,
            },
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations(session)

        # Create report
        report = SessionReport(
            session_id=session.id,
            topic=session.topic,
            total_questions=total_q,
            correct_answers=correct,
            accuracy=score,
            difficulty_progression=session.difficulty_progression
            if session.difficulty_progression
            else [session.current_difficulty],
            time_minutes=session.total_time_seconds / 60.0,
            recommendations=recommendations,
            metadata={
                "model": "tinyllama",
                "session_count": self.session_counter,
            },
        )

        self.current_session = None
        return report

    async def select_or_generate_question(
        self, topic: str, difficulty: int
    ) -> Question | None:
        """
        Get next question for topic and difficulty.

        Streaming from ExamGenerator.
        """
        async for question in self.exam_gen.stream_questions(
            topic=topic, num_questions=1, difficulty=difficulty
        ):
            return question
        return None

    async def evaluate_answer(
        self, question: Question, user_answer: str
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Evaluate user's answer and provide feedback.

        Args:
            question: The question answered
            user_answer: User's response

        Returns:
            (is_correct, feedback, details)
        """
        if not self.current_session:
            return False, "No active session", {}

        # Validate answer using brain
        validation_prompt = f"""
Question: {question.text}
Correct Answer: {question.correct_answer}
User Answer: {user_answer}

Is the user's answer correct? Respond with YES or NO, then explain.
"""

        result = await self.brain.think(validation_prompt)
        is_correct = "yes" in result.lower()[:50]

        # Generate detailed feedback
        if is_correct:
            self.current_session.correct_answers += 1
            feedback = f"✓ Correct! {question.explanation}"
        else:
            self.current_session.incorrect_answers += 1
            feedback = (
                f"✗ Incorrect.\n"
                f"Your answer: {user_answer}\n"
                f"Correct answer: {question.correct_answer}\n"
                f"Explanation: {question.explanation}"
            )

        self.current_session.questions_asked += 1

        details = {
            "is_correct": is_correct,
            "question_id": question.id,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "explanation": question.explanation,
        }

        return is_correct, feedback, details

    async def adjust_difficulty(self, recent_accuracy: float) -> int:
        """
        Adjust difficulty based on recent performance.

        Args:
            recent_accuracy: Success rate in last few questions (0.0-1.0)

        Returns:
            New difficulty level (1-5)
        """
        if not self.current_session:
            return 2

        current = self.current_session.current_difficulty

        # Difficulty adjustment logic
        if recent_accuracy >= 0.9 and current < 5:
            # Excellent - increase difficulty
            current += 1
        elif recent_accuracy <= 0.5 and current > 1:
            # Struggling - decrease difficulty
            current -= 1
        # Otherwise maintain current difficulty

        self.current_session.current_difficulty = current
        self.current_session.difficulty_progression.append(current)
        return current

    async def get_interactive_explanation(self, topic: str) -> AsyncIterator[str]:
        """
        Stream an interactive explanation on a topic.

        Args:
            topic: Topic to explain

        Yields:
            Explanation chunks as they're generated
        """
        prompt = f"""
Provide a clear, beginner-friendly explanation of: {topic}

Include:
1. Simple definition
2. Why it matters
3. Practical example
4. Common mistakes
5. Key takeaway

Keep each section concise and engaging.
"""

        async for chunk in self.brain.stream_think(prompt):
            yield chunk

    async def suggest_code_example(self, topic: str) -> str | None:
        """
        Generate executable code example for topic.

        Args:
            topic: Topic to demonstrate

        Returns:
            Executable code snippet
        """
        prompt = f"""
Generate a simple, working Python code example for: {topic}

Requirements:
- Include comments explaining each line
- Be runnable as-is
- Show the most common use case
- Keep it under 15 lines

Return ONLY the code, no explanation."""

        code = await self.brain.think(prompt)

        # Try to execute the example
        result = await self.executor.execute(code)

        if result.is_success():
            return code
        else:
            # Ask brain to fix it
            fix_prompt = f"""
This code has an error:
{code}

Error: {result.exception}

Please fix it and return the corrected code."""

            fixed_code = await self.brain.think(fix_prompt)
            return fixed_code

    async def _generate_recommendations(
        self, session: TutorSession
    ) -> list[LearningRecommendation]:
        """Generate personalized learning recommendations"""
        recommendations = []

        if session.questions_asked == 0:
            return recommendations

        accuracy = session.correct_answers / session.questions_asked

        # Recommendation 1: Difficulty adjustment
        if accuracy >= 0.85:
            recommendations.append(
                LearningRecommendation(
                    topic=session.topic,
                    reason=f"Strong performance ({accuracy:.0%})",
                    difficulty_level=min(5, session.current_difficulty + 1),
                    suggested_action="Try harder problems to challenge yourself",
                    confidence_score=0.9,
                )
            )
        elif accuracy <= 0.6:
            recommendations.append(
                LearningRecommendation(
                    topic=session.topic,
                    reason=f"Needs reinforcement ({accuracy:.0%})",
                    difficulty_level=max(1, session.current_difficulty - 1),
                    suggested_action="Review fundamentals before advancing",
                    confidence_score=0.85,
                )
            )

        # Recommendation 2: Related topics
        if session.topic == "Python":
            recommendations.append(
                LearningRecommendation(
                    topic="Data Structures",
                    reason="Natural next step after Python fundamentals",
                    difficulty_level=2,
                    suggested_action="Learn lists, dicts, sets after mastering syntax",
                    confidence_score=0.75,
                )
            )

        # Recommendation 3: Practice
        recommendations.append(
            LearningRecommendation(
                topic=session.topic,
                reason="Spaced repetition improves retention",
                difficulty_level=session.current_difficulty,
                suggested_action="Practice again tomorrow to reinforce learning",
                confidence_score=0.8,
            )
        )

        return recommendations

    async def get_session_progress(self) -> dict[str, Any] | None:
        """Get current session progress"""
        if not self.current_session:
            return None

        session = self.current_session
        total = session.questions_asked
        accuracy = session.correct_answers / total if total > 0 else 0.0

        return {
            "session_id": session.id,
            "topic": session.topic,
            "questions_asked": total,
            "correct": session.correct_answers,
            "accuracy": accuracy,
            "current_difficulty": session.current_difficulty,
            "progress_bar": self._create_progress_bar(accuracy),
        }

    def _create_progress_bar(self, accuracy: float, width: int = 20) -> str:
        """Create ASCII progress bar"""
        filled = int(width * accuracy)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {accuracy:.0%}"


class AdaptiveTutorSession:
    """
    Manages a multi-turn adaptive learning session with streaming responses.
    """

    def __init__(self, skill: TeachingSkill):
        """Initialize adaptive session manager"""
        self.skill = skill
        self.session: TutorSession | None = None

    async def start(self, topic: str, difficulty: int = 2) -> TutorSession:
        """Start new session"""
        self.session = await self.skill.start_session(topic, difficulty)
        return self.session

    async def ask_question(self) -> Question | None:
        """Get next question"""
        if not self.session:
            return None

        question = await self.skill.select_or_generate_question(
            self.session.topic, self.session.current_difficulty
        )
        return question

    async def submit_answer(self, question: Question, answer: str) -> dict[str, Any]:
        """Submit answer and get feedback"""
        is_correct, feedback, details = await self.skill.evaluate_answer(
            question, answer
        )

        # Calculate recent accuracy for 5 last questions
        session = self.skill.current_session
        if session and session.questions_asked >= 5:
            recent = session.correct_answers / session.questions_asked
        else:
            recent = 0.5  # Default

        # Adjust difficulty if needed
        if session and session.questions_asked % 3 == 0:
            new_difficulty = await self.skill.adjust_difficulty(recent)
            details["difficulty_adjusted"] = new_difficulty

        return {
            "is_correct": is_correct,
            "feedback": feedback,
            "details": details,
        }

    async def end(self) -> SessionReport | None:
        """End session and get report"""
        report = await self.skill.end_session()
        self.session = None
        return report

    async def explain_topic(self) -> AsyncIterator[str]:
        """Stream explanation of current topic"""
        if not self.session:
            return

        async for chunk in self.skill.get_interactive_explanation(self.session.topic):
            yield chunk

    async def get_example(self) -> str | None:
        """Get code example"""
        if not self.session:
            return None

        return await self.skill.suggest_code_example(self.session.topic)
