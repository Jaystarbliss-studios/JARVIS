"""
Week 6: Coding Skill - Advanced Code Review & Optimization

Combines CodeExecutor, DebugAnalyzer, ToolRegistry, and Brain
into a comprehensive code review and optimization system.

Features:
- Code review with AI feedback
- Bug detection and suggestions
- Refactoring recommendations
- Performance optimization tips
- Code quality scoring
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from providers.brain import Brain
from providers.code_executor import CodeExecutor, DebugAnalyzer
from providers.memory_manager import MemoryManager
from providers.tools import ToolRegistry


class IssueType(Enum):
    """Types of code issues"""

    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOGIC = "logic"
    MAINTAINABILITY = "maintainability"


@dataclass
class CodeIssue:
    """Discovered code issue"""

    issue_type: IssueType
    severity: int  # 1-5, where 5 is critical
    line_number: int
    description: str
    suggestion: str
    confidence_score: float


@dataclass
class CodeReviewResult:
    """Result of code review"""

    code_hash: str
    total_issues: int
    issues: list[CodeIssue]
    quality_score: float  # 0-100
    overall_feedback: str
    refactoring_recommendations: list[str]
    performance_tips: list[str]
    security_concerns: list[str]


@dataclass
class RefactoringPlan:
    """Plan to refactor code"""

    before_code: str
    suggested_code: str
    changes_summary: str
    expected_benefits: dict[str, Any]


class CodingSkill:
    """
    Advanced code review and optimization system combining all Week 1-4 components.

    Workflow:
    1. User submits code
    2. System analyzes code structure and executes it
    3. Bug detection and error analysis performed
    4. Quality metrics calculated
    5. Detailed feedback generated
    6. Refactoring suggestions provided
    7. Progress tracked in memory
    """

    def __init__(
        self,
        brain: Brain,
        code_executor: CodeExecutor,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry | None = None,
    ):
        """
        Initialize coding skill.

        Args:
            brain: Brain for explanations and analysis
            code_executor: For safe code execution
            memory_manager: For tracking progress
            tool_registry: For tool support
        """
        self.brain = brain
        self.executor = code_executor
        self.memory = memory_manager
        self.tools = tool_registry or ToolRegistry()
        self.analyzer = DebugAnalyzer()

    async def review_code(
        self, code: str, language: str = "python"
    ) -> CodeReviewResult:
        """
        Perform comprehensive code review.

        Args:
            code: Code to review
            language: Programming language

        Returns:
            CodeReviewResult with detailed analysis
        """
        import hashlib

        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]

        # Step 1: Execute code to find runtime issues
        execution_result = await self.executor.execute(code)

        issues: list[CodeIssue] = []
        severity_scores = [1, 1, 1]  # [style, perf, security]

        # Step 2: Detect execution errors
        if not execution_result.is_success():
            error_analysis = self.analyzer.analyze(execution_result)

            error_desc = error_analysis.get("description", "Execution error occurred")
            error_sugg = error_analysis.get("suggestion", "Check code syntax")

            issues.append(
                CodeIssue(
                    issue_type=IssueType.LOGIC,
                    severity=4,
                    line_number=1,
                    description=f"Execution error: {error_desc}",
                    suggestion=error_sugg,
                    confidence_score=0.9,
                )
            )
            severity_scores[2] = 4

        # Step 3: Static analysis using brain
        analysis_prompt = f"""
Analyze this {language} code for issues:

```{language}
{code}
```

Identify issues in categories:
1. Code style/readability
2. Performance concerns
3. Security issues
4. Mutable state/side effects
5. Error handling

For each issue, provide:
- Line number (approximate)
- Severity (1-5)
- Description
- Suggestion

Keep it concise and actionable."""

        analysis = await self.brain.think(analysis_prompt)

        # Parse analysis (simplified)
        if "style" in analysis.lower():
            issues.append(
                CodeIssue(
                    issue_type=IssueType.STYLE,
                    severity=2,
                    line_number=1,
                    description="Code style can be improved",
                    suggestion="Follow PEP 8 conventions",
                    confidence_score=0.7,
                )
            )

        if "performance" in analysis.lower():
            issues.append(
                CodeIssue(
                    issue_type=IssueType.PERFORMANCE,
                    severity=2,
                    line_number=1,
                    description="Potential performance issue",
                    suggestion="Consider using more efficient algorithms",
                    confidence_score=0.6,
                )
            )

        if "security" in analysis.lower() or "injection" in analysis.lower():
            issues.append(
                CodeIssue(
                    issue_type=IssueType.SECURITY,
                    severity=5,
                    line_number=1,
                    description="Security concern detected",
                    suggestion="Validate all user inputs",
                    confidence_score=0.85,
                )
            )

        # Step 4: Calculate quality score
        quality_score = max(0, 100 - len(issues) * 15)

        # Step 5: Generate refactoring suggestions
        refactoring_suggestions = await self._get_refactoring_suggestions(
            code, language, issues
        )

        # Step 6: Performance tips
        performance_tips = await self._get_performance_tips(code, language)

        # Step 7: Security concerns
        security_concerns = [
            i.description for i in issues if i.issue_type == IssueType.SECURITY
        ]

        # Generate overall feedback
        overall_feedback = f"""
Code Quality Analysis Complete

Total Functions/Classes: ~{code.count("def") + code.count("class")}
Lines of Code: {len(code.splitlines())}
Complexity: {"High" if len(code) > 500 else "Medium" if len(code) > 200 else "Low"}
Issues Found: {len(issues)}
Quality Score: {quality_score:.0f}/100

Key Findings:
- {len([i for i in issues if i.issue_type == IssueType.STYLE])} style issues
- {len([i for i in issues if i.issue_type == IssueType.PERFORMANCE])} performance concerns
- {len([i for i in issues if i.issue_type == IssueType.SECURITY])} security issues
- {len([i for i in issues if i.issue_type == IssueType.LOGIC])} logic errors
"""

        result = CodeReviewResult(
            code_hash=code_hash,
            total_issues=len(issues),
            issues=issues,
            quality_score=quality_score,
            overall_feedback=overall_feedback,
            refactoring_recommendations=refactoring_suggestions,
            performance_tips=performance_tips,
            security_concerns=security_concerns,
        )

        # Store in memory
        await self.memory.record_snippet(
            id=code_hash,
            code=code,
            language=language,
            description=f"Code Review - Quality: {quality_score:.0f}",
            tags=["reviewed", "analyzed"],
            metadata={
                "quality_score": quality_score,
                "total_issues": len(issues),
                "security_issues": len(security_concerns),
            },
        )

        return result

    async def suggest_refactoring(
        self, code: str, language: str = "python", focus_area: str = "readability"
    ) -> RefactoringPlan | None:
        """
        Suggest refactoring improvements.

        Args:
            code: Code to refactor
            language: Programming language
            focus_area: What to focus on (readability, performance, testability)

        Returns:
            RefactoringPlan with suggested changes
        """
        prompt = f"""
Refactor this {language} code focusing on {focus_area}:

```{language}
{code}
```

Provide:
1. Improved version of the code
2. Summary of changes made
3. Expected benefits

Keep the improved code in a code block with triple backticks."""

        response = await self.brain.think(prompt)

        # Extract improved code from response (simplified)
        suggested_code = code  # Placeholder
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 2:
                suggested_code = parts[1].strip()

        return RefactoringPlan(
            before_code=code,
            suggested_code=suggested_code,
            changes_summary=f"Refactoring focused on {focus_area}",
            expected_benefits={
                "readability": focus_area == "readability",
                "performance": focus_area == "performance",
                "testability": focus_area == "testability",
            },
        )

    async def get_performance_tips(
        self, code: str, language: str = "python"
    ) -> AsyncIterator[str]:
        """Stream performance optimization tips"""
        prompt = f"""
Analyze this {language} code for performance:

```{language}
{code}
```

List 5 specific performance tips in order of impact.
Format each tip on a new line starting with "- "."""

        async for chunk in self.brain.stream_think(prompt):
            yield chunk

    async def detect_bugs(self, code: str) -> list[str]:
        """Detect potential bugs in code"""
        prompt = f"""
Find potential bugs or issues in this Python code:

```python
{code}
```

List each bug as:
BUG: [description]
FIX: [suggested fix]

Keep it concise."""

        response = await self.brain.think(prompt)
        bugs = [line for line in response.split("\n") if line.startswith("BUG:")]
        return bugs

    async def explain_functionality(self, code: str) -> AsyncIterator[str]:
        """Stream explanation of what code does"""
        prompt = f"""
Explain what this code does in clear, simple terms.
Focus on the main purpose and key operations.

```python
{code}
```

Explanation:"""

        async for chunk in self.brain.stream_think(prompt):
            yield chunk

    async def _get_refactoring_suggestions(
        self, code: str, language: str, issues: list[CodeIssue]
    ) -> list[str]:
        """Generate refactoring suggestions based on issues"""
        suggestions = []

        style_issues = [i for i in issues if i.issue_type == IssueType.STYLE]
        if style_issues:
            suggestions.append("Improve code formatting and style (PEP 8)")

        perf_issues = [i for i in issues if i.issue_type == IssueType.PERFORMANCE]
        if perf_issues:
            suggestions.append("Optimize loops and data structures")

        if len(code) > 500:
            suggestions.append("Break into smaller functions")

        if code.count("\n") > 50:
            suggestions.append("Extract helper functions for clarity")

        return suggestions

    async def _get_performance_tips(self, code: str, language: str) -> list[str]:
        """Generate performance optimization tips"""
        tips = []

        if "for" in code and "append" in code:
            tips.append("Use list comprehensions instead of append loops")

        if ".copy()" in code:
            tips.append("Minimize copy operations for large structures")

        if "import" in code and ".*" in code:
            tips.append("Use specific imports instead of * imports")

        if code.count("if") > 10:
            tips.append("Consider using a switch/case pattern or dict lookup")

        return tips


class CodeMentor:
    """
    Interactive code mentor combining Teaching + Coding skills.
    """

    def __init__(self, skill: CodingSkill):
        """Initialize code mentor"""
        self.skill = skill

    async def analyze_and_teach(
        self, code: str, language: str = "python"
    ) -> dict[str, Any]:
        """Analyze code and provide teaching feedback"""

        review = await self.skill.review_code(code, language)

        teaching_feedback = {
            "quality_score": review.quality_score,
            "issues_found": review.total_issues,
            "critical_issues": [
                i.description for i in review.issues if i.severity >= 4
            ],
            "learning_points": [
                i.suggestion
                for i in review.issues[:3]  # Top 3 lessons
            ],
            "refactoring_focus": review.refactoring_recommendations[0]
            if review.refactoring_recommendations
            else "Code quality",
        }

        return teaching_feedback
