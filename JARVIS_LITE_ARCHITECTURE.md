# JARVIS-Lite Architecture

> Lean, offline-first AI assistant for teaching + coding  
> **Constraints**: 4GB RAM, Core i5, ₦0 budget, no internet required

**Status**: DESIGN COMPLETE  
**Date**: April 7, 2026  
**Diagram Version**: 1.0

---

## 🎯 Core Philosophy

**Move fast, stay lean.**

Instead of:
- ❌ Complex multi-service architecture
- ❌ High memory models (10B+)
- ❌ Cloud dependencies
- ❌ Features we don't need

We build:
- ✅ Single cohesive process
- ✅ Small models (1-2B parameters)
- ✅ 100% offline operation
- ✅ Teaching + coding focus only

---

## 📐 System Architecture (Visual)

```
┌─────────────────────────────────────────────────────┐
│                    JARVIS-LITE                      │
│                   (~80-100MB base)                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  INTERFACE LAYER                            │  │
│  ├──────────────────────────────────────────────┤  │
│  │  • CLI Chat (main)                          │  │
│  │  • Voice Input (Vosk STT) - optional        │  │
│  │  • Voice Output (Coqui TTS) - optional      │  │
│  └──────────────────────────────────────────────┘  │
│                      ↓                              │
│  ┌──────────────────────────────────────────────┐  │
│  │  BRAIN LAYER (Reasoning Loop)               │  │
│  ├──────────────────────────────────────────────┤  │
│  │  1. Parse user input                        │  │
│  │  2. Detect intent (rules-based)             │  │
│  │  3. Select skill + model                    │  │
│  │  4. Execute with tools                      │  │
│  │  5. Generate response                       │  │
│  │  6. Store in memory                         │  │
│  └──────────────────────────────────────────────┘  │
│         ↓              ↓              ↓             │
│    ┌────────┐     ┌────────┐    ┌──────────┐      │
│    │ LOCAL  │     │ SKILLS │    │  TOOLS   │      │
│    │  LLM   │     │ SYSTEM │    │  LAYER   │      │
│    └────────┘     └────────┘    └──────────┘      │
│       ↓              ↓              ↓             │
│    TinyLlama   exam_generator  file_reader       │
│    Phi-2       code_helper     code_runner       │
│    Gemma       teacher_mode    text_formatter    │
│                                                   │
│  ┌──────────────────────────────────────────────┐  │
│  │  MEMORY LAYER (SQLite)                       │  │
│  ├──────────────────────────────────────────────┤  │
│  │  • conversations.db (all chats)              │  │
│  │  • user_profile.json (learned patterns)      │  │
│  │  • skill_memory.db (per-skill learnings)     │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🧠 Brain Layer (Core Engine)

The reasoning loop that powers everything:

```python
# jarvis.py (main entry point)
class JARVISBrain:
    def __init__(self):
        self.model = load_local_llm()      # TinyLlama/Phi-2
        self.memory = setup_sqlite()        # Conversations + profile
        self.tools = load_tools()           # File, code, text tools
        self.skills = load_skills()         # Instructions per domain
    
    async def think(self, user_input):
        """Main reasoning loop"""
        
        # 1. Intent detection (rules, no ML needed)
        intent = self.detect_intent(user_input)
        
        # 2. Select appropriate skill
        skill = self.skills[intent]
        
        # 3. Build prompt with context from memory
        context = self.memory.get_recent_context(intent)
        prompt = skill.build_prompt(user_input, context)
        
        # 4. Generate response from local LLM
        response = await self.model.generate(prompt)
        
        # 5. If tool needed, execute it
        if skill.needs_tools:
            tool_result = await self.tools.execute(skill.tool_name)
            response = skill.refine_response(response, tool_result)
        
        # 6. Store in memory for learning
        self.memory.add_turn("user", user_input)
        self.memory.add_turn("assistant", response)
        
        return response
```

---

## 📚 Skills System (Reusable Intelligence)

Skills are the domain knowledge. Each skill is:
- Simple instructions file
- System prompt for LLM
- Optional tools it can call
- Optional post-processing logic

### Structure:

```
skills/
├── coding/
│   ├── debug_code.json
│   ├── explain_code.json
│   ├── refactor_code.json
│   └── generate_function.json
│
├── teaching/
│   ├── generate_exam.json
│   ├── create_lesson.json
│   ├── explain_simple.json
│   └── format_questions.json
│
├── productivity/
│   ├── summarize_text.json
│   ├── analyze_project.json
│   └── create_report.json
│
└── system/
    ├── search_files.json
    └── organize_project.json
```

### Example Skill File:

```json
{
  "name": "generate_exam",
  "domain": "teaching",
  "description": "Generate exam questions for students",
  
  "system_prompt": "You are an experienced teacher creating exam questions. 
                    Generate well-structured, clear questions with correct answers.
                    Format: Q1. Question here\n   a) Option\n   b) Option...",
  
  "model": "phi-2",
  "temperature": 0.7,
  "max_tokens": 2000,
  
  "input_template": "Generate {count} {difficulty} questions on {topic}
                      Subject: ICT, Format: MCQ",
  
  "output_format": "numbered_list",
  "needs_tools": false,
  
  "pre_requirements": ["load_user_teaching_style"],
  
  "cache_key": "exam_{topic}_{difficulty}_{date}"
}
```

---

## 🛠️ Tools Layer (Execution)

Simple, sandboxed operations:

### Available Tools:

```python
# tools/file_tools.py
class FileTools:
    def read_file(self, path, start_line=None, end_line=None)
    def list_files(self, directory, pattern=None)
    def search_text(self, directory, query)

# tools/code_tools.py
class CodeTools:
    def run_python(self, code, timeout=5)  # Sandboxed!
    def analyze_syntax(self, code)
    def highlight_errors(self, code, error_output)

# tools/text_tools.py
class TextTools:
    def format_text(self, text, format_type)
    def count_words(self, text)
    def extract_sections(self, text, delimiter)
```

### Sandboxing:

```python
class SafeToolRunner:
    ALLOWED_OPERATIONS = {
        "file_read": restricted_read,
        "file_list": restricted_list,
        "python_run": run_in_sandbox,  # No rm -rf /
    }
    
    def execute(self, tool_name, args):
        if tool_name not in self.ALLOWED_OPERATIONS:
            return {"error": "Tool not allowed"}
        
        return self.ALLOWED_OPERATIONS[tool_name](**args)
```

---

## 💾 Memory Layer (Learning)

SQLite database (built into Python, zero setup):

### Schema:

```sql
-- Store all conversations
conversations.db:
  - id (int)
  - timestamp (datetime)
  - user_input (text)
  - assistant_response (text)
  - intent (text)
  - skill_used (text)
  - user_feedback (text) -- corrections
  - created_at (datetime)

-- Learning from corrections
  - Original response stored
  - If user corrects: store delta
  - Future similar questions use corrected version
```

### User Profile (Explicit Commands):

```json
{
  "teaching_style": "concise",
  "exam_format": "MCQ",
  "question_difficulty": "intermediate",
  "coding_languages": ["python", "javascript"],
  "code_style": "functional"
}
```

### How Learning Works:

```bash
User: > jarvis remember: I prefer MCQ format
JARVIS: ✓ Added to profile. Future exams will use MCQ.

User: > jarvis remember: use simple language
JARVIS: ✓ Added to profile.

User: > generate exam
JARVIS: [Generates MCQ with simple language]
```

**Why explicit is better**:
- ✅ Deterministic (no guessing)
- ✅ Easy to test (input → expected output)
- ✅ User has control (knows what JARVIS learned)
- ✅ Reliable (no NLP ambiguity)
- ✅ Foundation for later implicit learning

---

## 🎯 Intent Detection (Hybrid - Regex + Scoring)

No ML needed. Hybrid approach with fallback:

```python
# brain/intent_detector.py

class HybridIntentDetector:
    def detect(self, user_input: str):
        text = user_input.lower()
        
        # Layer 1: Fast regex for clear cases (<1ms)
        for intent, patterns in self.CLEAR_PATTERNS.items():
            if any(re.search(p, text) for p in patterns):
                return (intent, confidence=0.95)
        
        # Layer 2: Keyword scoring fallback (5-10ms)
        scores = self.score_by_keywords(text)  # "exam" + "generate" = high score
        if scores.max >= 0.7:
            return (scores.best_intent, confidence=scores.max)
        
        # Layer 3: Low confidence - ask user
        if scores.max >= 0.5:
            return (scores.best_guess, confidence=0.5, ask_user=True)
        
        # No match
        return ("general_chat", confidence=0.1, ask_user=False)

# Usage:
result = detector.detect("generate exam questions")
if result.ask_user:
    print(f"Did you mean {result.intent}? (y/n)")
else:
    execute(result.intent)
```

**Performance**: <1ms for clear cases, 5-10ms with scoring, better UX (fewer misroutes)

---

## 💬 Interface Layer

### Option 1: CLI (Default - Weeks 1-6)

```bash
$ python jarvis.py
🎤 JARVIS-Lite v1.0
Type 'quit' to exit, 'memory' to see stats

> generate 30 ICT questions for year 1
⏳ Thinking... (2-3 seconds)

Q1. What is an algorithm?
a) A sequence of steps to solve a problem
b) A type of computer
c) A programming language
d) A data structure
[Answer: a]

Q2. What does CPU stand for?
[continues...]

Exam generated! (30 questions, ~500 words)
Memory: 127 conversations stored

> explain this code
[paste code]

> explain for a 10 year old
This code makes a list and sorts it...

> quit
✓ Saved session. See you next time!
```

### Option 2: Voice (Weeks 7+, if RAM permits)

```bash
$ python jarvis.py --voice

🎤 JARVIS-Lite v1.0 (Voice Mode)
Listening for voice commands...

[User speaks]: "Generate 20 exam questions on networking"

JARVIS (voice): "Generating exam questions on networking..."
[Waits 3-4 seconds]
JARVIS (voice): "Here are your exam questions. Would you like me to save them?"
```

---

## 📊 Model Strategy (Smart Selection + Batching)

### Model Selection:

| Task Domain | Model | Size | RAM | Speed | Quality |
|-------------|-------|------|-----|-------|----------|
| **Teaching** (default) | TinyLlama 1.1B | ~1GB | 1.5GB | ⚡⚡⚡ Fast | 85% |
| **Code tasks** | Phi-2 1.7B | ~1.7GB | 2.2GB | ⚡⚡ Medium | 95% |
| **General chat** | TinyLlama 1.1B | ~1GB | 1.5GB | ⚡⚡⚡ Fast | 80% |

### Auto-Switching Strategy:

```python
# Smart model selection
MODEL_SELECTION = {
    "teaching": "tinyllama",      # Fast, good for exams
    "generate_exam": "tinyllama",
    "explain_simple": "tinyllama",
    "general_chat": "tinyllama",
    
    "code_debug": "phi-2",        # Better logic for code
    "generate_function": "phi-2",
    "refactor_code": "phi-2",
}

class SmartModelLoader:
    def get_model_for_skill(self, skill_name):
        model_name = MODEL_SELECTION.get(skill_name, "tinyllama")
        return self.load_model(model_name)  # Auto-switches
```

**Benefits**:
- Default TinyLlama: 1.5GB RAM (fits on 4GB easily)
- Code tasks auto-switch to Phi-2 when needed
- No manual switching needed
- **First response**: 5-10s (TinyLlama) or 8-12s (Phi-2)
- **Subsequent**: 2-4s (TinyLlama) or 3-5s (Phi-2)

### Exam Generation with Batching:

```python
# Skills/teaching/generate_exam.json
{
  "name": "generate_exam",
  "batch_size": 5,  # Generate 5 at a time
  "strategy": "streaming",
  "# Instead of: Generate 30 questions (wait 15-20s)
  "# Now: Generate batches of 5 (show first 5 in 3-4s!)
}

class BatchExamGenerator:
    def generate_exam(self, count=30):
        questions = []
        for batch_num in range(0, count, 5):
            batch_size = min(5, count - batch_num)
            batch = self.llm.generate(f"Generate {batch_size} questions...")
            questions.extend(batch)
            
            # Stream first batch immediately
            if batch_num == 0:
                yield questions
        
        return questions
```

**Batching benefits**:
- User sees first 5 questions in 3-4 seconds
- Doesn't wait for all 30 (better perceived speed)
- Can interrupt after first batch if wanted
- Easier to debug individual batches

---

## 📁 Project Structure

```
jarvis-lite/
│
├── jarvis.py               # Main entry point
│
├── brain/
│   ├── __init__.py
│   ├── reasoning.py        # Main loop
│   ├── intent_detector.py  # Pattern-based
│   └── model_loader.py     # Smart caching
│
├── skills/
│   ├── _base.py            # Skill template
│   ├── coding/
│   │   ├── debug_code.json
│   │   ├── explain_code.json
│   │   └── generate_function.json
│   ├── teaching/
│   │   ├── generate_exam.json
│   │   ├── create_lesson.json
│   │   └── explain_simple.json
│   └── productivity/
│       ├── summarize_text.json
│       └── analyze_project.json
│
├── tools/
│   ├── __init__.py
│   ├── file_tools.py
│   ├── code_tools.py
│   └── text_tools.py
│
├── memory/
│   ├── __init__.py
│   ├── database.py         # SQLite interface
│   ├── user_profile.py     # Personalization
│   └── conversations.db    # Actual data
│
├── config/
│   ├── models.json         # Which models to load
│   └── settings.json       # Defaults
│
└── tests/
    ├── test_brain.py
    ├── test_skills.py
    └── test_memory.py
```

---

## 🔗 How PHASE 1 Integrates

JARVIS-Lite **uses** PHASE 1 (local models + memory):

```python
# jarvis_lite/brain/reasoning.py
from providers.local import OllamaEngine  # ← PHASE 1
from providers.local.memory_storage import MemoryManager  # ← PHASE 1

class JARVISBrain:
    def __init__(self):
        # Use existing infrastructure from PHASE 1
        self.model = OllamaEngine(model="phi-2")
        self.memory = MemoryManager(backend="sqlite")
        
        # Add skills system on top
        self.skills = load_skills()
        self.tools = load_tools()
```

**Result**: JARVIS-Lite doesn't reinvent—it **layers on top** of PHASE 1.

---

## ⚡ Performance Profile

| Operation | Time | Offline? |
|-----------|------|----------|
| **Voice verification** | 150-300ms | ✅ Yes |
| **Intent detection** | <1ms | ✅ Yes |
| **First token** | 3-8s | ✅ Yes |
| **Subsequent tokens** | 100-150ms each | ✅ Yes |
| **Full response (50 tokens)** | 5-15s | ✅ Yes |
| **File search** | 100-500ms | ✅ Yes |
| **Memory lookup** | <10ms | ✅ Yes |
| **Full E2E (voice in → text out)** | 5-20s | ✅ Yes |

---

## 📋 MVP Definition (Version 1.0)

**JARVIS-Lite v1 is complete when:**

✅ Runs on 4GB RAM without swapping  
✅ Boots in <3 seconds  
✅ CLI chat works (type input, get response)  
✅ Intent detection works for 5+ domains  
✅ Skills work: exam generation, code debug, simple explanation  
✅ Memory stores conversations (can recall past)  
✅ First response <10s, subsequent <5s  
✅ Works 100% offline  
✅ No external dependencies (pip install, done)  

---

## 🚀 Stretch Goals (Post-MVP)

- 🎤 Voice input (Vosk STT)
- 🔊 Voice output (Coqui TTS)
- 📊 Dashboard showing conversation stats
- 🎯 Custom skill creation (easy syntax)
- 🔄 Sync with other devices
- 📚 Community skill sharing

---

## 📈 Realistic Performance Expectations (4GB/i5)

| Task | Expected | Achievable? |
|------|----------|-------------|
| Generate 30 exam questions | 10-20s | ✅ Yes |
| Explain code (50 lines) | 5-10s | ✅ Yes |
| Debug code error | 3-8s | ✅ Yes |
| Search files | <500ms | ✅ Yes |
| Recall past conversation | <10ms | ✅ Yes |
| Voice input → output | 4-6s | ✅ Yes (with Vosk) |

---

## 🎓 Design Principles

1. **Lean First** → Only build what's needed for MVP
2. **Offline Always** → No internet dependency, ever
3. **User Data Private** → Everything stored locally
4. **Modular Design** → Easy to add/remove skills
5. **Zero Configuration** → Works out of the box
6. **Testable Code** → High code coverage
7. **Clear Docs** → Anyone can extend it

---

**Status**: ARCHITECTURE COMPLETE  
**Ready for**: Implementation (PHASE 2)  
**Next**: Detailed integration roadmap

