# Register Machine Compiler - Backend API

## Overview

This is the **FastAPI backend service** for the Register Machine Compiler toolchain. It exposes the multi-phase compiler pipeline (Lexer → Parser → Semantic Analyzer → Lowerer) as a REST API, allowing web clients and other services to compile Register Machine assembly code.

### What This Service Does
- **Compiles** `.rm` source code to bytecode
- **Validates** programs for lexical, syntax, and semantic errors
- **Returns** structured error messages with source locations
- **Serves** the compiled bytecode as JSON

### What This Service Does NOT Do
- **Does not execute** code (execution happens in frontend client)
- **Does not provide UI** (UI is separate frontend service)
- **Does not store** programs (stateless service)

---

## Architecture

```
HTTP Request (JSON)
    ↓
FastAPI App → Extract source code & settings
    ↓
Compiler Pipeline (imports from src/register_machine/)
    ├─ Lexer: Tokenize source
    ├─ Parser: Build AST
    ├─ Semantic: Validate types & symbols
    └─ Lowerer: Generate bytecode
    ↓
JSON Response (bytecode or errors)
    ↓
HTTP Response
```

---

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{"status":"ok"}
```

### `POST /api/assemble`
Compile Register Machine assembly source code.

**Request Body:**
```json
{
  "source": "load 5\nadd 10\nhalt",
  "maxRegisters": 32
}
```

**Success Response (200):**
```json
{
  "success": true,
  "instructions": [
    {"op": "load", "arg": 5, "sourceLine": 1},
    {"op": "add", "arg": 10, "sourceLine": 2},
    {"op": "halt", "arg": null, "sourceLine": 3}
  ]
}
```

**Error Response (400):**
```json
{
  "success": false,
  "phase": "Lexical Error",
  "errors": "unexpected character 'x' at line 1, column 5"
}
```

**Error Response (500):**
```json
{
  "success": false,
  "errors": "Internal compiler crash: [error details]"
}
```

---

## Local Development

### 1. Setup Environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run with Hot Reload
```bash
ALLOWED_ORIGINS="*" python -m uvicorn api:app --reload --port 8000
```

### 3. Test the API
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test compilation
curl -X POST http://localhost:8000/api/assemble \
  -H "Content-Type: application/json" \
  -d '{
    "source": "load 5\nadd 10\nhalt",
    "maxRegisters": 32
  }'
```

---

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PORT` | HTTP port for API | `8000` | `8000` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` | `*` or `https://my-app.vercel.app` |
| `PYTHONUNBUFFERED` | Show logs immediately | `1` | `1` |

---

## Docker Deployment

The backend is deployed via the root [Dockerfile](../Dockerfile), which uses a multi-stage build:

**Build Stage:**
- Installs `build-essential` and compiler dependencies
- Runs `pip install -e .` (installs src/register_machine as editable package)
- Installs backend requirements from `requirements.txt`

**Runtime Stage:**
- Copies installed packages (no rebuild needed)
- Copies src/, backend/, frontend/ files
- Exposes port 8000
- Runs `python -m backend.api`

**Local testing:**
```bash
docker build -t compiler-dap2:local ..
docker run -p 8000:8000 -e ALLOWED_ORIGINS="*" compiler-dap2:local
```

---

## Docker Compose

For local development with frontend + backend together:
```bash
cd ..
docker compose up --build
```

This runs:
- Backend on :8000
- Frontend on :8080
- Auto-rebuilds when files change (via volume mounts)
  -H "Content-Type: application/json" \
  -d '{"source":"load 5\nhalt","maxRegisters":32}'
```

### 4. View Interactive Docs
Open **http://localhost:8000/docs** to see Swagger UI with interactive testing.

---

## Environment Variables

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `ALLOWED_ORIGINS` | CORS origins | `*` | `https://frontend.vercel.app` |
| `PORT` | HTTP port (Railway sets this) | `8000` | `8000` |

See `.env.example` for template.

---

## Production Deployment

### Docker Build & Run
```bash
docker build -t register-machine-api .
docker run -p 8000:8000 \
  -e ALLOWED_ORIGINS="https://your-frontend.com" \
  register-machine-api
```

### Deploy to Railway
1. Connect your GitHub repo to Railway
2. Create new service, set root to `backend/`
3. Railway auto-detects `Dockerfile`
4. Set environment variable: `ALLOWED_ORIGINS=https://your-vercel-frontend.vercel.app`
5. Deploy

Your API will be live at: `https://your-project.up.railway.app`

### Health Check
```bash
curl https://your-project.up.railway.app/health
```

---

## Code Structure

- **api.py**: FastAPI application, middleware setup, endpoint handlers
- **requirements.txt**: Python dependencies (FastAPI, uvicorn, pydantic)
- **Dockerfile**: Container configuration for Railway/Docker deployment
- **.env.example**: Template for environment variables

The backend imports compiler modules from `src/register_machine/` — it does not duplicate compiler logic.

---

## Integration with Frontend

The frontend calls this backend to compile code, then executes the resulting bytecode in the client-side JavaScript VM (no server-side execution).

**CORS Configuration:**
- Frontend URL must be in `ALLOWED_ORIGINS` environment variable
- If running on `localhost`, set `ALLOWED_ORIGINS="*"` for development

---

## Troubleshooting

### CORS Errors in Frontend
**Symptom:** Browser console shows "CORS policy: blocked"

**Solution:** Ensure frontend URL is in `ALLOWED_ORIGINS`:
```bash
ALLOWED_ORIGINS="http://localhost:8080,https://your-frontend.vercel.app" uvicorn api:app --reload
```

### Import Errors (`ModuleNotFoundError: No module named 'src'`)
**Symptom:** Python errors when starting API

**Solution:** Ensure you're running from the `backend/` folder with correct `sys.path` setup. The `api.py` file adds parent paths automatically.

### API Returns 500 Errors
**Solution:** Check server logs for full error stack trace. Likely issues:
- Syntax error in source code → should return 400 instead
- Bug in compiler logic → report as issue

---

## Further Reading

- [Main README](../README.md): Project overview
- [FULL_DOCUMENTATION.md](../FULL_DOCUMENTATION.md): Detailed compiler architecture
- [DEPLOYMENT.md](../DEPLOYMENT.md): Multi-service deployment guide
- [ARCHITECTURE_EVOLUTION.md](../ARCHITECTURE_EVOLUTION.md): Design decisions