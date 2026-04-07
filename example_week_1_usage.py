"""
WEEK 1 Integration Example
Shows how Brain, IntentDetection, and ModelSelection work together
Run with: uv run python example_week_1_usage.py
"""

import asyncio

from providers.brain import Brain
from providers.intent_detector import IntentDetector
from providers.local.ollama_engine import OllamaEngine
from providers.model_selector import ModelSelector


async def main():
    print("=" * 70)
    print("WEEK 1 INTEGRATION EXAMPLE: Brain + Intent + Model Selection")
    print("=" * 70)

    # Initialize components
    print("\n[Setup] Initializing components...")
    ollama = OllamaEngine(model_name="mistral")  # Note: requires Ollama running
    intent_detector = IntentDetector()
    model_selector = ModelSelector()
    brain = Brain(ollama, intent_detector, model_selector)
    print("✓ Brain initialized with OllamaEngine (mistral)")

    # Test cases covering different intents
    test_inputs = [
        "explain how recursion works",
        "write a function to sort a list",
        "solve 3x + 7 = 22",
        "remember my favorite coffee is espresso",
    ]

    print("\n" + "=" * 70)
    print("INTENT DETECTION PIPELINE")
    print("=" * 70)

    for user_input in test_inputs:
        print(f"\n▶ Input: '{user_input}'")

        # Step 1: Detect intent
        intent_result = intent_detector.detect(user_input)
        print(
            f"  → Intent: {intent_result.primary_intent.value.upper():12} "
            f"(confidence: {intent_result.confidence:.0%})"
        )

        # Step 2: Select model
        model_result = model_selector.select(intent_result)
        print(
            f"  → Model: {model_result.selected_model.value.upper():12}    "
            f"(confidence: {model_result.confidence:.0%})"
        )

        # Step 3: Get system prompt (what the model will use)
        system_prompt = brain._get_system_prompt(intent_result.primary_intent)
        prompt_preview = system_prompt.split("\n")[0][:50]
        print(f"  → Prompt: {prompt_preview}...")

    print("\n" + "=" * 70)
    print("REASONING TRACKING (DEBUG INFO)")
    print("=" * 70)

    # Simulate a thinking operation
    print("\nProcessing: 'explain what a REST API is'")
    user_input = "explain what a REST API is"

    # Note: This would stream from Ollama if it's running
    # For this example, we'll just track the reasoning
    intent_result = intent_detector.detect(user_input)
    model_result = model_selector.select(intent_result)

    # Store reasoning (like Brain does)
    reasoning = {
        "user_input": user_input,
        "intent": intent_result.primary_intent.value,
        "intent_confidence": intent_result.confidence,
        "model": model_result.selected_model.value,
        "model_confidence": model_result.confidence,
        "reasoning_text": model_result.reasoning,
    }

    print("\nStored Reasoning:")
    for key, value in reasoning.items():
        if isinstance(value, float):
            print(f"  {key:20} = {value:.0%}")
        else:
            print(f"  {key:20} = {value}")

    print("\n" + "=" * 70)
    print("INTENT DISTRIBUTION ANALYSIS")
    print("=" * 70)

    # Analyze intent distribution across test cases
    intent_counts = {}
    for user_input in test_inputs:
        result = intent_detector.detect(user_input)
        intent = result.primary_intent.value
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\nIntent Distribution:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent:15} : {'█' * count} ({count})")

    print("\n" + "=" * 70)
    print("MODEL SELECTION DISTRIBUTION")
    print("=" * 70)

    # Analyze model selection distribution
    model_counts = {}
    for user_input in test_inputs:
        intent_result = intent_detector.detect(user_input)
        model_result = model_selector.select(intent_result)
        model = model_result.selected_model.value
        model_counts[model] = model_counts.get(model, 0) + 1

    print("\nModel Selection Distribution:")
    for model, count in sorted(model_counts.items()):
        print(f"  {model:15} : {'█' * count} ({count})")

    print("\n" + "=" * 70)
    print("ACTUAL INFERENCE (requires Ollama running)")
    print("=" * 70)

    print("\nTo test actual inference:")
    print("1. Start Ollama in another terminal: ollama serve")
    print("2. Run this script")
    print("3. Brain will stream responses from the local model")
    print("\nExample async code:")
    print("""
    async for chunk in brain.stream_think("explain recursion"):
        print(chunk, end='', flush=True)
    """)

    print("\n" + "=" * 70)
    print("✓ WEEK 1 INTEGRATION EXAMPLE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
