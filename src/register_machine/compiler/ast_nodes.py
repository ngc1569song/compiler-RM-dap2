from dataclasses import dataclass
from typing import List, Union
from register_machine.compiler.diagnostics import Span

@dataclass
class ASTNode:
    span: Span

@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]

@dataclass
class LabelNode(ASTNode):
    name: str

@dataclass
class ReadNode(ASTNode):
    register: int

@dataclass
class StoreNode(ASTNode):
    register: int

@dataclass
class LoadNode(ASTNode):
    value: int

@dataclass
class AddNode(ASTNode):
    value: int

@dataclass
class SubNode(ASTNode):
    value: int

@dataclass
class JumpNode(ASTNode):
    target: str

@dataclass
class JposNode(ASTNode):
    target: str

@dataclass
class JnegNode(ASTNode):
    target: str

@dataclass
class JzeroNode(ASTNode):
    target: str

@dataclass
class HaltNode(ASTNode):
    pass

# A type union for all individual instruction/label nodes in a program
StatementNode = Union[
    LabelNode, ReadNode, StoreNode, LoadNode, AddNode, SubNode,
    JumpNode, JposNode, JnegNode, JzeroNode, HaltNode
]
