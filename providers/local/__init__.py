"""
Local Providers Module
Enables interaction with locally-running LLM models (Ollama)
"""

from .memory_storage import JSONMemory, MemoryManager, MemoryType, SQLiteMemory
from .ollama_engine import ModelSize, OllamaEngine, get_ollama_engine

__all__ = [
    "JSONMemory",
    "MemoryManager",
    "MemoryType",
    "ModelSize",
    "OllamaEngine",
    "SQLiteMemory",
    "get_ollama_engine",
]
