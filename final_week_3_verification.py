"""
Week 3 Final Verification - All Components

Comprehensive verification that all Week 3 components work correctly.
"""

import asyncio
import subprocess
import sys


async def run_tests():
    """Run Week 3 tests"""
    print("Running pytest for Week 3...")
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_week_3_code.py", "-q"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr


async def run_verification():
    """Run verification script"""
    print("Running verification script...")
    result = subprocess.run(
        ["python", "verify_week_3.py"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr


async def main():
    print("=" * 70)
    print("WEEK 3 FINAL COMPREHENSIVE VERIFICATION")
    print("=" * 70)
    print()
    
    tests_pass, tests_stdout, tests_stderr = await run_tests()
    
    print("[TESTS]")
    if tests_pass:
        # Count passed tests
        lines = tests_stdout.strip().split('\n')
        for line in lines:
            if 'passed' in line:
                print(f"✓ {line}")
    else:
        print(f"✗ Tests failed")
        print(f"Stdout:\n{tests_stdout}")
        print(f"Stderr:\n{tests_stderr}")
    print()
    
    verify_pass, verify_stdout, verify_stderr = await run_verification()
    
    print("[VERIFICATION]")
    if verify_pass:
        for line in verify_stdout.split('\n'):
            if line.strip():
                print(f"✓ {line}")
    else:
        print(f"✗ Verification failed")
        print(f"Stdout:\n{verify_stdout}")
        print(f"Stderr:\n{verify_stderr}")
    print()
    
    success = tests_pass and verify_pass
    
    print("=" * 70)
    if success:
        print("✓✓✓ WEEK 3 COMPLETE AND VERIFIED ✓✓✓")
    else:
        print("✗ WEEK 3 VERIFICATION FAILED")
    print("=" * 70)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
