"""
Hybrid Intent Detection System
Combines regex patterns, keyword scoring, and clarification logic
to accurately identify user intent.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Primary intent categories"""

    TEACHING = "teaching"  # Explanations, learning, how-tos
    CODE = "code"  # Code generation, debugging, refactoring
    REASONING = "reasoning"  # Math, logic, analysis, problem-solving
    MEMORY = "memory"  # Store/retrieve memory commands
    CLARIFICATION = "clarification"  # User needs to clarify
    OTHER = "other"  # Unclassified


@dataclass
class IntentResult:
    """Result of intent detection"""

    primary_intent: Intent
    confidence: float  # 0.0 to 1.0
    keywords: list[str] = field(default_factory=list)
    patterns_matched: list[str] = field(default_factory=list)
    reasoning: str = ""


class IntentDetector:
    """Hybrid intent detection using regex, keywords, and scoring"""

    # Regex patterns for each intent
    PATTERNS = {
        Intent.CODE: [
            r"\b(def|class|function|import|export|const|let|var|function)\b",
            r"\b(debug|fix|error|bug|exception|stack trace|traceback)\b",
            r"\b(code|script|program|refactor|optimize|algorithm)\b",
            r"```(\w+)",  # Code block language marker
            r"(\.py|\.js|\.ts|\.java|\.cpp|\.go|\.rs)\b",  # File extensions
        ],
        Intent.TEACHING: [
            r"\b(explain|how to|what is|teach|tutorial|guide|step by step)\b",
            r"\b(understand|learn|learning|educational|concept|idea)\b",
            r"\b(why|describe|tell me about|what does|meaning)\b",
            r"^(how|what|explain|describe|teach)\b",  # Start of sentence
        ],
        Intent.REASONING: [
            r"\b(calculate|math|solve|equation|formula|prove|logical)\b",
            r"\b(analyze|analysis|reasoning|think through|work through)\b",
            r"\b(problem|puzzle|riddle|challenge)\b",
            r"(\d+\s*[+\-*/=]|√|∑|∫|∞)",  # Math symbols
        ],
        Intent.MEMORY: [
            r"\b(remember|memorize|store|save|recall|memory|forgot)\b",
            r"^(jarvis\s+)?(remember|store|save|recall)",  # Memory commands
            r"'remember|'store|'save",  # Command markers
        ],
    }

    # Keywords for keyword scoring
    KEYWORDS = {
        Intent.CODE: {
            "high": [
                "def",
                "class",
                "import",
                "debug",
                "error",
                "bug",
                "code",
                "function",
                "fix",
            ],
            "medium": [
                "implement",
                "write",
                "create",
                "generate",
                "refactor",
                "optimize",
            ],
            "low": ["do", "make", "build"],
        },
        Intent.TEACHING: {
            "high": [
                "explain",
                "teach",
                "tutorial",
                "guide",
                "how to",
                "learn",
                "understand",
            ],
            "medium": ["what", "why", "describe", "example", "show", "demonstrate"],
            "low": ["tell", "say", "hear"],
        },
        Intent.REASONING: {
            "high": ["solve", "calculate", "math", "logic", "analyze", "prove"],
            "medium": ["think", "reason", "problem", "work through", "step by step"],
            "low": ["try", "check", "test"],
        },
        Intent.MEMORY: {
            "high": ["remember", "memorize", "store", "recall", "save", "memory"],
            "medium": ["forget", "remind", "note"],
            "low": [],
        },
    }

    def __init__(self):
        """Initialize detector with compiled patterns"""
        self.compiled_patterns = {}
        for intent, patterns in self.PATTERNS.items():
            self.compiled_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        logger.debug("IntentDetector initialized with %d patterns", len(self.PATTERNS))

    def detect(self, user_input: str) -> IntentResult:
        """
        Detect intent from user input using hybrid approach.

        Returns:
            IntentResult with primary intent and confidence
        """
        # Step 1: Check for memory commands (highest priority)
        memory_score = self._score_patterns(user_input, Intent.MEMORY)
        if memory_score > 0.6:
            return IntentResult(
                primary_intent=Intent.MEMORY,
                confidence=memory_score,
                reasoning="Memory command detected via regex patterns",
            )

        # Step 2: Score all intents using hybrid approach
        scores: dict[Intent, tuple[float, str]] = {}
        for intent in Intent:
            if intent == Intent.MEMORY:
                continue  # Already checked

            pattern_score = self._score_patterns(user_input, intent)
            keyword_score = self._score_keywords(user_input, intent)

            # Weighted average (patterns more reliable than keywords)
            combined_score = (pattern_score * 0.6) + (keyword_score * 0.4)
            scores[intent] = (
                combined_score,
                f"Patterns: {pattern_score:.2f}, Keywords: {keyword_score:.2f}",
            )

        # Step 3: Find best match
        best_intent, (best_score, reasoning) = max(
            scores.items(), key=lambda x: x[1][0]
        )

        # Step 4: Check confidence threshold
        if best_score < 0.3:
            # Low confidence - ask for clarification
            return IntentResult(
                primary_intent=Intent.CLARIFICATION,
                confidence=0.5,
                reasoning=f"Low confidence ({best_score:.2f}) - all intents below threshold",
            )

        # Step 5: Check for competing intents
        top_scores = sorted(scores.values(), key=lambda x: x[0], reverse=True)
        if len(top_scores) > 1 and abs(top_scores[0][0] - top_scores[1][0]) < 0.15:
            # Close call - might need clarification
            logger.warning("Close intent match: %s vs %s", best_intent, top_scores[1])

        return IntentResult(
            primary_intent=best_intent,
            confidence=min(best_score, 1.0),
            reasoning=reasoning,
        )

    def _score_patterns(self, user_input: str, intent: Intent) -> float:
        """
        Score based on regex pattern matches.

        Returns:
            Score from 0.0 to 1.0
        """
        if intent not in self.compiled_patterns:
            return 0.0

        patterns = self.compiled_patterns[intent]
        if not patterns:
            return 0.0

        matches = 0
        for pattern in patterns:
            if pattern.search(user_input):
                matches += 1

        # Normalize: max score approaches 1.0 but doesn't exceed it
        max_matches = len(patterns)
        return min(matches / max_matches, 1.0)

    def _score_keywords(self, user_input: str, intent: Intent) -> float:
        """
        Score based on keyword frequency and weight.

        Returns:
            Score from 0.0 to 1.0
        """
        if intent not in self.KEYWORDS:
            return 0.0

        keywords = self.KEYWORDS[intent]
        text = user_input.lower()
        total_score = 0.0

        # High priority keywords
        for word in keywords.get("high", []):
            matches = len(re.findall(rf"\b{re.escape(word)}\b", text, re.IGNORECASE))
            total_score += matches * 0.5

        # Medium priority keywords
        for word in keywords.get("medium", []):
            matches = len(re.findall(rf"\b{re.escape(word)}\b", text, re.IGNORECASE))
            total_score += matches * 0.3

        # Low priority keywords
        for word in keywords.get("low", []):
            matches = len(re.findall(rf"\b{re.escape(word)}\b", text, re.IGNORECASE))
            total_score += matches * 0.1

        # Normalize: cap at 1.0
        return min(total_score / 2.0, 1.0)

    def get_keywords(self, user_input: str) -> list[str]:
        """Extract relevant keywords from input"""
        words = user_input.lower().split()
        keywords = []

        # Check against all keyword lists
        all_keywords = set()
        for intent_keywords in self.KEYWORDS.values():
            for priority_list in intent_keywords.values():
                all_keywords.update(priority_list)

        for word in words:
            if any(kw in word.lower() for kw in all_keywords):
                keywords.append(word)

        return keywords[:5]  # Return top 5

    def explain_detection(self, intent_result: IntentResult) -> str:
        """Human-readable explanation of detection"""
        return (
            f"Detected intent: {intent_result.primary_intent.value}\n"
            f"Confidence: {intent_result.confidence:.0%}\n"
            f"Reasoning: {intent_result.reasoning}"
        )
