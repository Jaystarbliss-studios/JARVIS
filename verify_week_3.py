"""
Week 3 Verification Script

Validates all code execution and debugging components.
"""

import asyncio
import sys


async def main():
    print("=" * 70)
    print("WEEK 3 CODE EXECUTION FRAMEWORK VERIFICATION")
    print("=" * 70)
    print()

    # Step 1: Import components
    print("[1/5] Importing components...")
    try:
        from providers.code_executor import CodeExecutor, DebugAnalyzer, ExecutionStatus
        from providers.tools import ToolRegistry

        print("✓ All components imported")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    print()

    # Step 2: Create instances
    print("[2/5] Creating instances...")
    try:
        executor = CodeExecutor(timeout_seconds=5.0)
        analyzer = DebugAnalyzer()
        registry = ToolRegistry()
        print("✓ Executor created")
        print("✓ Analyzer created")
        print("✓ ToolRegistry created")
    except Exception as e:
        print(f"✗ Instance creation failed: {e}")
        return False
    print()

    # Step 3: Test code execution
    print("[3/5] Testing code execution...")
    try:
        # Success case
        result = await executor.execute("print('Hello from TinyLlama!')")
        assert result.is_success(), "Basic execution failed"
        print("✓ Basic execution works")

        # Loop case
        result = await executor.execute("""
for i in range(3):
    print(f"Line {i+1}")
""")
        assert result.is_success(), "Loop execution failed"
        print("✓ Loop execution works")

        # Error case
        result = await executor.execute("print(1/0)")
        assert result.status == ExecutionStatus.RUNTIME_ERROR
        print("✓ Error detection works")

        # Security case
        result = await executor.execute("exec('print(1)')")
        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        print("✓ Security checks work")

    except Exception as e:
        print(f"✗ Execution test failed: {e}")
        return False
    print()

    # Step 4: Test debugging
    print("[4/5] Testing error analysis...")
    try:
        # Execute failing code
        result = await executor.execute("""
items = [1, 2, 3]
print(items[10])
""")

        # Analyze result
        analysis = analyzer.analyze(result)
        formatted = analyzer.format_analysis(analysis)

        assert not analysis["success"]
        assert "IndexError" in analysis.get("error_type", "")
        print("✓ Error analysis works")
        print("✓ Suggestions generated")

    except Exception as e:
        print(f"✗ Debugging test failed: {e}")
        return False
    print()

    # Step 5: Test code snippets
    print("[5/5] Testing code snippet storage...")
    try:
        # Store snippet
        executor.store_snippet(
            id="hello_world",
            code="print('Hello, World!')",
            description="Classic hello world",
            tags=["intro", "print"],
        )
        print("✓ Snippet stored")

        # Retrieve snippet
        snippet = executor.get_snippet("hello_world")
        assert snippet is not None
        assert snippet.code == "print('Hello, World!')"
        print("✓ Snippet retrieved")

        # List snippets
        snippets = executor.list_snippets()
        assert len(snippets) > 0
        print(f"✓ Listed {len(snippets)} snippet(s)")

        # Update stats
        executor.update_snippet_stats("hello_world", success=True)
        snippet = executor.get_snippet("hello_world")
        assert snippet.execution_count == 1
        assert snippet.success_count == 1
        print("✓ Snippet stats updated")

    except Exception as e:
        print(f"✗ Snippet test failed: {e}")
        return False
    print()

    print("=" * 70)
    print("✓ WEEK 3 ALL SYSTEMS OPERATIONAL")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
