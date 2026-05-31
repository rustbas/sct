from __future__ import annotations

import re

from sct.core.models import Status

LINE_RE = re.compile(
    r"^(?P<prefix>.*?)(?<![\w.])(?P<marker>TOD[O]{1,3}|DON[E]{1,3}):\s*(?P<task>.*?)\s*$"
)

MARKER_OPEN_RE = re.compile(r"^TOD[O]{1,3}$")
MARKER_DONE_RE = re.compile(r"^DON[E]{1,3}$")


def priority_from_marker(marker: str) -> int:
    if marker.startswith("TOD"):
        return len(marker) - len("TOD")
    if marker.startswith("DON"):
        return len(marker) - len("DON")
    return 1


def open_marker(priority: int) -> str:
    priority = max(1, min(3, priority))
    return "TOD" + "O" * priority


def done_marker(priority: int) -> str:
    priority = max(1, min(3, priority))
    return "DON" + "E" * priority


def status_from_marker(marker: str) -> Status:
    return Status.from_marker(marker)


def parse_line(line: str) -> tuple[str, str, str, str] | None:
    """Return (prefix, marker, task, full_line_unchanged) or None."""
    m = LINE_RE.match(line.rstrip("\n\r"))
    if not m:
        return None
    return m.group("prefix"), m.group("marker"), m.group("task"), line


def replace_marker_on_line(line: str, new_marker: str) -> str:
    parsed = parse_line(line.rstrip("\n\r"))
    if not parsed:
        raise ValueError("Line does not contain a TODO/DONE marker")
    prefix, _old, task, _full = parsed
    newline = ""
    if line.endswith("\r\n"):
        newline = "\r\n"
    elif line.endswith("\n"):
        newline = "\n"
    return f"{prefix}{new_marker}: {task}{newline}"
