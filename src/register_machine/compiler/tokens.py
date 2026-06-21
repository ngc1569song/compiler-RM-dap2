from enum import Enum, auto
from dataclasses import dataclass
from register_machine.compiler.diagnostics import Span

class TokenType(Enum):
    IDENTIFIER = auto()
    INSTRUCTION = auto()
    INTEGER = auto()
    LABEL = auto()       # e.g., "start:" or just "start" if identified as label
    COLON = auto()       # ":"
    NEWLINE = auto()     # "\n"
    COMMENT = auto()     # "; comment" or "# comment"
    EOF = auto()

@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    span: Span

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, {self.span.start.line}:{self.span.start.column})"
