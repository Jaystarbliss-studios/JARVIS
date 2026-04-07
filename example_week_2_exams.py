"""
Week 2 Example: Live Exam Generation
Demonstrates streaming exam questions from TinyLlama
Run with: uv run python example_week_2_exams.py
"""

import asyncio

from providers.brain import Brain
from providers.exam_generator import ExamGenerator
from providers.local.ollama_engine import OllamaEngine


async def main():
    print("=" * 70)
    print("WEEK 2 LIVE EXAM GENERATION EXAMPLE")
    print("=" * 70)

    # Initialize
    print("\n[Setup] Initializing components...")
    ollama = OllamaEngine(model_name="tinyllama")
    brain = Brain(ollama)
    exam_gen = ExamGenerator(brain)
    print("✓ Ready for exam generation")

    # Generate exam
    print("\n" + "=" * 70)
    print("GENERATING EXAM: Python Fundamentals (5 questions, difficulty 3/5)")
    print("=" * 70)

    try:
        # Stream questions as they're generated
        question_count = 0
        async for question in exam_gen.stream_questions(
            topic="Python Fundamentals",
            num_questions=5,
            difficulty=3,
        ):
            question_count += 1
            print(f"\n[Question {question_count}] {question.text}")
            print(f"  Type: {question.question_type.value}")
            print(
                f"  Difficulty: {'★' * question.difficulty}{'☆' * (5 - question.difficulty)}"
            )

            if question.options:
                for i, opt in enumerate(question.options, 1):
                    print(f"    {chr(64 + i)}) {opt}")

            print(f"  [Est. time: {question.estimated_time_seconds}s]")

    except Exception as e:
        print(f"\n✗ Error during exam generation: {e}")
        return False

    print("\n" + "=" * 70)
    if question_count == 5:
        print(f"✓ EXAM GENERATED: {question_count} questions")
    else:
        print(f"⚠ Partial exam: {question_count} question(s) generated (expected 5)")
    print("=" * 70)

    print("\nNext: Answer questions using exam_gen.validate_answer()")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
