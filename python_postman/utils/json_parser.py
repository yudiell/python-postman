"""
JSON parsing utilities with error handling.
"""

import json
from typing import Dict, Any, Union
from pathlib import Path
from ..exceptions import CollectionParseError, CollectionFileError


def parse_json_safely(json_content: str) -> Dict[str, Any]:
    """
    Safely parse JSON content with proper error handling.

    Args:
        json_content: JSON string to parse

    Returns:
        Parsed JSON as dictionary

    Raises:
        CollectionParseError: If JSON parsing fails
    """
    if not isinstance(json_content, str):
        raise CollectionParseError(
            f"Expected string input, got {type(json_content).__name__}",
            details={"input_type": type(json_content).__name__},
        )

    if not json_content.strip():
        raise CollectionParseError(
            "Empty or whitespace-only JSON content provided",
            details={"content_length": len(json_content)},
        )

    try:
        parsed_data = json.loads(json_content)

        # Ensure we get a dictionary (collections should be objects, not arrays)
        if not isinstance(parsed_data, dict):
            raise CollectionParseError(
                f"Expected JSON object, got {type(parsed_data).__name__}",
                details={"parsed_type": type(parsed_data).__name__},
            )

        return parsed_data

    except json.JSONDecodeError as e:
        # Provide more context about the error location
        lines = json_content.split("\n")
        error_line = lines[e.lineno - 1] if e.lineno <= len(lines) else ""

        raise CollectionParseError(
            f"Failed to parse JSON content at line {e.lineno}, column {e.colno}: {e.msg}",
            details={
                "line": e.lineno,
                "column": e.colno,
                "position": e.pos,
                "error_message": e.msg,
                "error_line": error_line.strip() if error_line else "",
                "context": _get_error_context(json_content, e.pos),
            },
        ) from e


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a JSON file with comprehensive error handling.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON as dictionary

    Raises:
        CollectionFileError: If file operations fail
        CollectionParseError: If JSON parsing fails
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise CollectionFileError(
            f"File not found: {file_path}",
            details={"file_path": str(file_path), "exists": False},
        )

    if not file_path.is_file():
        raise CollectionFileError(
            f"Path is not a file: {file_path}",
            details={"file_path": str(file_path), "is_file": False},
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return parse_json_safely(content)

    except UnicodeDecodeError as e:
        raise CollectionFileError(
            f"Failed to decode file as UTF-8: {e}",
            details={"file_path": str(file_path), "encoding_error": str(e)},
        ) from e
    except IOError as e:
        raise CollectionFileError(
            f"Failed to read file: {e}",
            details={"file_path": str(file_path), "io_error": str(e)},
        ) from e


def _get_error_context(
    json_content: str, error_pos: int, context_chars: int = 50
) -> str:
    """
    Get context around the error position for better debugging.

    Args:
        json_content: The original JSON content
        error_pos: Position where the error occurred
        context_chars: Number of characters to show before and after error

    Returns:
        Context string showing the area around the error
    """
    if error_pos < 0 or error_pos >= len(json_content):
        return ""

    start = max(0, error_pos - context_chars)
    end = min(len(json_content), error_pos + context_chars)

    context = json_content[start:end]
    marker_pos = error_pos - start

    # Add a marker to show exactly where the error occurred
    if 0 <= marker_pos < len(context):
        context = context[:marker_pos] + "<<<ERROR>>>" + context[marker_pos:]

    return context
