from __future__ import annotations

from pathlib import Path

from sct.core.config import Config
from sct.core.models import TodoItem
from sct.core.scanner import file_stat, iter_source_files, scan_project
from sct.core.store import Cache, Store


def merge_items(scanned: list[TodoItem], previous: dict[str, TodoItem]) -> dict[str, TodoItem]:
    merged: dict[str, TodoItem] = {}
    for item in scanned:
        old = previous.get(item.id)
        if old and old.github:
            item.github = old.github
        merged[item.id] = item
    return merged


def sync(config: Config, *, full: bool = True) -> Cache:
    store = Store(config)
    cache = store.load() if full else store.load()

    file_index: dict[str, dict[str, int]] = {}
    for path in iter_source_files(config):
        rel = str(path.relative_to(config.root))
        file_index[rel] = file_stat(path)

    scanned = scan_project(config)
    cache.items = merge_items(scanned, cache.items)
    cache.files = file_index
    store.save(cache)
    return cache
