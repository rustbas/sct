"""GitHub issue integration (planned).

Future: create/link issues via `gh` CLI; store issue id in cache item `github` field.
"""

from __future__ import annotations

from typing import Any

from sct.core.models import TodoItem


def issue_payload(item: TodoItem) -> dict[str, Any]:
    title = f"[P{item.priority}] {item.task}"
    body = (
        f"Source: `{item.file}:{item.line}`\n\n"
        f"<!-- sct:id={item.id} -->\n"
    )
    return {"title": title, "body": body}
