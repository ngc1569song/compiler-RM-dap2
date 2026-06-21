import unittest
from register_machine.compiler.diagnostics import DiagnosticReporter
from register_machine.compiler.lexer import Lexer
from register_machine.compiler.tokens import TokenType

class TestLexer(unittest.TestCase):
    def test_basic_instructions(self) -> None:
        source = "load 5\nstore 1"
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        self.assertFalse(reporter.has_errors)
        # Expected: load (inst), 5 (int), newline, store (inst), 1 (int), EOF
        self.assertEqual(len(tokens), 6)
        
        self.assertEqual(tokens[0].type, TokenType.INSTRUCTION)
        self.assertEqual(tokens[0].value, "load")
        self.assertEqual(tokens[0].span.start.line, 1)
        self.assertEqual(tokens[0].span.start.column, 1)

        self.assertEqual(tokens[1].type, TokenType.INTEGER)
        self.assertEqual(tokens[1].value, "5")

        self.assertEqual(tokens[2].type, TokenType.NEWLINE)

        self.assertEqual(tokens[3].type, TokenType.INSTRUCTION)
        self.assertEqual(tokens[3].value, "store")

        self.assertEqual(tokens[4].type, TokenType.INTEGER)
        self.assertEqual(tokens[4].value, "1")

        self.assertEqual(tokens[5].type, TokenType.EOF)

    def test_labels_and_comments(self) -> None:
        source = "start:\n    add -2 ; minus two\n    halt"
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        self.assertFalse(reporter.has_errors)
        
        # Filter out comments and newlines for easier assertion of instruction structure
        code_tokens = [t for t in tokens if t.type not in (TokenType.COMMENT, TokenType.NEWLINE, TokenType.EOF)]
        
        self.assertEqual(len(code_tokens), 4)
        
        # start:
        self.assertEqual(code_tokens[0].type, TokenType.LABEL)
        self.assertEqual(code_tokens[0].value, "start")
        
        # add
        self.assertEqual(code_tokens[1].type, TokenType.INSTRUCTION)
        self.assertEqual(code_tokens[1].value, "add")
        
        # -2
        self.assertEqual(code_tokens[2].type, TokenType.INTEGER)
        self.assertEqual(code_tokens[2].value, "-2")
        
        # halt
        self.assertEqual(code_tokens[3].type, TokenType.INSTRUCTION)
        self.assertEqual(code_tokens[3].value, "halt")

    def test_lexical_errors(self) -> None:
        source = "load @\nsub 1"
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        self.assertTrue(reporter.has_errors)
        self.assertEqual(len(reporter.diagnostics), 1)
        self.assertIn("Unrecognized character: '@'", reporter.diagnostics[0].message)
        self.assertEqual(reporter.diagnostics[0].span.start.line, 1)
        self.assertEqual(reporter.diagnostics[0].span.start.column, 6)

    def test_format_diagnostics(self) -> None:
        source = "load @\nsub 1"
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter)
        tokens = lexer.tokenize()
        
        self.assertTrue(reporter.has_errors)
        formatted = reporter.format_diagnostics()
        self.assertIn("Unrecognized character: '@'", formatted)
        self.assertIn("--> <source>:1:6", formatted)
        self.assertIn("1 | load @", formatted)

if __name__ == "__main__":
    unittest.main()
