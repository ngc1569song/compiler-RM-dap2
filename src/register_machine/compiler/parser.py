from typing import List, Dict, Callable, Optional
from register_machine.compiler.diagnostics import DiagnosticReporter, Span
from register_machine.compiler.tokens import Token, TokenType
from register_machine.compiler.ast_nodes import (
    ASTNode, ProgramNode, LabelNode, ReadNode, StoreNode, LoadNode,
    AddNode, SubNode, JumpNode, JposNode, JnegNode, JzeroNode, HaltNode
)

# Registry to map instruction names to their specific parser handlers.
# This makes it easy to add new instructions without modifying parser core.
InstructionHandler = Callable[['Parser', Token], ASTNode]
INSTRUCTION_HANDLERS: Dict[str, InstructionHandler] = {}

def register_instruction(name: str) -> Callable[[InstructionHandler], InstructionHandler]:
    def decorator(func: InstructionHandler) -> InstructionHandler:
        INSTRUCTION_HANDLERS[name.lower()] = func
        return func
    return decorator

class Parser:
    def __init__(self, tokens: List[Token], reporter: DiagnosticReporter):
        self.tokens = tokens
        self.reporter = reporter
        self.cursor = 0

    def peek(self) -> Token:
        if self.cursor >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.cursor]

    def peek_next(self) -> Token:
        if self.cursor + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.cursor + 1]

    def advance(self) -> Token:
        tok = self.peek()
        if tok.type != TokenType.EOF:
            self.cursor += 1
        return tok

    def check(self, expected_type: TokenType) -> bool:
        return self.peek().type == expected_type

    def match(self, expected_type: TokenType) -> bool:
        if self.check(expected_type):
            self.advance()
            return True
        return False

    def expect(self, expected_type: TokenType, error_message: str) -> Token:
        tok = self.peek()
        if tok.type == expected_type:
            return self.advance()
        self.reporter.error(error_message, tok.span)
        raise SyntaxError(error_message)

    def expect_jump_target(self, error_message: str) -> Token:
        tok = self.peek()
        if tok.type in (TokenType.IDENTIFIER, TokenType.INSTRUCTION, TokenType.INTEGER):
            return self.advance()
        self.reporter.error(error_message, tok.span)
        raise SyntaxError(error_message)

    def synchronize(self) -> None:
        # Advance until we find a newline or EOF, then skip the newline to try parsing next line.
        while not self.check(TokenType.EOF):
            if self.check(TokenType.NEWLINE):
                self.advance()
                return
            self.advance()

    def parse(self) -> ProgramNode:
        statements: List[ASTNode] = []
        start_span = self.peek().span

        while not self.check(TokenType.EOF):
            # Consume leading newlines, blank lines, or comments
            if self.match(TokenType.NEWLINE) or self.match(TokenType.COMMENT):
                continue

            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)

                # Expect newline, comment, or EOF after a statement
                if not self.check(TokenType.EOF):
                    if self.check(TokenType.COMMENT):
                        self.advance()  # Consume inline comment
                    elif not self.match(TokenType.NEWLINE):
                        tok = self.peek()
                        self.reporter.error(
                            "Expected newline or end of file after statement",
                            tok.span,
                            hint="Instructions must be separated by a newline."
                        )
                        raise SyntaxError("Expected newline")
            except SyntaxError:
                self.synchronize()

        end_span = self.peek().span
        return ProgramNode(statements=statements, span=Span(start_span.start, end_span.end))

    def parse_statement(self) -> Optional[ASTNode]:
        tok = self.peek()

        # Direct label definition from lexer (e.g. "loop:")
        if tok.type == TokenType.LABEL:
            self.advance()
            return LabelNode(name=tok.value, span=tok.span)

        # Standard instruction execution
        if tok.type == TokenType.INSTRUCTION:
            inst_token = self.advance()
            handler = INSTRUCTION_HANDLERS.get(inst_token.value.lower())
            if handler:
                return handler(self, inst_token)
            else:
                self.reporter.error(f"Unknown instruction registered: {inst_token.value}", inst_token.span)
                raise SyntaxError(f"Unknown instruction: {inst_token.value}")

        # Loose label definition (e.g. "loop :") or typo instruction
        if tok.type == TokenType.IDENTIFIER:
            id_token = self.advance()
            if self.match(TokenType.COLON):
                span = Span(id_token.span.start, self.tokens[self.cursor - 1].span.end)
                return LabelNode(name=id_token.value, span=span)
            
            # Syntax error for typo instructions
            self.reporter.error(
                f"Expected instruction keyword, found identifier '{id_token.value}'",
                id_token.span,
                hint=f"Is '{id_token.value}' a typo? If defining a label, write '{id_token.value}:'"
            )
            raise SyntaxError("Expected instruction")

        # Unexpected token type
        self.reporter.error(f"Unexpected token: '{tok.value or tok.type.name}'", tok.span)
        self.advance()
        raise SyntaxError("Unexpected token")


# --- Register Instruction Handlers ---

@register_instruction("read")
def parse_read(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect(TokenType.INTEGER, "Expected integer register index for 'read'")
    return ReadNode(register=int(op.value), span=Span(token.span.start, op.span.end))

@register_instruction("store")
def parse_store(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect(TokenType.INTEGER, "Expected integer register index for 'store'")
    return StoreNode(register=int(op.value), span=Span(token.span.start, op.span.end))

@register_instruction("load")
def parse_load(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect(TokenType.INTEGER, "Expected integer value for 'load'")
    return LoadNode(value=int(op.value), span=Span(token.span.start, op.span.end))

@register_instruction("add")
def parse_add(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect(TokenType.INTEGER, "Expected integer value for 'add'")
    return AddNode(value=int(op.value), span=Span(token.span.start, op.span.end))

@register_instruction("sub")
def parse_sub(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect(TokenType.INTEGER, "Expected integer value for 'sub'")
    return SubNode(value=int(op.value), span=Span(token.span.start, op.span.end))

@register_instruction("jump")
def parse_jump(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect_jump_target("Expected target label or numeric PC for 'jump'")
    return JumpNode(target=op.value, span=Span(token.span.start, op.span.end))

@register_instruction("jpos")
def parse_jpos(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect_jump_target("Expected target label or numeric PC for 'jpos'")
    return JposNode(target=op.value, span=Span(token.span.start, op.span.end))

@register_instruction("jneg")
def parse_jneg(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect_jump_target("Expected target label or numeric PC for 'jneg'")
    return JnegNode(target=op.value, span=Span(token.span.start, op.span.end))

@register_instruction("jzero")
def parse_jzero(parser: Parser, token: Token) -> ASTNode:
    op = parser.expect_jump_target("Expected target label or numeric PC for 'jzero'")
    return JzeroNode(target=op.value, span=Span(token.span.start, op.span.end))

@register_instruction("halt")
def parse_halt(parser: Parser, token: Token) -> ASTNode:
    return HaltNode(span=token.span)
