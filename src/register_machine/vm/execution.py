from typing import List, Optional
from src.register_machine.compiler.ir import IRInstruction
from src.register_machine.vm.machine import VirtualMachine

def execute_program(
    instructions: List[IRInstruction],
    trace: bool = False,
    max_registers: int = 32,
    max_cycles: Optional[int] = None
) -> VirtualMachine:
    """Convenience helper to initialize a Virtual Machine and execute a program."""
    vm = VirtualMachine(instructions, max_registers=max_registers)
    vm.run(trace=trace, max_cycles=max_cycles)
    return vm
