"""
Comprehensive tests for Week 3 Code Execution Framework

Tests CodeExecutor, DebugAnalyzer, and integration with Brain/Tools.
"""

import pytest

from providers.code_executor import (
    CodeExecutor,
    CodeSnippet,
    DebugAnalyzer,
    ExecutionResult,
    ExecutionStatus,
)


class TestCodeExecutor:
    """Test code execution engine"""

    @pytest.fixture
    def executor(self):
        return CodeExecutor(timeout_seconds=5.0)

    @pytest.mark.asyncio
    async def test_simple_print(self, executor):
        """Test basic print statement"""
        code = "print('Hello, World!')"
        result = await executor.execute(code)

        assert result.is_success()
        assert "Hello, World!" in result.stdout
        assert result.status == ExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_arithmetic(self, executor):
        """Test arithmetic operations"""
        code = "print(2 + 3 * 4)"
        result = await executor.execute(code)

        assert result.is_success()
        assert "14" in result.stdout

    @pytest.mark.asyncio
    async def test_loop_output(self, executor):
        """Test loop with output"""
        code = """
for i in range(3):
    print(f"Number: {i}")
"""
        result = await executor.execute(code)

        assert result.is_success()
        assert "Number: 0" in result.stdout
        assert "Number: 1" in result.stdout
        assert "Number: 2" in result.stdout

    @pytest.mark.asyncio
    async def test_list_operations(self, executor):
        """Test list comprehension"""
        code = """
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]
print(squares)
"""
        result = await executor.execute(code)

        assert result.is_success()
        assert "[1, 4, 9, 16, 25]" in result.stdout

    @pytest.mark.asyncio
    async def test_syntax_error(self, executor):
        """Test detection of syntax errors"""
        code = "print('unclosed"
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.SYNTAX_ERROR
        assert result.exception is not None

    @pytest.mark.asyncio
    async def test_runtime_error(self, executor):
        """Test detection of runtime errors"""
        code = """
x = 5
y = 0
print(x / y)
"""
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.RUNTIME_ERROR
        assert "ZeroDivisionError" in result.exception

    @pytest.mark.asyncio
    async def test_undefined_variable(self, executor):
        """Test undefined variable error"""
        code = "print(undefined_var)"
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.RUNTIME_ERROR
        assert "NameError" in result.exception

    @pytest.mark.asyncio
    async def test_index_out_of_range(self, executor):
        """Test index out of range error"""
        code = """
items = [1, 2, 3]
print(items[10])
"""
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.RUNTIME_ERROR
        assert "IndexError" in result.exception

    @pytest.mark.asyncio
    async def test_forbidden_exec(self, executor):
        """Test security check: exec forbidden"""
        code = "exec('print(1)')"
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        assert "exec" in result.exception.lower()

    @pytest.mark.asyncio
    async def test_forbidden_eval(self, executor):
        """Test security check: eval forbidden"""
        code = "result = eval('2+2')"
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        assert "eval" in result.exception.lower()

    @pytest.mark.asyncio
    async def test_forbidden_open(self, executor):
        """Test security check: open forbidden"""
        code = "f = open('file.txt')"
        result = await executor.execute(code)

        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        assert "open" in result.exception.lower()

    @pytest.mark.asyncio
    async def test_execution_timing(self, executor):
        """Test execution time is captured"""
        code = """
total = 0
for i in range(100):
    total += i
print(total)
"""
        result = await executor.execute(code)

        assert result.is_success()
        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 100  # Should be fast

    def test_store_snippet(self, executor):
        """Test storing code snippets"""
        code = "print('test')"
        snippet = executor.store_snippet(
            id="test1", code=code, description="Test snippet", tags=["test", "print"]
        )

        assert snippet.id == "test1"
        assert snippet.code == code
        assert "test" in snippet.tags

    def test_get_snippet(self, executor):
        """Test retrieving snippet"""
        executor.store_snippet("s1", "code1", "desc1", ["tag1"])

        retrieved = executor.get_snippet("s1")
        assert retrieved is not None
        assert retrieved.code == "code1"

    def test_list_snippets(self, executor):
        """Test listing snippets"""
        executor.store_snippet("s1", "code1", tags=["math"])
        executor.store_snippet("s2", "code2", tags=["string"])
        executor.store_snippet("s3", "code3", tags=["math", "loop"])

        all_snippets = executor.list_snippets()
        assert len(all_snippets) == 3

        math_snippets = executor.list_snippets(tag="math")
        assert len(math_snippets) == 2

    def test_delete_snippet(self, executor):
        """Test deleting snippet"""
        executor.store_snippet("s1", "code")
        assert executor.get_snippet("s1") is not None

        success = executor.delete_snippet("s1")
        assert success
        assert executor.get_snippet("s1") is None

    def test_snippet_execution_stats(self, executor):
        """Test updating snippet statistics"""
        executor.store_snippet("s1", "code")

        executor.update_snippet_stats("s1", success=True)
        executor.update_snippet_stats("s1", success=True)
        executor.update_snippet_stats("s1", success=False)

        snippet = executor.get_snippet("s1")
        assert snippet.execution_count == 3
        assert snippet.success_count == 2
        assert snippet.success_rate() == pytest.approx(66.67, rel=1)

    def test_snippet_success_rate(self):
        """Test success rate calculation"""
        snippet = CodeSnippet(
            id="test", code="code", execution_count=10, success_count=7
        )

        assert snippet.success_rate() == 70.0

    def test_snippet_empty_success_rate(self):
        """Test success rate with no executions"""
        snippet = CodeSnippet(
            id="test", code="code", execution_count=0, success_count=0
        )

        assert snippet.success_rate() == 0.0


class TestDebugAnalyzer:
    """Test error analysis engine"""

    @pytest.fixture
    def analyzer(self):
        return DebugAnalyzer()

    def test_analyze_success(self, analyzer):
        """Test analyzing successful execution"""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS, stdout="output", execution_time_ms=10.5
        )

        analysis = analyzer.analyze(result)

        assert analysis["success"] is True
        assert analysis["status"] == "success"
        assert analysis["has_output"] is True
        assert analysis["execution_time_ms"] == 10.5

    def test_analyze_name_error(self, analyzer):
        """Test analyzing NameError"""
        result = ExecutionResult(
            status=ExecutionStatus.RUNTIME_ERROR,
            exception="NameError: name 'x' is not defined",
            traceback="Traceback...",
        )

        analysis = analyzer.analyze(result)

        assert analysis["error_type"] == "NameError"
        assert len(analysis["suggestions"]) > 0
        assert any("defined" in s.lower() for s in analysis["suggestions"])

    def test_analyze_type_error(self, analyzer):
        """Test analyzing TypeError"""
        result = ExecutionResult(
            status=ExecutionStatus.RUNTIME_ERROR,
            exception="TypeError: unsupported operand type(s)",
        )

        analysis = analyzer.analyze(result)

        assert "TypeError" in analysis.get("error_type", "")
        assert len(analysis["suggestions"]) > 0

    def test_analyze_index_error(self, analyzer):
        """Test analyzing IndexError"""
        result = ExecutionResult(
            status=ExecutionStatus.RUNTIME_ERROR,
            exception="IndexError: list index out of range",
        )

        analysis = analyzer.analyze(result)

        assert len(analysis["suggestions"]) > 0
        assert any("range" in s.lower() for s in analysis["suggestions"])

    def test_analyze_slow_execution(self, analyzer):
        """Test performance suggestion"""
        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS, stdout="output", execution_time_ms=2500
        )

        analysis = analyzer.analyze(result)

        assert len(analysis["suggestions"]) > 0
        assert any("optimization" in s.lower() for s in analysis["suggestions"])

    def test_format_analysis(self, analyzer):
        """Test formatting analysis for display"""
        result = ExecutionResult(
            status=ExecutionStatus.RUNTIME_ERROR,
            exception="ValueError: invalid literal",
        )

        analysis = analyzer.analyze(result)
        formatted = analyzer.format_analysis(analysis)

        assert "Status:" in formatted
        assert "ValueError" in formatted
        assert "Suggestions:" in formatted

    def test_get_error_type(self, analyzer):
        """Test extracting error type"""
        error_type = analyzer._get_error_type("NameError: name 'x' is not defined")
        assert error_type == "NameError"

        # If no colon, should return a default
        error_type = analyzer._get_error_type("No colons here")
        assert "Error" in error_type or error_type == "UnknownError"


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_executor_and_analyzer(self):
        """Test executor and analyzer together"""
        executor = CodeExecutor()
        analyzer = DebugAnalyzer()

        # Execute code with error
        code = "print(1/0)"
        result = await executor.execute(code)

        # Analyze result
        analysis = analyzer.analyze(result)

        assert result.status == ExecutionStatus.RUNTIME_ERROR
        assert not analysis["success"]
        assert analysis["error_type"] == "ZeroDivisionError"
        assert len(analysis["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_snippet_execution_tracking(self):
        """Test tracking snippet execution"""
        executor = CodeExecutor()

        # Store snippet
        executor.store_snippet("calc", "print(2+2)", tags=["math"])

        # Execute it
        snippet = executor.get_snippet("calc")
        assert snippet is not None
        code = snippet.code
        result = await executor.execute(code)
        
        # Update stats
        executor.update_snippet_stats("calc", success=result.is_success())
        
        # Verify
        snippet = executor.get_snippet("calc")
        assert snippet is not None
