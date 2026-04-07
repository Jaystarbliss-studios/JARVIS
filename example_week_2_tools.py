"""
Week 2 Example: Tool Framework
Demonstrates tool registration and execution
Run with: uv run python example_week_2_tools.py
"""

import asyncio

from providers.brain import Brain
from providers.exam_generator import ExamGenerator
from providers.local.ollama_engine import OllamaEngine
from providers.tools import EXAM_TOOL_SCHEMA, ToolParser, ToolRegistry


async def main():
    print("=" * 70)
    print("WEEK 2 TOOL FRAMEWORK EXAMPLE")
    print("=" * 70)

    # Initialize
    print("\n[Setup] Initializing components...")
    ollama = OllamaEngine(model_name="tinyllama")
    brain = Brain(ollama)
    exam_gen = ExamGenerator(brain)
    registry = ToolRegistry()
    print("✓ Components ready")

    # Register tools
    print("\n" + "=" * 70)
    print("REGISTERING TOOLS")
    print("=" * 70)

    # Tool 1: Generate Exam
    async def handle_generate_exam(
        topic: str, num_questions: int = 5, difficulty: int = 3
    ):
        """Handler for exam generation tool"""
        print(
            f"\n  [Tool] Generating exam: topic={topic}, q={num_questions}, d={difficulty}"
        )
        session = await exam_gen.generate_exam(topic, num_questions, difficulty)
        return {
            "exam_id": session.exam_id,
            "topic": session.topic,
            "questions_generated": len(session.questions),
        }

    registry.register(
        name="generate_exam",
        description="Generate a batch of exam questions on a topic",
        parameters=EXAM_TOOL_SCHEMA,
        handler=handle_generate_exam,
        is_async=True,
    )
    print("✓ Registered: generate_exam")

    # Tool 2: Calculate something
    def calculate_difficulty_avg(scores: list) -> float:
        """Calculate average score"""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    registry.register(
        name="calculate_score",
        description="Calculate average score from exam results",
        parameters={
            "type": "object",
            "properties": {
                "scores": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of scores (0-1)",
                }
            },
            "required": ["scores"],
        },
        handler=calculate_difficulty_avg,
    )
    print("✓ Registered: calculate_score")

    # Tool 3: Format results
    def format_exam_results(exam_id: str, score: float, num_questions: int) -> str:
        """Format exam results"""
        percentage = score * 100
        return f"Exam {exam_id}: {percentage:.0f}% ({int(score * num_questions)}/{num_questions})"

    registry.register(
        name="format_results",
        description="Format exam results for display",
        parameters={
            "type": "object",
            "properties": {
                "exam_id": {"type": "string"},
                "score": {"type": "number"},
                "num_questions": {"type": "integer"},
            },
            "required": ["exam_id", "score", "num_questions"],
        },
        handler=format_exam_results,
    )
    print("✓ Registered: format_results")

    # Show tools
    print(f"\n[Tools] Total registered: {len(registry.get_tools())}")
    for tool in registry.get_tools():
        print(f"  - {tool.name}: {tool.description}")

    # Show schema
    print("\n" + "=" * 70)
    print("TOOL SCHEMAS (for LLM)")
    print("=" * 70)
    schemas = registry.to_schema()
    for schema in schemas:
        print(f"\n{schema['function']['name']}:")
        print(f"  Description: {schema['function']['description']}")

    # Execute tools
    print("\n" + "=" * 70)
    print("EXECUTING TOOLS")
    print("=" * 70)

    # Execute calculate_score
    print("\n[1] Executing: calculate_score")
    result = await registry.execute(
        "calculate_score", {"scores": [0.8, 0.9, 0.7, 1.0, 0.85]}
    )
    print(f"    Result: {result.result:.2f} (avg score)")
    print(f"    Time: {result.execution_time_ms:.1f}ms")

    # Execute format_results
    print("\n[2] Executing: format_results")
    result = await registry.execute(
        "format_results", {"exam_id": "exam_001", "score": 0.86, "num_questions": 5}
    )
    print(f"    Result: {result.result}")
    print(f"    Time: {result.execution_time_ms:.1f}ms")

    # Parse tool calls from text
    print("\n" + "=" * 70)
    print("PARSING TOOL CALLS FROM LLM OUTPUT")
    print("=" * 70)

    example_output = """
The exam results show good understanding. Let me calculate the stats:
<tool_call>{"tool": "calculate_score", "args": {"scores": [0.95, 0.88, 0.92]}}</tool_call>

Now formatting for display:
<tool_call>{"tool": "format_results", "args": {"exam_id": "test123", "score": 0.917, "num_questions": 3}}</tool_call>

Overall, this is excellent performance!
"""

    print("\nExample LLM output:")
    print(example_output)

    print("Parsing tool calls...")
    calls = ToolParser.parse_from_text(example_output)
    print(f"Found {len(calls)} tool call(s):")
    for i, call in enumerate(calls, 1):
        print(f"  {i}. {call.tool_name}({call.arguments})")

    print("\n" + "=" * 70)
    print("✓ TOOL FRAMEWORK DEMONSTRATION COMPLETE")
    print("=" * 70)

    print("\nKey features:")
    print("  - Tool registration with async/sync support")
    print("  - Tool execution with timing")
    print("  - OpenAI-compatible schema generation")
    print("  - Automatic parsing from LLM output")
    print("  - Error handling and fallback")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
