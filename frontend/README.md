# Register Machine Compiler - Frontend UI

## Overview

This is the **browser-based interactive IDE** for the Register Machine Compiler. It provides a code editor, compiler interface, and visual debugger that runs entirely in the client (with compilation delegated to the backend API).

### Features
- **Live Code Editor**: Write Register Machine assembly directly
- **One-Click Compilation**: Assemble code via backend API
- **Client-Side VM**: Execute bytecode in JavaScript (no server execution)
- **Interactive Debugger**: Step through execution with visual feedback
- **Register Inspector**: Monitor register state changes
- **Error Visualization**: Highlighted error messages with source locations
- **Responsive Design**: Works on desktop and tablet

---

## Architecture

```
Browser UI (HTML/CSS)
    ↓
JavaScript Frontend (main.js)
    ├─ Code Editor UI
    ├─ Compile Button Handler → POST /api/assemble
    └─ VM Simulation
        ├─ Client-Side VM (JavaScript port of Python VM)
        ├─ Step / Continue / Reset controls
        └─ Register Display & Trace Output

Backend API (optional)
    ↓ (used only for compilation)
    Python Compiler Pipeline
```

### Key Design Decision: Client-Side Execution

Unlike traditional web IDEs that execute on the server, this frontend:
1. **Sends source code** to backend only for compilation (lexing, parsing, semantic analysis)
2. **Receives compiled bytecode** (flat array of instructions)
3. **Executes bytecode** entirely in the browser using a JavaScript VM
4. **Never sends runtime state** to backend — all execution is local

**Benefits:**
- ✅ No server load from execution
- ✅ Instant feedback on step/continue
- ✅ Works offline after code is compiled
- ✅ Scales to unlimited concurrent users

---

## Anatomy of Files

| File | Purpose |
|------|---------|
| **index.html** | Page structure, elements for editor, output, registers |
| **main.js** | JavaScript VM, UI logic, event handlers, compilation flow |
| **config.js** | API endpoint configuration (switches between localhost and cloud) |
| **styles.css** | Styling for editor, debugger controls, register display |

---

## Local Development

### Option 1: Docker Compose (Easiest)
```bash
cd ..
docker compose up --build
```

Frontend: http://localhost:8080  
Backend: http://localhost:8000

Frontend automatically connects to backend at `http://localhost:8000`.

### Option 2: Manual Setup (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd ../backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd ../frontend
python -m http.server 8080
```

Then open **http://localhost:8080** in your browser.

---

## Configuring API Endpoint

### For Local Development
The frontend defaults to connecting to `http://localhost:8000`. If you're using a different port or host:

**In browser console (F12):**
```javascript
// Override API endpoint
window.API_BASE_URL = 'http://localhost:8000';
location.reload();
```

Or edit `config.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000';  // Change this
```

### For Production
The API endpoint is set in `config.js`:
```javascript
const API_BASE_URL = 'https://your-backend.up.railway.app';
```

---

## How It Works

### 1. User Writes Code
```
load 5
add 3
halt
```

### 2. Click "Compile" Button
Frontend sends POST request to backend:
```javascript
POST /api/assemble
{
  "source": "load 5\nadd 3\nhalt",
  "maxRegisters": 32
}
```

### 3. Backend Compiles
Backend runs through: Lexer → Parser → Semantic Analyzer → Lowerer
Returns compiled instructions:
```json
{
  "success": true,
  "instructions": [
    {"op": "load", "arg": 5, "sourceLine": 1},
    {"op": "add", "arg": 3, "sourceLine": 2},
    {"op": "halt", "arg": null, "sourceLine": 3}
  ]
}
```

### 4. Frontend Loads and Executes
JavaScript VM loads the instruction array. All execution happens in the browser.

### 5. Step or Run
- **Step**: Execute one instruction, show register changes
- **Run**: Execute until halt or user stops
- **Reset**: Clear state and start over

No further backend calls are made during execution.

The VM supports all instructions:
- `load`, `add`, `sub` (ALU operations)
- `read`, `store` (register access)
- `jump`, `jpos`, `jneg`, `jzero` (control flow)
- `halt` (termination)

---

## Troubleshooting

### Compilation Fails with CORS Error
**Symptom:** Browser console shows "CORS policy: blocked"

**Solution:** Ensure backend `ALLOWED_ORIGINS` includes your frontend URL:
```bash
ALLOWED_ORIGINS="http://localhost:8080" uvicorn api:app --reload
```

### API Endpoint is Wrong
**Symptom:** "Fetch error" or timeout when clicking Assemble

**Solution:** Check in browser console:
```javascript
console.log(window.API_BASE_URL);
```

Should match your backend service. If running locally, should be `http://localhost:8000`.

### Bytecode Doesn't Execute
**Symptom:** Compiled successfully, but stepping doesn't work

**Solution:** Check for runtime errors in browser console (F12). JavaScript VM errors will be logged there.

---

## Further Reading

- [Main README](../README.md): Project overview
- [Backend README](../backend/README.md): API documentation
- [FULL_DOCUMENTATION.md](../FULL_DOCUMENTATION.md): Detailed compiler architecture
- [DEPLOYMENT.md](../DEPLOYMENT.md): Multi-service deployment guide
- [ARCHITECTURE_EVOLUTION.md](../ARCHITECTURE_EVOLUTION.md): Design decisions