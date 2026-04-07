"""
Ollama Local Model Interface
Provides unified access to locally-running LLM models via Ollama
"""

import asyncio
import httpx
import json
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelSize(Enum):
    """Model size categories"""
    TINY = "7b"       # ~4GB RAM (Mistral 7B, Phi 2)
    SMALL = "13b"     # ~8GB RAM (Llama 2 13B)
    MEDIUM = "70b"    # ~40GB RAM (Llama 2 70B)
    LARGE = "405b"    # ~200GB+ (Llama 3 405B)


@dataclass
class OllamaModel:
    """Model configuration"""
    name: str
    display_name: str
    size: ModelSize
    ram_required: int  # GB
    context_window: int = 4096
    description: str = ""


class OllamaEngine:
    """Interface to Ollama local model server"""
    
    OLLAMA_HOST = "http://localhost:11434"
    
    # Recommended models for different use cases
    RECOMMENDED_MODELS = {
        ModelSize.TINY: OllamaModel(
            name="mistral",
            display_name="Mistral 7B",
            size=ModelSize.TINY,
            ram_required=8,
            context_window=8192,
            description="Fast, efficient 7B model. Best for speed."
        ),
        ModelSize.SMALL: OllamaModel(
            name="neural-chat",
            display_name="Neural Chat 13B",
            size=ModelSize.SMALL,
            ram_required=16,
            context_window=4096,
            description="Conversation-optimized 13B model."
        ),
        ModelSize.MEDIUM: OllamaModel(
            name="llama2",
            display_name="Llama 2 70B",
            size=ModelSize.MEDIUM,
            ram_required=48,
            context_window=4096,
            description="Most capable open model. Requires 48GB+ RAM."
        ),
    }
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize Ollama engine
        
        Args:
            model_name: Name of model to use (e.g., 'mistral')
                       If None, defaults to 'mistral'
        """
        self.model_name = model_name or "mistral"
        self.client = httpx.AsyncClient(timeout=None)
        self._is_ready = False
    
    async def check_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = await self.client.get(f"{self.OLLAMA_HOST}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False
    
    async def list_models(self) -> list:
        """List all available models"""
        try:
            response = await self.client.get(f"{self.OLLAMA_HOST}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Download and cache model from Ollama registry
        
        Args:
            model_name: Model identifier (e.g., 'mistral', 'neural-chat')
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            response = await self.client.post(
                f"{self.OLLAMA_HOST}/api/pull",
                json={"name": model_name},
            )
            response.raise_for_status()
            logger.info(f"✓ Model {model_name} downloaded")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def stream_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
    ) -> AsyncIterator[str]:
        """
        Stream response from local model
        
        Args:
            prompt: Input prompt
            temperature: Higher = more creative (0.0-2.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
        
        Yields:
            Response tokens as they're generated
        """
        try:
            async with self.client.stream(
                "POST",
                f"{self.OLLAMA_HOST}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
        except Exception as e:
            logger.error(f"Stream response error: {e}")
            yield f"Error: {e}"
    
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate complete response from local model
        
        Args:
            prompt: Input prompt
            temperature: Higher = more creative
            max_tokens: Maximum response length
        
        Returns:
            Complete response text
        """
        response = ""
        async for token in self.stream_response(prompt, temperature=temperature):
            response += token
            if len(response) > max_tokens:
                break
        return response
    
    async def generate_with_history(
        self,
        messages: list,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response considering conversation history
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            temperature: Response creativity
        
        Returns:
            Assistant's response
        """
        # Build context from message history
        context = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n\n"
        
        context += "Assistant:"
        
        return await self.generate_response(context, temperature=temperature)
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()


# Singleton instance
_ollama_instance: Optional[OllamaEngine] = None


async def get_ollama_engine(model_name: str = "mistral") -> OllamaEngine:
    """Get or create Ollama engine instance"""
    global _ollama_instance
    if _ollama_instance is None:
        _ollama_instance = OllamaEngine(model_name)
    return _ollama_instance
