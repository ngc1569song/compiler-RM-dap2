import unittest
from src.register_machine.compiler.diagnostics import DiagnosticReporter
from src.register_machine.compiler.lexer import Lexer
from src.register_machine.compiler.parser import Parser
from src.register_machine.compiler.lowering import Lowerer
from src.register_machine.compiler.ir import serialize_ir, deserialize_ir

class TestLowerer(unittest.TestCase):
    def test_lower_label_resolutions(self) -> None:
        source = """
        start:
            load 5
            jpos start
            halt
        """
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        lowerer = Lowerer(program)
        instructions = lowerer.lower()
        
        # We expect exactly 3 IR instructions:
        # 0: load 5
        # 1: jpos 0  (start was defined at instruction index 0)
        # 2: halt
        self.assertEqual(len(instructions), 3)
        
        self.assertEqual(instructions[0].op, "load")
        self.assertEqual(instructions[0].arg, 5)
        
        self.assertEqual(instructions[1].op, "jpos")
        self.assertEqual(instructions[1].arg, 0)
        
        self.assertEqual(instructions[2].op, "halt")
        self.assertIsNone(instructions[2].arg)

    def test_serialization_roundtrip(self) -> None:
        source = """
        load 10
        store 1
        sub 2
        jneg 0
        halt
        """
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        lowerer = Lowerer(program)
        instructions = lowerer.lower()
        
        # Serialize to JSON
        json_bytecode = serialize_ir(instructions)
        self.assertIsInstance(json_bytecode, str)
        self.assertIn("load", json_bytecode)
        
        # Deserialize back and check roundtrip equality
        roundtripped = deserialize_ir(json_bytecode)
        self.assertEqual(len(roundtripped), len(instructions))
        
        for i in range(len(instructions)):
            self.assertEqual(roundtripped[i].op, instructions[i].op)
            self.assertEqual(roundtripped[i].arg, instructions[i].arg)

if __name__ == "__main__":
    unittest.main()
