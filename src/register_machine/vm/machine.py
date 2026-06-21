import sys
from typing import List, Optional
from src.register_machine.compiler.ir import IRInstruction
from src.register_machine.vm.registers import RegisterBank
from src.register_machine.vm.instruction_set import DISPATCH_TABLE

class VirtualMachine:
    def __init__(self, instructions: List[IRInstruction], max_registers: int = 32):
        self.instructions = instructions
        self.registers = RegisterBank(max_registers)
        self.pc = 0
        self.halted = False
        self.cycle_count = 0
        self.history: List[dict] = []

    def step(self) -> None:
        """Executes a single IR instruction and updates the VM state."""
        if self.halted:
            return

        if not (0 <= self.pc < len(self.instructions)):
            self.halted = True
            raise RuntimeError(
                f"Virtual Machine error: Program Counter PC={self.pc} is out of bounds. "
                "The program did not terminate with a 'halt' instruction."
            )

        inst = self.instructions[self.pc]
        handler = DISPATCH_TABLE.get(inst.op.lower())
        
        if not handler:
            self.halted = True
            raise RuntimeError(f"Virtual Machine error: Unknown opcode '{inst.op}' at PC={self.pc}")

        # Capture snapshot before execution for step-back history
        snapshot = {
            "pc": self.pc,
            "r0": self.registers.read_r0(),
            "registers": list(self.registers.registers),
            "halted": self.halted,
            "cycle_count": self.cycle_count
        }
        self.history.append(snapshot)

        # Execute instruction (PC is updated inside the instruction handler)
        handler(self, inst.arg)
        self.cycle_count += 1

    def step_back(self) -> bool:
        """Restores the VM to the previous step in history, returning True if successful."""
        if not self.history:
            return False
        
        snapshot = self.history.pop()
        self.pc = snapshot["pc"]
        self.registers.write_r0(snapshot["r0"])
        self.registers.registers = list(snapshot["registers"])
        self.halted = snapshot["halted"]
        self.cycle_count = snapshot["cycle_count"]
        return True

    def run(self, trace: bool = False, max_cycles: Optional[int] = None) -> None:
        """Runs the program until halt, bounds error, or keyboard interrupt."""
        if trace:
            print("\033[94m\033[1m=== Starting VM Execution Trace ===\033[0m")
            self.dump_state()
            print("-" * 50)

        try:
            while not self.halted:
                if max_cycles is not None and self.cycle_count >= max_cycles:
                    print(f"\n\033[93mWarning: Execution reached maximum cycle limit of {max_cycles}.\033[0m")
                    break

                if trace:
                    next_inst = self.instructions[self.pc] if 0 <= self.pc < len(self.instructions) else "EOF"
                    print(f"Step {self.cycle_count:04d} | PC: {self.pc:03d} | Current Instruction: \033[92m{next_inst}\033[0m")

                self.step()

                if trace:
                    self.dump_state()
                    print("-" * 50)

            if not trace:
                # If not tracing, dump final state at the very end
                print("\033[92mExecution completed successfully.\033[0m")
                self.dump_state()

        except KeyboardInterrupt:
            print("\n\033[91m\033[1mExecution interrupted by user!\033[0m")
            print(f"Interrupted at PC: {self.pc} after {self.cycle_count} cycles.")
            self.dump_state()
        except Exception as e:
            print(f"\n\033[91m\033[1mRuntime Execution Error:\033[0m {str(e)}")
            self.dump_state()
            raise

    def dump_state(self) -> None:
        """Prints the CPU state: PC, accumulator r0, and all non-zero registers."""
        print(f"  PC: {self.pc:<3} | r0: {self.registers.read_r0():<6} | Cycles: {self.cycle_count}")
        active_registers = []
        for idx in range(self.registers.size):
            val = self.registers.read_register(idx)
            if val != 0:
                active_registers.append(f"r{idx}: {val}")
        
        if active_registers:
            print(f"  Registers: {', '.join(active_registers)}")
        else:
            print("  Registers: All zero")
