from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sct.core.config import Config
from sct.core.models import TodoItem


CACHE_VERSION = 1


@dataclass
class Cache:
    version: int = CACHE_VERSION
    scanned_at: str = ""
    files: dict[str, dict[str, int]] = field(default_factory=dict)
    items: dict[str, TodoItem] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "scanned_at": self.scanned_at,
            "files": self.files,
            "items": {k: v.to_dict() for k, v in self.items.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Cache:
        items = {k: TodoItem.from_dict(v) for k, v in data.get("items", {}).items()}
        return cls(
            version=int(data.get("version", 1)),
            scanned_at=data.get("scanned_at", ""),
            files=data.get("files", {}),
            items=items,
        )


class Store:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.path = config.cache_path

    def load(self) -> Cache:
        if not self.path.is_file():
            return Cache()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return Cache()
        if data.get("version") != CACHE_VERSION:
            return Cache()
        return Cache.from_dict(data)

    def save(self, cache: Cache) -> None:
        self.config.ensure_dirs()
        cache.scanned_at = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(cache.to_dict(), indent=2, ensure_ascii=False)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.path)
