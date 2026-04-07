"""
Tools Framework
Registers and manages executable tools (exams, code execution, etc)
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Metadata for a tool"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable
    is_async: bool = False


@dataclass
class ToolCall:
    """A parsed tool call from LLM output"""

    tool_name: str
    arguments: dict[str, Any]
    tool_use_id: str = ""


@dataclass
class ToolResult:
    """Result from tool execution"""

    tool_name: str
    success: bool
    result: Any
    error: str | None = None
    execution_time_ms: float = 0.0


class ToolRegistry:
    """
    Registry for tools that can be called by the model.

    Tools are functions that:
    1. Take JSON-serializable arguments
    2. Return JSON-serializable results
    3. Can be async or sync
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        logger.info("ToolRegistry initialized")

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable,
        is_async: bool = False,
    ) -> None:
        """
        Register a new tool.

        Args:
            name: Tool identifier (e.g., "generate_exam")
            description: Human-readable description
            parameters: JSON Schema of parameters
            handler: Callable that executes the tool
            is_async: Whether handler is async
        """
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            is_async=is_async,
        )

        self._tools[name] = tool_def
        logger.info(f"Registered tool: {name}")

    def get_tools(self) -> list[ToolDefinition]:
        """Get all registered tools"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get tool by name"""
        return self._tools.get(name)

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of tool to execute
            arguments: Arguments to pass to tool

        Returns:
            ToolResult with execution result or error
        """
        tool_def = self.get_tool(tool_name)
        if not tool_def:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Unknown tool: {tool_name}",
            )

        try:
            # Execute with timing
            start_time = asyncio.get_event_loop().time()

            if tool_def.is_async:
                result = await tool_def.handler(**arguments)
            else:
                result = tool_def.handler(**arguments)

            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000

            logger.info(f"Tool '{tool_name}' executed in {execution_time:.0f}ms")

            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {e}")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
            )

    def to_schema(self) -> list[dict[str, Any]]:
        """
        Convert tools to OpenAI function format for LLM.

        Returns:
            List of function schemas
        """
        schemas = []
        for tool in self.get_tools():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            schemas.append(schema)
        return schemas


class ToolParser:
    """Parses tool calls from LLM output"""

    @staticmethod
    def parse_from_text(text: str) -> list[ToolCall]:
        """
        Parse tool calls from model output.

        Looks for patterns like:
        <tool_call>{"tool": "name", "args": {...}}</tool_call>
        or
        ```json
        {"action": "tool_name", ...}
        ```

        Args:
            text: LLM output text

        Returns:
            List of parsed ToolCall objects
        """
        tool_calls = []

        # Look for XML-style tool calls
        import re

        pattern = r"<tool_call>(.*?)</tool_call>"
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                tool_call = ToolCall(
                    tool_name=data.get("tool", data.get("action", "")),
                    arguments=data.get("args", data.get("arguments", {})),
                )
                if tool_call.tool_name:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                pass

        # Look for JSON code blocks
        pattern = r"```(?:json)?\s*({.*?})\s*```"
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                if "tool" in data or "action" in data:
                    tool_call = ToolCall(
                        tool_name=data.get("tool", data.get("action", "")),
                        arguments=data.get("args", data.get("arguments", {})),
                    )
                    if tool_call.tool_name:
                        tool_calls.append(tool_call)
            except json.JSONDecodeError:
                pass

        return tool_calls


# Standard tool definitions
EXAM_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string",
            "description": "Exam topic (e.g., 'Python basics')",
        },
        "num_questions": {
            "type": "integer",
            "description": "Number of questions (1-10)",
            "minimum": 1,
            "maximum": 10,
        },
        "difficulty": {
            "type": "integer",
            "description": "Difficulty level (1-5)",
            "minimum": 1,
            "maximum": 5,
        },
    },
    "required": ["topic"],
}

CODE_EXECUTION_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": "Python code to execute",
        },
        "timeout": {
            "type": "number",
            "description": "Execution timeout in seconds",
            "default": 5.0,
        },
    },
    "required": ["code"],
}
