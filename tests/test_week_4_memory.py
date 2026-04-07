"""
Comprehensive tests for Week 4 Memory System

Tests MemoryStore, AnalyticsEngine, and MemoryManager.
"""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from providers.memory_manager import (
    ExamRecord,
    SnippetRecord,
    ConversationMessage,
    MemoryStore,
    AnalyticsEngine,
    MemoryManager,
)


class TestExamRecord:
    """Test exam record dataclass"""

    def test_exam_record_creation(self):
        """Test creating exam record"""
        record = ExamRecord(
            id="exam_001",
            timestamp=datetime.now().isoformat(),
            topic="Python",
            num_questions=5,
            difficulty=3,
            score=0.85,
            time_taken_seconds=120.5,
            questions_answered=5,
            correct_answers=4,
            metadata={"model": "tinyllama"},
        )

        assert record.id == "exam_001"
        assert record.topic == "Python"
        assert record.score == 0.85

    def test_exam_record_to_dict(self):
        """Test converting record to dict"""
        record = ExamRecord(
            id="exam_001",
            timestamp="2026-04-07T10:00:00",
            topic="Python",
            num_questions=5,
            difficulty=3,
            score=0.85,
            time_taken_seconds=120.5,
            questions_answered=5,
            correct_answers=4,
            metadata={},
        )

        record_dict = record.to_dict()
        assert record_dict["id"] == "exam_001"
        assert record_dict["score"] == 0.85


class TestSnippetRecord:
    """Test code snippet record"""

    def test_snippet_record_creation(self):
        """Test creating snippet record"""
        record = SnippetRecord(
            id="snippet_001",
            code="print('hello')",
            language="python",
            created_at=datetime.now().isoformat(),
            last_executed=None,
            execution_count=0,
            success_count=0,
            description="Hello world",
            tags=["intro"],
            metadata={},
        )

        assert record.id == "snippet_001"
        assert record.language == "python"

    def test_snippet_success_rate(self):
        """Test success rate calculation"""
        record = SnippetRecord(
            id="snippet_001",
            code="code",
            language="python",
            created_at="2026-04-07T10:00:00",
            last_executed=None,
            execution_count=10,
            success_count=8,
            description="test",
            tags=[],
            metadata={},
        )

        assert record.success_rate() == 80.0

    def test_snippet_success_rate_zero(self):
        """Test success rate with no executions"""
        record = SnippetRecord(
            id="snippet_001",
            code="code",
            language="python",
            created_at="2026-04-07T10:00:00",
            last_executed=None,
            execution_count=0,
            success_count=0,
            description="test",
            tags=[],
            metadata={},
        )

        assert record.success_rate() == 0.0


class TestConversationMessage:
    """Test conversation message"""

    def test_message_creation(self):
        """Test creating message"""
        msg = ConversationMessage(
            id="msg_001",
            timestamp=datetime.now().isoformat(),
            role="user",
            content="What is Python?",
            intent="TEACHING",
            model="tinyllama",
        )

        assert msg.role == "user"
        assert msg.intent == "TEACHING"

    def test_message_to_dict(self):
        """Test converting message to dict"""
        msg = ConversationMessage(
            id="msg_001",
            timestamp="2026-04-07T10:00:00",
            role="assistant",
            content="Python is...",
        )

        msg_dict = msg.to_dict()
        assert msg_dict["role"] == "assistant"
        assert msg_dict["content"] == "Python is..."


class TestMemoryStore:
    """Test memory store functionality"""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_store_and_retrieve_exam(self, temp_storage):
        """Test storing and retrieving exam"""
        store = MemoryStore(temp_storage)

        exam = ExamRecord(
            id="exam_001",
            timestamp=datetime.now().isoformat(),
            topic="Python",
            num_questions=5,
            difficulty=3,
            score=0.85,
            time_taken_seconds=120.0,
            questions_answered=5,
            correct_answers=4,
            metadata={},
        )

        await store.store_exam(exam)
        retrieved = await store.get_exam("exam_001")

        assert retrieved is not None
        assert retrieved.score == 0.85

    @pytest.mark.asyncio
    async def test_list_exams(self, temp_storage):
        """Test listing exams"""
        store = MemoryStore(temp_storage)

        for i in range(3):
            exam = ExamRecord(
                id=f"exam_{i:03d}",
                timestamp=datetime.now().isoformat(),
                topic="Python" if i < 2 else "JavaScript",
                num_questions=5,
                difficulty=3,
                score=0.7 + (i * 0.05),
                time_taken_seconds=120.0,
                questions_answered=5,
                correct_answers=3 + i,
                metadata={},
            )
            await store.store_exam(exam)

        all_exams = await store.list_exams(limit=10)
        assert len(all_exams) == 3

        python_exams = await store.list_exams(topic="Python", limit=10)
        assert len(python_exams) == 2

    @pytest.mark.asyncio
    async def test_store_and_retrieve_snippet(self, temp_storage):
        """Test storing and retrieving snippet"""
        store = MemoryStore(temp_storage)

        snippet = SnippetRecord(
            id="snippet_001",
            code="print('test')",
            language="python",
            created_at=datetime.now().isoformat(),
            last_executed=None,
            execution_count=0,
            success_count=0,
            description="Test snippet",
            tags=["test"],
            metadata={},
        )

        await store.store_snippet(snippet)
        retrieved = await store.get_snippet("snippet_001")

        assert retrieved is not None
        assert retrieved.code == "print('test')"

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, temp_storage):
        """Test storing and retrieving messages"""
        store = MemoryStore(temp_storage)

        msg1 = ConversationMessage(
            id="msg_001",
            timestamp=datetime.now().isoformat(),
            role="user",
            content="Hello",
        )
        msg2 = ConversationMessage(
            id="msg_002",
            timestamp=datetime.now().isoformat(),
            role="assistant",
            content="Hi there",
        )

        await store.add_message(msg1)
        await store.add_message(msg2)

        history = await store.get_conversation_history(last_n=10)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_storage_stats(self, temp_storage):
        """Test getting storage statistics"""
        store = MemoryStore(temp_storage)

        exam = ExamRecord(
            id="exam_001",
            timestamp=datetime.now().isoformat(),
            topic="Python",
            num_questions=5,
            difficulty=3,
            score=0.85,
            time_taken_seconds=120.0,
            questions_answered=5,
            correct_answers=4,
            metadata={},
        )
        await store.store_exam(exam)

        stats = await store.get_storage_stats()
        assert stats["exams_total"] == 1
        assert stats["snippets_total"] == 0


class TestAnalyticsEngine:
    """Test analytics engine"""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_exam_stats(self, temp_storage):
        """Test exam statistics"""
        store = MemoryStore(temp_storage)
        analytics = AnalyticsEngine(store)

        for i in range(5):
            exam = ExamRecord(
                id=f"exam_{i:03d}",
                timestamp=datetime.now().isoformat(),
                topic="Python",
                num_questions=5,
                difficulty=3,
                score=0.7 + (i * 0.04),
                time_taken_seconds=120.0,
                questions_answered=5,
                correct_answers=3 + i,
                metadata={},
            )
            await store.store_exam(exam)

        stats = await analytics.get_exam_stats()

        assert stats["total_exams"] == 5
        assert stats["average_score"] > 0.7
        assert stats["best_score"] >= stats["worst_score"]

    @pytest.mark.asyncio
    async def test_skill_assessment(self, temp_storage):
        """Test skill assessment"""
        store = MemoryStore(temp_storage)
        analytics = AnalyticsEngine(store)

        topics = ["Python", "JavaScript", "Python"]
        for i, topic in enumerate(topics):
            exam = ExamRecord(
                id=f"exam_{i:03d}",
                timestamp=datetime.now().isoformat(),
                topic=topic,
                num_questions=5,
                difficulty=3,
                score=0.8 if topic == "Python" else 0.6,
                time_taken_seconds=120.0,
                questions_answered=5,
                correct_answers=4 if topic == "Python" else 3,
                metadata={},
            )
            await store.store_exam(exam)

        assessment = await analytics.get_skill_assessment()

        assert "Python" in assessment
        assert "JavaScript" in assessment
        assert assessment["Python"]["attempts"] == 2
        assert assessment["JavaScript"]["attempts"] == 1

    @pytest.mark.asyncio
    async def test_code_stats(self, temp_storage):
        """Test code statistics"""
        store = MemoryStore(temp_storage)
        analytics = AnalyticsEngine(store)

        for i in range(3):
            snippet = SnippetRecord(
                id=f"snippet_{i:03d}",
                code="code",
                language="python" if i < 2 else "javascript",
                created_at=datetime.now().isoformat(),
                last_executed=None,
                execution_count=10,
                success_count=8 + i,
                description="test",
                tags=[],
                metadata={},
            )
            await store.store_snippet(snippet)

        stats = await analytics.get_code_stats()

        assert stats["total_snippets"] == 3
        assert stats["languages"]["python"] == 2
        assert stats["languages"]["javascript"] == 1


class TestMemoryManager:
    """Test memory manager orchestration"""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_record_exam(self, temp_storage):
        """Test recording exam"""
        manager = MemoryManager(temp_storage)

        record = await manager.record_exam(
            topic="Python",
            num_questions=5,
            difficulty=3,
            score=0.85,
            time_taken_seconds=120.0,
            questions_answered=5,
            correct_answers=4,
        )

        assert record.id is not None
        assert record.topic == "Python"
        assert record.score == 0.85

    @pytest.mark.asyncio
    async def test_record_snippet(self, temp_storage):
        """Test recording snippet"""
        manager = MemoryManager(temp_storage)

        record = await manager.record_snippet(
            id="snippet_001",
            code="print('hello')",
            language="python",
            description="Hello world",
            tags=["intro"],
        )

        assert record.id == "snippet_001"
        assert record.execution_count == 0

    @pytest.mark.asyncio
    async def test_update_snippet_execution(self, temp_storage):
        """Test updating snippet after execution"""
        manager = MemoryManager(temp_storage)

        await manager.record_snippet(
            id="snippet_001",
            code="code",
            language="python",
            description="test",
        )

        # Update stats
        snippet = await manager.update_snippet_execution("snippet_001", success=True)

        assert snippet is not None
        assert snippet.execution_count == 1
        assert snippet.success_count == 1

    @pytest.mark.asyncio
    async def test_record_conversation(self, temp_storage):
        """Test recording conversation"""
        manager = MemoryManager(temp_storage)

        msg = await manager.record_conversation(
            role="user",
            content="What is Python?",
            intent="TEACHING",
            model="tinyllama",
        )

        assert msg.role == "user"
        assert msg.intent == "TEACHING"

    @pytest.mark.asyncio
    async def test_learning_summary(self, temp_storage):
        """Test getting learning summary"""
        manager = MemoryManager(temp_storage)

        # Record some data
        await manager.record_exam(
            topic="Python",
            num_questions=5,
            difficulty=3,
            score=0.85,
            time_taken_seconds=120.0,
            questions_answered=5,
            correct_answers=4,
        )

        await manager.record_snippet(
            id="snippet_001",
            code="code",
            language="python",
            description="test",
        )

        summary = await manager.get_learning_summary()

        assert "exam_statistics" in summary
        assert "skill_assessment" in summary
        assert "code_statistics" in summary
        assert summary["exam_statistics"]["total_exams"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
