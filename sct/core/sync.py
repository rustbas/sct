from __future__ import annotations

import logging
from pathlib import Path

from sct.core.config import Config
from sct.core.models import TodoItem
from sct.core.scanner import file_stat, iter_source_files, scan_file, scan_project
from sct.core.store import Cache, Store

log = logging.getLogger(__name__)


def merge_items(scanned: list[TodoItem], previous: dict[str, TodoItem]) -> dict[str, TodoItem]:
    merged: dict[str, TodoItem] = {}
    for item in scanned:
        old = previous.get(item.id)
        if old and old.github:
            item.github = old.github
        merged[item.id] = item
    return merged


def sync(
    config: Config,
    *,
    full: bool = False,
    verbose: bool = False,
) -> Cache:
    store = Store(config)
    cache = store.load()

    all_paths = iter_source_files(config)
    new_file_index: dict[str, dict[str, int]] = {}
    for path in all_paths:
        rel = str(path.relative_to(config.root))
        new_file_index[rel] = file_stat(path)

    existing_files = set(new_file_index.keys())

    if full or not cache.items:
        scanned = scan_project(config)
        if verbose:
            log.info("sync full: %d file(s) in tree", len(all_paths))
    else:
        paths_to_scan: list[Path] = []
        for path in all_paths:
            rel = str(path.relative_to(config.root))
            if cache.files.get(rel) != new_file_index[rel]:
                paths_to_scan.append(path)
        changed_rels = {str(p.relative_to(config.root)) for p in paths_to_scan}
        kept = [
            item
            for item in cache.items.values()
            if item.file not in changed_rels and item.file in existing_files
        ]
        scanned = list(kept)
        for path in paths_to_scan:
            scanned.extend(scan_file(config, path))
        if verbose:
            log.info(
                "sync incremental: %d changed, %d kept",
                len(paths_to_scan),
                len(kept),
            )

    cache.items = merge_items(scanned, cache.items)
    cache.items = {
        item_id: item
        for item_id, item in cache.items.items()
        if item.file in existing_files
    }
    cache.files = new_file_index
    store.save(cache)
    if verbose:
        log.info("sync done: %d item(s)", len(cache.items))
    return cache
