# AGENTS

## Project summary
This repository contains a Python-based register machine compiler, assembler, and virtual machine runtime, plus a FastAPI backend and browser-based frontend visualizer.

The compiler core lives under `src/register_machine/` and is shared by:
- the CLI in `src/register_machine/cli.py`
- the backend adapter in `backend/api.py`

The frontend lives in `frontend/` and is mostly JavaScript UI/visualization code.

## Important files and directories
- `README.md` — top-level quick start and architecture summary
- `FULL_DOCUMENTATION.md` — comprehensive project reference
- `ARCHITECTURE_EVOLUTION.md` — design decisions and migration notes
- `src/register_machine/cli.py` — CLI entrypoint for compile/run/debug
- `src/register_machine/compiler/` — lexer, parser, semantic analysis, lowering, diagnostics, symbols
- `src/register_machine/vm/` — VM execution components, instruction dispatch, registers
- `src/register_machine/HOW_TO_ADD_INSTRUCTION.md` — documented pattern for adding new instructions
- `backend/api.py` — FastAPI backend adapter that exposes compilation via HTTP
- `frontend/` — browser UI, buildless web app, client-side VM integration, and frontend Dockerfile
- `backend/requirements.txt`, root `Dockerfile`, `docker-compose.yml`, `DEPLOYMENT.md`, `DOCKER.md` — deployment and runtime configuration

## How to run and test
- CLI compile / run: `python src/register_machine/cli.py run examples/sum.rm --trace`
- Unit tests: `python -m pytest src/register_machine/tests`
- Backend development: `cd backend && python -m uvicorn api:app --reload --port 8000`
- Frontend development: `cd frontend && python -m http.server 8080`
- Docker deployment: see root `Dockerfile`, `frontend/Dockerfile`, and `docker-compose.yml`

## Key conventions for AI agents
- Preserve separation of concerns: compiler core, backend adapter, and frontend UI are distinct layers.
- The compiler pipeline is phase-separated: lexer → parser → semantic analyzer → lowerer → VM.
- Instruction parsing is registry-driven in `src/register_machine/compiler/parser.py`.
- VM execution is dispatch-table driven in `src/register_machine/vm/instruction_set.py`.
- Diagnostics use structured spans; error reporting is important and should not be dropped.
- Backend changes should adapt compiler output rather than reimplement compiler phases.
- Frontend changes should be isolated to UI/visualization code unless the underlying VM or instruction semantics change.

## When editing this repo
- If the task is compiler-related, start with `src/register_machine/compiler/` and `src/register_machine/vm/`.
- If the task is backend or API-related, start with `backend/api.py` and `backend/requirements.txt`.
- If the task is UI-related, start with `frontend/`.
- Link to existing docs rather than copying long explanations.
- If a requested change affects both CLI and backend, update the shared `src/register_machine/` package and keep adapter layers thin.
