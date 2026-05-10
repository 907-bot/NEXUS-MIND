"""
code_executor.py — MCP-style sandboxed Python code execution tool.

WARNING: Never execute untrusted code without a proper sandbox (e.g., Docker,
gVisor, Firecracker). This implementation uses subprocess with strict timeouts
and is safe only for development / trusted inputs.
"""
import asyncio
import sys
import tempfile
import os
from typing import Optional


async def execute_python(code: str, timeout: int = 10) -> dict:
    """
    Execute a Python snippet in a subprocess and return its output.

    Args:
        code: The Python source code to execute.
        timeout: Maximum execution time in seconds (default 10).

    Returns:
        dict with keys: stdout, stderr, exit_code, timed_out, success
    """
    # Write code to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            timed_out = False
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            stdout_b, stderr_b = b"", b"Execution timed out."
            timed_out = True

        return {
            "stdout": stdout_b.decode("utf-8", errors="replace"),
            "stderr": stderr_b.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode if not timed_out else -1,
            "timed_out": timed_out,
            "success": proc.returncode == 0 and not timed_out,
        }
    finally:
        os.unlink(tmp_path)


def validate_code_safety(code: str) -> tuple[bool, Optional[str]]:
    """
    Basic static check for obviously dangerous patterns.
    Returns (is_safe, reason_if_unsafe).
    """
    dangerous = [
        ("import subprocess", "subprocess usage"),
        ("os.system", "shell execution"),
        ("os.popen", "shell execution"),
        ("__import__", "dynamic import"),
        ("eval(", "eval usage"),
        ("exec(", "exec usage"),
        ("open(", "file I/O (potential)"),
        ("shutil.rmtree", "file deletion"),
    ]
    for pattern, reason in dangerous:
        if pattern in code:
            return False, f"Blocked: {reason} detected"
    return True, None
