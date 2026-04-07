"""
Week 1 Tests: Brain, Intent Detection, and Model Selection
Tests core reasoning loop components (16+ test cases)
"""

from unittest.mock import AsyncMock, Mock

import pytest

from providers.brain import Brain
from providers.intent_detector import Intent, IntentDetector, IntentResult
from providers.model_selector import ModelChoice, ModelSelector


class TestIntentDetector:
    """Test suit for hybrid intent detection"""

    def setup_method(self):
        """Setup for each test"""
        self.detector = IntentDetector()

    def test_detect_code_intent_with_regex(self):
        """Test code detection via regex patterns"""
        inputs = [
            "def hello(): pass",
            "import numpy",
            "class MyClass: pass",
            "fix this bug",
            "debug the error",
        ]

        for user_input in inputs:
            result = self.detector.detect(user_input)
            assert result.primary_intent == Intent.CODE, f"Failed for: {user_input}"
            assert result.confidence > 0.5, f"Low confidence for: {user_input}"

    def test_detect_teaching_intent(self):
        """Test teaching detection"""
        inputs = [
            "explain how this works",
            "teach me recursion",
            "what is a database",
            "how to use APIs",
            "describe the algorithm",
        ]

        for user_input in inputs:
            result = self.detector.detect(user_input)
            assert result.primary_intent == Intent.TEACHING, f"Failed for: {user_input}"
            assert result.confidence > 0.4, f"Low confidence for: {user_input}"

    def test_detect_reasoning_intent(self):
        """Test reasoning/math detection"""
        inputs = [
            "solve x + 5 = 10",
            "analyze this problem",
            "think through this logic",
            "calculate 2^8",
        ]

        for user_input in inputs:
            result = self.detector.detect(user_input)
            assert result.primary_intent == Intent.REASONING, (
                f"Failed for: {user_input}"
            )

    def test_detect_memory_intent(self):
        """Test memory command detection"""
        inputs = [
            "remember my name is John",
            "save this for later",
            "jarvis remember: coffee at 3pm",
            "recall my preferences",
        ]

        for user_input in inputs:
            result = self.detector.detect(user_input)
            assert result.primary_intent == Intent.MEMORY, f"Failed for: {user_input}"

    def test_clarification_for_low_confidence(self):
        """Test clarification request for ambiguous input"""
        # Very short, ambiguous input
        result = self.detector.detect("x")
        assert result.primary_intent == Intent.CLARIFICATION or result.confidence < 0.35

    def test_confidence_scores_are_valid(self):
        """Test that confidence scores are between 0 and 1"""
        test_inputs = [
            "hello",
            "def foo(): pass",
            "explain this",
            "remember x",
        ]

        for user_input in test_inputs:
            result = self.detector.detect(user_input)
            assert 0.0 <= result.confidence <= 1.0, (
                f"Invalid confidence {result.confidence} for {user_input}"
            )

    def test_pattern_matching(self):
        """Test regex pattern compilation and matching"""
        assert len(self.detector.compiled_patterns) > 0

        # Test that patterns exist for each intent
        for intent in [Intent.CODE, Intent.TEACHING, Intent.REASONING, Intent.MEMORY]:
            assert intent in self.detector.compiled_patterns
            assert len(self.detector.compiled_patterns[intent]) > 0

    def test_keyword_extraction(self):
        """Test keyword extraction from input"""
        text = "explain how to debug this python code"
        keywords = self.detector.get_keywords(text)

        # Should extract relevant keywords
        assert len(keywords) > 0
        assert any(kw.lower() in text.lower() for kw in keywords)


class TestModelSelector:
    """Test suite for adaptive model selection"""

    def setup_method(self):
        """Setup for each test"""
        self.selector = ModelSelector()

    def test_select_tinyllama_for_teaching(self):
        """Test that TinyLlama is preferred for teaching"""
        intent_result = IntentResult(
            primary_intent=Intent.TEACHING,
            confidence=0.9,
            reasoning="Clear teaching intent",
        )

        result = self.selector.select(intent_result)
        assert result.selected_model == ModelChoice.TINYLLAMA
        assert result.confidence > 0.7

    def test_select_phi2_for_code(self):
        """Test that Phi-2 is preferred for code"""
        intent_result = IntentResult(
            primary_intent=Intent.CODE, confidence=0.9, reasoning="Clear code intent"
        )

        result = self.selector.select(intent_result)
        assert result.selected_model == ModelChoice.PHI_2
        assert result.confidence > 0.7

    def test_select_tinyllama_for_memory(self):
        """Test that TinyLlama is preferred for memory"""
        intent_result = IntentResult(
            primary_intent=Intent.MEMORY, confidence=0.9, reasoning="Memory command"
        )

        result = self.selector.select(intent_result)
        assert result.selected_model == ModelChoice.TINYLLAMA

    def test_fallback_model_is_set(self):
        """Test that fallback model is always available"""
        intent_result = IntentResult(
            primary_intent=Intent.CODE, confidence=0.9, reasoning="Code intent"
        )

        result = self.selector.select(intent_result)
        assert result.fallback_model is not None
        assert result.fallback_model != result.selected_model

    def test_complexity_adjustment(self):
        """Test that complexity adjusts model scores"""
        # Simple input
        simple_result = self.selector._adjust_by_complexity(
            {ModelChoice.TINYLLAMA: 0.7, ModelChoice.PHI_2: 0.5}, complexity=0.2
        )
        assert simple_result[ModelChoice.TINYLLAMA] > simple_result[ModelChoice.PHI_2]

        # Complex input
        complex_result = self.selector._adjust_by_complexity(
            {ModelChoice.TINYLLAMA: 0.7, ModelChoice.PHI_2: 0.5}, complexity=0.8
        )
        assert complex_result[ModelChoice.PHI_2] > complex_result[ModelChoice.TINYLLAMA]

    def test_model_availability_affects_selection(self):
        """Test that unavailable models are not selected"""
        # Mark Phi-2 as unavailable
        self.selector.set_model_availability(ModelChoice.PHI_2, False)

        intent_result = IntentResult(
            primary_intent=Intent.CODE, confidence=0.9, reasoning="Code intent"
        )

        result = self.selector.select(intent_result)
        assert result.selected_model != ModelChoice.PHI_2

    def test_selection_scores_normalized(self):
        """Test that selection scores are normalized to 0-1"""
        intent_result = IntentResult(
            primary_intent=Intent.CODE, confidence=0.9, reasoning="Code intent"
        )

        result = self.selector.select(intent_result)
        assert 0.0 <= result.confidence <= 1.0


class TestBrain:
    """Test suite for Brain core reasoning loop"""

    @pytest.fixture
    def mock_ollama(self):
        """Mock OllamaEngine"""
        mock = AsyncMock()
        mock.list_models = AsyncMock(
            return_value=[
                Mock(name="mistral"),
                Mock(name="tinyllama"),
                Mock(name="phi"),
            ]
        )
        return mock

    @pytest.fixture
    def brain(self, mock_ollama):
        """Create Brain instance with mocks"""
        return Brain(
            ollama_engine=mock_ollama,
            intent_detector=IntentDetector(),
            model_selector=ModelSelector(),
        )

    @pytest.mark.asyncio
    async def test_brain_initialization(self, brain):
        """Test Brain initialization"""
        assert brain.ollama is not None
        assert brain.intent_detector is not None
        assert brain.model_selector is not None
        assert brain.last_reasoning == {}

    @pytest.mark.asyncio
    async def test_think_returns_string(self, brain, mock_ollama):
        """Test that think() returns string response"""

        # Mock streaming response
        async def mock_stream(*args, **kwargs):
            for chunk in ["Hello", " ", "world", "!"]:
                yield chunk

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        result = await brain.think("test input")
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_stream_think_yields_chunks(self, brain, mock_ollama):
        """Test that stream_think yields response chunks"""

        # Mock streaming response
        async def mock_stream(*args, **kwargs):
            for chunk in ["Test", " ", "response"]:
                yield chunk

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        chunks = []
        async for chunk in brain.stream_think("test input"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "".join(chunks) == "Test response"

    @pytest.mark.asyncio
    async def test_reasoning_is_tracked(self, brain, mock_ollama):
        """Test that reasoning is stored for debugging"""

        async def mock_stream(*args, **kwargs):
            yield "response"

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        await brain.think("test input")

        reasoning = brain.get_last_reasoning()
        assert reasoning["user_input"] == "test input"
        assert "intent" in reasoning
        assert "model" in reasoning
        assert "timestamp" in reasoning

    @pytest.mark.asyncio
    async def test_explain_last_decision(self, brain, mock_ollama):
        """Test that decision explanation is readable"""

        async def mock_stream(*args, **kwargs):
            yield "response"

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        await brain.think("def foo(): pass")

        explanation = brain.explain_last_decision()
        assert "Intent:" in explanation
        assert "Model:" in explanation
        assert "confidence" in explanation

    @pytest.mark.asyncio
    async def test_code_routing(self, brain, mock_ollama):
        """Test that code inputs route to appropriate model"""

        async def mock_stream(*args, **kwargs):
            yield "response"

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)
        mock_ollama.list_models = AsyncMock(
            return_value=[
                Mock(name="mistral"),
                Mock(name="tinyllama"),
                Mock(name="phi"),
            ]
        )

        await brain.think("def hello(): pass")

        reasoning = brain.get_last_reasoning()
        # Code should be detected
        assert reasoning["intent"] == Intent.CODE.value

    @pytest.mark.asyncio
    async def test_teaching_routing(self, brain, mock_ollama):
        """Test that teaching inputs route to appropriate model"""

        async def mock_stream(*args, **kwargs):
            yield "response"

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        await brain.think("explain how recursion works")

        reasoning = brain.get_last_reasoning()
        # Teaching should be detected
        assert reasoning["intent"] == Intent.TEACHING.value


class TestIntegration:
    """Integration tests for entire Week 1 system"""

    @pytest.mark.asyncio
    async def test_end_to_end_code_request(self):
        """Test complete flow for code request"""
        from unittest.mock import AsyncMock

        mock_ollama = AsyncMock()
        mock_ollama.list_models = AsyncMock(
            return_value=[
                Mock(name="mistral"),
                Mock(name="tinyllama"),
                Mock(name="phi"),
            ]
        )

        async def mock_stream(*args, **kwargs):
            yield "def hello():\n    print('Hello')"

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        brain = Brain(
            ollama_engine=mock_ollama,
            intent_detector=IntentDetector(),
            model_selector=ModelSelector(),
        )

        result = await brain.think("write a hello world function")

        assert "def" in result or "hello" in result.lower()
        assert brain.get_last_reasoning()["intent"] == Intent.CODE.value

    @pytest.mark.asyncio
    async def test_end_to_end_teaching_request(self):
        """Test complete flow for teaching request"""
        from unittest.mock import AsyncMock

        mock_ollama = AsyncMock()
        mock_ollama.list_models = AsyncMock(
            return_value=[
                Mock(name="mistral"),
                Mock(name="tinyllama"),
                Mock(name="phi"),
            ]
        )

        async def mock_stream(*args, **kwargs):
            yield "A database is a structured collection of data..."

        mock_ollama.stream_response = AsyncMock(side_effect=mock_stream)

        brain = Brain(
            ollama_engine=mock_ollama,
            intent_detector=IntentDetector(),
            model_selector=ModelSelector(),
        )

        result = await brain.think("what is a database")

        assert len(result) > 0
        assert brain.get_last_reasoning()["intent"] == Intent.TEACHING.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
