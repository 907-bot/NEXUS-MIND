"""
file_writer.py — MCP-style in-memory file writer tool.

Agents use this to stage generated files in the session's shared memory,
so the AssemblerAgent can collect them into the final deliverable.
"""
import json
import re
from pathlib import PurePosixPath
from typing import Optional
from app.core.memory_store import memory_store


# Allowlist of file extensions agents are permitted to write
ALLOWED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml",
    ".md", ".txt", ".html", ".css", ".sql", ".sh", ".dockerfile",
    ".toml", ".cfg", ".ini", ".env",
}


def _sanitize_filename(filename: str) -> Optional[str]:
    """
    Reject filenames with path traversal or disallowed extensions.
    Returns the cleaned filename, or None if rejected.
    """
    # Normalise separators and collapse traversal attempts
    clean = PurePosixPath(filename)
    parts = clean.parts

    # Block absolute paths and traversal
    if any(p in ("..", "/", "\\") for p in parts):
        return None

    ext = clean.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS and ext != "":
        return None  # Unknown extension blocked

    return str(clean)


async def write_file(session_id: str, filename: str, content: str) -> dict:
    """
    Stage a generated file in the session's shared memory.

    Args:
        session_id: Active session identifier.
        filename:   Relative path/filename (e.g. "api/routes/orders.py").
        content:    Full file content as a string.

    Returns:
        dict with keys: success, filename, size_bytes, error (if any)
    """
    safe_name = _sanitize_filename(filename)
    if not safe_name:
        return {
            "success": False,
            "filename": filename,
            "size_bytes": 0,
            "error": "Filename rejected: path traversal or disallowed extension.",
        }

    key = f"file:{safe_name}"
    record = {"filename": safe_name, "content": content, "size_bytes": len(content.encode())}
    await memory_store.set(session_id, key, record)

    return {"success": True, "filename": safe_name, "size_bytes": len(content.encode())}


async def list_files(session_id: str) -> list[dict]:
    """Return metadata for all staged files in the session (without content)."""
    all_memory = await memory_store.get_all(session_id)
    files = []
    for key, value in all_memory.items():
        if key.startswith("file:"):
            files.append({
                "filename": value.get("filename"),
                "size_bytes": value.get("size_bytes", 0),
            })
    return files


async def get_file(session_id: str, filename: str) -> Optional[dict]:
    """Retrieve a staged file by name."""
    safe_name = _sanitize_filename(filename)
    if not safe_name:
        return None
    return await memory_store.get(session_id, f"file:{safe_name}")
