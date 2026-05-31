from __future__ import annotations

import logging
import shutil
from pathlib import Path

from sct.core.config import Config
from sct.core.doctor import DoctorReport, run_doctor
from sct.core.errors import NotFoundError, SctError
from sct.core.models import Status, TodoItem
from sct.core.patch import mark_done, mark_open
from sct.core.store import Cache, Store
from sct.core.sync import sync

log = logging.getLogger(__name__)


class TodoService:
    def __init__(self, root: Path | None = None) -> None:
        self.config = Config.discover(root)
        self.store = Store(self.config)

    def load_cache(self) -> Cache:
        return self.store.load()

    def sync(self, *, full: bool = False, verbose: bool = False) -> Cache:
        if verbose:
            logging.basicConfig(level=logging.INFO, format="%(message)s")
        return sync(self.config, full=full, verbose=verbose)

    def init_project(self, *, force: bool = False) -> Path:
        self.config.ensure_dirs()
        example = self.config.root / ".sct" / "config.json.example"
        target = self.config.config_path
        if target.is_file() and not force:
            return target
        if example.is_file():
            shutil.copy(example, target)
        else:
            target.write_text(
                '{\n  "exclude_dirs": [".git", "__pycache__", ".venv", "node_modules"]\n}\n',
                encoding="utf-8",
            )
        return target

    def doctor(self, *, resync_compare: bool = False) -> DoctorReport:
        return run_doctor(self.config, resync_compare=resync_compare)

    def list_items(
        self,
        *,
        status: Status | None = None,
        priority: int | None = None,
        use_cache: bool = True,
    ) -> list[TodoItem]:
        if use_cache and self.config.cache_path.is_file():
            items = list(self.load_cache().items.values())
        else:
            items = list(self.sync().items.values())
        if status is not None:
            items = [i for i in items if i.status == status]
        if priority is not None:
            items = [i for i in items if i.priority == priority]
        items.sort(key=lambda t: (-t.priority, t.file, t.line))
        return items

    def get(self, item_id: str) -> TodoItem | None:
        return self.load_cache().items.get(item_id)

    def resolve(self, ref: str) -> TodoItem | None:
        """ref: id, or file:line"""
        cache = self.load_cache()
        if ref in cache.items:
            return cache.items[ref]
        if ":" in ref:
            file_part, line_part = ref.rsplit(":", 1)
            try:
                line_no = int(line_part)
            except ValueError:
                return None
            for item in cache.items.values():
                if item.file == file_part and item.line == line_no:
                    return item
            for item in cache.items.values():
                if item.file.endswith(file_part) and item.line == line_no:
                    return item
        return None

    def done(self, ref: str) -> TodoItem:
        item = self._require(ref)
        if item.status == Status.DONE:
            return item
        updated = mark_done(item, self.config.root)
        cache = self.load_cache()
        cache.items[updated.id] = updated
        self.store.save(cache)
        return updated

    def reopen(self, ref: str) -> TodoItem:
        item = self._require(ref)
        if item.status == Status.OPEN:
            return item
        updated = mark_open(item, self.config.root)
        cache = self.load_cache()
        cache.items[updated.id] = updated
        self.store.save(cache)
        return updated

    def _require(self, ref: str) -> TodoItem:
        item = self.resolve(ref)
        if item is None:
            raise NotFoundError(f"Todo not found: {ref}")
        return item

    def preview_done(self, ref: str) -> tuple[str, str]:
        item = self._require(ref)
        from sct.core.markers import done_marker, replace_marker_on_line
        from sct.core.validate import verify_line_unchanged

        verify_line_unchanged(item, self.config.root)
        path = self.config.root / item.file
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        old = lines[item.line - 1].rstrip("\n\r")
        new = replace_marker_on_line(
            lines[item.line - 1], done_marker(item.priority)
        ).rstrip("\n\r")
        return old, new
