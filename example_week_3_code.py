"""
Week 3 Code Execution Example

Demonstrates code execution, error analysis, and code snippet storage.
"""

import asyncio

from providers.code_executor import CodeExecutor, DebugAnalyzer


async def main():
    print("=" * 70)
    print("WEEK 3 CODE EXECUTION FRAMEWORK DEMO")
    print("=" * 70)
    print()

    executor = CodeExecutor()
    analyzer = DebugAnalyzer()

    # Example 1: Simple code execution
    print("[Example 1] Simple Code Execution")
    print("-" * 70)
    code = """
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
average = total / len(numbers)
print(f"Sum: {total}")
print(f"Average: {average}")
"""
    print(f"Code:\n{code}")
    result = await executor.execute(code)
    print(f"\nResult:\n{result.stdout}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
    print()

    # Example 2: Loop and list comprehension
    print("[Example 2] Loop and List Comprehension")
    print("-" * 70)
    code = """
# Generate squares of even numbers
even_numbers = [2, 4, 6, 8, 10]
squares = [x**2 for x in even_numbers]
print(f"Even numbers: {even_numbers}")
print(f"Squares: {squares}")

# Print with formatting
for num, square in zip(even_numbers, squares):
    print(f"{num}² = {square}")
"""
    print(f"Code:\n{code}")
    result = await executor.execute(code)
    print(f"\nResult:\n{result.stdout}")
    print()

    # Example 3: Error detection and analysis
    print("[Example 3] Error Detection and Analysis")
    print("-" * 70)
    code = """
items = ['a', 'b', 'c']
print(items[0])
print(items[5])  # This will cause an error
"""
    print(f"Code:\n{code}")
    result = await executor.execute(code)
    print(f"\nExecution Status: {result.status.value.upper()}")

    if not result.is_success():
        analysis = analyzer.analyze(result)
        print("\nError Analysis:")
        print(analyzer.format_analysis(analysis))
    print()

    # Example 4: Type error analysis
    print("[Example 4] Type Error Analysis")
    print("-" * 70)
    code = """
name = "Alice"
age = 30
print(f"{name} is {age} years old")
print(f"Sum: {age + name}")  # This will cause a type error
"""
    print(f"Code:\n{code}")
    result = await executor.execute(code)
    print(f"\nExecution Status: {result.status.value.upper()}")

    if not result.is_success():
        analysis = analyzer.analyze(result)
        print("\nError Analysis:")
        print(analyzer.format_analysis(analysis))
        print(f"\nOutput captured before error:\n{result.stdout}")
    print()

    # Example 5: Code snippets storage
    print("[Example 5] Code Snippet Storage")
    print("-" * 70)

    # Store some useful snippets
    executor.store_snippet(
        id="factorial",
        code="""
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(f"5! = {factorial(5)}")
""",
        description="Calculate factorial using recursion",
        tags=["math", "recursion"],
    )

    executor.store_snippet(
        id="fibonacci",
        code="""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

fib_sequence = [fibonacci(i) for i in range(10)]
print(f"Fibonacci sequence: {fib_sequence}")
""",
        description="Generate Fibonacci sequence",
        tags=["math", "sequence"],
    )

    executor.store_snippet(
        id="count_words",
        code="""
text = "The quick brown fox jumps over the lazy dog"
words = text.split()
word_count = len(words)
print(f"Text: {text}")
print(f"Word count: {word_count}")
print(f"Unique words: {len(set(words))}")
""",
        description="Count words in a text",
        tags=["string", "text"],
    )

    print("Stored 3 code snippets:")
    for snippet in executor.list_snippets():
        print(f"  - {snippet.id}: {snippet.description}")
    print()

    # Execute a snippet
    print("Executing 'fibonacci' snippet:")
    snippet = executor.get_snippet("fibonacci")
    result = await executor.execute(snippet.code)
    executor.update_snippet_stats("fibonacci", success=result.is_success())
    print(result.stdout)

    # Show snippet stats
    snippet = executor.get_snippet("fibonacci")
    print(
        f"Snippet stats - Executed: {snippet.execution_count}, Success rate: {snippet.success_rate():.0f}%"
    )
    print()

    # Example 6: Security checks
    print("[Example 6] Security Checks")
    print("-" * 70)

    dangerous_code_samples = [
        ("exec('malicious')", "exec() is forbidden"),
        ("eval('2+2')", "eval() is forbidden"),
        ("open('file.txt')", "open() is forbidden"),
    ]

    for code, description in dangerous_code_samples:
        print(f"Code: {code}")
        print(f"Description: {description}")
        result = await executor.execute(code)
        print(f"Status: BLOCKED ({result.status.value})")
        print()

    print("=" * 70)
    print("✓ CODE EXECUTION FRAMEWORK DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
