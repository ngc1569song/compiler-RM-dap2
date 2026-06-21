class RegisterBank:
    def __init__(self, size: int = 32):
        if size <= 0:
            raise ValueError("Register bank size must be greater than zero.")
        self.size = size
        self.r0: int = 0
        self.registers: list[int] = [0] * size

    def read_r0(self) -> int:
        return self.r0

    def write_r0(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Accumulator register only holds signed integers.")
        self.r0 = value

    def read_register(self, index: int) -> int:
        self._validate_index(index)
        return self.registers[index]

    def write_register(self, index: int, value: int) -> None:
        self._validate_index(index)
        if not isinstance(value, int):
            raise TypeError("Registers only hold signed integers.")
        self.registers[index] = value

    def reset(self) -> None:
        self.r0 = 0
        self.registers = [0] * self.size

    def _validate_index(self, index: int) -> None:
        if not (0 <= index < self.size):
            raise IndexError(
                f"Register index r_{index} is out of bounds. "
                f"Valid indices: r_0 to r_{self.size - 1}."
            )

    def __repr__(self) -> str:
        # Format the first few registers, and summarize the rest if they're zero to keep display clean
        active_regs = [f"r{i}:{val}" for i, val in enumerate(self.registers) if val != 0]
        regs_str = ", ".join(active_regs) if active_regs else "all zero"
        return f"RegisterBank(r0={self.r0}, size={self.size}, active_registers=[{regs_str}])"
