"""
Week 4 Memory System Example

Demonstrates persistent storage, analytics, and learning tracking.
"""

import asyncio
import tempfile
from datetime import datetime

from providers.memory_manager import MemoryManager


async def main():
    print("=" * 70)
    print("WEEK 4 MEMORY SYSTEM DEMO")
    print("=" * 70)
    print()

    # Create temporary storage for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MemoryManager(tmpdir)

        # ===== Example 1: Recording Exam Results =====
        print("[Example 1] Recording Exam Results")
        print("-" * 70)

        exam1 = await manager.record_exam(
            topic="Python Fundamentals",
            num_questions=5,
            difficulty=2,
            score=0.8,
            time_taken_seconds=300.0,
            questions_answered=5,
            correct_answers=4,
            metadata={"model": "tinyllama", "mode": "teaching"},
        )
        print(f"✓ Exam recorded: {exam1.id}")
        print(
            f"  Topic: {exam1.topic} | Score: {exam1.score:.0%} | Difficulty: {exam1.difficulty}"
        )

        exam2 = await manager.record_exam(
            topic="Python Fundamentals",
            num_questions=5,
            difficulty=3,
            score=0.9,
            time_taken_seconds=280.0,
            questions_answered=5,
            correct_answers=5,
        )
        print(f"✓ Exam recorded: {exam2.id}")
        print(
            f"  Topic: {exam2.topic} | Score: {exam2.score:.0%} | Difficulty: {exam2.difficulty}"
        )

        exam3 = await manager.record_exam(
            topic="Data Structures",
            num_questions=5,
            difficulty=4,
            score=0.7,
            time_taken_seconds=350.0,
            questions_answered=5,
            correct_answers=3,
        )
        print(f"✓ Exam recorded: {exam3.id}")
        print(
            f"  Topic: {exam3.topic} | Score: {exam3.score:.0%} | Difficulty: {exam3.difficulty}"
        )
        print()

        # ===== Example 2: Storing Code Snippets =====
        print("[Example 2] Storing Code Snippets")
        print("-" * 70)

        snippet1 = await manager.record_snippet(
            id="fibonacci",
            code="""def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))""",
            language="python",
            description="Fibonacci sequence using recursion",
            tags=["math", "recursion", "algorithm"],
        )
        print(f"✓ Snippet stored: {snippet1.id}")
        print(f"  Description: {snippet1.description}")
        print(f"  Tags: {', '.join(snippet1.tags)}")

        # Update after first execution
        await manager.update_snippet_execution("fibonacci", success=True)
        print(f"  After execution: 1 attempt, 1 success (100%)")

        snippet2 = await manager.record_snippet(
            id="list_comprehension",
            code="""numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers if x % 2 == 0]
print(squares)""",
            language="python",
            description="List comprehension for even numbers",
            tags=["list", "comprehension"],
        )
        print(f"✓ Snippet stored: {snippet2.id}")
        print(f"  Description: {snippet2.description}")
        print()

        # ===== Example 3: Conversation History =====
        print("[Example 3] Conversation History")
        print("-" * 70)

        msg1 = await manager.record_conversation(
            role="user",
            content="How do I write a function in Python?",
            intent="TEACHING",
            model="tinyllama",
        )
        print(f"✓ User: {msg1.content}")

        msg2 = await manager.record_conversation(
            role="assistant",
            content="In Python, you define a function with the def keyword: def my_function(): ...",
            intent="TEACHING",
            model="tinyllama",
        )
        print(f"✓ Assistant: {msg2.content[:50]}...")

        msg3 = await manager.record_conversation(
            role="user",
            content="Execute my_function()",
            intent="CODE",
            model="tinyllama",
        )
        print(f"✓ User: {msg3.content}")
        print()

        # ===== Example 4: Learning Summary =====
        print("[Example 4] Learning Summary")
        print("-" * 70)

        summary = await manager.get_learning_summary()

        print("📊 EXAM STATISTICS:")
        exam_stats = summary["exam_statistics"]
        print(f"  Total exams: {exam_stats['total_exams']}")
        print(f"  Average score: {exam_stats['average_score']:.1%}")
        print(f"  Best score: {exam_stats['best_score']:.1%}")
        print(f"  Worst score: {exam_stats['worst_score']:.1%}")
        print(f"  Score trend: {exam_stats['score_trend']}")
        print()

        print("🎯 SKILL ASSESSMENT:")
        skills = summary["skill_assessment"]
        for topic, data in skills.items():
            level = data["level"].upper()
            print(
                f"  {topic}: {data['attempts']} attempts, avg {data['average_score']:.0%} ({level})"
            )
        print()

        print("💻 CODE STATISTICS:")
        code_stats = summary["code_statistics"]
        print(f"  Total snippets: {code_stats['total_snippets']}")
        print(f"  Average success rate: {code_stats['average_success_rate']:.0%}")
        print(f"  Languages: {code_stats['languages']}")
        print()

        # ===== Example 5: Querying History =====
        print("[Example 5] Querying History")
        print("-" * 70)

        exams = await manager.store.list_exams(topic="Python Fundamentals", limit=10)
        print(
            f"Python Fundamentals exams: {len(exams)} (avg score: {sum(e.score for e in exams) / len(exams):.0%})"
        )

        snippets = await manager.store.list_snippets(tag="recursion", limit=10)
        print(f"Recursion snippets: {len(snippets)}")

        history = await manager.store.get_conversation_history(last_n=10)
        print(f"Recent messages: {len(history)}")
        print()

        # ===== Example 6: Storage Statistics =====
        print("[Example 6] Storage Statistics")
        print("-" * 70)

        stats = await manager.store.get_storage_stats()
        print(f"Exams stored: {stats['exams_total']}")
        print(f"Snippets stored: {stats['snippets_total']}")
        print(f"Messages stored: {stats['messages_total']}")
        print(f"Storage directory: {stats['storage_dir']}")
        print()

    print("=" * 70)
    print("✓ MEMORY SYSTEM DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Key features demonstrated:")
    print("  ✓ Exam result storage with progress tracking")
    print("  ✓ Code snippet management with execution history")
    print("  ✓ Conversation history recording")
    print("  ✓ Learning analytics and assessments")
    print("  ✓ Query system for historical data")
    print("  ✓ Storage statistics and metadata")


if __name__ == "__main__":
    asyncio.run(main())
