from __future__ import annotations

import hashlib
from pathlib import Path

from sct.core.config import Config
from sct.core.markers import LINE_RE, priority_from_marker, status_from_marker
from sct.core.models import TodoItem


def line_hash(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8", errors="replace")).hexdigest()[:16]


def make_id(relative_file: str, task: str) -> str:
    key = f"{relative_file}\0{task.strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def iter_source_files(config: Config) -> list[Path]:
    root = config.root
    suffixes = set(config.include_suffixes)
    exclude = set(config.exclude_dirs)
    files: list[Path] = []

    def walk(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name)
        except OSError:
            return
        for path in entries:
            name = path.name
            if path.is_dir():
                if name in exclude or name.startswith("."):
                    continue
                walk(path)
            elif path.is_file():
                if path.suffix in suffixes or path.suffix.lower() in suffixes:
                    files.append(path)

    walk(root)
    return files


def scan_file(config: Config, path: Path) -> list[TodoItem]:
    rel = str(path.relative_to(config.root))
    items: list[TodoItem] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return items

    for lineno, line in enumerate(text.splitlines(), start=1):
        m = LINE_RE.match(line)
        if not m:
            continue
        marker = m.group("marker")
        task = m.group("task").strip()
        item_id = make_id(rel, task)
        items.append(
            TodoItem(
                id=item_id,
                file=rel,
                line=lineno,
                marker=marker,
                status=status_from_marker(marker),
                priority=priority_from_marker(marker),
                task=task,
                line_hash=line_hash(line),
            )
        )
    return items


def scan_project(config: Config) -> list[TodoItem]:
    found: list[TodoItem] = []
    for path in iter_source_files(config):
        found.extend(scan_file(config, path))
    found.sort(key=lambda t: (t.file, t.line))
    return found


def file_stat(path: Path) -> dict[str, int]:
    st = path.stat()
    return {"mtime_ns": st.st_mtime_ns, "size": st.st_size}
