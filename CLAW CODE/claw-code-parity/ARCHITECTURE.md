# 🏗️ Claw Code Architecture Guide

**For Complete Beginners (Seriously, We Explain Like You're 5)**

---

## Table of Contents

1. [What is This Project? (The Simple Version)](#what-is-this-project)
2. [The Big Picture (How Everything Works Together)](#the-big-picture)
3. [The Three Main Pieces](#three-main-pieces)
4. [How Things Talk to Each Other](#how-things-talk)
5. [Where All the Files Live](#file-locations)
6. [What Happens When You Type a Command](#the-flow)
7. [The Tools (What It Can Do)](#the-tools)
8. [Python vs Rust (Which One Do I Use?)](#python-vs-rust)
9. [Practical Examples](#practical-examples)

---

## What is This Project? {#what-is-this-project}

### The Super Simple Explanation

Imagine you have a very smart friend (Claude, an AI) who can help you write code, answer questions, and get things done. But this friend can't leave their room - they can't run commands on your computer or read your files directly.

**Claw Code** is like a robot assistant that stands between you and your smart friend. This robot:
- Listens to what you ask (questions or problems)
- Tells your smart friend (the AI) what you said
- Carries messages back and forth
- Listens to what your friend wants to do (like "read this file" or "run this command")
- Actually does those things for your friend
- Reports back what happened

This project is the **robot** - the bridge between you, the AI, and your computer.

### Why Does It Exist?

Someone accidentally shared the original Claude Code source code online. Instead of using that directly, someone built a **cleaner version from scratch** inspired by those ideas. This is that cleaner version - it's open source and anyone can use it or improve it.

### What Can You Do With It?

Once you set it up, you can:
- Chat with Claude (or other AI models) from your computer
- The AI can read your code files
- The AI can write new files
- The AI can run commands/scripts
- The AI can search the web
- The AI can work with notebooks and git
- All while keeping track of costs and following safety rules

---

## The Big Picture {#the-big-picture}

### How It All Fits Together

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOU (The User)                           │
│                  (Typing questions at a command line)             │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    CLI (Command Line)   │
                    │   Interface Layer       │
                    │  Pretty printing & input│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Runtime Engine       │
                    │  (The Smart Coordinator)│
                    │  - Remembers context    │
                    │  - Checks permissions   │
                    │  - Tracks costs         │
                    │  - Manages sessions     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │   API Connection     │   │   Tool Executor      │
        │  (Talks to Claude)   │   │  (Does the work)     │
        │ - Sends prompts      │   │ - Runs bash commands │
        │ - Receives responses │   │ - Reads files        │
        │ - Handles streaming  │   │ - Writes files       │
        │ - Tracks tokens      │   │ - Searches files     │
        └──────────────────────┘   │ - Calls plugins      │
                    │               └──────────────────────┘
                    │                         │
                    ▼                         ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │   Claude AI Model    │   │  Your Computer       │
        │  (The Smart Friend)  │   │  (Filesystem, bash)  │
        │ - Thinks             │   │ - Stores data        │
        │ - Plans              │   │ - Runs programs      │
        │ - Decides what to do │   │ - Has files          │
        └──────────────────────┘   └──────────────────────┘
```

**Key insight:** The runtime engine is like an orchestra conductor - it coordinates between the AI (who has great ideas) and the tools (which can actually do things).

---

## The Three Main Pieces {#three-main-pieces}

### 1. The Python Version (The Original Porting Work)

Located in: `src/` folder

**What it is:** The first rewrite, done in Python (the programming language that's easier to read).

**What it includes:**
- Tools that can read and write files
- Basic command execution
- Session management (remembering what you talked about)
- Permission checking (making sure you're allowed to do what you're trying)
- Models for different types of operations

**Why it exists:** It's the reference implementation - the first version created to understand how everything should work. Think of it as the architect's sketch before building the real house.

**Status:** Functional, but being replaced by the Rust version which is faster.

### 2. The Rust Version (The Fast Professional Grade)

Located in: `rust/` folder

**What it is:** A rewritten version in Rust (a programming language that's very fast and safe).

**What it includes:**
- Everything from Python, but much faster
- Better safety (Rust prevents certain types of programming errors)
- More features (web search, notebooks, MCP servers, OAuth login, etc.)
- Streaming support (real-time responses)
- Better error handling

**Why it's better:**
- **Speed:** Rust is compiled and runs way faster than Python
- **Safety:** Rust catches bugs at compile time
- **Professional:** Used by big companies for performance-critical code
- **Native:** Runs directly on your OS

**The structure:**
```
rust/
├── crates/api/              ← Talks to Claude API
├── crates/commands/         ← Slash commands (/help, /status, etc)
├── crates/runtime/          ← The heart: manages conversation flow
├── crates/tools/            ← Actual tools (bash, read, write, etc)
├── crates/rusty-claude-cli/ ← The command-line interface
├── crates/mock-anthropic-service/ ← Fake Claude for testing
└── crates/plugins/          ← Optional extensions
```

### 3. The Test Suite & Mock Services

Located in: `tests/` and `rust/crates/mock-anthropic-service/`

**What it is:** Automated tests that make sure everything works correctly.

**Why it matters:**
- Catches bugs before they affect you
- Makes sure the Rust version works exactly like the Python version (parity)
- Tests all the tools in a safe, controlled way
- Uses a "fake Claude" so you don't spend money testing

---

## How Things Talk to Each Other {#how-things-talk}

### The Conversation Flow (A Real Example)

Let's say you type: `"Please read my main.py file"`

**Step 1: You Type** → CLI captures your input
```
You: read my main.py file
```

**Step 2: CLI Passes to Runtime** 
```
Runtime receives: "read my main.py file"
```

**Step 3: Runtime Sends to Claude**
```
Message to API: 
  "Here's what the user asked: read my main.py file
   Here are the tools you can use: read_file, write_file, bash, etc
   Please help them"
```

**Step 4: Claude Thinks & Decides**
```
Claude AI analyzes this and thinks:
  "The user wants me to read main.py
   I should use the read_file tool
   The file path should be main.py
   Let me call that tool"
```

**Step 5: Claude Asks the Runtime**
```
Claude: "Please use the read_file tool with path=main.py"
```

**Step 6: Runtime Executes the Tool**
```
Tool executor gets: read_file(path="main.py")
Tool actually reads the file from your disk
Tool returns: "Here's what's in main.py: [file contents]"
```

**Step 7: Runtime Reports Back to Claude**
```
Message back to API:
  "I read main.py, here's what it contains: [contents]"
```

**Step 8: Claude Generates Response**
```
Claude thinks about the file contents and writes:
  "I see your main.py file. It defines a function called process_data.
   Here's what I notice about it: ..."
```

**Step 9: Response Flows Back to You**
```
CLI displays: "I see your main.py file..."
You see the answer
```

### The Key Players & Their Jobs

| Component | Job | Talks To |
|-----------|-----|----------|
| **CLI** | Gets your input, shows results | Runtime |
| **Runtime** | Manages the whole flow | API + Tools |
| **API Client** | Sends/receives messages | Claude server |
| **Tool Pool** | Manages available tools | Runtime |
| **Permission Checker** | Decides if an action is allowed | Runtime |
| **Session Manager** | Remembers conversation history | Runtime |
| **Cost Tracker** | Counts tokens & money spent | Runtime |

---

## Where All the Files Live {#file-locations}

### Python Version (`src/`)
```
src/
├── main.py                 ← Entry point, command parsing
├── runtime.py              ← Core conversation engine
├── tools.py                ← Tool implementations
├── models.py               ← Data structures
├── session_store.py        ← Remembers conversations
├── permissions.py          ← Access control rules
├── cost_tracker.py         ← Token/money counter
├── query_engine.py         ← Smart prompt routing
├── commands.py             ← Available commands
├── task.py / tasks.py      ← Task management
│
├── assistant/              ← AI assistant logic
├── runtime/                ← Runtime utilities
├── services/               ← External services
├── utils/                  ← Helper functions
├── skills/                 ← AI agent skills
├── plugins/                ← Optional extensions
│
└── reference_data/         ← Static data
    ├── commands_snapshot.json
    ├── tools_snapshot.json
    └── archive_surface_snapshot.json
```

### Rust Version (`rust/crates/`)

```
rust/crates/
├── api/                    ← HTTP client & streaming
│   ├── src/
│   │   ├── client.rs       ← Makes API calls
│   │   ├── models.rs       ← Request/response types
│   │   └── streaming.rs    ← Real-time response handling
│
├── runtime/                ← Conversation management
│   ├── src/
│   │   ├── conversation.rs ← Main loop
│   │   ├── config.rs       ← Settings
│   │   ├── session.rs      ← Remembers chats
│   │   ├── permissions.rs  ← Access control
│   │   └── mcp.rs          ← Plugin server support
│
├── tools/                  ← What the AI can do
│   ├── src/
│   │   ├── bash.rs         ← Run shell commands
│   │   ├── file_ops.rs     ← Read/write files
│   │   ├── search.rs       ← Search files
│   │   ├── web.rs          ← Internet access
│   │   └── lib.rs          ← Tool registry
│
├── rusty-claude-cli/       ← The executable
│   ├── src/
│   │   ├── main.rs         ← Entry point
│   │   ├── repl.rs         ← Interactive mode
│   │   └── display.rs      ← Pretty printing
│
└── mock-anthropic-service/ ← For testing
    └── src/
        └── lib.rs          ← Fake Claude API
```

### Configuration Files

```
project/
├── .claude.json            ← Default settings for Claude
├── Cargo.toml              ← Rust dependencies
├── Cargo.lock              ← Exact versions used
├── PARITY.md               ← Python vs Rust comparison
└── README.md               ← Instructions
```

---

## What Happens When You Type a Command {#the-flow}

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER TYPES                                                   │
│    $ claw prompt "write a hello world program"                  │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CLI PARSING (rusty-claude-cli)                              │
│    ✓ Recognizes "prompt" command                                │
│    ✓ Extracts arguments                                         │
│    ✓ Loads .claude.json settings                                │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RUNTIME INIT (runtime/)                                      │
│    ✓ Loads config hierarchy                                     │
│    ✓ Reads API key / OAuth token                                │
│    ✓ Loads session (if continuing)                              │
│    ✓ Initializes permission policy                              │
│    ✓ Sets up cost tracker                                       │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. TOOL POOL ASSEMBLY (tools/)                                  │
│    ✓ Registers available tools:                                 │
│      - bash (run commands)                                      │
│      - read_file                                                │
│      - write_file                                               │
│      - edit_file                                                │
│      - grep_search                                              │
│      - web_search                                               │
│    ✓ Applies permission restrictions                            │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. PROMPT ASSEMBLY                                              │
│    Combines:                                                    │
│    - System prompt (who Claude should be)                       │
│    - Tool definitions (what Claude can do)                      │
│    - Conversation history (what was said before)                │
│    - Your question: "write a hello world program"               │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. SEND TO CLAUDE API (api/client)                              │
│    POST https://api.anthropic.com/v1/messages                   │
│    Headers: Authorization: Bearer [your-key]                    │
│    Body: {                                                      │
│      "model": "claude-opus-4-6",                                │
│      "system": "You are helpful...",                            │
│      "tools": [{ definitions }],                                │
│      "messages": [{ "role": "user", "content": "write hw" }]    │
│    }                                                            │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. CLAUDE THINKS & RESPONDS                                     │
│    Claude processes and decides:                                │
│    "The user wants a hello world program.                       │
│     I should use write_file tool to create one."                │
│                                                                 │
│    Response (streaming):                                        │
│    {                                                            │
│      "type": "content_block_start",                             │
│      "content_block": { "type": "tool_use",                     │
│                        "id": "tool_123",                        │
│                        "name": "write_file",                    │
│                        "input": {                               │
│                          "path": "hello.py",                    │
│                          "content": "print('Hello, World!')" }  │
│    }                                                            │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. EXTRACT TOOL CALL                                            │
│    Runtime extracts: "write_file" call                          │
│    Parameters: path="hello.py", content="print(...)"            │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. PERMISSION CHECK (permissions.rs)                            │
│    ✓ Is write_file allowed? YES                                 │
│    ✓ Is path within workspace? YES                              │
│    ✓ Would it overwrite important file? NO                      │
│    ✓ APPROVED - proceed                                         │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. EXECUTE TOOL (tools/file_ops.rs)                            │
│     Actually write the file:                                    │
│     File: /workspace/hello.py                                   │
│     Content: print('Hello, World!')                             │
│     Result: ✓ SUCCESS                                           │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. SEND RESULT BACK TO CLAUDE                                  │
│     Message: "Tool write_file succeeded.                        │
│              File written to hello.py with content:             │
│              print('Hello, World!')"                            │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 12. CLAUDE GENERATES FINAL RESPONSE                             │
│     Claude sees the file was created and writes:                │
│     "I've created a hello world program for you in hello.py.    │
│      You can run it with: python hello.py                       │
│      It will print: Hello, World!"                              │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 13. DISPLAY RESPONSE                                            │
│     CLI shows:                                                  │
│     ✓ I've created a hello world program for you in hello.py    │
│     ✓ You can run it with: python hello.py                      │
│     ✓ It will print: Hello, World!                              │
│                                                                 │
│     Session saved to ${SESSION_ID}                              │
│     Tokens used: 156 input, 89 output                           │
│     Cost: $0.00234                                              │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
        ┌─────────────┐
        │ YOU SEE IT! │
        └─────────────┘
```

---

## The Tools (What It Can Do) {#the-tools}

Think of tools like superpowers. Each tool lets Claude do something different:

### Available Tools

| Tool | What It Does | Example |
|------|-------------|---------|
| **bash** | Run shell commands | `rm -rf` or `npm install` |
| **read_file** | Read a file's contents | View your code files |
| **write_file** | Create or overwrite files | Make new scripts |
| **edit_file** | Change specific parts of files | Fix a bug on line 42 |
| **grep_search** | Search for text in files | Find where a function is used |
| **glob_search** | Find files by pattern | Get all `.py` files in a folder |
| **web_search** | Search the internet | Look up current events |
| **web_fetch** | Read web pages | Get documentation |
| **agent** | Call other AI agents | Delegate subtasks |
| **todo_write** | Create/manage todo lists | Track work |
| **notebook_edit** | Edit Jupyter notebooks | Work with data science |
| **skill** | Use pre-built workflows | Run packaged solutions |

### Permission Levels

```
┌─────────────────────────────────────────────────────────┐
│ PERMISSION LEVELS (Most Restrictive → Most Permissive)  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 🔐 READ_ONLY                                           │
│    ✓ Can read files                                    │
│    ✓ Can search files                                  │
│    ✗ Cannot write                                      │
│    ✗ Cannot run commands                               │
│                                                         │
│ 📝 WORKSPACE_WRITE                                     │
│    ✓ Can read files                                    │
│    ✓ Can write files in workspace                      │
│    ✓ Can run safe commands                             │
│    ✗ Cannot access system files                        │
│                                                         │
│ 🔥 DANGER_FULL_ACCESS                                 │
│    ✓ Everything allowed                                │
│    ✗ NOT SAFE - use only if you trust the AI          │
│    ✗ Could delete everything!                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Python vs Rust (Which One Do I Use?) {#python-vs-rust}

### Quick Comparison

| Aspect | Python Version | Rust Version |
|--------|---|---|
| **Status** | Porting/Reference | Main/Production |
| **Speed** | Slower (good for learning) | Much faster (production ready) |
| **Ease of Reading** | Easier for beginners | Steeper learning curve |
| **Safety** | Less safe (you're responsible) | Very safe (compiler checks) |
| **Features** | Basic | Full-featured |
| **Where to run** | Tests, learning | Real usage |
| **Installation** | `python -m src` | `cargo build --release` |

### Decision Tree

```
Are you a beginner learning the codebase?
├─ YES → Use Python (src/) - easier to read
└─ NO
    Do you want maximum speed and performance?
    ├─ YES → Use Rust (rust/) - production quality
    └─ NO
        Is this for production/real use?
        ├─ YES → Use Rust
        └─ NO → Use Python for learning
```

### Running Each

**Python version:**
```bash
cd claw-code-parity
python -m src commands --query "what tools exist"
```

**Rust version:**
```bash
cd claw-code-parity/rust
cargo build --release
./target/release/claw prompt "write me a poem"
```

---

## Practical Examples {#practical-examples}

### Example 1: You Want Claude to Fix a Bug

**What you do:**
```bash
claw prompt "There's a bug in src/utils.py line 42. Can you fix it?"
```

**Behind the scenes:**
1. CLI sends your question to Runtime
2. Runtime loads your .claude.json settings
3. Assembles the tool pool (gives Claude the read_file and write_file tools)
4. Sends to Claude API: "Here's what the user needs, here are your tools"
5. Claude thinks: "I need to read the file first to see the bug"
6. Claude calls: `read_file("src/utils.py")`
7. Runtime executes that, reads the actual file
8. Runtime sends back the file contents to Claude
9. Claude analyzes the code, spots the bug
10. Claude calls: `write_file("src/utils.py", [fixed content])`
11. Runtime writes the fixed file
12. Claude sends back: "I found the bug on line 42 and fixed it!"
13. You see the response

**Total time:** A few seconds

### Example 2: You Want to Set Up a New Project

**What you do:**
```bash
claw prompt "Set up a new Python project with these files: main.py, requirements.txt, README.md. Initialize git."
```

**Behind the scenes:**
1. Claude plans the steps
2. Calls `write_file` multiple times to create each file
3. Calls `bash` to run `git init`
4. Calls `bash` to run `git add .`
5. Summarizes what was created

### Example 3: Continuous Conversation

**What you do:**
```bash
claw  # Starts interactive REPL
> read my main.py file
[Claude reads the file]
> can you add a docstring to the process_data function?
[Claude edits the file]
> now add type hints
[Claude makes more changes]
> /cost
[Shows how much money you spent]
> /session mysession
[Saves this conversation]
```

---

## Key Concepts Explained Simply

### Sessions

**What it is:** A saved conversation with all its history.

**Why it matters:** You can stop, come back later, and keep going from where you left off.

**How it works:**
```
Session 1 (Monday):
  You: "Read my code"
  Claude: [reads and comments]
  ...conversation...
  
[You close the program]

Session 2 (Tuesday):
  You: claw /session monday
  Claude remembers everything from Monday
  You: "Now let's fix that bug"
  Claude: "Sure! About that code from yesterday..."
```

### MCP (Model Context Protocol) Servers

**What it is:** Extra programs that give Claude superpowers.

**Simple example:** You could have an MCP server that lets Claude directly query your database. Or one that talks to your email. Or one that controls your smart home.

**How it works:**
```
You → Claude → MCP Server → External System
                    ↓
              Returns data
                    ↓
Claude → You with the answer
```

### Streaming

**What it is:** Getting responses piece-by-piece instead of all at once.

**Why it's good:**
- No waiting for the entire response
- You see Claude "typing" like in ChatGPT
- Faster-feeling experience

**How it looks:**
```
Without streaming:
[30 seconds wait]
[Complete response appears]

With streaming:
I've analyzed your code...
[slight pause]
The main issue is...
[slight pause]
Here's how to fix it...
[slight pause]
Done!
```

### Cost Tracking

**What it is:** Counting how many tokens Claude uses and how much money it costs.

**How it works:**
```
When you use Claude:
  Input tokens (what you send): 150
  Output tokens (what Claude responds): 89
  Model: claude-opus-4-6 ($15/1M input, $75/1M output)
  
  Cost = (150 * $15 + 89 * $75) / 1,000,000 = $0.00234

Total after 5 conversations: $0.01234
```

---

## Common Questions

### Q: Is this safe?

**A:** Yes, with permission levels:
- Default is `READ_ONLY` - Claude can't break things
- You can enable `WORKSPACE_WRITE` if needed
- Never use `DANGER_FULL_ACCESS` unless you really know what you're doing

### Q: How much does it cost?

**A:** Only what Claude costs (you pay Anthropic). Typical conversation: $0.001 - $0.01

### Q: Can I use this offline?

**A:** The Rust version can work with local models if configured, but default uses Claude API (requires internet).

### Q: What if Claude tries to do something bad?

**A:** The permission system stops it. Plus, the code reviews everything before execution.

### Q: Which version should I actually use?

**A:** If you're learning: Python (easier to read code)  
If you want to actually use it: Rust (faster, more features)

---

## File & Folder Cheat Sheet

```
claw-code-parity/
├── README.md               ← Start here for quick start
├── PARITY.md               ← Details about Python vs Rust
├── CLAUDE.md               ← AI assistant hints
│
├── src/                    ← Python version (learning)
│   ├── main.py             ← Entry point
│   ├── runtime.py          ← Core engine
│   ├── tools.py            ← Available tools
│   └── [many more files]
│
├── rust/                   ← Rust version (production)
│   ├── Cargo.toml          ← Configuration
│   ├── crates/
│   │   ├── api/            ← Claude API client
│   │   ├── runtime/        ← Conversation engine
│   │   ├── tools/          ← Tool implementations
│   │   ├── rusty-claude-cli/ ← Main program
│   │   └── [5 more crates]
│   └── scripts/            ← Useful scripts
│
├── tests/                  ← Tests for Python
└── assets/                 ← Images & stuff
```

---

## What We Actually Do

In **ONE SENTENCE:**

> Claw Code is a safe, open-source AI agent that can read your code, write new files, run commands, and help you build software - all while you control what it's allowed to do.

---

## Next Steps to Understand More

1. **Read:** [README.md](README.md) - Quick start guide
2. **Understand:** Look at `rust/crates/runtime/` - the heart of the system
3. **Explore:** Try `claw prompt "explain this codebase"` - let Claude explain!
4. **Test:** Run the mock harness: `cd rust && ./scripts/run_mock_parity_harness.sh`
5. **Learn:** Read the Rust code - it's an excellent example of well-structured Rust

---

## Summary

This project is a **bridge between you and AI**, letting Claude:
- **Read** your computer's files
- **Think** about problems
- **Write** solutions
- **Run** commands
- **Remember** everything

It's built in two versions:
- **Python** - for learning and understanding
- **Rust** - for fast, safe, production use

The magic happens in the **runtime engine**, which:
1. Takes your question
2. Asks Claude what to do
3. Lets Claude ask for tools
4. Checks permissions
5. Executes tools
6. Reports back to Claude
7. Returns the answer to you

That's it! You now understand the entire architecture. 🎉

