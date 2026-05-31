from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sct.core.config import Config
from sct.core.scanner import file_stat, iter_source_files, line_hash, scan_project
from sct.core.store import Cache, Store


@dataclass
class DoctorReport:
    stale_files: list[str] = field(default_factory=list)
    orphan_items: list[str] = field(default_factory=list)
    duplicate_tasks: list[tuple[str, str, int]] = field(default_factory=list)
    missing_in_cache: int = 0
    extra_in_cache: int = 0
    ok: bool = True

    def add_issue(self) -> None:
        self.ok = False


def run_doctor(config: Config, *, resync_compare: bool = False) -> DoctorReport:
    store = Store(config)
    cache = store.load()
    report = DoctorReport()

    current_files = iter_source_files(config)
    current_rels = {str(p.relative_to(config.root)) for p in current_files}
    file_index: dict[str, dict[str, int]] = {}

    for path in current_files:
        rel = str(path.relative_to(config.root))
        stat = file_stat(path)
        file_index[rel] = stat
        prev = cache.files.get(rel)
        if prev and prev != stat:
            report.stale_files.append(rel)
            report.add_issue()

    for rel in cache.files:
        if rel not in current_rels:
            report.stale_files.append(f"{rel} (removed)")
            report.add_issue()

    # Orphan / hash mismatch in cache
    for item in cache.items.values():
        if item.file not in current_rels:
            report.orphan_items.append(f"{item.id} ({item.file} missing)")
            report.add_issue()
            continue
        path = config.root / item.file
        try:
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines()
            if item.line < 1 or item.line > len(lines):
                report.orphan_items.append(f"{item.id} ({item.file}:{item.line} out of range)")
                report.add_issue()
                continue
            line = lines[item.line - 1]
            if item.line_hash and line_hash(line) != item.line_hash:
                report.orphan_items.append(
                    f"{item.id} ({item.file}:{item.line} line changed)"
                )
                report.add_issue()
        except OSError:
            report.orphan_items.append(f"{item.id} (cannot read {item.file})")
            report.add_issue()

    # Duplicate (file, task) in fresh scan
    if resync_compare:
        scanned = scan_project(config)
        from collections import Counter

        keys = [(i.file, i.task) for i in scanned]
        for (file, task), count in Counter(keys).items():
            if count > 1:
                report.duplicate_tasks.append((file, task, count))
                report.add_issue()
        scan_ids = {i.id for i in scanned}
        cache_ids = set(cache.items.keys())
        report.missing_in_cache = len(scan_ids - cache_ids)
        report.extra_in_cache = len(cache_ids - scan_ids)
        if report.missing_in_cache or report.extra_in_cache:
            report.add_issue()
    else:
        scanned = []
        by_key: dict[tuple[str, str], int] = {}
        for item in cache.items.values():
            key = (item.file, item.task)
            by_key[key] = by_key.get(key, 0) + 1
        for (file, task), count in by_key.items():
            if count > 1:
                report.duplicate_tasks.append((file, task, count))
                report.add_issue()

    return report
