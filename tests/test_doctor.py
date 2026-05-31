import tempfile
import unittest
from pathlib import Path

from sct.core.service import TodoService


class DoctorTest(unittest.TestCase):
    def test_doctor_ok_after_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "x.py").write_text("# TODO: x\n", encoding="utf-8")
            svc = TodoService(root)
            svc.sync(full=True)
            report = svc.doctor()
            self.assertTrue(report.ok)

    def test_doctor_stale_after_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "x.py"
            path.write_text("# TODO: x\n", encoding="utf-8")
            svc = TodoService(root)
            svc.sync(full=True)
            path.write_text("# TODO: edited\n", encoding="utf-8")
            report = svc.doctor()
            self.assertFalse(report.ok)
            self.assertTrue(report.orphan_items or report.stale_files)


if __name__ == "__main__":
    unittest.main()
