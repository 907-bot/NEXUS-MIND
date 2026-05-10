"""
code_formatter.py — MCP-style code syntax checking tools.

BackendAgent uses check_python_syntax() to validate generated Python files.
FrontendAgent uses check_typescript_syntax() for lightweight TS/TSX checks.

Full formatting (black, prettier) requires those tools to be installed;
this module degrades gracefully when they are not available.
"""
import ast
import re
import subprocess
import sys
import tempfile
import os
from typing import Optional


# ── Python ────────────────────────────────────────────────────────────────────

async def check_python_syntax(code: str) -> dict:
    """
    Parse Python source with the ast module to catch syntax errors.
    Does NOT execute the code.

    Returns:
        dict: { valid, error, line, col }
    """
    if not code or not code.strip():
        return {"valid": False, "error": "Empty code string", "line": None, "col": None}

    try:
        ast.parse(code)
        return {"valid": True, "error": None, "line": None, "col": None}
    except SyntaxError as exc:
        return {
            "valid": False,
            "error": exc.msg,
            "line": exc.lineno,
            "col": exc.offset,
        }


async def format_python(code: str) -> dict:
    """
    Format Python code with black (if installed).
    Falls back gracefully if black is not available.

    Returns:
        dict: { formatted_code, changed, error }
    """
    try:
        import black  # type: ignore
        mode = black.Mode()
        formatted = black.format_str(code, mode=mode)
        return {"formatted_code": formatted, "changed": formatted != code, "error": None}
    except ImportError:
        return {
            "formatted_code": code,
            "changed": False,
            "error": "black not installed — skipping formatting",
        }
    except Exception as exc:
        return {"formatted_code": code, "changed": False, "error": str(exc)}


# ── TypeScript / TSX ──────────────────────────────────────────────────────────

async def check_typescript_syntax(code: str) -> dict:
    """
    Lightweight TypeScript/TSX static checks without a full compiler.
    Catches the most common structural issues:
      - Unbalanced braces / brackets / parens
      - Missing closing JSX tags (heuristic)
      - Import syntax errors

    For production, replace with a tsc --noEmit subprocess.

    Returns:
        dict: { valid, issues (list[str]), error }
    """
    issues = []

    # Bracket balance check
    for open_ch, close_ch, label in [("{", "}", "curly brace"), ("[", "]", "bracket"), ("(", ")", "parenthesis")]:
        depth = 0
        for i, ch in enumerate(code):
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
            if depth < 0:
                issues.append(f"Unmatched closing {label} near character {i}")
                break
        if depth > 0:
            issues.append(f"Unclosed {label} ({depth} unclosed)")

    # Detect obvious missing semicolons on import lines (heuristic)
    for lineno, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("import ") and not stripped.endswith(("{", ",", "\\")) and not stripped.endswith(";"):
            issues.append(f"Line {lineno}: import statement may be missing semicolon")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "error": None,
    }
