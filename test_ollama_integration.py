"""
Week 1 + Ollama Integration Test
Tests that Brain can actually stream responses from local TinyLlama
Run with: uv run python test_ollama_integration.py
"""

import asyncio
from providers.brain import Brain
from providers.intent_detector import IntentDetector
from providers.model_selector import ModelSelector
from providers.local.ollama_engine import OllamaEngine

async def main():
    print("=" * 70)
    print("WEEK 1 + OLLAMA LIVE INTEGRATION TEST")
    print("=" * 70)
    
    # Initialize with TinyLlama
    print("\n[1] Initializing components...")
    ollama = OllamaEngine(model_name="tinyllama")
    
    # Check connection
    print("[2] Checking Ollama connection...")
    is_ready = await ollama.check_connection()
    if not is_ready:
        print("  ✗ Ollama not responding. Make sure Ollama is running!")
        return False
    print("  ✓ Ollama connected")
    
    # List models
    print("[3] Listing available models...")
    models = await ollama.list_models()
    for model in models:
        # Model is a dict from the API
        model_name = model.get("name", "unknown") if isinstance(model, dict) else model.name
        print(f"  ✓ {model_name}")
    
    # Create Brain
    print("\n[4] Creating Brain with TinyLlama...")
    brain = Brain(ollama)
    print("  ✓ Brain initialized")
    
    # Test intent detection + model selection + streaming
    test_cases = [
        ("explain what machine learning is", "teaching")
    ]
    
    print("\n[5] Testing live inference...")
    for user_input, expected_intent in test_cases:
        print(f"\n  Input: '{user_input}'")
        print(f"  Expected: {expected_intent}")
        
        print(f"  Response: ", end="", flush=True)
        
        try:
            response = ""
            async for chunk in brain.stream_think(user_input):
                print(chunk, end="", flush=True)
                response += chunk
            
            print("\n  ✓ Response complete")
            
            # Show reasoning
            reasoning = brain.get_last_reasoning()
            print(f"  Debug: Intent={reasoning['intent']}, "
                  f"Model={reasoning['model']}, "
                  f"Confidence={reasoning['intent_confidence']:.0%}")
            
        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            return False
    
    print("\n" + "=" * 70)
    print("✓ LIVE INTEGRATION TEST PASSED - Ready for Week 2!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
