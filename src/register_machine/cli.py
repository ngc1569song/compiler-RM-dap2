import os
import sys
import argparse
from typing import List, Optional
from src.register_machine.compiler.diagnostics import DiagnosticReporter
from src.register_machine.compiler.lexer import Lexer
from src.register_machine.compiler.parser import Parser
from src.register_machine.compiler.semantic import SemanticAnalyzer
from src.register_machine.compiler.lowering import Lowerer
from src.register_machine.compiler.ir import IRInstruction, serialize_ir, deserialize_ir
from src.register_machine.vm.machine import VirtualMachine
from src.register_machine.vm.execution import execute_program

def print_ast(node, indent: int = 0) -> None:
    """Helper to beautifully visualize the AST structure with clear indentations."""
    space = "  " * indent
    if node.__class__.__name__ == "ProgramNode":
        print(f"{space}\033[1mProgramNode\033[0m [span={node.span.start} to {node.span.end}]")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    else:
        # Construct attribute values excluding span
        attrs = ", ".join(
            f"\033[36m{k}\033[0m={repr(v)}" 
            for k, v in node.__dict__.items() if k != "span"
        )
        print(f"{space}{node.__class__.__name__}({attrs}) \033[90m[span={node.span.start}]\033[0m")

def compile_source(source: str, file_path: str, max_registers: int = 32) -> Optional[List[IRInstruction]]:
    """Helper pipeline to lex, parse, validate, and lower source code to IR bytecode."""
    reporter = DiagnosticReporter(source, file_path)

    # 1. Lexer Phase
    lexer = Lexer(source, reporter)
    tokens = lexer.tokenize()
    if reporter.has_errors:
        print("\033[91m\033[1mLexical Errors Found:\033[0m")
        reporter.print_diagnostics()
        return None

    # 2. Parser Phase
    parser = Parser(tokens, reporter)
    program = parser.parse()
    if reporter.has_errors:
        print("\033[91m\033[1mSyntax Errors Found:\033[0m")
        reporter.print_diagnostics()
        return None

    # 3. Semantic Analysis Phase
    analyzer = SemanticAnalyzer(program, reporter, max_registers=max_registers)
    success = analyzer.analyze()
    if not success or reporter.has_errors:
        print("\033[91m\033[1mSemantic Errors Found:\033[0m")
        reporter.print_diagnostics()
        return None

    # 4. Lowering Phase
    lowerer = Lowerer(program)
    return lowerer.lower()

def run_debugger(instructions: List[IRInstruction], max_registers: int = 32) -> None:
    """A fully interactive, premium command-line debugger for VM execution."""
    vm = VirtualMachine(instructions, max_registers=max_registers)
    print("\033[96m\033[1m=== Interactive Register Machine Debugger ===\033[0m")
    print(f"Loaded {len(instructions)} instructions. Registers limit: {max_registers}.")
    print("Type 'help' or 'h' for list of commands.\n")

    vm.dump_state()
    print("-" * 50)

    while not vm.halted:
        pc = vm.pc
        if pc < 0 or pc >= len(instructions):
            print(f"\033[91mProgram Counter PC={pc} is out of bounds! Interrupted.\033[0m")
            break

        next_inst = instructions[pc]
        prompt = f"\033[94m(dbg PC:{pc:02d} | {next_inst})>\033[0m "
        
        try:
            line = input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting debugger...")
            break

        if not line:
            # Default behavior is to step on empty press
            line = "step"

        parts = line.split()
        cmd = parts[0]

        if cmd in ("h", "help"):
            print("Debugger Commands:")
            print("  s, step      - Execute the current instruction and step to the next")
            print("  b, back      - Step backward to the previous instruction")
            print("  c, continue  - Resume full execution until halt or interrupt")
            print("  d, dump      - Print current register bank values")
            print("  l, list      - Show instructions surrounding the current PC")
            print("  q, quit      - Quit the debugger session")
        elif cmd in ("s", "step"):
            try:
                print(f"Stepping: {next_inst}")
                vm.step()
                vm.dump_state()
                print("-" * 50)
            except Exception as e:
                print(f"\033[91mExecution Error:\033[0m {str(e)}")
                break
        elif cmd in ("b", "back"):
            if vm.step_back():
                print("Stepped back to previous instruction.")
                vm.dump_state()
                print("-" * 50)
            else:
                print("\033[93mWarning: Already at the beginning of program history. Cannot step back further.\033[0m")
                print("-" * 50)
        elif cmd in ("c", "continue"):
            print("Resuming execution...")
            vm.run(trace=True)
            break
        elif cmd in ("d", "dump"):
            vm.dump_state()
            print("-" * 50)
        elif cmd in ("l", "list"):
            start = max(0, pc - 2)
            end = min(len(instructions), pc + 3)
            for i in range(start, end):
                pointer = "\033[92m=>\033[0m " if i == pc else "   "
                print(f"{pointer}{i:02d}: {instructions[i]}")
            print("-" * 50)
        elif cmd in ("q", "quit"):
            print("Quitting debugger.")
            break
        else:
            print(f"Unknown debugger command: '{cmd}'. Type 'help' for info.")

    if vm.halted:
        print("\033[92m\033[1mProgram halted.\033[0m")
        vm.dump_state()

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register Machine Compiler & Virtual Machine Toolchain CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # Lex Subcommand
    lex_p = subparsers.add_parser("lex", help="Run the lexical analyzer and print tokens")
    lex_p.add_argument("file", help="Path to .rm source file")

    # AST Subcommand
    ast_p = subparsers.add_parser("ast", help="Parse the source code and print the strongly typed AST")
    ast_p.add_argument("file", help="Path to .rm source file")

    # Compile Subcommand
    comp_p = subparsers.add_parser("compile", help="Compile and assemble source file to lowered IR JSON bytecode")
    comp_p.add_argument("file", help="Path to .rm source file")
    comp_p.add_argument("-o", "--output", help="Output file path (default: replaces .rm extension with .rmb)")
    comp_p.add_argument("-r", "--registers", type=int, default=32, help="Validate registers limit (default: 32)")

    # Run Subcommand
    run_p = subparsers.add_parser("run", help="Run a source code (.rm) or compiled bytecode (.rmb) program")
    run_p.add_argument("file", help="Path to .rm source file or .rmb JSON bytecode file")
    run_p.add_argument("-t", "--trace", action="store_true", help="Print step-by-step tracing log")
    run_p.add_argument("-r", "--registers", type=int, default=32, help="Set registers count limit (default: 32)")
    run_p.add_argument("-c", "--cycles", type=int, help="Optional cycles threshold to prevent execution hang")

    # Debug Subcommand
    db_p = subparsers.add_parser("debug", help="Start the interactive debugger on a program")
    db_p.add_argument("file", help="Path to .rm source file or .rmb JSON bytecode file")
    db_p.add_argument("-r", "--registers", type=int, default=32, help="Set registers count limit (default: 32)")

    args = parser.parse_args()

    # Read target file content
    if not os.path.exists(args.file):
        print(f"\033[91mError: File not found: '{args.file}'\033[0m")
        sys.exit(1)

    # 1. Lex command execution
    if args.command == "lex":
        with open(args.file, "r") as f:
            source = f.read()
        reporter = DiagnosticReporter(source, args.file)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        if reporter.has_errors:
            print("\033[91mLexical Errors Found:\033[0m")
            reporter.print_diagnostics()
            sys.exit(1)
        
        print("\033[92m\033[1mTokens Scanned:\033[0m")
        for token in tokens:
            print(f"  {token}")

    # 2. AST command execution
    elif args.command == "ast":
        with open(args.file, "r") as f:
            source = f.read()
        reporter = DiagnosticReporter(source, args.file)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        if reporter.has_errors:
            reporter.print_diagnostics()
            sys.exit(1)
        parser = Parser(tokens, reporter)
        program = parser.parse()
        if reporter.has_errors:
            reporter.print_diagnostics()
            sys.exit(1)
        
        print("\033[92m\033[1mAST Tree Representation:\033[0m")
        print_ast(program)

    # 3. Compile command execution
    elif args.command == "compile":
        with open(args.file, "r") as f:
            source = f.read()
        
        ir = compile_source(source, args.file, max_registers=args.registers)
        if ir is None:
            sys.exit(1)
        
        bytecode = serialize_ir(ir)
        
        out_path = args.output
        if not out_path:
            base, _ = os.path.splitext(args.file)
            out_path = base + ".rmb"

        with open(out_path, "w") as f:
            f.write(bytecode)
        
        print(f"\033[92mAssembly lowering complete. Bytecode saved to: '{out_path}'\033[0m")

    # 4. Run command execution
    elif args.command == "run":
        # Check if compiling or reading compiled bytecode
        _, ext = os.path.splitext(args.file)
        instructions: Optional[List[IRInstruction]] = None
        
        if ext.lower() == ".rmb":
            # Direct bytecode read
            with open(args.file, "r") as f:
                bytecode_str = f.read()
            try:
                instructions = deserialize_ir(bytecode_str)
            except Exception as e:
                print(f"\033[91mError reading compiled bytecode:\033[0m {str(e)}")
                sys.exit(1)
        else:
            # Source file compile-on-the-fly
            with open(args.file, "r") as f:
                source = f.read()
            instructions = compile_source(source, args.file, max_registers=args.registers)
            if instructions is None:
                sys.exit(1)

        execute_program(
            instructions=instructions,
            trace=args.trace,
            max_registers=args.registers,
            max_cycles=args.cycles
        )

    # 5. Debug command execution
    elif args.command == "debug":
        _, ext = os.path.splitext(args.file)
        instructions = None
        
        if ext.lower() == ".rmb":
            with open(args.file, "r") as f:
                bytecode_str = f.read()
            try:
                instructions = deserialize_ir(bytecode_str)
            except Exception as e:
                print(f"\033[91mError reading compiled bytecode:\033[0m {str(e)}")
                sys.exit(1)
        else:
            with open(args.file, "r") as f:
                source = f.read()
            instructions = compile_source(source, args.file, max_registers=args.registers)
            if instructions is None:
                sys.exit(1)

        run_debugger(instructions, max_registers=args.registers)

if __name__ == "__main__":
    main()
