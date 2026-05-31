from __future__ import annotations

from pathlib import Path

from sct.core.markers import done_marker, open_marker, parse_line, replace_marker_on_line
from sct.core.models import Status, TodoItem


def _write_lines_atomically(path: Path, lines: list[str]) -> None:
    tmp = path.with_suffix(path.suffix + ".sct.tmp")
    content = "".join(lines)
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def patch_line(path: Path, line_number: int, new_marker: str) -> str:
    """Replace marker on given 1-based line. Returns new line text."""
    text = path.read_text(encoding="utf-8")
    file_lines = text.splitlines(keepends=True)
    if not file_lines and line_number == 1:
        file_lines = [""]
    if line_number < 1 or line_number > len(file_lines):
        raise ValueError(f"Line {line_number} out of range in {path}")

    idx = line_number - 1
    old = file_lines[idx]
    new = replace_marker_on_line(old, new_marker)
    file_lines[idx] = new
    _write_lines_atomically(path, file_lines)
    return new.rstrip("\n\r")


def mark_done(item: TodoItem, root: Path) -> TodoItem:
    path = root / item.file
    new_marker = done_marker(item.priority)
    new_line = patch_line(path, item.line, new_marker)
    parsed = parse_line(new_line)
    if not parsed:
        raise ValueError("Patched line could not be parsed")
    from sct.core.scanner import line_hash

    item.marker = new_marker
    item.status = Status.DONE
    item.line_hash = line_hash(new_line)
    return item


def mark_open(item: TodoItem, root: Path) -> TodoItem:
    path = root / item.file
    new_marker = open_marker(item.priority)
    new_line = patch_line(path, item.line, new_marker)
    parsed = parse_line(new_line)
    if not parsed:
        raise ValueError("Patched line could not be parsed")
    from sct.core.scanner import line_hash

    item.marker = new_marker
    item.status = Status.OPEN
    item.line_hash = line_hash(new_line)
    return item
