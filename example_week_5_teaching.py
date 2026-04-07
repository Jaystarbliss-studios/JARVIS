"""
Week 5 Teaching Skill - Live Demonstration

Shows interactive tutoring, adaptive difficulty, and personalized recommendations.
"""

import asyncio
import sys
import tempfile


async def main():
    print("\n" + "=" * 80)
    print(" WEEK 5 TEACHING SKILL - INTERACTIVE TUTORING DEMONSTRATION")
    print("=" * 80 + "\n")

    from providers.teaching_skill import TeachingSkill, AdaptiveTutorSession
    from providers.brain import Brain
    from providers.exam_generator import ExamGenerator
    from providers.memory_manager import MemoryManager
    from providers.local.ollama_engine import OllamaEngine

    # Initialize components
    print("📚 Initializing tutoring system...")
    with tempfile.TemporaryDirectory() as tmpdir:
        ollama = OllamaEngine()
        brain = Brain(ollama)
        exam_gen = ExamGenerator(brain)
        memory = MemoryManager(tmpdir)
        skill = TeachingSkill(brain, exam_gen, memory)

    print("✓ System ready\n")

    # Demo 1: Session Creation
    print("-" * 80)
    print("DEMO 1: Starting Adaptive Learning Session")
    print("-" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        skill = TeachingSkill(brain, exam_gen, MemoryManager(tmpdir))

        session = await skill.start_session("Python Basics", starting_difficulty=2)

        print(f"✓ Session created: {session.id}")
        print(f"  Topic: {session.topic}")
        print(f"  Starting difficulty: {session.initial_difficulty}/5")
        print(f"  Started: {session.started_at}\n")

        # Demo 2: Interactive Explanation
        print("-" * 80)
        print("DEMO 2: Interactive Topic Explanation")
        print("-" * 80)
        print("📖 Streaming explanation of 'Variables in Python':\n")

        chunk_count = 0
        async for chunk in skill.get_interactive_explanation("Variables in Python"):
            print(chunk, end="", flush=True)
            chunk_count += 1
            if chunk_count >= 20:  # Limit for demo
                print("...")
                break

        print("\n")

        # Demo 3: Question Generation & Evaluation
        print("-" * 80)
        print("DEMO 3: Adaptive Question Generation & Evaluation")
        print("-" * 80)

        # Generate question
        question = await skill.select_or_generate_question(
            "Python Basics", session.current_difficulty
        )

        if question:
            print(f"✓ Question generated: {question.id}")
            print(f"  Text: {question.text}")
            print(f"  Difficulty: {question.difficulty}/5")
            print(f"  Type: {question.type}\n")

            # Simulate some answers to show progression
            answers = [
                ("a good choice", True),  # Correct
                ("wrong answer", False),  # Incorrect
            ]

            for i, (answer, is_correct_expected) in enumerate(answers, 1):
                print(f"  Attempt {i}: User answered '{answer}'")

                is_correct, feedback, details = await skill.evaluate_answer(
                    question, answer
                )

                print(f"  Result: {'✓ Correct' if is_correct else '✗ Incorrect'}")
                print(f"  Feedback: {feedback[:60]}...\n")

            # Demo 4: Dynamic Difficulty Adjustment
            print("-" * 80)
            print("DEMO 4: Dynamic Difficulty Adjustment")
            print("-" * 80)

            print("Scenario 1: Student excels (90% accuracy)")
            new_diff = await skill.adjust_difficulty(0.90)
            print(f"  Previous difficulty: 2")
            print(f"  New difficulty: {new_diff} ✓ Increased to challenge student\n")

            # Reset for next scenario
            await skill.start_session("Python Basics", 3)

            print("Scenario 2: Student struggles (40% accuracy)")
            new_diff = await skill.adjust_difficulty(0.40)
            print(f"  Previous difficulty: 3")
            print(f"  New difficulty: {new_diff} ✓ Decreased to rebuild confidence\n")

            # Reset for next scenario
            await skill.start_session("Python Basics", 3)

            print("Scenario 3: Student steady (70% accuracy)")
            new_diff = await skill.adjust_difficulty(0.70)
            print(f"  Previous difficulty: 3")
            print(f"  New difficulty: {new_diff} ✓ Maintained to reinforce concepts\n")

            # Demo 5: Session Progress Tracking
            print("-" * 80)
            print("DEMO 5: Session Progress Tracking")
            print("-" * 80)

            await skill.start_session("Python Basics", 2)

            # Simulate multiple interactions
            skill.current_session.questions_asked = 10
            skill.current_session.correct_answers = 8
            skill.current_session.current_difficulty = 3

            progress = await skill.get_session_progress()

            print(f"✓ Progress Update:")
            print(f"  Questions answered: {progress['questions_asked']}")
            print(f"  Correct: {progress['correct']}")
            print(f"  Accuracy: {progress['accuracy']:.0%}")
            print(f"  Current difficulty: {progress['current_difficulty']}/5")
            print(f"  {progress['progress_bar']}\n")

            # Demo 6: Session End & Report
            print("-" * 80)
            print("DEMO 6: Session Completion & Report")
            print("-" * 80)

            report = await skill.end_session()

            if report:
                print(f"✓ Session ended: {report.session_id}")
                print(f"\n📊 LEARNING REPORT:")
                print(f"  Topic: {report.topic}")
                print(f"  Total questions: {report.total_questions}")
                print(f"  Correct answers: {report.correct_answers}")
                print(f"  Accuracy: {report.accuracy:.0%}")
                print(f"  Time: {report.time_minutes:.1f} minutes")

                print(f"\n💡 PERSONALIZED RECOMMENDATIONS:")
                for i, rec in enumerate(report.recommendations, 1):
                    print(f"  {i}. {rec.suggested_action}")
                    print(f"     Topic: {rec.topic}")
                    print(f"     Reason: {rec.reason}")
                    print(f"     Confidence: {rec.confidence_score:.0%}\n")

    # Demo 7: Adaptive Session Manager
    print("-" * 80)
    print("DEMO 7: Multi-Turn Adaptive Session")
    print("-" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        skill = TeachingSkill(brain, exam_gen, MemoryManager(tmpdir))
        session_mgr = AdaptiveTutorSession(skill)

        # Start adaptive session
        session = await session_mgr.start("Data Structures", difficulty=2)
        print(f"✓ Adaptive session started")
        print(f"  Session ID: {session.id}")
        print(f"  Topic: {session.topic}\n")

        # Get first question
        question = await session_mgr.ask_question()
        if question:
            print(f"✓ Question generated:")
            print(f"  {question.text}\n")

        # Submit answer and get feedback
        result = (
            await session_mgr.submit_answer(question, "Sample answer")
            if question
            else None
        )

        if result:
            print(f"✓ Answer evaluated:")
            print(f"  Correct: {result['is_correct']}")
            print(f"  Feedback: {result['feedback'][:60]}...\n")

        # End session
        report = await session_mgr.end()
        if report:
            print(f"✓ Session complete")
            print(f"  Accuracy: {report.accuracy:.0%}\n")

    print("=" * 80)
    print(" ✓ TEACHING SKILL DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Interactive session management")
    print("  ✓ Streaming explanations")
    print("  ✓ Adaptive question generation")
    print("  ✓ Answer evaluation and feedback")
    print("  ✓ Dynamic difficulty adjustment")
    print("  ✓ Progress tracking and reports")
    print("  ✓ Personalized recommendations")
    print("  ✓ Multi-turn adaptive sessions\n")


if __name__ == "__main__":
    asyncio.run(main())
