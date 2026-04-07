"""
Week 4 Memory System - Persistent Storage for Learning & Code

Extends Week 1-3 with:
- Exam result storage and progress tracking
- Code snippet persistence and statistics
- Conversation history
- Query and analytics system
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class StorageType(Enum):
    """Storage backend type"""

    JSON = "json"
    SQLITE = "sqlite"


@dataclass
class ExamRecord:
    """Stored exam result"""

    id: str
    timestamp: str
    topic: str
    num_questions: int
    difficulty: int
    score: float
    time_taken_seconds: float
    questions_answered: int
    correct_answers: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SnippetRecord:
    """Stored code snippet with history"""

    id: str
    code: str
    language: str
    created_at: str
    last_executed: Optional[str]
    execution_count: int
    success_count: int
    description: str
    tags: list[str]
    metadata: dict[str, Any]

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ConversationMessage:
    """Single message in conversation history"""

    id: str
    timestamp: str
    role: str  # "user" or "assistant"
    content: str
    intent: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        return asdict(self)


class MemoryStore:
    """
    Unified memory storage for all Week 1-4 systems.

    Stores:
    - Exam results and progress
    - Code snippets and execution history
    - Conversation history
    - User preferences and patterns
    """

    def __init__(self, storage_dir: str = "./.jarvis_memory"):
        """
        Initialize memory store.

        Args:
            storage_dir: Directory for memory files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # Storage files
        self.exams_file = self.storage_dir / "exams.json"
        self.snippets_file = self.storage_dir / "snippets.json"
        self.conversations_file = self.storage_dir / "conversations.json"
        self.metadata_file = self.storage_dir / "metadata.json"

        # In-memory caches
        self._exams: dict[str, ExamRecord] = {}
        self._snippets: dict[str, SnippetRecord] = {}
        self._conversations: list[ConversationMessage] = []

        self._load_all()

    def _load_all(self):
        """Load all data from storage"""
        self._load_exams()
        self._load_snippets()
        self._load_conversations()

    def _load_exams(self):
        """Load exam records"""
        if self.exams_file.exists():
            try:
                data = json.loads(self.exams_file.read_text())
                for exam_data in data:
                    record = ExamRecord(**exam_data)
                    self._exams[record.id] = record
            except Exception as e:
                print(f"Warning: Failed to load exams: {e}")

    def _load_snippets(self):
        """Load code snippets"""
        if self.snippets_file.exists():
            try:
                data = json.loads(self.snippets_file.read_text())
                for snippet_data in data:
                    record = SnippetRecord(**snippet_data)
                    self._snippets[record.id] = record
            except Exception as e:
                print(f"Warning: Failed to load snippets: {e}")

    def _load_conversations(self):
        """Load conversation history"""
        if self.conversations_file.exists():
            try:
                data = json.loads(self.conversations_file.read_text())
                self._conversations = [
                    ConversationMessage(**msg_data) for msg_data in data
                ]
            except Exception as e:
                print(f"Warning: Failed to load conversations: {e}")

    def _save_all(self):
        """Save all data to storage"""
        self._save_exams()
        self._save_snippets()
        self._save_conversations()

    def _save_exams(self):
        """Save exam records"""
        data = [record.to_dict() for record in self._exams.values()]
        self.exams_file.write_text(json.dumps(data, indent=2))

    def _save_snippets(self):
        """Save code snippets"""
        data = [record.to_dict() for record in self._snippets.values()]
        self.snippets_file.write_text(json.dumps(data, indent=2))

    def _save_conversations(self):
        """Save conversation history"""
        data = [msg.to_dict() for msg in self._conversations]
        self.conversations_file.write_text(json.dumps(data, indent=2))

    async def store_exam(self, exam_record: ExamRecord) -> None:
        """Store exam result"""
        self._exams[exam_record.id] = exam_record
        self._save_all()

    async def get_exam(self, exam_id: str) -> Optional[ExamRecord]:
        """Retrieve exam by ID"""
        return self._exams.get(exam_id)

    async def list_exams(
        self, topic: Optional[str] = None, limit: int = 10
    ) -> list[ExamRecord]:
        """List exams with optional filtering"""
        exams = list(self._exams.values())

        if topic:
            exams = [e for e in exams if e.topic.lower() == topic.lower()]

        # Sort by timestamp descending
        exams.sort(key=lambda e: e.timestamp, reverse=True)
        return exams[:limit]

    async def store_snippet(self, snippet_record: SnippetRecord) -> None:
        """Store code snippet"""
        self._snippets[snippet_record.id] = snippet_record
        self._save_all()

    async def get_snippet(self, snippet_id: str) -> Optional[SnippetRecord]:
        """Retrieve snippet by ID"""
        return self._snippets.get(snippet_id)

    async def list_snippets(
        self, tag: Optional[str] = None, limit: int = 20
    ) -> list[SnippetRecord]:
        """List snippets with optional tag filter"""
        snippets = list(self._snippets.values())

        if tag:
            snippets = [s for s in snippets if tag in s.tags]

        # Sort by last_executed desc (most recent first)
        snippets.sort(key=lambda s: s.last_executed or s.created_at, reverse=True)
        return snippets[:limit]

    async def add_message(self, message: ConversationMessage) -> None:
        """Add message to conversation history"""
        self._conversations.append(message)
        self._save_all()

    async def get_conversation_history(
        self, last_n: int = 20, intent: Optional[str] = None
    ) -> list[ConversationMessage]:
        """Get conversation history"""
        messages = self._conversations

        if intent:
            messages = [m for m in messages if m.intent == intent]

        return messages[-last_n:] if len(messages) > last_n else messages

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics"""
        return {
            "exams_total": len(self._exams),
            "snippets_total": len(self._snippets),
            "messages_total": len(self._conversations),
            "storage_dir": str(self.storage_dir),
            "exams_file_size": self.exams_file.stat().st_size
            if self.exams_file.exists()
            else 0,
            "snippets_file_size": self.snippets_file.stat().st_size
            if self.snippets_file.exists()
            else 0,
            "conversations_file_size": self.conversations_file.stat().st_size
            if self.conversations_file.exists()
            else 0,
        }


class AnalyticsEngine:
    """
    Analyze stored data to provide insights and recommendations.

    Features:
    - Learning progress tracking
    - Skill identification
    - Code quality metrics
    - Performance trends
    """

    def __init__(self, memory_store: MemoryStore):
        """Initialize analytics engine"""
        self.store = memory_store

    async def get_exam_stats(self, topic: Optional[str] = None) -> dict[str, Any]:
        """
        Get exam statistics.

        Args:
            topic: Optional topic to filter

        Returns:
            Dictionary with stats
        """
        exams = await self.store.list_exams(topic=topic, limit=1000)

        if not exams:
            return {
                "total_exams": 0,
                "average_score": 0.0,
                "best_score": 0.0,
                "worst_score": 0.0,
            }

        scores = [e.score for e in exams]
        times = [e.time_taken_seconds for e in exams]

        return {
            "total_exams": len(exams),
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_time_seconds": sum(times) / len(times),
            "total_time_seconds": sum(times),
            "score_trend": self._calculate_trend(scores),
            "recent_avg": sum(scores[-5:]) / len(scores[-5:])
            if len(scores) >= 5
            else sum(scores) / len(scores),
        }

    async def get_skill_assessment(self) -> dict[str, Any]:
        """
        Assess learning progress across topics.

        Returns:
            Dictionary mapping topics to performance
        """
        exams = await self.store.list_exams(limit=1000)

        topics: dict[str, list[float]] = {}
        for exam in exams:
            if exam.topic not in topics:
                topics[exam.topic] = []
            topics[exam.topic].append(exam.score)

        assessment = {}
        for topic, scores in topics.items():
            avg_score = sum(scores) / len(scores)
            assessment[topic] = {
                "attempts": len(scores),
                "average_score": avg_score,
                "level": self._score_to_level(avg_score),
                "trend": self._calculate_trend(scores),
            }

        return assessment

    async def get_code_stats(self) -> dict[str, Any]:
        """
        Get code snippet statistics.

        Returns:
            Dictionary with code metrics
        """
        snippets = await self.store.list_snippets(limit=1000)

        if not snippets:
            return {
                "total_snippets": 0,
                "average_success_rate": 0.0,
                "languages": {},
            }

        success_rates = [s.success_rate() for s in snippets]
        languages: dict[str, int] = {}
        for snippet in snippets:
            lang = snippet.language
            languages[lang] = languages.get(lang, 0) + 1

        return {
            "total_snippets": len(snippets),
            "average_success_rate": sum(success_rates) / len(success_rates),
            "best_success_rate": max(success_rates),
            "worst_success_rate": min(success_rates),
            "languages": languages,
            "most_executed": max([s.execution_count for s in snippets]),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return "insufficient_data"

        recent = values[-5:] if len(values) >= 5 else values
        older = values[: max(0, len(values) - 5)]

        if not older:
            return "new"

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg * 1.1:
            return "improving"
        elif recent_avg < older_avg * 0.9:
            return "declining"
        else:
            return "stable"

    def _score_to_level(self, score: float) -> str:
        """Convert score to proficiency level"""
        if score >= 0.9:
            return "expert"
        elif score >= 0.8:
            return "advanced"
        elif score >= 0.7:
            return "intermediate"
        elif score >= 0.6:
            return "beginner"
        else:
            return "novice"


class MemoryManager:
    """
    Orchestrates memory system integration with Brain, ExamGenerator, and
    CodeExecutor.

    Coordinates:
    - Storing exam results
    - Storing code snippets
    - Recording conversations
    - Providing historical context
    """

    def __init__(self, storage_dir: str = "./.jarvis_memory"):
        """Initialize memory manager"""
        self.store = MemoryStore(storage_dir)
        self.analytics = AnalyticsEngine(self.store)
        self.msg_counter = 0

    async def record_exam(
        self,
        topic: str,
        num_questions: int,
        difficulty: int,
        score: float,
        time_taken_seconds: float,
        questions_answered: int,
        correct_answers: int,
        metadata: Optional[dict] = None,
    ) -> ExamRecord:
        """Record exam result"""
        from datetime import datetime
        import uuid

        exam_id = f"exam_{uuid.uuid4().hex[:8]}"
        record = ExamRecord(
            id=exam_id,
            timestamp=datetime.now().isoformat(),
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            score=score,
            time_taken_seconds=time_taken_seconds,
            questions_answered=questions_answered,
            correct_answers=correct_answers,
            metadata=metadata or {},
        )
        await self.store.store_exam(record)
        return record

    async def record_snippet(
        self,
        id: str,
        code: str,
        language: str,
        description: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> SnippetRecord:
        """Record code snippet"""
        from datetime import datetime

        record = SnippetRecord(
            id=id,
            code=code,
            language=language,
            created_at=datetime.now().isoformat(),
            last_executed=None,
            execution_count=0,
            success_count=0,
            description=description,
            tags=tags or [],
            metadata=metadata or {},
        )
        await self.store.store_snippet(record)
        return record

    async def update_snippet_execution(
        self, snippet_id: str, success: bool
    ) -> Optional[SnippetRecord]:
        """Update snippet after execution"""
        snippet = await self.store.get_snippet(snippet_id)
        if snippet:
            from datetime import datetime

            snippet.last_executed = datetime.now().isoformat()
            snippet.execution_count += 1
            if success:
                snippet.success_count += 1
            await self.store.store_snippet(snippet)
        return snippet

    async def record_conversation(
        self,
        role: str,
        content: str,
        intent: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Record conversation message"""
        from datetime import datetime
        import uuid

        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        message = ConversationMessage(
            id=msg_id,
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            intent=intent,
            model=model,
            metadata=metadata or {},
        )
        await self.store.add_message(message)
        return message

    async def get_learning_summary(self) -> dict[str, Any]:
        """Get overall learning summary"""
        exam_stats = await self.analytics.get_exam_stats()
        skill_assessment = await self.analytics.get_skill_assessment()
        code_stats = await self.analytics.get_code_stats()
        storage_stats = await self.store.get_storage_stats()

        return {
            "exam_statistics": exam_stats,
            "skill_assessment": skill_assessment,
            "code_statistics": code_stats,
            "storage": storage_stats,
        }
