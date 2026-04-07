"""
Code Execution Framework for JARVIS-Lite (Week 3)

Handles safe code execution, output capture, and error analysis.
Supports Python code execution with full stdin/stdout/stderr control.
"""

import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Code execution result status"""

    SUCCESS = "success"
    RUNTIME_ERROR = "runtime_error"
    SYNTAX_ERROR = "syntax_error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class ExecutionResult:
    """Result of code execution"""

    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    exception: str | None = None
    traceback: str | None = None
    execution_time_ms: float = 0.0
    return_value: Any = None

    def is_success(self) -> bool:
        """Check if execution succeeded"""
        return self.status == ExecutionStatus.SUCCESS

    def __str__(self) -> str:
        """Human-readable output"""
        parts = []
        if self.stdout:
            parts.append(f"Output:\n{self.stdout}")
        if self.stderr:
            parts.append(f"Stderr:\n{self.stderr}")
        if self.exception:
            parts.append(f"Error: {self.exception}")
        if self.traceback:
            parts.append(f"Traceback:\n{self.traceback}")
        return "\n".join(parts) if parts else "No output"


@dataclass
class CodeSnippet:
    """Stored code snippet with metadata"""

    id: str
    code: str
    language: str = "python"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    last_executed: str | None = None
    execution_count: int = 0
    success_count: int = 0

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100


class CodeExecutor:
    """
    Safely execute Python code with output capture and error handling.

    Features:
    - Capture stdout/stderr/exceptions
    - Timeout protection
    - Security vocabulary checks (basic)
    - Execution timing
    - Full traceback capture
    """

    # Disallowed operations for security
    FORBIDDEN_KEYWORDS = {
        "exec",
        "eval",
        "__import__",
        "open",
        "compile",
        "globals",
        "locals",
        "vars",
        "__builtins__",
        "getattr",
        "setattr",
        "delattr",
        "__dict__",
        "__code__",
        "__class__",
    }

    def __init__(self, timeout_seconds: float = 5.0, max_output_chars: int = 10000):
        """
        Args:
            timeout_seconds: Maximum execution time
            max_output_chars: Maximum output characters to capture
        """
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars
        self.snippet_store: dict[str, CodeSnippet] = {}

    async def execute(
        self, code: str, timeout: float | None = None
    ) -> ExecutionResult:
        """
        Execute Python code and capture output.

        Args:
            code: Python code to execute
            timeout: Override default timeout

        Returns:
            ExecutionResult with status and output
        """
        timeout = timeout or self.timeout_seconds

        # Check for syntax errors
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            return ExecutionResult(
                status=ExecutionStatus.SYNTAX_ERROR,
                exception=str(e),
                traceback=traceback.format_exc(),
            )

        # Check for forbidden keywords
        security_check = self._check_security(code)
        if security_check:
            return ExecutionResult(
                status=ExecutionStatus.SECURITY_VIOLATION,
                exception=f"Security violation: {security_check}",
            )

        # Execute in isolated namespace
        import time

        start_time = time.time()

        try:
            # Capture output
            import io
            import sys

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            try:
                # Create isolated namespace
                namespace = {
                    "__builtins__": {
                        "print": print,
                        "range": range,
                        "len": len,
                        "str": str,
                        "int": int,
                        "float": float,
                        "bool": bool,
                        "list": list,
                        "dict": dict,
                        "tuple": tuple,
                        "set": set,
                        "sum": sum,
                        "max": max,
                        "min": min,
                        "abs": abs,
                        "type": type,
                    }
                }

                # Execute code
                exec(code, namespace)

                execution_time = (time.time() - start_time) * 1000
                stdout_text = stdout_capture.getvalue()[: self.max_output_chars]

                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    stdout=stdout_text,
                    execution_time_ms=execution_time,
                )

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                stdout_text = stdout_capture.getvalue()[: self.max_output_chars]
                stderr_text = stderr_capture.getvalue()[: self.max_output_chars]

                # Format exception with type name
                exc_type = type(e).__name__
                exc_msg = f"{exc_type}: {e!s}"

                return ExecutionResult(
                    status=ExecutionStatus.RUNTIME_ERROR,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    exception=exc_msg,
                    traceback=traceback.format_exc(),
                    execution_time_ms=execution_time,
                )

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        except TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                exception=f"Code execution timeout after {timeout}s",
            )

    def _check_security(self, code: str) -> str | None:
        """
        Basic security check for forbidden operations.

        Args:
            code: Code to check

        Returns:
            Error message if violation found, None otherwise
        """
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in code:
                return f"Forbidden operation: {keyword}"
        return None

    def store_snippet(
        self,
        id: str,
        code: str,
        description: str = "",
        tags: list[str] | None = None,
    ) -> CodeSnippet:
        """
        Store a code snippet for later reference.

        Args:
            id: Unique identifier
            code: Code to store
            description: Human-readable description
            tags: Tags for searching

        Returns:
            Stored snippet
        """
        from datetime import datetime

        snippet = CodeSnippet(
            id=id,
            code=code,
            description=description,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
        )
        self.snippet_store[id] = snippet
        logger.info(f"Stored code snippet: {id}")
        return snippet

    def get_snippet(self, id: str) -> CodeSnippet | None:
        """Retrieve stored snippet"""
        return self.snippet_store.get(id)

    def list_snippets(self, tag: str | None = None) -> list[CodeSnippet]:
        """
        List stored snippets.

        Args:
            tag: Filter by tag

        Returns:
            List of snippets
        """
        snippets = list(self.snippet_store.values())
        if tag:
            snippets = [s for s in snippets if tag in s.tags]
        return snippets

    def delete_snippet(self, id: str) -> bool:
        """Delete stored snippet"""
        if id in self.snippet_store:
            del self.snippet_store[id]
            return True
        return False

    def update_snippet_stats(self, id: str, success: bool):
        """Update execution statistics for a snippet"""
        if id in self.snippet_store:
            snippet = self.snippet_store[id]
            snippet.execution_count += 1
            if success:
                snippet.success_count += 1
            from datetime import datetime

            snippet.last_executed = datetime.now().isoformat()


class DebugAnalyzer:
    """
    Analyze code errors and provide suggestions for fixes.

    Parses execution results and generates helpful error messages
    and debugging recommendations.
    """

    def __init__(self):
        self.error_patterns: dict[str, str] = {
            "NameError": "Variable or function not defined. Check spelling or define it first.",
            "TypeError": "Type mismatch. Check that you're using compatible types.",
            "IndexError": "List index out of range. Check list length before indexing.",
            "KeyError": "Dictionary key not found. Check that the key exists.",
            "ZeroDivisionError": "Cannot divide by zero. Add a check before division.",
            "ValueError": "Invalid value for operation. Check input format.",
            "AttributeError": "Object has no such attribute. Check object type and available methods.",
            "ImportError": "Cannot import module. Check that the module is installed.",
            "IndentationError": "Code indentation is incorrect. Check spacing.",
            "FileNotFoundError": "File not found. Check file path.",
        }

    def analyze(self, result: ExecutionResult) -> dict[str, Any]:
        """
        Analyze execution result and provide debugging info.

        Args:
            result: Execution result to analyze

        Returns:
            Dictionary with analysis information
        """
        analysis = {
            "status": result.status.value,
            "success": result.is_success(),
            "execution_time_ms": result.execution_time_ms,
            "has_output": bool(result.stdout),
            "has_errors": bool(result.stderr or result.exception),
            "suggestions": [],
        }

        if result.exception:
            error_type = self._get_error_type(result.exception)
            analysis["error_type"] = error_type

            # Find matching pattern
            for pattern, suggestion in self.error_patterns.items():
                if pattern.lower() in result.exception.lower():
                    analysis["suggestions"].append(suggestion)

            # Parse exception details
            if result.traceback:
                lines = result.traceback.split("\n")
                for i, line in enumerate(lines):
                    if "File" in line and i < len(lines) - 1:
                        analysis["error_location"] = line.strip()
                        if i + 1 < len(lines):
                            analysis["error_line"] = lines[i + 1].strip()
                        break

        # Add performance insights
        if result.execution_time_ms > 1000:
            analysis["suggestions"].append(
                f"Code took {result.execution_time_ms:.0f}ms to execute. Consider optimization."
            )

        return analysis

    def _get_error_type(self, exception: str) -> str:
        """Extract error type from exception string"""
        if ":" in exception:
            return exception.split(":")[0].strip()
        return "UnknownError"

    def format_analysis(self, analysis: dict[str, Any]) -> str:
        """Format analysis for human display"""
        lines = [f"Status: {analysis['status'].upper()}"]

        if "error_type" in analysis:
            lines.append(f"Error Type: {analysis['error_type']}")

        if "error_location" in analysis:
            lines.append(f"Location: {analysis['error_location']}")

        if "error_line" in analysis:
            lines.append(f"Code: {analysis['error_line']}")

        if analysis.get("suggestions"):
            lines.append("\nSuggestions:")
            for i, suggestion in enumerate(analysis["suggestions"], 1):
                lines.append(f"  {i}. {suggestion}")

        return "\n".join(lines)
