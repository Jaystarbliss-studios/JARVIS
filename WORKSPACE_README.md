# Integrated Voice-Assisted AI Agent Workspace

> A comprehensive ecosystem combining **voice-based authentication**, **AI proxy middleware**, and **agentic orchestration** to create a fully autonomous, offline-capable assistant system.

## 🎯 Overview

This workspace contains three tightly integrated systems designed to work both independently and together:

1. **Free Claude Code** - API proxy middleware for free/local AI model access
2. **Claw Code** - Complete agent harness for tool orchestration and task management  
3. **JARVIS** - Military-grade voice authentication and command execution system

**Goal**: Enable a single authenticated user to interact with Claude-powered AI tools entirely via voice commands, with full local execution, zero cloud dependency, and enterprise-grade security.

---

## 📦 System Components

### 1️⃣ **Free Claude Code** (Root Level)
**What:** Lightweight FastAPI proxy middleware  
**Why:** Free Claude Code (VSCode extension) requires Anthropic API keys and paid usage. This proxy intercepts requests and routes them to free alternatives.

#### Problem It Solves
- ❌ Claude Code CLI needs Anthropic API keys ($)
- ✅ Free Claude Code redirects to NVIDIA NIM (40 req/min free), OpenRouter (hundreds of free models), or LM Studio (fully offline)
- ✅ Zero modifications to Claude Code CLI or VSCode extension needed

#### Key Features
- **Multi-provider support**: NVIDIA NIM, OpenRouter, LM Studio
- **Streaming SSE responses**: Compatible with Anthropic API format
- **Request optimization**: Intercepts & caches trivial calls (5 categories)
- **Messaging bot integration**: Discord & Telegram for remote execution
- **Session management**: Multiple concurrent Claude CLI sessions
- **Rate limiting**: Per-provider rolling-window throttle
- **Smart error mapping**: Provider errors → Anthropic-compatible responses

#### Directory Structure
```
free-claude-code/
├── server.py                 # FastAPI app entry point
├── api/
│   ├── app.py                # Request lifecycle, lifespan
│   ├── routes.py             # /v1/messages endpoints
│   ├── dependencies.py       # Provider selection
│   ├── optimization_handlers.py  # Trivial call detection
│   └── models/
├── providers/                # Provider implementations
│   ├── base.py               # BaseProvider ABC
│   ├── common/               # Shared utilities (DRY)
│   ├── nvidia_nim/
│   ├── open_router/
│   └── lmstudio/
├── messaging/                # Discord & Telegram bots
│   ├── discord.py
│   ├── telegram.py
│   └── factory.py
├── cli/                      # Session management
│   ├── manager.py
│   └── session.py
└── config/
    ├── settings.py           # Config via .env
    └── nim.py
```

#### How It Works

```
Claude Code CLI/VSCode Extension
         ↓ (Anthropic API format)
    HTTP Request
         ↓
╔═══════════════════════════════╗
║  FastAPI Proxy (Port 8082)    ║
║  • Drop-in Anthropic API      ║
║  • Request optimization       ║
║  • Provider routing           ║
╚═════════════╤═════════════════╝
              │
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 NVIDIA NIM  OpenRouter LM Studio
  (Free)    (hundreds)  (Local)
    │         │         │
    └─────────┼─────────┘
              ↓
      Streaming SSE Response
       (Anthropic format)
              ↓
    Claude Code receives unchanged
```

#### Technology Stack
- **Framework**: FastAPI + Uvicorn
- **HTTP**: httpx (async)
- **Tokens**: tiktoken (Anthropic tokenizer)
- **Logging**: loguru (structured)
- **Config**: Pydantic + python-dotenv
- **Type Safety**: Strict (ty checker, no type ignores)

---

### 2️⃣ **Claw Code** (CLAW CODE/claw-code-parity/)
**What:** Clean-room Python/Rust rewrite of Claude Code's agent harness  
**Why:** Implements proper agentic orchestration with tool registry patterns, permission enforcement, and comprehensive testing.

#### Problem It Solves
- ❌ Need to orchestrate AI → Tools → Filesystem → Bash in a secure, auditable way
- ✅ Claw Code provides TaskRegistry, PermissionEnforcer, tool templates, MCP/LSP support
- ✅ Clean-room architecture inspired by (not derived from) the original Claude Code

#### Key Features
- **Tool Registry Pattern**: 40+ explicit tool specs (Bash, Files, Tasks, Teams, MCP, LSP)
- **Permission Enforcement**: Workspace boundaries, bash read-only modes, whitelist gating
- **Stateful Management**: TaskRegistry (create/get/list/stop), TeamRegistry, CronRegistry
- **MCP Integration**: Model Context Protocol for external tool bridges
- **LSP Support**: Language Server Protocol for symbol/ref/hover/diagnostic queries
- **Real-Time Streaming**: Response generation with context preservation
- **Comprehensive Testing**: Mock parity harness with 10 scripted scenarios
- **Multi-Language**: Python v1 (portalable) → Rust v2 (production, 48.5K LOC)

#### Directory Structure
```
CLAW CODE/claw-code-parity/
├── ARCHITECTURE.md          # Detailed architecture
├── PARITY.md                # 9-lane development overview
├── README.md                # Quick start
├── src/                     # Python reference implementation
│   ├── agent/
│   ├── tools/               # Tool modules (bash, files, tasks, etc.)
│   ├── registries/          # TaskRegistry, TeamRegistry, etc.
│   └── orchestrator.py      # Main harness
├── rust/                    # Production Rust port
│   ├── agent/
│   ├── tools/
│   ├── permissions/         # PermissionEnforcer
│   └── server.rs            # Streaming server
└── tests/
    ├── mock_harness.py      # Parity validation
    └── scenarios/           # 10 scripted test cases
```

#### 9 Lanes of Development (All Merged)

| Lane | Component | Status | Purpose |
|------|-----------|--------|---------|
| 1 | Bash Validation | ✅ Merged | 18 submodules: read-only, destructive warnings, sed validation |
| 2 | CI Sandbox Fix | ✅ Merged | Container-aware sandbox probing |
| 3 | File Tools | ✅ Merged | Binary detection, size limits, workspace boundaries |
| 4 | TaskRegistry | ✅ Merged | Task lifecycle (create, get, list, stop, update) |
| 5 | Task Wiring | ✅ Merged | Registry backing for 6 task tools |
| 6 | Team+Cron | ✅ Merged | Background work orchestration |
| 7 | MCP Lifecycle | ✅ Merged | Model Context Protocol server bridge |
| 8 | LSP Client | ✅ Merged | Language Server Protocol dispatch |
| 9 | Permission Enforcement | ✅ Merged | Workspace + bash + tool gating |

#### How It Works

```
┌────────────────────────────────────┐
│  Authenticated User (JARVIS)       │
│  or Direct CLI                     │
└────────────┬───────────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │  Runtime Engine         │
    │  • Parse command        │
    │  • Check permissions    │
    │  • Route to tool        │
    └──────────┬──────────────┘
               │
    ┌──────────┴────────────────────────┐
    │                                   │
    ▼                                   ▼
┌────────────────────┐         ┌──────────────────┐
│ File Tools         │         │ Bash Tools       │
│ • read_file        │         │ • execute_bash   │
│ • write_file       │         │ • validate_sed   │
│ • list_dir         │         │ • check_readonly │
└────────────────────┘         └──────────────────┘
                                       │
    ┌─────────────┬──────────────┬────┴────┬───────────┐
    │             │              │         │           │
    ▼             ▼              ▼         ▼           ▼
┌────────┐  ┌────────┐  ┌────────────┐  ┌────┐  ┌─────────┐
│Tasks   │  │Teams   │  │Cron Jobs   │  │MCP │  │LSP      │
│(async) │  │(multi) │  │(scheduled) │  │    │  │(symbols)│
└────────┘  └────────┘  └────────────┘  └────┘  └─────────┘
     │           │             │          │         │
     └───────────┴─────────────┴──────────┴────────┘
                         │
                         ▼
      ┌──────────────────────────────────┐
      │ Your Computer / Local Files      │
      │ (Sandboxed, timeout-protected)   │
      └──────────────────────────────────┘
```

#### Key Design Principles
- **DRY via shared utilities** (`providers/common/`)
- **Encapsulation**: Accessor methods for internal state
- **Provider/tool abstraction**: Pluggable implementations
- **Fail-secure**: Permission enforcer gates all operations
- **Type-safe**: No `# type: ignore`, strict static analysis
- **Comprehensive testing**: Mock scenarios validate behavior

---

### 3️⃣ **JARVIS** (JARVIS/jarvis_voice_assistant/)
**What:** Military-grade encryption + voice biometric authentication system  
**Why:** Enable secure, hands-free access to Claude agent tools. User proves identity via voice, then issues commands—all offline, no internet required.

#### Problem It Solves
- ❌ "How do I securely give Claude voice control on my laptop without exposing my identity to the cloud?"
- ✅ Voice biometric authentication (ECAPA-TDNN embedding, 99% accuracy)
- ✅ Anti-spoofing checks (replay, deepfakes, synthetics)
- ✅ AES-256 encryption at rest (Fernet)
- ✅ Fully offline (Vosk STT, local processing)
- ✅ Deterministic command matching (no LLM interpretation)
- ✅ Sandbox execution with timeouts & output sanitization

#### Key Features
**Authentication Layer**
- ECAPA-TDNN speaker verification (512-dim embeddings)
- Multi-sample enrollment (7 samples = better accuracy, fewer false positives)
- Cosine-similarity matching (threshold: 0.70, configurable)
- Fail-secure (denies by default)

**Liveness Detection**
- Frequency concentration check (<85% single frequency)
- Energy variation check (>10% variation)
- Silence detection (<50% silent)
- Detects: replay attacks, deepfakes, synthetic audio

**Speech Recognition**
- Offline STT via Vosk (~40MB model)
- 16 kHz mono audio capture
- No cloud dependency

**Command Execution**
- Whitelist-only intent matching (regex patterns)
- Sandboxed subprocess execution (timeout: 30s)
- Output truncation (1000 chars max)
- Limited environment variables
- No shell access (subprocess safety)

**Security & Audit**
- AES-256 Fernet encryption (voiceprint at rest)
- Encryption key in environment variable (not on disk)
- Audit logging: PASS/FAIL only (no biometric data)
- Timestamps + reason codes

#### Directory Structure
```
JARVIS/jarvis_voice_assistant/
├── QUICKSTART.md             # Getting started
├── SECURITY.md               # Threat model & mitigations
├── IMPLEMENTATION_SUMMARY.md # Technical deep dive
├── README.md                 # Overview
├── setup.py                  # Installation script
├── requirements.txt          # Dependencies
├── src/
│   ├── main.py               # CLI orchestrator
│   ├── audio/
│   │   └── capture.py        # Real-time microphone input
│   ├── verification/
│   │   └── verify.py         # ECAPA-TDNN + similarity
│   ├── enrollment/
│   │   └── enroll.py         # Voice enrollment (7 samples)
│   ├── security/
│   │   └── encryption.py     # Fernet AES-256
│   ├── recognition/
│   │   └── stt.py            # Vosk offline STT
│   └── command/
│       └── executor.py       # Whitelist + sandboxed exec
└── config/
    ├── settings.yaml         # Audio params (16kHz mono, etc.)
    ├── commands.yaml         # Whitelisted command patterns
    └── thresholds.yaml       # Security presets (0.70, timeout)
```

#### How It Works

```
USER SPEAKS
    ↓ (into microphone)
AUDIO CAPTURE (16 kHz mono)
    ↓
NORMALIZE AUDIO
    ↓
┌─────────────────────────────────┐
│ SPEAKER VERIFICATION (ECAPA-TDNN)
│ • Extract 512-dim embedding    │
│ • Cosine similarity vs stored  │
│ • Score ≥ 0.70? → PASS          │
│ • Fail-secure: DENY by default  │
└────────────┬────────────────────┘
             │ (if PASS)
             ▼
┌─────────────────────────────────┐
│ LIVENESS CHECK (Anti-spoofing)  │
│ • Frequency concentration <85%  │
│ • Energy variation >10%         │
│ • Silence <50%                  │
│ Detects: replay, deepfakes      │
└────────────┬────────────────────┘
             │ (if PASS)
             ▼
┌─────────────────────────────────┐
│ SPEECH-TO-TEXT (Vosk)           │
│ • Offline transcription         │
│ • Returns exact text            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ INTENT PARSING (Whitelist)      │
│ • Regex matching vs commands.yaml
│ • No LLM (deterministic)        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ COMMAND EXECUTION (Sandboxed)   │
│ • Subprocess: 30s timeout       │
│ • Output: 1000 chars max        │
│ • Env: Limited variables        │
│ • No shell access (safety)      │
└────────────┬────────────────────┘
             │
             ▼
      SECURITY & AUDIT LOG
      (PASS/FAIL only, no PII)
```

#### Voice Enrollment Process
```
ENROLLMENT MODE (Initial Setup)
    ↓
"RECORD 7 SAMPLES (3-10 seconds each)"
    ↓ (User speaks 7 times)
    ↓
FOR EACH SAMPLE:
  1. Normalize audio
  2. Extract ECAPA-TDNN embedding (512 dims)
  3. Store embedding in list
    ↓
AVERAGE 7 EMBEDDINGS
  → Final voiceprint (512 dims)
    ↓
ENCRYPT WITH AES-256 FERNET
  → Encrypted blob
    ↓
SAVE TO DISK
  • encryption_key in env var (not on disk)
  • Blob in encrypted_voiceprints/ directory
```

#### Technology Stack
- **Audio Capture**: librosa, PyAudio
- **Speaker Verification**: transformers (HuggingFace), torch (ECAPA-TDNN pre-trained)
- **Speech Recognition**: Vosk (offline, ~40MB model)
- **Encryption**: cryptography.fernet (AES-256)
- **Config**: PyYAML
- **Testing**: pytest with fixtures
- **Deployment**: setup.py + requirements.txt
- **Platform**: Python 3.8+, no GPU required (CPU friendly)

#### Security Threats & Mitigations

| Threat | Severity | Mitigation | Residual Risk |
|--------|----------|-----------|----------------|
| Voice Imitation / Deepfakes | HIGH | ECAPA-TDNN (99% accuracy), threshold tuning, liveness checks | MEDIUM (voice conversion tools advancing) |
| Replay Attack (Pre-recorded) | MEDIUM | Frequency/energy/silence checks | MEDIUM (sophisticated replays might add noise) |
| Voiceprint Exposure | MEDIUM | AES-256 Fernet encryption, env-based key | MEDIUM (if key leaked, embedding comparisons possible) |
| Command Injection | LOW | Whitelist-only regex matching | LOW (small curated list) |
| System Info Leakage | LOW | Output truncation, escaping | LOW |

---

## 🔗 System Integration

### How They Work Together

```
┌─────────────────────────────────────────────┐
│  LAYER 1: VOICE INTERFACE                   │
│  JARVIS (verification + commands)           │
└────────┬────────────────────────────────────┘
         │
         ├─→[Sends authenticated command]
         │
┌────────▼────────────────────────────────────┐
│  LAYER 2: API TRANSLATION                   │
│  Free Claude Code (proxy routing)            │
└────────┬────────────────────────────────────┘
         │
         ├─→[Converts Anthropic → Provider format]
         ├─→[Rate limiting, optimization]
         │
┌────────▼────────────────────────────────────┐
│  LAYER 3: AGENT RUNTIME                     │
│  Claw Code (orchestration + tools)          │
└────────┬────────────────────────────────────┘
         │
         ├─→[TaskRegistry, PermissionEnforcer]
         ├─→[Tool execution (bash, files, MCP, LSP)]
         │
┌────────▼────────────────────────────────────┐
│  LAYER 4: AI MODELS                         │
│  NVIDIA NIM / OpenRouter / LM Studio        │
└─────────────────────────────────────────────┘
```

### Integration Scenario 1: Voice-Activated Coding Assistant
```
User (speaking): "Hey Jarvis, ask Claude to write a Python function for sorting"
                           ↓
              JARVIS (voice verified)
                           ↓
              HTTP to Free Claude Code proxy
                           ↓
            Routes to NVIDIA NIM (free tier)
                           ↓
              NIM returns streamed response
                           ↓
         Claw Code tools available for refinement
                           ↓
      Result spoken back to user (optional TTS)
```

### Integration Scenario 2: Remote Bot Control via Discord
```
Discord user: "/claude write a CLI tool for organizing files"
                           ↓
        Free Claude Code Discord handler intercepts
                           ↓
              Message queued to CLI session
                           ↓
         Claw Code runtime orchestrates execution
                           ↓
         Tool registry provides bash + file tools
                           ↓
           Results posted back to Discord channel
```

### Integration Scenario 3: Local Autonomous Agent
```
User runs: claw-code --interactive
                           ↓
        Claw Code CLI starts task loop
                           ↓
            Requests Claude (via Free Claude Code)
                           ↓
              Claude uses tool registry to:
           • Read files
           • Execute bash commands  
           • Manage tasks
           • Query LSP/MCP tools
                           ↓
        Repeats until task complete
           (fully local, no internet)
```

---

## 📊 Quick Comparison

| Feature | Free Claude Code | Claw Code | JARVIS |
|---------|-----------------|-----------|--------|
| **Primary Role** | API Proxy | Agent Harness | Voice Auth |
| **State Management** | Stateless | Stateful (registries) | Biometric + logs |
| **Cloud Dependency** | Optional | None | Zero |
| **Tool Coverage** | Inherited | 40+ explicit specs | 9 whitelisted |
| **Security Focus** | Rate limiting | Permission enforcement | Biometric encryption |
| **Deployment** | Server (port 8082) | CLI or daemon | Local script |
| **Language Support** | Python | Python + Rust | Python |
| **Extensibility** | Add provider | Add tool + registry | Add command patterns |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (venv or conda)
- `uv` package manager (https://astral.sh/uv/)

### Quick Setup

#### 1. Free Claude Code (API Proxy)
```bash
# Activate venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env to set PROVIDER_TYPE (nvidia_nim, open_router, or lmstudio)

# Start proxy server (listens on port 8082)
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

#### 2. Claw Code (Agent Runtime)
```bash
cd "CLAW CODE/claw-code-parity"

# Python v1 (reference)
python -m src.main --help

# Rust v2 (production)
cargo build --release
./target/release/claw-code --interactive
```

#### 3. JARVIS (Voice Assistant)
```bash
cd JARVIS/jarvis_voice_assistant

# Install & setup
python setup.py

# Set encryption key
export JARVIS_ENCRYPTION_KEY="<generated-key>"

# Enroll your voice (7 samples)
python src/main.py --enroll

# Interactive mode (verify & execute)
python src/main.py --interactive
```

---

## 📝 Development Guidelines

### Code Quality Standards
All three systems enforce:
- ✅ **Strict typing**: No `# type: ignore` — fix the root cause
- ✅ **Formatting**: `uv run ruff format`
- ✅ **Linting**: `uv run ruff check`
- ✅ **Type checking**: `uv run ty check`
- ✅ **Testing**: `uv run pytest`

All CI checks must pass before merge.

### Architecture Principles (From CLAUDE.md & PLAN.md)
- **DRY**: Extract common logic to shared utilities
- **Encapsulation**: Use accessor methods for internal state
- **Provider/Tool abstraction**: Pluggable implementations
- **Fail-secure**: Default-deny for security decisions
- **Performance**: List accumulation, env var caching
- **Platform-agnostic naming**: Generic names in shared code
- **Clean imports**: No circular dependencies, backward-compat re-exports

---

## 📂 Directory Layout

```
free-claude-code/                    # Root workspace
├── WORKSPACE_README.md              # This file
├── WORKSPACE_ARCHITECTURE.md        # Detailed architecture
├── AGENTS.md                        # Agentic directive
├── CLAUDE.md                        # Coding standards (identical to AGENTS.md)
├── PLAN.md                          # Architecture principles
├── server.py                        # Free Claude Code entry
├── pyproject.toml                   # Project config
├── .env.example                     # Configuration template
│
├── api/                             # Free Claude Code API layer
│   ├── app.py, routes.py, dependencies.py
│   ├── models/, optimization_handlers.py
│   └── ...
│
├── providers/                       # Provider implementations
│   ├── base.py, common/, nvidia_nim/, open_router/, lmstudio/
│   └── ...
│
├── messaging/                       # Discord & Telegram bots
├── cli/                             # CLI session manager
├── config/                          # Configuration
├── utils/                           # Utilities
├── tests/                           # Test suite
│
├── CLAW CODE/claw-code-parity/      # Second system: Agent harness
│   ├── ARCHITECTURE.md, PARITY.md, README.md
│   ├── src/                         # Python reference
│   ├── rust/                        # Production port
│   └── tests/
│
├── JARVIS/jarvis_voice_assistant/   # Third system: Voice auth
│   ├── QUICKSTART.md, SECURITY.md, README.md
│   ├── setup.py, requirements.txt
│   ├── src/                         # Voice modules
│   ├── config/                      # Audio & command config
│   └── tests/
│
└── claude-code/                     # Reference: Original Claude Code
    ├── src/, components/, hooks/, etc.
    └── ...
```

---

## 🔐 Security Philosophy

### Fail-Secure Design
- **JARVIS**: Denies voice access by default; all checks must pass
- **Free Claude Code**: Rate limits prevent abuse; timeouts prevent hangs
- **Claw Code**: Permission enforcer gates all filesystem/bash operations

### Zero Trust
- Every request validated
- Environment variables treated as secrets
- Subprocess timeouts prevent resource exhaustion
- Output sanitization prevents info leakage

### Defense in Depth
- JARVIS: Biometric + liveness + audio analysis
- Free Claude Code: Rate limiting + error mapping
- Claw Code: Permissions + whitelist + timeout

---

## 🛠️ Troubleshooting

### Issue: "No module named 'uv'"
```bash
# Install astral uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal
```

### Issue: JARVIS audio capture fails
```bash
# Ensure PyAudio is installed (platform-specific)
# Linux: sudo apt-get install portaudio19-dev
# Mac: brew install portaudio
# Windows: pre-built wheel in requirements.txt

uv sync
```

### Issue: Free Claude Code 429 (Rate Limited)
```bash
# Check PROVIDER_TYPE in .env
# Switch to different provider or wait for quota reset
python src/main.py --health-check
```

### Issue: Claw Code permission denied on bash
```bash
# Check PermissionEnforcer configuration
# Verify command is in whitelist
# Check workspace boundary settings
```

---

## 📚 Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| **WORKSPACE_README.md** (this file) | System overview & integration | Everyone |
| **WORKSPACE_ARCHITECTURE.md** | Detailed technical architecture | Developers |
| **AGENTS.md & CLAUDE.md** | Coding standards & principles | Contributors |
| **PLAN.md** | Architecture principles & decisions | Architects |
| **free-claude-code/README.md** | Proxy usage & configuration | Free Claude Code users |
| **CLAW CODE/ARCHITECTURE.md** | Agent runtime internals | Agent developers |
| **CLAW CODE/PARITY.md** | 9-lane development overview | Team leads |
| **JARVIS/SECURITY.md** | Threat model & mitigations | Security reviewers |
| **JARVIS/IMPLEMENTATION_SUMMARY.md** | Voice system deep dive | Voice systems engineers |

---

## 📞 Support

For issues or contributions:
1. Check the relevant system's README
2. Review WORKSPACE_ARCHITECTURE.md for integration patterns
3. Run quality checks: `uv run ruff format && uv run ruff check && uv run ty check && uv run pytest`
4. Create a minimal reproduction case
5. File an issue with logs & configuration

---

## 📄 License

See LICENSE file for terms and conditions.

---

## 🎓 Key Insights

### Why Three Systems?
- **Free Claude Code** solves: "_Free_ Claude Code access"
- **Claw Code** solves: "Secure agentic orchestration with tools"
- **JARVIS** solves: "Voice-locked, offline AI assistant"
- Together: A complete, voice-first, autonomous AI system

### Why This Architecture?
- **Separation of concerns**: Each system has one responsibility
- **Composability**: Systems work together or independently
- **Extensibility**: Add providers (Free Claude Code), tools (Claw Code), or commands (JARVIS)
- **Security**: Multiple fail-secure layers
- **Testing**: Each system testable in isolation
- **Performance**: Streaming, caching, optimization at each layer

### Key Technologies
- **FastAPI**: Async request handling
- **Pydantic**: Type-safe config
- **transformers + torch**: Modern deep learning embeddings
- **Vosk**: Lightweight offline STT
- **Fernet**: Standard cryptography (AES-256)
- **Rust**: Memory-safe agent runtime (Claw Code v2)

---

**Last Updated**: April 7, 2026  
**Workspace Structure**: 3 Systems, 48.5K+ LOC, 99.2% Type Coverage
