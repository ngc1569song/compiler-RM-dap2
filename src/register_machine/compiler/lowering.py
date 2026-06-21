import dataclasses
from typing import List, Dict, Callable
from register_machine.compiler.ast_nodes import (
    ASTNode, ProgramNode, LabelNode, ReadNode, StoreNode, LoadNode, AddNode, SubNode,
    JumpNode, JposNode, JnegNode, JzeroNode, HaltNode
)
from src.register_machine.compiler.ir import IRInstruction

# Registry to map AST node types to their lowering handlers.
# This ensures easy extensibility when adding new instructions.
LoweringHandler = Callable[[ASTNode, Dict[str, int]], IRInstruction]
LOWERING_HANDLERS: Dict[type, LoweringHandler] = {}

def register_lowering(node_type: type) -> Callable[[LoweringHandler], LoweringHandler]:
    def decorator(func: LoweringHandler) -> LoweringHandler:
        LOWERING_HANDLERS[node_type] = func
        return func
    return decorator


class Lowerer:
    def __init__(self, program: ProgramNode):
        self.program = program
        self.label_map: Dict[str, int] = {}  # Maps label names to instruction indices (PC)
        self.line_to_instruction: Dict[int, int] = {}  # Maps source line numbers (1-based) to instruction indices (0-based)

    def lower(self) -> List[IRInstruction]:
        """Lowers a validated ProgramNode AST into concrete IR bytecode instructions."""
        self._pass1_collect_labels_and_lines()
        return self._pass2_resolve_jumps()

    def _pass1_collect_labels_and_lines(self) -> None:
        """First Pass: Determine instruction indices for labels and build line-to-instruction mapping."""
        instruction_idx = 0
        for stmt in self.program.statements:
            if isinstance(stmt, LabelNode):
                # The label points to the next non-label instruction's index
                self.label_map[stmt.name] = instruction_idx
            else:
                # Map source line number to instruction index
                source_line = stmt.span.start.line
                self.line_to_instruction[source_line] = instruction_idx
                instruction_idx += 1

    def _pass2_resolve_jumps(self) -> List[IRInstruction]:
        """Second Pass: Emit IR instructions, replacing label names with target indices."""
        ir_instructions: List[IRInstruction] = []
        for stmt in self.program.statements:
            if isinstance(stmt, LabelNode):
                # Skip label definitions during code emission
                continue
            
            stmt_type = type(stmt)
            handler = LOWERING_HANDLERS.get(stmt_type)
            if handler:
                inst = handler(stmt, self.label_map, self.line_to_instruction)
                inst = dataclasses.replace(inst, source_line=stmt.span.start.line)
                ir_instructions.append(inst)
            else:
                raise TypeError(f"No lowering handler registered for AST node type: {stmt_type.__name__}")
                
        return ir_instructions


# --- Register Lowering Handlers ---

@register_lowering(ReadNode)
def lower_read(node: ReadNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    return IRInstruction("read", node.register)

@register_lowering(StoreNode)
def lower_store(node: StoreNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    return IRInstruction("store", node.register)

@register_lowering(LoadNode)
def lower_load(node: LoadNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    return IRInstruction("load", node.value)

@register_lowering(AddNode)
def lower_add(node: AddNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    return IRInstruction("add", node.value)

@register_lowering(SubNode)
def lower_sub(node: SubNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    return IRInstruction("sub", node.value)

@register_lowering(JumpNode)
def lower_jump(node: JumpNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    try:
        # Try to parse as line number first; if it exists in the mapping, convert to instruction index
        target_line = int(node.target)
        if line_to_instruction and target_line in line_to_instruction:
            return IRInstruction("jump", line_to_instruction[target_line])
        # Otherwise, treat as instruction index (backward compatible)
        return IRInstruction("jump", target_line)
    except ValueError:
        # It's a label name
        return IRInstruction("jump", label_map[node.target])

@register_lowering(JposNode)
def lower_jpos(node: JposNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    try:
        target_line = int(node.target)
        if line_to_instruction and target_line in line_to_instruction:
            return IRInstruction("jpos", line_to_instruction[target_line])
        return IRInstruction("jpos", target_line)
    except ValueError:
        return IRInstruction("jpos", label_map[node.target])

@register_lowering(JnegNode)
def lower_jneg(node: JnegNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    try:
        target_line = int(node.target)
        if line_to_instruction and target_line in line_to_instruction:
            return IRInstruction("jneg", line_to_instruction[target_line])
        return IRInstruction("jneg", target_line)
    except ValueError:
        return IRInstruction("jneg", label_map[node.target])

@register_lowering(JzeroNode)
def lower_jzero(node: JzeroNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    try:
        target_line = int(node.target)
        if line_to_instruction and target_line in line_to_instruction:
            return IRInstruction("jzero", line_to_instruction[target_line])
        return IRInstruction("jzero", target_line)
    except ValueError:
        return IRInstruction("jzero", label_map[node.target])

@register_lowering(HaltNode)
def lower_halt(node: HaltNode, label_map: Dict[str, int], line_to_instruction: Dict[int, int] = None) -> IRInstruction:
    return IRInstruction("halt", None)
