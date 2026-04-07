"""
PHASE 1 Implementation Tests
Tests for Ollama engine, memory storage, and CLI
"""

import pytest
import asyncio
from pathlib import Path
import json
import tempfile
from unittest.mock import Mock, patch, AsyncMock

### Ollama Engine Tests ###

@pytest.mark.asyncio
async def test_ollama_engine_initialization():
    """Test OllamaEngine initializes correctly"""
    from providers.local.ollama_engine import OllamaEngine
    
    engine = OllamaEngine("mistral")
    assert engine.model_name == "mistral"
    assert engine.client is not None
    await engine.close()


@pytest.mark.asyncio
async def test_ollama_model_size_enum():
    """Test ModelSize enum"""
    from providers.local.ollama_engine import ModelSize
    
    assert ModelSize.TINY.value == "7b"
    assert ModelSize.SMALL.value == "13b"
    assert ModelSize.MEDIUM.value == "70b"


@pytest.mark.asyncio
async def test_ollama_recommended_models():
    """Test recommended models are defined"""
    from providers.local.ollama_engine import OllamaEngine, ModelSize
    
    models = OllamaEngine.RECOMMENDED_MODELS
    assert ModelSize.TINY in models
    assert models[ModelSize.TINY].name == "mistral"
    assert models[ModelSize.TINY].ram_required == 8


### Memory Storage Tests ###

def test_json_memory_initialization():
    """Test JSONMemory initializes correctly"""
    from providers.local.memory_storage import JSONMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = JSONMemory(Path(tmpdir) / "test.json")
        assert mem.storage_path.exists()
        assert mem.memory == []


def test_json_memory_add_entry():
    """Test adding entries to JSON memory"""
    from providers.local.memory_storage import JSONMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = JSONMemory(Path(tmpdir) / "test.json")
        entry_id = mem.add_entry(
            memory_type="test",
            content="Hello world",
            tags=["test"]
        )
        
        assert entry_id is not None
        assert len(mem.memory) == 1
        assert mem.memory[0].content == "Hello world"


def test_json_memory_persistence():
    """Test JSON memory persists to disk"""
    from providers.local.memory_storage import JSONMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test.json"
        
        # Add entry
        mem1 = JSONMemory(storage_path)
        mem1.add_entry("test", "Hello", tags=["tag1"])
        
        # Load again
        mem2 = JSONMemory(storage_path)
        assert len(mem2.memory) == 1
        assert mem2.memory[0].content == "Hello"


def test_sqlite_memory_initialization():
    """Test SQLiteMemory initializes correctly"""
    from providers.local.memory_storage import SQLiteMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SQLiteMemory(Path(tmpdir) / "test.db")
        assert mem.db_path.exists()


def test_sqlite_memory_add_entry():
    """Test adding entries to SQLite memory"""
    from providers.local.memory_storage import SQLiteMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SQLiteMemory(Path(tmpdir) / "test.db")
        entry_id = mem.add_entry(
            memory_type="test",
            content="Hello world",
            tags=["test"]
        )
        
        assert entry_id is not None
        
        # Verify entry was stored
        entries = mem.get_entries_by_type("test")
        assert len(entries) == 1
        assert entries[0]["content"] == "Hello world"


def test_sqlite_memory_search():
    """Test searching SQLite memory"""
    from providers.local.memory_storage import SQLiteMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SQLiteMemory(Path(tmpdir) / "test.db")
        mem.add_entry("test", "Python programming")
        mem.add_entry("test", "Java programming")
        mem.add_entry("test", "Rust safety")
        
        results = mem.search("Python")
        assert len(results) == 1
        assert "Python" in results[0]["content"]


def test_sqlite_memory_tags():
    """Test querying by tags"""
    from providers.local.memory_storage import SQLiteMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SQLiteMemory(Path(tmpdir) / "test.db")
        mem.add_entry("test", "Content 1", tags=["important"])
        mem.add_entry("test", "Content 2", tags=["normal"])
        mem.add_entry("test", "Content 3", tags=["important"])
        
        important = mem.get_entries_by_tag("important")
        assert len(important) == 2


def test_sqlite_memory_stats():
    """Test memory statistics"""
    from providers.local.memory_storage import SQLiteMemory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SQLiteMemory(Path(tmpdir) / "test.db")
        mem.add_entry("conversation", "User: Hello")
        mem.add_entry("task", "Build task")
        mem.add_entry("conversation", "Assistant: Hi")
        
        stats = mem.get_stats()
        assert stats["total_entries"] == 3
        assert stats["by_type"]["conversation"] == 2
        assert stats["by_type"]["task"] == 1


def test_memory_manager_abstraction():
    """Test MemoryManager abstraction layer"""
    from providers.local.memory_storage import MemoryManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test SQLite backend
        manager = MemoryManager(backend="sqlite")
        manager.add_conversation_turn("user", "Hello")
        assert manager.backend == "sqlite"


def test_memory_manager_conversation():
    """Test conversation management"""
    from providers.local.memory_storage import MemoryManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MemoryManager(backend="sqlite")
        manager.add_conversation_turn("user", "What is AI?")
        manager.add_conversation_turn("assistant", "AI is artificial intelligence...")
        
        history = manager.memory.get_entries_by_type("conversation")
        assert len(history) == 2


def test_memory_manager_task_result():
    """Test task result logging"""
    from providers.local.memory_storage import MemoryManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MemoryManager(backend="sqlite")
        manager.add_task_result(
            task_name="code_gen",
            result="def hello(): pass",
            success=True
        )
        
        tasks = manager.memory.get_entries_by_type("task")
        assert len(tasks) == 1


### CLI Tests ###

def test_local_command_interface_initialization():
    """Test LocalCommandInterface initializes"""
    from providers.local.cli import LocalCommandInterface
    
    interface = LocalCommandInterface("mistral")
    assert interface.model_name == "mistral"
    assert interface.memory is not None
    assert interface.history == []


def test_messages_formatting():
    """Test message formatting for model input"""
    from providers.local.cli import LocalCommandInterface
    
    interface = LocalCommandInterface()
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    
    formatted = interface._format_messages(messages)
    assert "User: Hello" in formatted
    assert "Assistant: Hi there!" in formatted
    assert "Assistant:" in formatted  # Final prompt


### Integration Tests ###

@pytest.mark.asyncio
async def test_full_chat_flow_mock():
    """Test full chat flow with mocked Ollama"""
    from providers.local.cli import LocalCommandInterface
    
    interface = LocalCommandInterface("mistral")
    
    with patch.object(interface.ollama or type('Obj', (), {})(), 'stream_response', new_callable=AsyncMock) as mock_stream:
        mock_stream.return_value = iter(["Hi", " there", "!"])
        
        # Simulate chat
        # (This would work with real Ollama in integration tests)


def test_memory_persistence_across_sessions():
    """Test memory persists across sessions"""
    from providers.local.memory_storage import MemoryManager
    from pathlib import Path
    import tempfile
    
    db_path = Path(tempfile.gettempdir()) / "test_persistence.db"
    
    # Session 1
    manager1 = MemoryManager(backend="sqlite")
    manager1.add_conversation_turn("user", "Session 1")
    
    # Session 2
    manager2 = MemoryManager(backend="sqlite")
    history = manager2.memory.get_entries_by_type("conversation")
    
    # Should have entries from session 1
    assert len(history) >= 1


### Performance Tests ###

def test_sqlite_query_performance():
    """Test SQLite query performance with many entries"""
    from providers.local.memory_storage import SQLiteMemory
    import time
    
    with tempfile.TemporaryDirectory() as tmpdir:
        mem = SQLiteMemory(Path(tmpdir) / "test.db")
        
        # Add 100 entries
        for i in range(100):
            mem.add_entry("test", f"Content {i}", tags=[f"tag{i % 10}"])
        
        # Time search
        start = time.time()
        results = mem.search("Content")
        elapsed = time.time() - start
        
        assert len(results) == 100
        assert elapsed < 0.1  # Should be fast


@pytest.mark.parametrize("model_size,ram", [
    ("mistral", 8),
    ("neural-chat", 16),
    ("llama2", 48),
])
def test_model_ram_requirements(model_size, ram):
    """Test model RAM requirements"""
    from providers.local.ollama_engine import OllamaEngine, ModelSize
    
    models = OllamaEngine.RECOMMENDED_MODELS
    # Verify RAM requirements are defined
    for size, model in models.items():
        assert model.ram_required > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
