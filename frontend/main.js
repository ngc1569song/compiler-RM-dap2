// ============================================================================
// REGISTER MACHINE COMPILER CLIENT + VM FRONT-END IMPLEMENTATION
// ============================================================================

// --- Virtual Machine ---

class VirtualMachine {
    constructor(instructions, maxRegisters = 32) {
        this.instructions = instructions;
        this.maxRegisters = maxRegisters;
        this.r0 = 0;
        this.registers = new Array(maxRegisters).fill(0);
        this.pc = 0;
        this.halted = false;
        this.cycles = 0;
        this.history = [];
        
        // Tracing changes for highlight effects
        this.lastRegRead = null;
        this.lastRegWritten = null;
    }

    reset() {
        this.r0 = 0;
        this.registers.fill(0);
        this.pc = 0;
        this.halted = false;
        this.cycles = 0;
        this.history = [];
        this.lastRegRead = null;
        this.lastRegWritten = null;
    }

    step() {
        if (this.halted) return;
        
        // Capture snapshot before execution for step-back history
        const snapshot = {
            r0: this.r0,
            registers: [...this.registers],
            pc: this.pc,
            halted: this.halted,
            cycles: this.cycles,
            lastRegRead: this.lastRegRead,
            lastRegWritten: this.lastRegWritten
        };
        this.history.push(snapshot);

        this.lastRegRead = null;
        this.lastRegWritten = null;

        if (this.pc < 0 || this.pc >= this.instructions.length) {
            this.halted = true;
            throw new Error(`PC index ${this.pc} is out of bounds! Ensure program halts cleanly.`);
        }

        const inst = this.instructions[this.pc];
        const arg = inst.arg;

        switch (inst.op) {
            case 'read':
                this.lastRegRead = arg;
                this.r0 = this.registers[arg];
                this.pc++;
                break;
            case 'store':
                this.lastRegWritten = arg;
                this.registers[arg] = this.r0;
                this.pc++;
                break;
            case 'load':
                this.r0 = arg;
                this.pc++;
                break;
            case 'add':
                this.r0 += arg;
                this.pc++;
                break;
            case 'sub':
                this.r0 -= arg;
                this.pc++;
                break;
            case 'jump':
                this.pc = arg;
                break;
            case 'jpos':
                if (this.r0 > 0) this.pc = arg;
                else this.pc++;
                break;
            case 'jneg':
                if (this.r0 < 0) this.pc = arg;
                else this.pc++;
                break;
            case 'jzero':
                if (this.r0 === 0) this.pc = arg;
                else this.pc++;
                break;
            case 'halt':
                this.halted = true;
                break;
            default:
                throw new Error(`Runtime error: Unknown IR instruction operation '${inst.op}'`);
        }

        this.cycles++;
    }

    stepBack() {
        if (this.history.length === 0) return false;
        
        const snapshot = this.history.pop();
        this.r0 = snapshot.r0;
        this.registers = snapshot.registers;
        this.pc = snapshot.pc;
        this.halted = snapshot.halted;
        this.cycles = snapshot.cycles;
        this.lastRegRead = snapshot.lastRegRead;
        this.lastRegWritten = snapshot.lastRegWritten;
        return true;
    }
}

// ============================================================================
// BROWSER UI INTEGRATION
// ============================================================================

// Sample Assembly Codes
const EXAMPLES = {
    countdown: `# Countdown Loop
# Counts down from 5 to 1, updating register 1.

load 5
store 1

loop:
    read 1
    sub 1
    store 1
    jpos loop   # Jump to 'loop' if r0 > 0

halt`,

    multiply: `# Multiply Example (Repeated Add)
# Multiplies variable count by a constant (3).
# Computes n * 3. Here n = 4.

load 4
store 1       # r1 = counter = 4
load 0
store 2       # r2 = result = 0

loop:
    read 1
    jzero done  # Exit if counter reaches 0
    sub 1
    store 1     # Decrement counter

    read 2
    add 3       # Add constant (3) to result
    store 2
    jump loop   # Repeat

done:
    halt`,

    sum: `# Sum 1 to 5 nested loop
# Calculates 5 + 4 + 3 + 2 + 1 = 15.
# Counter in r1, sum in r2, temp in r3.

load 5
store 1
load 0
store 2

outer_loop:
    read 1
    jzero done        # Finish if counter r1 is 0
    store 3           # r3 = r1 (copy counter)
    
add_loop:
    read 3
    jzero add_done    # finished adding r1
    sub 1
    store 3           # Decrement temporary r3
    
    read 2
    add 1             # Increment sum r2 by 1
    store 2
    jump add_loop

add_done:
    read 1
    sub 1             # Decrement counter r1
    store 1
    jump outer_loop

done:
    halt`,

    error: `# Syntax & Semantic Errors Showcase
# Click 'Assemble Code' to view compilation diagnostics.

loop:
    load 100
    store 35       # SEMANTIC ERROR: Register out of bounds (max 32)!
    add 5000000000 # SEMANTIC ERROR: Value literal exceeds 32-bit range!
    
    jzero loop_typ # SEMANTIC ERROR: Undefined label loop_typ!
    
    sub            # SYNTAX ERROR: Missing integer literal operand!
    
    jump 50        # SEMANTIC ERROR: Numeric PC target exceeds instruction count!`
};

// UI Elements References
const elEditor = document.getElementById('code-editor');
const elLineNumbers = document.getElementById('line-numbers');
const elExampleSelect = document.getElementById('example-select');
const elTerminal = document.getElementById('terminal-body');

const elBtnAssemble = document.getElementById('btn-assemble');
const elBtnStep = document.getElementById('btn-step');
const elBtnStepBack = document.getElementById('btn-step-back');
const elBtnRun = document.getElementById('btn-run');
const elBtnPause = document.getElementById('btn-pause');
const elBtnReset = document.getElementById('btn-reset');
const elBtnClearTerm = document.getElementById('btn-clear-term');

const elValR0 = document.getElementById('val-r0');
const elValPC = document.getElementById('val-pc');
const elValCycles = document.getElementById('val-cycles');
const elValState = document.getElementById('val-state');
const elRegGrid = document.getElementById('registers-grid');
const elRegCount = document.getElementById('reg-count-input');

// Application State Variables
let activeInstructions = [];
let vmInstance = null;
let runInterval = null;
let maxRegisters = 32;

// Add highlight overlay layer to editor container
const elHighlightLine = document.createElement('div');
elHighlightLine.className = 'active-line-highlight';
elHighlightLine.style.top = '-100px';
document.querySelector('.editor-container').appendChild(elHighlightLine);

// Initialize Line Numbers
function updateLineNumbers() {
    const lines = elEditor.value.split('\n').length;
    let numsHTML = '';
    for (let i = 1; i <= lines; i++) {
        numsHTML += `<div id="line-num-${i}">${i}</div>`;
    }
    elLineNumbers.innerHTML = numsHTML;
}

// Log message inside system terminal
function logTerminal(message, type = 'system-msg') {
    const div = document.createElement('div');
    div.className = `terminal-line ${type}`;
    div.textContent = message;
    elTerminal.appendChild(div);
    elTerminal.scrollTop = elTerminal.scrollHeight;
}

// Render dynamic memory cell tiles in Registers grid
// Using subscript r_i labels to avoid accumulator/register 0 naming collision!
function renderRegistersGrid() {
    elRegGrid.innerHTML = '';
    for (let i = 0; i < maxRegisters; i++) {
        const val = vmInstance ? vmInstance.registers[i] : 0;
        
        const cell = document.createElement('div');
        cell.className = 'memory-cell';
        cell.id = `reg-cell-${i}`;
        cell.innerHTML = `
            <span class="reg-lbl">r_${i}</span>
            <span class="reg-val" id="reg-val-${i}">${val}</span>
        `;
        elRegGrid.appendChild(cell);
    }
}

// Synchronize VM state and registers data values to UI components
function updateVMUI() {
    if (!vmInstance) return;

    elValR0.textContent = vmInstance.r0;
    elValPC.textContent = vmInstance.pc;
    elValCycles.textContent = vmInstance.cycles;

    // Synchronize register values
    for (let i = 0; i < maxRegisters; i++) {
        const valSpan = document.getElementById(`reg-val-${i}`);
        const cell = document.getElementById(`reg-cell-${i}`);
        if (valSpan) {
            valSpan.textContent = vmInstance.registers[i];
        }
        
        // Handle read flash glow hit
        if (vmInstance.lastRegRead === i && cell) {
            cell.classList.remove('read-hit', 'write-hit');
            void cell.offsetWidth; // Trigger reflow for animation restart
            cell.classList.add('read-hit');
        }
        
        // Handle write flash glow hit
        if (vmInstance.lastRegWritten === i && cell) {
            cell.classList.remove('read-hit', 'write-hit');
            void cell.offsetWidth; // Trigger reflow for animation restart
            cell.classList.add('write-hit');
        }
    }

    // Highlight source code line execution PC sync
    highlightExecutionPC();
}

// Sync execution program-counter directly to highlighting line numbers/editor line
function highlightExecutionPC() {
    // Reset active line numbers
    document.querySelectorAll('.line-numbers div').forEach(el => el.classList.remove('active-line-num'));
    elHighlightLine.style.top = '-100px';

    if (!vmInstance || vmInstance.halted || vmInstance.pc >= activeInstructions.length) {
        return;
    }

    const inst = activeInstructions[vmInstance.pc];
    if (inst && inst.sourceLine) {
        const lineNumEl = document.getElementById(`line-num-${inst.sourceLine}`);
        if (lineNumEl) {
            lineNumEl.classList.add('active-line-num');
            
            // Calculate absolute top position in pixels of target line
            const editorPadding = 19.2; // 1.2rem
            const lineHeight = 21.6;    // line-height multiplier height
            const topPos = editorPadding + (inst.sourceLine - 1) * lineHeight;
            
            elHighlightLine.style.top = `${topPos}px`;
            elHighlightLine.style.height = `${lineHeight}px`;
        }
    }
}

// Update State Badge Indicators
function updateVMStateBadge(state) {
    elValState.className = 'value badge';
    if (state === 'RESET') {
        elValState.classList.add('state-reset');
        elValState.textContent = 'RESET';
    } else if (state === 'READY') {
        elValState.classList.add('state-ready');
        elValState.textContent = 'READY';
    } else if (state === 'RUNNING') {
        elValState.classList.add('state-running');
        elValState.textContent = 'RUNNING';
    } else if (state === 'HALTED') {
        elValState.classList.add('state-halted');
        elValState.textContent = 'HALTED';
    }
}

// Core Compiler Assembler Invocation (decoupled backend server fetch)
async function compile() {
    const source = elEditor.value;
    maxRegisters = parseInt(elRegCount.value, 10) || 32;
    
    logTerminal("--- Starting Backend Compilation ---", "info-msg");
    elBtnAssemble.disabled = true;
    
    try {
        const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/assemble`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source: source,
                maxRegisters: maxRegisters
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            // Log formatted compiler errors from backend directly to terminal
            logTerminal(data.errors || "Compilation failed with unknown error.", "error-msg");
            logTerminal("Compilation failed! Backend returned diagnostic errors.", "error-msg");
            elBtnAssemble.disabled = false;
            return false;
        }

        activeInstructions = data.instructions;
        
        logTerminal(`Assembly compilation successful! Generated ${activeInstructions.length} instructions.`, "success-msg");
        
        // Build and display line-to-instruction mapping for user clarity
        const lineToInstruction = {};
        const lines = source.split('\n');
        let instructionIdx = 0;
        for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
            const line = lines[lineIdx].trim();
            const lineNum = lineIdx + 1; // 1-based line numbers for display
            
            // Skip empty lines, comments, and lines that are only labels
            const isComment = line.startsWith('#') || line.startsWith(';');
            const isLabel = line.endsWith(':') && !line.includes(' ');
            const isEmpty = line === '';
            
            if (!isEmpty && !isComment && !isLabel) {
                lineToInstruction[lineNum] = instructionIdx;
                instructionIdx++;
            }
        }
        
        // Display mapping helper
        logTerminal("📌 Jump Target Guide: Use source LINE numbers from the editor (left), they auto-map to instruction indices.", "system-msg");
        logTerminal(`   Example: 'jump 5' jumps to the first instruction on or after line 5.`, "system-msg");
        
        // Setup VM
        vmInstance = new VirtualMachine(activeInstructions, maxRegisters);
        renderRegistersGrid();
        updateVMUI();
        updateVMStateBadge('READY');
        
        elBtnStep.disabled = false;
        elBtnStepBack.disabled = true;
        elBtnRun.disabled = false;
        elBtnAssemble.disabled = false;
        
        return true;
    } catch (err) {
        logTerminal(`Unexpected Compiler/Connection Crash: ${err.message}`, "error-msg");
        console.error(err);
        elBtnAssemble.disabled = false;
        return false;
    }
}

// Step single cycle execution
function executeStep() {
    if (!vmInstance || vmInstance.halted) return;

    try {
        const nextPC = vmInstance.pc;
        const inst = activeInstructions[nextPC];
        
        vmInstance.step();
        
        logTerminal(`PC:${nextPC.toString().padStart(2, '0')} | Executed: ${inst.op} ${inst.arg !== null ? inst.arg : ''}`, "info-msg");
        updateVMUI();

        // Enable step back button since we now have step history
        elBtnStepBack.disabled = false;

        if (vmInstance.halted) {
            logTerminal("Execution Completed. Program Halted cleanly.", "success-msg");
            updateVMStateBadge('HALTED');
            stopRunner();
        }
    } catch (err) {
        logTerminal(`Runtime Crash: ${err.message}`, "error-msg");
        updateVMStateBadge('HALTED');
        stopRunner();
    }
}

// Step backward single cycle execution
function executeStepBack() {
    if (!vmInstance) return;

    const prevPC = vmInstance.pc;
    const success = vmInstance.stepBack();
    if (success) {
        const currentPC = vmInstance.pc;
        const inst = activeInstructions[currentPC];
        logTerminal(`Step Back | Undid PC:${prevPC.toString().padStart(2, '0')}. Restored state at PC:${currentPC.toString().padStart(2, '0')} (${inst.op} ${inst.arg !== null ? inst.arg : ''})`, "warning-msg");
        
        // If we stepped back, program is no longer halted
        if (!vmInstance.halted && elValState.textContent === 'HALTED') {
            updateVMStateBadge('READY');
        }
        
        updateVMUI();

        if (vmInstance.history.length === 0) {
            elBtnStepBack.disabled = true;
        }
    } else {
        logTerminal("Already at the beginning of program history. Cannot step back further.", "warning-msg");
        elBtnStepBack.disabled = true;
    }
}

// Continuous VM execution runner loop
function startRunner() {
    if (!vmInstance || vmInstance.halted) return;
    
    updateVMStateBadge('RUNNING');
    elBtnRun.disabled = true;
    elBtnPause.disabled = false;
    elBtnStep.disabled = true;
    elBtnStepBack.disabled = true;
    
    runInterval = setInterval(() => {
        if (vmInstance && !vmInstance.halted) {
            executeStep();
        } else {
            stopRunner();
        }
    }, 100); // 100ms step delays for clean step animation tracking
}

// Stop execution runner
function stopRunner() {
    if (runInterval) {
        clearInterval(runInterval);
        runInterval = null;
    }
    elBtnPause.disabled = true;
    if (vmInstance && !vmInstance.halted) {
        elBtnRun.disabled = false;
        elBtnStep.disabled = false;
        if (vmInstance.history.length > 0) {
            elBtnStepBack.disabled = false;
        }
        updateVMStateBadge('READY');
    }
}

// Reset VM state
function resetVM() {
    stopRunner();
    if (vmInstance) {
        vmInstance.reset();
        updateVMUI();
        updateVMStateBadge('READY');
        elBtnStepBack.disabled = true;
        logTerminal("Virtual Machine state reset. Program counter reset to 0.", "system-msg");
    } else {
        renderRegistersGrid();
        updateVMStateBadge('RESET');
    }
}

// Load preloaded example programs
function loadExample(exampleName) {
    stopRunner();
    const code = EXAMPLES[exampleName];
    if (code) {
        elEditor.value = code;
        updateLineNumbers();
        resetVM();
        
        // Reset instructions and buttons
        activeInstructions = [];
        vmInstance = null;
        elBtnStep.disabled = true;
        elBtnStepBack.disabled = true;
        elBtnRun.disabled = true;
        
        logTerminal(`Loaded pre-set example: '${exampleName}'. Click 'Assemble Code' to load it.`, "system-msg");
    }
}

// --- Event Listeners Bindings ---

elEditor.addEventListener('input', () => {
    updateLineNumbers();
    stopRunner();
    
    // Invalidate compiler state if editor changes
    vmInstance = null;
    activeInstructions = [];
    elBtnStep.disabled = true;
    elBtnStepBack.disabled = true;
    elBtnRun.disabled = true;
    updateVMStateBadge('RESET');
});

// Horizontal scrolling synchronization
elEditor.addEventListener('scroll', () => {
    elLineNumbers.scrollTop = elEditor.scrollTop;
});

elExampleSelect.addEventListener('change', (e) => {
    loadExample(e.target.value);
});

elBtnAssemble.addEventListener('click', async () => {
    stopRunner();
    await compile();
});

elBtnStep.addEventListener('click', () => {
    executeStep();
});

elBtnStepBack.addEventListener('click', () => {
    stopRunner();
    executeStepBack();
});

elBtnRun.addEventListener('click', () => {
    startRunner();
});

elBtnPause.addEventListener('click', () => {
    stopRunner();
});

elBtnReset.addEventListener('click', () => {
    resetVM();
});

elBtnClearTerm.addEventListener('click', () => {
    elTerminal.innerHTML = '';
});

elRegCount.addEventListener('change', () => {
    maxRegisters = parseInt(elRegCount.value, 10) || 32;
    resetVM();
});

// App Initialization entry
window.addEventListener('DOMContentLoaded', () => {
    loadExample('sum');
});
