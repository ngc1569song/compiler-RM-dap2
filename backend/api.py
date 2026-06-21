import os
import sys
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Ensure project paths are available so we can import compiler modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(CURRENT_DIR)
# Always add the workspace root so 'src.register_machine' imports work from any cwd
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from register_machine.compiler.diagnostics import DiagnosticReporter
from register_machine.compiler.lexer import Lexer
from register_machine.compiler.parser import Parser
from register_machine.compiler.semantic import SemanticAnalyzer
from register_machine.compiler.lowering import Lowerer


def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

app = FastAPI()

# CORS: Read allowed origins from env var, default to all (*) for dev
allowed = os.environ.get('ALLOWED_ORIGINS', '*')
if allowed == '*':
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AssembleRequest(BaseModel):
    source: str
    maxRegisters: int = 32


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/api/assemble')
def assemble(req: AssembleRequest):
    source = req.source or ''
    max_registers = int(req.maxRegisters or 32)
    try:
        reporter = DiagnosticReporter(source, "program.rm")

        # 1. Lexer Phase
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        if reporter.has_errors:
            err_msg = strip_ansi(reporter.format_diagnostics())
            raise HTTPException(status_code=400, detail={"success": False, "errors": err_msg, "phase": "Lexical Error"})

        # 2. Parser Phase
        parser = Parser(tokens, reporter)
        program = parser.parse()
        if reporter.has_errors:
            err_msg = strip_ansi(reporter.format_diagnostics())
            raise HTTPException(status_code=400, detail={"success": False, "errors": err_msg, "phase": "Syntax Error"})

        # 3. Semantic Analysis Phase
        analyzer = SemanticAnalyzer(program, reporter, max_registers=max_registers)
        sem_success = analyzer.analyze()
        if not sem_success or reporter.has_errors:
            err_msg = strip_ansi(reporter.format_diagnostics())
            raise HTTPException(status_code=400, detail={"success": False, "errors": err_msg, "phase": "Semantic Analysis Error"})

        # 4. Lowering
        lowerer = Lowerer(program)
        instructions = lowerer.lower()

        serialized_insts = [
            {"op": inst.op, "arg": inst.arg, "sourceLine": inst.source_line}
            for inst in instructions
        ]

        return {"success": True, "instructions": serialized_insts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"success": False, "errors": f"Internal compiler crash: {str(e)}"})


def main() -> None:
    import uvicorn
    port = int(os.environ.get('PORT', '8000'))
    uvicorn.run(app, host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
