"""
yaml_validator.py — MCP-style YAML validation tool.

Used by DevOpsAgent to verify that generated configuration files
(Dockerfiles, docker-compose, GitHub Actions CI YAML, render.yaml, etc.)
are syntactically valid before including them in the final deliverable.
"""
import yaml
from typing import Any


async def validate_yaml(content: str) -> dict:
    """
    Parse and validate a YAML string.

    Args:
        content: YAML text to validate.

    Returns:
        dict with keys: valid (bool), parsed (the parsed object or None),
                        error (str or None), line (int or None)
    """
    if not content or not content.strip():
        return {
            "valid": False,
            "parsed": None,
            "error": "Empty content — nothing to validate.",
            "line": None,
        }

    try:
        parsed: Any = yaml.safe_load(content)
        return {
            "valid": True,
            "parsed": parsed,
            "error": None,
            "line": None,
        }
    except yaml.YAMLError as exc:
        # Extract line number if available
        line = None
        if hasattr(exc, "problem_mark") and exc.problem_mark:
            line = exc.problem_mark.line + 1  # 1-indexed
        return {
            "valid": False,
            "parsed": None,
            "error": str(exc),
            "line": line,
        }


async def validate_yaml_multi(content: str) -> dict:
    """
    Validate a YAML file that may contain multiple documents (--- separators).
    Returns a list of parsed documents.
    """
    try:
        docs = list(yaml.safe_load_all(content))
        return {"valid": True, "documents": docs, "count": len(docs), "error": None}
    except yaml.YAMLError as exc:
        return {"valid": False, "documents": [], "count": 0, "error": str(exc)}
