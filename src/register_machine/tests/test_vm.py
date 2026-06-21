import unittest
from src.register_machine.compiler.diagnostics import DiagnosticReporter
from src.register_machine.compiler.lexer import Lexer
from src.register_machine.compiler.parser import Parser
from src.register_machine.compiler.lowering import Lowerer
from src.register_machine.vm.machine import VirtualMachine

class TestVirtualMachine(unittest.TestCase):
    def test_arithmetic_and_accumulator(self) -> None:
        source = """
        load 10
        add 5
        sub 3
        store 1
        halt
        """
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        instructions = Lowerer(program).lower()
        
        vm = VirtualMachine(instructions, max_registers=32)
        vm.run(max_cycles=10)
        
        self.assertTrue(vm.halted)
        # 10 + 5 - 3 = 12
        self.assertEqual(vm.registers.read_r0(), 12)
        self.assertEqual(vm.registers.read_register(1), 12)
        # Register 0 is still 0 (only accumulator is changed unless explicitly stored)
        self.assertEqual(vm.registers.read_register(0), 0)

    def test_countdown_loop(self) -> None:
        source = """
        load 5
        store 1
        loop:
            read 1
            sub 1
            store 1
            jpos loop
        halt
        """
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        instructions = Lowerer(program).lower()
        
        vm = VirtualMachine(instructions, max_registers=32)
        vm.run(max_cycles=100)
        
        self.assertTrue(vm.halted)
        self.assertEqual(vm.registers.read_register(1), 0)
        self.assertEqual(vm.registers.read_r0(), 0)
        self.assertEqual(vm.cycle_count, 23) # 2 setup + (4 per loop * 4 loops) + 1 final loop check (3 instructions) + 1 halt?
        # Let's count cycles:
        # Load 5 (1), store 1 (2).
        # Loop 1: read 1 (3), sub 1 (4), store 1 (5), jpos loop (6) -> r0=4
        # Loop 2: read 1 (7), sub 1 (8), store 1 (9), jpos loop (10) -> r0=3
        # Loop 3: read 1 (11), sub 1 (12), store 1 (13), jpos loop (14) -> r0=2
        # Loop 4: read 1 (15), sub 1 (16), store 1 (17), jpos loop (18) -> r0=1
        # Loop 5: read 1 (19), sub 1 (20), store 1 (21), jpos loop (22) -> r0=0. Since r0=0, no jump. PC advances.
        # Halt (23).
        # Actually it's ~22 cycles, which is fine and well within max_cycles=100.

    def test_conditional_jumps(self) -> None:
        # Test jneg and jzero
        source = """
        load -5
        jneg negative
        halt
        negative:
            load 0
            jzero zero
            halt
        zero:
            load 42
            halt
        """
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        instructions = Lowerer(program).lower()
        
        vm = VirtualMachine(instructions, max_registers=32)
        vm.run(max_cycles=20)
        
        self.assertTrue(vm.halted)
        self.assertEqual(vm.registers.read_r0(), 42)

    def test_runtime_register_error(self) -> None:
        # Program attempts to write to register 32, but max size is 32 (valid range 0..31)
        # Semantic analyzer checks register sizes, but let's test if VM *runtime* holds limits too!
        from compiler.ir import IRInstruction
        # Create invalid IR instruction directly bypass compiler semantic checks
        bad_instructions = [
            IRInstruction("store", 32), # out of bounds!
            IRInstruction("halt")
        ]
        
        vm = VirtualMachine(bad_instructions, max_registers=32)
        
        with self.assertRaises(IndexError):
            vm.step()

    def test_numeric_jumps(self) -> None:
        # load 10 (PC=0), jump 3 (PC=1), load 20 (PC=2), halt (PC=3)
        # Bypasses "load 20", leaving r0 at 10.
        source = "load 10\njump 3\nload 20\nhalt"
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        # Verify semantic analyzer passes
        from compiler.semantic import SemanticAnalyzer
        analyzer = SemanticAnalyzer(program, reporter)
        self.assertTrue(analyzer.analyze())
        
        instructions = Lowerer(program).lower()
        
        # Check lowered address
        self.assertEqual(instructions[1].op, "jump")
        self.assertEqual(instructions[1].arg, 3)
        
        vm = VirtualMachine(instructions, max_registers=32)
        vm.run(max_cycles=10)
        
        self.assertTrue(vm.halted)
        self.assertEqual(vm.registers.read_r0(), 10)

    def test_step_back(self) -> None:
        source = """
        load 42
        store 1
        add 10
        store 2
        """
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        instructions = Lowerer(program).lower()
        
        vm = VirtualMachine(instructions, max_registers=32)
        
        # Step 1: load 42
        vm.step()
        self.assertEqual(vm.registers.read_r0(), 42)
        self.assertEqual(vm.pc, 1)
        self.assertEqual(vm.cycle_count, 1)
        
        # Step 2: store 1
        vm.step()
        self.assertEqual(vm.registers.read_register(1), 42)
        self.assertEqual(vm.pc, 2)
        self.assertEqual(vm.cycle_count, 2)

        # Step 3: add 10
        vm.step()
        self.assertEqual(vm.registers.read_r0(), 52)
        self.assertEqual(vm.pc, 3)
        self.assertEqual(vm.cycle_count, 3)

        # Step back: undo add 10
        self.assertTrue(vm.step_back())
        self.assertEqual(vm.registers.read_r0(), 42)
        self.assertEqual(vm.pc, 2)
        self.assertEqual(vm.cycle_count, 2)

        # Step back: undo store 1
        self.assertTrue(vm.step_back())
        self.assertEqual(vm.registers.read_register(1), 0)
        self.assertEqual(vm.pc, 1)
        self.assertEqual(vm.cycle_count, 1)

        # Step back: undo load 42
        self.assertTrue(vm.step_back())
        self.assertEqual(vm.registers.read_r0(), 0)
        self.assertEqual(vm.pc, 0)
        self.assertEqual(vm.cycle_count, 0)

        # No more steps to back up
        self.assertFalse(vm.step_back())

if __name__ == "__main__":
    unittest.main()
