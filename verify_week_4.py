"""
Week 4 Verification Script

Validates all memory system components.
"""

import asyncio
import sys
import tempfile


async def main():
    print("=" * 70)
    print("WEEK 4 MEMORY SYSTEM VERIFICATION")
    print("=" * 70)
    print()

    # Step 1: Import components
    print("[1/5] Importing components...")
    try:
        from providers.memory_manager import (
            MemoryStore,
            AnalyticsEngine,
            MemoryManager,
            ExamRecord,
            SnippetRecord,
            ConversationMessage,
        )

        print("✓ All components imported")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    print()

    # Step 2: Create instances
    print("[2/5] Creating instances...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(tmpdir)
            analytics = AnalyticsEngine(store)
            manager = MemoryManager(tmpdir)
            print("✓ MemoryStore created")
            print("✓ AnalyticsEngine created")
            print("✓ MemoryManager created")
    except Exception as e:
        print(f"✗ Instance creation failed: {e}")
        return False
    print()

    # Step 3: Test data structures
    print("[3/5] Testing data structures...")
    try:
        from datetime import datetime

        exam = ExamRecord(
            id="test_exam",
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
        print("✓ ExamRecord created")

        snippet = SnippetRecord(
            id="test_snippet",
            code="print('test')",
            language="python",
            created_at=datetime.now().isoformat(),
            last_executed=None,
            execution_count=0,
            success_count=0,
            description="Test",
            tags=["test"],
            metadata={},
        )
        print("✓ SnippetRecord created")

        msg = ConversationMessage(
            id="test_msg",
            timestamp=datetime.now().isoformat(),
            role="user",
            content="Test message",
        )
        print("✓ ConversationMessage created")

    except Exception as e:
        print(f"✗ Data structure test failed: {e}")
        return False
    print()

    # Step 4: Test storage and retrieval
    print("[4/5] Testing storage and retrieval...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(tmpdir)

            # Record exam
            exam_record = await manager.record_exam(
                topic="Python",
                num_questions=5,
                difficulty=3,
                score=0.85,
                time_taken_seconds=120.0,
                questions_answered=5,
                correct_answers=4,
            )
            print("✓ Exam recorded")

            # Record snippet
            snippet_record = await manager.record_snippet(
                id="snippet_001",
                code="print('hello')",
                language="python",
                description="Hello world",
                tags=["intro"],
            )
            print("✓ Snippet recorded")

            # Record conversation
            msg = await manager.record_conversation(
                role="user",
                content="What is Python?",
                intent="TEACHING",
                model="tinyllama",
            )
            print("✓ Message recorded")

            # Update snippet execution
            await manager.update_snippet_execution("snippet_001", success=True)
            print("✓ Snippet stats updated")

    except Exception as e:
        print(f"✗ Storage test failed: {e}")
        return False
    print()

    # Step 5: Test analytics
    print("[5/5] Testing analytics...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(tmpdir)

            # Record multiple exams
            for i in range(3):
                await manager.record_exam(
                    topic="Python",
                    num_questions=5,
                    difficulty=3,
                    score=0.7 + (i * 0.05),
                    time_taken_seconds=120.0,
                    questions_answered=5,
                    correct_answers=3 + i,
                )

            # Get summary
            summary = await manager.get_learning_summary()

            assert summary["exam_statistics"]["total_exams"] == 3
            print("✓ Analytics working")
            print("✓ Learning summary generated")

    except Exception as e:
        print(f"✗ Analytics test failed: {e}")
        return False
    print()

    print("=" * 70)
    print("✓ WEEK 4 ALL SYSTEMS OPERATIONAL")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
