# Register Machine Compiler + VM Toolchain

A highly maintainable, strongly typed compiler, assembler, and virtual machine toolchain built in Python for a register-machine ISA. It features a completely decoupled architecture, extensible registries, structured diagnostic systems with visual pointing, and a fully interactive CLI step-debugger.

This project includes both a **command-line interface (CLI)** for local development and a **full-stack web application** with a FastAPI backend and interactive JavaScript frontend for cloud deployment.

---

## Quick Start

### Option 1: Docker Compose (Multi-Container, Recommended for Testing)
```bash
docker compose up --build
```
- Backend API: http://localhost:8000
- Frontend IDE: http://localhost:3000
- Test health: `curl http://localhost:8000/health`

### Option 2: Local Development (CLI + Manual Services)

**Setup environment (one-time):**
```powershell
# Windows
.\setup.ps1

# macOS/Linux
bash setup.sh
```

**Run CLI compiler & debugger:**
```bash
python src/register_machine/cli.py run examples/sum.rm --trace
python src/register_machine/cli.py debug examples/countdown.rm
```

**Run Web IDE locally (two terminals):**
```bash
# Terminal 1: Backend API
cd backend
python -m uvicorn api:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
python -m http.server 8080
# Open http://localhost:8080 in browser
```

---

## System Architecture & Compiler Pipeline

The project implements a classic multi-phase compiler pipeline:

```text
Source Text (.rm) 
  ↓ [Lexical Analysis]
Tokens (with Line & Column positions)
  ↓ [Parser Analysis]
Abstract Syntax Tree (strongly-typed immutable AST nodes)
  ↓ [Semantic Analysis]
Verified AST & Symbol Table (validates jumps, registers, duplicate labels, literals)
  ↓ [Lowering/Code Generation]
Lowered IR (Label symbols resolved to concrete program address offsets)
  ↓ [JSON Serialization]
Bytecode File (.rmb) or Direct VM Execution
```

### Decoupled Phases
1. **Lexer** ([compiler/lexer.py](./compiler/lexer.py)): Performs no grammar or semantic checks. Scans inputs into `Token` objects with exact line and column ranges.
2. **Parser** ([compiler/parser.py](./compiler/parser.py)): Converts tokens into an AST using a **Parser Registry** (eliminating monolithic if-else blocks). Includes synchronizing error recovery to find multiple syntax errors on different lines in one compile.
3. **Semantic Analyzer** ([compiler/semantic.py](./compiler/semantic.py)): Compiles a Symbol Table of labels and executes static analysis: checks label duplicates, makes sure all jumps target declared labels, and validates that register indices are in-bounds and constants fit 32-bit signed integers.
4. **Lowerer** ([compiler/lowering.py](./compiler/lowering.py)): Emits a flat array of `IRInstruction` bytecode, using a two-pass label resolver to map string targets to integer program-counter indices.
5. **Virtual Machine** ([vm/machine.py](./vm/machine.py)): Executes the flat IR bytecode using an instruction dispatch table ([vm/instruction_set.py](./vm/instruction_set.py)) and register bank ([vm/registers.py](./vm/registers.py)). The VM has zero knowledge of source code, syntax, or label names.

---

## Project Structure

```text
compiler-DAP2-Copie/
├── src/
│   └── register_machine/
│       ├── compiler/              # Compiler frontend package
│       │   ├── ast_nodes.py       # Immutable strongly-typed AST nodes
│       │   ├── diagnostics.py     # Diagnostics reporter with visual line-pointing
│       │   ├── ir.py              # Flat IR bytecode structure and JSON serialization
│       │   ├── lexer.py           # Character-by-character scanner
│       │   ├── lowering.py        # Two-pass assembler lowering
│       │   ├── parser.py          # Extensible registry parser
│       │   ├── semantic.py        # Label, register, and integer boundary analyzer
│       │   ├── symbols.py         # Symbol table mapping
│       │   └── tokens.py          # Token types and structures
│       │
│       ├── vm/                    # Virtual machine backend package
│       │   ├── execution.py       # High-level runner helper
│       │   ├── instruction_set.py # Modulized instruction executions and dispatch table
│       │   ├── machine.py         # CPU registers and executor
│       │   └── registers.py       # Accumulator r0 and register array r_j
│       │
│       ├── examples/              # Sample source programs
│       │   ├── countdown.rm       # Simple branch decrement
│       │   ├── multiply.rm        # Repeated addition multiply
│       │   └── sum.rm             # Complex nested sum loop
│       │
│       ├── tests/                 # Full unit-testing suite
│       ├── cli.py                 # Main pipeline runner & interactive debugger CLI
│       └── HOW_TO_ADD_INSTRUCTION.md # Extension guidelines
│
├── backend/                       # FastAPI REST API server
│   ├── api.py                     # FastAPI application with /api/assemble endpoint
│   ├── requirements.txt           # Python dependencies (FastAPI, uvicorn)
│   ├── Dockerfile                 # Container configuration for deployment
│   ├── .env.example               # Environment variables template
│   └── README.md                  # Backend-specific documentation
│
├── frontend/                      # Web UI (HTML/CSS/JavaScript)
│   ├── index.html                 # Main entry point
│   ├── main.js                    # Interactive UI logic + client-side VM
│   ├── config.js                  # Environment configuration (API endpoint)
│   ├── styles.css                 # Styling
│   ├── vercel.json                # Vercel deployment config
│   └── README.md                  # Frontend-specific documentation
│
├── AGENTS.md                      # AI agent guidance for project structure
├── Dockerfile                     # Production multi-stage build
├── docker-compose.yml             # Local development orchestration
├── setup.ps1                      # Windows venv setup script
├── setup.sh                       # macOS/Linux venv setup script
├── .gitignore                     # Git exclusions (venv, __pycache__, etc.)
├── README.md                      # This file
└── pyproject.toml                 # Project metadata & dependencies
```

---

## Architecture Overview

### Classical Three-Tier Web Architecture

```
┌─────────────────────────────────────┐
│     Browser Frontend (React UI)     │
│  (HTML/CSS/JavaScript + Client VM)  │
│  - Code Editor                      │
│  - Interactive Debugger             │
│  - Visual Register/Memory Display   │
└────────────┬────────────────────────┘
             │ HTTP REST API
             │ (Compile, Assemble)
┌────────────▼────────────────────────┐
│      Backend API (FastAPI)          │
│  - Lexer, Parser, Semantic Analysis │
│  - Lowerer, IR Generation           │
│  - CORS Middleware                  │
└────────────┬────────────────────────┘
             │ Python Imports
┌────────────▼────────────────────────┐
│    Compiler Core (src/register_)   │
│    - Shared by CLI and API          │
│    - No dependencies on server      │
│    - Pure functional compilation    │
└─────────────────────────────────────┘
```

### Separation of Concerns

1. **Compiler Core** (`src/register_machine/`): Pure compilation logic, used by both CLI and API
2. **Backend API** (`backend/api.py`): REST interface to the compiler, no UI knowledge
3. **Frontend UI** (`frontend/main.js`): Interactive editor and debugger client, calls API endpoints

This decoupling allows:
- CLI users to compile/debug locally without web infrastructure
- Web users to compile and execute entirely in the browser (client-side VM)
- Backend-only deployment for headless systems
- Independent scaling of frontend and backend services

---

## Directory Structure

## Usage Guide & Command Line Commands

Run `cli.py` to interact with any pipeline phase.

### 1. Lexical Token Inspection
Tokenize a program and print its tokens:
```bash
python cli.py lex examples/countdown.rm
```

### 2. AST Visualizer
Parse a program and print its visual AST hierarchy tree:
```bash
python cli.py ast examples/countdown.rm
```

### 3. Compile Bytecode
Assemble a `.rm` program and compile it to a serialized `.rmb` JSON bytecode file:
```bash
python cli.py compile examples/countdown.rm -o countdown.rmb
```

### 4. VM Execution
Run a `.rm` source program directly (on-the-fly compile) or run a compiled `.rmb` bytecode:
```bash
python cli.py run examples/sum.rm
```
Use `-t` or `--trace` to print full register state traces at each cycle step:
```bash
python cli.py run examples/multiply.rm --trace
```
Set register size limits (default is 32 registers):
```bash
python cli.py run examples/countdown.rm -r 16
```

### 5. Interactive Terminal Debugger
Launch the premium interactive step-debugger on any program:
```bash
python cli.py debug examples/sum.rm
```

**Debugger Prompt Commands:**
* `s` or `step` or just pressing `Enter`: Step and execute exactly one instruction, then print registers.
* `c` or `continue`: Resume execution until a `halt` instruction or user interruption.
* `d` or `dump`: Dump registers bank values.
* `l` or `list`: Print instructions around current Program Counter.
* `q` or `quit`: Terminate session.

---

## Instruction Set Architecture (ISA) Reference

| Instruction | Type | Action Semantics |
| :--- | :--- | :--- |
| `read j` | Register | `r0 := r_j` (Load value of register `j` into accumulator) |
| `store j` | Register | `r_j := r0` (Store accumulator `r0` value into register `j`) |
| `load x` | Immediate | `r0 := x` (Load immediate integer `x` into accumulator) |
| `add x` | Immediate | `r0 := r0 + x` (Add immediate integer `x` to accumulator) |
| `sub x` | Immediate | `r0 := r0 - x` (Subtract immediate integer `x` from accumulator) |
| `jump label` | Control | `PC := label` (Unconditional jump) |
| `jpos label` | Control | `if r0 > 0: PC := label` (Jump if accumulator is positive) |
| `jneg label` | Control | `if r0 < 0: PC := label` (Jump if accumulator is negative) |
| `jzero label` | Control | `if r0 == 0: PC := label` (Jump if accumulator is zero) |
| `halt` | Control | Stop execution |

---

## Diagnostic System & Visual Errors

Our compiler contains a robust diagnostic printer. When errors are found during lexical, syntax, or semantic analysis, they are cleanly shown with absolute locations and visual indicators:

```text
SEMANTIC ERROR: Register index 35 is out of bounds for 'store'
  --> program.rm:5:11
    |
  4 |     load 10
  5 |     store 35
    |           ^^
    = hint: Valid registers are 0 to 31 inclusive (Current VM holds max 32 registers).
```

---

## Web IDE & Browser Visualizer

### Features
- **Live Code Editor**: Write `.rm` programs directly in the browser
- **One-Click Compile**: Assemble code via the backend API
- **Interactive Debugger**: Step through execution with register inspection
- **Visual Trace Output**: See register state changes at each cycle
- **Client-Side VM**: Execute compiled bytecode entirely in the browser (no server round-trip)

---

## Docker Compose Development

This repo includes `docker-compose.yml` for quick local setup with both services:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    volumes:
      - ./backend:/app/backend
      - ./src:/app/src
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - backend
```

**Run it:**
```bash
docker compose up --build
```

- Backend running: `curl http://localhost:8000/health` → `{"status":"ok"}`
- Frontend serving: Open http://localhost:3000

---

## Deployment to Cloud

This is a monorepo designed for multi-service deployment:

### Backend (FastAPI on Railway/Render)
- Dockerfile auto-detected at repo root
- `ALLOWED_ORIGINS` env var controls CORS (set to frontend domain in production)
- Example: `ALLOWED_ORIGINS=https://my-app.vercel.app`

### Frontend (Static on Vercel/Cloudflare Pages)
- Deploy `frontend/` folder as static site
- Point frontend config to backend API URL via environment variables

### Reference Documentation
- For detailed architecture: See [AGENTS.md](AGENTS.md) (AI guidance)
- For extending ISA: See [src/register_machine/HOW_TO_ADD_INSTRUCTION.md](src/register_machine/HOW_TO_ADD_INSTRUCTION.md)

---

## Architecture Evolution

For a detailed explanation of all recent changes, new components, and architectural decisions, see [ARCHITECTURE_EVOLUTION.md](ARCHITECTURE_EVOLUTION.md).
