from register_machine.compiler.diagnostics import DiagnosticReporter, Span
from register_machine.compiler.ast_nodes import (
    ProgramNode, LabelNode, ReadNode, StoreNode, LoadNode, AddNode, SubNode,
    JumpNode, JposNode, JnegNode, JzeroNode, HaltNode
)
from register_machine.compiler.symbols import SymbolTable

class SemanticAnalyzer:
    def __init__(self, program: ProgramNode, reporter: DiagnosticReporter, max_registers: int = 32):
        self.program = program
        self.reporter = reporter
        self.max_registers = max_registers
        self.symbol_table = SymbolTable()
        self._build_line_to_instruction_map()

    def _build_line_to_instruction_map(self) -> None:
        """Build mapping of source line numbers to instruction indices."""
        self.line_to_instruction = {}
        instruction_idx = 0
        for stmt in self.program.statements:
            if not isinstance(stmt, LabelNode):
                source_line = stmt.span.start.line
                self.line_to_instruction[source_line] = instruction_idx
                instruction_idx += 1
        self.total_instructions = instruction_idx

    def analyze(self) -> bool:
        """Runs the semantic checks. Returns True if analysis succeeded without errors."""
        self._collect_labels()
        self._validate_statements()
        return not self.reporter.has_errors

    def _collect_labels(self) -> None:
        """Pass 1: Collect and define all labels, detecting duplicates."""
        for stmt in self.program.statements:
            if isinstance(stmt, LabelNode):
                success = self.symbol_table.insert(stmt.name, "label", stmt.span)
                if not success:
                    existing = self.symbol_table.lookup(stmt.name)
                    existing_loc = existing.span.start if existing else None
                    hint_msg = f"Rename this label. It was already defined on line {existing_loc.line}." if existing_loc else None
                    self.reporter.error(
                        f"Duplicate label definition: '{stmt.name}'",
                        stmt.span,
                        hint=hint_msg
                    )

    def _validate_statements(self) -> None:
        """Pass 2: Validate register indices, integer operands, and jump targets."""
        for stmt in self.program.statements:
            if isinstance(stmt, (ReadNode, StoreNode)):
                # Validate register bounds: must be 0 <= reg < max_registers
                reg = stmt.register
                op_name = "read" if isinstance(stmt, ReadNode) else "store"
                if reg < 0 or reg >= self.max_registers:
                    self.reporter.error(
                        f"Register index {reg} is out of bounds for '{op_name}'",
                        stmt.span,
                        hint=f"Valid register indices are 0 to {self.max_registers - 1} inclusive (total {self.max_registers} registers)."
                    )

            elif isinstance(stmt, (LoadNode, AddNode, SubNode)):
                # Validate 32-bit signed integer boundaries
                val = stmt.value
                op_name = (
                    "load" if isinstance(stmt, LoadNode) else
                    "add" if isinstance(stmt, AddNode) else "sub"
                )
                min_val = -2147483648
                max_val = 2147483647
                if val < min_val or val > max_val:
                    self.reporter.error(
                        f"Immediate operand '{val}' out of 32-bit signed integer range for '{op_name}'",
                        stmt.span,
                        hint=f"Literal value must be between {min_val} and {max_val} inclusive."
                    )

            elif isinstance(stmt, (JumpNode, JposNode, JnegNode, JzeroNode)):
                # Validate jump target exists
                target = stmt.target
                op_name = (
                    "jump" if isinstance(stmt, JumpNode) else
                    "jpos" if isinstance(stmt, JposNode) else
                    "jneg" if isinstance(stmt, JnegNode) else "jzero"
                )
                
                # Check if target is a numeric value (could be line number or instruction index)
                is_numeric = False
                target_val = 0
                try:
                    target_val = int(target)
                    is_numeric = True
                except ValueError:
                    pass

                if is_numeric:
                    # Check if it's a valid source line number first
                    if target_val in self.line_to_instruction:
                        # Valid: it's a line number that has an instruction
                        pass
                    elif 0 <= target_val < self.total_instructions:
                        # Valid: it's a direct instruction index
                        pass
                    else:
                        # Invalid: not a valid line number or instruction index
                        self.reporter.error(
                            f"Jump target '{target_val}' is invalid for '{op_name}'",
                            stmt.span,
                            hint=f"Use a source line number (1-{max(self.line_to_instruction.keys()) if self.line_to_instruction else 0}) or instruction index (0-{self.total_instructions - 1})."
                        )
                else:
                    # Check label symbol exists
                    if not self.symbol_table.exists(target):
                        self.reporter.error(
                            f"Undefined jump target label: '{target}' inside '{op_name}' instruction",
                            stmt.span,
                            hint=f"Define the label '{target}:' elsewhere in the program."
                        )
