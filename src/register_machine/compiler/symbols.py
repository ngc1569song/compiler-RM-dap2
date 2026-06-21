from dataclasses import dataclass
from typing import Dict, Optional
from register_machine.compiler.diagnostics import Span

@dataclass
class Symbol:
    name: str
    symbol_type: str  # e.g., "label"
    span: Span

class SymbolTable:
    def __init__(self) -> None:
        self.symbols: Dict[str, Symbol] = {}

    def insert(self, name: str, symbol_type: str, span: Span) -> bool:
        """Inserts a symbol. Returns False if duplicate exists."""
        if name in self.symbols:
            return False
        self.symbols[name] = Symbol(name, symbol_type, span)
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def exists(self, name: str) -> bool:
        return name in self.symbols
