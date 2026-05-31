from __future__ import annotations

from pathlib import Path

from sct.core.errors import StaleLineError
from sct.core.markers import parse_line
from sct.core.models import Status, TodoItem
from sct.core.scanner import line_hash


def read_line(path: Path, line_number: int) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise StaleLineError(f"Cannot read {path}: {e}") from e
    lines = text.splitlines()
    if line_number < 1 or line_number > len(lines):
        raise StaleLineError(
            f"Line {line_number} out of range in {path} (file has {len(lines)} lines). "
            "Run `sct sync` after editing."
        )
    return lines[line_number - 1]


def verify_line_unchanged(item: TodoItem, root: Path) -> str:
    """Return current line text or raise StaleLineError."""
    path = root / item.file
    line = read_line(path, item.line)
    current_hash = line_hash(line)
    if item.line_hash and current_hash != item.line_hash:
        raise StaleLineError(
            f"Line changed since last sync ({item.file}:{item.line}). "
            "Run `sct sync` and try again."
        )
    parsed = parse_line(line)
    if not parsed:
        raise StaleLineError(
            f"No TODO/DONE marker on {item.file}:{item.line}. "
            "Run `sct sync`."
        )
    _prefix, marker, task, _ = parsed
    if task.strip() != item.task.strip():
        raise StaleLineError(
            f"Task text changed on {item.file}:{item.line}. "
            "Run `sct sync`."
        )
    if marker != item.marker:
        raise StaleLineError(
            f"Marker is '{marker}', expected '{item.marker}'. Run `sct sync`."
        )
    expected_status = item.status
    from sct.core.markers import status_from_marker

    if status_from_marker(marker) != expected_status:
        raise StaleLineError(
            f"Status mismatch on {item.file}:{item.line}. Run `sct sync`."
        )
    return line
