import unittest
from src.register_machine.compiler.diagnostics import DiagnosticReporter
from src.register_machine.compiler.lexer import Lexer
from src.register_machine.compiler.parser import Parser
from src.register_machine.compiler.semantic import SemanticAnalyzer

class TestSemanticAnalyzer(unittest.TestCase):
    def test_valid_program(self) -> None:
        source = "loop:\n    load 100\n    store 31\n    jzero loop\n    halt"
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        analyzer = SemanticAnalyzer(program, reporter, max_registers=32)
        success = analyzer.analyze()
        
        self.assertTrue(success)
        self.assertFalse(reporter.has_errors)

    def test_duplicate_labels(self) -> None:
        source = "loop:\n    load 5\nloop:\n    halt"
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        analyzer = SemanticAnalyzer(program, reporter)
        success = analyzer.analyze()
        
        self.assertFalse(success)
        self.assertTrue(reporter.has_errors)
        self.assertEqual(len(reporter.diagnostics), 1)
        self.assertIn("Duplicate label definition: 'loop'", reporter.diagnostics[0].message)

    def test_undefined_jump_target(self) -> None:
        source = "load 5\njump non_existent"
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        analyzer = SemanticAnalyzer(program, reporter)
        success = analyzer.analyze()
        
        self.assertFalse(success)
        self.assertTrue(reporter.has_errors)
        self.assertEqual(len(reporter.diagnostics), 1)
        self.assertIn("Undefined jump target label: 'non_existent'", reporter.diagnostics[0].message)

    def test_register_index_out_of_bounds(self) -> None:
        # Default max registers = 32 (indices 0 to 31). Index 32 is invalid!
        source = "read 32\nstore -1"
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        # Parse allows any integer, let's see if semantic analyzer flags it.
        # Wait, since parsing 'store -1' parses as StoreNode(-1), that's fine.
        analyzer = SemanticAnalyzer(program, reporter, max_registers=32)
        success = analyzer.analyze()
        
        self.assertFalse(success)
        self.assertTrue(reporter.has_errors)
        # We expect 2 errors (register 32 exceeds, and register -1 is negative/out of bounds)
        self.assertEqual(len(reporter.diagnostics), 2)
        self.assertIn("Register index 32 is out of bounds", reporter.diagnostics[0].message)
        self.assertIn("Register index -1 is out of bounds", reporter.diagnostics[1].message)

    def test_integer_literal_out_of_bounds(self) -> None:
        # Limits: -2147483648 to 2147483647
        source = "load 2147483648\nadd -2147483649"
        reporter = DiagnosticReporter(source)
        tokens = Lexer(source, reporter).tokenize()
        program = Parser(tokens, reporter).parse()
        
        analyzer = SemanticAnalyzer(program, reporter)
        success = analyzer.analyze()
        
        self.assertFalse(success)
        self.assertTrue(reporter.has_errors)
        self.assertEqual(len(reporter.diagnostics), 2)
        self.assertIn("Immediate operand '2147483648' out of 32-bit signed integer range", reporter.diagnostics[0].message)
        self.assertIn("Immediate operand '-2147483649' out of 32-bit signed integer range", reporter.diagnostics[1].message)

if __name__ == "__main__":
    unittest.main()
