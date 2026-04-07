"""
Adaptive Model Selection System
Automatically selects appropriate model based on intent and context
"""

import logging
from dataclasses import dataclass
from enum import Enum

from providers.intent_detector import Intent, IntentResult

logger = logging.getLogger(__name__)


class ModelChoice(Enum):
    """Available model tiers"""

    TINYLLAMA = "tinyllama"  # 1.1B - Fast, good for teaching
    PHI_2 = "phi-2"  # 2.7B - Better for code, reasoning
    MISTRAL = "mistral"  # 7B - Fallback, most capable


@dataclass
class ModelSelectionResult:
    """Result of model selection"""

    selected_model: ModelChoice
    confidence: float  # 0.0 to 1.0
    reasoning: str
    fallback_model: ModelChoice | None = None


class ModelSelector:
    """
    Selects optimal model based on:
    - Intent (code vs teaching vs reasoning)
    - Input complexity
    - Estimated time budget
    - Hardware availability
    """

    # Intent scoring for each model
    INTENT_SCORES = {
        Intent.TEACHING: {
            ModelChoice.TINYLLAMA: 0.9,  # Best for teaching
            ModelChoice.PHI_2: 0.7,
            ModelChoice.MISTRAL: 0.8,
        },
        Intent.CODE: {
            ModelChoice.TINYLLAMA: 0.5,
            ModelChoice.PHI_2: 0.95,  # Best for code
            ModelChoice.MISTRAL: 1.0,
        },
        Intent.REASONING: {
            ModelChoice.TINYLLAMA: 0.7,
            ModelChoice.PHI_2: 0.85,
            ModelChoice.MISTRAL: 1.0,
        },
        Intent.MEMORY: {
            ModelChoice.TINYLLAMA: 0.95,  # Simple operations
            ModelChoice.PHI_2: 0.8,
            ModelChoice.MISTRAL: 0.7,
        },
        Intent.CLARIFICATION: {
            ModelChoice.TINYLLAMA: 0.8,  # Quick response
            ModelChoice.PHI_2: 0.75,
            ModelChoice.MISTRAL: 0.7,
        },
        Intent.OTHER: {
            ModelChoice.TINYLLAMA: 0.7,  # Default, balanced
            ModelChoice.PHI_2: 0.8,
            ModelChoice.MISTRAL: 0.9,
        },
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        "high": [
            r"\b(complex|advanced|deep|sophisticated|intricate)\b",
            r"\b(architecture|design pattern|algorithm|optimization)\b",
            r"\b(multi-step|recursive|concurrent|distributed)\b",
        ],
        "medium": [
            r"\b(implement|fix|refactor|improve)\b",
            r"\b(function|method|class|module)\b",
        ],
        "low": [
            r"\b(simple|basic|quick|easy|straightforward)\b",
            r"\b(what|explain|describe)\b",
        ],
    }

    def __init__(self):
        """Initialize model selector"""
        self.model_availability = {
            ModelChoice.TINYLLAMA: True,  # Assume available
            ModelChoice.PHI_2: True,
            ModelChoice.MISTRAL: True,
        }
        logger.debug("ModelSelector initialized")

    def select(
        self, intent_result: IntentResult, input_length: int = 0
    ) -> ModelSelectionResult:
        """
        Select best model for user input.

        Args:
            intent_result: Result from intent detection
            input_length: Length of user input (for complexity estimation)

        Returns:
            ModelSelectionResult with selected model and reasoning
        """
        primary_intent = intent_result.primary_intent
        intent_confidence = intent_result.confidence

        # Step 1: Get base scores from intent
        scores = self._score_by_intent(primary_intent)

        # Step 2: Adjust scores by input complexity
        complexity_score = self._estimate_complexity(intent_result.reasoning)
        scores = self._adjust_by_complexity(scores, complexity_score)

        # Step 3: Filter by availability
        available_scores = {
            model: score
            for model, score in scores.items()
            if self.model_availability.get(model, False)
        }

        if not available_scores:
            # Fallback: all models should be available
            logger.warning("No models available! Using fallback")
            return ModelSelectionResult(
                selected_model=ModelChoice.TINYLLAMA,
                confidence=0.5,
                reasoning="No models available - using default fallback",
                fallback_model=ModelChoice.PHI_2,
            )

        # Step 4: Select best available model
        selected_model = max(available_scores, key=available_scores.get)
        confidence = available_scores[selected_model]

        # Step 5: Determine fallback
        remaining = [(m, s) for m, s in available_scores.items() if m != selected_model]
        fallback = max(remaining, key=lambda x: x[1])[0] if remaining else None

        reasoning = (
            f"Intent: {primary_intent.value} (confidence: {intent_confidence:.0%}), "
            f"Complexity: {complexity_score:.0%}, "
            f"Model score: {confidence:.0%}"
        )

        logger.debug(
            "Model selection: %s (score: %.2f)", selected_model.value, confidence
        )

        return ModelSelectionResult(
            selected_model=selected_model,
            confidence=confidence,
            reasoning=reasoning,
            fallback_model=fallback,
        )

    def _score_by_intent(self, intent: Intent) -> dict[ModelChoice, float]:
        """Get model scores based on intent"""
        return self.INTENT_SCORES.get(
            intent,
            {
                ModelChoice.TINYLLAMA: 0.7,
                ModelChoice.PHI_2: 0.8,
                ModelChoice.MISTRAL: 0.9,
            },
        )

    def _estimate_complexity(self, reasoning: str) -> float:
        """
        Estimate input complexity from reasoning text.

        Returns:
            Score from 0.0 (simple) to 1.0 (complex)
        """
        text = reasoning.lower()

        # Check high complexity indicators
        for indicator in self.COMPLEXITY_INDICATORS.get("high", []):
            if any(word in indicator for word in text.split()):
                return 0.8

        # Check medium complexity
        for indicator in self.COMPLEXITY_INDICATORS.get("medium", []):
            if any(word in indicator for word in text.split()):
                return 0.5

        # Default to low complexity
        return 0.3

    def _adjust_by_complexity(
        self, scores: dict[ModelChoice, float], complexity: float
    ) -> dict[ModelChoice, float]:
        """
        Adjust model scores based on complexity.
        Higher complexity → prefer more capable models
        """
        adjusted = {}

        for model, base_score in scores.items():
            if complexity > 0.7:
                # High complexity: prefer Mistral > Phi-2 > TinyLlama
                if model == ModelChoice.TINYLLAMA:
                    adjusted[model] = base_score * 0.8  # Reduce for simple model
                elif model == ModelChoice.PHI_2:
                    adjusted[model] = base_score * 1.1  # Boost for medium
                else:
                    adjusted[model] = base_score * 1.3  # Boost for most capable
            else:
                # Low complexity: prefer TinyLlama (faster)
                if model == ModelChoice.TINYLLAMA:
                    adjusted[model] = base_score * 1.2  # Boost for speed
                else:
                    adjusted[model] = base_score * 0.9  # Reduce overkill

            # Cap at 1.0
            adjusted[model] = min(adjusted[model], 1.0)

        return adjusted

    def set_model_availability(self, model: ModelChoice, available: bool):
        """Update model availability (e.g., if download fails)"""
        self.model_availability[model] = available
        logger.info("Model %s availability set to %s", model.value, available)

    def explain_selection(self, result: ModelSelectionResult) -> str:
        """Human-readable explanation of model selection"""
        return (
            f"Selected model: {result.selected_model.value}\n"
            f"Confidence: {result.confidence:.0%}\n"
            f"Reasoning: {result.reasoning}\n"
            f"Fallback: {result.fallback_model.value if result.fallback_model else 'None'}"
        )
