import json
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class IRInstruction:
    op: str              # e.g., "read", "store", "load", "add", "sub", "jump", "jpos", "jneg", "jzero", "halt"
    arg: Optional[int] = None  # Holds the integer register index, immediate value, or resolved target PC.
    source_line: Optional[int] = None  # Tracks original 1-based source code line for visualizer/debugging.

    def __repr__(self) -> str:
        if self.arg is not None:
            return f"{self.op} {self.arg}"
        return self.op

def serialize_ir(instructions: List[IRInstruction]) -> str:
    """Serializes a list of IR instructions into a readable JSON string bytecode."""
    bytecode_list = []
    for inst in instructions:
        bytecode_list.append({
            "op": inst.op,
            "arg": inst.arg,
            "sourceLine": inst.source_line
        })
    return json.dumps(bytecode_list, indent=2)

def deserialize_ir(json_str: str) -> List[IRInstruction]:
    """Deserializes a JSON bytecode string back into a list of IR instructions."""
    bytecode_list = json.loads(json_str)
    instructions = []
    for item in bytecode_list:
        instructions.append(IRInstruction(
            op=item["op"],
            arg=item.get("arg"),
            source_line=item.get("sourceLine")
        ))
    return instructions
