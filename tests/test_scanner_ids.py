import tempfile
import unittest
from pathlib import Path

from sct.core.errors import AmbiguousRefError
from sct.core.models import Status
from sct.core.refs import resolve_ref
from sct.core.scanner import make_id
from sct.core.service import TodoService


class ScannerIdsTest(unittest.TestCase):
    def test_same_task_text_different_lines_get_different_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "app.py"
            path.write_text(
                "# TODO: same\n"
                "# TODO: same\n",
                encoding="utf-8",
            )
            svc = TodoService(root)
            cache = svc.sync(full=True)
            self.assertEqual(len(cache.items), 2)
            ids = {item.id for item in cache.items.values()}
            self.assertEqual(len(ids), 2)

    def test_make_id_uses_line_not_task(self) -> None:
        a = make_id("f.py", 10)
        b = make_id("f.py", 20)
        c = make_id("f.py", 10)
        self.assertNotEqual(a, b)
        self.assertEqual(a, c)


class ResolveRefTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / "app.py"
        self.path.write_text(
            "# TODO: first\n"
            "# TODO: second\n",
            encoding="utf-8",
        )
        self.svc = TodoService(self.root)
        self.svc.sync(full=True)
        self.items = dict(self.svc.load_cache().items)
        self.ids = sorted(self.items.keys())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_exact_id(self) -> None:
        full = self.ids[0]
        item = resolve_ref(full, self.items)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.id, full)

    def test_unique_prefix(self) -> None:
        full = self.ids[0]
        prefix = full[:6]
        item = resolve_ref(prefix, self.items)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.id, full)

    def test_file_line(self) -> None:
        item = resolve_ref("app.py:1", self.items)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.line, 1)

    def test_prefix_too_short_returns_none(self) -> None:
        self.assertIsNone(resolve_ref("ab", self.items))

    def test_ambiguous_prefix(self) -> None:
        from sct.core.models import Status, TodoItem

        fake = {
            "abcd111111111111": TodoItem(
                id="abcd111111111111",
                file="a.py",
                line=1,
                marker="TODO",
                status=Status.OPEN,
                priority=1,
                task="one",
            ),
            "abcd222222222222": TodoItem(
                id="abcd222222222222",
                file="a.py",
                line=2,
                marker="TODO",
                status=Status.OPEN,
                priority=1,
                task="two",
            ),
        }
        with self.assertRaises(AmbiguousRefError):
            resolve_ref("abcd", fake)

    def test_done_by_prefix_via_service(self) -> None:
        open_items = self.svc.list_items(status=Status.OPEN)
        target = open_items[0]
        prefix = target.id[:8]
        updated = self.svc.done(prefix)
        self.assertEqual(updated.id, target.id)
        self.assertEqual(updated.status, Status.DONE)


if __name__ == "__main__":
    unittest.main()
