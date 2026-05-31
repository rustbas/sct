from __future__ import annotations

from pathlib import Path

from sct.core.config import Config
from sct.core.models import Status, TodoItem
from sct.core.patch import mark_done, mark_open
from sct.core.store import Cache, Store
from sct.core.sync import sync


# TODO: GitHub issue integration (gh / API)


class TodoService:
    def __init__(self, root: Path | None = None) -> None:
        self.config = Config.discover(root)
        self.store = Store(self.config)

    def load_cache(self) -> Cache:
        return self.store.load()

    def sync(self, *, full: bool = True) -> Cache:
        return sync(self.config, full=full)

    def list_items(
        self,
        *,
        status: Status | None = None,
        use_cache: bool = True,
    ) -> list[TodoItem]:
        if use_cache and self.config.cache_path.is_file():
            items = list(self.load_cache().items.values())
        else:
            items = list(self.sync().items.values())
        if status is not None:
            items = [i for i in items if i.status == status]
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
                if item.file == file_part or item.file.endswith("/" + file_part):
                    if item.line == line_no:
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
            raise KeyError(f"Todo not found: {ref}")
        return item

    def preview_done(self, ref: str) -> tuple[str, str]:
        item = self._require(ref)
        from sct.core.markers import done_marker, replace_marker_on_line

        path = self.config.root / item.file
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        old = lines[item.line - 1].rstrip("\n\r")
        new = replace_marker_on_line(lines[item.line - 1], done_marker(item.priority)).rstrip("\n\r")
        return old, new
