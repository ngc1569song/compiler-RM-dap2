from typing import List
from register_machine.compiler.diagnostics import DiagnosticReporter, Location, Span
from register_machine.compiler.tokens import Token, TokenType

class Lexer:
    def __init__(self, source_code: str, reporter: DiagnosticReporter):
        self.source = source_code
        self.reporter = reporter
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(source_code)

    def peek(self) -> str:
        if self.pos >= self.length:
            return ""
        return self.source[self.pos]

    def peek_next(self) -> str:
        if self.pos + 1 >= self.length:
            return ""
        return self.source[self.pos + 1]

    def advance(self) -> str:
        if self.pos >= self.length:
            return ""
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char

    def skip_whitespace(self) -> None:
        # We only skip horizontal whitespace (spaces and tabs).
        # Newlines are treated as tokens to separate instructions.
        while self.peek() in (' ', '\t'):
            self.advance()

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break

            start_line = self.line
            start_col = self.col
            char = self.peek()

            # Handle newlines
            if char in ('\r', '\n'):
                # Match CRLF
                if char == '\r' and self.peek_next() == '\n':
                    self.advance()  # Consume \r
                newline_char = self.advance()  # Consume \n or lone \r
                span = Span(Location(start_line, start_col), Location(start_line, start_col))
                tokens.append(Token(TokenType.NEWLINE, newline_char, span))
                continue

            # Handle comments
            if char in (';', '#'):
                comment_val = ""
                while self.pos < self.length and self.peek() not in ('\r', '\n'):
                    comment_val += self.advance()
                span = Span(Location(start_line, start_col), Location(self.line, max(1, self.col - 1)))
                tokens.append(Token(TokenType.COMMENT, comment_val, span))
                continue

            # Handle standard colons
            if char == ':':
                self.advance()
                span = Span(Location(start_line, start_col), Location(start_line, start_col))
                tokens.append(Token(TokenType.COLON, ":", span))
                continue

            # Handle integers with signs
            if char in ('+', '-') and self.peek_next().isdigit():
                val = self.advance()  # Consume sign
                while self.peek().isdigit():
                    val += self.advance()
                span = Span(Location(start_line, start_col), Location(self.line, max(1, self.col - 1)))
                tokens.append(Token(TokenType.INTEGER, val, span))
                continue

            # Handle positive integers
            if char.isdigit():
                val = ""
                while self.peek().isdigit():
                    val += self.advance()
                span = Span(Location(start_line, start_col), Location(self.line, max(1, self.col - 1)))
                tokens.append(Token(TokenType.INTEGER, val, span))
                continue

            # Handle instructions, identifiers, and labels
            if char.isalpha() or char == '_':
                val = ""
                while self.peek().isalnum() or self.peek() == '_':
                    val += self.advance()

                # If followed immediately by a colon, it's a label definition (e.g. "loop:")
                if self.peek() == ':':
                    self.advance()  # Consume the colon
                    span = Span(Location(start_line, start_col), Location(self.line, max(1, self.col - 1)))
                    # Value is just the label identifier name
                    tokens.append(Token(TokenType.LABEL, val, span))
                else:
                    span = Span(Location(start_line, start_col), Location(self.line, max(1, self.col - 1)))
                    # Check if instruction keyword
                    keywords = {"read", "store", "load", "add", "sub", "jump", "jpos", "jneg", "jzero", "halt"}
                    if val.lower() in keywords:
                        tokens.append(Token(TokenType.INSTRUCTION, val.lower(), span))
                    else:
                        tokens.append(Token(TokenType.IDENTIFIER, val, span))
                continue

            # Unrecognized character error
            err_char = self.advance()
            span = Span(Location(start_line, start_col), Location(start_line, start_col))
            self.reporter.error(f"Unrecognized character: {repr(err_char)}", span, hint="Ensure valid ISA character")

        # Emit EOF
        eof_span = Span(Location(self.line, self.col), Location(self.line, self.col))
        tokens.append(Token(TokenType.EOF, "", eof_span))
        return tokens
