from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

class DiagnosticSeverity(Enum):
    ERROR = auto()
    WARNING = auto()
    NOTE = auto()

@dataclass(frozen=True)
class Location:
    line: int      # 1-based
    column: int    # 1-based

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"

@dataclass(frozen=True)
class Span:
    start: Location
    end: Location

    @classmethod
    def single_point(cls, line: int, column: int) -> 'Span':
        loc = Location(line, column)
        return cls(loc, loc)

@dataclass
class Diagnostic:
    message: str
    severity: DiagnosticSeverity
    span: Span
    file_path: Optional[str] = None
    hint: Optional[str] = None

class DiagnosticReporter:
    def __init__(self, source_code: str, file_path: Optional[str] = None):
        self.source_code = source_code
        self.file_path = file_path or "<source>"
        self.source_lines = source_code.splitlines()
        self.diagnostics: List[Diagnostic] = []

    def report(self, diagnostic: Diagnostic) -> None:
        if diagnostic.file_path is None:
            diagnostic.file_path = self.file_path
        self.diagnostics.append(diagnostic)

    def error(self, message: str, span: Span, hint: Optional[str] = None) -> None:
        self.report(Diagnostic(message, DiagnosticSeverity.ERROR, span, self.file_path, hint))

    def warning(self, message: str, span: Span, hint: Optional[str] = None) -> None:
        self.report(Diagnostic(message, DiagnosticSeverity.WARNING, span, self.file_path, hint))

    def note(self, message: str, span: Span, hint: Optional[str] = None) -> None:
        self.report(Diagnostic(message, DiagnosticSeverity.NOTE, span, self.file_path, hint))

    @property
    def has_errors(self) -> bool:
        return any(d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics)

    def format_diagnostic(self, diag: Diagnostic) -> str:
        severity_str = {
            DiagnosticSeverity.ERROR: "error",
            DiagnosticSeverity.WARNING: "warning",
            DiagnosticSeverity.NOTE: "note"
        }[diag.severity]

        # ANSI color codes for premium visuals (can fall back gracefully)
        color_prefix = ""
        color_suffix = ""
        if diag.severity == DiagnosticSeverity.ERROR:
            color_prefix = "\033[91m\033[1m" # bold red
            color_suffix = "\033[0m"
        elif diag.severity == DiagnosticSeverity.WARNING:
            color_prefix = "\033[93m\033[1m" # bold yellow
            color_suffix = "\033[0m"
        elif diag.severity == DiagnosticSeverity.NOTE:
            color_prefix = "\033[96m\033[1m" # bold cyan
            color_suffix = "\033[0m"

        header = f"{color_prefix}{severity_str}{color_suffix}: {diag.message}\n"
        loc_info = f"  --> {diag.file_path}:{diag.span.start.line}:{diag.span.start.column}\n"
        
        body = ""
        start_line = diag.span.start.line
        end_line = diag.span.end.line
        
        # Display the source context if within range
        if 1 <= start_line <= len(self.source_lines):
            line_idx = start_line - 1
            line_text = self.source_lines[line_idx]
            
            # Format single-line span highlight
            if start_line == end_line:
                col_start = diag.span.start.column - 1
                col_end = diag.span.end.column - 1
                length = max(1, col_end - col_start + 1)
                
                # Align prefix spacing with line number width
                line_num_str = f"{start_line}"
                padding = " " * len(line_num_str)
                
                body += f"{padding} |\n"
                body += f"{line_num_str} | {line_text}\n"
                underline = " " * col_start + "^" * length
                body += f"{padding} | {color_prefix}{underline}{color_suffix}\n"
            else:
                # Multiline span
                line_num_str = f"{start_line}"
                padding = " " * len(line_num_str)
                body += f"{padding} |\n"
                for idx in range(start_line - 1, min(end_line, len(self.source_lines))):
                    body += f"{idx + 1} | {self.source_lines[idx]}\n"
                body += f"{padding} |\n"

        if diag.hint:
            # Align hint padding
            padding = " " * len(f"{start_line}")
            body += f"{padding} = hint: {diag.hint}\n"

        return header + loc_info + body

    def format_diagnostics(self) -> str:
        return "".join(self.format_diagnostic(diag) for diag in self.diagnostics)

    def print_diagnostics(self) -> None:
        print(self.format_diagnostics(), end="")
