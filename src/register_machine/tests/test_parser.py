import unittest
from src.register_machine.compiler.diagnostics import DiagnosticReporter
from src.register_machine.compiler.lexer import Lexer
from src.register_machine.compiler.parser import Parser
from src.register_machine.compiler.ast_nodes import (
    ProgramNode, LabelNode, LoadNode, StoreNode, ReadNode, SubNode, AddNode,
    JumpNode, JposNode, HaltNode
)

class TestParser(unittest.TestCase):
    def test_parse_valid_program(self) -> None:
        source = """
        start:
            load 10
            store 2
            sub 1
            jpos start
            halt
        """
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens, reporter)
        program = parser.parse()
        
        self.assertFalse(reporter.has_errors)
        self.assertIsInstance(program, ProgramNode)
        
        stmts = program.statements
        self.assertEqual(len(stmts), 6)
        
        self.assertIsInstance(stmts[0], LabelNode)
        self.assertEqual(stmts[0].name, "start")
        
        self.assertIsInstance(stmts[1], LoadNode)
        self.assertEqual(stmts[1].value, 10)
        
        self.assertIsInstance(stmts[2], StoreNode)
        self.assertEqual(stmts[2].register, 2)
        
        self.assertIsInstance(stmts[3], SubNode)
        self.assertEqual(stmts[3].value, 1)
        
        self.assertIsInstance(stmts[4], JposNode)
        self.assertEqual(stmts[4].target, "start")
        
        self.assertIsInstance(stmts[5], HaltNode)

    def test_loose_labels_and_comments(self) -> None:
        source = "loop : ; space before colon\n    read 1"
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens, reporter)
        program = parser.parse()
        
        self.assertFalse(reporter.has_errors)
        self.assertEqual(len(program.statements), 2)
        self.assertIsInstance(program.statements[0], LabelNode)
        self.assertEqual(program.statements[0].name, "loop")
        self.assertIsInstance(program.statements[1], ReadNode)
        self.assertEqual(program.statements[1].register, 1)

    def test_parse_syntax_error_and_synchronize(self) -> None:
        # line 2 has syntax error (missing immediate), line 3 should still parse correctly!
        source = "load 5\nadd\nstore 1"
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens, reporter)
        program = parser.parse()
        
        self.assertTrue(reporter.has_errors)
        # Verify that synchronization allowed us to parse statement 3
        # Statement 1 (load 5) and Statement 3 (store 1) should be in AST
        self.assertEqual(len(program.statements), 2)
        self.assertIsInstance(program.statements[0], LoadNode)
        self.assertIsInstance(program.statements[1], StoreNode)
        
        # Verify correct error message on line 2
        self.assertEqual(len(reporter.diagnostics), 1)
        self.assertEqual(reporter.diagnostics[0].span.start.line, 2)
        self.assertIn("Expected integer value for 'add'", reporter.diagnostics[0].message)

if __name__ == "__main__":
    unittest.main()
