"""
JARVIS-Lite Brain: Core Reasoning Loop
Orchestrates intent detection, model selection, and inference
"""

import asyncio
import logging
from typing import AsyncIterator, Optional, Dict, Any
from datetime import datetime

from providers.intent_detector import IntentDetector, Intent
from providers.model_selector import ModelSelector, ModelChoice
from providers.local.ollama_engine import OllamaEngine

logger = logging.getLogger(__name__)


class Brain:
    """
    Core reasoning engine that:
    1. Detects user intent
    2. Selects appropriate model
    3. Generates and streams responses
    4. Tracks reasoning for debugging
    """

    # System prompts for different intents
    SYSTEM_PROMPTS = {
        Intent.TEACHING: """You are JARVIS-Lite, a helpful AI tutor. Your role is to explain concepts clearly and help users learn. 
- Break down complex ideas into simple steps
- Use examples when helpful
- Ask clarifying questions if needed
- Be patient and encouraging""",

        Intent.CODE: """You are JARVIS-Lite, a skilled code assistant. Your role is to help with programming tasks.
- Provide clear, working code examples
- Explain your approach
- Follow best practices
- Ask for clarification if needed
- Be concise but thorough""",

        Intent.REASONING: """You are JARVIS-Lite, a logical reasoning assistant. Your role is to help solve problems and analyze situations.
- Think through problems step by step
- Show your reasoning
- Consider multiple angles
- Be precise and thorough
- Explain your conclusions""",

        Intent.MEMORY: """You are JARVIS-Lite, managing user preferences and memory.
- Store information the user wants to remember
- Recall relevant context when needed
- Be accurate and reliable""",

        Intent.OTHER: """You are JARVIS-Lite, a helpful AI assistant.
- Provide accurate, helpful responses
- Be clear and concise
- Ask for clarification if needed
- Adapt to the user's needs""",

        Intent.CLARIFICATION: """You are JARVIS-Lite. The user's request is unclear. Ask for clarification:
- What specifically do you need help with?
- Are you asking about [possible interpretation 1] or [possible interpretation 2]?
- More details would help me assist you better.""",
    }

    def __init__(
        self,
        ollama_engine: OllamaEngine,
        intent_detector: Optional[IntentDetector] = None,
        model_selector: Optional[ModelSelector] = None,
    ):
        """
        Initialize Brain with dependencies.

        Args:
            ollama_engine: OllamaEngine instance for inference
            intent_detector: IntentDetector for intent analysis
            model_selector: ModelSelector for model routing
        """
        self.ollama = ollama_engine
        self.intent_detector = intent_detector or IntentDetector()
        self.model_selector = model_selector or ModelSelector()
        
        # Reasoning history for debugging
        self.last_reasoning: Dict[str, Any] = {}
        
        logger.info("Brain initialized with Ollama engine")

    async def think(self, user_input: str) -> str:
        """
        Main reasoning loop - synchronous version.
        
        Args:
            user_input: User's text input
            
        Returns:
            Model response as complete string
        """
        # Collect streaming response
        chunks = []
        async for chunk in self.stream_think(user_input):
            chunks.append(chunk)
        
        return "".join(chunks)

    async def stream_think(self, user_input: str) -> AsyncIterator[str]:
        """
        Main reasoning loop - streaming version.
        Yields response chunks as they arrive.
        
        Args:
            user_input: User's text input
            
        Yields:
            Response chunks (typically 1-2 word tokens)
        """
        try:
            # Step 1: Detect intent
            logger.debug("Step 1: Detecting intent...")
            intent_result = self.intent_detector.detect(user_input)
            
            # Step 2: Select model
            logger.debug("Step 2: Selecting model...")
            model_result = self.model_selector.select(intent_result, len(user_input))
            
            # Step 3: Prepare prompt with system context
            logger.debug("Step 3: Preparing prompt...")
            system_prompt = self._get_system_prompt(intent_result.primary_intent)
            prompt = self._prepare_prompt(user_input, system_prompt, intent_result)
            
            # Step 4: Store reasoning for debugging
            self.last_reasoning = {
                'timestamp': datetime.now().isoformat(),
                'user_input': user_input[:200],  # First 200 chars
                'intent': intent_result.primary_intent.value,
                'intent_confidence': intent_result.confidence,
                'model': model_result.selected_model.value,
                'model_confidence': model_result.confidence,
            }
            
            logger.info(
                "Processing: intent=%s (%.1f%%), model=%s",
                intent_result.primary_intent.value,
                intent_result.confidence * 100,
                model_result.selected_model.value,
            )
            
            # Step 5: Stream response from model
            logger.debug("Step 5: Streaming response...")
            async for chunk in self._stream_from_model(
                prompt,
                model_result.selected_model
            ):
                yield chunk
                
        except Exception as e:
            logger.error("Error in reasoning loop: %s", str(e))
            yield f"\n\n[Error: {str(e)}]"

    def _get_system_prompt(self, intent: Intent) -> str:
        """Get system prompt for the detected intent"""
        return self.SYSTEM_PROMPTS.get(intent, self.SYSTEM_PROMPTS[Intent.OTHER])

    def _prepare_prompt(
        self,
        user_input: str,
        system_prompt: str,
        intent_result: Any,
    ) -> str:
        """
        Prepare final prompt for the model.
        
        Args:
            user_input: User's original input
            system_prompt: Intent-specific system prompt
            intent_result: Result from intent detection
            
        Returns:
            Formatted prompt ready for model
        """
        # Build prompt with system context
        prompt = f"""{system_prompt}

---

User: {user_input}

JARVIS: """
        return prompt

    async def _stream_from_model(
        self,
        prompt: str,
        model_choice: ModelChoice,
    ) -> AsyncIterator[str]:
        """
        Stream response from the selected model.
        
        Args:
            prompt: Prepared prompt for the model
            model_choice: Selected model (TinyLlama, Phi-2, Mistral)
            
        Yields:
            Response chunks from the model
        """
        try:
            # Note: OllamaEngine is initialized with a specific model
            # Dynamic model switching is handled via model selection scoring
            # The actual model used is determined by the OllamaEngine instance
            
            logger.debug("Streaming from model: %s (current: %s)", 
                        model_choice.value, self.ollama.model_name)
            
            # Stream from ollama with parameters based on model choice
            temperature = 0.5 if model_choice == ModelChoice.TINYLLAMA else 0.7
            top_p = 0.85 if model_choice == ModelChoice.TINYLLAMA else 0.9
            
            async for chunk in self.ollama.stream_response(
                prompt,
                temperature=temperature,
                top_p=top_p,
            ):
                yield chunk
                
        except Exception as e:
            logger.error("Error streaming from model: %s", str(e))
            yield f"[Model error: {str(e)}]"

    def get_last_reasoning(self) -> Dict[str, Any]:
        """Get reasoning info from last call (for debugging)"""
        return self.last_reasoning.copy()

    def explain_last_decision(self) -> str:
        """Human-readable explanation of last decision"""
        if not self.last_reasoning:
            return "No reasoning history yet"
        
        reasoning = self.last_reasoning
        return (
            f"Last request:\n"
            f"- Intent: {reasoning['intent']} (confidence: {reasoning['intent_confidence']:.0%})\n"
            f"- Model: {reasoning['model']} (confidence: {reasoning['model_confidence']:.0%})\n"
            f"- Input: {reasoning['user_input']}\n"
            f"- Time: {reasoning['timestamp']}"
        )