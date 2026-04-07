"""
Local Providers Module
Enables interaction with locally-running LLM models (Ollama)
"""

from .ollama_engine import OllamaEngine, get_ollama_engine, ModelSize
from .memory_storage import MemoryManager, MemoryType, SQLiteMemory, JSONMemory

__all__ = [
    "OllamaEngine",
    "get_ollama_engine",
    "ModelSize",
    "MemoryManager",
    "MemoryType",
    "SQLiteMemory",
    "JSONMemory",
]
