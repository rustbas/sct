import tempfile
import unittest
from pathlib import Path

from sct.core.errors import StaleLineError
from sct.core.models import Status
from sct.core.service import TodoService


class IntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        sample = self.root / "app.py"
        sample.write_text(
            "# TODO: first task\n"
            "# TODOO: second task\n",
            encoding="utf-8",
        )
        self.svc = TodoService(self.root)
        self.svc.init_project()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_sync_list_done_reopen(self) -> None:
        cache = self.svc.sync(full=True)
        self.assertEqual(len(cache.items), 2)
        open_items = self.svc.list_items(status=Status.OPEN)
        self.assertEqual(len(open_items), 2)
        target = next(i for i in open_items if i.priority == 2)
        self.svc.done(target.id)
        text = (self.root / "app.py").read_text(encoding="utf-8")
        self.assertIn("DONEE:", text)
        self.assertNotIn("TODOO:", text)
        self.svc.reopen(target.id)
        text = (self.root / "app.py").read_text(encoding="utf-8")
        self.assertIn("TODOO:", text)

    def test_incremental_sync_after_edit(self) -> None:
        self.svc.sync(full=True)
        path = self.root / "app.py"
        path.write_text("# TODO: only one\n", encoding="utf-8")
        self.svc.sync(full=False)
        items = self.svc.list_items(status=Status.OPEN)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].task, "only one")

    def test_done_rejects_stale_line(self) -> None:
        self.svc.sync(full=True)
        item = self.svc.list_items(status=Status.OPEN)[0]
        path = self.root / "app.py"
        path.write_text("# TODO: changed text\n", encoding="utf-8")
        with self.assertRaises(StaleLineError):
            self.svc.done(item.id)


if __name__ == "__main__":
    unittest.main()
