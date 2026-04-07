"""
Week 5 Verification Script

Validates all teaching skill components.
"""

import asyncio
import sys
import tempfile


async def main():
    print("=" * 70)
    print("WEEK 5 TEACHING SKILL VERIFICATION")
    print("=" * 70)
    print()

    # Step 1: Import components
    print("[1/5] Importing components...")
    try:
        from providers.teaching_skill import (
            TeachingSkill,
            AdaptiveTutorSession,
            TutorSession,
            LearningRecommendation,
        )
        from providers.brain import Brain
        from providers.exam_generator import ExamGenerator
        from providers.memory_manager import MemoryManager
        from providers.local.ollama_engine import OllamaEngine

        print("✓ All components imported")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    print()

    # Step 2: Create instances
    print("[2/5] Creating instances...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ollama = OllamaEngine()
            brain = Brain(ollama)
            exam_gen = ExamGenerator(brain)
            memory = MemoryManager(tmpdir)
            skill = TeachingSkill(brain, exam_gen, memory)

            print("✓ Brain created")
            print("✓ ExamGenerator created")
            print("✓ MemoryManager created")
            print("✓ TeachingSkill created")
    except Exception as e:
        print(f"✗ Instance creation failed: {e}")
        return False
    print()

    # Step 3: Test session management
    print("[3/5] Testing session management...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = TeachingSkill(brain, exam_gen, MemoryManager(tmpdir))

            session = await skill.start_session("Python", 2)
            assert session is not None
            assert session.topic == "Python"
            print("✓ Session started")

            progress = await skill.get_session_progress()
            assert progress is not None
            print("✓ Session progress tracked")

    except Exception as e:
        print(f"✗ Session management test failed: {e}")
        return False
    print()

    # Step 4: Test adaptive difficulty
    print("[4/5] Testing adaptive difficulty...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = TeachingSkill(brain, exam_gen, MemoryManager(tmpdir))

            await skill.start_session("Python", 2)

            # Test difficulty increase
            new_diff = await skill.adjust_difficulty(0.95)
            assert new_diff == 3
            print("✓ Difficulty increases with high accuracy")

            # Reset and test decrease
            await skill.start_session("Python", 3)
            new_diff = await skill.adjust_difficulty(0.4)
            assert new_diff == 2
            print("✓ Difficulty decreases with low accuracy")

            # Test maintain
            await skill.start_session("Python", 3)
            new_diff = await skill.adjust_difficulty(0.7)
            assert new_diff == 3
            print("✓ Difficulty maintained with medium accuracy")

    except Exception as e:
        print(f"✗ Difficulty adjustment test failed: {e}")
        return False
    print()

    # Step 5: Test data structures
    print("[5/5] Testing data structures...")
    try:
        from datetime import datetime

        session = TutorSession(
            id="test_session",
            topic="Python",
            initial_difficulty=2,
            current_difficulty=2,
            questions_asked=0,
            correct_answers=0,
            incorrect_answers=0,
            started_at=datetime.now().isoformat(),
        )
        print("✓ TutorSession created")

        rec = LearningRecommendation(
            topic="Python",
            reason="Test",
            difficulty_level=3,
            suggested_action="Continue",
            confidence_score=0.85,
        )
        print("✓ LearningRecommendation created")

    except Exception as e:
        print(f"✗ Data structure test failed: {e}")
        return False
    print()

    print("=" * 70)
    print("✓ WEEK 5 ALL SYSTEMS OPERATIONAL")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
