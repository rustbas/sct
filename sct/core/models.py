from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    OPEN = "open"
    DONE = "done"

    @classmethod
    def from_marker(cls, marker: str) -> Status:
        if marker.startswith("TOD"):
            return cls.OPEN
        if marker.startswith("DON"):
            return cls.DONE
        return cls.OPEN


@dataclass
class TodoItem:
    id: str
    file: str
    line: int
    marker: str
    status: Status
    priority: int
    task: str
    line_hash: str = ""
    github: dict[str, Any] | None = None

    def list_line(self) -> str:
        return f"{self.file}:{self.line}:{self.task}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file": self.file,
            "line": self.line,
            "marker": self.marker,
            "status": self.status.value,
            "priority": self.priority,
            "task": self.task,
            "line_hash": self.line_hash,
            "github": self.github,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TodoItem:
        return cls(
            id=data["id"],
            file=data["file"],
            line=int(data["line"]),
            marker=data["marker"],
            status=Status(data["status"]),
            priority=int(data["priority"]),
            task=data["task"],
            line_hash=data.get("line_hash", ""),
            github=data.get("github"),
        )
