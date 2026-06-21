from typing import Dict, Any, Callable

# An instruction handler takes the virtual machine instance and the instruction argument.
InstructionHandler = Callable[[Any, Any], None]

def execute_read(vm: Any, arg: int) -> None:
    """r0 := r_j"""
    val = vm.registers.read_register(arg)
    vm.registers.write_r0(val)
    vm.pc += 1

def execute_store(vm: Any, arg: int) -> None:
    """r_j := r0"""
    val = vm.registers.read_r0()
    vm.registers.write_register(arg, val)
    vm.pc += 1

def execute_load(vm: Any, arg: int) -> None:
    """r0 := x"""
    vm.registers.write_r0(arg)
    vm.pc += 1

def execute_add(vm: Any, arg: int) -> None:
    """r0 := r0 + x"""
    val = vm.registers.read_r0()
    vm.registers.write_r0(val + arg)
    vm.pc += 1

def execute_sub(vm: Any, arg: int) -> None:
    """r0 := r0 - x"""
    val = vm.registers.read_r0()
    vm.registers.write_r0(val - arg)
    vm.pc += 1

def execute_jump(vm: Any, arg: int) -> None:
    """PC := target_pc"""
    vm.pc = arg

def execute_jpos(vm: Any, arg: int) -> None:
    """if r0 > 0: PC := target_pc else PC := PC + 1"""
    if vm.registers.read_r0() > 0:
        vm.pc = arg
    else:
        vm.pc += 1

def execute_jneg(vm: Any, arg: int) -> None:
    """if r0 < 0: PC := target_pc else PC := PC + 1"""
    if vm.registers.read_r0() < 0:
        vm.pc = arg
    else:
        vm.pc += 1

def execute_jzero(vm: Any, arg: int) -> None:
    """if r0 == 0: PC := target_pc else PC := PC + 1"""
    if vm.registers.read_r0() == 0:
        vm.pc = arg
    else:
        vm.pc += 1

def execute_halt(vm: Any, arg: Any) -> None:
    """Stop execution"""
    vm.halted = True


DISPATCH_TABLE: Dict[str, InstructionHandler] = {
    "read": execute_read,
    "store": execute_store,
    "load": execute_load,
    "add": execute_add,
    "sub": execute_sub,
    "jump": execute_jump,
    "jpos": execute_jpos,
    "jneg": execute_jneg,
    "jzero": execute_jzero,
    "halt": execute_halt,
}
