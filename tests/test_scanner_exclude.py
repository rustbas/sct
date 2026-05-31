import tempfile
import unittest
from pathlib import Path

from sct.core.config import Config
from sct.core.scanner import iter_source_files, scan_project


class ScannerExcludeTest(unittest.TestCase):
    def test_tests_dir_excluded_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("# TODO: real\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "t.py").write_text(
                '# TODO: fixture in test\n"',
                encoding="utf-8",
            )
            cfg = Config(root=root)
            paths = iter_source_files(cfg)
            rels = {str(p.relative_to(root)) for p in paths}
            self.assertIn("app.py", rels)
            self.assertNotIn("tests/t.py", rels)
            items = scan_project(cfg)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].task, "real")


if __name__ == "__main__":
    unittest.main()
