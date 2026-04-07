# PHASE 1 Setup Guide: Local Model Store & Command Interface

> Setting up Ollama, local 7B models, SQLite memory, and command interface

**Status**: 🚀 Ready to start implementation  
**Date**: April 7, 2026  
**Estimated Time**: 30-45 minutes

---

## Overview

PHASE 1 implements **Idea #1: Unified Local Model Store & Adaptive Switching** by:

1. Installing Ollama (local model server)
2. Downloading a 7B model (Mistral, neural-chat, or Phi)
3. Building a command interface for local inference
4. Implementing memory storage (SQLite + JSON)
5. Integrating with Free Claude Code

---

## 🔧 Installation Steps

### Step 1: Install Ollama

**For Windows:**
```powershell
# Option A: Download installer (GUI)
Start-Process "https://ollama.ai/download"

# Wait for installer to complete, then verify:
ollama --version
```

**For Mac:**
```bash
# Via Homebrew
brew install ollama

# Or download from: https://ollama.ai/download
```

**For Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

### Step 2: Verify Ollama Installation

```powershell
# Check version
ollama --version

# Should output: ollama version X.X.X
```

### Step 3: Start Ollama Server

**Windows (Background Service):**
```powershell
# Ollama runs as a background service automatically after installation
# Verify it's running:
curl http://localhost:11434/api/tags
# Should return JSON with model list (initially empty)
```

**Mac/Linux:**
```bash
# Start Ollama server
ollama serve

# In another terminal:
curl http://localhost:11434/api/tags
```

### Step 4: Download a 7B Model

Ollama will automatically download models on first use. Choose one:

**Mistral 7B** (⭐ Recommended - fastest, best balance):
```powershell
ollama pull mistral
```

**Neural Chat 13B** (More conversational, slightly slower):
```powershell
ollama pull neural-chat
```

**Phi 2** (Smallest, fastest on low RAM):
```powershell
ollama pull phi
```

**Choose based on your system:**
```
Mistral 7B:    ~4GB RAM, ~10 tokens/sec
Neural Chat:   ~8GB RAM, ~7 tokens/sec
Phi 2:         ~2GB RAM, ~15 tokens/sec
Llama 2 13B:   ~16GB RAM, ~5 tokens/sec
```

Download will take 5-15 minutes depending on internet speed.

---

## 📦 Python Dependencies

### Add to `pyproject.toml`

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "httpx>=0.24.0",           # Async HTTP client for Ollama
    "click>=8.1.0",            # CLI framework
    "rich>=13.5.0",            # Rich terminal output
    "pydantic>=2.0.0",         # Data validation
    "python-dotenv>=1.0.0",    # Environment variables
]

[tool.uv]
# Enable offline installs for local development
cache-dir = ".uv-cache"
```

### Install Dependencies

```powershell
# Using uv (preferred)
cd free-claude-code
uv sync

# Or using pip
pip install httpx click rich pydantic python-dotenv
```

---

## 🚀 Quick Start

### 1. Test Ollama Connection

```powershell
# From project root
cd free-claude-code

# Python test
python -c "
import asyncio
from providers.local.ollama_engine import OllamaEngine

async def test():
    engine = OllamaEngine('mistral')
    if await engine.check_connection():
        print('✓ Connected to Ollama')
        models = await engine.list_models()
        print(f'Available models: {[m[\"name\"] for m in models]}')
    await engine.close()

asyncio.run(test())
"
```

### 2. Interactive Chat

```powershell
# Start chat mode
python providers/local/cli.py chat

# In chat mode, type:
# "What is machine learning?"
# "Write a Python function to calculate factorial"
# "Help" for commands
# "Exit" to quit
```

### 3. Single Query

```powershell
# Ask single question
python providers/local/cli.py ask "What is the capital of France?"

# Generate code
python providers/local/cli.py generate "Write a Python function to reverse a list"

# Analyze code
python providers/local/cli.py analyze path/to/code.py

# List available models
python providers/local/cli.py list-models
```

---

## 📝 Project Structure

```
free-claude-code/
├── providers/
│   └── local/
│       ├── __init__.py                 # Module exports
│       ├── ollama_engine.py            # ✓ Ollama interface
│       ├── memory_storage.py           # ✓ SQLite/JSON memory
│       └── cli.py                      # ✓ Command interface
│
├── PHASE_1_SETUP.md                    # This file
├── pyproject.toml                      # Update with new deps
└── .env.example                        # Update with LOCAL_PROVIDER
```

---

## 🎯 Usage Examples

### Example 1: Chat with Memory

```powershell
# Start chat
python providers/local/cli.py chat

You: What is Python?
Assistant: Python is a high-level, interpreted programming language...

You: List its main features
Assistant: Python has several key features:
1. Simple and readable syntax
2. Dynamic typing...

# Type 'memory' to see stored conversations
# Type 'clear' to clear history
```

### Example 2: Code Generation

```powershell
python providers/local/cli.py generate "Create a REST API endpoint in FastAPI that returns user data from a SQLite database"

# Output:
# Generated Code:
# ```python
# from fastapi import FastAPI, Depends
# from sqlalchemy import create_engine
# 
# app = FastAPI()
# ...
```

### Example 3: Code Analysis

```powershell
python providers/local/cli.py analyze myfile.py

# Output:
# Analyzing code...
# 
# What it does:
# - Reads configuration from environment variables
# - Connects to database
# - Handles HTTP requests
# 
# Potential issues:
# - No error handling for database connection
# - Missing input validation
# 
# Suggestions:
# - Add try/except blocks
# - Validate request parameters
```

### Example 4: Access Memory Storage

```python
# Python script to query memory
from providers.local.memory_storage import MemoryManager, MemoryType

memory = MemoryManager(backend="sqlite")

# Get conversation history
history = memory.memory.get_entries_by_type(MemoryType.CONVERSATION.value)
print(f"Stored {len(history)} conversation turns")

# Search memory
results = memory.memory.search("Python functions")
print(f"Found {len(results)} results about Python functions")

# Get statistics
stats = memory.memory.get_stats()
print(f"Total entries: {stats['total_entries']}")
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```env
# Local provider settings
LOCAL_PROVIDER_ENABLED=true
LOCAL_MODEL_NAME=mistral
LOCAL_MODEL_CONTEXT=8192
LOCAL_TEMPERATURE=0.7

# Fallback to cloud if needed
ENABLE_REMOTE_FALLBACK=true
REMOTE_PROVIDER=nvidia_nim

# Memory settings
MEMORY_BACKEND=sqlite
MEMORY_PATH=~/.jarvis_memory/memory.db
```

### Model Configuration

Edit `providers/local/ollama_engine.py`:

```python
# Change default model
DEFAULT_MODEL = "mistral"  # Options: mistral, neural-chat, phi, llama2

# Adjust performance parameters
TEMPERATURE = 0.7          # 0.0 = deterministic, 1.0+ = random
TOP_P = 0.9               # Nucleus sampling
TOP_K = 40                # Top-k sampling
```

---

## 🧪 Testing

### Unit Tests

```powershell
# Test Ollama engine
uv run pytest tests/providers/test_ollama_engine.py -v

# Test memory storage
uv run pytest tests/providers/test_memory_storage.py -v

# Run all local provider tests
uv run pytest tests/providers/local/ -v
```

### Manual Tests

```powershell
# 1. Connection test
python -c "
import asyncio
from providers.local import OllamaEngine

asyncio.run(OllamaEngine().check_connection())
"

# 2. Model availability test
python providers/local/cli.py list-models

# 3. Response streaming test
python providers/local/cli.py ask "Hello, world!"

# 4. Memory persistence test
python -c "
from providers.local.memory_storage import MemoryManager
m = MemoryManager()
m.add_conversation_turn('user', 'Test message')
history = m.memory.get_entries_by_type('conversation')
print(f'Stored and retrieved {len(history)} entries')
"
```

---

## 📊 Performance Baseline

Once running, measure performance:

```powershell
# Time first response (includes model loading)
Measure-Command {
    python providers/local/cli.py ask "Hello" | Out-Null
}

# Expected: 3-10 seconds (first run)

# Time subsequent responses  
Measure-Command {
    python providers/local/cli.py ask "How are you?" | Out-Null
}

# Expected: 1-3 seconds (model cached)
```

**Baseline Performance (Mistral 7B):**
- First response: 8-12 seconds
- Subsequent responses: 1-3 seconds
- Tokens/second: 8-12 tokens/sec
- Memory usage: 4.2GB

---

## 🐛 Troubleshooting

### Issue: "Ollama not found"

```powershell
# Solution: Add Ollama to PATH
# Windows: Restart terminal or restart computer after installation
# Mac/Linux: Check installation guide above
```

### Issue: "Connection refused at http://localhost:11434"

```powershell
# Solution: Start Ollama server
# Windows: Service should auto-start. Check Services:
Get-Service ollama

# Mac/Linux: Run ollama serve
ollama serve
```

### Issue: Model download slow

```powershell
# Solutions:
# 1. Check internet connection: Test-NetConnection -ComputerName ollama.ai
# 2. Try different model: ollama pull phi (smaller, 2GB)
# 3. Download manually: https://ollama.ai/models
```

### Issue: "Out of memory" errors

```powershell
# Solutions:
# 1. Use smaller model: phi (2GB) instead of mistral (4GB)
# 2. Close other applications
# 3. Check available RAM: Get-ComputerInfo | Select TotalPhysicalMemory
```

### Issue: Slow responses

```powershell
# Solutions:
# 1. Check CPU usage. If low: may not have GPU acceleration
# 2. Use smaller model
# 3. Reduce context window: LOCAL_MODEL_CONTEXT=2048
```

---

## ✅ Validation Checklist

Before moving to PHASE 2, verify:

- [ ] Ollama installed and running (`ollama --version` works)
- [ ] Model downloaded (`ollama pull mistral` complete)
- [ ] Python dependencies installed (`pip list | grep httpx`)
- [ ] Ollama connection test passes
- [ ] Chat mode works (`python providers/local/cli.py chat`)
- [ ] Memory storage persistent (chat history saved)
- [ ] Code generation works (`python providers/local/cli.py generate "..."`)
- [ ] Memory stats show entries (`'memory' command in chat`)

---

## 📈 Next Steps (PHASE 2)

Once PHASE 1 complete:

1. **Voice-Guided Autonomy Mode**
   - Integrate JARVIS voice commands with local model
   - Enable multi-step workflows
   - Build autonomy levels (manual → autonomous)

2. **Adaptive Switching**
   - Detect network conditions
   - Route queries: local if offline → remote if online
   - Intelligent fallback logic

3. **Caching & Optimization**
   - Cache repeated queries (LRU)
   - Batch similar requests
   - Model quantization for faster inference

---

## 📚 Resources

- **Ollama Docs**: https://github.com/ollama/ollama
- **Available Models**: https://ollama.ai/models
- **LLM Performance Guide**: https://huggingface.co/blog/llm-inference
- **Memory Patterns**: https://python-patterns.guide/

---

## 🎓 Learning Resources

If new to local LLMs:

1. **Understanding LLMs**: https://www.youtube.com/watch?v=d0qjBrx0q0Q
2. **Ollama Tutorial**: https://www.youtube.com/watch?v=E8W0pgTp4gI
3. **Model Selection**: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard
4. **Quantization**: https://github.com/ggerganov/llama.cpp

---

## 💡 Tips & Best Practices

### Performance Optimization

```python
# Reuse engine instance
engine = OllamaEngine("mistral")

# Don't close/reopen for each query
for query in queries:
    response = await engine.generate_response(query)

# Close once when done
await engine.close()
```

### Memory Management

```python
# Use SQLite for large histories (1000+ entries)
memory = MemoryManager(backend="sqlite")

# Use JSON for small projects (<100 entries)
memory = MemoryManager(backend="json")

# Periodically archive old entries
old_entries = memory.memory.search("timestamp < 2026-01-01")
# Archive to file...
memory.memory.clear()
```

### Error Handling

```python
# Always wrap in try/except
try:
    response = await engine.generate_response(prompt)
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Fallback to cached response or return error
```

---

**Status**: Ready for Implementation  
**Next Update**: After PHASE 1 Complete  
**Estimated Completion**: April 8-9, 2026
