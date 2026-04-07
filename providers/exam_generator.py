"""
Exam Generator System
Generates interactive exams with progressive streaming of questions
"""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Type of question"""

    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    TRUE_FALSE = "true_false"
    CODE = "code"


@dataclass
class Question:
    """Represents a single exam question"""

    id: int
    text: str
    question_type: QuestionType
    options: list[str] = field(default_factory=list)  # For multiple choice
    correct_answer: str = ""
    difficulty: int = 3  # 1-5, where 5 is hardest
    explanation: str = ""
    topic: str = ""
    estimated_time_seconds: int = 60

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "text": self.text,
            "type": self.question_type.value,
            "options": self.options,
            "difficulty": self.difficulty,
            "time_estimate": self.estimated_time_seconds,
            "topic": self.topic,
        }


@dataclass
class AnswerResult:
    """Result of answer validation"""

    is_correct: bool
    score: float  # 0.0-1.0
    feedback: str
    explanation: str
    time_taken_seconds: float = 0.0


@dataclass
class ExamSession:
    """Tracks exam progress"""

    exam_id: str
    topic: str
    difficulty: int
    questions: list[Question] = field(default_factory=list)
    answers: list[tuple[int, str]] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)

    @property
    def score(self) -> float:
        """Average score"""
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)

    @property
    def progress(self) -> tuple[int, int]:
        """(completed, total)"""
        return (len(self.answers), len(self.questions))


class ExamGenerator:
    """Generates and manages exams"""

    # Difficulty descriptions for prompting
    DIFFICULTY_PROMPTS = {
        1: "very basic, suitable for beginners",
        2: "basic, testing fundamental understanding",
        3: "intermediate, testing practical knowledge",
        4: "advanced, testing deep understanding",
        5: "expert-level, testing edge cases and advanced concepts",
    }

    # Estimated time per difficulty
    TIME_ESTIMATES = {
        1: 30,  # Very easy = 30 seconds
        2: 45,  # Easy = 45 seconds
        3: 60,  # Medium = 60 seconds
        4: 90,  # Hard = 90 seconds
        5: 120,  # Very hard = 2 minutes
    }

    def __init__(self, brain):
        """
        Initialize exam generator.

        Args:
            brain: Brain instance for generating questions
        """
        self.brain = brain
        logger.info("ExamGenerator initialized")

    async def generate_exam(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: int = 3,
    ) -> ExamSession:
        """
        Generate a complete exam session.

        Args:
            topic: Exam topic (e.g., "Python basics", "REST APIs")
            num_questions: Number of questions (default 5)
            difficulty: Difficulty level 1-5 (default 3 = medium)

        Returns:
            ExamSession with all questions loaded
        """
        if not 1 <= difficulty <= 5:
            difficulty = 3

        # Create session
        import uuid

        exam_id = str(uuid.uuid4())[:8]
        session = ExamSession(
            exam_id=exam_id,
            topic=topic,
            difficulty=difficulty,
        )

        logger.info(
            f"Generating exam: {topic}, {num_questions} Q, difficulty {difficulty}/5"
        )

        # Generate questions
        async for question in self.stream_questions(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
        ):
            session.questions.append(question)

        return session

    async def stream_questions(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: int = 3,
    ) -> AsyncIterator[Question]:
        """
        Stream questions one by one as they're generated.

        Args:
            topic: Exam topic
            num_questions: Number of questions to generate
            difficulty: Difficulty level 1-5

        Yields:
            Question objects as they're generated
        """
        difficulty_desc = self.DIFFICULTY_PROMPTS.get(difficulty, "medium")

        # Prompt for batch generation
        prompt = f"""Generate exactly {num_questions} exam questions about "{topic}".

Requirements:
- Difficulty: {difficulty_desc}
- Mix of question types: multiple choice, short answer, or code questions
- Each question should be independent
- Include clear, specific correct answers
- Provide brief explanations

Format each question as JSON on its own line:
{{"id": 1, "text": "...", "type": "multiple_choice", "options": [...], "correct": "...", "explanation": "..."}}

Generate the questions now:"""

        logger.debug(f"Streaming questions for: {topic}")

        question_count = 0
        async for chunk in self.brain.stream_think(prompt):
            # Try to parse complete JSON objects from the stream
            lines = chunk.strip().split("\n")
            for line in lines:
                if line.strip().startswith("{"):
                    try:
                        data = json.loads(line)
                        question = self._parse_question_json(
                            data, question_count + 1, topic, difficulty
                        )
                        if question:
                            question_count += 1
                            yield question

                            # Stop at num_questions
                            if question_count >= num_questions:
                                return
                    except json.JSONDecodeError:
                        # Not a complete JSON yet, continue accumulating
                        pass

    def _parse_question_json(
        self,
        data: dict,
        question_id: int,
        topic: str,
        difficulty: int,
    ) -> Question | None:
        """
        Parse question from JSON data.

        Args:
            data: Dictionary from parsed JSON
            question_id: Question number
            topic: Exam topic
            difficulty: Difficulty level

        Returns:
            Question object or None if parsing failed
        """
        try:
            question_type = data.get("type", "short_answer").lower()

            # Map type string to enum
            type_map = {
                "multiple_choice": QuestionType.MULTIPLE_CHOICE,
                "short_answer": QuestionType.SHORT_ANSWER,
                "true_false": QuestionType.TRUE_FALSE,
                "code": QuestionType.CODE,
            }

            q_type = type_map.get(question_type, QuestionType.SHORT_ANSWER)

            question = Question(
                id=question_id,
                text=data.get("text", ""),
                question_type=q_type,
                options=data.get("options", []),
                correct_answer=data.get("correct", ""),
                difficulty=difficulty,
                explanation=data.get("explanation", ""),
                topic=topic,
                estimated_time_seconds=self.TIME_ESTIMATES.get(difficulty, 60),
            )

            return question if question.text else None

        except Exception as e:
            logger.warning(f"Failed to parse question: {e}")
            return None

    async def validate_answer(
        self,
        question: Question,
        user_answer: str,
        time_taken_seconds: float = 0.0,
    ) -> AnswerResult:
        """
        Validate user's answer to a question.

        Args:
            question: The question being answered
            user_answer: User's answer text
            time_taken_seconds: How long the user took

        Returns:
            AnswerResult with score and feedback
        """
        logger.debug(f"Validating answer for Q{question.id}: {user_answer[:50]}...")

        # Use Brain to score the answer
        validation_prompt = f"""Evaluate if this answer is correct for the question.

Question: {question.text}
Correct Answer: {question.correct_answer}
User Answer: {user_answer}

Respond in JSON format:
{{"is_correct": true/false, "score": 0.0-1.0, "feedback": "brief feedback"}}"""

        response = await self.brain.think(validation_prompt)

        try:
            # Try to parse JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback: simple comparison
                is_correct = (
                    user_answer.lower().strip()
                    == question.correct_answer.lower().strip()
                )
                data = {
                    "is_correct": is_correct,
                    "score": 1.0 if is_correct else 0.0,
                    "feedback": "Correct!" if is_correct else "Incorrect",
                }

            return AnswerResult(
                is_correct=data.get("is_correct", False),
                score=float(data.get("score", 0.0)),
                feedback=data.get("feedback", ""),
                explanation=question.explanation,
                time_taken_seconds=time_taken_seconds,
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            # Fallback to simple comparison
            is_correct = (
                user_answer.lower().strip() == question.correct_answer.lower().strip()
            )
            return AnswerResult(
                is_correct=is_correct,
                score=1.0 if is_correct else 0.0,
                feedback="Could not validate",
                explanation=question.explanation,
                time_taken_seconds=time_taken_seconds,
            )

    def get_session_stats(self, session: ExamSession) -> dict:
        """Get statistics for a completed exam"""
        return {
            "exam_id": session.exam_id,
            "topic": session.topic,
            "total_questions": len(session.questions),
            "questions_answered": len(session.answers),
            "average_score": session.score,
            "difficulty": session.difficulty,
            "scores": session.scores,
        }
