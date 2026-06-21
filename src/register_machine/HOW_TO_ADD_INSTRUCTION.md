# How to Add a New Instruction to the Register Machine

This guide explains how to extend our modular compiler + VM pipeline with a new instruction. As an example, we will add a multiplication instruction `mul x` which multiplies the accumulator by immediate integer value `x` (i.e. `r0 := r0 * x`).

---

## Step 1: Lexer (Keywords Update)
In [compiler/lexer.py](./compiler/lexer.py), add your instruction keyword to the set of recognized instructions in `tokenize()`.

```python
# Locate in compiler/lexer.py
keywords = {"read", "store", "load", "add", "sub", "jump", "jpos", "jneg", "jzero", "halt", "mul"}
```

---

## Step 2: Define AST Node
In [compiler/ast_nodes.py](./compiler/ast_nodes.py), add a strongly typed AST node.

```python
# Add to compiler/ast_nodes.py
@dataclass
class MulNode(ASTNode):
    value: int
```

Include it in `StatementNode` type union for clean type hinting.

---

## Step 3: Register Parser Handler
In [compiler/parser.py](./compiler/parser.py), write and register a parser handler using the `@register_instruction` decorator.

```python
# Add to compiler/parser.py
@register_instruction("mul")
def parse_mul(parser: Parser, token: Token) -> ASTNode:
    # Expect a single integer operand
    op = parser.expect(TokenType.INTEGER, "Expected integer value for 'mul'")
    return MulNode(value=int(op.value), span=Span(token.span.start, op.span.end))
```

---

## Step 4: Define Semantic Rules
In [compiler/semantic.py](./compiler/semantic.py), add validation checks for your new AST node in `_validate_statements()`.

```python
# Add to compiler/semantic.py -> _validate_statements()
elif isinstance(stmt, MulNode):
    val = stmt.value
    min_val = -2147483648
    max_val = 2147483647
    if val < min_val or val > max_val:
        self.reporter.error(
            f"Immediate operand '{val}' out of 32-bit signed integer range for 'mul'",
            stmt.span,
            hint=f"Literal value must be between {min_val} and {max_val} inclusive."
        )
```

---

## Step 5: Define Lowering Rule
In [compiler/lowering.py](./compiler/lowering.py), register a lowering handler to translate the AST node into a flattened `IRInstruction`.

```python
# Add to compiler/lowering.py
@register_lowering(MulNode)
def lower_mul(node: MulNode, label_map: Dict[str, int]) -> IRInstruction:
    # Emit an IR instruction with the opcode "mul" and its immediate argument
    return IRInstruction("mul", node.value)
```

---

## Step 6: Define VM Execution Rule
In [vm/instruction_set.py](./vm/instruction_set.py), write the execution handler for the virtual machine and register it in `DISPATCH_TABLE`.

```python
# Add to vm/instruction_set.py
def execute_mul(vm: Any, arg: int) -> None:
    """r0 := r0 * x"""
    val = vm.registers.read_r0()
    vm.registers.write_r0(val * arg)
    vm.pc += 1

# Register in DISPATCH_TABLE
DISPATCH_TABLE["mul"] = execute_mul
```

---

## Step 7: Update the Frontend JavaScript VM
If you want your instruction to work in the Web UI visualizer, you must add it to the JavaScript Virtual Machine in `frontend/main.js`.

```javascript
# Locate VirtualMachine.step() in frontend/main.js
# Add your case to the switch statement
case 'mul':
    this.r0 *= arg;
    this.pc++;
    break;
```

---

## Step 8: Verification
Your pipeline is fully extended! To verify:
1. Write a test program using `mul 5` in a file.
2. Run it via the CLI:
   ```bash
   python cli.py run my_program.rm --trace
   ```
3. Add a dedicated unit test in `tests/` covering parsing, lowering, and execution.
4. Try compiling and running it in the Web IDE!
