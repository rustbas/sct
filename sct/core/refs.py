from __future__ import annotations

import re

from sct.core.errors import AmbiguousRefError
from sct.core.models import TodoItem

MIN_ID_PREFIX_LEN = 4
_HEX_REF_RE = re.compile(r"^[0-9a-fA-F]+$")


def _resolve_file_line(ref: str, items: dict[str, TodoItem]) -> TodoItem | None:
    if ":" not in ref:
        return None
    file_part, line_part = ref.rsplit(":", 1)
    try:
        line_no = int(line_part)
    except ValueError:
        return None
    for item in items.values():
        if item.file == file_part and item.line == line_no:
            return item
    for item in items.values():
        if item.file.endswith(file_part) and item.line == line_no:
            return item
    return None


def _resolve_id_prefix(ref: str, items: dict[str, TodoItem]) -> TodoItem | None:
    if not _HEX_REF_RE.match(ref):
        return None
    if len(ref) < MIN_ID_PREFIX_LEN:
        return None
    needle = ref.lower()
    matches = [item_id for item_id in items if item_id.startswith(needle)]
    if len(matches) == 1:
        return items[matches[0]]
    if len(matches) > 1:
        preview = ", ".join(sorted(matches)[:5])
        extra = f" (+{len(matches) - 5} more)" if len(matches) > 5 else ""
        raise AmbiguousRefError(
            f"Ambiguous id {ref!r}: {preview}{extra}"
        )
    return None


def resolve_ref(ref: str, items: dict[str, TodoItem]) -> TodoItem | None:
    """Resolve ref as exact id, file:line, or unique hex id prefix."""
    if ref in items:
        return items[ref]
    by_path = _resolve_file_line(ref, items)
    if by_path is not None:
        return by_path
    return _resolve_id_prefix(ref, items)
